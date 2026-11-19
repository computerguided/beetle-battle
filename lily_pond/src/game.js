/* =============================================================================
   Lily Pond — the game: scene dressing, frog behaviour, turn flow, computer
   player, interface and sound.
   ============================================================================= */
'use strict';

const core = PondCore();
const TAU = Math.PI * 2;
const FROG_LEN = 0.39;                       // snout-to-vent length in pond units
const TEAM = { 1: { name: 'Red', css: '#ff5a3c', ring: [1.0, 0.42, 0.25] }, 2: { name: 'Blue', css: '#4aa3ff', ring: [0.35, 0.68, 1.0] } };
const RING_RECT = [-0.5, -0.5, 2, 2];
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const angDiff = (a, b) => { let d = (b - a) % TAU; if (d > Math.PI) d -= TAU; if (d < -Math.PI) d += TAU; return d; };
const ease = t => t * t * (3 - 2 * t);

/* ---------------------------------------------------------------------------
   Sound: ElevenLabs-generated effects played through Web Audio.
   --------------------------------------------------------------------------- */
class Sound {
  constructor(urls) { this.urls = urls; this.buf = {}; this.ctx = null; this.muted = false; this.last = {}; }
  async unlock() {
    if (this.ctx) { if (this.ctx.state === 'suspended') this.ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain(); this.master.gain.value = this.muted ? 0 : 1; this.master.connect(this.ctx.destination);
    await Promise.all(Object.keys(this.urls).map(async k => {
      try { const ab = await (await fetch(this.urls[k])).arrayBuffer(); this.buf[k] = await this.ctx.decodeAudioData(ab); } catch (e) { /* silent */ }
    }));
    if (this.buf.ambient) {
      const s = this.ctx.createBufferSource(), g = this.ctx.createGain();
      s.buffer = this.buf.ambient; s.loop = true; s.loopStart = 0.06; s.loopEnd = s.buffer.duration - 0.08;
      g.gain.value = 0; g.gain.linearRampToValueAtTime(0.55, this.ctx.currentTime + 3);
      s.connect(g); g.connect(this.master); s.start();
    }
  }
  setMuted(m) { this.muted = m; if (this.master) this.master.gain.setTargetAtTime(m ? 0 : 1, this.ctx.currentTime, 0.08); }
  play(name, vol = 1, rate = 1, minGap = 0) {
    if (!this.ctx || !this.buf[name] || this.muted) return;
    const now = this.ctx.currentTime;
    if (minGap && now - (this.last[name] || 0) < minGap) return;
    this.last[name] = now;
    const s = this.ctx.createBufferSource(), g = this.ctx.createGain();
    s.buffer = this.buf[name]; s.playbackRate.value = rate; g.gain.value = vol;
    s.connect(g); g.connect(this.master); s.start();
  }
}

/* ---------------------------------------------------------------------------
   Frog
   --------------------------------------------------------------------------- */
class Frog {
  constructor(id, team, x, y, heading) {
    this.id = id; this.team = team; this.mix = team === 2 ? 1 : 0;
    this.x = x; this.y = y; this.heading = heading;
    this.size = FROG_LEN * (0.93 + Math.random() * 0.14);
    this.state = 'sit'; this.frame = 'sit';
    this.sx = x; this.sy = y;                 // the spot on the pad this frog calls home
    this.wait = 1 + Math.random() * 4;
    this.breath = Math.random() * 3; this.breathPeriod = 1.6 + Math.random() * 1.4;
    this.walk = 0; this.h = 0; this.alpha = 1; this.wet = 0; this.flinch = 0; this.restless = false;
    this.pad = -1; this.jump = null; this.party = false;
  }
  goto(x, y, speed) { this.tx = x; this.ty = y; this.speed = speed; this.state = 'walk'; }
  update(dt, game) {
    const targetMix = this.team === 2 ? 1 : 0;
    this.mix += clamp(targetMix - this.mix, -dt * 3.2, dt * 3.2);
    if (this.flinch > 0) this.flinch = Math.max(0, this.flinch - dt * 3.5);
    if (this.wet > 0) this.wet = Math.max(0, this.wet - dt * 1.2);
    switch (this.state) {
      case 'sit': {
        this.breath += dt * (this.restless ? 2.4 : 1);
        this.frame = (this.breath % this.breathPeriod) < 0.32 ? 'puff' : 'sit';
        const d = Math.hypot(this.sx - this.x, this.sy - this.y);
        if (d > 0.095) { this.goto(this.sx, this.sy, 0.55); break; }
        this.wait -= dt * (this.restless ? 2 : 1);
        if (this.party && this.wait <= 0) { this.hop(game); break; }
        if (this.wait <= 0) {
          const r = Math.random();
          if (r < 0.5) {                       // amble to another spot close by
            const a = Math.random() * TAU, rr = 0.02 + Math.random() * 0.05;
            this.goto(this.sx + Math.cos(a) * rr, this.sy + Math.sin(a) * rr, 0.16 + Math.random() * 0.1);
          } else if (r < 0.82) {               // look around
            this.turnTo = this.heading + (Math.random() - 0.5) * 2.6; this.state = 'turn';
          } else {                             // call
            this.state = 'croak'; this.t = 0;
            if (Math.random() < 0.5) game.sound.play(Math.random() < 0.5 ? 'croak1' : 'croak2', 0.16 + Math.random() * 0.12, 0.85 + Math.random() * 0.4, 0.5);
          }
          this.wait = 1.5 + Math.random() * 6;
        }
        break;
      }
      case 'turn': {
        const d = angDiff(this.heading, this.turnTo), step = dt * 5;
        this.walk += dt * 1.8; this.frame = 'walk' + (Math.floor(this.walk * 6) % 6);
        if (Math.abs(d) <= step) { this.heading = this.turnTo; this.state = 'sit'; } else this.heading += Math.sign(d) * step;
        break;
      }
      case 'walk': {
        const dx = this.tx - this.x, dy = this.ty - this.y, d = Math.hypot(dx, dy);
        if (d < 0.012) { this.state = 'sit'; break; }
        const want = Math.atan2(dy, dx), da = angDiff(this.heading, want);
        this.heading += clamp(da, -dt * 9, dt * 9);
        this.walk += dt * (1.2 + this.speed * 3.5);
        this.frame = 'walk' + (Math.floor(this.walk * 6) % 6);
        if (Math.abs(da) < 1.0 || d < 0.05) {
          const step = Math.min(d, this.speed * dt);
          this.x += dx / d * step; this.y += dy / d * step;
        }
        break;
      }
      case 'croak': {
        this.t += dt;
        this.frame = this.t < 0.12 ? 'puff' : this.t < 0.5 ? 'croak' : 'puff';
        if (this.t > 0.62) this.state = 'sit';
        break;
      }
      case 'jump': this.updateJump(dt, game); break;
    }
  }
  /* A leap from where the frog is to (x, y). `opts`: pre, dur, height, delay, onLand, swim */
  leap(x, y, opts) {
    this.jump = Object.assign({ x0: this.x, y0: this.y, x1: x, y1: y, t: -(opts.delay || 0), pre: 0.14, dur: 0.38, height: 1, speed: 1, landed: false }, opts);
    this.state = 'jump';
    return new Promise(res => { this.jump.done = res; });
  }
  hop(game) {                                  // a little jump of joy, on the spot
    const a = Math.random() * TAU, r = 0.04;
    this.leap(this.sx + Math.cos(a) * r, this.sy + Math.sin(a) * r, { pre: 0.1, dur: 0.3, height: 0.45, quiet: true });
    this.wait = 0.4 + Math.random() * 1.6;
  }
  updateJump(dt, game) {
    const j = this.jump;
    j.t += dt * j.speed;
    if (j.t < 0) return;
    const dir = Math.atan2(j.y1 - j.y0, j.x1 - j.x0);
    if (j.t < j.pre) {                         // turn towards the target and crouch
      this.heading += clamp(angDiff(this.heading, dir), -dt * j.speed * 22, dt * j.speed * 22);
      this.frame = j.swim ? 'swim' : 'crouch';
      if (j.swim) { this.alpha = clamp(j.t / j.pre * 1.4, 0, 1); this.wet = 1; }
      return;
    }
    const u = (j.t - j.pre) / j.dur;
    if (u < 1) {
      if (!j.off) { j.off = true; this.alpha = 1; if (j.onTakeoff) j.onTakeoff(); }
      this.heading = dir;
      const e = u * (2 - u) * 0.35 + u * 0.65;   // quick off the mark, floating in
      this.x = lerp(j.x0, j.x1, e); this.y = lerp(j.y0, j.y1, e);
      this.h = 4 * u * (1 - u) * j.height;
      this.frame = u < 0.14 ? 'launch' : u < 0.55 ? 'fly' : u < 0.8 ? 'glide' : 'tuck';
      return;
    }
    if (!j.landed) {
      j.landed = true; this.x = j.x1; this.y = j.y1; this.h = 0;
      if (j.onLand) j.onLand();
    }
    this.frame = 'land';
    if (j.t > j.pre + j.dur + 0.13) {
      this.state = 'sit'; this.jump = null; this.frame = 'sit';
      j.done();
    }
  }
}

/* ---------------------------------------------------------------------------
   Game
   --------------------------------------------------------------------------- */
class Game {
  constructor(renderer, atlas, sound, ui) {
    this.R = renderer; this.atlas = atlas; this.sound = sound; this.ui = ui;
    this.time = 0; this.timers = [];
    this.settings = Object.assign({ dim: 5, players: { 1: 'human', 2: 'ai' }, level: 2 }, ui.loadSettings());
    this.hover = -1; this.pointer = null; this.epoch = 0;
    this.worker = this.makeWorker(); this.jobs = {}; this.jobId = 0;
    this.newGame();
  }

