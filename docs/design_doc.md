# Time Travel Game — Design Doc

Sep 28, 2026 · @Slava Chalnev

## Vision

A personal game where you travel back in time with only what's in your head, and see how much progress you can actually bring. A frontier LLM acts as the game master, so you can try anything.

**The fantasy.** "If I went back to 1710 knowing what I know, how far could I push things?" The fun is that *you* bring the knowledge. The game has to test whether you actually know how to make the thing, not just its name.

**What makes it real.** Saying "I build a steam engine" gets you nothing. You need the materials, the tools to bore a cylinder, workers who can make valves, and the insight that the condenser must be separate. Half the fun is finding out how little you actually know (how do you make glass? get iron hot enough?) and working around it.

**Why now.** A traditional game would need every object and interaction designed in advance, which is impossible for an open world of invention. A frontier model running in an agent harness can do what no designer could pre-author:

- judge feasibility with Fermi estimates;
- keep a persistent world state;
- make new assets and write new interactions on the fly.

**Who it's for.** Me, then maybe close friends. Cost per session doesn't matter. If it is shared, it ships as a repo or prompt people run with their own Claude Code or API key.

**Shape.** A set of scenarios ("you arrive in X at date Y with Z"). Start with one well-made scenario, and make new ones cheap to write later (e.g. "build a computer in 1850").

## Design principles

Six rules the rest of the design follows.

1. **The LLM judges; it doesn't simulate.** Faithful 3D physics or falling-sand sims are a trap for the builder and the player alike. The game master (DM) decides how things behave, what works and what fails.
2. **But real state underneath.** The DM is not free-floating. A persistent, structured world state (things, properties, people, resources, time) keeps it consistent. That state is shown to the player and constrains every ruling.
3. **Fermi before ruling.** Before a non-trivial ruling, the DM runs back-of-envelope numbers in code: force = pressure × area, heat balance, strength of materials, labour-hours. This grounds judgement; it is not a simulation.
4. **Rulings are precedent.** Every built thing gets a spec sheet. Later rulings must agree with existing sheets, like case law. This is the main defence against drift and leniency.
5. **Freedom of input.** Anything can be done by chatting or sketching. The UI is a view of state plus optional shortcuts (point at a thing, drag an item to a bench), never a menu you must go through.
6. **Abstraction as you master things.** Something built in detail once becomes a recipe, then a black-box component, then a production rate. You never re-simulate a cylinder inside an engine inside a train. Known flaws carry up through every layer.

Also: **2D pictures, 3D objects.** Whatever the rendering, objects have real 3D properties (dimensions, cross-sections, how parts fit). The DM reasons in 3D even when the view is flat.

## Architecture

The game is a local web app that draws whatever is in the state files. A Claude Code session is the DM and is the only thing that edits those files.

&#91;embedded content: architecture · 3 parts\]

The browser never decides anything, so the whole game is savable, diffable and easy to inspect. Leaning on Claude Code means bash, Python and file editing come for free; there's almost no custom LLM plumbing.

**DM tools.**

- **Inspect:** read any part of the thing graph at any zoom level.
- **Rule:** update spec sheets, inventory, people, money and the clock.
- **Fermi:** run Python for estimates, saved alongside the ruling so it can be checked later.
- **Draw:** write a visual for a thing (SVG, or Three.js primitives), including its states: idle, running, leaking, broken.
- **Extend:** add small interaction modules (a new panel, a new click action) through a narrow plugin API. It never edits core engine code.
- **Advance time:** skip hours, days or weeks.

**Data by default, code only where needed.** Things and processes are JSON under a strict schema. Code is only for visuals and plugins. This keeps saves coherent and rulings auditable.

**One DM, one model.** A single Claude Code session rules, narrates and plays the characters. Merging those roles makes leniency the main risk. So the DM always rules first, in the spec files, and only then narrates. If leniency still shows up in play, add a fresh-context ruling check the DM calls for big rulings: same model, no second persona.

**Latency is in-game time.** A ruling plus a new asset may take 30 seconds to a few minutes. Actions are time-skips ("you spend four days at the forge"), so the wait reads as time passing, not lag.

**Turn loop.**

