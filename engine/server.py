"""Live view server: the web UI, the save's state as JSON, change events, sketch uploads, screenshots."""
import base64
import json
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from . import state

WEB = state.ROOT / "web"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, save, **kwargs):
        self.save = save
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/api/state":
            return self.send_json(state.load_state(self.save))
        if route == "/api/events":
            return self.stream_changes()
        if route.startswith("/save/"):  # files inside the save: visuals, maps, sketches, fermi scripts
            if route == "/save/secret.md" or "/." in route:  # the referee's secrets and history stay private
                return self.send_error(404)
            self.directory, self.path = str(self.save), self.path.removeprefix("/save")
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/sketch":
            return self.send_error(404)
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        folder = self.save / "sketches"
        folder.mkdir(exist_ok=True)
        n = max((int(p.stem) for p in folder.glob("*.png") if p.stem.isdigit()), default=0) + 1
        path = folder / f"{n:04d}.png"
        path.write_bytes(base64.b64decode(body["png"].split(",", 1)[1]))
        self.send_json({"path": f"sketches/{path.name}"})

    def stream_changes(self):
        """Server-sent events: one 'change' message whenever a file in the save changes."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        last = None
        try:
            while True:
                sig = state.signature(self.save)
                if sig != last:
                    self.wfile.write(b"data: change\n\n")
                    self.wfile.flush()
                    last = sig
                time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError):
            pass  # browser tab closed or reloaded

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_request(self, *args):
        pass  # quiet; errors still go to stderr


def make_server(save, port):
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, save=save))
    server.daemon_threads = True
    return server


def shot(save, target, visual_state=None, sheet=False):
    """Render a view with headless Chromium and return the PNG path."""
    from playwright.sync_api import sync_playwright

    server = make_server(save, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    tab = (target in ("workshop", "capabilities", "people", "map", "journal", "sketch") or "/" in target) and not sheet
    route = f"#/{target}" if tab else f"#/{'thing' if sheet else 'visual'}/{target}"
    if visual_state:
        route += f"?state={visual_state}"
    out = save / ".shots" / f"{target.replace('/', '-')}{'-sheet' if sheet else ''}{'-' + visual_state if visual_state else ''}.png"
    out.parent.mkdir(exist_ok=True)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/{route}")
        page.wait_for_function("document.body.dataset.ready === '1'", timeout=15000)
        page.screenshot(path=out, full_page=tab or sheet)
        browser.close()
    server.shutdown()
    for e in errors:
        print(f"page error: {e}", file=sys.stderr)
    return out