  /* ---------- computer player runs in a worker, from the same source ---------- */
  makeWorker() {
    try {
      const src = `const core=(${PondCore.toString()})();onmessage=e=>{const d=e.data;postMessage({id:d.id,move:core.chooseMove(d.state,d.geo,d.p,d.level)});};`;
      const w = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      w.onmessage = e => { const f = this.jobs[e.data.id]; delete this.jobs[e.data.id]; if (f) f(e.data.move); };
      w.onerror = () => { this.worker = null; for (const k in this.jobs) this.jobs[k](null); this.jobs = {}; };
      return w;
    } catch (e) { return null; }
  }
  think(p) {
    const geo = { n: this.pond.n, cap: this.pond.cap, nbr: this.pond.nbr }, level = this.settings.level;
    const local = () => core.chooseMove(this.state, geo, p, level);
    if (!this.worker) return Promise.resolve(local());
    return new Promise(res => {
      const id = ++this.jobId;
      this.jobs[id] = m => res(m === null ? local() : m);
      this.worker.postMessage({ id, state: this.state, geo, p, level });
    });
  }

  after(sec) { return new Promise(res => this.timers.push({ at: this.time + sec, res })); }

  /* ---------- a fresh pond ---------- */
  newGame(seed) {
    this.epoch++;
    const s = this.settings;
    this.seed = seed !== undefined ? seed : (Math.random() * 0xffffffff) >>> 0;
    this.rng = core.mulberry32(this.seed ^ 0x9e3779b9);
    const pond = core.generatePond(s.dim, this.seed);
    // tall screens get a tall pond
    if (this.R.canvas.clientHeight > this.R.canvas.clientWidth * 1.08) {
      for (let i = 0; i < pond.n; i++) { const x = pond.x[i]; pond.x[i] = -pond.y[i]; pond.y[i] = x; }
    }
    this.pond = pond;
    this.state = core.newState(pond);
    this.turn = 1; this.winner = 0; this.busy = false; this.acting = false; this.lastMove = -1;
    this.frogs = []; this.frogId = 0;
    this.padFrogs = Array.from({ length: pond.n }, () => []);
    const rng = this.rng, nv = this.atlas.pad.rects.length;
    this.pads = pond.x.map((x, i) => ({
      x, y: pond.y[i], r: pond.r[i], rot: rng() * TAU, variant: Math.floor(rng() * nv), phase: rng() * TAU,
      slotA: rng() * TAU, dip: 0, dipV: 0, glow: 0, shade: 0.92 + rng() * 0.16, warm: rng() * rng(),
    }));
    this.order = this.pads.map((_, i) => i).sort((a, b) => this.pads[b].y - this.pads[a].y);
    this.layout();
    this.timers = [];
    this.ui.setBanner(null);
    this.ui.update(this);
    this.nextTurn();
  }