1. The player acts: chat, sketch or click.
2. The DM reads the relevant state.
3. The DM runs a Fermi check if the outcome isn't obvious.
4. The DM rules: specs, resources and the clock update.
5. The DM draws or extends if something new now exists.
6. The DM narrates the result.

**Plugging in Claude Code: rails plus flexibility.**

- **Rails.** A project CLAUDE.md with the DM rules. An MCP server exposing the game's API: get state, apply ruling, advance clock, render preview, screenshot the player's view. A hook that checks every state write against the schema and rejects bad ones.
- **Flexibility.** The DM can still write any code in the visuals and plugins folders, run Python, and read anything.
- **Seeing.** A headless browser (Playwright) renders any asset on its own, so the DM can iterate on an animation: draw, screenshot, look, fix. The player's current view is screenshotted and sent with each action, so the DM sees what the player sees.
- **Input, in stages.** MVP: the player types in the Claude Code terminal next to the browser window, so there's no plumbing. Later: chat moves into the browser and reaches the session through the Agent SDK (Claude Code as a library).

## Building layer

This is the highest-uncertainty part. You say or sketch what you want to make, the DM judges it against real constraints, and the result becomes a thing with a spec sheet you can see and build on.

**Input: sketch and chat.** You draw a rough design (a cross-section of a pump, a valve linkage) and annotate it in words. The DM reads it with vision, asks what's unclear ("what seals the piston?"), then rules. Sketching fits the game well: the interface is exactly the skill being tested, knowing the design.

**Spec sheets.** Every thing carries:

- material and dimensions (real 3D: bore, wall thickness, how parts fit);
- performance properties (pressure rating, output, efficiency, lifespan);
- tolerance and quality, which is often what decides success historically. Newcomen's engine worked badly and Watt's worked well largely because of cylinder-boring precision;
- known flaws ("leaks above 2 atm", "cracks if cooled fast");
- how it was made, which becomes the recipe.

**Specificity buys shortcuts.** The referee holds hidden notes on what really matters for each technology. The more of it you specify correctly, the fewer trial-and-error rounds you need. A vague idea still works, slowly, with hints from each failure. A confidently wrong idea wastes materials and time. The referee must never quietly fill in knowledge you didn't supply.

**The abstraction ladder.** As you master something, it gets cheaper to use:

1. **Hands-on.** The first cylinder is made in detail: sketches, tools, trial and error.
2. **Recipe.** It becomes a capability: "bore iron cylinders to ±1 mm; 3 days; needs the boring rig and a trained smith."
3. **Component.** Machines use it through a summary interface (bore, tolerance, pressure rating, flaws). The engine never re-simulates the cylinder; the train never re-simulates the engine.
4. **Production.** Hand the recipe to workers or a workshop and it becomes a rate and a cost. That's where the world layer takes over.

**Flaws carry upward.** A component's known flaws must show up in every assembly that uses it, or abstraction becomes a way to launder bad work.

**Visuals.** A mix of blueprints and 2D renders and animations of objects and processes. The DM hand-codes SVG or canvas for things and processes by default: precise, animatable and tied to state, so a leak shows exactly where the spec says it is. An image model is optional for atmosphere (scenes, portraits, textures), where consistency and technical accuracy matter less. A style guide file (palette, line weights, paper texture, type) keeps the look consistent. The exact vibe is still open and matters a lot.

## World layer

The world layer is where abstracted capabilities turn into production, money and influence. It's the more standard game-design part, so it can come after the building layer proves fun.

- **Time.** A calendar, with actions measured in hours, days or weeks. It sets the pace and the stakes: you have one lifetime, and seasons and harvests matter.
- **Resources.** Money, materials and where they come from (a local smelter, imported brass). Scarcity forces substitution, which is where good ideas shine.
- **People.** Named workers and patrons with skills, wages, loyalty and opinions. You have to persuade, train and pay them. Delegating a recipe to a trained person is how production scales.
- **Economy and demand.** Someone has to want the thing. A mine owner pays for a pump; nobody pays for an abstract engine. This is often the real historical bottleneck.
- **Society.** Guilds, patents, church, state, rumours. These react to what you do and can help or block you.

