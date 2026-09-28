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