  /* Fits the camera to the window and dresses the scene: the outline of the
     pond, rocks along its bank, water lilies, koi and dragonflies. */
  layout() {
    const c = this.R.canvas, W = c.clientWidth, H = c.clientHeight, pads = this.pads, rng = core.mulberry32(this.seed ^ 0x51ed27);
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (const p of pads) { x0 = Math.min(x0, p.x - p.r); x1 = Math.max(x1, p.x + p.r); y0 = Math.min(y0, p.y - p.r); y1 = Math.max(y1, p.y + p.r); }
    const hud = 64, bw = x1 - x0 + 2.3, bh = y1 - y0 + 2.3;
    const scale = Math.min(W * 0.86 / bw, (H - hud) * 0.86 / bh, 240);
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2 + hud * 0.5 / scale;
    this.R.cam = [cx, cy, scale];
    const vw = W / 2 / scale, vh = H / 2 / scale;
    this.view = { cx, cy, vw, vh, scale };
    // --- signed distance to the bank (positive = water) ---
    const rect = [cx - vw * 1.1, cy - vh * 1.1, vw * 2.2, vh * 2.2];
    const gw = 256, gh = clamp(Math.round(gw * vh / vw), 96, 420), sd = new Float32Array(gw * gh);
    const NF = this.R.noiseField, NS = this.R.noiseSize;
    const noise = (u, v) => {
      u = (u % 1 + 1) % 1 * NS; v = (v % 1 + 1) % 1 * NS;
      const xa = Math.floor(u) % NS, ya = Math.floor(v) % NS, xb = (xa + 1) % NS, yb = (ya + 1) % NS, tx = u - Math.floor(u), ty = v - Math.floor(v);
      return lerp(lerp(NF[ya * NS + xa], NF[ya * NS + xb], tx), lerp(NF[yb * NS + xa], NF[yb * NS + xb], tx), ty);
    };
    const ox = rng() * 7, oy = rng() * 7, ea = vw * 0.94, eb = vh * 0.91, em = Math.min(ea, eb);
    for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
      const x = rect[0] + (i + 0.5) / gw * rect[2], y = rect[1] + (j + 0.5) / gh * rect[3];
      let acc = 0;
      for (const p of pads) { const d = Math.hypot(x - p.x, y - p.y) - p.r; if (d < 3.5) acc += Math.exp(-2.2 * d); }
      const cluster = 1.2 + (acc > 0 ? Math.log(acc) / 2.2 : -9);
      const ex = Math.abs(x - cx) / ea, ey = Math.abs((y - cy + hud * 0.35 / scale)) / eb;
      const ell = (1 - Math.pow(Math.pow(ex, 3) + Math.pow(ey, 3), 1 / 3)) * em;
      const wob = (noise(x * 0.045 + ox, y * 0.045 + oy) - 0.5) * 1.5 + (noise(x * 0.17 + oy, y * 0.17 + ox) - 0.5) * 0.35;
      sd[j * gw + i] = Math.max(cluster, ell + wob * Math.min(1, em * 0.25));
    }
    this.shore = { sd, gw, gh, rect };
    this.R.setWorld(rect, sd, gw, gh);
    const sample = this.shoreAt = (x, y) => {
      const u = clamp((x - rect[0]) / rect[2] * gw - 0.5, 0, gw - 1.001), v = clamp((y - rect[1]) / rect[3] * gh - 0.5, 0, gh - 1.001);
      const xa = Math.floor(u), ya = Math.floor(v), tx = u - xa, ty = v - ya;
      return lerp(lerp(sd[ya * gw + xa], sd[ya * gw + xa + 1], tx), lerp(sd[(ya + 1) * gw + xa], sd[(ya + 1) * gw + xa + 1], tx), ty);
    };
    // --- rocks where the water meets the grass ---
    const unit = clamp(vw / 9, 0.75, 1.4), cand = [];
    const cellW = rect[2] / gw, cellH = rect[3] / gh;
    for (let j = 1; j < gh - 1; j++) for (let i = 1; i < gw - 1; i++) {
      const a = sd[j * gw + i], b = sd[j * gw + i + 1], d = sd[(j + 1) * gw + i];
      const px = rect[0] + (i + 0.5) * cellW, py = rect[1] + (j + 0.5) * cellH;
      if ((a > 0) !== (b > 0)) cand.push([px + cellW * a / (a - b), py]);
      if ((a > 0) !== (d > 0)) cand.push([px, py + cellH * a / (a - d)]);
    }
    for (let i = cand.length - 1; i > 0; i--) { const k = Math.floor(rng() * (i + 1)); [cand[i], cand[k]] = [cand[k], cand[i]]; }
    this.rocks = [];
    const tryRock = (x, y, r) => {
      if (Math.abs(x - cx) > vw + r || Math.abs(y - cy) > vh + r) return;
      for (const q of this.rocks) if (Math.hypot(q.x - x, q.y - y) < (q.r + r) * 0.62) return;
      this.rocks.push({ x, y, r, rot: rng() * TAU, v: Math.floor(rng() * 8), shade: 0.8 + rng() * 0.3 });
    };
    for (const [x, y] of cand) {
      if (this.rocks.length > 420) break;
      const r = (0.17 + rng() * rng() * 0.34) * unit;
      const gx = sample(x + 0.1, y) - sample(x - 0.1, y), gy = sample(x, y + 0.1) - sample(x, y - 0.1), gl = Math.hypot(gx, gy) || 1;
      const off = (rng() - 0.75) * 0.5 * r;                    // mostly pulled up onto the bank
      tryRock(x + gx / gl * off, y + gy / gl * off, r);
      if (rng() < 0.45) tryRock(x + gx / gl * off + (rng() - 0.5) * r * 3, y + gy / gl * off + (rng() - 0.5) * r * 3, r * (0.3 + rng() * 0.3));
    }
    this.rocks.sort((a, b) => a.r - b.r);
    // --- water lilies in the open water ---
    this.flowers = [];
    const wantFlowers = clamp(Math.round(pads.length / 4.5), 2, 14);
    for (let k = 0; k < 4000 && this.flowers.length < wantFlowers; k++) {
      const x = cx + (rng() * 2 - 1) * vw, y = cy + (rng() * 2 - 1) * vh, r = (0.2 + rng() * 0.13) * Math.min(1.15, unit * 1.05);
      if (sample(x, y) < 0.5 + r) continue;
      let ok = true;
      for (const p of pads) if (Math.hypot(p.x - x, p.y - y) < p.r + r + 0.3) { ok = false; break; }
      for (const f of this.flowers) if (Math.hypot(f.x - x, f.y - y) < 1.4) { ok = false; break; }
      if (ok) this.flowers.push({ x, y, r, rot: rng() * TAU, v: Math.floor(rng() * 3), phase: rng() * TAU, leaf: rng() * TAU, leafV: Math.floor(rng() * 6) });
    }
    // --- koi and dragonflies ---
    const nk = pads.length < 15 ? 2 : pads.length < 60 ? 3 : 5;
    this.koi = [];
    for (let k = 0; k < nk; k++) this.koi.push({ x: cx + (rng() - 0.5) * vw, y: cy + (rng() - 0.5) * vh, a: rng() * TAU, v: k % 4, len: (1.0 + rng() * 0.5) * unit, speed: 0.35 + rng() * 0.25, turn: 0, phase: rng() * 9, burst: 0 });
    this.flies = [0, 1].map(k => ({ x: cx + (rng() - 0.5) * vw * 2, y: cy + (rng() - 0.5) * vh * 2, a: rng() * TAU, tx: cx, ty: cy, wait: rng() * 3, v: k, size: 0.42 * unit }));
    // frogs keep their places on their pads
    for (let i = 0; i < pads.length; i++) this.assignSlots(i, true);
  }