Historically, ideas were rarely the constraint: Hero of Alexandria had a steam toy about 1,700 years early. The world layer should make materials, precision, capital, demand and institutions matter at least as much as the idea. It should also reward cheap, high-leverage knowledge (boiling water, soap, crop rotation, bookkeeping), because that's the strongest real time-traveller move.

**No win condition; track metrics instead.** A progress dashboard:

- years ahead of history (each capability's real historical date against the in-game date);
- wealth;
- people employed;
- capabilities held;
- influence and power;
- lives improved.

## Scenarios

Start with one hand-tuned scenario. Keep scenarios as plain files so a new one ("build a computer in 1850") is mostly writing, not engineering.

**A scenario file holds:**

- place, date and who you are (status, skills, reputation);
- starting assets: money, workshop, tools, people you know;
- a starting pressure or opportunity (e.g. the flooded mine), not a win condition;
- period notes for the DM: materials, prices, available crafts, local institutions;
- hidden referee notes on what really matters for the key technologies;
- difficulty settings: starting wealth, how strict the referee is, time limit.

The DM could draft most of a new scenario itself from a one-line brief, with a quick research pass before play. The hand-tuned first one serves as the template.

**First scenario: the steam engine.** A Cornwall tin mine in 1705, seven years before Newcomen's first engine (1712). The mine is flooding and the owners will pay for anything that drains it. It's mechanical, hinges on tolerances, has clear demand and is well documented.

**Later candidates:**

| Scenario | Starting pressure | What it tests |
| --- | --- | --- |
| London, 1850 | Usable penicillin | Biology and process, not machining; experiment loops |
| Mainz, 1450 | Print faster than Gutenberg | Metallurgy, inks, presses; a shorter chain of dependencies |
| England, 1850 | A working computing machine | A deep abstraction ladder |

Starting money and the exact setup are placeholders to tune once the building layer works.

## MVP and prototype plan

First prove the core loop, then add visuals: can a strict, consistent DM make "actually building it" fun? Time estimates below are rough guesses for vibe-coding with Claude Code.

1. **DM only, no UI (about half a day).** Plain Claude Code, a DM prompt, a state folder of JSON spec sheets, Python for Fermi checks. Play one scenario for an hour. Test: are rulings fair, consistent with earlier specs, and not lenient?
2. **Minimal view (1–2 days).** A browser page rendering the state: inventory, spec sheets, event log, and the DM-drawn picture of each thing, hot-reloading as files change, plus headless screenshots so the DM can see what it drew.
3. **Sketch input (about 1 day).** A canvas where you draw and annotate; the image goes to the DM with your message.
4. **Abstraction and delegation.** Recipes, components with summary interfaces, flaw propagation, and handing work to people. This brings in the first world-layer pieces: money, people, the clock.
5. **World view and more scenarios.** A walkable scene or map, the scenario template, and a second scenario.

**Decision point after step 2:** is it fun, and does the referee feel fair? If not, fix the DM before building any more UI.

**Useful byproduct:** a session log with rulings and Fermi scripts doubles as a test set. Replay old player moves against a new DM prompt and check the rulings stay consistent.

## Risks and open questions

**Risks**

- **Lenient referee.** LLMs tend to say yes and fill in gaps with what they already know. Mitigations: rule before narrating, an optional fresh-context ruling check, hidden notes on what matters, spec-sheet precedent, mandatory Fermi checks.
- **Being your own only player.** You'll unconsciously hint at the answer. Consider a rule that the referee only credits what you explicitly state or sketch.
- **State drift.** Over a long game, specs and narration contradict each other. Strict schema, precedent checks, and occasional consistency passes by the DM.
- **Generated code piling up.** A pile of ad-hoc modules becomes unmaintainable. Keep the plugin API narrow and prefer data.
- **Context length.** Long games outgrow the context window. The DM has to rely on the files, reading only what the current zoom level needs.

**Open questions**

- Art direction: which mix of blueprints and renders sets the right vibe? Prototype a few style samples early.
- Image model: needed at all, and for which assets?
- How strict should the DM be by default, and should strictness be a setting?
- Which metrics best capture progress and power?

