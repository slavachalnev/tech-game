// Sketch sheet: draw and label a design, then save it as a PNG in the save's sketches/ for the referee to read.
const W = 1200, H = 900;
const COLORS = { ink: "#2b2118", red: "#9c3b25" };

export function initSketch(root, { traces, toast }) {
  root.innerHTML = `
    <div class="sketch-tools">
      <span class="group">
        <button data-tool="pen" class="on">Pen</button><button data-tool="text">Label</button><button data-tool="erase">Eraser</button>
      </span>
      <span class="group">
        <button data-color="ink" class="on"><i class="swatch ink"></i>Ink</button><button data-color="red"><i class="swatch red"></i>Red</button>
        <select id="sk-width" title="Line width"><option value="2">Fine</option><option value="4" selected>Medium</option><option value="9">Bold</option></select>
      </span>
      <span class="group">
        <select id="sk-trace" title="Draw over a drawing or an earlier sketch"></select>
      </span>
      <span class="group">
        <button id="sk-undo" title="Undo (⌘Z)">Undo</button><button id="sk-clear">Clear</button>
        <button id="sk-save" class="primary">Save sketch</button>
      </span>
    </div>
    <div class="sketch-sheet"><canvas id="sk-bg"></canvas><canvas id="sk-ink"></canvas></div>
    <p class="hint">Draw your design and label the parts. Saving puts it in the game's <code>sketches/</code> folder and copies its path: paste that into the terminal with your message, and the referee will look at it.</p>`;

  const [bg, ink] = [root.querySelector("#sk-bg"), root.querySelector("#sk-ink")];
  for (const c of [bg, ink]) Object.assign(c, { width: W, height: H });
  const bctx = bg.getContext("2d"), ictx = ink.getContext("2d");
  const widthSel = root.querySelector("#sk-width"), traceSel = root.querySelector("#sk-trace");
  let tool = "pen", color = "ink", items = [], current = null, under = null, options = [];

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
    if (it.text) {
      ictx.globalCompositeOperation = "source-over";
      ictx.fillStyle = COLORS[it.color];
      ictx.font = "italic 30px Georgia, serif";
      ictx.fillText(it.text, it.x, it.y);
      return;
    }
    pen(it);
    ictx.beginPath();
    ictx.moveTo(...it.pts[0]);
    it.pts.forEach((p) => ictx.lineTo(...p));
    if (it.pts.length === 1) ictx.lineTo(it.pts[0][0] + 0.1, it.pts[0][1]); // a dot
    ictx.stroke();
  }

  const redraw = () => (ictx.clearRect(0, 0, W, H), items.forEach(draw));
  const undo = () => (items.pop(), redraw());
  const at = (e) => [(e.offsetX / ink.clientWidth) * W, (e.offsetY / ink.clientHeight) * H];

  ink.addEventListener("pointerdown", (e) => {
    const [x, y] = at(e);
    if (tool === "text") {
      const text = prompt("Label:");
      if (text) items.push({ text, x, y, color }), redraw();
      return;
    }
    ink.setPointerCapture(e.pointerId);
    current = { tool, color, width: Number(widthSel.value), pts: [[x, y]] };
    items.push(current);
    draw(current);
  });
  ink.addEventListener("pointermove", (e) => {
    if (!current) return;
    const last = current.pts.at(-1), p = at(e);
    current.pts.push(p);
    pen(current);
    ictx.beginPath();
    ictx.moveTo(...last);
    ictx.lineTo(...p);
    ictx.stroke();
  });
  for (const type of ["pointerup", "pointercancel"]) ink.addEventListener(type, () => (current = null));

  root.querySelectorAll("[data-tool]").forEach((b) => (b.onclick = () => {
    tool = b.dataset.tool;
    root.querySelectorAll("[data-tool]").forEach((x) => x.classList.toggle("on", x === b));
  }));
  root.querySelectorAll("[data-color]").forEach((b) => (b.onclick = () => {
    color = b.dataset.color;
    root.querySelectorAll("[data-color]").forEach((x) => x.classList.toggle("on", x === b));
  }));
  root.querySelector("#sk-undo").onclick = undo;
  root.querySelector("#sk-clear").onclick = () => items.length && confirm("Clear the whole sheet?") && ((items = []), redraw());
  document.addEventListener("keydown", (e) => {
    if (!root.hidden && (e.metaKey || e.ctrlKey) && e.key === "z") e.preventDefault(), undo();
  });

  traceSel.onchange = async () => {
    const opt = options.find((o) => o.key === traceSel.value);
    under = null;
    if (opt) {
      under = new Image();
      under.src = await opt.url();
      await under.decode();
    }
    paper();
  };

  root.querySelector("#sk-save").onclick = async () => {
    const out = Object.assign(document.createElement("canvas"), { width: W, height: H });
    const octx = out.getContext("2d");
    octx.drawImage(bg, 0, 0);
    octx.drawImage(ink, 0, 0);
    const res = await fetch("/api/sketch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ png: out.toDataURL("image/png") }),
    });
    const { path } = await res.json();
    const copied = await navigator.clipboard.writeText(path).then(() => true, () => false);
    toast(`Saved as ${path}${copied ? " (path copied)" : ""}. Mention it in the terminal with your message.`);
  };

  paper();
  return {
    refresh() {
      options = traces();
      const keep = traceSel.value;
      traceSel.replaceChildren(new Option("Plain paper", ""), ...options.map((o) => new Option(`Over: ${o.label}`, o.key)));
      traceSel.value = options.some((o) => o.key === keep) ? keep : "";
    },
  };
}
