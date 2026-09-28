> **SECRET, REFEREE ONLY. Never show, quote, paraphrase or hint at any of this to the player, in or out of character.**

# Cornwall 1705: Referee notes

Use this with `period_notes.md`. "≈" marks an approximate figure. Once a ruling fixes a value, it is precedent. Units: metric throughout, money in decimal pounds (£1 = 100p). 1 L of water = 1 kg. Pump flows are in L/min, stream flows in L/s. Pressures are in bar above atmospheric unless stated (1 atm ≈ 1.013 bar ≈ 10.3 m of water; 1 bar = 100 kPa). 1 hp ≈ 0.75 kW. spm = strokes per minute. Depths are measured down from the shaft collar (the top of the shaft).

## 0. How to rule
- **Credit only what is stated or sketched.** A named part ("a snifter", "a condenser", "make it airtight") earns nothing until the player says what it does, where it sits and what it's made of. Ask those three questions; never suggest an answer.
- **Period craft is not new insight.** Hired craftsmen bring their trade's ordinary practice unasked: casting in clay moulds, riveting, soldering, leather cup seals, bored elm pipes, gearing, masonry, surveying the fall of a leat (a channel bringing water to a wheel). They never supply an insight from §3, never diagnose a new machine, and never propose the fix. The same holds for Newcomen as an NPC.
- **A missing insight costs a trial round:** ≈1–3 weeks plus rework at ≈10–30% of the part's cost, ending in the listed **symptom**. Narrate what is seen, heard, felt, timed or measured. Don't use cause words ("air", "vacuum", "condensation", "leak at the piston") unless the player has named that cause. After 2–3 failed rounds on the same symptom, give sharper observations only if the player goes looking (opens a tap, feels a pipe, times the strokes, looks inside).
- **A confidently wrong design** is built exactly as specified and fails, and the materials are spent. **Specificity buys shortcuts:** each "what matters" item stated correctly up front removes its round. A vague plan still progresses, slowly, through symptoms.
- **Out-of-character questions:** answer period facts, prices, who and where, and what the character would observe. Refuse design answers ("would X help?" gets "You'd have to try it").
- **Fermi-check every non-trivial ruling in code** and save the script with the ruling. Every spec sheet carries its tolerance and flaws, and those flaws must show up in every assembly that uses the part.

