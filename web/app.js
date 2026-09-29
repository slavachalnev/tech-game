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
const list = (title, items, cls = "") => (items?.length ? `<h3>${title}</h3><ul class="${cls}">${items.map((i) => `<li>${i}</li>`).join("")}</ul>` : "");
const table = (title, obj) =>
  obj && Object.keys(obj).length
    ? `<h3>${title}</h3><dl>${Object.entries(obj).map(([k, v]) => prop(k, v)).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`
    : "";
const fermi = (paths) =>
  paths?.length
    ? `<h3>Fermi estimates</h3>${paths.map((p) => `<details class="fermi" data-key="${esc(p)}" data-src="${esc(p)}"><summary>${esc(p)}</summary><pre>…</pre></details>`).join("")}`
    : "";
const history = (items) => list("History", items?.map((h) => `<span class="turn-ref">Turn ${h.turn}.</span> ${esc(h.note)}`), "history");

// ---------- drawings ----------

const sources = new Map(); // "path@version" -> SVG text
const drawings = new Map(); // "path@version@state" -> object URL

async function svgText(item) {
  const key = `${item.visual}@${item._v}`;
  if (!sources.has(key)) sources.set(key, await (await fetch(`/save/${item.visual}`)).text());
  return sources.get(key);
}

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

// ---------- views ----------

async function card(t) {
  const url = await drawing(t);
  const qty = t.quantity !== undefined ? `<span class="qty">${t.quantity} ${esc(t.unit ?? "")}</span>` : "";
  return `<a class="card${fresh.has(t.id) ? " fresh" : ""}" href="#/thing/${t.id}">
    <div class="thumb">${url ? `<img src="${url}" alt="">` : `<span class="initial">${esc(t.name[0])}</span>`}</div>
    <div class="card-body">
      <h3>${esc(t.name)}</h3>
      <div class="meta">${stamp(t.status)} ${qty} ${t.owner ? `<span class="owner">${esc(t.owner)}</span>` : ""}</div>
      <p>${esc(t.summary)}</p>
    </div>
  </a>`;
}

