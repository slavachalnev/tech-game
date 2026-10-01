// Ambient sound for the drawings on screen, made on the spot with Web Audio (no sound files). A drawing says what
// can be heard with data-sound="fire|engine|wind|water|hammer" on groups; only groups that are showing count.
let ctx = null, master = null, on = false;
const playing = new Map(); // kind -> stop function
let wanted = [];

try { on = localStorage.getItem("sound") === "on"; } catch {}

function noise() {
  const buffer = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), data = buffer.getChannelData(0);
  for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  const src = ctx.createBufferSource();
  src.buffer = buffer;
  src.loop = true;
  return src;
}
function filter(type, frequency, Q = 1) {
  const f = ctx.createBiquadFilter();
  f.type = type;
  f.frequency.value = frequency;
  f.Q.value = Q;
  return f;
}
const gain = (value) => { const g = ctx.createGain(); g.gain.value = value; return g; };
const wire = (...nodes) => (nodes.reduce((a, b) => (a.connect(b), b)), nodes[0]); // connect in a row; returns the first

// A short burst: gain up fast, down over `decay` seconds.
function burst(node, out, at, peak, decay) {
  const g = gain(0);
  wire(node, g, out);
  g.gain.setValueAtTime(0, at);
  g.gain.linearRampToValueAtTime(peak, at + 0.005);
  g.gain.exponentialRampToValueAtTime(0.0001, at + decay);
  node.start(at);
  node.stop(at + decay + 0.05);
}
const crackle = (out, at) => burst(noise(), wire(filter("bandpass", 1500 + Math.random() * 3000, 3), out), at, 0.3 + Math.random() * 0.5, 0.02 + Math.random() * 0.05);
function ping(out, at, base, level = 0.12) {
  for (const k of [1, 1.62, 2.73]) {
    const o = ctx.createOscillator();
    o.frequency.value = base * k;
    burst(o, out, at, level / k, 0.9 / k);
  }
}
// Something that happens every `every()` seconds until stopped.
function every(seconds, act) {
  let timer;
  const next = () => (timer = setTimeout(() => (act(ctx.currentTime + 0.05), next()), seconds() * 1000));
  next();
  return () => clearTimeout(timer);
}

const SOUNDS = {
  fire(out) { // a low roar and crackles
    const roar = noise();
    wire(roar, filter("lowpass", 280), gain(0.35), out);
    roar.start();
    const stop = every(() => 0.08 + Math.random() * 0.35, (at) => crackle(out, at));
    return () => (roar.stop(), stop());
  },
  engine(out) { // a slow stroke: a thump as the piston lands, then the hiss of the condenser
    return every(() => 3.4, (at) => {
      const thump = ctx.createOscillator();
      thump.frequency.setValueAtTime(70, at);
      thump.frequency.exponentialRampToValueAtTime(38, at + 0.35);
      burst(thump, out, at, 0.5, 0.45);
      burst(noise(), wire(filter("highpass", 2500), out), at + 1.6, 0.12, 0.7);
      ping(out, at + 0.05, 420, 0.05);
    });
  },
  wind(out) { // noise through a slowly wandering filter
    const air = noise(), f = filter("lowpass", 450), g = gain(0.25), lfo = ctx.createOscillator(), depth = gain(300);
    lfo.frequency.value = 0.09;
    wire(lfo, depth, f.frequency);
    wire(air, f, g, out);
    air.start(), lfo.start();
    return () => (air.stop(), lfo.stop());
  },
  water(out) { // a trickle
    const run = noise(), g = gain(0.08);
    wire(run, filter("bandpass", 1900, 2.5), g, out);
    run.start();
    const stop = every(() => 0.09, (at) => g.gain.setTargetAtTime(0.03 + Math.random() * 0.1, at, 0.03));
    return () => (run.stop(), stop());
  },
  hammer(out) { // a smith at the anvil, now and then
    return every(() => 2.5 + Math.random() * 5, (at) => {
      for (let i = 0; i < 2 + Math.random() * 3; i++) ping(out, at + i * 0.42, 820 + Math.random() * 40);
    });
  },
};

function update() {
  const kinds = on && ctx ? new Set(wanted.filter((k) => SOUNDS[k])) : new Set();
  for (const [k, stop] of playing) if (!kinds.has(k)) stop(), playing.delete(k);
  for (const k of kinds) if (!playing.has(k)) playing.set(k, SOUNDS[k](master));
}

// What the drawings on screen can be heard doing.
export function ambience(kinds) {
  wanted = kinds;
  update();
}

// The on/off switch. Browsers only allow sound after a click, so the context starts on the first one.
export function initSound(button) {
  const show = () => ((button.textContent = on ? "sound on" : "sound off"), button.classList.toggle("on", on));
  const start = () => {
    if (!ctx) {
      ctx = new AudioContext();
      master = wire(gain(0.5), ctx.destination);
    }
    ctx.resume();
    update();
  };
  button.onclick = () => {
    on = !on;
    try { localStorage.setItem("sound", on ? "on" : "off"); } catch {}
    show();
    start();
  };
  if (on) addEventListener("pointerdown", start, { once: true });
  show();
}
