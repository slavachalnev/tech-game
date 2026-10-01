"""Smoke test for the live view: every page renders a well-populated save without JavaScript errors."""
import threading

import pytest
from playwright.sync_api import sync_playwright

from engine import history, state
from engine.server import make_server

ROUTES = ["workshop", "board/anvil", "capabilities", "people", "map", "map/region", "journal", "sketch",
          "thing/wheal-fortune", "thing/smithy?state=fire-lit", "thing/anvil", "visual/scene-yard",
          "visual/smithy?hotspots", "visual/smithy?state=night"]


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:  # one per module: the sync API can't run two at once
        browser = p.chromium.launch()
        yield browser
        browser.close()


def open_page(browser, save, route):
    """Serve `save`, open a route, wait until the view says it's ready, and return (page, JS errors)."""
    server = make_server(save, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://127.0.0.1:{server.server_address[1]}/#/{route}")
    page.wait_for_function("document.body.dataset.ready === '1'", timeout=10000)
    return page, errors


@pytest.fixture(scope="module")
def full_save(tmp_path_factory):
    """A save with some of everything: a turn with illustrations, a recipe, stores, a scene."""
    saves = tmp_path_factory.mktemp("saves")
    state.SAVES, old = saves, state.SAVES
    save = state.new_save("cornwall-1705", "view")
    state.SAVES = old
    (save / "visuals/scene-yard.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><text x="10" y="20">Yard</text></svg>')
    state.write_json(save / "stores.json", {"items": [{"name": "Scrap brass", "quantity": 20, "unit": "kg"}]})
    state.write_json(save / "recipes/hoops.json", {
        "id": "hoops", "name": "Forge iron hoops", "makes": "hoops", "how": "bend and weld", "tools": ["anvil"],
        "people": ["jacca-pascoe"], "time": "1 day", "cost_p": 30, "quality": {"roundness_mm": 5}, "historical_year": 1800})
    state.write_json(save / "log/0001.json", {
        "turn": 1, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T08:00", "action": "Walk to Wheal Fortune.",
        "rulings": ["ok"], "narration": "You reach Wheal Fortune.", "visuals": ["visuals/scene-yard.svg", "visuals/anvil.svg"],
        "measurements": [{"title": "Hammer rebound", "thing": "anvil", "x": "blow", "y": "rebound (cm)", "series": [
            {"name": "cold", "points": [[1, 12], [2, 11.5], [3, 11]]}, {"name": "warm", "points": [[1, 9], [2, 9], [3, 8.5]]}]}]})
    assert state.check_save(save) == []
    return save


@pytest.mark.parametrize("route", ROUTES)
def test_page_renders_without_errors(browser, full_save, route):
    page, errors = open_page(browser, full_save, route)
    assert errors == []
    assert "No drawing for" not in page.inner_text("body")


def test_trials_are_plotted_in_the_journal_and_on_the_sheet(browser, full_save):
    for route in ("journal", "thing/anvil"):
        page, errors = open_page(browser, full_save, route)
        assert page.locator(".chart polyline").count() == 2 and errors == []
        assert "Hammer rebound" in page.inner_text(".chart figcaption")


def test_workshop_shows_what_is_coming_up_and_recent_drawings(browser, full_save):
    page, errors = open_page(browser, full_save, "workshop")
    assert "24 June" in page.inner_text(".almanac") and page.locator(".recent img").count() == 4 and errors == []


def test_the_workshop_is_a_drawing_board_of_machines_and_their_parts(browser, full_save):
    page, errors = open_page(browser, full_save, "workshop")
    page.wait_for_selector(".board-svg .plate")
    page.locator("#board .board-keys [data-k=all]").click()  # the whole sheet, then into the smithy's drawing
    page.wait_for_timeout(900)
    box = page.evaluate("(() => { const r = document.querySelector('.plate[data-id=smithy] image').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    page.mouse.click(*box)
    page.wait_for_function("document.querySelector('.board-panel h3')?.textContent === 'The smithy'", timeout=5000)
    assert page.locator(".board-overlay .balloon").count() == 7  # its forge and anvil, and the five other things in it
    assert "Hearth and bellows" in page.inner_text(".bom")
    page.locator(".balloon[data-id=anvil]").dispatch_event("click")  # the anvil's own drawing opens in place
    page.wait_for_function("document.querySelector('.board-trail').textContent.includes('Anvil')", timeout=5000)
    assert "The smithy › Anvil" in page.inner_text(".board-trail") and errors == []


def test_old_journal_entries_show_drawings_as_they_were(browser, tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "old")
    history.snapshot(save)
    for n in (1, 2):
        (save / "visuals/scene-yard.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 60"><text y="20">version {n}</text></svg>')
        state.write_json(save / f"log/{n:04d}.json", {"turn": n, "clock_start": "1705-04-02T08:00", "clock_end": "1705-04-02T08:00",
                                                     "action": "a", "rulings": [], "narration": "n", "visuals": ["visuals/scene-yard.svg"]})
        history.snapshot(save)
    page, errors = open_page(browser, save, "journal")
    shown = page.evaluate("Promise.all([...document.querySelectorAll('.entry .illus img')].map(async (i) => (await fetch(i.src)).text()))")
    assert ["version 2" in shown[0], "version 1" in shown[1]] == [True, True] and errors == []


def test_map_labels_open_place_cards(browser, full_save):
    page, errors = open_page(browser, full_save, "map/district")
    page.locator(".map-host text.place", has_text="Wheal Fortune").first.click()
    assert "Captain Richard Tregonning" in page.inner_text(".place-card") and errors == []


def test_broken_world_shows_the_problems(browser, tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SAVES", tmp_path)
    save = state.new_save("cornwall-1705", "broken")
    (save / "world.json").write_text('{"scenario": "cornwall-1705"}')
    page, errors = open_page(browser, save, "workshop")
    assert errors == [] and "world.json" in page.inner_text("#problems")
    assert "world.json is broken" in page.inner_text("main")
