// Live view of a save. It only renders the state files; the referee (Claude Code) is the only writer.
import { initSketch } from "./sketch.js";

const $ = (sel) => document.querySelector(sel);
const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const KINDS = { machine: "Machines", component: "Components", structure: "Structures", tool: "Tools", material: "Materials", document: "Documents", site: "Sites", other: "Other" };
const STATUS = { planned: "planned", building: "being built", ok: "OK", faulty: "faulty", broken: "broken", consumed: "used up" };
const UNIT = /^(.*?)_((?:mm|cm|m|km|m2|m3|g|kg|t|l|ml|bar|kpa|mpa|atm|w|kw|c|pct|s|min|h|days|weeks|p)(?:_per_[a-z0-9]+)?)$/;
const UNIT_LABEL = { m2: "m²", m3: "m³", l: "L", ml: "mL", kpa: "kPa", mpa: "MPa", w: "W", kw: "kW", c: "°C", pct: "%" };

let S = null; // latest state from the server
let seen = new Map(); // key -> JSON last rendered, to highlight what the referee just changed
const fresh = new Set();
let renderId = 0;
const opened = JSON.parse(localStorage.getItem("opened") ?? "{}"); // details open/closed, by data-key, kept across pages and reloads
const scrolls = {}; // scroll position per page, restored when you come back
let shownHash = null;
let lastMap = null;
let spent = null; // the purse's last change, shown for a while: { p }
let mapToMount = null; // the map to draw into the page once the Map view's HTML is in place
const COMPASS = "N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split(" ");

// ---------- formatting ----------