  /* ---------- frogs on pads ---------- */
  slotsFor(i, k) {
    const p = this.pads[i], out = [];
    if (k === 1) return [[p.x, p.y]];
    const ring = k === 2 ? 0.40 : k === 3 ? 0.47 : k === 4 ? 0.53 : 0.58;
    const n = k > 5 ? k - 1 : k;
    for (let m = 0; m < n; m++) { const a = p.slotA + m * TAU / n; out.push([p.x + Math.cos(a) * p.r * ring, p.y + Math.sin(a) * p.r * ring]); }
    if (k > 5) out.push([p.x, p.y]);
    return out;
  }
  /* Gives every frog on pad i a home spot; frogs keep the spot nearest to them. */
  assignSlots(i, snap) {
    const list = this.padFrogs[i], slots = this.slotsFor(i, list.length), free = slots.map((_, k) => k);
    for (const f of list) {
      let best = 0, bd = 1e9;
      const fx = f.jump && !f.jump.landed ? f.jump.x1 : f.x, fy = f.jump && !f.jump.landed ? f.jump.y1 : f.y;
      free.forEach((k, idx) => { const d = Math.hypot(slots[k][0] - fx, slots[k][1] - fy); if (d < bd) { bd = d; best = idx; } });
      const k = free.splice(best, 1)[0];
      f.sx = slots[k][0]; f.sy = slots[k][1]; f.pad = i;
      if (snap && !f.jump) { f.x = f.sx; f.y = f.sy; }
    }
    const crit = list.length === this.pond.cap[i] - 1;
    for (const f of list) f.restless = crit;
  }