async function workshop() {
  const cards = async (things) => `<div class="cards">${(await Promise.all(things.map(card))).join("")}</div>`;
  const mine = S.things.filter((t) => !t.owner);
  const groups = Object.keys(KINDS).map((k) => [k, mine.filter((t) => t.kind === k)]).filter(([, ts]) => ts.length);
  const others = S.things.filter((t) => t.owner);
  return `
    <details class="briefing" data-key="briefing" ${S.log.length ? "" : "open"}><summary>Briefing</summary>${markdown(S.briefing)}</details>
    ${S.world.threads.length ? `<section><h2>Open threads</h2><ul class="threads">${S.world.threads.map((t) => `<li>${inline(t)}</li>`).join("")}</ul></section>` : ""}
    ${S.world.house_rules?.length ? `<section><h2>House rules</h2><ul class="threads">${S.world.house_rules.map((t) => `<li>${inline(t)}</li>`).join("")}</ul></section>` : ""}
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
        ${list("Known flaws", t.flaws?.map(esc), "flaws")}
        ${list("Materials", t.materials?.map(esc))}
        ${table("Dimensions", t.dimensions)}
        ${table("Performance", t.performance)}
        ${table("Quality", t.quality)}
        ${list("Components", t.components?.map((c) => (byId[c] ? link(byId[c]) + flawCount(byId[c]) : esc(c))))}
        ${list("Used in", S.things.filter((x) => x.components?.includes(t.id)).map(link))}
        ${m ? `<h3>How it was made</h3><p>${esc(m.how)}</p><dl>${madeRows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>${m.recipe ? `<p class="recipe">Made by a known recipe: <a href="#/capabilities">${esc(S.recipes.find((r) => r.id === m.recipe)?.name ?? m.recipe)}</a></p>` : ""}` : ""}
        ${t.historical_year ? `<p class="dated">First made in real history: ${t.historical_year}.</p>` : ""}
        ${fermi(t.fermi)}
        ${t.notes ? `<h3>Notes</h3><p>${esc(t.notes)}</p>` : ""}
        ${history(t.history)}
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

function capabilities() {
  const ahead = aheadOfHistory();
  const table = ahead.length ? `<section class="listing"><h2>Ahead of history</h2><table>
    <tr><th>What</th><th>Kind</th><th>First in real history</th><th>Years ahead</th></tr>
    ${ahead.map((x) => `<tr><td><a href="${x.href}">${esc(x.name)}</a></td><td>${esc(x.kind)}</td><td>${x.year}</td><td>${x.ahead}</td></tr>`).join("")}</table></section>` : "";
  if (!S.recipes.length) return table + `<p class="empty">No capabilities yet. Once you've made something that can be made again, the referee writes down how, and you can simply order more.</p>`;
  const year = Number(S.world.clock.slice(0, 4));
  const name = (list, id) => esc(list.find((x) => x.id === id)?.name ?? id);
  return table + `<section><h2>Capabilities</h2><div class="cards recipes">${S.recipes.map((r) => `
    <div class="card${fresh.has("r:" + r.id) ? " fresh" : ""}"><div class="card-body">
      <h3>${esc(r.name)}</h3>
      <div class="meta">${esc(r.time)} · ${money(r.cost_p)} each${r.historical_year > year ? ` · <span class="ahead">${r.historical_year - year} years ahead of history</span>` : ""}</div>
      <p>${esc(r.makes)}</p>
      <div class="spec">
        <h3>Method</h3><p>${esc(r.how)}</p>
        ${table("Reliably achieves", r.quality)}
        ${list("Needs", [...(r.tools ?? []).map((t) => `<a href="#/thing/${t}">${name(S.things, t)}</a>`), ...(r.inputs ?? []).map(esc)])}
        ${list("Who knows how", (r.people ?? []).map((p) => name(S.people, p)))}
        ${list("Known flaws", r.flaws?.map(esc), "flaws")}
        ${r.first_made ? `<p class="dated">First made: <a href="#/thing/${r.first_made}">${name(S.things, r.first_made)}</a>${r.turn ? `, turn ${r.turn}` : ""}.</p>` : ""}
        ${r.notes ? `<p>${esc(r.notes)}</p>` : ""}
      </div>
    </div></div>`).join("")}</div></section>`;
}

function people() {
  return `<div class="cards people">${S.people.map((p) => `
    <div class="card person${fresh.has("p:" + p.id) ? " fresh" : ""}"><div class="card-body">
      <h3>${esc(p.name)}</h3>
      <div class="meta">${esc(p.role)}${p.employed ? ` · <b>employed by you</b>${p.wage_p_week ? `, ${money(p.wage_p_week)} a week` : ""}` : ""}</div>
      ${p.attitude ? `<p class="attitude">${esc(p.attitude)}</p>` : ""}
      ${p.skills?.length ? `<p class="skills">${p.skills.map(esc).join(" · ")}</p>` : ""}
      ${p.location ? `<p class="where">${esc(p.location)}</p>` : ""}
      ${p.notes ? `<p>${esc(p.notes)}</p>` : ""}
      ${history(p.history)}
    </div></div>`).join("")}</div>`;
}

// A drawing listed in a turn's visuals: a thing's links to its spec sheet, a scene opens full size.
async function illustration(path) {
  const thing = S.things.find((t) => t.visual === path);
  const url = await drawing(thing ?? { visual: path, _v: S.visuals[path] });
  return url ? `<a class="illus" href="${thing ? `#/thing/${thing.id}` : url}"${thing ? "" : ' target="_blank"'}><img src="${url}" alt=""></a>` : "";
}

async function journal() {
  if (!S.log.length) return `<p class="empty">Nothing has happened yet. The journal fills in as you play.</p>`;
  const workings = (title, items) => (items?.length ? `<h4>${title}</h4><ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : "");
  const entries = [...S.log].reverse().map(async (e) => `
    <article class="entry${fresh.has("t:" + e.turn) ? " fresh" : ""}">
      <header><span class="turn-no">Turn ${e.turn}</span> <span class="when">${span(e.clock_start, e.clock_end)}</span></header>
      <blockquote>${esc(e.action)}</blockquote>
      ${e.sketches?.length ? `<div class="entry-sketches">${e.sketches.map((s) => `<a href="/save/${s}" target="_blank"><img src="/save/${s}" alt="${s}"></a>`).join("")}</div>` : ""}
      ${e.visuals?.length ? `<div class="illustrations">${(await Promise.all(e.visuals.map(illustration))).join("")}</div>` : ""}
      <div class="narration">${e.narration.split(/\n+/).map((p) => `<p>${inline(p)}</p>`).join("")}</div>
      <details data-key="w${e.turn}"><summary>How the referee ruled</summary>
        ${workings("Credited to you", e.specified)}${workings("Filled in with standard period practice", e.assumed)}
        ${workings("Rulings", e.rulings)}${workings("Changes", e.changes)}
        ${fermi(e.fermi)}
      </details>
    </article>`);
  return (await Promise.all(entries)).join("");
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
  const w = S.world;
  const ahead = aheadOfHistory()[0];
  $("#title").textContent = w.title;
  $("#clock").textContent = S.clock_label;
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
  $("#problems").hidden = !S.problems.length;
  $("#problems").innerHTML = `<b>State problems</b> (the referee should fix these)<ul>${S.problems.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>`;
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
  const html = await (views[route] ?? workshop)(arg, query);
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

// Clicking a row of the places table shows that place on the map.
document.addEventListener("click", (e) => {
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
