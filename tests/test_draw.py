"""The drawing kit and tg draw."""
import re
from xml.etree import ElementTree

from engine import state
from engine.draw import Sheet, wrap
from tests.test_cli import save, tg  # noqa: F401  (fixtures)

SVG = "{http://www.w3.org/2000/svg}"


def box(p, cut=False):
    """A 400 × 300 mm box, its origin the middle of its base."""
    p.rect(-200, 0, 400, 300, "timber", cut=cut)
    p.anchor("lid", 0, 300)


def crate(p):
    """A crate: a box with another box (a lid) on it, marked as its own part."""
    p.part(box)
    p.part(box, at=(0, 300), thing="lid")


def test_a_part_drawn_on_two_sheets_is_the_same_shape_and_marked_for_the_board():
    own = Sheet("box", "Box")
    own.place(box, cut=True)
    inside = Sheet("crate", "Crate")
    c = inside.place(crate, thing="crate")
    for svg in (own.svg(), inside.svg()):
        root = ElementTree.fromstring(svg)
        assert root.find(f".//{SVG}g[@data-object]") is not None
        assert '<rect x="-200" y="0" width="400" height="300"' in svg  # the same geometry, in mm
    assert 'data-thing="crate"' in inside.svg() and 'data-thing="lid"' in inside.svg()
    assert c.at(0, 600) == (0, 600)  # a point of the part, in the sheet's mm


def test_the_object_is_fitted_inside_the_sheet_with_room_for_labels():
    s = Sheet("box", "Box", size=(800, 600))
    b = s.place(box, at=(5000, -2000))  # anywhere: the sheet fits it
    s.label("the lid", b["lid"])
    k, ox, oy = s._fit()
    x0, y0, x1, y1 = s.box
    assert 0 < ox + x0 * k < ox + x1 * k < 800 and 0 < oy - y1 * k < oy - y0 * k < 600
    assert ox + x0 * k >= 300 or ox + x1 * k <= 500  # a margin for the label column on one side


def test_labels_in_a_column_do_not_overlap():
    s = Sheet("box", "Box")
    b = s.place(box)
    for i in range(6):
        s.label(f"label {i}, a fairly long one that wraps onto two lines", b.at(150, 150 + i))  # all at nearly one height
    ys = [float(y) for y in re.findall(r'<text x="[\d.]+" y="([\d.]+)" font-size="13" font-style="italic" text-anchor="start"', s.svg())]
    assert len(ys) == 6 and all(b - a >= 2 * 15 for a, b in zip(ys, ys[1:]))


def test_states_and_steps_wrap_what_is_drawn_inside_them():
    s = Sheet("box", "Box")
    with s.state("open"):
        s.place(box, thing="lid")
    with s.step(1, "Lift the lid"):
        s.label("lifted", (0, 300))
    svg = s.svg()
    assert re.search(r'<g data-state="open"><g data-thing="lid"', svg)
    assert re.search(r'<g data-step="1" data-caption="Lift the lid"><text', svg)


def test_wrap_keeps_lines_short():
    assert wrap("one two three four five", 9) == ["one two", "three", "four five"]


def test_tg_draw_runs_the_save_drawing_scripts_and_checks_them(save, monkeypatch, capsys):  # noqa: F811
    folder = save / "drawings"
    folder.mkdir()
    (folder / "parts.py").write_text("def box(p):\n    p.rect(0, 0, 100, 50, 'brass')\n")
    (folder / "anvil.py").write_text("from engine.draw import Sheet\nfrom parts import box\ns = Sheet('anvil', 'Anvil')\ns.place(box)\ns.save()\n")
    (folder / "broken.py").write_text("raise ValueError('no such part')\n")
    code, out, _ = tg(monkeypatch, capsys, "--save", "g1", "draw", "anvil")
    assert code == 0 and out.strip() == "visuals/anvil.svg" and state.check_file(save, save / "visuals/anvil.svg") == []
    code, out, _ = tg(monkeypatch, capsys, "--save", "g1", "draw")  # all of them: one fails
    assert code == 1 and "drawings/broken.py failed" in out and "no such part" in out