  /* ---------- turn flow ---------- */
  nextTurn() {
    if (this.winner) { this.ui.update(this); return; }
    if (this.settings.players[this.turn] === 'ai') {
      const epoch = this.epoch, p = this.turn, ask = this.asked = (this.asked || 0) + 1;
      this.busy = true;
      this.ui.update(this);
      Promise.all([this.think(p), this.after(this.state.moves < 2 ? 0.7 : 0.45)]).then(([m]) => {
        if (epoch !== this.epoch || ask !== this.asked || this.acting) return;   // the question went stale
        if (m < 0 || !core.isLegal(this.state, m, p)) m = core.legalMoves(this.state, p)[0];
        this.playMove(m);
      });
    } else { this.asked = (this.asked || 0) + 1; this.busy = false; this.ui.update(this); }
  }
  canPlay(i) { return !this.busy && !this.winner && i >= 0 && this.settings.players[this.turn] === 'human' && core.isLegal(this.state, i, this.turn); }

  async playMove(idx) {
    const epoch = this.epoch, p = this.turn, pond = this.pond, pad = this.pads[idx];
    this.busy = true; this.acting = true; this.lastMove = idx; this.lastTeam = p;
    this.ui.update(this);
    // 1. a frog surfaces beside the pad and hops on
    let best = 0, bestScore = -1;
    for (let k = 0; k < 20; k++) {
      const a = k / 20 * TAU, x = pad.x + Math.cos(a) * (pad.r + 0.26), y = pad.y + Math.sin(a) * (pad.r + 0.26);
      let score = Math.min(1.2, this.shoreAt(x, y));
      for (let j = 0; j < pond.n; j++) if (j !== idx) score = Math.min(score, Math.hypot(this.pads[j].x - x, this.pads[j].y - y) - this.pads[j].r);
      score += Math.random() * 0.08;
      if (score > bestScore) { bestScore = score; best = a; }
    }
    const ex = pad.x + Math.cos(best) * (pad.r + 0.24), ey = pad.y + Math.sin(best) * (pad.r + 0.24);
    const frog = new Frog(this.frogId++, p, ex, ey, best + Math.PI);
    frog.alpha = 0; frog.wet = 1;
    this.frogs.push(frog);
    this.padFrogs[idx].push(frog);
    this.assignSlots(idx);
    this.R.drop(ex, ey, 0.13, 0.9);
    this.sound.play('splash', 0.22, 0.95 + Math.random() * 0.25, 0.08);
    await frog.leap(frog.sx, frog.sy, {
      pre: 0.3, dur: 0.3, height: 0.5, swim: true,
      onTakeoff: () => this.R.drop(ex, ey, 0.1, -0.8),
      onLand: () => this.landed(idx, p, frog, 0.6),
    });
    if (epoch !== this.epoch) return;
    // 2. the rules decide what happens next; the pond acts it out wave by wave
    const waves = [];
    const winner = core.applyMove(this.state, pond, idx, p, waves);
    for (let w = 0; w < waves.length; w++) {
      await this.playWave(waves[w], p, w);
      if (epoch !== this.epoch) return;
      this.ui.update(this, true);
    }
    this.verify();
    this.acting = false;
    this.turn = 3 - p;
    if (winner) { this.winner = winner; this.celebrate(winner); this.ui.update(this); return; }
    this.nextTurn();
  }

  /* One wave of the cascade: every full pad empties onto its neighbours at once. */
  async playWave(wave, p, index) {
    const pond = this.pond, speed = Math.min(1 + index * 0.17, 3.4), jobs = [];
    const flights = [];
    for (const i of wave) {
      const pad = this.pads[i], list = this.padFrogs[i], leaving = [];
      for (const j of pond.nbr[i]) {
        // the frog best placed for this neighbour goes there
        const dir = Math.atan2(this.pads[j].y - pad.y, this.pads[j].x - pad.x);
        let bi = -1, bs = 1e9;
        list.forEach((f, k) => {
          if (leaving.includes(f)) return;
          const s = -((f.x - pad.x) * Math.cos(dir) + (f.y - pad.y) * Math.sin(dir));
          if (s < bs) { bs = s; bi = k; }
        });
        if (bi < 0) continue;
        leaving.push(list[bi]);
        flights.push({ frog: list[bi], from: i, to: j });
      }
      this.padFrogs[i] = list.filter(f => !leaving.includes(f));
    }
    const touched = new Set(wave);
    for (const fl of flights) { this.padFrogs[fl.to].push(fl.frog); touched.add(fl.to); fl.frog.team = p; }
    // decide where everybody ends up, then let them go
    for (const fl of flights) { fl.frog.jump = { landed: false, x1: this.pads[fl.to].x, y1: this.pads[fl.to].y }; }
    for (const i of touched) this.assignSlots(i);
    for (const fl of flights) {
      const f = fl.frog; f.jump = null;
      const d = Math.hypot(f.sx - f.x, f.sy - f.y);
      jobs.push(f.leap(f.sx, f.sy, {
        delay: Math.random() * 0.07, pre: 0.15, dur: 0.30 + d * 0.085, height: 0.8 + d * 0.25, speed,
        onTakeoff: () => { const s = this.pads[fl.from]; s.dipV -= 0.6; this.R.drop(s.x, s.y, s.r * 0.8, -0.14); },
        onLand: () => this.landed(fl.to, p, f, 1 / Math.sqrt(speed)),
      }));
    }
    await Promise.all(jobs);
    await this.after(0.05 / speed);
  }

