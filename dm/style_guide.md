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
- Every drawing has a title cartouche at the bottom right: the thing's name, a scale line ("Scale: 1 in to 1 ft", or "not to scale"), and "Fig. N" if you like.
- Label the parts that matter with leader lines. Put dimensions from the spec sheet on the drawing: bore, stroke, lengths.
- Show each flaw from the spec sheet where it physically is, as a small red-ochre mark and label ("leaks here above 2 atm").

## Technical conventions

- Start from `../../dm/visual_template.svg`: `viewBox="0 0 800 600"`, transparent background, with the ink-wobble filter and hatch patterns already defined. Use a wider or taller viewBox when the subject needs it.
- Drawings are shown as `<img>`: no scripts, no external files, no web fonts. Keep everything inside the SVG.
- **States:** wrap the parts that differ by state in `<g data-state="running">`. A group may list several states, as in `data-state="running leaking"`. Parts with no `data-state` always show. The view shows only the groups that match the thing's current `state` (from its spec sheet), and the player can switch between the states listed in `states`.
- **Animation:** use SMIL (`<animate>`, `<animateTransform>`) or CSS `@keyframes` in a `<style>` inside the SVG, only inside the state groups that move. Keep it slow and legible: a piston stroke takes 2–5 s, water drips and flows, fire flickers.
- Prefer sections and elevations: a cross-section when the inside matters, an elevation when the outside does, both side by side for machines. Keep proportions true to the spec's dimensions. The player reads these drawings as evidence.
- Apply `filter="url(#ink)"` to the main linework for a hand-drawn wobble. Leave text unfiltered so it stays crisp.
- After drawing, look at it with `uv run tg shot <id>` (plus `--state` for each state) and fix whatever reads badly.
