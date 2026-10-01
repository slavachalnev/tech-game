# Drawing style guide: the engineer's notebook

Every drawing looks like a page from a careful 18th-century engineer's notebook: iron-gall ink on warm paper, precise but hand-made. The view supplies the paper, so drawings have **transparent backgrounds**.

## Starting points

- **Things** (machines, tools, materials, documents): copy `../../dm/visual_template.svg`.
- **Scenes** (what the player sees on arriving somewhere or meeting someone): copy `../../dm/scene_template.svg`. Its comments set out the layers and how to size figures from the horizon.
- **Parts:** `../../dm/drawing_parts.svg` is a sheet of 35 ready-drawn parts: drawing furniture, materials, hardware, figures, a horse, scenery and two animations. Copy a part's `<g id="part-…">`, drop the id, and wrap it in `<g transform="translate(x,y) scale(s)">`, keeping s between about 0.4 and 1.6. Parts need only the `<defs>` the templates already have.

## Palette

| Use | Colour |
|---|---|
| Ink: outlines, text | `#2b2118` |
| Faded ink: hatching, dimension lines, hidden lines | `#7a6a55` |
| Red ochre: flaws, leaks, cracks, warnings, annotations | `#9c3b25` |
| Water (wash) | `#4f7390`, fill-opacity 0.25–0.45 |
| Fire, heat (wash) | `#c0662b`, fill-opacity 0.3–0.6 |
| Steam (wash) | `#9aa5a8`, fill-opacity 0.3 |
| Brass or copper (wash) | `#b08d3c` |
| Iron (wash) | `#56514b` |
| Timber (wash) | `#9a7446` |
| Earth or rock (wash) | `#8a7a62` |

Washes are pale fills under ink outlines. Never fill a shape with solid ink.

## Line and type

- Outlines are 2 px. Details are 1.2 px. Hatching is 0.6 px at 45°, about 5 px apart, in faded ink. Dimension lines are 0.8 px with small arrowheads.
- Cut surfaces in sections are hatched: diagonal for metal, grain-like strokes for timber, stipple for masonry or earth.
- Text: `font-family="Georgia, 'Times New Roman', serif"`, `font-style="italic"`, 13–16 px, in ink. Titles use `font-variant="small-caps"` at 18–22 px.
- Every drawing has a title cartouche at the bottom right: the thing's name and a scale ("Scale 1:20", or "not to scale"). Add a small metric scale bar (0, 1, 2 m or 0, 10, 20 cm) when the drawing is to scale.
- Label the parts that matter with leader lines, in plain modern words. Put dimensions from the spec sheet on the drawing, in metric (mm for small parts, m for large): bore, stroke, lengths.
- Show each flaw from the spec sheet where it physically is, as a small red-ochre mark and label ("leaks here above 2 bar").

## Maps