  /* A frog touches down on pad i: the pad dips, the water answers, and any
     frogs already there change sides. */
  landed(i, p, frog, loud) {
    const pad = this.pads[i];
    pad.dipV += 2.2; pad.glow = 1;
    this.R.drop(pad.x, pad.y, pad.r * 0.85, 0.42);
    this.R.drop(frog.x, frog.y, 0.12, 0.5);
    this.sound.play(Math.random() < 0.5 ? 'land1' : 'land2', 0.32 * loud, 0.85 + Math.random() * 0.5, 0.035);
    for (const f of this.padFrogs[i]) if (f !== frog && f.team !== p && !f.jump) { f.team = p; f.flinch = 1; }
    this.ui.update(this, true);
  }
  /* Frogs per colour as they are on screen right now (the rules run ahead of
     the animation, so the scoreboard counts what you can see). */
  counts() { const c = [0, 0, 0]; for (const f of this.frogs) c[f.team]++; return c; }

  verify() {
    for (let i = 0; i < this.pond.n; i++) {
      const l = this.padFrogs[i];
      if (l.length !== this.state.cnt[i] || l.some(f => f.team !== this.state.own[i])) { console.warn('view out of step with rules at pad', i); this.resync(); return; }
    }
  }
  resync() {                                   // never expected; keeps the picture honest if it happens
    this.frogs = [];
    for (let i = 0; i < this.pond.n; i++) {
      this.padFrogs[i] = [];
      for (let k = 0; k < this.state.cnt[i]; k++) { const f = new Frog(this.frogId++, this.state.own[i], this.pads[i].x, this.pads[i].y, Math.random() * TAU); this.frogs.push(f); this.padFrogs[i].push(f); }
      this.assignSlots(i, true);
    }
  }

  celebrate(winner) {
    for (const f of this.frogs) if (f.team === winner) { f.party = true; f.wait = Math.random() * 1.2; }
    this.sound.play('chorus', 0.7, 1);
    const human = this.settings.players[winner] === 'human', both = this.settings.players[3 - winner] === 'human';
    this.after(0.9).then(() => this.ui.setBanner({ team: winner, title: `${TEAM[winner].name} frogs rule the pond`,
      sub: human && !both ? `You won in ${Math.ceil(this.state.moves / 2)} moves.` : !human && both ? 'The computer out-hopped you this time.' : `Decided after ${this.state.moves} moves.` }));
  }

  /* ---------- pointer ---------- */
  worldOf(px, py) {
    const c = this.R.canvas, v = this.view;
    return [v.cx + (px - c.clientWidth / 2) / v.scale, v.cy - (py - c.clientHeight / 2) / v.scale];
  }
  padAt(x, y) {
    for (let i = 0; i < this.pads.length; i++) { const p = this.pads[i]; if (Math.hypot(p.x - x, p.y - y) < p.r) return i; }
    return -1;
  }
  pointerMove(px, py) {
    const [x, y] = this.worldOf(px, py);
    if (this.pointer) {
      const d = Math.hypot(x - this.pointer[0], y - this.pointer[1]);
      this.trail = (this.trail || 0) + d;
      if (this.trail > 0.22 && this.padAt(x, y) < 0 && this.shoreAt(x, y) > 0.1) { this.R.drop(x, y, 0.07, 0.22); this.trail = 0; }
    }
    this.pointer = [x, y];
    this.hover = this.padAt(x, y);
    this.R.canvas.style.cursor = this.canPlay(this.hover) ? 'pointer' : 'default';
  }
  click(px, py) {
    const [x, y] = this.worldOf(px, py), i = this.padAt(x, y);
    if (this.canPlay(i)) { this.hover = -1; this.playMove(i); }
    else if (i < 0 && this.shoreAt(x, y) > 0.05) { this.R.drop(x, y, 0.1, 0.9); this.sound.play('land2', 0.12, 1.5, 0.1); }
  }