## 1. Hidden truths: Wheal Fortune (fixed; don't drift)
- **Inflow.** Tregonning's estimate is right to within ±15%. By month (L/min): Apr 160 · May 150 · Jun 140 · Jul 130 · Aug 130 · Sep 150 · Oct 195 · Nov 240 · Dec 265 · Jan 270 · Feb 255 · Mar 210. Wet spells, 3–10 days after heavy rain and mostly Oct–Feb, add 40–60% (≈390–430 L/min).
- **Current drainage.** Two whims (horse-driven winches) with 2 horses at work on each: 4 working at a time, ≈12 in three shifts, ≈1.6 kW at the sweeps (the arms the horses pull). The worn rag-and-chain pumps lift 22 m in two stages at ≈30% efficiency: ≈0.5–0.55 kW in the water, or ≈140–160 L/min. The £12 a month is fodder and stable boys only; the horses (≈£4 each) belong to the adventurers (shareholders).
- **Water level through the year.** It holds at ≈44 m Apr–Sep, falling to ≈46 m by August if the pump rags are renewed. From mid-October it rises ≈2 m a week. It settles at ≈33–37 m Dec–Feb, because the whims deliver more as the lift gets shorter, and is back to ≈42–44 m by April.
- **Storage.** ≈125 m³ of water per meter of depth between 22 and 44 m (old workings); ≈50 m³ per meter between 44 and 66 m (the levels at 55 and 66 m, plus the stopes, the spaces left where ore was dug out). Drawing down from 44 to 55 m means removing ≈550 m³ beyond the inflow, ≈4 days at a 90 L/min surplus. From 44 to 66 m it is ≈1,100 m³. Starting from a winter level of ≈35 m adds ≈1,100 m³.
- **"Below 55 m for a month."** Tregonning measures the water in the engine shaft (the main pumping shaft) each morning with a marked line; any morning the water stands higher than 55 m restarts the month. Penrose insists on a written contract drawn up by an attorney (£1–£3). He pays the £250 on Tregonning's word and then the £60 a year quarterly. Some adventurers will argue that "a month" means a winter month; the contract decides.
- **Money and shares.** The ground at 48–66 m is rich tin and copper, worth ≈£1,500–£2,500 a year gross once worked. There are 16 shares among ≈9 adventurers: Penrose holds 2/16 and Tregonning 1/32. The mineral lord (the landowner who owns the minerals) is a Basset, taking dues (a royalty) of 1/15. The mine is making calls (demands for more money) of ≈£2–£4 per sixteenth. Count days (shareholders' meetings) fall on the first Friday of alternate months; the next is 1 June 1705.
- **The stream.** The adit's outlet is in a valley ≈800 m SE, where the stream runs at ≈11–23 L/s in summer and ≈55–140 L/s in winter. A leat from ≈1.6 km up-valley gives ≈9 m of fall at a wheel site ≈370 m from the engine shaft (≈15 m below its collar). A 3 km leat following the contour could bring ≈8.5 L/s (summer) to ≈28 L/s (winter) at collar height. A tin stamps (ore-crushing mill) downstream claims the water; expect a dispute unless its owner is compensated (£2–£5 a year or a share).
- **A deeper adit.** The land falls toward Restronguet Creek. Draining at ≈37 m needs a tunnel mouth ≈1.5–2.5 km away; draining at 55 m needs ≈5 km, to tidewater.
- **Earlier schemers.** A Bristol man's chain of buckets broke in 1703, and a local sump scheme failed. Penrose paid £15 for nothing, hence he is "tired of inventors with schemes".

## 2. Requirement arithmetic
Water power (kW) = flow (L/min) × lift (m) ÷ 6,120.

| Case | Lift | Summer 140 L/min | Winter 250–270 L/min | Wet peak 410 L/min |
|---|---|---|---|---|
| Hold below 55 m (sump at ≈56 m up to the adit at 22 m) | ≈34 m | 0.8 kW | 1.4–1.5 kW | 2.3 kW |
| Drain to the bottom, 66 m | 44 m | 1.0 kW | 1.8–1.9 kW | 2.9 kW |

- **Power at the shaft** = water power ÷ efficiency. Use ≈0.3 for rag-and-chain and ≈0.55–0.65 for good lift pumps on a crank. Flat rods cost a further ×0.8–0.9.
- **Atmospheric engine size** (12 spm, 1.8 m pump stroke, mean effective pressure 0.48–0.55 bar, +30% friction): 270 L/min at 44 m needs a ≈13 cm pump and a ≈40–43 cm cylinder; a 410 L/min peak needs a ≈15–16 cm pump and a ≈50 cm cylinder. **So a 40–50 cm engine does the whole job**, smaller than Dudley's 53 cm.
- **Coal for that engine** (early engines deliver ≈0.16 MJ of useful work per kg of coal): ≈1.0 t/day at 270 L/min and 44 m; ≈0.5 t/day at 140 L/min. That is ≈270 t a year, or ≈£220–£270 at 80p–£1 a tonne. It costs more than the whims' £144, and the adventurers will notice.

## 3. Technologies
For each: **What matters**, ranked. **Specificity**: what the player must state to skip rounds. **Symptoms**: what to narrate when an item is missing, never the diagnosis.

### 3.1 Atmospheric engine (Newcomen type), the system
**What matters**
1. Steam at about atmospheric pressure fills the cylinder under the piston. Condensing it leaves a partial vacuum, and the atmosphere drives the piston down: the working stroke. The weight of the pump rods on the far end of a beam lifts the piston again while steam refills the cylinder. Boiler pressure is only ≈0.07–0.14 bar.
2. Condense with a jet of cold water sprayed **inside** the cylinder at the top of the stroke, not by cooling the outside.
3. Drain the injection water and condensate every stroke through a pipe from the cylinder bottom into a hot well (a tank of warm drain water), the pipe end sealed under water or fitted with a non-return flap.
4. Expel the air (it comes in with the injection and feed water) every stroke, through a small outward-opening flap valve (a "clack") at the cylinder bottom, blown open by the incoming steam: the snifting valve.
5. Seal the piston with flexible packing (a leather flange or hemp) plus a 5–10 cm layer of water kept on top. This tolerates a bore that is out by ≈3–6 mm.
6. A boiler that evaporates ≈2.5–4× the swept volume per stroke (the cooled cylinder condenses much of the fresh steam), with a weighted safety valve, try-cocks (small taps at two heights to check the water level), and feed from the hot well.
7. **Valve sequence:** steam open on the upstroke and shut before injection; a short injection; then drain and snift. A boy works it at first; later a plug rod hung from the beam trips the valves with pegs (tappets).
8. **Beam and stroke:** arch heads (curved ends on the beam) and chains keep both rods pulling straight; catch-pieces or spring beams stop the stroke at both ends; the pump side is overbalanced by ≈10–20% of the piston load.
9. **Load match:** piston area × 0.48–0.55 bar ≈ the water column plus friction.

**Specificity.** Items 1–5 stated with a sketch: the first full-size trial runs and needs 1–2 weeks of tuning. Items 6–8 are engineering a good millwright can carry out once the player states the need (for example, "a valve that trips itself at the top of the stroke"); each left unstated costs a short round of a few days.

**Symptoms**
- **External cooling only (no 2):** with steam shut off and the outside drenched, the piston creeps down over 1–3 minutes. The cooling water steams, and reheating takes minutes more: ≈1 stroke every 3–5 minutes, and the coal heap shrinks alarmingly.
- **No drain (3):** each stroke is a little shorter, with gurgling and splashing below the piston. After ≈10–30 strokes the piston stops high. Opened, the cylinder stands half full of warm water.
- **No air release (4):** strong first strokes, then each weaker and slower over ≈10–40 strokes until it stalls. An hour's rest with steam blown through revives it briefly. The cylinder bottom stays oddly cool to the hand. Only if the player opens a tap there after a stroke: a cool breath comes out, not steam.
- **Poor seal (5):** a whistle or suck at the piston's edge on the downstroke, a white plume from the open top on the upstroke, a weak stroke. Water on top drains away fast if the bore is bad. Dry leather goes hard and cracks within days.
- **Boiler too small (6):** runs well for a few minutes, then the strokes space out and the safety valve barely lifts; it has to pause to "gather steam".
- **Valves (7):** steam left open during injection makes the boiler roar and the water level jump, with almost no stroke. Too long an injection gives a strong stroke, then a slow upstroke and a cold cylinder; too short gives half a stroke and a hot cylinder. Working by hand manages ≈6–8 spm at best, and the boy tires and slips.
- **No stops or balance (8):** the piston strikes the bottom with a bang (cracked flange, broken chain) or overshoots the top and throws out the water seal. Too heavy a pump side stalls the piston part-way; too light gives a violent, jerky downstroke and snapped chains.
- **Designed for full atmospheric pressure, 1.013 bar (9):** it stalls under the design load and lifts only about half of it.

### 3.2 Boilers
**What matters:** (1) a broad, shallow vessel over the fire: bottom of riveted, caulked copper plate; dome of copper or sheet lead, lead only at ≤0.14 bar; (2) a brick setting with iron grate bars, a flue round the sides, and a chimney of ≥9 m for draught; (3) a weighted safety valve (Papin, 1679, is period knowledge); (4) try-cocks at two heights and continuous feed from the hot well. A 40–50 cm engine needs a boiler ≈1.8–2.4 m across, evaporating ≈180–360 kg of water and burning ≈35–75 kg of coal an hour at full work.
**Pressure limits with period joints:** soft solder (tin-lead, melts at 180–230 °C) weeps above ≈0.7–1.4 bar; riveted copper reaches ≈1.4–2.8 bar at best, in a drum ≤0.9 m across; lead domes "breathe" at a few tenths of a bar, then split; cast iron cracks under uneven firing and bursts without warning. There is no boiler plate: hammered iron plates are ≈60 × 90 cm at most.
**Symptoms:** low water: the lead dome sags and drips, the copper bottom glows dull red and bulges, then a gush of steam. Mud and scale from mine water: output falls over weeks, and hot spots appear. Priming: water is carried into the cylinder, which knocks. Over-pressure: seams weep, then open with a bang and a scalding cloud, and injuries are likely.

### 3.3 Cylinder casting and boring
**What matters:** (1) the material: brass or bell metal (cast in clay moulds by bell founders; finishes well; expensive), or cast iron (cannon founders; walls 4–5 cm; heavy; hard to bore); (2) walls of ≈2–2.5 cm brass for a 40–50 cm bore, with a bottom flange; (3) the bore finished with a boring bar steadied at both ends and turned by a horse or water, the cylinder turned 90° between passes, then ground with sand under a weighted grinding block (a "muller"); (4) checking the bore with a trammel (a rod gauge) at many heights and angles.
**Tolerances (≈):** as cast ±6–13 mm, with taper and ovality; bored in 1705 ±3–6 mm; hand-ground brass ±1.5 mm after weeks of work. The Newcomen water seal tolerates ≈6 mm. Steam above the piston, or any high pressure, needs ≤1.5 mm, which only arrives with Wilkinson in 1775. The first large casting of an unfamiliar shape has ≈1 chance in 3 of needing a re-pour.
**Symptoms:** blowholes hiss or whistle through the wall under vacuum and leave wet "sweat" patches. A cold shut (a seam where two flows of metal failed to fuse) or crack weeps along a line and may split on first heating. An oval or tapered bore makes the piston bind at one height and leak at another. A wall too thin rings and cracks at the flange.

### 3.4 Pistons and seals
**What matters:** a disc of iron plate, or wood and iron, ≈1–2.5 cm smaller than the bore; flexible packing (a turned-up leather collar, or hemp packing pressed down by a follower ring); continuous water on top; tallow on the leather; the rod or chain attached at the centre.
**Symptoms:** dry or hot leather turns hard and cracks in days; hemp chars at the edges; an off-centre pull scores one side, tears the packing on that side, and tilts and jams the piston.

### 3.5 Valve gear
**What matters:** a steam valve (a sliding plate or tap over a port of ≈¼–⅓ of the bore's area); an injection tap with its nozzle pointing upward; the snifting and drain flap valves; the sequence in 3.1 item 7, worked first by hand, then by plug rod, tappets and weighted levers.
**Symptoms:** a small steam port gives a sluggish upstroke; a sticking plate valve lets steam through during the working stroke; a tappet set wrong gives the mistimings listed in 3.1.

### 3.6 Pumps and rods in the shaft
**What matters:** (1) lift (bucket) pumps: a bucket (piston) with a leather cup and flap valve in a smooth pump barrel, a foot valve below, suction ≤6–7.5 m; (2) the rods lift the water when pulled up, so they work in tension, and fall back under their own weight; (3) staged lifts: bored-elm pump pipes, iron-hooped, take ≈18–24 m per lift with a tank between (lead pipe stands more pressure); (4) rods of fir 13–20 cm square, joined with scarf joints and iron straps, with guide stays; (5) catch-pieces, so a broken rod doesn't fall; (6) a strainer at the foot, and spare leathers.
**Symptoms:** suction too high: the pump "snores" and gives no water. Too much head on wooden pipe: the joints spurt and water rains down the shaft. Rods pushed in compression whip and break at the joints. Worn leathers cut output by ≈20–40% over 2–6 weeks. Grit jams a valve and the pump stops dead. A sump drawn dry sucks air and the rods jerk.

### 3.7 Beam and chains
**What matters:** an oak beam ≈6–7 m long (arms ≈2.7–3.7 m for a 1.8 m stroke), ≈30 × 40 to 45 × 55 cm in section, or two timbers trussed together; iron gudgeons (axle pins) in bearing blocks on a stone lever wall; arch heads so the chains wrap and pull vertically; chains of 2–2.5 cm iron; catch-beams. Piston load is ≈7–11 kN (the weight of ≈0.7–1.1 t), which puts only ≈1.5–5 MPa of bending stress in sound oak: shocks, cracks along the grain and gudgeon holes break beams, not the steady load.
**Symptoms:** creaking, then a split along a grain crack at the gudgeon holes; one bad chain weld parts; a bent gudgeon makes the beam rock; the lever wall cracks from the thumping.

### 3.8 Savery-type engine
**What matters:** a receiver (or two, used alternately) filled with steam, then cooled by an outside spray, so the vacuum draws water up the suction pipe (≤≈6–7 m in practice); steam pressure then forces the water up the delivery pipe, with head in meters ≈ 10.2 × gauge pressure in bar. It needs non-return valves on both pipes and a boiler strong enough for the forcing head.
**Limits:** period joints hold ≈1.4–2 bar at most, giving ≈14–20 m of forcing plus ≈6 m of suction per stage. A lift of 34–44 m needs 2–3 stages down the shaft, each with its own boiler and fire underground, coal carried down, smoke, and fire risk. Steam condenses on the cold water and the walls, so coal use runs ≈2–4× a Newcomen engine's for the same work. The engine at Broad Waters (Wednesbury, ≈1705–06) burst.
**Symptoms:** with too much suction the receiver never fills. The forcing phase is sluggish and the receiver empties only partly, sweating and steaming. Soldered joints bead with molten solder, then open. The delivery pipe bursts at its joints.

### 3.9 High-pressure (non-condensing) steam
**What matters:** a small, strong cylindrical boiler of riveted wrought iron, ≥6–10 mm plate, with an internal flue, a safety valve and a fusible plug; a closed cylinder with a stuffing box (a packed gland where the rod passes through); a piston fitted to ≤1–1.5 mm; slide or plug valves exhausting to the air.
**1705 reality:** there is no plate, no boring to that tolerance, and only soft joints. A model of ≤5 cm bore from a clockmaker or instrument maker can run at ≈1.4–2 bar. At full size, expect failure after failure.
**Symptoms:** plumes past the piston and out of the gland; spitting joints; seams parting with a bang; a stall under load.

### 3.10 Separate condenser (Watt)
**What matters:** (1) condense in a separate vessel kept cold, with the jet inside it; (2) an **air pump** worked off the beam to draw water and air out of the condenser every stroke; (3) keep the cylinder hot, with a closed top and a steam jacket; (4) a closed top needs a stuffing box and a bore within ≤1.5 mm. In 1705 an open-top, water-sealed cylinder with a separate condenser and an air pump can be built, and saves ≈30–50% of the coal (≈). A closed-top version leaks badly with a 1705 bore.
**Symptoms:** without the air pump, a few superb strokes, then the vacuum fades over ≈5–15 strokes; the condenser is warm and, opened, full of warm water. A closed top with a poor bore: steam roars past the piston.

### 3.11 Adits
**What matters:** a survey with a level and a measuring chain from a lower tunnel mouth, falling ≈1:500–1:1000; intermediate shafts every ≈180–370 m for air, spoil and extra working faces; cost shared with neighbouring mines in return for adit dues (≈1/32–1/16 of their ore). Progress is ≈2–4 m a month per face in killas (the local slate rock), by hand and gunpowder, slower in granite or elvan (a hard intrusive rock), at ≈£1.60–£4.40 per meter. At that rate 1.6 km from one face takes ≈40 years; with 10 faces ≈4–6 years and ≈£4,000–£8,000. This is a joint venture, not a fix for £50.
**Symptoms:** beyond ≈90–180 m without air, candles burn dim and blue, the men grow dizzy, and progress slows. A survey error means the tunnel misses the shaft or climbs.

### 3.12 Water-wheels, flat rods, water-pressure engine, windmill
- **Water-wheel.** Overshot wheels run at 60–70% efficiency, breast wheels 40–50%, undershot 20–30%. Use 7–11 m diameter, a crank and connecting rod, and a leat with a pond and sluice. Power (W) = flow (L/s) × fall (m) × 9.81 × efficiency. Holding 55 m in winter needs ≈50 L/s at a 9 m fall; draining to 66 m needs ≈70 L/s. The summer stream falls short, so a pond or the horses must help.
- **Flat rods over the ≈370 m** (horizontal rods carrying a back-and-forth pull overland): timber rods on rollers or swinging posts, working in pull only, returned by a balance bob (a weighted lever) or a weight at the shaft and turned down it by an angle bob (a bell crank). Expect ≈10–20% loss and 4–8 spm.
- **Water-pressure engine.** Leat water falls in a pipe from the collar to a cylinder at adit level (22 m ≈ 2.2 bar) and leaves by the adit. Tappets reverse the valves, and a leather-cup piston tolerates a rough bore. 8.5 L/s gives ≈1.1 kW net (≈130 L/min at 34 m); 28 L/s gives ≈3.7 kW.
- **Windmill.** A post mill with sails ≈18–21 m across gives ≈3–6 kW in a fresh breeze and nothing in a calm. It is useful ≈30–40% of hours, and storms break sails.
- **Symptoms:** flat rods pushed in compression buckle and jump the rollers, and slack or stretch leaves the stroke at the shaft several cm short. Frost locks the wheel, and summer drought slows it while the water rises. Water-pressure valves that close too fast hammer and burst a pipe; too slow, and it stalls at the end of the stroke. With a windmill, the water rises in calm spells (August high pressure).

### 3.13 Horse gins with lift pumps
**What matters:** a gin (horse-driven wheel) driving a crank and connecting rod to lift pumps, replacing rag-and-chain; gearing so the pump makes 8–12 spm at a horse's walk of 3–4 km/h; a sweep of 3.5–6 m; two lifts; fresh leathers. A horse gives ≈0.37–0.45 kW over a 6–8 h shift, and the system runs at 0.55–0.65. The existing 4 horses then raise ≈160–185 L/min at 34 m, which **holds 55 m in summer and can win the £250**. Winter needs 5–6 horses at work and a wet peak 9–10: ≈20–30 horses in shifts at ≈£20–£30 a month.
**Symptoms:** output falls as the shift wears on; the crank jerks the gin at each stroke; leathers wear; horses get sore shoulders; rain churns the horse path to mud.

## 4. Historical benchmarks and Fermi constants
- **Dudley, 1712:** brass cylinder 53 cm bore × 2.4 m long, stroke ≈1.8 m, 12 spm, ≈45 L per stroke lifted 47 m, ≈4.1 kW. Haystack-shaped boiler at 0.07–0.14 bar (copper with a lead dome). Coal ≈1.5–2.5 t/day (derived from useful work per kg). Cost ≈£1,000–£1,200, the brass cylinder ≈¼ of it. A replacement 56 cm cylinder was cast by a bell founder (Saunders of Bromsgrove). The Proprietors (the patent holders) later charged royalties of up to £420 a year.
- **Early engines generally:** brass cylinders stayed under ≈90 cm. Iron cylinders appeared from 1714–15 (Hawarden) and came from Coalbrookdale from 1722–23. ≈110–125 engines were built 1712–33. Cornwall's first was at Wheal Vor ≈1710–15; it had 5 by 1727 and ≈20 by 1740, held back by the tax on seaborne coal until 1741.
- **Savery:** suction ≈6–8 m; he claimed "8–10 atmospheres" but the joints failed. Campden House ran ≈18 years; Broad Waters burst. **Watt:** separate condenser conceived 1765, patented 1769, in engines from 1776. It needed a bore true to ≈0.8–1.3 mm on 1.83 m (Wilkinson 1774–75), and used ≈⅓ of a Newcomen engine's coal (Gwennap, 1779–80). **Smeaton's Chacewater, 1775:** 1.83 m bore, 2.7 m stroke, 9 spm, ≈57 kW. **Boring:** as cast ±13 mm; bored brass in 1705 ±3–6 mm; iron in the 1720s–60s ±6–10 mm; Wilkinson ±1.3 mm.
- **Air, water, steam:** atmosphere 1.013 bar = 760 mm Hg = 10.3 m of water; practical suction 6–7.5 m. Water weighs 1,000 kg/m³ and gives ≈0.098 bar per meter of head. Steam at 100 °C: 1.67 m³/kg, latent heat 2.26 MJ/kg. Saturation temperatures: 1 bar gauge 120 °C, 2 bar 134 °C, 3.5 bar 148 °C, 7 bar 170 °C. Hoop stress σ = P·r/t; allow ≈20 MPa in riveted copper at steam heat.
- **Atmospheric mean effective pressure:** 0.48–0.55 bar in early engines, 0.62–0.69 bar in later good practice; a cylinder at 60–70 °C keeps 0.2–0.3 bar of back pressure.
- **Coal** ≈30 MJ/kg, so 1 kg ≈ 8.4 kWh of heat. Useful work per kg of coal: Newcomen 0.14–0.18 MJ (≈0.5% efficient); Smeaton 0.32–0.43 MJ; Watt 0.7–1.1 MJ; Savery ≈0.04–0.07 MJ (≈).
- **Muscle:** a horse gives 0.37–0.45 kW over 6–8 h (Watt's horsepower, 0.75 kW, is generous); a man 75 W all day, or 220–370 W for minutes; a boy ≈40 W.

| Material (period quality) | Ultimate strength, MPa | Notes |
|---|---|---|
| Cast iron | 80–125 tension (flawed castings 55); 410–620 compression | brittle; 7,200 kg/m³ |
| Wrought iron | 240–340 along the grain, far less across it | forge welds 50–80% of the bar |
| Brass, bell metal | 170–240 | bell metal is brittle |
| Copper sheet | 190–220 | weakens above ≈200 °C |
| Lead | 14 | creeps at ≈2 MPa |
| Oak | 70–105 tension, 80–95 bending, 40–50 compression, ≈8 shear | work it at ⅕ |
| Fir | 55–75 bending, 35 compression | |
| Leather | 20–35 | stiffens when dry above ≈70 °C |
| Hemp rope | breaking load ≈ d²/200 tonnes (d = diameter in mm) | work it at ⅙ |
| Wrought chain | 13 mm bar breaks at 4–6 t; 19 mm at 9–13 t | the worst weld governs |

## 5. Time, cost and who can build it (≈, 1705)
| Item | Who and where | Time | Cost |
|---|---|---|---|
| Model engine, 7.5–10 cm bore | Truro brazier or pewterer (rough work; the `forge` can melt a few kg of brass); London instrument maker (fine work) | 2–4 wk; 6–10 wk by post | £2–£5; £8–£20 |
| Brass cylinder, 40–50 cm × 2.1–2.4 m (≈0.5–0.9 t) | Bell founders: **Pennington** (travel; can cast in a pit at Redruth if metal is supplied), **Bilbie** (Chew Stoke), **Rudhall** (Gloucester; has a lathe), **Whitechapel**; London bronze cannon founders. Bristol brass founders handle only a few hundred kg; nobody in Redruth can | mould 3–6 wk, pour and cool 1–2 wk, bore and grind 3–8 wk, sea carriage 1–6 wk | metal £60–£120 (⅓ less with old metal), founding £15–£30, finishing £20–£60, carriage £3–£10: **≈£100–£220** |
| Cast-iron cylinder | Weald cannon founder or Forest of Dean furnace; furnaces run ≈Oct–May | 2–4 months | casting £25–£50. No mill anywhere bores over ≈20 cm, so one must be built (£40–£100, months) |
| Boiler, 1.8–2.4 m copper with lead dome | coppersmith (Bristol, Exeter, Plymouth; Truro only small work), then a mason to set it in brick | 6–10 wk + 2–3 wk | ≈£110–£190 |
| Oak beam, 6–7 m | Plymouth, Tamar or Bristol timber merchant; local carpenters | 2–8 wk to find, 1–2 wk to shape | £10–£25 delivered, plus £5–£10 of ironwork |
| Engine house, lever wall, chimney | 2–3 masons and 4–6 labourers | 8–14 wk; stalls in gales and frost | £60–£130 |
| Pumps: 2 lifts, 13–15 cm barrels, ≈45 m of elm pipe | Hocking with carpenters | 4–8 wk | £30–£70 |
| Rods, stays, catches | carpenters and a smith | 3–5 wk | £20–£40 |
| Chains, straps, gudgeons, grate, bolts (≈0.7–1 t) | Jacca and 1–2 other smiths | 4–8 wk | £20–£45 |
| Piston, valves, taps, pipes | brazier, plumber, founder | 3–6 wk | £15–£40 |
| Erection and trials | millwright, smiths, carpenters, labourers | 4–8 wk | £30–£60 |
| **Whole engine** | orders placed in parallel | **≈9–15 months once the design is fixed** | **≈£400–£750** |
| Running an engine | engine driver 50p–60p a week, 2 stokers at 35p–40p, a boy, 0.5–1 t of coal a day | — | ≈£300 a year |
| 9 m wheel, leat, 370 m of flat rods, pumps | Hocking with carpenters and labourers; a leat takes 3–4.5 m per man-day | 4–7 months | £150–£300 plus water rights |
| Horse-gin lift pumps (2 whims converted) | Hocking and Jacca | 4–8 wk | £30–£70, plus £4 per extra horse |
| Water-pressure engine and 3 km leat | Hocking, a founder (20–25 cm rough bore), a plumber | 5–9 months | £150–£300 |

## 6. Traps and leniency risks
1. **Naming isn't knowing.** "A Newcomen engine", "a proper seal", "a condenser", "make it self-acting": ask what, where and of what.
2. **NPCs gifting insight.** Jacca, Hocking, founders and Newcomen never propose injection inside the cylinder, the drain, the snifter, the water seal or the air pump, and never diagnose.
3. **OOC fishing.** "Would air build up?" or "is external cooling enough?" gets "Try it and see." Answering leaks design knowledge.
4. **Tolerance creep.** "We bore it very carefully" doesn't beat §3.3. Bore error carries into piston leakage and into every assembly built on it.
5. **Perfect materials.** Bar iron has slag streaks, castings have blowholes, oak has cracks along the grain, leathers wear. First big castings fail ≈1 in 3.
6. **Anachronisms.** No rubber, gauge glass, rolled plate, standard screws, pressure gauges, scaled thermometers, mineral oil or Portland cement. Substitutes: leather, hemp, tallow, lead, try-cocks, a mercury U-tube (glass comes from London).
7. **Model to full size.** A working model proves the sequence only, not castings, coal, strength or sealing at 50 cm.
8. **Thermodynamic optimism.** Mean effective pressure ≤0.55 bar, and reheating the cylinder eats steam. Check coal, and check boiler size.
9. **Hydraulics.** Suction ≤7.5 m. A siphon can't lift above its source. Water the pump has raised can't drive the pump's own wheel. Claimed L/min must equal pump area × stroke × spm × ≈0.8.
10. **Time, money and labour.** Letters, founders' queues, sea weather and harvest all take time: nothing big arrives from Bristol in under 4–8 weeks. No one pays in advance, craftsmen want a third down, and `purse_p` is debited every week. Good workers are busy; Hocking needs a clear drawing and his wage. Accidents happen: scalds, falls, gunpowder.
11. **Forgotten costs.** The coal bill, the running crew, wear, and Savery.
12. **Too harsh is wrong too.** Don't demand period craft from the player: they don't need to explain clay-mould casting. The insights in §3 are what the player owes. Books of the day (Moxon, Agricola) take weeks to obtain and read, and teach only period craft.

## 7. World pressures and events
- **Purse.** The base spending is ≈75p–90p a week (Jacca 45p, own board 25p–35p, candles and sundries 5p–10p), plus rent of £1.50 a quarter. £50 lasts ≈a year doing nothing, or 4–6 months with experiments. Credit for a stranger stops at ≈£2–£5 until they have a name.
- **Adventurers' patience** starts at "wary". A cheap demonstration (a working model, a pump trial) earns a trial allowance of £5–£20; more needs Tregonning's endorsement. After two failed public trials they turn to another schemer. At the Christmas count day, with the water at ≈35 m and nothing in hand, they vote to "knock" (abandon) the deep ground, leaving tributers working above the adit. If they do, a sixteenth share sells for ≈£10–£20: an opening for the player.
- **Rumour.** Jacca talks at the Fountain inn: any project is known across the parish in 2–4 days and at Truro in a week. The stranger is said to be a Jacobite, a French spy, a conjuror or a London con man.
- **Rivals.** *Savery's agent:* a London man with Captain Savery's letters tours the mines in late summer 1705, sells a Savery steam pump (a "fire engine") to a neighbouring mine, and installs it in 1706; it fails. *Thomas Newcomen* (b. 1664): a Dartmouth ironmonger and Baptist who sells tools to Cornish mines and experiments privately with John Calley (plumber). If the player's engine becomes known, he comes to look within 2–6 months. He can be a partner, or a rival who learns anything he is shown; in 1705 he holds none of §3.1 items 2–5 unless he sees them. For colour: a local windmill schemer and a dowser.
- **Savery's patent.** Once a steam engine raising water runs in public, news reaches London within 1–3 months (through MPs, Stannary men, letters). Savery's attorney writes 2–6 weeks later, demanding a licence or a stop and threatening a Chancery lawsuit, and the adventurers take fright and ask the player to indemnify them. Outcomes: a licence at ≈£50–£200 a year per engine or a share; a partnership (Newcomen's historical route); or a fight lasting years and costing hundreds of pounds, likely lost because the Act's wording is broad. Wheels, horses and adits are not covered. Savery dies on 15 May 1715; his Proprietors hold the rights until 1733.
- **War.** Privateers (licensed enemy raiders) raise freight by 20–50% and hold ships in port. Convoys run from Falmouth, where the press gang works (it takes seamen, not tinners, who claim exemption), and spy scares follow strangers. News to deliver: Gibraltar relieved (spring 1705); Barcelona taken (Oct 1705); Ramillies (May 1706), with bonfires; the Union with Scotland (1 May 1707); Shovell's fleet wrecked on Scilly (22 Oct 1707); peace in 1713.
- **Harvests.** 1705–07 are good and bread is cheap. The Great Frost of winter 1708–09 brings food shortage in 1709: wheat roughly doubles and tinners riot over food.
- **Seasons.** Apr–Sep the water holds or falls: the window for trials and for the £250 month. Aug–Sep the harvest steals labour. Oct–Feb the water rises; north-coast landings stop in gales, with gaps of 1–4 weeks and coal up 20–40%; roads turn to mud and masonry slows. Midsummer and Michaelmas coinages put cash in the district, the best time to raise money.
- **Gentry.** During the election campaign (Apr–Jun 1705) the Bassets, Boscawens and Godolphins are keen on popular works. A patron might put in £50–£200 for a share and the credit, and will expect deference and results.
- **Law and health.** A water-rights dispute with the stamps goes to the Vice-Warden's court: weeks, and £1–£5 in fees. Smallpox outbreaks, mine accidents, and winter fevers that can lay the player up for 1–3 weeks.

## 8. Cheap high-leverage knowledge
| Idea | The player must state | Time and cost | Payoff | Friction |
|---|---|---|---|---|
| Horse-gin lift pumps (§3.13) | crank and rod, bucket-and-valve pumps, staging | 1–2 months, £30–£70 | the £250 in summer; credibility | winter needs many more horses |
| Safety fuse (1831) | a continuous core of fine powder, yarn wrapped in opposite directions, a tarred waterproof coat, a measured burn rate | 1–3 months on a ropewalk rig, £10–£30 | ≈£30–£150 a year from a few mines; fewer deaths; captains' goodwill | handling gunpowder; copied within a year |
| Copper-ore assay and dealing | an assay procedure: crucible, fluxes, weighing | 1–3 months, £10–£30 plus capital | £50–£300 a year | the smelters' agents; needs Bristol or Swansea contacts |
| Levelling and surveying for leats and adits | a sighted level, a staff, the method | weeks, £2–£10 | fees of £1–£5 per survey; reputation | local mine surveyors ("dialling" men, who survey with a compass) |
| Hygiene: boiled water, washing, latrines, fresh air | the practices | cheap | lives saved; slow reputation | thought fussy |
| Cowpox vaccination (1796) or variolation (1721) | method, cowpox source (dairy herds), follow-up | months to years | lives; fame | the physicians and the church; a single death ruins it |
| Scurvy (citrus, greens) for the Falmouth packet ships | specifics | slow | contacts; small money | scepticism |
| Knowledge of future events | exact dates and positions | — | grain before the 1709 shortage (laws against hoarding, risk of riot); the South Sea Bubble in 1720 | credit only what the player states exactly |
| Better ore dressing (buddles, jigging, sizing) | designs | weeks, £5–£20 | +5–15% ore value | tributers' suspicion |

## 9. Historical dates (for the "years ahead" metric)
- **Period knowledge already (0 years ahead):** Papin's safety valve 1679; Savery's engine 1698; lift pumps, rag-and-chain, horse gins and water-wheels; German flat rods (16th c.; common in Cornwall only from ≈1750); Morland's plunger pump 1675.
- **Atmospheric engine:** internal injection and the snifting valve 1712; plug-rod valve gear ≈1713–15; cast-iron cylinder 1714–15; Coalbrookdale cylinders 1722. **Water power:** water-pressure engine 1731 (France), 1749 (Höll), ≈1765 in England.
- **Watt and after:** separate condenser 1765 (in engines 1776); steam jacket and closed cylinder 1769; crank on a steam engine 1780; compound engine 1781; sun-and-planet gear 1781; expansive working 1782; double action 1782; parallel motion 1784; governor on a steam engine 1788; accurate boring 1774–75 (Wilkinson); slide rest 1797 and screw-cutting lathe ≈1800 (Maudslay).
- **High pressure:** Trevithick's high-pressure engine 1799–1801; locomotive 1804; Cornish boiler and Cornish engine 1812.
- **Metals, mining, science, medicine:** coke-smelted iron 1709; crucible steel ≈1740; puddling 1784; cast-iron rails 1767; safety fuse 1831; wire rope 1834; mercury thermometer 1714 (Fahrenheit's scale 1724); latent heat 1761; lightning rod 1752; variolation in England 1721; Lind's scurvy trial 1747; vaccination 1796.
