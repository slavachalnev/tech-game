"""The tg commands, including the two Claude Code hooks, run in-process."""
import io
import json
import sys

import pytest

from engine import cli, history, state


@pytest.fixture
def save(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    return state.new_save("cornwall-1705", "g1")


def tg(monkeypatch, capsys, *args, stdin=None):
    """Run `tg ...` and return (exit code, stdout, stderr)."""
    monkeypatch.setattr(sys, "argv", ["tg", *args])
    if stdin is not None:
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(stdin)))
    try:
        cli.main()
        code = 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    out = capsys.readouterr()
    return code, out.out, out.err


@pytest.mark.parametrize("content", [
    {"id": "bad", "name": "Bad", "kind": "gadget", "status": "ok", "summary": "s"},  # schema error
    ["not", "an", "object"],  # parses, wrong shape
])
def test_hook_blocks_bad_writes_with_exit_2(save, monkeypatch, capsys, content):
    (save / "things/bad.json").write_text(json.dumps(content))
    code, _, err = tg(monkeypatch, capsys, "hook", stdin={"cwd": str(save), "tool_input": {"file_path": "things/bad.json"}})
    assert code == 2 and "things/bad.json" in err


def test_hook_blocks_values_the_engine_cant_compute_with(save, monkeypatch, capsys):
    world = state.read_json(save / "world.json")
    turn = {"turn": 1.0, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T09:00", "action": "a", "rulings": [], "narration": "n"}
    for path, content in [("world.json", {**world, "clock": "1705-04-31T08:00"}), ("world.json", {**world, "clock": "1705-04-30T24:00"}),
                          ("world.json", {**world, "purse_p": 4718.0}), ("log/0001.json", turn)]:
        state.write_json(save / path, content)
        code, _, err = tg(monkeypatch, capsys, "hook", stdin={"cwd": str(save), "tool_input": {"file_path": path}})
        assert code == 2 and path in err, (content, err)


def test_undo_names_every_turn_it_takes_back(save, monkeypatch, capsys):
    history.snapshot(save)
    for n in (1, 2):  # two turns in one snapshot go back together
        state.write_json(save / f"log/{n:04d}.json", {"turn": n, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T09:00", "action": f"act {n}", "rulings": [], "narration": "n"})
    history.snapshot(save)
    code, out, _ = tg(monkeypatch, capsys, "--save", str(save), "undo")
    assert code == 0 and "turns 1–2" in out and state.next_turn(save) == 1


def test_a_drawing_named_like_a_module_hides_nothing(save, monkeypatch, capsys):
    (save / "drawings/engine.py").write_text((save / "drawings/anvil.py").read_text())  # "engine" is a likely id
    code, out, _ = tg(monkeypatch, capsys, "--save", str(save), "draw", "forge")
    assert code == 0 and "visuals/forge.svg" in out, out


def test_hook_passes_good_writes_and_ignores_files_outside_saves(save, monkeypatch, capsys, tmp_path):
    assert tg(monkeypatch, capsys, "hook", stdin={"cwd": str(save), "tool_input": {"file_path": str(save / "world.json")}})[0] == 0
    (tmp_path / "notes.json").write_text("{")
    assert tg(monkeypatch, capsys, "hook", stdin={"cwd": str(tmp_path), "tool_input": {"file_path": "notes.json"}})[0] == 0


def test_snapshot_hook_reads_the_save_from_stdin(save, monkeypatch, capsys):
    tg(monkeypatch, capsys, "snapshot", stdin={"hook_event_name": "Stop", "cwd": str(save / "things")})
    assert history.log(save)[0][1] == "start"


def test_money_clock_and_paydays(save, monkeypatch, capsys):
    assert "Purse: £47.65" in tg(monkeypatch, capsys, "--save", str(save), "pay", "£2.35")[1]
    assert "Purse: £48.10" in tg(monkeypatch, capsys, "receive", "45p", "--save", str(save))[1]  # --save after the command
    world = state.read_json(save / "world.json")
    world["coming_up"].append({"when": "1705-04-03T10:00", "what": "See Penrose"})
    state.write_json(save / "world.json", world)
    out = tg(monkeypatch, capsys, "--save", str(save), "advance", "1w")[1]
    assert "Monday 9 April 1705" in out and "Payday passed: Saturday 7 April" in out and "Jacca Pascoe 45p" in out
    assert "Passed (from coming_up):\n  Tuesday 3 April 1705, 10:00: See Penrose" in out and "rent" not in out


def test_status_show_and_places(save, monkeypatch, capsys):
    out = tg(monkeypatch, capsys, "--save", str(save), "status")[1]
    assert "Player:  (no name yet)" in out and "Coming up:\n  Sunday 24 June (in 3 months): Midsummer quarter day" in out
    code, out, _ = tg(monkeypatch, capsys, "--save", str(save), "show", "anvil", "carnkie", "nothing")
    assert code == 1 and "== things/anvil" in out and "== place carnkie" in out
    assert "carn-brea" in tg(monkeypatch, capsys, "--save", str(save), "places", "carnkie")[1]
    assert tg(monkeypatch, capsys, "--save", str(save), "places", "atlantis")[0] == 1


def test_broken_world_gives_a_message_not_a_traceback(save, monkeypatch, capsys):
    (save / "world.json").write_text('{"scenario": "cornwall-1705"}')
    code, _, _ = tg(monkeypatch, capsys, "--save", str(save), "advance", "1d")
    assert code == 1