  /* ---------- per-frame ---------- */
  update(dt) {
    this.time += dt;
    for (let i = this.timers.length - 1; i >= 0; i--) if (this.timers[i].at <= this.time) this.timers.splice(i, 1)[0].res();
    for (const p of this.pads) {
      p.dipV += (-60 * p.dip - 7 * p.dipV) * dt; p.dip += p.dipV * dt;
      p.glow = Math.max(0, p.glow - dt * 2.2);
    }
    for (const f of this.frogs) f.update(dt, this);
    // frogs sharing a pad keep a polite distance
    for (const list of this.padFrogs) for (let a = 0; a < list.length; a++) for (let b = a + 1; b < list.length; b++) {
      const f = list[a], g = list[b];
      if (f.state === 'jump' || g.state === 'jump') continue;
      const dx = g.x - f.x, dy = g.y - f.y, d = Math.hypot(dx, dy) || 1e-3, min = 0.26;
      if (d < min) { const s = (min - d) / d * 0.5 * Math.min(1, dt * 10); f.x -= dx * s; f.y -= dy * s; g.x += dx * s; g.y += dy * s; }
    }
    const v = this.view;
    // koi wander under the surface and turn away from the bank
    for (const k of this.koi) {
      k.turn += (Math.random() - 0.5) * dt * 2.2; k.turn *= 1 - dt * 0.8;
      const ahead = this.shoreAt(k.x + Math.cos(k.a) * 1.6, k.y + Math.sin(k.a) * 1.6);
      if (ahead < 0.9) { const toC = Math.atan2(v.cy - k.y, v.cx - k.x); k.a += clamp(angDiff(k.a, toC), -1, 1) * dt * 1.6; }
      k.a += k.turn * dt;
      k.burst = Math.max(0, k.burst - dt);
      if (Math.random() < dt * 0.04) k.burst = 1.2;
      const sp = k.speed * (1 + k.burst * 1.4);
      k.x += Math.cos(k.a) * sp * dt; k.y += Math.sin(k.a) * sp * dt; k.phase += dt * (3.2 + sp * 5);
    }
    // dragonflies dart, hover, dart
    for (const d of this.flies) {
      const dx = d.tx - d.x, dy = d.ty - d.y, dist = Math.hypot(dx, dy);
      if (dist < 0.08) {
        d.wait -= dt;
        if (d.wait <= 0) { d.tx = v.cx + (Math.random() * 2 - 1) * v.vw * 1.15; d.ty = v.cy + (Math.random() * 2 - 1) * v.vh * 1.15; d.wait = 0.6 + Math.random() * 3.5; }
      } else {
        const sp = Math.min(dist * 4 + 0.6, 5.5) * dt;
        d.x += dx / dist * Math.min(sp, dist); d.y += dy / dist * Math.min(sp, dist);
        d.a += clamp(angDiff(d.a, Math.atan2(dy, dx)), -dt * 12, dt * 12);
      }
    }
    // the pond is never perfectly still
    if (Math.random() < dt * 1.1) {
      const x = v.cx + (Math.random() * 2 - 1) * v.vw, y = v.cy + (Math.random() * 2 - 1) * v.vh;
      if (this.shoreAt(x, y) > 0.2 && this.padAt(x, y) < 0) this.R.drop(x, y, 0.05 + Math.random() * 0.05, 0.35 + Math.random() * 0.4);
    }
    if (Math.random() < dt * 2.5 && this.pads.length) { const p = this.pads[Math.floor(Math.random() * this.pads.length)]; this.R.drop(p.x, p.y, p.r * 0.9, 0.05); }
  }

