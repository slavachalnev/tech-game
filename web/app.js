// Live view of a save. It only renders the state files; the referee (Claude Code) is the only writer.
import { initSketch } from "./sketch.js";

const $ = (sel) => document.querySelector(sel);
const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const KINDS = { machine: "Machines", component: "Components", structure: "Structures", tool: "Tools", material: "Materials", document: "Papers", site: "Sites", other: "Other" };
const STATUS = { planned: "planned", building: "building", ok: "sound", faulty: "faulty", broken: "broken", consumed: "used up" };
const UNIT = /^(.*?)_((?:in|ft|fm|yd|mi|mm|cm|m|lb|oz|cwt|tons?|kg|atm|psi|hp|gal|min|h|s|d|days|weeks|deg|pct)(?:_per_[a-z]+)?)$/;

let S = null; // latest state from the server
let seen = new Map(); // key -> JSON last rendered, to highlight what the referee just changed
const fresh = new Set();
let renderId = 0;

// ---------- formatting ----------

function money(d) {
  const a = Math.abs(d);
  const parts = [a >= 240 && `£${Math.floor(a / 240)}`, a % 240 >= 12 && `${Math.floor((a % 240) / 12)}s`, a % 12 && `${a % 12}d`];
  return (d < 0 ? "-" : "") + (parts.filter(Boolean).join(" ") || "0d");
}
function day(clock) {
  const [y, m, d] = clock.slice(0, 10).split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
const span = (a, b) => (day(a) === day(b) ? day(a) : `${day(a)} – ${day(b)}`);
function prop(key, value) {
  const m = key.match(UNIT);
  const name = (m ? m[1] : key).replace(/_/g, " ");
  if (m?.[2] === "d" && typeof value === "number") return [name, money(value)];
  return [m ? `${name} (${m[2].replace("_per_", "/")})` : name, value === true ? "yes" : value === false ? "no" : value];
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
    ? `<h3>Fermi workings</h3>${paths.map((p) => `<details class="fermi" data-key="${esc(p)}" data-src="${esc(p)}"><summary>${esc(p)}</summary><pre>…</pre></details>`).join("")}`
    : "";
const history = (items) => list("History", items?.map((h) => `<span class="turn-ref">Turn ${h.turn}.</span> ${esc(h.note)}`), "history");

// ---------- drawings ----------

const drawings = new Map(); // "path@version@state" -> object URL

// A thing's SVG, with only the groups for `state` kept, as an <img>-ready URL (isolates each drawing's ids and styles).
async function drawing(thing, state = thing.state ?? thing.states?.[0] ?? "") {
  if (!thing.visual || !thing._v) return null;
  const key = `${thing.visual}@${thing._v}@${state}`;
  if (!drawings.has(key)) {
    const text = await (await fetch(`/save/${thing.visual}`)).text();
    const svg = new DOMParser().parseFromString(text, "image/svg+xml").documentElement;
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
    ${S.world.threads.length ? `<section><h2>Open matters</h2><ul class="threads">${S.world.threads.map((t) => `<li>${inline(t)}</li>`).join("")}</ul></section>` : ""}
    ${(await Promise.all(groups.map(async ([k, ts]) => `<section><h2>${KINDS[k]}</h2>${await cards(ts)}</section>`))).join("")}
    ${others.length ? `<section><h2>Elsewhere</h2>${await cards(others)}</section>` : ""}`;
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
  const madeRows = m && [["by", m.by?.join(", ")], ["took", m.took], ["cost", m.cost_d !== undefined && money(m.cost_d)], ["turn", m.turn]].filter(([, v]) => v || v === 0);
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
        ${m ? `<h3>How it was made</h3><p>${esc(m.how)}</p><dl>${madeRows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl>${m.recipe ? `<p class="recipe"><b>Recipe.</b> ${esc(m.recipe)}</p>` : ""}` : ""}
        ${t.historical_year ? `<p class="dated">First made in our history: ${t.historical_year}.</p>` : ""}
        ${fermi(t.fermi)}
        ${t.notes ? `<h3>Notes</h3><p>${esc(t.notes)}</p>` : ""}
        ${history(t.history)}
      </div>
    </div>
  </article>`;
}

function people() {
  return `<div class="cards people">${S.people.map((p) => `
    <div class="card person${fresh.has("p:" + p.id) ? " fresh" : ""}"><div class="card-body">
      <h3>${esc(p.name)}</h3>
      <div class="meta">${esc(p.role)}${p.employed ? ` · <b>in your pay</b>${p.wage_d_week ? `, ${money(p.wage_d_week)} a week` : ""}` : ""}</div>
      ${p.attitude ? `<p class="attitude">${esc(p.attitude)}</p>` : ""}
      ${p.skills?.length ? `<p class="skills">${p.skills.map(esc).join(" · ")}</p>` : ""}
      ${p.location ? `<p class="where">${esc(p.location)}</p>` : ""}
      ${p.notes ? `<p>${esc(p.notes)}</p>` : ""}
      ${history(p.history)}
    </div></div>`).join("")}</div>`;
}

function journal() {
  if (!S.log.length) return `<p class="empty">Nothing has happened yet. The journal fills in as you play.</p>`;
  const workings = (title, items) => (items?.length ? `<h4>${title}</h4><ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : "");
  return [...S.log].reverse().map((e) => `
    <article class="entry${fresh.has("t:" + e.turn) ? " fresh" : ""}">
      <header><span class="turn-no">Turn ${e.turn}</span> <span class="when">${span(e.clock_start, e.clock_end)}</span></header>
      <blockquote>${esc(e.action)}</blockquote>
      ${e.sketches?.length ? `<div class="entry-sketches">${e.sketches.map((s) => `<a href="/save/${s}" target="_blank"><img src="/save/${s}" alt="${s}"></a>`).join("")}</div>` : ""}
      <div class="narration">${e.narration.split(/\n+/).map((p) => `<p>${inline(p)}</p>`).join("")}</div>
      <details data-key="w${e.turn}"><summary>Referee's workings</summary>
        ${workings("Credited to you", e.specified)}${workings("Filled in with period practice", e.assumed)}
        ${workings("Rulings", e.rulings)}${workings("Changes", e.changes)}
        ${e.check ? `<h4>Check</h4><p>${esc(e.check)}</p>` : ""}
        ${fermi(e.fermi)}
      </details>
    </article>`).join("");
}

async function plate(id, query) {
  const t = S.things.find((x) => x.id === id);
  const url = t && (await drawing(t, query.get("state") ?? undefined));
  return url ? `<div class="bare-plate"><img src="${url}" alt=""></div>` : `<p class="empty">No drawing for “${esc(id)}”.</p>`;
}

// ---------- page ----------

function masthead(route) {
  const w = S.world;
  const year = Number(w.clock.slice(0, 4));
  const ahead = S.things
    .filter((t) => t.historical_year > year && !t.owner && ["ok", "faulty"].includes(t.status))
    .sort((a, b) => b.historical_year - a.historical_year)[0];
  $("#title").textContent = w.title;
  $("#clock").textContent = S.clock_label;
  $("#place").textContent = w.location;
  $("#purse").textContent = money(w.purse_d);
  $("#purse").classList.toggle("debt", w.purse_d < 0);
  $("#turn").textContent = `turn ${S.log.length}`;
  $("#ahead").textContent = ahead ? ` · ${ahead.historical_year - year} years ahead of history` : "";
  $("#ahead").title = ahead ? ahead.name : "";
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
  const views = { workshop, thing: thingPage, people, journal, visual: plate, sketch: () => "" };
  const html = await (views[route] ?? workshop)(arg, query);
  if (id !== renderId) return; // a newer render started meanwhile
  const open = [...main.querySelectorAll("details[open]")].map((d) => d.dataset.key);
  main.innerHTML = html;
  open.forEach((k) => main.querySelector(`details[data-key="${CSS.escape(k ?? "")}"]`)?.setAttribute("open", ""));
  await Promise.all([...main.querySelectorAll("img")].map((img) => img.decode().catch(() => {})));
  await document.fonts.ready;
  if (id === renderId) document.body.dataset.ready = "1";
}

function markFresh(next) {
  const keyed = [...next.things.map((t) => [t.id, t]), ...next.people.map((p) => ["p:" + p.id, p]), ...next.log.map((e) => ["t:" + e.turn, e])];
  const changed = seen.size ? keyed.filter(([k, v]) => seen.get(k) !== JSON.stringify(v)).map(([k]) => k) : [];
  seen = new Map(keyed.map(([k, v]) => [k, JSON.stringify(v)]));
  changed.forEach((k) => fresh.add(k));
  setTimeout(() => changed.forEach((k) => fresh.delete(k)), 5000);
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), 7000);
}

// Fermi scripts load when opened.
document.addEventListener("toggle", async (e) => {
  const d = e.target;
  if (d.matches?.("details[data-src]") && d.open) d.querySelector("pre").textContent = await (await fetch(`/save/${d.dataset.src}`)).text();
}, true);

const sketch = initSketch($("#sketch"), {
  toast,
  traces: () => [
    ...S.things.filter((t) => t.visual && t._v).map((t) => ({ key: "t:" + t.id, label: t.name, url: () => drawing(t) })),
    ...S.sketches.map((s) => ({ key: s, label: `Sketch ${s.slice(9, 13)}`, url: async () => `/save/${s}` })),
  ],
});

const events = new EventSource("/api/events");
events.onopen = () => $("#live").classList.add("on");
events.onerror = () => $("#live").classList.remove("on");
events.onmessage = async () => {
  const next = await (await fetch("/api/state")).json();
  markFresh(next);
  S = next;
  render();
};
addEventListener("hashchange", render);
