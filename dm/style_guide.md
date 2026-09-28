# Drawing style guide: the engineer's notebook

Every drawing looks like a page from a careful 18th-century engineer's notebook: iron-gall ink on warm paper, precise but hand-made. The view supplies the paper, so drawings have **transparent backgrounds**.

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

## Technical conventions

- Start from `../../dm/visual_template.svg`: `viewBox="0 0 800 600"`, transparent background, with the ink-wobble filter and hatch patterns already defined. Use a wider or taller viewBox when the subject needs it.
- Drawings are shown as `<img>`: no scripts, no external files, no web fonts. Keep everything inside the SVG.
- **States:** wrap the parts that differ by state in `<g data-state="running">`. A group may list several states, as in `data-state="running leaking"`. Parts with no `data-state` always show. The view shows only the groups that match the thing's current `state` (from its spec sheet), and the player can switch between the states listed in `states`.
- **Animation:** use SMIL (`<animate>`, `<animateTransform>`) or CSS `@keyframes` in a `<style>` inside the SVG, only inside the state groups that move. Keep it slow and legible: a piston stroke takes 2–5 s, water drips and flows, fire flickers.
- Tools, materials and documents get a simple, clear drawing too: the object itself, like a still life, with one or two labels.
- Prefer sections and elevations: a cross-section when the inside matters, an elevation when the outside does, both side by side for machines. Keep proportions true to the spec's dimensions. The player reads these drawings as evidence.
- Apply `filter="url(#ink)"` to the main linework for a hand-drawn wobble. Leave text unfiltered so it stays crisp.
- After drawing, look at it with `uv run tg shot <id>` (plus `--state` for each state) and fix whatever reads badly.
