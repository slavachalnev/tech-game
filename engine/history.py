"""A save's history: a git repo in <save>/.history, snapshotted after every referee reply, so turns can be undone.

It lives in .history rather than .git so Claude Code doesn't treat each save as a separate project.
"""
import re
import subprocess

from . import state

IGNORE = ".history/\n.shots/\n.claude/settings.local.json\n"


def git(save, *args):
    cmd = ["git", f"--git-dir={save / '.history'}", f"--work-tree={save}",
           "-c", "user.name=Time Travel Game", "-c", "user.email=game@localhost", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def snapshot(save):
    """Commit whatever changed, labelled by the latest turn. Returns the message, or None if nothing changed."""
    if not (save / ".history").exists():
        git(save, "init", "-q")
        (save / ".history" / "info" / "exclude").write_text(IGNORE)
    git(save, "add", "-A")
    changes = git(save, "status", "--porcelain").splitlines()
    if not changes:
        return None
    n = state.next_turn(save) - 1
    if f"A  log/{n:04d}.json" in changes:
        message = f"turn {n}: {(state.read_json(save / 'log' / f'{n:04d}.json') or {}).get('action', '')[:70]}"
    else:
        message = f"after turn {n}" if n else "start"
    git(save, "commit", "-q", "-m", message)
    return message


def turn_ends(save):
    """{turn: snapshot} for every turn that another turn has been logged after: the last snapshot before the next
    turn's, so the journal can show a turn's drawings as they were when it ended."""
    if not (save / ".history").exists():
        return {}
    ends, parent = {}, None
    for line in git(save, "log", "--diff-filter=A", "--format=>%P", "--name-only", "--", "log/").splitlines():
        if line.startswith(">"):
            parent = line[1:].split(" ")[0] or None
        elif (m := re.fullmatch(r"log/(\d{4})\.json", line)) and parent and int(m[1]) > 1:
            ends[int(m[1]) - 1] = parent
    return ends


def show(save, rev, path):
    """A file's text in a snapshot, or None if it wasn't there."""
    try:
        return git(save, "show", f"{rev}:{path}")
    except RuntimeError:
        return None


def log(save):
    """Snapshots, newest first, as (short hash, message) pairs."""
    return [tuple(line.split(" ", 1)) for line in git(save, "log", "--format=%h %s").splitlines()]


def restore(save, ref):
    """Snapshot the current state, then reset the save to `ref`. Returns the tag that keeps what was replaced."""
    snapshot(save)
    tag = f"kept-{git(save, 'rev-parse', '--short', 'HEAD')}"
    git(save, "tag", "-f", tag)
    git(save, "reset", "-q", "--hard", ref)
    return tag


def undo(save):
    """Put the save back as it was just before the last logged turn. Returns (turn number, tag of the undone state)."""
    snapshot(save)
    n = state.next_turn(save) - 1
    if not n:
        raise SystemExit("No turns to undo.")
    added = git(save, "log", "--diff-filter=A", "--format=%H", "--", f"log/{n:04d}.json").split()
    if not added or added[0] in git(save, "rev-list", "--max-parents=0", "HEAD").split():
        raise SystemExit(f"Turn {n} is older than this save's history, so it can't be undone.")
    return n, restore(save, f"{added[0]}^")