- Same ink-on-paper style. North is up. Every map has a compass mark, a scale bar in km and a `<title>` element (the name shown in the view's Map tab).
- **Coast:** an ink line with a pale water wash on the sea side, plus a few short parallel ripple strokes. **Hills:** small hachured bumps. **Rivers and streams:** thin water-coloured lines. **Roads:** fine ink lines; **tracks:** dashed.
- **Towns:** small filled squares, sized by importance, labelled in italic. **Mines:** a tiny headframe (or ⚒). **The player's base:** a red-ochre star.
- Places the player hasn't visited but has heard of can be drawn with a dotted outline or a "?".
- Places off the map's edge get an arrow at the edge: "London, 430 km, 7–9 days".

## Sites: buildings and places

Your workshop, a mine, a foundry: a building or site is a thing too (kind `structure` or `site`), and its drawing shows it with what's in it, like a cutaway of a workshop or a yard seen from the side. On the drawing board you zoom from the site into anything in it.

- **Start** from `../../dm/site_template.svg` (indoors) or `../../dm/yard_template.svg` (outdoors). Their header comments give the scale, the file order and the details below.
- **True relative sizes:** pick a scale (e.g. 1 m = 150 px indoors, 36 px in a yard) and hold to it. Write the scale, the floor line, any projection and where there's free space in a comment at the top.
- **What's there:** each thing in its own `<g data-thing="<id>">`, self-contained, after a one-line comment saying what and where, so it can be added, removed or redrawn alone as things come and go. Start each with a paper-coloured (`#f8f1e1`) silhouette so what's behind doesn't show through.
- **People** who are usually there can be drawn (`<g data-person="<id>">`), as illustration.
- **States and time of day:** a `data-state` group follows the nearest thing around it that has states (the engine drawn in the smithy runs when the engine runs), else the site's own state (the smithy `idle` or `fire-lit`). `data-sky="day"`, `"dawn dusk"` or `"night"` groups show only at those times. Preview with `uv run tg shot <id> --state night --set engine-10cm=cold`.
- **Sound:** `data-sound="fire"`, `engine`, `water`, `hammer` or `wind` on a group that shows, and the board plays it while the site is in view.
- **Outdoors:** faint long shadows in `data-sky="dawn"` (falling west) and `data-sky="dusk"` (falling east).

## Hotspots: parts you can click in a drawing

In a machine's drawing, mark each component the player might want a closer look at, so clicking it opens that component. Either wrap the component's drawn parts in `<g data-thing="<component-id>">`, or add an invisible outline over it at the end of the drawing: `<g data-layer="hotspots"><rect data-thing="cylinder-10cm" x="…" y="…" width="…" height="…" fill="none"/></g>`. Only ids of existing things. Check them with `uv run tg shot <id> --hotspots`, which outlines everything clickable with its id.

## Drawing sets: zooming from machine to part

The Drawing Board shows every drawing on one sheet the player zooms through. A part with its own drawing opens in place: zoom in on it in its machine's drawing and its own drawing fades in right there, lined up over it, while the machine stays around it. For that to line up:

- **Mark the object.** In every drawing, wrap the object itself (its outlines, washes and section, but no labels, leader lines, dimensions, notes or cartouche) in `<g data-object="">` (the empty value keeps it valid XML). The board fits that group's outline onto the part's outline in the machine's drawing.
- **Draw parts the way their machine shows them**: the same side, the same way up. A cylinder standing upright in the engine stands upright in its own drawing; a section of it is fine.
- **Mark parts snugly** in the machine's drawing (`data-thing`, see Hotspots), so the outline is the part's real extent.
- Keep the object's proportions true to the spec sheet in both drawings, so the two outlines have the same shape.
- **Check** with `uv run tg shot board/<part-id> --half`: the part's drawing, half grown in its circle, should sit over the machine's picture of it the same way round.
- **A project** (a big machine being gathered and built) gets a general-arrangement drawing with each part's real geometry wrapped in its own `data-thing` group, not invisible outlines: the board draws parts not yet in hand as pale blueprint ghosts, so the drawing shows how the project stands.

## Steps: how it works

To show a machine's working cycle, give a state step groups: `<g data-step="1" data-caption="Steam in: the piston rises">…</g>`, numbered from 1, three to six of them. The view shows one step at a time with its caption, with buttons to step and play. Parts outside step groups show in every step, so draw the machine once and put only what changes (valve positions, flows as coloured washes and arrows, the piston's place) in the steps. Moving parts are easiest kept out of the still drawing and placed in each step with `<use>` and a transform. Add the new state only to the groups that don't move, so the other states stay as they were. Check each step with `uv run tg shot <id> --state <state> --step <n>`.

## Technical conventions

- Start from `../../dm/visual_template.svg`: `viewBox="0 0 800 600"`, transparent background, with the ink-wobble filter and hatch patterns already defined. Use a wider or taller viewBox when the subject needs it.
- Drawings are shown as `<img>` (maps are drawn inline, so their place labels can be clicked): no scripts, no external files, no web fonts. Keep everything inside the SVG. Maps don't use `data-state` groups.
- **States:** wrap the parts that differ by state in `<g data-state="running">`. A group may list several states, as in `data-state="running leaking"`. Parts with no `data-state` always show. The view shows only the groups that match the thing's current `state` (from its spec sheet), and the player can switch between the states listed in `states`.
- **Animation:** use SMIL (`<animate>`, `<animateTransform>`) or CSS `@keyframes` in a `<style>` inside the SVG, only inside the state groups that move. Keep it slow and legible: a piston stroke takes 2–5 s, water drips and flows, fire flickers.
- Tools, materials and documents get a simple, clear drawing too: the object itself, like a still life, with one or two labels.
- Prefer sections and elevations: a cross-section when the inside matters, an elevation when the outside does, both side by side for machines. Keep proportions true to the spec's dimensions. The player reads these drawings as evidence.
- Apply `filter="url(#ink)"` to the main linework for a hand-drawn wobble. Leave text unfiltered so it stays crisp.
- After drawing, look at it with `uv run tg shot <id>` (plus `--state` for each state) and fix whatever reads badly.

## Gotchas

- **Straight lines can vanish under the ink filter.** With the default filter region (a margin around the element's bounding box), a perfectly horizontal or vertical line has zero height or width, so the region is empty and nothing is drawn. The templates define `#ink` with `filterUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"`, which covers the whole drawing. Keep that definition when you copy it, and draw in positive coordinates.
- **SMIL `keyTimes` must start at 0 and end at 1**, with as many entries as `values`. Otherwise the browser silently ignores the animation.
- **Keep drawings 4:3 (800×600)** unless the subject really needs another shape. Any aspect ratio now displays in full, but 4:3 fits the view best.
