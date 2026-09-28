import json

import pytest

from engine import state


def test_money_round_trip():
    assert [state.parse_money(t) for t in ("£3.25", "3.25", "£3", "45p", "£0.5")] == [325, 325, 300, 45, 50]
    assert [state.fmt_money(p) for p in (5000, 4718, 150, 45, 0, -150)] == ["£50", "£47.18", "£1.50", "45p", "0p", "-£1.50"]
    with pytest.raises(SystemExit):
        state.parse_money("three pounds")


def test_clock_uses_old_style_weekdays_before_1752():
    assert state.fmt_clock("1705-04-02T08:00") == "Monday 2 April 1705, 08:00"  # Julian; Gregorian 13 April
    assert state.advance_clock("1705-04-02T08:00", "1w2d3h30m") == "1705-04-11T11:30"
    assert state.fmt_clock("1850-06-01T12:00").startswith("Saturday")
    # Monday 2 April 1705 (Old Style): the first Saturday payday is the 7th, at 18:00
    assert [d.day for d in state.paydays("1705-04-02T08:00", "1705-04-16T08:00")] == [7, 14]
    assert state.paydays("1705-04-07T08:00", "1705-04-07T17:00") == []
    assert len(state.paydays("1705-04-07T17:00", "1705-04-07T19:00")) == 1


@pytest.mark.parametrize("scenario", sorted(p.name for p in state.SCENARIOS.iterdir() if p.is_dir()))
def test_scenario_start_state_is_valid(scenario):
    assert state.check_save(state.SCENARIOS / scenario / "start") == []


def test_find_save_refuses_to_guess(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    monkeypatch.chdir(tmp_path)
    state.new_save("cornwall-1705", "a")
    assert state.find_save().name == "a"
    state.new_save("cornwall-1705", "b")
    with pytest.raises(SystemExit, match="several"):
        state.find_save()
    monkeypatch.chdir(tmp_path / "b" / "things")
    assert state.find_save().name == "b"


def test_new_save_is_a_dm_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "g1")
    assert "@../../scenarios/cornwall-1705/referee.md" in (save / "CLAUDE.md").read_text()
    assert "tg hook" in (save / ".claude/settings.json").read_text()
    assert state.next_turn(save) == 1 and state.check_save(save) == []


def test_check_file_rejects_bad_thing_and_misnumbered_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "g1")
    (save / "things/pump.json").write_text(json.dumps({"id": "pump", "name": "Pump", "kind": "gadget", "status": "ok"}))
    problems = state.check_file(save, save / "things/pump.json")
    assert any("summary" in p for p in problems) and any("gadget" in p for p in problems)
    turn = {"turn": 2, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T09:00", "action": "a", "rulings": [], "narration": "n"}
    (save / "log/0001.json").write_text(json.dumps(turn))
    assert any("must live in log/0002.json" in p for p in state.check_file(save, save / "log/0001.json"))
    (save / "maps/town.svg").write_text("<svg><title>Town</title>")
    assert any("not well-formed SVG" in p for p in state.check_file(save, save / "maps/town.svg"))


def test_places_must_be_labelled_on_their_maps(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "g1")
    gazetteer = state.read_json(save / "places.json")
    gazetteer["places"].append({"id": "st-agnes", "name": "St Agnes", "kind": "village", "x_km": 6, "y_km": 7, "maps": ["district"]})
    gazetteer["routes"].append({"from": "redruth", "to": "atlantis", "km": 1, "by": "sea", "time": "never"})
    state.write_json(save / "places.json", gazetteer)
    problems = state.check_save(save)
    assert any("'St Agnes' isn't labelled on maps/district.svg" in p for p in problems)
    assert any("unknown place 'atlantis'" in p for p in problems)


def test_undo_and_restore_turns(tmp_path, monkeypatch):
    from engine import history
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "g1")
    assert history.snapshot(save) == "start"
    for n in (1, 2):
        world = state.read_json(save / "world.json")
        world["purse_p"] -= 100
        state.write_json(save / "world.json", world)
        turn = {"turn": n, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T09:00", "action": f"act {n}", "rulings": [], "narration": "n"}
        state.write_json(save / f"log/{n:04d}.json", turn)
        assert history.snapshot(save) == f"turn {n}: act {n}"
    (save / "secret.md").write_text("a hidden fact")  # a later, non-turn edit
    assert history.snapshot(save) == "after turn 2"
    assert history.snapshot(save) is None  # nothing changed

    assert history.undo(save)[0] == 2
    assert state.next_turn(save) == 2 and state.read_json(save / "world.json")["purse_p"] == 4900
    assert "hidden fact" not in (save / "secret.md").read_text()
    tag = history.undo(save)[1]
    assert state.next_turn(save) == 1
    history.restore(save, tag)  # changed my mind
    assert state.next_turn(save) == 2


def test_recipes_link_to_real_tools_people_and_things(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "g1")
    recipe = {"id": "hoops", "name": "Forge iron hoops", "makes": "iron hoops up to 1 m across", "how": "bend and forge-weld bar",
              "tools": ["forge", "anvil"], "people": ["jacca-pascoe"], "time": "1 day each", "cost_p": 30, "quality": {"roundness_mm": 5}}
    state.write_json(save / "recipes/hoops.json", recipe)
    assert state.check_save(save) == []
    state.write_json(save / "recipes/hoops.json", {**recipe, "tools": ["lathe"], "first_made": "hoop-1"})
    problems = state.check_save(save)
    assert any("unknown tool 'lathe'" in p for p in problems) and any("unknown first_made thing 'hoop-1'" in p for p in problems)
