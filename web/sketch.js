// Sketch sheet: draw and label a design, then save it as a PNG in the save's sketches/ for the referee to read.
const W = 1200, H = 900;
const COLORS = { ink: "#2b2118", red: "#9c3b25" };
const TEXT = { 2: 20, 4: 30, 9: 44 }; // label size on the sheet for each line width
const LH = 1.2; // label line height
const font = (it) => `${it.size}px Georgia, serif`;
const shape = (tool) => tool === "line" || tool === "arrow" || tool === "oval"; // drawn from where a drag starts to where it ends
const copy = (text) => navigator.clipboard.writeText(text).then(() => true, () => false);

// A page of the sketchbook: a saved sketch, the turns it was sent in, and what you can do with it.
const page = ({ path, turns }) => `
  <figure>
    <a href="/save/${path}" target="_blank" title="Open full size"><img src="/save/${path}" alt="${path}" loading="lazy"></a>
    <figcaption><code>${path}</code>${turns.length ? ` · sent in turn${turns.length > 1 ? "s" : ""} ${turns.join(", ")}` : ""}</figcaption>
    <div class="actions"><a href="/save/${path}" target="_blank">Open</a><button data-copy="${path}">Copy path</button><button data-over="${path}" title="Draw over it: put it faintly under the sheet">Draw over</button></div>
  </figure>`;

