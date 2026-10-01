"""Draws the catalogue of stock parts, dm/stock.png: each part on a small sheet with how to call it.

    uv run python dm/stock_catalogue.py
"""
from pathlib import Path
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright

from engine import stock
from engine.draw import Sheet

ElementTree.register_namespace("", "http://www.w3.org/2000/svg")

# (function, its arguments as written in the call, the time of day to show)
CALLS = [
    ("person", {}, None), ("person", {"pose": "work", "hat": "cap"}, None), ("person", {"pose": "carry", "facing": "left"}, None),
    ("person", {"pose": "sit"}, None), ("horse", {}, None), ("barrel", {"water": 0.6}, None), ("bucket", {}, None),
    ("bench", {}, None), ("shelf", {}, None), ("ladder", {}, None), ("door", {}, None), ("door", {"open": True}, None),
    ("window", {}, None), ("masonry", {"x": 0, "y": 0, "w": 2400, "h": 1500}, None), ("ground", {"x0": 0, "x1": 3000, "kind": "grass"}, None),
    ("water", {"x0": 0, "x1": 2000, "level": 0, "depth": 600}, None), ("pipe", {"points": [(0, 0), (400, 0), (400, 300), (900, 300)]}, None),
    ("flange", {}, None), ("cock", {}, None), ("cock", {"open": True}, None), ("wheel", {"radius": 600}, None),
    ("gear", {"radius": 300}, None), ("beam", {"length": 3000, "depth": 300, "pivot": 0}, None),
    ("chain", {"points": [(0, 1000), (300, 400), (500, 0)]}, None), ("rope", {"points": [(0, 1000), (100, 0)]}, None),
    ("cylinder", {"bore": 100, "length": 250, "wall": 8, "cut": True}, None), ("piston", {"diameter": 100, "thickness": 40, "rod": 300}, None),
    ("break_line", {"x0": 0, "x1": 800, "y": 0}, None), ("fire", {}, None), ("steam", {}, None),
    ("sky", {"x0": 0, "x1": 3000, "horizon": 0, "top": 1500}, "day"), ("sky", {"x0": 0, "x1": 3000, "horizon": 0, "top": 1500}, "night"),
    ("rain", {"x0": 0, "x1": 3000, "y0": 0, "y1": 1500}, "day"), ("lantern", {}, "night"),
]


def night_scene(p):
    """A lantern by a barrel, at night: the dark wash with a pool of light."""
    stock.ground(p, -1500, 1500, "floor")
    stock.barrel(p)
    p.part(stock.lantern, at=(700, 2000))
    stock.night(p, -1500, -250, 1500, 2200, lights=[(700, 1700, 900)])


def at_time(svg, phase):
    """Keep only the groups for one time of day, as the view would."""
    root = ElementTree.fromstring(svg)
    for parent in list(root.iter()):
        for el in list(parent):
            if el.get("data-sky") and phase not in el.get("data-sky").split():
                parent.remove(el)
    return ElementTree.tostring(root, encoding="unicode")


def call(name, kw):
    return f"{name}(p{''.join(f', {k}={v!r}' for k, v in kw.items())})"


cells = []
for name, kw, phase in CALLS + [("night_scene", {}, "night")]:
    fn = night_scene if name == "night_scene" else getattr(stock, name)
    s = Sheet(f"stock-{name}", name.replace("_", " "), "lantern, barrel and night(...)" if name == "night_scene" else call(name, kw), size=(520, 340))
    s.place(lambda p: fn(p, **kw))
    svg = s.svg()
    cells.append(at_time(svg, phase) if phase else svg)

html = ("<body style='margin:0;background:#f2e8d2'><div style='display:grid;grid-template-columns:repeat(5,520px);gap:6px;padding:6px'>"
        + "".join(f"<div style='background:#f8f1e1;height:340px'>{c}</div>" for c in cells) + "</div></body>")
out = Path(__file__).with_name("stock.png")
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 5 * 526 + 6, "height": 400})
    page.set_content(html)
    page.wait_for_timeout(300)
    page.screenshot(path=out, full_page=True)
    browser.close()
print(out)