function money(p) {
  const a = Math.abs(p), sign = p < 0 ? "-" : "";
  if (a < 100) return `${sign}${a}p`;
  return `${sign}£${Math.floor(a / 100)}${a % 100 ? "." + String(a % 100).padStart(2, "0") : ""}`;
}
function day(clock) {
  const [y, m, d] = clock.slice(0, 10).split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
const span = (a, b) => (day(a) === day(b) ? day(a) : `${day(a)} – ${day(b)}`);
function prop(key, value) {
  const m = key.match(UNIT);
  const name = (m ? m[1] : key).replace(/_/g, " ");
  if (m?.[2] === "p" && typeof value === "number") return [name, money(value)];
  const unit = m?.[2].split("_per_").map((u) => UNIT_LABEL[u] ?? u).join("/");
  return [unit ? `${name} (${unit})` : name, value === true ? "yes" : value === false ? "no" : value];
}
const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>").replace(/`(.+?)`/g, "<code>$1</code>");
function markdown(text) {
  return text.split(/\n{2,}/).map((block) => {
    if (block.startsWith("# ")) return `<h2>${inline(block.slice(2))}</h2>`;
    const lines = block.split("\n");
    const para = lines.filter((l) => !l.startsWith("- "));
    const items = lines.filter((l) => l.startsWith("- "));
    return (para.length ? `<p>${inline(para.join(" "))}</p>` : "") + (items.length ? `<ul>${items.map((l) => `<li>${inline(l.slice(2))}</li>`).join("")}</ul>` : "");
  }).join("");
}
const stamp = (s) => `<span class="stamp s-${s}">${STATUS[s] ?? s}</span>`;
const bullets = (title, items, cls = "") => (items?.length ? `<h3>${title}</h3><ul class="${cls}">${items.map((i) => `<li>${i}</li>`).join("")}</ul>` : "");
const facts = (title, obj) =>
  obj && Object.keys(obj).length
    ? `<h3>${title}</h3><dl>${Object.entries(obj).map(([k, v]) => prop(k, v)).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`
    : "";
const fermi = (paths) =>
  paths?.length
    ? `<h3>Fermi estimates</h3>${paths.map((p) => `<details class="fermi" data-key="${esc(p)}" data-src="${esc(p)}"><summary>${esc(p)}</summary><pre>…</pre></details>`).join("")}`
    : "";
const initials = (name) => name.split(/\s+/).filter((w) => /^[A-Z]/.test(w) && !/^(Mr|Mrs|Miss|Dr|Sir|Lady|Lord|Captain|Rev)\.?$/.test(w)).map((w) => w[0]).slice(0, 2).join("") || name[0];
const historyNotes = (items) => bullets("History", items?.map((h) => `<span class="turn-ref">Turn ${h.turn}.</span> ${esc(h.note)}`), "history");

// ---------- the sky at the clock's time ----------

const LATITUDE = 50.2; // degrees north: the scenarios so far are set in southern Britain
const MOON = ["new moon", "waxing crescent moon", "first-quarter moon", "waxing gibbous moon", "full moon", "waning gibbous moon", "last-quarter moon", "waning crescent moon"];

// Julian Day of a clock time (local solar time, as clocks then were set by the sun). Old Style before Britain's 1752 switch.
function julianDay(clock) {
  const [y, m, d, hh, mm] = clock.split(/[-T:]/).map(Number);
  const a = Math.floor((14 - m) / 12), Y = y + 4800 - a, M = m + 12 * a - 3;
  const calendar = clock >= "1752-09-14" ? Math.floor(Y / 400) - Math.floor(Y / 100) - 32045 : -32083;
  return d + Math.floor((153 * M + 2) / 5) + 365 * Y + Math.floor(Y / 4) + calendar - 0.5 + (hh + mm / 60) / 24;
}

// Sunrise and sunset (hours of solar time), the time of day, and the moon's age (0 new, 0.5 full).
function sky(clock) {
  const rad = Math.PI / 180, jd = julianDay(clock), n = jd - 2451545;
  const g = (357.528 + 0.9856003 * n) * rad;
  const decl = Math.asin(Math.sin(23.44 * rad) * Math.sin((280.46 + 0.9856474 * n + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * rad));
  const half = Math.acos((Math.sin(-0.833 * rad) - Math.sin(LATITUDE * rad) * Math.sin(decl)) / (Math.cos(LATITUDE * rad) * Math.cos(decl))) / rad / 15;
  const [rise, set] = [12 - half, 12 + half], h = +clock.slice(11, 13) + clock.slice(14, 16) / 60;
  const phase = h < rise - 0.75 || h > set + 0.75 ? "night" : h < rise + 0.75 ? "dawn" : h > set - 0.75 ? "dusk" : "day";
  return { rise, set, phase, moon: ((((jd - 2451550.1) / 29.530588853) % 1) + 1) % 1 };
}
const hm = (h) => `${String(Math.floor(Math.round(h * 60) / 60)).padStart(2, "0")}:${String(Math.round(h * 60) % 60).padStart(2, "0")}`;
const moonName = (f) => MOON[Math.round(f * 8) % 8];

// The moon as it looks: the lit part is a half disc plus or minus half an ellipse.
function moonIcon(f, r = 9) {
  const c = r + 1, k = Math.cos(2 * Math.PI * f), waxing = f < 0.5;
  const lit = `M${c} ${c - r}A${r} ${r} 0 0 ${waxing ? 1 : 0} ${c} ${c + r}A${(r * Math.abs(k)).toFixed(2)} ${r} 0 0 ${k > 0 === waxing ? 0 : 1} ${c} ${c - r}Z`;
  return `<svg class="moon" viewBox="0 0 ${2 * c} ${2 * c}" width="${2 * c}" height="${2 * c}"><title>${moonName(f)}</title><circle class="dark" cx="${c}" cy="${c}" r="${r}"/><path class="lit" d="${lit}"/><circle class="rim" cx="${c}" cy="${c}" r="${r}"/></svg>`;
}
const SUN = `<svg class="sun" viewBox="0 0 20 20" width="20" height="20"><circle cx="10" cy="10" r="4"/>${[0, 45, 90, 135, 180, 225, 270, 315].map((a) => `<line x1="10" y1="1.5" x2="10" y2="4" transform="rotate(${a} 10 10)"/>`).join("")}</svg>`;

// Small ink glyphs for things that have no drawing yet, by kind.
const GLYPH = {
  machine: `<polygon points="${Array.from({ length: 40 }, (_, i) => { const a = (i / 40) * 2 * Math.PI, r = [15, 15, 19, 19][i % 4]; return `${(24 + r * Math.cos(a)).toFixed(1)},${(24 + r * Math.sin(a)).toFixed(1)}`; }).join(" ")}"/><circle cx="24" cy="24" r="5"/>`,
  component: `<polygon points="40,24 32,37.9 16,37.9 8,24 16,10.1 32,10.1"/><circle cx="24" cy="24" r="7"/>`,
  tool: `<rect x="11" y="9" width="24" height="9" rx="1.5"/><path d="M21 18v22h5V18"/>`,
  material: `<path d="M8 38h14l-2-7H10zM26 38h14l-2-7H28zM17 30h14l-2-7H19z"/>`,
  document: `<path d="M13 7h16l7 7v27H13zM29 7v7h7M17 20h14M17 25h14M17 30h9"/>`,
  structure: `<path d="M9 40V22l15-12 15 12v18zM20 40v-9h8v9"/>`,
  site: `<path d="M5 40q19-11 38 0M24 34V9l12 4.5L24 18"/>`,
  other: `<path d="M24 11v26M12.7 17.5l22.6 13M35.3 17.5l-22.6 13"/>`,
};
const glyph = (kind) => `<svg class="glyph" viewBox="0 0 48 48">${GLYPH[kind] ?? GLYPH.other}</svg>`;

// ---------- drawings ----------

const sources = new Map(); // URL -> promise of its text (null if missing)
const drawings = new Map(); // "path@version@state" -> object URL

function fetchText(url) {
  if (!sources.has(url)) sources.set(url, fetch(url).then((r) => (r.ok ? r.text() : null)));
  return sources.get(url);
}
// A drawing's SVG: the current file, or the file in an earlier snapshot of the save (`_rev`).
const svgText = (item) => fetchText(item._rev ? `/api/rev/${item._rev}/${item.visual}` : `/save/${item.visual}?v=${item._v}`);
// A drawing's caption: its thing's name, or the file's name for a scene.
function caption(path, thing) {
  const name = thing?.name ?? path.slice(8, -4).replace(/^scene-/, "").replace(/-/g, " ");
  return name[0].toUpperCase() + name.slice(1);
}
// Link attributes for a drawing: a thing's opens its spec sheet, a scene opens full size.
const opens = (thing, url) => (thing ? `href="#/thing/${thing.id}"` : `href="${url}" target="_blank"`);

// A thing's SVG, with only the groups for `state` kept, as an <img>-ready URL (isolates each drawing's ids and styles).
async function drawing(thing, state = thing.state ?? thing.states?.[0] ?? "") {
  if (!thing.visual || !thing._v) return null;
  const key = `${thing.visual}@${thing._v}@${state}`;
  if (!drawings.has(key)) {
    const svg = new DOMParser().parseFromString(await svgText(thing), "image/svg+xml").documentElement;
    svg.querySelectorAll("[data-state]").forEach((el) => {
      if (!el.getAttribute("data-state").split(/\s+/).includes(state)) el.remove();
    });
    if (!svg.getAttribute("width")) {
      const [, , w, h] = (svg.getAttribute("viewBox") ?? "0 0 800 600").split(/[\s,]+/);
      svg.setAttribute("width", w);
      svg.setAttribute("height", h);
    }
    drawings.set(key, URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" })));
  }
  return drawings.get(key);
}

// ---------- plots of trials ----------

// Round tick values spanning lo..hi, about five of them.
function ticks(lo, hi) {
  if (lo === hi) [lo, hi] = [lo - 1, hi + 1];
  const rough = (hi - lo) / 5, mag = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((k) => k * mag).find((k) => k >= rough);
  const first = Math.floor(lo / step) * step, n = Math.round((Math.ceil(hi / step) * step - first) / step);
  return Array.from({ length: n + 1 }, (_, i) => +(first + i * step).toPrecision(12));
}

// A turn's measurements as a line chart: one line per run.
function chart(m, prefix = "") {
  const pts = m.series.flatMap((s) => s.points), xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  let ylo = Math.min(...ys);
  const yhi = Math.max(...ys);
  if (ylo >= 0 && yhi - ylo > 0.2 * yhi) ylo = 0; // magnitudes start at zero, unless that would flatten them
  const X = ticks(Math.min(...xs), Math.max(...xs)), Y = ticks(ylo, yhi);
  const W = 480, H = 210, L = 44, R = 12, T = 24, B = 38;
  const sx = (x) => (L + ((x - X[0]) / (X.at(-1) - X[0])) * (W - L - R)).toFixed(1);
  const sy = (y) => (H - B - ((y - Y[0]) / (Y.at(-1) - Y[0])) * (H - T - B)).toFixed(1);
  const lines = m.series.map((s, i) => {
    const p = [...s.points].sort((a, b) => a[0] - b[0]).map(([x, y]) => [sx(x), sy(y)]);
    return `<g class="s${i % 5}"><polyline points="${p.join(" ")}"/>${p.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="2.6"/>`).join("")}</g>`;
  });
  return `<figure class="chart">
    <figcaption>${esc(prefix + m.title)}</figcaption>
    ${m.series.length > 1 ? `<div class="legend">${m.series.map((s, i) => `<span class="s${i % 5}"><i></i>${esc(s.name ?? `run ${i + 1}`)}</span>`).join("")}</div>` : ""}
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(m.title)}">
      ${Y.map((v) => `<line class="grid" x1="${L}" x2="${W - R}" y1="${sy(v)}" y2="${sy(v)}"/><text x="${L - 6}" y="${+sy(v) + 4}" text-anchor="end">${v}</text>`).join("")}
      <line class="axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/>
      ${X.map((v) => `<line class="axis" x1="${sx(v)}" x2="${sx(v)}" y1="${H - B}" y2="${H - B + 4}"/><text x="${sx(v)}" y="${H - B + 17}" text-anchor="middle">${v}</text>`).join("")}
      <text class="label" x="${L}" y="${T - 10}">${esc(m.y)}</text>
      <text class="label" x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle">${esc(m.x)}</text>
      ${lines.join("")}
    </svg>
  </figure>`;
}

// ---------- views ----------

async function card(t) {
  const url = await drawing(t);
  const qty = t.quantity !== undefined ? `<span class="qty">${t.quantity} ${esc(t.unit ?? "")}</span>` : "";
  return `<a class="card${fresh.has(t.id) ? " fresh" : ""}" data-status="${t.status}" href="#/thing/${t.id}">
    <div class="thumb">${url ? `<img src="${url}" alt="">` : glyph(t.kind)}</div>
    <div class="card-body">
      <h3>${esc(t.name)}</h3>
      <div class="meta">${stamp(t.status)} ${qty} ${t.owner ? `<span class="owner">${esc(t.owner)}</span>` : ""}</div>
      <p>${esc(t.summary)}</p>
    </div>
  </a>`;
}

// What's ahead, from world.json's coming_up: a note, not a calendar.
function comingUp() {
  const items = (S.coming_up ?? []).slice(0, 5);
  return items.length ? `<aside class="coming-up"><h2>Coming up</h2><table>${items.map((c) =>
    `<tr><td class="date">${esc(c.label)}</td><td class="away">${esc(c.in)}</td><td>${inline(c.what)}</td></tr>`).join("")}</table></aside>` : "";
}

// The drawings changed most recently, newest first.
async function recentDrawings() {
  if (!S.log.length) return ""; // a new save's drawings all date from the scenario
  const recent = Object.entries(S.visuals).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const items = await Promise.all(recent.map(async ([path, v]) => {
    const thing = S.things.find((t) => t.visual === path);
    const url = await drawing(thing ?? { visual: path, _v: v });
    return `<a class="recent" ${opens(thing, url)}><span class="thumb"><img src="${url}" alt=""></span><span class="caption">${esc(caption(path, thing))}</span></a>`;
  }));
  return `<section><h2>Recent drawings</h2><div class="recent-row">${items.join("")}</div></section>`;
}

// The top of the Workshop: the last turn, to pick up from.
function lastTurn() {
  const e = S.log.at(-1);
  if (!e) return "";
  let chars = 0;
  const paras = e.narration.split(/\n+/), shown = paras.filter((p) => (chars += p.length) < 700 || chars === p.length);
  return `<article class="last-turn${fresh.has("t:" + e.turn) ? " fresh" : ""}">
    <div class="kicker">Where you left off</div>
    <header><span class="turn-no">Turn ${e.turn}</span> <span class="when">${span(e.clock_start, e.clock_end)}</span></header>
    <blockquote class="order">${esc(e.action)}</blockquote>
    <div class="narration">${shown.map((p) => `<p>${inline(p)}</p>`).join("")}</div>
    <a class="more" href="#/journal">${shown.length < paras.length ? "Read on in the journal" : "The journal"} →</a>
  </article>`;
}

// Today's leaf of the almanac: the date, the sky, the purse and what's coming.
function almanac() {
  const w = S.world, s = sky(w.clock), [y, m, d] = w.clock.slice(0, 10).split("-").map(Number);
  const when = { night: "after dark", dusk: "dusk", dawn: "dawn", day: "daylight" }[s.phase];
  const items = (S.coming_up ?? []).slice(0, 5);
  return `<aside class="almanac">
    <div class="leaf${fresh.has("clock") ? " turned" : ""}">
      <div class="dow">${esc(S.clock_label.split(" ")[0])}</div>
      <div class="dom">${d}</div>
      <div class="month">${MONTHS[m - 1]} ${y}</div>
    </div>
    <p class="sky-line">${s.phase === "day" ? SUN : moonIcon(s.moon)} ${w.clock.slice(11)}, ${when}. Sun up ${hm(s.rise)}, down ${hm(s.set)}; a ${moonName(s.moon)}.</p>
    <p class="purse-line">In your purse ${spent ? `<span class="delta ${spent.p < 0 ? "down" : "up"}">${spent.p > 0 ? "+" : ""}${money(spent.p)}</span>` : ""}<b class="${w.purse_p < 0 ? "debt" : ""}">${money(w.purse_p)}</b></p>
    ${items.length ? `<h3>Coming up</h3><ul class="days">${items.map((c) => `<li><span class="date">${esc(c.label)}</span> <span class="away">${esc(c.in)}</span><div>${inline(c.what)}</div></li>`).join("")}</ul>` : ""}
  </aside>`;
}

// A list that can be folded away; long ones start folded.
const foldable = (key, title, items) => (items?.length ? `<details class="fold" data-key="${key}" ${items.length > 6 ? "" : "open"}>
  <summary><h2>${title} <span class="count">${items.length}</span></h2></summary><ul class="threads">${items.map((t) => `<li>${inline(t)}</li>`).join("")}</ul></details>` : "");

async function workshop() {
  const cards = async (things) => `<div class="cards">${(await Promise.all(things.map(card))).join("")}</div>`;
  const mine = S.things.filter((t) => !t.owner);
  const groups = Object.keys(KINDS).map((k) => [k, mine.filter((t) => t.kind === k)]).filter(([, ts]) => ts.length);
  const others = S.things.filter((t) => t.owner);
  const briefing = `<details class="briefing" data-key="briefing" ${S.log.length ? "" : "open"}><summary>Briefing</summary>${markdown(S.briefing)}</details>`;
  return `
    <div class="desk"><div>${S.log.length ? lastTurn() + (await recentDrawings()) : briefing}</div>${almanac()}</div>
    ${S.log.length ? briefing : ""}
    ${foldable("threads", "Open threads", S.world.threads)}
    ${foldable("house-rules", "House rules", S.world.house_rules)}
    ${(await Promise.all(groups.map(async ([k, ts]) => `<section><h2>${KINDS[k]}</h2>${await cards(ts)}</section>`))).join("")}
    ${S.stores.length ? `<section class="listing"><h2>Stores</h2><table><tr><th>Item</th><th>Quantity</th><th>Where</th><th>Notes</th></tr>
      ${S.stores.map((s) => `<tr><td>${esc(s.name)}</td><td>${s.quantity} ${esc(s.unit)}</td><td>${esc(s.location ?? "")}</td><td>${esc(s.notes ?? "")}</td></tr>`).join("")}</table></section>` : ""}
    ${others.length ? `<section><h2>Not yours</h2>${await cards(others)}</section>` : ""}`;
}

async function thingPage(id, query) {
  const t = S.things.find((x) => x.id === id);
  if (!t) return `<p class="empty">Nothing called “${esc(id)}”.</p>`;
  const state = query.get("state") ?? t.state ?? t.states?.[0] ?? "";
  const url = await drawing(t, state);
  const byId = Object.fromEntries(S.things.map((x) => [x.id, x]));
  const link = (x) => `<a href="#/thing/${x.id}">${esc(x.name)}</a>`;
  const flawCount = (x) => (x?.flaws?.length ? ` <span class="flag">${x.flaws.length} flaw${x.flaws.length > 1 ? "s" : ""}</span>` : "");
  const m = t.made;
  const trials = S.log.flatMap((e) => (e.measurements ?? []).filter((x) => x.thing === t.id).map((x) => chart(x, `Turn ${e.turn}: `))).reverse();
  const madeRows = m && [["by", m.by?.join(", ")], ["took", m.took], ["cost", m.cost_p !== undefined && money(m.cost_p)], ["turn", m.turn]].filter(([, v]) => v || v === 0);
  return `<article class="sheet">
    <a class="back" href="#/workshop">← Workshop</a>
    <header>
      <h1>${esc(t.name)}</h1>
      <div class="meta">${stamp(t.status)} ${esc(t.kind)}${t.quantity !== undefined ? ` · ${t.quantity} ${esc(t.unit ?? "")}` : ""}${t.location ? ` · ${esc(t.location)}` : ""}${t.owner ? ` · belongs to ${esc(t.owner)}` : ""}</div>
      <p class="summary">${esc(t.summary)}</p>
    </header>
    <div class="sheet-body">
      <figure class="plate">
        ${url ? `<img src="${url}" alt="${esc(t.name)}">` : `<div class="no-drawing">No drawing yet</div>`}
        ${t.states?.length > 1 ? `<nav class="states">${t.states.map((s) => `<a href="#/thing/${t.id}?state=${esc(s)}" class="${s === state ? "on" : ""}">${esc(s)}</a>`).join("")}</nav>` : ""}
      </figure>
      <div class="spec">
        ${bullets("Known flaws", t.flaws?.map(esc), "flaws")}
        ${trials.length ? `<h3>Trials</h3>${trials.join("")}` : ""}
        ${bullets("Materials", t.materials?.map(esc))}
        ${facts("Dimensions", t.dimensions)}
        ${facts("Performance", t.performance)}
        ${facts("Quality", t.quality)}
        ${bullets("Components", t.components?.map((c) => (byId[c] ? link(byId[c]) + flawCount(byId[c]) : esc(c))))}
        ${bullets("Used in", S.things.filter((x) => x.components?.includes(t.id)).map(link))}
        ${m ? `<h3>How it was made</h3><p>${esc(m.how)}</p><dl>${madeRows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>${m.recipe ? `<p class="recipe">Made by a known recipe: <a href="#/capabilities">${esc(S.recipes.find((r) => r.id === m.recipe)?.name ?? m.recipe)}</a></p>` : ""}` : ""}
        ${t.historical_year ? `<p class="dated">First made in real history: ${t.historical_year}.</p>` : ""}
        ${fermi(t.fermi)}
        ${t.notes ? `<h3>Notes</h3><p>${esc(t.notes)}</p>` : ""}
        ${historyNotes(t.history)}
      </div>
    </div>
  </article>`;
}

// Everything the player has that the real world didn't have yet, furthest ahead first.
function aheadOfHistory() {
  const year = Number(S.world.clock.slice(0, 4));
  return [
    ...S.things.filter((t) => !t.owner && ["ok", "faulty"].includes(t.status)).map((t) => ({ name: t.name, kind: t.kind, href: `#/thing/${t.id}`, year: t.historical_year })),
    ...S.recipes.map((r) => ({ name: r.name, kind: "capability", href: "#/capabilities", year: r.historical_year })),
  ].filter((x) => x.year > year).map((x) => ({ ...x, ahead: x.year - year })).sort((a, b) => b.ahead - a.ahead);
}

// Everything ahead of history on one time line: each row runs from now to the year the real world caught up.
function aheadChart(ahead) {
  const now = Number(S.world.clock.slice(0, 4)), Y = ticks(now, Math.max(...ahead.map((x) => x.year)));
  const W = 1000, L = 290, R = 150, row = 30, T = 44, H = T + ahead.length * row + 8;
  const sx = (y) => (L + ((y - now) / (Y.at(-1) - now)) * (W - L - R)).toFixed(1);
  return `<figure class="timeline"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Ahead of history">
    ${Y.filter((y) => y - now > (Y.at(-1) - now) / 12).map((y) => `<line class="grid" x1="${sx(y)}" x2="${sx(y)}" y1="${T - 10}" y2="${H}"/><text class="tick" x="${sx(y)}" y="${T - 16}" text-anchor="middle">${y}</text>`).join("")}
    <line class="now" x1="${sx(now)}" x2="${sx(now)}" y1="${T - 26}" y2="${H}"/>
    <text class="now-label" x="${+sx(now) - 7}" y="${T - 16}" text-anchor="end">now, ${now}</text>
    ${ahead.map((x, i) => {
      const y = T + i * row + row / 2;
      return `<a href="${x.href}"><title>${esc(x.name)}: first made in ${x.year}</title>
        <rect class="hit" x="0" y="${y - row / 2}" width="${W}" height="${row}"/>
        <text class="name" x="${L - 16}" y="${y + 5}" text-anchor="end">${esc(x.name)}</text>
        <line class="span" x1="${sx(now)}" x2="${sx(x.year)}" y1="${y}" y2="${y}"/>
        <circle class="pin" cx="${sx(now)}" cy="${y}" r="3"/><circle class="real" cx="${sx(x.year)}" cy="${y}" r="4.5"/>
        <text class="ahead-by" x="${W - R + 14}" y="${y + 5}">${x.year} · ${x.ahead} year${x.ahead === 1 ? "" : "s"} early</text></a>`;
    }).join("")}
  </svg></figure>`;
}

function capabilities() {
  const ahead = aheadOfHistory();
  const aheadTable = ahead.length ? `<section><h2>Ahead of history</h2>
    <p class="hint">What you have that the real world didn't yet: a dot marks the year history made it.</p>${aheadChart(ahead)}</section>` : "";
  if (!S.recipes.length) return aheadTable + `<p class="empty">No capabilities yet. Once you've made something that can be made again, the referee writes down how, and you can simply order more.</p>`;
  const year = Number(S.world.clock.slice(0, 4));
  const name = (records, id) => esc(records.find((x) => x.id === id)?.name ?? id);
  return aheadTable + `<section><h2>Capabilities</h2><div class="cards recipes">${S.recipes.map((r) => `
    <div class="card${fresh.has("r:" + r.id) ? " fresh" : ""}"><div class="card-body">
      <h3>${esc(r.name)}</h3>
      <div class="meta">${esc(r.time)} · ${money(r.cost_p)} each${r.historical_year > year ? ` · <span class="ahead">${r.historical_year - year} years ahead of history</span>` : ""}</div>
      <p>${esc(r.makes)}</p>
      <div class="spec">
        <h3>Method</h3><p>${esc(r.how)}</p>
        ${facts("Reliably achieves", r.quality)}
        ${bullets("Needs", [...(r.tools ?? []).map((t) => `<a href="#/thing/${t}">${name(S.things, t)}</a>`), ...(r.inputs ?? []).map(esc)])}
        ${bullets("Who knows how", (r.people ?? []).map((p) => name(S.people, p)))}
        ${bullets("Known flaws", r.flaws?.map(esc), "flaws")}
        ${r.first_made ? `<p class="dated">First made: <a href="#/thing/${r.first_made}">${name(S.things, r.first_made)}</a>${r.turn ? `, turn ${r.turn}` : ""}.</p>` : ""}
        ${r.notes ? `<p>${esc(r.notes)}</p>` : ""}
      </div>
    </div></div>`).join("")}</div></section>`;
}

function people() {
  const me = S.world.player;
  const you = `<div class="card person you"><div class="card-body">
    <header class="who"><span class="cameo">${esc(initials(me.name || "You"))}</span><div><h3>${esc(me.name || "You")}</h3><div class="meta">you</div></div></header>
    <p class="attitude">${esc(me.status)}</p>
    ${me.skills?.length ? `<p class="skills">${me.skills.map(esc).join(" · ")}</p>` : ""}
    ${me.reputation ? `<p><b>Reputation:</b> ${esc(me.reputation)}</p>` : ""}
    ${me.health ? `<p><b>Health:</b> ${esc(me.health)}</p>` : ""}
    ${me.notes ? `<p>${esc(me.notes)}</p>` : ""}
  </div></div>`;
  const last = (p) => Math.max(0, ...(p.history ?? []).map((h) => h.turn));
  const cast = [...S.people].sort((a, b) => !!b.employed - !!a.employed || last(b) - last(a)); // your people, then the most recently met
  return `<div class="people">${you}${cast.map((p) => `
    <div class="card person${p.employed ? " yours" : ""}${fresh.has("p:" + p.id) ? " fresh" : ""}"><div class="card-body">
      <header class="who"><span class="cameo">${esc(initials(p.name))}</span><div>
        <h3>${esc(p.name)}</h3>
        <div class="meta">${esc(p.role)}${p.employed ? ` · <b>works for you</b>${p.wage_p_week ? `, ${money(p.wage_p_week)} a week` : ""}` : ""}</div>
      </div></header>
      ${p.attitude ? `<p class="attitude">${esc(p.attitude)}</p>` : ""}
      ${p.skills?.length ? `<p class="skills">${p.skills.map(esc).join(" · ")}</p>` : ""}
      <p class="where">${esc(p.location ?? "")}${last(p) ? `${p.location ? " · " : ""}last dealt with in turn ${last(p)}` : ""}</p>
      ${p.notes || p.history?.length ? `<details data-key="p:${esc(p.id)}"><summary>Notes and history</summary>${p.notes ? `<p>${esc(p.notes)}</p>` : ""}${historyNotes(p.history)}</details>` : ""}
    </div></div>`).join("")}</div>`;
}

// A drawing listed in a turn's visuals, as it was when that turn ended: read from the save's history once a
// later turn has been snapshotted, else the current file. Nothing is redrawn.
async function illustration(path, turn) {
  const thing = S.things.find((t) => t.visual === path);
  const rev = S.snapshots?.[turn];
  let item = thing ?? { visual: path, _v: S.visuals[path] };
  if (rev && (await fetchText(`/api/rev/${rev}/${path}`)) !== null) {
    const then = thing && JSON.parse((await fetchText(`/api/rev/${rev}/things/${thing.id}.json`)) ?? "null");
    item = { visual: path, _v: rev, _rev: rev, state: (then ?? thing)?.state, states: (then ?? thing)?.states };
  }
  const url = await drawing(item);
  return url ? `<a class="illus" ${opens(thing, url)}><img src="${url}" alt=""><span class="caption">${esc(caption(path, thing))}</span></a>` : "";
}

async function journal() {
  if (!S.log.length) return `<p class="empty">Nothing has happened yet. The journal fills in as you play.</p>`;
  const workings = (title, items) => (items?.length ? `<h4>${title}</h4><ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : "");
  const entry = async (e) => `
    <article class="entry${fresh.has("t:" + e.turn) ? " fresh" : ""}">
      <header><span class="turn-no">Turn ${e.turn}</span> <span class="when">${span(e.clock_start, e.clock_end)}</span></header>
      <blockquote class="order">${esc(e.action)}</blockquote>
      ${e.sketches?.length ? `<div class="entry-sketches">${e.sketches.map((s) => `<a href="/save/${s}" target="_blank"><img src="/save/${s}" alt="${s}"></a>`).join("")}</div>` : ""}
      ${e.visuals?.length ? `<div class="illustrations">${(await Promise.all(e.visuals.map((v) => illustration(v, e.turn)))).join("")}</div>` : ""}
      ${(e.measurements ?? []).map((x) => chart(x)).join("")}
      <div class="narration">${e.narration.split(/\n+/).map((p) => `<p>${inline(p)}</p>`).join("")}</div>
      <details data-key="w${e.turn}"><summary>How the referee ruled</summary>
        ${workings("Credited to you", e.specified)}${workings("Filled in with standard period practice", e.assumed)}
        ${workings("Rulings", e.rulings)}${workings("Changes", e.changes)}
        ${fermi(e.fermi)}
      </details>
    </article>`;
  const months = []; // [yyyy-mm, entries], newest first
  for (const e of [...S.log].reverse()) {
    if (months.at(-1)?.[0] !== e.clock_start.slice(0, 7)) months.push([e.clock_start.slice(0, 7), []]);
    months.at(-1)[1].push(e);
  }
  const title = (ym) => `${MONTHS[+ym.slice(5) - 1]} ${ym.slice(0, 4)}`;
  const chapters = await Promise.all(months.map(async ([ym, es]) =>
    `<h2 class="chapter" id="ch-${ym}"><span>${title(ym)}</span></h2>${(await Promise.all(es.map(entry))).join("")}`));
  return `<div class="journal">
    <nav class="chapters">${months.map(([ym, es]) => `<a data-jump="ch-${ym}">${title(ym)}<span>turn${es.length > 1 ? `s ${es.at(-1).turn}–${es[0].turn}` : ` ${es[0].turn}`}</span></a>`).join("")}</nav>
    <div class="pages"><div class="journal-head">${comingUp()}</div>${chapters.join("")}</div>
  </div>`;
}

async function map(id) {
  if (!S.maps.length) return `<p class="empty">No maps yet. The referee draws them as places come up.</p>`;
  const m = S.maps.find((x) => x.id === (id ?? lastMap)) ?? S.maps[0];
  lastMap = m.id;
  const [url, svg] = await Promise.all([drawing(m), svgText(m)]);
  mapToMount = { m, svg };
  return `<nav class="states map-list">${S.maps.map((x) => `<a href="#/map/${x.id}" class="${x === m ? "on" : ""}">${esc(x.title)}</a>`).join("")}</nav>
    <figure class="plate map${fresh.has("m:" + m.id) ? " fresh" : ""}"><div class="map-host"></div><div class="place-card" hidden></div></figure>
    <a class="full-size" href="${url}" target="_blank">Open full size</a>
    ${gazetteer(m.id)}`;
}

// Places are matched to map labels by name, ignoring a leading "the" or "your".
const plain = (s) => s.toLowerCase().replace(/\s+/g, " ").trim().replace(/^(the|your) /, "");
const mentions = (text, name) => plain(text ?? "").includes(plain(name));
const byPlaceId = () => Object.fromEntries(S.places.places.map((p) => [p.id, p]));
const dist = (p, o) => Math.hypot(p.x_km - o.x_km, p.y_km - o.y_km);
const where = (p, o) => `${dist(p, o).toFixed(1)} km ${COMPASS[Math.round((Math.atan2(p.x_km - o.x_km, p.y_km - o.y_km) * 180) / Math.PI / 22.5 + 16) % 16]}`;

// Draw the map into the page, in a shadow root so its ids and styles stay its own, and make place labels clickable.
function mountMap(host, { m, svg }) {
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `<style>
    svg { display: block; width: 100%; height: auto; max-height: calc(100vh - 230px); }
    text.place { cursor: pointer; }
    text.place:hover, text.place.on { fill: #9c3b25; }
  </style>${svg}`;
  const places = S.places.places.filter((p) => p.maps.includes(m.id));
  for (const label of root.querySelectorAll("text")) {
    const hits = places.filter((p) => mentions(label.textContent, p.name));
    if (!hits.length) continue;
    label.classList.add("place");
    label.addEventListener("click", (e) => (e.stopPropagation(), showPlaces(hits, label)));
  }
  host.addEventListener("click", closePlaces);
}

// A card of what the player knows about some places, next to the label they clicked.
function showPlaces(places, label) {
  const root = label.getRootNode(), figure = root.host.closest("figure"), card = figure.querySelector(".place-card");
  root.querySelectorAll("text.on").forEach((t) => t.classList.remove("on"));
  label.classList.add("on");
  card.innerHTML = `<button class="close" title="Close">×</button>${places.map(placeInfo).join("")}`;
  card.querySelector(".close").onclick = closePlaces;
  card.hidden = false;
  const box = label.getBoundingClientRect(), frame = figure.getBoundingClientRect();
  const below = box.bottom - frame.top + 8, above = box.top - frame.top - card.offsetHeight - 8;
  card.style.left = `${Math.max(10, Math.min(box.left - frame.left, frame.width - card.offsetWidth - 10))}px`;
  card.style.top = `${below + card.offsetHeight > frame.height && above > 0 ? above : below}px`;
}

function closePlaces() {
  const card = document.querySelector(".place-card");
  if (!card || card.hidden) return;
  card.hidden = true;
  document.querySelector(".map-host")?.shadowRoot?.querySelectorAll("text.on").forEach((t) => t.classList.remove("on"));
}

function placeInfo(p) {
  const byId = byPlaceId(), o = byId[S.places.origin];
  const thing = S.things.find((t) => t.id === p.thing);
  const people = S.people.filter((x) => mentions(x.location, p.name));
  const routes = S.places.routes.filter((r) => r.from === p.id || r.to === p.id);
  const turns = S.log.filter((e) => mentions(e.narration, p.name)).map((e) => e.turn);
  return `<div class="place-info">
    <h3>${esc(p.name)}</h3>
    <div class="meta">${esc(p.kind)}${o && p !== o ? ` · ${where(p, o)} from ${esc(o.name)}` : ""} · ${p.visited ? "you've been here" : "not visited yet"}</div>
    ${p.notes ? `<p>${esc(p.notes)}</p>` : ""}
    ${thing ? `<p><a href="#/thing/${thing.id}">${esc(thing.name)}</a> ${stamp(thing.status)} ${esc(thing.summary)}</p>` : ""}
    ${people.length ? `<h4>People here</h4><ul>${people.map((x) => `<li>${esc(x.name)}, ${esc(x.role)}</li>`).join("")}</ul>` : ""}
    ${routes.length ? `<h4>Routes</h4><ul>${routes.map((r) => `<li>${esc(byId[r.from === p.id ? r.to : r.from]?.name ?? "?")}: ${r.km} km by ${r.by}, ${esc(r.time)}</li>`).join("")}</ul>` : ""}
    ${turns.length ? `<p class="dated">In your <a href="#/journal">journal</a>: turn${turns.length > 1 ? "s" : ""} ${turns.join(", ")}</p>` : ""}
  </div>`;
}

// The places on a map, nearest to the origin first, and the routes between them. Clicking a row shows it on the map.
function gazetteer(mapId) {
  const g = S.places, byId = byPlaceId(), o = byId[g.origin];
  if (!o) return "";
  const here = g.places.filter((p) => p.maps.includes(mapId));
  const rows = here.sort((a, b) => dist(a, o) - dist(b, o)).map((p) => `<tr data-place="${p.id}"${p.visited ? ' class="visited"' : ""}>
    <td>${esc(p.name)}</td><td>${esc(p.kind)}</td><td>${p === o ? "" : where(p, o)}</td><td>${esc(p.notes ?? "")}</td></tr>`);
  const ids = new Set(here.map((p) => p.id));
  const routes = g.routes.filter((r) => ids.has(r.from) && ids.has(r.to))
    .map((r) => `<li>${esc(byId[r.from].name)} – ${esc(byId[r.to].name)}: ${r.km} km by ${r.by}, ${esc(r.time)}${r.notes ? `. ${esc(r.notes)}` : ""}</li>`);
  return `<section class="listing"><h2>Places</h2><table><tr><th>Place</th><th>Kind</th><th>From ${esc(o.name)}</th><th>Notes</th></tr>${rows.join("")}</table>
    ${routes.length ? `<h2>Routes</h2><ul>${routes.join("")}</ul>` : ""}</section>`;
}

// One drawing alone, for screenshots: a thing's, or any other drawing in visuals/ (e.g. a scene).
async function plate(id, query) {
  const path = `visuals/${id}.svg`;
  const t = S.things.find((x) => x.id === id) ?? (S.visuals[path] && { visual: path, _v: S.visuals[path] });
  const url = t && (await drawing(t, query.get("state") ?? undefined));
  return url ? `<div class="bare-plate"><img src="${url}" alt=""></div>` : `<p class="empty">No drawing for “${esc(id)}”.</p>`;
}

// ---------- page ----------

function masthead(route) {
  $("#problems").hidden = !S.problems.length;
  $("#problems").innerHTML = `<b>State problems</b> (the referee should fix these)<ul>${S.problems.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>`;
  const w = S.world;
  if (!w.clock) return; // world.json is broken; the problems say why
  const ahead = aheadOfHistory()[0];
  $("#title").textContent = w.title;
  $("#clock").textContent = S.clock_label;
  const s = sky(w.clock);
  $("#sky").innerHTML = s.phase === "day" ? SUN : moonIcon(s.moon);
  $("#sky").title = `Sunrise ${hm(s.rise)}, sunset ${hm(s.set)}; ${moonName(s.moon)}`;
  document.body.dataset.sky = s.phase;
  $("#place").textContent = w.location;
  $("#purse").textContent = money(w.purse_p);
  $("#purse").classList.toggle("debt", w.purse_p < 0);
  $("#save").textContent = `save: ${S.save}`;
  document.title = `${w.title} · ${S.save}`;
  $("#turn").textContent = `turn ${S.log.length}`;
  $("#ahead").textContent = ahead ? `· ${ahead.ahead} years ahead of history` : "";
  $("#ahead").title = ahead ? `Furthest ahead: ${ahead.name}. See all.` : "";
  const tab = route === "thing" ? "workshop" : route;
  document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("on", a.getAttribute("href") === `#/${tab}`));
}

async function render() {
  if (!S) return;
  const id = ++renderId;
  document.body.dataset.ready = "0";
  const [path, q] = location.hash.slice(2).split("?");
  const [route = "workshop", arg] = path.split("/");
  const query = new URLSearchParams(q);
  masthead(route);
  document.body.classList.toggle("bare", route === "visual");
  $("#sketch").hidden = route !== "sketch";
  const main = $("#main");
  main.hidden = route === "sketch";
  if (route === "sketch") sketch.refresh();
  const views = { workshop, thing: thingPage, capabilities, people, map, journal, visual: plate, sketch: () => "" };
  const broken = `<p class="empty">world.json is broken, so there's nothing to show until the referee fixes the problems above.</p>`;
  const html = S.world.clock ? await (views[route] ?? workshop)(arg, query) : broken;
  if (id !== renderId) return; // a newer render started meanwhile
  const navigated = location.hash !== shownHash;
  if (navigated) scrolls[shownHash] = scrollY;
  main.innerHTML = html;
  if (route === "map" && mapToMount) mountMap(main.querySelector(".map-host"), mapToMount);
  main.querySelectorAll("details[data-key]").forEach((d) => d.dataset.key in opened && (d.open = opened[d.dataset.key]));
  await Promise.all([...main.querySelectorAll("img")].map((img) => img.decode().catch(() => {})));
  await document.fonts.ready;
  if (id !== renderId) return;
  if (navigated) scrollTo(0, scrolls[location.hash] ?? 0);
  shownHash = location.hash;
  document.body.dataset.ready = "1";
}

function markFresh(next) {
  const keyed = [...next.things.map((t) => [t.id, t]), ...next.people.map((p) => ["p:" + p.id, p]), ...next.recipes.map((r) => ["r:" + r.id, r]), ...next.maps.map((m) => ["m:" + m.id, m]), ...next.log.map((e) => ["t:" + e.turn, e])];
  const changed = seen.size ? keyed.filter(([k, v]) => seen.get(k) !== JSON.stringify(v)).map(([k]) => k) : [];
  seen = new Map(keyed.map(([k, v]) => [k, JSON.stringify(v)]));
  if (S?.world.clock && next.world.clock !== S.world.clock) changed.push("clock");
  if (S?.world.purse_p !== undefined && next.world.purse_p !== S.world.purse_p) {
    const now = (spent = { p: next.world.purse_p - S.world.purse_p });
    setTimeout(() => spent === now && (spent = null), 8000);
  }
  changed.forEach((k) => fresh.add(k));
  setTimeout(() => changed.forEach((k) => fresh.delete(k)), 5000);
}

function toast(message, href) {
  const el = $("#toast");
  el.textContent = message;
  el.onclick = href ? () => (location.hash = href) : null;
  el.style.cursor = href ? "pointer" : "";
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), 7000);
}

// Clicking a row of the places table shows that place on the map; the journal's index jumps to a month.
document.addEventListener("click", (e) => {
  const jump = e.target.closest?.("[data-jump]");
  if (jump) return document.getElementById(jump.dataset.jump)?.scrollIntoView({ behavior: "smooth" });
  const row = e.target.closest?.("tr[data-place]");
  const place = row && byPlaceId()[row.dataset.place];
  const label = place && [...(document.querySelector(".map-host")?.shadowRoot?.querySelectorAll("text.place") ?? [])].find((t) => mentions(t.textContent, place.name));
  if (!label) return;
  label.scrollIntoView({ block: "center" });
  showPlaces([place], label);
});
addEventListener("keydown", (e) => e.key === "Escape" && closePlaces());

// Remember which sections are open; Fermi scripts load when opened.
document.addEventListener("toggle", async (e) => {
  const d = e.target;
  if (!d.matches?.("details[data-key]")) return;
  opened[d.dataset.key] = d.open;
  localStorage.setItem("opened", JSON.stringify(opened));
  if (d.dataset.src && d.open) d.querySelector("pre").textContent = await (await fetch(`/save/${d.dataset.src}`)).text();
}, true);

const sketch = initSketch($("#sketch"), {
  toast,
  traces: () => [
    ...S.things.filter((t) => t.visual && t._v).map((t) => ({ key: "t:" + t.id, label: t.name, url: () => drawing(t) })),
    ...S.maps.map((m) => ({ key: "m:" + m.id, label: `Map: ${m.title}`, url: () => drawing(m) })),
    ...S.sketches.map((s) => ({ key: s, label: `Sketch ${s.slice(9, 13)}`, url: async () => `/save/${s}` })),
  ],
  sketchbook: () => S.sketches.map((path) => ({ path, turns: S.log.filter((t) => t.sketches?.includes(path)).map((t) => t.turn) })),
});

const events = new EventSource("/api/events");
events.onopen = () => $("#live").classList.add("on");
events.onerror = () => $("#live").classList.remove("on");
events.onmessage = async () => {
  const next = await (await fetch("/api/state")).json();
  const drawn = S && next.log.filter((e) => e.turn > S.log.length && e.visuals?.length).at(-1);
  if (drawn) toast(`New drawings in turn ${drawn.turn}: click to see them in the Journal.`, "#/journal");
  markFresh(next);
  S = next;
  render();
};
addEventListener("hashchange", render);