  draw() {
    const R = this.R, A = this.atlas, t = this.time, under = R.under, main = R.main;
    under.clear(); main.clear();
    const WHITE = [1, 1, 1, 1], sunX = -SUN[0], sunY = -SUN[1];
    // ---- below the surface: koi, and the shade under every pad ----
    for (const k of this.koi) {
      const rect = A.props.koi[k.v], SEG = 7, L = k.len * 1.37, half = L * 0.1875;
      const dx = Math.cos(k.a), dy = Math.sin(k.a), nx = -dy, ny = dx;
      let prev = null;
      for (let s = 0; s <= SEG; s++) {
        const u = s / SEG, sway = Math.sin(k.phase - u * 4.2) * (0.02 + 0.10 * u * u) * k.len;
        const px = k.x + dx * (0.5 - u) * L + nx * sway, py = k.y + dy * (0.5 - u) * L + ny * sway;
        const cur = [px + nx * half, py + ny * half, px - nx * half, py - ny * half];
        if (prev) {
          const r = [rect[0], rect[1] + rect[3] * (s - 1) / SEG, rect[2], rect[3] / SEG];
          under.quad4('props', [prev[0], prev[1], prev[2], prev[3], cur[2], cur[3], cur[0], cur[1]], r, 0, [0.8, 0.85, 0.8, 0.8], [0, 2, 0, 0]);
        }
        prev = cur;
      }
    }
    for (const i of this.order) {
      const p = this.pads[i], rect = A.pad.rects[p.variant], s = p.r * 1.1 * 1.07;
      under.sprite('pad', p.x + sunX * 0.2, p.y + sunY * 0.2, s, s, p.rot, rect, [0, 0.02, 0.03, 0.62], [0, 1, 3.2, 0]);
    }
    for (const f of this.flowers) {
      const rect = A.props.flower[f.v], s = f.r * 1.5;
      under.sprite('props', f.x + sunX * 0.12, f.y + sunY * 0.12, s, s, f.rot, rect, [0, 0.02, 0.03, 0.5], [0, 1, 3, 0]);
    }
    // ---- the bank ----
    for (const r of this.rocks) {
      const rect = A.props.rock[r.v], s = r.r * 1.6;
      main.sprite('props', r.x + sunX * r.r * 0.22, r.y + sunY * r.r * 0.22, s * 1.04, s * 1.04, r.rot, rect, [0, 0, 0, 0.5], [0, 1, 2.6, 0]);
      main.sprite('props', r.x, r.y, s, s, r.rot, rect, [r.shade, r.shade, r.shade, 1], [0, 0, 0, 0.12]);
    }
    // ---- water lilies: a small leaf and a blossom ----
    for (const f of this.flowers) {
      const bob = Math.sin(t * 0.9 + f.phase), x = f.x + Math.cos(f.phase) * bob * 0.012, y = f.y + Math.sin(f.phase) * bob * 0.012;
      const lr = f.r * 0.95, lx = x + Math.cos(f.leaf) * f.r * 0.75, ly = y + Math.sin(f.leaf) * f.r * 0.75;
      main.sprite('pad', lx, ly, lr * 1.1, lr * 1.1, f.leaf + 2.6 + bob * 0.03, A.pad.rects[f.leafV], [0.78, 0.86, 0.8, 1], [0, 0, 0, 0.25]);
      const s = f.r * 1.22;
      main.sprite('props', x + sunX * 0.04, y + sunY * 0.04, s, s, f.rot + bob * 0.04, A.props.flower[f.v], [0, 0.02, 0, 0.4], [0, 1, 2.5, 0]);
      main.sprite('props', x, y, s, s, f.rot + bob * 0.04, A.props.flower[f.v], WHITE, [0, 0, 0, 0.05]);
    }
    // ---- lily pads ----
    const turnPlayable = !this.busy && !this.winner && this.settings.players[this.turn] === 'human';
    for (const i of this.order) {
      const p = this.pads[i], rect = A.pad.rects[p.variant];
      const sway = Math.sin(t * 0.7 + p.phase), s = p.r * 1.1 * (1 - 0.03 * p.dip + 0.004 * sway);
      const x = p.x + Math.cos(p.phase) * sway * 0.006, y = p.y + Math.sin(p.phase) * sway * 0.006, rot = p.rot + sway * 0.012;
      main.sprite('pad', x + sunX * 0.035, y + sunY * 0.035, s * 1.02, s * 1.02, rot, rect, [0, 0.03, 0.02, 0.45], [0, 1, 2.2, 0]);
      let b = p.shade * (1 - 0.10 * clamp(p.dip, -1, 1)) + p.glow * 0.10;
      if (i === this.hover && this.canPlay(i)) b += 0.16;
      main.sprite('pad', x, y, s, s, rot, rect, [b * (1 + 0.16 * p.warm), b, b * (1 - 0.22 * p.warm), 1], [0, 0, 0, 0.30]);
    }
    // ---- highlights: where you can go, who its neighbours are, the last move ----
    if (this.lastMove >= 0) {
      const p = this.pads[this.lastMove], c = TEAM[this.lastTeam].ring, s = p.r * 1.16;
      main.sprite('frog', p.x, p.y, s, s, 0, RING_RECT, [c[0], c[1], c[2], 0.55 + 0.15 * Math.sin(t * 3)], [0, 3, 0.90, 0.07]);
    }
    if (this.hover >= 0 && turnPlayable) {
      const p = this.pads[this.hover], ok = this.canPlay(this.hover), c = ok ? TEAM[this.turn].ring : [0.7, 0.7, 0.7];
      const s = p.r * 1.2;
      main.sprite('frog', p.x, p.y, s, s, 0, RING_RECT, [c[0], c[1], c[2], ok ? 1 : 0.35], [0, 3, 0.88, 0.10]);
      for (const j of this.pond.nbr[this.hover]) {
        const q = this.pads[j], sq = q.r * 1.14;
        main.sprite('frog', q.x, q.y, sq, sq, 0, RING_RECT, [1, 1, 0.9, 0.5 + 0.2 * Math.sin(t * 4)], [0, 3, 0.9, 0.06]);
      }
    }
    // ---- frogs: those sitting first, the ones in the air on top ----
    const F = A.frog.frames;
    const drawFrog = (f) => {
      const k = 1 + 0.42 * f.h + 0.12 * f.flinch * Math.sin(f.flinch * Math.PI);
      const L = f.size * k, th = f.heading - Math.PI / 2, c = Math.cos(th), s = Math.sin(th);
      const hs = 1.1 * L, off = 0.42 * L, qx = f.x + s * off, qy = f.y - c * off;
      const rect = F[f.frame] || F.sit, lift = 0.03 + 0.5 * f.h;
      const pad = f.pad >= 0 ? this.pads[f.pad] : null, sink = pad && f.h === 0 ? pad.dip * 0.004 : 0;
      main.sprite('frog', qx + sunX * lift, qy + sunY * lift - sink, hs, hs, th, rect, [0, 0.02, 0.01, 0.42 * f.alpha * (1 - 0.45 * f.h)], [0, 1, 1.2 + 3.6 * f.h, 0]);
      const w = f.wet * 0.35, tint = [1 - w * 0.5, 1 - w * 0.15, 1 - w * 0.2, f.alpha];
      main.sprite('frog', qx, qy, hs, hs, th, rect, tint, [f.mix, 0, 0, 0.55]);
    };
    const air = [];
    for (const f of this.frogs) if (f.h > 0.02) air.push(f); else drawFrog(f);
    air.sort((a, b) => a.h - b.h).forEach(drawFrog);
    // ---- dragonflies ----
    for (const d of this.flies) {
      const rect = A.props.dragonfly[d.v][Math.floor(t * 30) % 2], s = d.size, th = d.a - Math.PI / 2;
      const jx = Math.sin(t * 23 + d.v * 5) * 0.012, jy = Math.cos(t * 19 + d.v) * 0.012;
      main.sprite('props', d.x + sunX * 0.5, d.y + sunY * 0.5, s, s, th, rect, [0, 0.02, 0.02, 0.22], [0, 1, 2.5, 0]);
      main.sprite('props', d.x + jx, d.y + jy, s, s, th, rect, WHITE, [0, 2, 0, 0]);
    }
  }
}