export function initSketch(root, { traces, sketchbook, toast }) {
  root.innerHTML = `
    <div class="sketch-tools">
      <span class="group">
        <button data-tool="pen" class="on" aria-keyshortcuts="P" title="Pen (P)"><u>P</u>en</button>
        <button data-tool="line" aria-keyshortcuts="L" title="Straight line (L); hold Shift to snap to 15° steps"><u>L</u>ine</button>
        <button data-tool="arrow" aria-keyshortcuts="A" title="Arrow (A), to point a label at a part; hold Shift to snap to 15° steps"><u>A</u>rrow</button>
        <button data-tool="oval" aria-keyshortcuts="O" title="Oval (O): drag out its box; hold Shift for a circle"><u>O</u>val</button>
        <button data-tool="text" aria-keyshortcuts="T" title="Label (T): click to write; click a label to change it, drag it to move it">Label</button>
        <button data-tool="erase" aria-keyshortcuts="E" title="Eraser (E)"><u>E</u>raser</button>
      </span>
      <span class="group">
        <button data-color="ink" class="on" aria-keyshortcuts="B" title="Black ink (B)"><i class="swatch ink"></i>Ink</button>
        <button data-color="red" aria-keyshortcuts="R" title="Red ink (R)"><i class="swatch red"></i><u>R</u>ed</button>
        <select id="sk-size" title="Size of lines and labels"><option value="2">Fine</option><option value="4" selected>Medium</option><option value="9">Bold</option></select>
      </span>
      <span class="group">
        <select id="sk-trace" title="Draw over a drawing or an earlier sketch"></select>
      </span>
      <span class="group">
        <button id="sk-undo" title="Undo (⌘Z); redo with ⇧⌘Z">Undo</button><button id="sk-clear">Clear</button>
        <button id="sk-save" class="primary">Save sketch</button>
      </span>
    </div>
    <div class="sketch-sheet"><canvas id="sk-bg"></canvas><canvas id="sk-ink"></canvas></div>
    <p class="hint">Draw your design and label the parts. Line and Arrow draw straight; hold Shift to snap the angle. Oval draws in the box you drag; hold Shift for a circle. With Label, click to write (Enter to finish, Shift+Enter for a new line), click a label to change it, or drag it to move it. Keys: P, L, A, O, T and E pick a tool, B and R the colour. Saving puts it in the game's <code>sketches/</code> folder and copies its path: paste that into the terminal with your message, and the referee will look at it.</p>
    <section class="sketchbook"><h2>Sketchbook</h2><div id="sk-book"></div></section>`;

  const [bg, ink] = [root.querySelector("#sk-bg"), root.querySelector("#sk-ink")];
  for (const c of [bg, ink]) Object.assign(c, { width: W, height: H });
  const bctx = bg.getContext("2d"), ictx = ink.getContext("2d");
  const sizeSel = root.querySelector("#sk-size"), traceSel = root.querySelector("#sk-trace");
  const saveBtn = root.querySelector("#sk-save"), book = root.querySelector("#sk-book");
  let tool = "pen", color = "ink", items = [], current = null, under = null, options = [];
  let past = [], future = [], editing = null, press = null;
  let saved = null, shown = null; // saved: a promise of the path the sheet as it stands was saved to; shown: the sketchbook on show

  function paper() {
    bctx.fillStyle = "#f6eedb";
    bctx.fillRect(0, 0, W, H);
    bctx.strokeStyle = "rgba(122, 106, 85, 0.16)";
    bctx.lineWidth = 1;
    bctx.beginPath();
    for (let x = 30; x < W; x += 30) bctx.moveTo(x, 0), bctx.lineTo(x, H);
    for (let y = 30; y < H; y += 30) bctx.moveTo(0, y), bctx.lineTo(W, y);
    bctx.stroke();
    if (under) {
      const s = Math.min(W / under.naturalWidth, H / under.naturalHeight);
      const [w, h] = [under.naturalWidth * s, under.naturalHeight * s];
      bctx.globalAlpha = 0.4;
      bctx.drawImage(under, (W - w) / 2, (H - h) / 2, w, h);
      bctx.globalAlpha = 1;
    }
  }

  function pen(it) {
    ictx.globalCompositeOperation = it.tool === "erase" ? "destination-out" : "source-over";
    ictx.strokeStyle = COLORS[it.color];
    ictx.lineWidth = it.tool === "erase" ? it.width * 5 : it.width;
    ictx.lineCap = ictx.lineJoin = "round";
  }

  function draw(it) {
    if (it.text) return label(it);
    pen(it);
    ictx.beginPath();
    if (it.tool === "oval") {
      const [[x0, y0], [x, y]] = it.pts;
      ictx.ellipse((x0 + x) / 2, (y0 + y) / 2, Math.abs(x - x0) / 2, Math.abs(y - y0) / 2, 0, 0, 2 * Math.PI);
    } else {
      ictx.moveTo(...it.pts[0]);
      it.pts.forEach((p) => ictx.lineTo(...p));
      if (it.pts.length === 1) ictx.lineTo(it.pts[0][0] + 0.1, it.pts[0][1]); // a dot
    }
    if (it.tool === "arrow") {
      const [[x0, y0], [x, y]] = it.pts, a = Math.atan2(y - y0, x - x0), head = 8 + it.width * 3;
      for (const s of [-0.5, 0.5]) ictx.moveTo(x, y), ictx.lineTo(x - head * Math.cos(a + s), y - head * Math.sin(a + s));
    }
    ictx.stroke();
  }

  // A label's top-left corner is at (x, y); each line sits where a CSS line box puts it, so the text stays where the editor showed it.
  function label(it) {
    ictx.globalCompositeOperation = "source-over";
    ictx.fillStyle = COLORS[it.color];
    ictx.font = font(it);
    const lh = it.size * LH, m = ictx.measureText(it.text);
    const base = (lh + m.fontBoundingBoxAscent - m.fontBoundingBoxDescent) / 2;
    it.text.split("\n").forEach((line, i) => ictx.fillText(line, it.x, it.y + i * lh + base));
  }

  // The topmost label under a point, by its measured text bounds.
  const labelAt = (x, y) => items.findLast((it) => {
    if (!it.text) return false;
    ictx.font = font(it);
    const lines = it.text.split("\n"), w = Math.max(...lines.map((l) => ictx.measureText(l).width));
    return x > it.x - 6 && x < it.x + w + 6 && y > it.y - 6 && y < it.y + lines.length * it.size * LH + 6;
  });

  // The Save button says whether the sheet as it stands is saved, and where; any change to the sheet makes it unsaved.
  const mark = (path) => ((saveBtn.textContent = path ? `Saved as ${path}` : "Save sketch"), (saveBtn.title = path ? "Copy its path again" : ""), saveBtn.classList.toggle("done", !!path));
  const changed = () => ((saved = null), mark());
  const redraw = () => (ictx.clearRect(0, 0, W, H), items.forEach((it) => it !== editing?.it && draw(it)));
  // Snapshots before each change. Drawn items are never modified (edits and moves replace them), so a shallow copy will do.
  const remember = () => (past.push([...items]), (future = []), changed());
  const restore = (from, to) => from.length && (to.push(items), (items = from.pop()), redraw(), changed());
  const undo = () => restore(past, future), redo = () => restore(future, past);
  const at = (e) => [(e.offsetX / ink.clientWidth) * W, (e.offsetY / ink.clientHeight) * H];

  // End point of a straight line; with Shift, the angle snaps to 15° steps.
  function lineEnd([x0, y0], [x, y], snap) {
    if (!snap) return [x, y];
    const step = Math.PI / 12, len = Math.hypot(x - x0, y - y0);
    const angle = Math.round(Math.atan2(y - y0, x - x0) / step) * step;
    return [x0 + len * Math.cos(angle), y0 + len * Math.sin(angle)];
  }

  // Far corner of an oval's box; with Shift, the box is square, for a circle.
  function boxEnd([x0, y0], [x, y], snap) {
    if (!snap) return [x, y];
    const d = Math.max(Math.abs(x - x0), Math.abs(y - y0));
    return [x < x0 ? x0 - d : x0 + d, y < y0 ? y0 - d : y0 + d];
  }

  // The label editor: a textarea over the sheet in the label's own font, size and colour.
  function edit(it) {
    const ta = Object.assign(document.createElement("textarea"), { className: "sk-label", value: it.text, wrap: "off" });
    Object.assign(ta.style, { left: `${(it.x / W) * 100}%`, top: `${(it.y / H) * 100}%`, fontSize: `${(it.size / W) * 100}cqw`, color: COLORS[it.color] });
    ta.onkeydown = (e) => {
      if (e.key === "Escape") finish(true);
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) e.preventDefault(), finish();
    };
    ta.onblur = () => finish();
    editing = { it, ta };
    redraw(); // hide the label while it's in the editor
    root.querySelector(".sketch-sheet").append(ta);
    ta.focus();
  }

  // Close the editor, keeping the text unless cancelled. An emptied label is deleted; an edited one comes to the front.
  function finish(cancel) {
    if (!editing) return;
    const { it, ta } = editing, text = ta.value.trimEnd();
    editing = null;
    ta.remove();
    if (!cancel && text !== it.text) {
      remember();
      items = items.filter((x) => x !== it);
      if (text) items.push({ ...it, text });
    }
    redraw();
  }

  // Drag a label to move it (it comes to the front); a press that moves less than 4px is a click, which edits it.
  function drag([x, y]) {
    const [dx, dy] = [x - press.at[0], y - press.at[1]];
    if (!press.moved) {
      if (Math.hypot(dx, dy) * (ink.clientWidth / W) < 4) return;
      remember();
      const moved = { ...press.it };
      items = [...items.filter((it) => it !== press.it), moved];
      Object.assign(press, { it: moved, moved: true });
    }
    Object.assign(press.it, { x: press.it.x + dx, y: press.it.y + dy });
    press.at = [x, y];
    redraw();
  }

  ink.addEventListener("pointerdown", (e) => {
    press = null;
    if (editing) return finish();
    const [x, y] = at(e);
    ink.setPointerCapture(e.pointerId);
    if (tool === "text") return (press = { it: labelAt(x, y), at: [x, y] });
    remember();
    current = { tool, color, width: Number(sizeSel.value), pts: shape(tool) ? [[x, y], [x, y]] : [[x, y]] };
    items.push(current);
    draw(current);
  });
  ink.addEventListener("pointermove", (e) => {
    const p = at(e);
    if (tool === "text" && !e.buttons) ink.style.cursor = labelAt(...p) ? "move" : "text";
    if (press?.it && e.buttons) return drag(p);
    if (!current) return;
    if (shape(current.tool)) return (current.pts[1] = (current.tool === "oval" ? boxEnd : lineEnd)(current.pts[0], p, e.shiftKey)), redraw();
    const last = current.pts.at(-1);
    current.pts.push(p);
    pen(current);
    ictx.beginPath();
    ictx.moveTo(...last);
    ictx.lineTo(...p);
    ictx.stroke();
  });
  for (const type of ["pointerup", "pointercancel"]) ink.addEventListener(type, () => (current = null));
  // The editor opens on click, after the browser has moved focus for the press.
  ink.addEventListener("click", () => {
    if (press && !press.moved) edit(press.it ?? { text: "", x: press.at[0], y: press.at[1], color, size: TEXT[sizeSel.value] });
    press = null;
  });

  root.querySelectorAll("[data-tool]").forEach((b) => (b.onclick = () => {
    tool = b.dataset.tool;
    ink.style.cursor = tool === "text" ? "text" : "";
    root.querySelectorAll("[data-tool]").forEach((x) => x.classList.toggle("on", x === b));
  }));
  root.querySelectorAll("[data-color]").forEach((b) => (b.onclick = () => {
    color = b.dataset.color;
    root.querySelectorAll("[data-color]").forEach((x) => x.classList.toggle("on", x === b));
  }));
  root.querySelector("#sk-undo").onclick = undo;
  root.querySelector("#sk-clear").onclick = () => items.length && confirm("Clear the whole sheet?") && (remember(), (items = []), redraw());
  // ⌘Z undoes and ⇧⌘Z redoes; a letter presses the button that has it as its aria-keyshortcuts, unless you're typing.
  document.addEventListener("keydown", (e) => {
    if (root.hidden || editing) return;
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key.toLowerCase() === "z") return e.preventDefault(), (e.shiftKey ? redo : undo)();
    if (mod || e.altKey || e.target.closest("input, textarea, select, [contenteditable]")) return;
    root.querySelector(`[aria-keyshortcuts="${CSS.escape(e.key.toUpperCase())}"]`)?.click();
  });

  traceSel.onchange = async () => {
    changed();
    const opt = options.find((o) => o.key === traceSel.value);
    under = null;
    if (opt) {
      under = new Image();
      under.src = await opt.url();
      await under.decode();
    }
    paper();
  };

  // Post the sheet as it stands and resolve to its path in the save.
  async function upload() {
    const out = Object.assign(document.createElement("canvas"), { width: W, height: H });
    const octx = out.getContext("2d");
    octx.drawImage(bg, 0, 0);
    octx.drawImage(ink, 0, 0);
    const res = await fetch("/api/sketch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ png: out.toDataURL("image/png") }),
    });
    return (await res.json()).path;
  }

  // Saves once per state of the sheet: until it changes, clicking again (even mid-save) only copies the path again.
  saveBtn.onclick = async () => {
    const again = !!saved, pending = (saved ??= upload());
    const path = await pending;
    if (saved === pending) mark(path);
    const copied = await copy(path);
    toast(`${again ? "Already saved" : "Saved"} as ${path}${copied ? " (path copied)" : ""}. Mention it in the terminal with your message.`);
  };

  // The traces include each saved sketch, keyed by its path.
  book.onclick = async (e) => {
    const { copy: path, over } = e.target.closest("button")?.dataset ?? {};
    if (path) toast((await copy(path)) ? `Copied ${path}.` : `Couldn't copy the path: ${path}`);
    if (over) (traceSel.value = over), traceSel.onchange(), scrollTo({ top: 0, behavior: "smooth" });
  };

  paper();
  return {
    refresh() {
      options = traces();
      const keep = traceSel.value;
      traceSel.replaceChildren(new Option("Plain paper", ""), ...options.map((o) => new Option(`Over: ${o.label}`, o.key)));
      traceSel.value = options.some((o) => o.key === keep) ? keep : "";
      const pages = sketchbook().toReversed(), key = JSON.stringify(pages);
      if (key === shown) return; // don't reload the thumbnails on every live update
      shown = key;
      book.innerHTML = pages.map(page).join("") || `<p class="hint">Your saved sketches will appear here.</p>`;
    },
  };
}
