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
    out = tg(monkeypatch, capsys, "--save", str(save), "advance", "1w")[1]
    assert "Monday 9 April 1705" in out and "Payday passed: Saturday 7 April" in out and "Jacca Pascoe 45p" in out


def test_status_show_and_places(save, monkeypatch, capsys):
    assert "Player:  (no name yet)" in tg(monkeypatch, capsys, "--save", str(save), "status")[1]
    code, out, _ = tg(monkeypatch, capsys, "--save", str(save), "show", "anvil", "carnkie", "nothing")
    assert code == 1 and "== things/anvil" in out and "== place carnkie" in out
    assert "carn-brea" in tg(monkeypatch, capsys, "--save", str(save), "places", "carnkie")[1]
    assert tg(monkeypatch, capsys, "--save", str(save), "places", "atlantis")[0] == 1


def test_broken_world_gives_a_message_not_a_traceback(save, monkeypatch, capsys):
    (save / "world.json").write_text('{"scenario": "cornwall-1705"}')
    code, _, _ = tg(monkeypatch, capsys, "--save", str(save), "advance", "1d")
    assert code == 1
