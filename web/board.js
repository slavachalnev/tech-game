// The drawing board: every drawing laid out on one sheet you zoom through like a map. A part with its own
// drawing opens in place: zoom in on it and its drawing grows out of a detail circle, lined up over it (by the
// drawings' [data-object] outlines), while the machine around it recedes. Balloons and a parts list say what can
// be opened. Drawings are shown as images; the board only measures them once.

const OPEN = [0.3, 0.78]; // a detail opens as its drawing grows from this share of the screen to this one
const FOCUS = 0.45; // a drawing on the sheet is in focus once it fills this share of the screen
// Where a part stands, for its look on the drawing and its balloon: in hand, being made, on its way, or planned.
function standing(t) {
  if (!t) return "none";
  if (["broken", "faulty"].includes(t.status)) return "faulty";
  if (["ordered", "in transit"].includes(t.state)) return "coming";
  return { planned: "planned", building: "making" }[t.status] ?? "ok";
}
const STANDING = { ok: "in hand", making: "being made", coming: "on its way", planned: "planned", faulty: "faulty" };

export function createBoard(host, h) {
  host.innerHTML = `<svg class="board-svg"><defs></defs><g class="plates"></g><g class="details"></g></svg>
    <svg class="board-overlay"></svg>
    <nav class="board-trail"></nav>
    <aside class="board-panel"></aside>
    <div class="tag" hidden></div>
    <div class="board-keys"><button data-k="out" title="Zoom out (or Escape)">−</button><button data-k="in" title="Zoom in">+</button><button data-k="all" title="The whole board">⤢</button></div>`;
  const svg = host.querySelector(".board-svg"), defs = svg.querySelector("defs"), platesG = svg.querySelector(".plates"), detailsG = svg.querySelector(".details");
  const overlay = host.querySelector(".board-overlay"), trailEl = host.querySelector(".board-trail"), panel = host.querySelector(".board-panel"), tag = host.querySelector(".tag");
  const sandbox = Object.assign(document.createElement("div"), { style: "position:fixed;left:-30000px;top:0;width:2000px;height:2000px;visibility:hidden" });
  document.body.append(sandbox);

  let S = null, roots = [], cam = null, path = [], focus = null, hover = null, frameAsked = false, panelKey = "", playing = null;
  let selected = null; // a part without a drawing of its own: its sheet is shown in the panel
  let closing = null; // the detail being closed as the camera backs out of it: { key, parentKey }
  let growing = null; // the detail being opened with a click, as the camera flies into it
  let quiet = false; // after a flight or jump nothing opens by itself, until you zoom in (dragging is only looking around)
  let aim = null; // where on the screen you're zooming at with the wheel; else the middle of the clear part
  let zoomedOut = null, sheetW = 1; // whether the camera takes in most of the sheet; the sheet's width
  const view = {}; // thing id -> { state, step } the player chose to look at, else its current state and step 1
  const measured = new Map(); // drawing key -> promise of { url, vb, object, parts }
  const children = new Map(), measuring = new Set(); // node key -> child node; keys being measured
  const opened = new Map(); // node key -> the child open in it: it stays open while you're inside its drawing
  const things = () => Object.fromEntries(S.things.map((t) => [t.id, t]));

  // ---------- drawings ----------

  const boxIn = (el, root) => {
    const b = el.getBBox(), m = root.getScreenCTM().inverse().multiply(el.getScreenCTM());
    const pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]].map(([x, y]) => new DOMPoint(x, y).matrixTransform(m));
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  };

  const stateFor = (t) => view[t.id]?.state ?? h.stateOf(t);
  // A thing's sheets: its drawing, then any others (visuals/<id>--how-it-works.svg, say), each with a name.
  const sheetsOf = (t) => [t.visual, ...Object.keys(S.visuals).filter((p) => p.startsWith(`visuals/${t.id}--`)).sort()].filter((p) => p && S.visuals[p]);
  const sheetName = (path) => (path.includes("--") ? path.slice(path.indexOf("--") + 2, -4).replace(/-/g, " ").replace(/^./, (c) => c.toUpperCase()) : "Drawing");
  const sheetFor = (t) => (sheetsOf(t).includes(view[t.id]?.sheet) ? view[t.id].sheet : sheetsOf(t)[0]);
  // A blank sheet for a thing that hasn't been drawn yet: its name and its kind's mark.
  const blank = (t) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" font-family="Georgia, serif">
    <rect x="30" y="30" width="740" height="540" fill="none" stroke="#b9a888" stroke-width="2" stroke-dasharray="14 8"/>
    <g data-object=""><g fill="none" stroke="#7a6a55" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round" opacity="0.7" transform="translate(304 150) scale(4)">${h.glyph(t.kind)}</g></g>
    <text x="400" y="420" font-size="34" font-variant="small-caps" text-anchor="middle" fill="#4a3d2e">${h.esc(t.name)}</text>
    <text x="400" y="462" font-size="22" font-style="italic" text-anchor="middle" fill="#7a6a55">not drawn yet</text></svg>`;

  // A thing's sheet prepared for the board, in the state and step being looked at: parts not in hand drawn as
  // blueprint ghosts, on squared paper; measured.
  function measure(item) {
    const all = things(), state = stateFor(item), step = view[item.id]?.step ?? 1, path = sheetFor(item);
    const key = `${path ?? "blank:" + item.id}@${S.visuals[path]}@${state}@${step}@${S.things.map((t) => standing(t)[0]).join("")}`;
    if (!measured.has(key)) measured.set(key, (async () => {
      const text = path ? await h.svgText({ visual: path, _v: S.visuals[path] }) : blank(item);
      const svg = h.prepare(text, state, { self: item.id });
      const steps = [...svg.querySelectorAll("[data-step]")], n = Math.max(0, ...steps.map((g) => +g.dataset.step));
      const captions = Array.from({ length: n }, (_, i) => steps.find((g) => +g.dataset.step === i + 1 && g.dataset.caption)?.dataset.caption ?? "");
      steps.forEach((g) => +g.dataset.step !== step && g.remove()); // one step at a time
      const vb = (svg.getAttribute("viewBox") ?? "0 0 800 600").split(/[\s,]+/).map(Number);
      svg.querySelectorAll("[data-thing]").forEach((el) => el.setAttribute("data-standing", standing(all[el.getAttribute("data-thing")])));
      svg.insertAdjacentHTML("afterbegin", `<style>
          [data-standing=planned] *, [data-standing=coming] * { stroke: #4f7390 !important; fill: rgba(79,115,144,0.07) !important; stroke-dasharray: 7 4; filter: none !important; }
          [data-standing=planned] text, [data-standing=coming] text { fill: #4f7390 !important; stroke: none !important; }
          [data-standing=coming] * { stroke-dasharray: 2 3; }
        </style>
        <defs><pattern id="board-grid" width="${vb[2] / 57}" height="${vb[2] / 57}" patternUnits="userSpaceOnUse"><path d="M${vb[2] / 57} 0V${vb[2] / 57}H0" fill="none" stroke="rgba(122,106,85,0.14)" stroke-width="${vb[2] / 800}"/></pattern></defs>
        <rect x="${vb[0]}" y="${vb[1]}" width="${vb[2]}" height="${vb[3]}" fill="#f8f1e1"/><rect x="${vb[0]}" y="${vb[1]}" width="${vb[2]}" height="${vb[3]}" fill="url(#board-grid)"/>`);
      svg.setAttribute("width", vb[2]), svg.setAttribute("height", vb[3]);
      sandbox.append(svg);
      const obj = svg.querySelector("[data-object]");
      const pieces = [...svg.querySelectorAll("[data-thing]")].map((el) => ({ id: el.getAttribute("data-thing"), box: boxIn(el, svg) })).filter((p) => p.box.w && all[p.id]);
      const data = { blank: !path, states: text.includes("data-state="), captions, sounds: [...svg.querySelectorAll("[data-sound]")].map((g) => g.dataset.sound), vb, object: obj && boxIn(obj, svg), parts: joined(pieces) };
      svg.remove();
      data.url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" }));
      return data;
    })());
    return measured.get(key);
  }

  // Pieces of one part that touch (a pump's tub, rod and pipe) make one outline; separate views of it (the
  // cylinder in the engine and again in its inset) stay separate.
  function joined(pieces) {
    const near = (a, b) => { const m = Math.max(a.w, a.h, b.w, b.h) * 0.05; return a.x - m < b.x + b.w && b.x - m < a.x + a.w && a.y - m < b.y + b.h && b.y - m < a.y + a.h; };
    const union = (a, b) => { const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y); return { x, y, w: Math.max(a.x + a.w, b.x + b.w) - x, h: Math.max(a.y + a.h, b.y + b.h) - y }; };
    const out = [];
    for (const p of pieces) {
      let box = p.box;
      for (let merged = true; merged; ) {
        merged = false;
        for (const q of out.filter((q) => q.id === p.id && near(q.box, box))) (box = union(box, q.box)), out.splice(out.indexOf(q), 1), (merged = true);
      }
      out.push({ id: p.id, box });
    }
    return out;
  }

  // ---------- nodes: drawings placed on the board ----------
  // A node's drawing maps onto the board by board = local * k + t; its rect is its whole drawing on the board.

  const toBoard = (T, b) => ({ x: b.x * T.k + T.tx, y: b.y * T.k + T.ty, w: b.w * T.k, h: b.h * T.k });
  const vbBox = (vb) => ({ x: vb[0], y: vb[1], w: vb[2], h: vb[3] });

  // The drawing of a part, lined up over where its machine's drawing shows it.
  // Measured once per state of the game; after a change, the old one shows until the new one is ready.
  function child(node, part) {
    const key = `${node.key}>${part.id}@${Math.round(part.box.x)},${Math.round(part.box.y)}`, have = children.get(key);
    if (have && !have.stale) return have;
    if (!measuring.has(key)) {
      const t = things()[part.id];
      measuring.add(key);
      measure(t).then((data) => {
        const O = data.object ?? vbBox(data.vb), B = part.box, s = Math.min(B.w / O.w, B.h / O.h);
        const T = { k: node.T.k * s, tx: node.T.k * (B.x + B.w / 2 - (O.x + O.w / 2) * s) + node.T.tx, ty: node.T.k * (B.y + B.h / 2 - (O.y + O.h / 2) * s) + node.T.ty };
        children.set(key, { key, id: part.id, thing: t, data, T, rect: toBoard(T, vbBox(data.vb)), part: toBoard(node.T, B), local: B, parent: node });
        measuring.delete(key);
        ask();
      });
    }
    return have ?? null;
  }

  // What can be opened from a node: the parts marked in its drawing, and the parts drawn inside it in the drawings
  // above (the piston, drawn inside the cylinder in the engine's drawing, opens from the cylinder). Boxes on the board.
  function candidates(node) {
    const own = node.data.parts.filter((p) => p.id !== node.id).map((p) => ({ id: p.id, local: p.box, box: toBoard(node.T, p.box), owner: node }));
    if (!node.parent) return own;
    return [...own, ...candidates(node.parent).filter((c) => c.id !== node.id && within(c.box, node.part))];
  }
  const within = (b, r) => { // mostly inside, and smaller
    const w = Math.min(b.x + b.w, r.x + r.w) - Math.max(b.x, r.x), hh = Math.min(b.y + b.h, r.y + r.h) - Math.max(b.y, r.y);
    return w > 0 && hh > 0 && (w * hh) / (b.w * b.h) >= 0.6 && b.w * b.h < r.w * r.h;
  };

  // Lay the top-level drawings out on the sheet, a section each: the project first and largest, then engines and
  // models, buildings and sites, spare parts, tools, materials, papers.
  const SECTIONS = [["The project", 3000], ["Engines and models", 1700], ["Buildings and sites", 1300], ["Spare parts", 950], ["Tools", 700], ["Materials", 700], ["Papers", 700], ["Used up or gone", 600]];
  const sectionOf = (t) => (t.status === "consumed" ? 7 : t.kind === "machine" && ["building", "planned"].includes(t.status) ? 0 : { machine: 1, structure: 2, site: 2, component: 3, tool: 4, material: 5 }[t.kind] ?? 6);
  async function layout() { // every thing has a place: on its own sheet, or inside the sheet of what it's part of
    const fitted = new Set(S.things.flatMap((t) => t.components ?? [])), section = sectionOf;
    const tops = S.things.filter((t) => !fitted.has(t.id));
    const datas = new Map(await Promise.all(tops.map(async (t) => [t, await measure(t)])));
    // Each section is a block of rows; blocks go into three columns, each into the shortest so far.
    const COL = 3600, GAP = 140, cols = [0, 0, 0], heads = [];
    roots = SECTIONS.flatMap(([title, w], sec) => {
      const mine = tops.filter((t) => section(t) === sec);
      if (!mine.length) return [];
      const c = cols.indexOf(Math.min(...cols)), x0 = c * (COL + 260), y0 = cols[c];
      heads.push(`<text class="section-title" x="${x0}" y="${y0 + 100}" font-size="110">${h.esc(title)}</text>`);
      let x = 0, y = 170, rowH = 0;
      const nodes = mine.map((t) => {
        const data = datas.get(t), vb = data.vb, hgt = (w * vb[3]) / vb[2];
        if (x > 0 && x + w > COL) (x = 0), (y += rowH + GAP + 90), (rowH = 0);
        const rect = { x: x0 + x, y: y0 + y, w, h: hgt }, k = w / vb[2];
        (x += w + GAP), (rowH = Math.max(rowH, hgt));
        return { key: t.id, id: t.id, thing: t, data, section: title, T: { k, tx: rect.x - vb[0] * k, ty: rect.y - vb[1] * k }, rect };
      });
      cols[c] = y0 + y + rowH + 260;
      return nodes;
    });
    sheetW = sheet().w;
    platesG.innerHTML = roots.map((n) => `<g class="plate" data-id="${h.esc(n.id)}">
        <rect class="plate-shadow" x="${n.rect.x + 8}" y="${n.rect.y + 10}" width="${n.rect.w}" height="${n.rect.h}"/>
        <image href="${n.data.url}" x="${n.rect.x}" y="${n.rect.y}" width="${n.rect.w}" height="${n.rect.h}" preserveAspectRatio="none"/>
        <rect class="plate-edge" x="${n.rect.x}" y="${n.rect.y}" width="${n.rect.w}" height="${n.rect.h}"/>
        <text class="plate-title" x="${n.rect.x}" y="${n.rect.y + n.rect.h + 64}" font-size="${Math.max(44, n.rect.w / 28)}">${h.esc(n.thing.name)}</text>
      </g>`).join("") + heads.join("");
  }
  const sheet = () => {
    const xs = roots.flatMap((n) => [n.rect.x, n.rect.x + n.rect.w]), ys = roots.flatMap((n) => [n.rect.y - 200, n.rect.y + n.rect.h + 140]);
    return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  };

  // ---------- the camera ----------

  const size = () => [host.clientWidth || 1, host.clientHeight || 1];
  // The part of the screen the panel doesn't cover: left of it on a wide screen, above it on a phone.
  function clear() {
    const [W, H] = size(), p = panel.getBoundingClientRect(), b = host.getBoundingClientRect(), L = h.cover();
    if (!panel.offsetWidth) return { x: L, y: 0, w: W - L, h: H };
    return p.left - b.left > W / 3 ? { x: L, y: 0, w: p.left - b.left - 16 - L, h: H } : { x: 0, y: 0, w: W, h: p.top - b.top - 8 };
  }
  function framed(r, fill = 0.92) { // a camera showing rect r in the clear part of the screen, filling `fill` of it
    const [W, H] = size(), a = clear(), u = Math.max(r.w / (fill * a.w), r.h / (fill * a.h)); // board units per pixel
    return [r.x + r.w / 2 - (a.x + a.w / 2) * u, r.y + r.h / 2 - (a.y + a.h / 2) * u, W * u, H * u];
  }
  let flight = null;
  function fly(to, ms = 750) {
    if (!ms) return (quiet = true), (aim = null), (cam = to), draw(), Promise.resolve(); // a jump, like a flight: nothing opens by itself
    let landed;
    (quiet = true), (aim = null);
    const done = new Promise((r) => (landed = r)), from = cam.slice(), t0 = performance.now(), id = (flight = { e: 0 });
    // Fly in log space for the zoom, so a deep zoom doesn't rush the last part.
    const step = (now) => {
      if (flight !== id) return;
      const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2;
      const w = from[2] * (to[2] / from[2]) ** e, f = (w - from[2]) / (to[2] - from[2] || 1);
      const cx = from[0] + from[2] / 2 + (to[0] + to[2] / 2 - from[0] - from[2] / 2) * (Number.isFinite(f) ? f : e);
      const cy = from[1] + from[3] / 2 + (to[1] + to[3] / 2 - from[1] - from[3] / 2) * (Number.isFinite(f) ? f : e);
      const hh = (w * to[3]) / to[2];
      (cam = [cx - w / 2, cy - hh / 2, w, hh]), (id.e = e);
      if (k >= 1) { // landed: a detail being closed is now shut
        if (closing?.parentKey) opened.delete(closing.parentKey);
        (closing = null), (growing = null), (flight = null);
      }
      draw();
      k < 1 ? requestAnimationFrame(step) : landed();
    };
    requestAnimationFrame(step);
    return done;
  }
  // Zoom about a point on the screen, but not more than three times past the deepest drawing there: no blank paper.
  const zoom = (factor, sx, sy) => {
    const [W, H] = size(), x = cam[0] + (sx / W) * cam[2], y = cam[1] + (sy / H) * cam[3];
    const deep = path.at(-1)?.node, under = deep && candidates(deep).filter((p) => things()[p.id]?.visual && inside(p.box, x, y)).sort((a, b) => a.box.w * a.box.h - b.box.w * b.box.h)[0];
    const limit = (under && child(under.owner, { id: under.id, box: under.local })) ?? deep ?? roots.find((r) => inside(r.rect, x, y));
    const most = limit ? fill(limit.rect) / 3 : Math.min(...roots.map(fill)) / 2; // the smallest factor allowed
    if (factor < 1 && factor < most) factor = Math.min(1, most);
    cam = [x - (x - cam[0]) * factor, y - (y - cam[1]) * factor, cam[2] * factor, cam[3] * factor];
    ask();
  };
  const atScreen = (sx, sy) => { const [W, H] = size(); return [cam[0] + (sx / W) * cam[2], cam[1] + (sy / H) * cam[3]]; };
  const onScreen = (x, y) => { const [W, H] = size(); return [((x - cam[0]) / cam[2]) * W, ((y - cam[1]) / cam[3]) * H]; };
  const fill = (r) => { const a = clear(), u = cam[2] / size()[0]; return Math.max(r.w / (a.w * u), r.h / (a.h * u)); };
  const inside = (r, x, y, slack = 0) => x >= r.x - slack && x <= r.x + r.w + slack && y >= r.y - slack && y <= r.y + r.h + slack;
  const clamp = (v) => Math.max(0, Math.min(1, v));

  // ---------- drawing a frame ----------

  function ask() {
    if (frameAsked) return;
    frameAsked = true;
    requestAnimationFrame(() => ((frameAsked = false), draw()));
  }

  // What the camera is looking into: a drawing on the sheet, then the part under the middle of the screen whose
  // drawing is opening, and so on down.
  // How far a part's drawing has opened, 0 to 1, by how far you've zoomed into the drawing it's in: nothing at that
  // drawing's own framing, starting a quarter past it, fully open just before the part's drawing fills the view. A
  // part whose drawing is about as big as the one it's in can't grow by zooming: it's open only when framed (click).
  function opening(node, c) {
    const F = fill(node.rect), size = fill(c.rect) / F; // the part's sheet against the drawing it's in, at any zoom
    const start = 0.92 * 1.25, end = OPEN[1] / size; // fills of the drawing it's in
    if (end <= start * 1.1) return fill(c.rect) >= OPEN[1] ? 1 : 0;
    return clamp(Math.log(F / start) / Math.log(end / start));
  }

  function walk() {
    const a = clear(), [cx, cy] = aim ? atScreen(...aim) : atScreen(a.x + a.w / 2, a.y + a.h / 2);
    const was = path[0]?.node, margin = (n) => Math.max(n.rect.w, n.rect.h) * 0.08; // the drawing in focus holds on a little
    const root = was && roots.includes(was) && inside(was.rect, cx, cy, margin(was)) && fill(was.rect) >= FOCUS * 0.8 ? was
      : roots.find((n) => inside(n.rect, cx, cy) && fill(n.rect) >= FOCUS);
    const out = root ? [{ node: root, p: 1 }] : [];
    for (let node = root; node; ) {
      // The child already open stays open while you're inside its drawing. Else the smallest part you're zooming at
      // opens, but not one with other parts drawn over much of it (an engine house, a cylinder with its piston):
      // zooming in on those is zooming toward what's inside, so they open on a click.
      let c = opened.get(node.key);
      if (c) c = child(nodeByKey(c.parent.key) ?? c.parent, { id: c.id, box: c.local }) ?? c; // the fresh one, after a change
      if (c && !inside(c.rect, cx, cy) && c.key !== closing?.key) c = null; // you've moved out of it
      if (!c && !quiet) {
        const cands = candidates(node), area = (b) => b.w * b.h;
        const holds = (p) => cands.filter((q) => q.id !== p.id && within(q.box, p.box)).reduce((sum, q) => sum + area(q.box), 0) > 0.25 * area(p.box);
        const part = cands.filter((p) => things()[p.id]?.visual && things()[p.id]?._v && inside(p.box, cx, cy) && !holds(p)).sort((a, b) => area(a.box) - area(b.box))[0];
        c = part && child(part.owner, { id: part.id, box: part.local });
      }
      if (!c) break;
      let p = opening(node, c);
      if (c.key === growing?.key) p = Math.max(p, flight?.e ?? 1); // opened with a click: growing as the camera flies in
      if (c.key === closing?.key) p = Math.min(p, 1 - (flight?.e ?? 1)); // shrinking away as the camera backs out
      if (p <= 0) { if (!flight) opened.delete(node.key); break; } // zoomed back out of it (not on the way in)
      opened.set(node.key, c);
      out.push({ node: c, p });
      node = p >= 1 ? c : null;
    }
    return out;
  }

  function draw() {
    if (!cam) return;
    svg.setAttribute("viewBox", cam.join(" "));
    path = walk();
    const was = focus;
    focus = [...path].reverse().find((e) => e.p >= 1)?.node ?? null;
    // Each drawing on the path recedes as the one inside it opens.
    platesG.querySelectorAll(".plate").forEach((g) => (g.style.opacity = g.dataset.id === path[0]?.node.id && path[1] ? 1 - 0.7 * path[1].p : 1));
    const keep = new Set();
    path.slice(1).forEach(({ node, p }, i) => {
      const id = `d-${btoa(node.key).replace(/[^a-z0-9]/gi, "")}`, next = path[i + 2];
      keep.add(id);
      let g = detailsG.querySelector(`#${id}`);
      if (!g) {
        detailsG.insertAdjacentHTML("beforeend", `<g id="${id}"><clipPath id="${id}-clip"><circle/></clipPath>
          <g clip-path="url(#${id}-clip)"><image href="${node.data.url}" x="${node.rect.x}" y="${node.rect.y}" width="${node.rect.w}" height="${node.rect.h}" preserveAspectRatio="none"/></g>
          <circle class="detail-edge" fill="none" vector-effect="non-scaling-stroke"/></g>`);
        g = detailsG.querySelector(`#${id}`);
      }
      const P = node.part, cx = P.x + P.w / 2, cy = P.y + P.h / 2, r0 = Math.hypot(P.w, P.h) * 0.62;
      const rFull = Math.max(...[[node.rect.x, node.rect.y], [node.rect.x + node.rect.w, node.rect.y], [node.rect.x, node.rect.y + node.rect.h], [node.rect.x + node.rect.w, node.rect.y + node.rect.h]].map(([x, y]) => Math.hypot(x - cx, y - cy)));
      const e = 1 - (1 - p) ** 2, r = r0 + (rFull - r0) * e;
      g.querySelectorAll("circle").forEach((c) => (c.setAttribute("cx", cx), c.setAttribute("cy", cy), c.setAttribute("r", r)));
      const img = g.querySelector("image");
      if (img.getAttribute("href") !== node.data.url) img.setAttribute("href", node.data.url); // another state or step
      g.querySelector(".detail-edge").style.opacity = p < 1 ? 1 : 0;
      g.querySelector("image").style.opacity = next ? 1 - 0.7 * next.p : 1;
      g.style.opacity = Math.min(1, p * 3);
    });
    detailsG.querySelectorAll(":scope > g").forEach((g) => keep.has(g.id) || g.remove());
    if (was !== focus) (hover = null), (selected = null), h.sounds(focus?.data.sounds ?? []); // what you'd hear there
    // Your papers are out when you've zoomed out to most of the sheet and away when you're in close: by zoom, with
    // some slack, never by focus (opening them moves the middle of the view, and so the focus).
    const far = cam[2] > sheetW * (zoomedOut ? 0.4 : 0.55);
    if (far !== zoomedOut) (zoomedOut = far), h.desk(far);
    drawOverlay();
    if (focus !== was || panelKey !== `${focus?.key ?? ""}|${selected ?? ""}`) showPanel();
  }

  // ---------- balloons and the parts list ----------

  // The parts of the drawing in focus, numbered as in its parts list: its components first, in their order, then
  // anything else drawn in it.
  function partsOf(node) {
    if (!node) return [];
    const all = things(), cands = candidates(node);
    const order = [...(node.thing.components ?? []), ...cands.map((c) => c.id)].filter((id, i, a) => a.indexOf(id) === i && id !== node.id);
    return order.map((id, i) => ({ n: i + 1, id, thing: all[id], cands: cands.filter((c) => c.id === id), boxes: cands.filter((c) => c.id === id).map((c) => c.box) })).filter((p) => p.thing);
  }

  function drawOverlay() {
    const [W, H] = size(), parts = partsOf(focus), marks = [];
    const screen = (r) => { const [x, y] = onScreen(r.x, r.y), [x2, y2] = onScreen(r.x + r.w, r.y + r.h); return { x, y, w: x2 - x, h: y2 - y }; };
    const fc = focus && screen(focus.rect), mid = fc ? [fc.x + fc.w / 2, fc.y + fc.h / 2] : [W / 2, H / 2];
    // Balloons sit just outside their part, away from the middle of the drawing, nudged apart.
    const balloons = parts.filter((p) => p.boxes.length).map((p) => {
      const b = screen(p.boxes.reduce((a, c) => (c.w * c.h > a.w * a.h ? c : a))), ax = b.x + b.w / 2, ay = b.y + b.h / 2;
      let dx = ax - mid[0], dy = ay - mid[1];
      const len = Math.hypot(dx, dy) || 1;
      (dx /= len), (dy /= len);
      const reach = Math.min(Math.abs(b.w / 2 / (dx || 1e-9)), Math.abs(b.h / 2 / (dy || 1e-9))) + 26;
      return { p, b, ax, ay, x: ax + dx * reach, y: ay + dy * reach };
    });
    for (let k = 0; k < 40; k++) for (const a of balloons) for (const c of balloons) {
      if (a === c) continue;
      const dx = a.x - c.x, dy = a.y - c.y, d = Math.hypot(dx, dy);
      if (d < 28) (a.x += ((dx || 1) / (d || 1)) * (28 - d) * 0.5), (a.y += ((dy || 1) / (d || 1)) * (28 - d) * 0.5);
    }
    balloons.forEach((a) => ((a.x = Math.max(16, Math.min(W - 16, a.x))), (a.y = Math.max(16, Math.min(H - 16, a.y)))));
    for (const { p, b, ax, ay, x, y } of balloons) {
      const hot = hover === p.id || selected === p.id, opens = !!(p.thing.visual && p.thing._v), st = standing(p.thing);
      const ex = Math.max(b.x, Math.min(b.x + b.w, x)), ey = Math.max(b.y, Math.min(b.y + b.h, y)); // where the leader meets the part
      if (opens && hot) marks.push(`<ellipse class="detail-mark hot" cx="${ax}" cy="${ay}" rx="${b.w * 0.62 + 6}" ry="${b.h * 0.62 + 6}"/>`);
      if (hot) marks.push(...p.boxes.map(screen).map((r) => `<rect class="part-hot" x="${r.x - 4}" y="${r.y - 4}" width="${r.w + 8}" height="${r.h + 8}" rx="6"/>`));
      marks.push(`<g class="balloon ${st}${hot ? " hot" : ""}${opens ? " opens" : ""}" data-id="${h.esc(p.id)}"><line x1="${x}" y1="${y}" x2="${ex}" y2="${ey}"/><circle cx="${x}" cy="${y}" r="12"/><text x="${x}" y="${y + 5}">${p.n}</text></g>`);
    }
    if (!focus && hover) { // on the sheet: the drawing under the pointer
      const n = roots.find((r) => r.id === hover);
      if (n) { const r = screen(n.rect); marks.push(`<rect class="part-hot" x="${r.x - 6}" y="${r.y - 6}" width="${r.w + 12}" height="${r.h + 12}" rx="4"/>`); }
    }
    overlay.innerHTML = marks.join("");
  }

  // The panel is the sheet of what you're looking at: the drawing in focus, or a part of it you picked that has
  // no drawing of its own. Zoomed out, it's the register of every sheet on the board.
  function showPanel() {
    panelKey = `${focus?.key ?? ""}|${selected ?? ""}`;
    const crumbs = path.filter((e) => e.p >= 1).map((e) => e.node); // the drawings you've zoomed through
    trailEl.innerHTML = [`<a data-go="sheet">The drawing board</a>`, ...crumbs.map((n) => `<a data-go="${h.esc(n.key)}">${h.esc(n.thing.name)}</a>`)].join(" › ");
    h.located(selected ?? focus?.id ?? null); // the address bar follows
    if (!focus) return (panel.innerHTML = register());
    const sel = selected && things()[selected];
    if (sel) return (panel.innerHTML = `<a class="back-to" data-unselect>← ${h.esc(focus.thing.name)}</a>${heading(sel)}<p>${h.esc(sel.summary)}</p>
      <p class="hint">Part of the ${h.esc(focus.thing.name)}. It has no drawing of its own yet.</p>${h.details(sel)}`);
    const t = focus.thing, parts = partsOf(focus), caps = focus.data.captions, step = view[t.id]?.step ?? 1, sheets = sheetsOf(t);
    panel.innerHTML = `${heading(t)}
      ${sheets.length > 1 ? `<div class="board-sheets">${sheets.map((p) => `<button data-sheet="${h.esc(p)}" class="${p === sheetFor(t) ? "on" : ""}">${h.esc(sheetName(p))}</button>`).join("")}</div>` : ""}
      ${t.states?.length > 1 && focus.data.states ? `<div class="board-states"><span>State</span>${t.states.map((st) => `<button data-state="${h.esc(st)}" class="${st === stateFor(t) ? "on" : ""}">${h.esc(st)}</button>`).join("")}</div>` : ""}
      ${caps.length ? `<div class="stepper"><button data-step="-1" title="Previous step">◀</button><span class="caption"><b>${step} of ${caps.length}</b> ${h.esc(caps[step - 1])}</span>
        <button data-step="1" title="Next step">▶</button><button class="play${playing ? " on" : ""}">${playing ? "Pause" : "Play"}</button></div>` : ""}
      <p>${h.esc(t.summary)}</p>
      ${progress(t)}
      ${parts.length ? `<table class="bom"><tr><th></th><th>Part</th><th>Stands</th></tr>${parts.map((p) => `<tr data-id="${h.esc(p.id)}" class="${p.boxes.length ? "" : "unmarked"}">
        <td><span class="balloon-n ${standing(p.thing)}">${p.n}</span></td><td>${h.esc(p.thing.name)}${p.thing.visual ? ` <span class="opens">⊕</span>` : ""}</td><td>${STANDING[standing(p.thing)]}</td></tr>`).join("")}</table>
        <p class="hint">⊕ has its own drawing: zoom in on it, or click.</p>` : ""}
      ${h.details(t)}`;
  }
  const heading = (t) => `<h2 class="sheet-name">${h.esc(t.name)}</h2><div class="meta">${h.stamp(t.status)} ${h.esc(t.kind)}${t.state ? ` · ${h.esc(t.state)}` : ""}${t.location ? ` · ${h.esc(t.location)}` : ""}</div>`;

  // Every sheet on the board, by section, as a drawing register.
  function register() {
    const project = roots.find((n) => n.section === SECTIONS[0][0]);
    const bySection = SECTIONS.map(([title]) => [title, roots.filter((n) => n.section === title)]).filter(([, ns]) => ns.length);
    return `<h2 class="sheet-name">The drawing board</h2>
      <p class="hint">Everything you have, each on its sheet, its parts inside it. Scroll to zoom, drag to move, click to go.</p>
      ${project ? `${progress(project.thing)}` : ""}
      ${bySection.map(([title, ns]) => `<h4>${h.esc(title)}</h4><ul class="register">${ns.map((n) => `<li data-go="${h.esc(n.key)}">${h.esc(n.thing.name)}
        ${n.thing.components?.length ? `<span class="count">${n.thing.components.length} parts</span>` : ""}${n.data.blank ? `<span class="count">not drawn</span>` : ""} ${h.stamp(n.thing.status)}</li>`).join("")}</ul>`).join("")}`;
  }

  // How far a machine's parts have got, as a line of coloured counts.
  function progress(t) {
    const all = things(), parts = (t.components ?? []).map((id) => all[id]).filter(Boolean);
    if (!parts.length) return "";
    const n = (s) => parts.filter((p) => standing(p) === s).length;
    return `<p class="board-progress">${["ok", "making", "coming", "planned", "faulty"].filter(n).map((s) => `<span class="${s}">${n(s)} ${STANDING[s]}</span>`).join(" · ")} <span class="of">of ${parts.length} parts</span></p>`;
  }

  // ---------- pointing, clicking, keys ----------

  // What the pointer is on: in the drawing in focus, the smallest part under it; on the sheet, a drawing.
  function pick(sx, sy) {
    const [x, y] = atScreen(sx, sy), slack = (6 * cam[2]) / size()[0];
    if (focus) return partsOf(focus).flatMap((p) => p.boxes.map((b) => ({ id: p.id, b }))).filter(({ b }) => inside(b, x, y, slack)).sort((a, c) => a.b.w * a.b.h - c.b.w * c.b.h)[0]?.id ?? null;
    return roots.find((n) => inside(n.rect, x, y))?.id ?? null;
  }
  function label(id, sx, sy) {
    const t = id && things()[id];
    tag.hidden = !t;
    if (!t) return;
    const opens = t.visual && t._v;
    tag.innerHTML = `<b>${h.esc(t.name)}</b> ${h.stamp(t.status)}<span>${focus ? (opens ? "Click or zoom in to open its drawing" : "No drawing of its own yet: click for its sheet") : "Click to go to its sheet"}</span>`;
    tag.style.left = `${Math.min(sx + 16, host.clientWidth - tag.offsetWidth - 8)}px`;
    tag.style.top = `${Math.max(8, sy - tag.offsetHeight - 14)}px`;
  }
  // Go to a part or drawing: open its drawing in place, or its sheet if it has none.
  async function open(id) {
    if (!focus) { const n = roots.find((r) => r.id === id); return n && (h.desk(false), fly(framed(n.rect))); }
    const part = candidates(focus).filter((p) => p.id === id).sort((a, b) => b.box.w * b.box.h - a.box.w * a.box.h)[0], t = things()[id];
    if (!part || !(t.visual && t._v)) return (selected = id), (panelKey = "?"), draw(); // nothing to open: show it in the panel
    const get = () => child(part.owner, { id, box: part.local });
    let c = get();
    while (!c) (await new Promise((r) => setTimeout(r, 40))), (c = get());
    opened.set(focus.key, c), (growing = c);
    fly(framed(c.rect));
  }
  const nodeByKey = (key) => roots.find((n) => n.key === key) ?? children.get(key);
  function up() { // back out to the drawing you came through, closing the one you were in, or to the whole sheet
    const open = path.filter((e) => e.p >= 1), back = open.at(-2)?.node;
    closing = back && { key: open.at(-1).node.key, parentKey: back.key };
    if (!back) h.desk(true); // out to the whole sheet: your papers beside it
    fly(back ? framed(back.rect) : framed(sheet(), 0.96));
  }

  let drag = null;
  svg.addEventListener("pointerdown", (e) => ((drag = { x: e.clientX, y: e.clientY, cam: cam.slice(), moved: false }), svg.setPointerCapture(e.pointerId)));
  svg.addEventListener("pointermove", (e) => {
    const r = host.getBoundingClientRect(), sx = e.clientX - r.left, sy = e.clientY - r.top;
    if (drag) {
      const [W] = size(), dx = ((e.clientX - drag.x) / W) * drag.cam[2], dy = ((e.clientY - drag.y) / W) * drag.cam[2];
      if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 4) drag.moved = true;
      if (drag.moved) (flight = null), (quiet = true), (aim = null), (cam = [drag.cam[0] - dx, drag.cam[1] - dy, cam[2], cam[3]]), ask();
      return;
    }
    const id = pick(sx, sy);
    if (id !== hover) (hover = id), drawOverlay();
    label(hover, sx, sy);
  });
  svg.addEventListener("pointerup", (e) => {
    const moved = drag?.moved;
    drag = null;
    if (moved) return;
    const r = host.getBoundingClientRect(), id = pick(e.clientX - r.left, e.clientY - r.top);
    if (id) open(id);
  });
  svg.addEventListener("pointerleave", () => ((hover = null), drawOverlay(), label(null)));
  host.addEventListener("wheel", (e) => { // anywhere on the board, balloons included, but the panel scrolls
    if (e.target.closest(".board-panel")) return;
    e.preventDefault();
    const r = host.getBoundingClientRect();
    (flight = null), (aim = [e.clientX - r.left, e.clientY - r.top]);
    if (e.deltaY < 0) quiet = false; // zooming in: what you zoom into may open
    zoom(Math.exp(e.deltaY * (e.ctrlKey ? 0.01 : 0.0015)), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });
  overlay.addEventListener("click", (e) => { const b = e.target.closest(".balloon"); if (b) open(b.dataset.id); });
  overlay.addEventListener("pointerover", (e) => { const b = e.target.closest(".balloon"); if (b && hover !== b.dataset.id) (hover = b.dataset.id), drawOverlay(); });
  panel.addEventListener("pointerover", (e) => { const row = e.target.closest("tr[data-id]"); if (row && hover !== row.dataset.id) (hover = row.dataset.id), drawOverlay(); });
  // Look at the drawing in focus in another state, or step through its working cycle.
  function look(id, change) {
    view[id] = { ...view[id], ...change };
    children.forEach((c) => (c.stale = true));
    layout().then(() => {
      panelKey = "?";
      const n = change.sheet && (roots.find((r) => r.id === id) ?? null);
      n ? fly(framed(n.rect), 300) : draw(); // another sheet may be another shape
    });
  }
  panel.addEventListener("click", (e) => {
    if (e.target.closest("[data-unselect]")) return (selected = null), (panelKey = "?"), draw();
    const t = focus?.thing, st = e.target.closest("[data-state]"), sp = e.target.closest("[data-step]"), sh = e.target.closest("[data-sheet]");
    if (t && sh) clearInterval(playing), (playing = null), look(t.id, { sheet: sh.dataset.sheet, step: 1 });
    if (t && st) clearInterval(playing), (playing = null), look(t.id, { state: st.dataset.state, step: 1 });
    const n = focus?.data.captions.length, turn = (d) => look(t.id, { step: (((view[t.id]?.step ?? 1) - 1 + d + n) % n) + 1 });
    if (t && sp) turn(+sp.dataset.step);
    if (t && e.target.closest(".play")) (playing = playing ? clearInterval(playing) : setInterval(() => (focus?.thing === t ? turn(1) : (clearInterval(playing), (playing = null))), 3200)), (panelKey = "?"), draw();
    const row = e.target.closest("tr[data-id]"), go = e.target.closest("[data-go]");
    if (row) open(row.dataset.id);
    if (go) { const n = nodeByKey(go.dataset.go); h.desk(!n); fly(n ? framed(n.rect) : framed(sheet(), 0.96)); }
  });
  trailEl.addEventListener("click", (e) => { const go = e.target.closest("[data-go]"); if (!go) return; const n = nodeByKey(go.dataset.go); h.desk(!n); fly(n ? framed(n.rect) : framed(sheet(), 0.96)); });
  host.querySelector(".board-keys").addEventListener("click", (e) => {
    const k = e.target.closest("button")?.dataset.k, [W, H] = size();
    if (k === "in") (quiet = false), zoom(0.6, W / 2, H / 2);
    if (k === "out") up();
    if (k === "all") h.desk(true), fly(framed(sheet(), 0.96));
  });
  addEventListener("resize", () => cam && ((cam = framed({ x: cam[0], y: cam[1], w: cam[2], h: cam[3] }, 1)), ask()));

  // ---------- the outside ----------

  return {
    // New state: re-lay the sheet (drawings are cached), keeping the camera.
    async update(state) {
      S = state;
      children.forEach((c) => (c.stale = true));
      await layout();
      if (!cam) h.desk(true), (cam = roots.length ? framed(sheet(), 0.96) : [0, 0, 1000, 600]); // first: the whole sheet, your papers open
      draw();
    },
    // Fly to a thing: through the drawings that show it, from the sheet down. Halfway: stop with its drawing half
    // grown over the drawing it's part of (to check they line up); now: jump there.
    async show(chain, { half = false, now = false } = {}) {
      let node = roots.find((n) => n.id === chain[0]);
      h.desk(false);
      let pick = null;
      for (const id of chain.slice(1)) {
        const part = node && candidates(node).filter((p) => p.id === id).sort((a, b) => b.box.w * b.box.h - a.box.w * a.box.h)[0];
        if (!part || !things()[id]?.visual) { pick = id; break; } // no drawing of its own: its sheet, in its machine
        let c = child(part.owner, { id, box: part.local });
        while (!c) (await new Promise((r) => setTimeout(r, 40))), (c = child(part.owner, { id, box: part.local }));
        opened.set(node.key, c);
        node = c;
      }
      if (!node) return;
      let to = framed(node.rect);
      if (half && node.parent) { // zoomed into the drawing it's in to where it's half open, centred on the part
        const par = node.parent, P = node.part, size = fill(node.rect) / fill(par.rect), start = 0.92 * 1.25, end = OPEN[1] / size;
        const F = end <= start * 1.1 ? end : Math.sqrt(start * end);
        to = framed({ x: P.x + P.w / 2 - par.rect.w / 2, y: P.y + P.h / 2 - par.rect.h / 2, w: par.rect.w, h: par.rect.h }, F);
      }
      await fly(to, now ? 0 : 750);
      (selected = pick), draw();
    },
    up,
    // Home: the whole sheet, your papers open beside it.
    home() { h.desk(true); fly(framed(sheet(), 0.96)); },
    // Keep the same view when your papers open or close: slide it over by half the drawer, at the same zoom.
    reframe(shift) { const u = cam[2] / size()[0]; fly([cam[0] - shift * u / 2, cam[1], cam[2], cam[3]], 350); },
    // The parts of the drawing in focus and their boxes on the screen (for tests and checks).
    parts() {
      const [W, H] = size();
      return partsOf(focus).map((p) => ({ id: p.id, n: p.n, boxes: p.boxes.map((b) => [((b.x - cam[0]) / cam[2]) * W, ((b.y - cam[1]) / cam[3]) * H, (b.w / cam[2]) * W, (b.h / cam[3]) * H]) }));
    },
    setBehind(b) { host.classList.toggle("behind", b); },
    get focus() { return focus?.id ?? null; },
  };
}
