/* =============================================================================
   Lily Pond — core: pond generation, rules engine and computer player.
   Everything lives inside one function so the exact same source can be used
   on the main thread and (via Function.toString) inside a Web Worker.
   ============================================================================= */
function PondCore() {
  'use strict';

  /* ---------- deterministic random numbers ---------- */
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  /* ===========================================================================
     POND GENERATION
     A pond is a set of round lily pads. Two pads are neighbours when they
     touch; pads that are not neighbours are separated by a clear strip of
     water, so adjacency can be read straight from the picture.
     Guarantees: every pad has 2..4 neighbours and the pond is one connected
     cluster.
     =========================================================================== */
  const TOUCH = 0.975;      // neighbours sit at (ri+rj)*TOUCH  (a slight overlap)
  const TOUCH_MAX = 1.035;  // ...and never further apart than this factor
  const GAP = 0.36;         // wanted water between non-neighbours
  const GAP_MIN = 0.27;     // accepted water between non-neighbours

  function segCross(ax, ay, bx, by, cx, cy, dx, dy) {
    const d1 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
    const d2 = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax);
    const d3 = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx);
    const d4 = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx);
    return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
  }

  function tryGenerate(wanted, rng) {
    const target = Math.round(wanted * 1.05);
    const S = 1.1;                                   // sampling distance
    /* --- 1. organic outline for the cluster --- */
    const area = 1.95 * target * S * S / 1.21;
    const stretch = 1 + rng() * 0.45;
    const R0 = Math.sqrt(area / Math.PI);
    const harm = [];
    for (let k = 2; k <= 5; k++) harm.push([k, (0.34 / k) * rng(), rng() * Math.PI * 2]);
    function inside(x, y) {
      const xx = x / Math.sqrt(stretch), yy = y * Math.sqrt(stretch);
      const th = Math.atan2(yy, xx);
      let rr = 1;
      for (const h of harm) rr += h[1] * Math.cos(h[0] * th + h[2]);
      return xx * xx + yy * yy < R0 * R0 * rr * rr;
    }
    /* --- 2. blue-noise sampling, growing outwards from the middle --- */
    const px = [0], py = [0], active = [0];
    while (active.length && px.length < target) {
      const ai = Math.floor(rng() * active.length), a = active[ai];
      let placed = false;
      for (let k = 0; k < 24; k++) {
        const ang = rng() * Math.PI * 2, rad = S * (1 + rng() * 0.42);
        const x = px[a] + Math.cos(ang) * rad, y = py[a] + Math.sin(ang) * rad;
        if (!inside(x, y)) continue;
        let ok = true;
        for (let j = 0; j < px.length; j++) {
          const dx = px[j] - x, dy = py[j] - y;
          if (dx * dx + dy * dy < S * S) { ok = false; break; }
        }
        if (ok) { px.push(x); py.push(y); active.push(px.length - 1); placed = true; break; }
      }
      if (!placed) active.splice(ai, 1);
    }
    let n = px.length;
    if (n < Math.max(5, target * 0.88)) return null;

    /* --- 3. choose which pads become neighbours --- */
    const cand = [];
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      const d = Math.hypot(px[i] - px[j], py[i] - py[j]);
      if (d < S * 1.62) cand.push([i, j, d]);
    }
    cand.sort((a, b) => a[2] - b[2]);
    const deg = new Int8Array(n), edges = [];
    const adj = []; for (let i = 0; i < n; i++) adj.push(new Set());
    const uf = Array.from({ length: n }, (_, i) => i);
    const find = i => { while (uf[i] !== i) { uf[i] = uf[uf[i]]; i = uf[i]; } return i; };
    const crosses = (i, j) => {
      for (const e of edges) {
        if (e[0] === i || e[0] === j || e[1] === i || e[1] === j) continue;
        if (segCross(px[i], py[i], px[j], py[j], px[e[0]], py[e[0]], px[e[1]], py[e[1]])) return true;
      }
      return false;
    };
    const link = (i, j) => { edges.push([i, j]); adj[i].add(j); adj[j].add(i); deg[i]++; deg[j]++; };
    // 3a. spanning tree: keeps the pond in one piece
    for (const c of cand) {
      const [i, j] = c;
      if (deg[i] >= 4 || deg[j] >= 4) continue;
      const a = find(i), b = find(j);
      if (a === b) continue;
      uf[a] = b; link(i, j);
    }
    for (let i = 1; i < n; i++) if (find(i) !== find(0)) return null;
    // 3b. extra links (cycles are what make cascades interesting)
    const pExtra = 0.72 + rng() * 0.28;
    const extra = cand.filter(c => c[2] < S * 1.42 && !adj[c[0]].has(c[1]))
      .map(c => [c[0], c[1], c[2] * (1 + rng() * 0.2)]).sort((a, b) => a[2] - b[2]);
    for (const c of extra) {
      const [i, j] = c;
      if (deg[i] >= 4 || deg[j] >= 4 || rng() > pExtra || crosses(i, j)) continue;
      link(i, j);
    }
    // 3c. no dead ends: every pad needs at least two neighbours
    for (let i = 0; i < n; i++) {
      if (deg[i] >= 2) continue;
      for (const c of cand) {
        if (c[0] !== i && c[1] !== i) continue;
        const j = c[0] === i ? c[1] : c[0];
        if (adj[i].has(j) || deg[j] >= 4 || crosses(i, j)) continue;
        link(i, j); break;
      }
    }

    /* --- 4. pad sizes: busy pads are the big ones --- */
    const r = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const base = deg[i] >= 4 ? 0.535 : deg[i] === 3 ? 0.5 : 0.46;
      r[i] = base + (rng() - 0.5) * 0.07;
    }

    /* --- 5. relax until "touching" means exactly "neighbours" ---
       Pads that cannot be made to fit are simply taken out of the pond. */
    const x = Float64Array.from(px), y = Float64Array.from(py);
    const alive = new Uint8Array(n).fill(1);
    const unlink = (i, j) => {
      adj[i].delete(j); adj[j].delete(i); deg[i]--; deg[j]--;
      const k = edges.findIndex(e => (e[0] === i && e[1] === j) || (e[0] === j && e[1] === i));
      edges.splice(k, 1);
    };
    const kill = (i) => { for (const j of Array.from(adj[i])) unlink(i, j); alive[i] = 0; };
    const components = () => {
      const comp = new Int16Array(n).fill(-1), sizes = [];
      for (let s0 = 0; s0 < n; s0++) {
        if (!alive[s0] || comp[s0] >= 0) continue;
        const id = sizes.length, st = [s0]; comp[s0] = id; let c = 1;
        while (st.length) { const a = st.pop(); for (const b of adj[a]) if (comp[b] < 0) { comp[b] = id; c++; st.push(b); } }
        sizes.push(c);
      }
      return { comp, sizes };
    };
    const connected = () => components().sizes.length === 1;
    const tidy = () => {              // one cluster, no dead ends
      for (let again = true; again;) {
        again = false;
        const { comp, sizes } = components();
        if (sizes.length > 1) {
          const big = sizes.indexOf(Math.max(...sizes));
          for (let i = 0; i < n; i++) if (alive[i] && comp[i] !== big) kill(i);
        }
        for (let i = 0; i < n; i++) if (alive[i] && deg[i] < 2) { kill(i); again = true; }
      }
    };
    const relax = (iters) => {
      // only pairs that are anywhere near each other can ever collide
      const near = [];
      for (let i = 0; i < n; i++) {
        if (!alive[i]) continue;
        for (let j = i + 1; j < n; j++) {
          if (!alive[j] || adj[i].has(j)) continue;
          const dx = x[j] - x[i], dy = y[j] - y[i];
          if (dx * dx + dy * dy < 6.5) near.push(i, j);
        }
      }
      for (let it = 0; it < iters; it++) {
        for (const e of edges) {
          const i = e[0], j = e[1];
          let dx = x[j] - x[i], dy = y[j] - y[i];
          const d = Math.hypot(dx, dy) || 1e-6, L = (r[i] + r[j]) * TOUCH;
          const f = 0.25 * (d - L) / d;
          dx *= f; dy *= f; x[i] += dx; y[i] += dy; x[j] -= dx; y[j] -= dy;
        }
        for (let k = 0; k < near.length; k += 2) {
          const i = near[k], j = near[k + 1];
          let dx = x[j] - x[i], dy = y[j] - y[i];
          const L = r[i] + r[j] + GAP;
          if (dx > L || dx < -L || dy > L || dy < -L) continue;
          const d = Math.hypot(dx, dy) || 1e-6;
          if (d >= L) continue;
          const f = 0.25 * (d - L) / d;
          dx *= f; dy *= f; x[i] += dx; y[i] += dy; x[j] -= dx; y[j] -= dy;
        }
      }
    };
    tidy();
    let good = false;
    for (let round = 0; round < 40 && !good; round++) {
      relax(round === 0 ? 400 : 200);
      good = true;
      const drastic = round >= 5;
      // neighbours that could not be pulled together
      for (const e of edges.slice()) {
        const i = e[0], j = e[1];
        if (!adj[i].has(j)) continue;
        const d = Math.hypot(x[i] - x[j], y[i] - y[j]);
        if (d <= (r[i] + r[j]) * TOUCH_MAX) continue;
        good = false;
        if (deg[i] > 2 && deg[j] > 2) { unlink(i, j); if (!connected()) link(i, j); }
        else if (drastic) kill(deg[i] <= deg[j] ? i : j);
      }
      // strangers that could not be pushed apart: let them be neighbours
      for (let i = 0; i < n; i++) {
        if (!alive[i]) continue;
        for (let j = i + 1; j < n; j++) {
          if (!alive[i]) break;
          if (!alive[j] || adj[i].has(j)) continue;
          const d = Math.hypot(x[i] - x[j], y[i] - y[j]);
          if (d >= r[i] + r[j] + GAP_MIN) continue;
          good = false;
          if (deg[i] < 4 && deg[j] < 4 && d < (r[i] + r[j]) * 1.18) link(i, j);
          else if (drastic) kill(deg[i] <= deg[j] ? i : j);
          else if (r[i] > 0.4 && r[j] > 0.4) { r[i] -= 0.012; r[j] -= 0.012; }
        }
      }
      if (!good) tidy();
    }
    if (!good) return null;

    /* --- 6. drop removed pads, then check straight from the geometry --- */
    {
      const keep = []; for (let i = 0; i < n; i++) if (alive[i]) keep.push(i);
      if (keep.length < Math.max(5, wanted * 0.85)) return null;
      const X = keep.map(i => x[i]), Y = keep.map(i => y[i]), Rr = keep.map(i => r[i]);
      n = keep.length;
      for (let i = 0; i < n; i++) { x[i] = X[i]; y[i] = Y[i]; r[i] = Rr[i]; }
    }
    const nbr = [];
    for (let i = 0; i < n; i++) nbr.push([]);
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      const d = Math.hypot(x[i] - x[j], y[i] - y[j]);
      const touching = d <= (r[i] + r[j]) * TOUCH_MAX;
      if (!touching && d < r[i] + r[j] + GAP_MIN) return null;
      if (touching) { nbr[i].push(j); nbr[j].push(i); }
    }
    for (let i = 0; i < n; i++) if (nbr[i].length < 2 || nbr[i].length > 4) return null;
    {
      const seen = new Uint8Array(n), st = [0]; seen[0] = 1; let c = 1;
      while (st.length) { const a = st.pop(); for (const b of nbr[a]) if (!seen[b]) { seen[b] = 1; c++; st.push(b); } }
      if (c !== n) return null;
    }

    /* --- 7. centre, and turn the long axis horizontal --- */
    let mx = 0, my = 0;
    for (let i = 0; i < n; i++) { mx += x[i]; my += y[i]; }
    mx /= n; my /= n;
    let sxx = 0, syy = 0, sxy = 0;
    for (let i = 0; i < n; i++) { x[i] -= mx; y[i] -= my; sxx += x[i] * x[i]; syy += y[i] * y[i]; sxy += x[i] * y[i]; }
    const th = 0.5 * Math.atan2(2 * sxy, sxx - syy), c = Math.cos(-th), s = Math.sin(-th);
    for (let i = 0; i < n; i++) { const X = x[i] * c - y[i] * s, Y = x[i] * s + y[i] * c; x[i] = X; y[i] = Y; }
    // sort neighbours by angle so jumps fan out in a stable order
    for (let i = 0; i < n; i++) nbr[i].sort((a, b) => Math.atan2(y[a] - y[i], x[a] - x[i]) - Math.atan2(y[b] - y[i], x[b] - x[i]));
    return { n, x: Array.from(x.subarray(0, n)), y: Array.from(y.subarray(0, n)), r: Array.from(r.subarray(0, n)), nbr, cap: nbr.map(l => l.length) };
  }

  function generatePond(dim, seed) {
    const target = dim * dim;
    for (let attempt = 0; attempt < 400; attempt++) {
      const pond = tryGenerate(target, mulberry32((seed + attempt * 7919) >>> 0));
      if (pond) { pond.dim = dim; pond.seed = seed; pond.attempts = attempt + 1; return pond; }
    }
    throw new Error('could not generate a pond');
  }

  /* ===========================================================================
     RULES ENGINE
     Same rules as Beetle Battle, on an arbitrary neighbour graph.
     Player 1 = red, player 2 = blue.
     =========================================================================== */
  function newState(geo) {
    return { cnt: new Int8Array(geo.n), own: new Int8Array(geo.n), b: [0, 0, 0], moves: 0 };
  }
  function cloneState(s) {
    return { cnt: s.cnt.slice(), own: s.own.slice(), b: [0, s.b[1], s.b[2]], moves: s.moves };
  }
  function legalMoves(s, p) {
    const out = [];
    for (let i = 0; i < s.cnt.length; i++) if (s.cnt[i] === 0 || s.own[i] === p) out.push(i);
    return out;
  }
  function isLegal(s, i, p) { return s.cnt[i] === 0 || s.own[i] === p; }
  function winnerOf(s) {
    if (s.moves >= 2) { if (s.b[1] === 0) return 2; if (s.b[2] === 0) return 1; }
    return 0;
  }
  /* Places a frog for player p on pad idx and resolves the cascade.
     Pads that are full all jump at the same moment (a "wave"); `waves`, when
     given, receives the list of pads that jumped in each wave. */
  function applyMove(s, geo, idx, p, waves) {
    const cap = geo.cap, nbr = geo.nbr, o = 3 - p;
    s.moves++;
    s.cnt[idx]++; s.own[idx] = p; s.b[p]++;
    if (s.cnt[idx] < cap[idx]) return winnerOf(s);
    let wave = [idx], guard = 0;
    while (wave.length) {
      if (s.moves >= 2 && s.b[o] === 0) break;       // nobody left to conquer
      if (++guard > 3000) break;
      for (let k = 0; k < wave.length; k++) s.cnt[wave[k]] -= cap[wave[k]];
      const next = [];
      for (let k = 0; k < wave.length; k++) {
        const L = nbr[wave[k]];
        for (let m = 0; m < L.length; m++) {
          const j = L[m];
          if (s.cnt[j] > 0 && s.own[j] === o) { s.b[o] -= s.cnt[j]; s.b[p] += s.cnt[j]; }
          s.own[j] = p; s.cnt[j]++;
        }
      }
      for (let k = 0; k < wave.length; k++) {
        const i = wave[k];
        if (s.cnt[i] === 0) s.own[i] = 0;
        const L = nbr[i];
        for (let m = 0; m < L.length; m++) { const j = L[m]; if (s.cnt[j] >= cap[j] && next.indexOf(j) < 0) next.push(j); }
        if (s.cnt[i] >= cap[i] && next.indexOf(i) < 0) next.push(i);
      }
      if (waves) waves.push(wave);
      wave = next;
    }
    return winnerOf(s);
  }

  /* ===========================================================================
     COMPUTER PLAYER
     boardValue() is the hand-tuned heuristic of the original Beetle Battle
     (frog count, safe corner/edge pads, loaded pads, vulnerability, chains),
     expressed in pad capacities so it works on any pond.
     =========================================================================== */
  function boardValue(s, geo, p) {
    const cap = geo.cap, nbr = geo.nbr, n = geo.n, cnt = s.cnt, own = s.own;
    const mine = s.b[p], theirs = s.b[3 - p];
    if (theirs === 0 && mine > 1) return 10000;
    if (mine === 0 && theirs > 1) return -10000;
    let v = mine;
    for (let i = 0; i < n; i++) {
      if (own[i] !== p) continue;
      let safe = true;
      const L = nbr[i];
      for (let m = 0; m < L.length; m++) {
        const j = L[m];
        if (own[j] === 3 - p && cnt[j] === cap[j] - 1) { v -= 5 - cap[i]; safe = false; }
      }
      if (safe) {
        if (cap[i] === 3) v += 2; else if (cap[i] === 2) v += 3;
        if (cnt[i] === cap[i] - 1) v += 2;
      }
    }
    // chains of loaded pads: one jump sets off the whole string
    const seen = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      if (seen[i] || own[i] !== p || cnt[i] !== cap[i] - 1) continue;
      let len = 0; const st = [i]; seen[i] = 1;
      while (st.length) {
        const a = st.pop(); len++;
        const L = nbr[a];
        for (let m = 0; m < L.length; m++) { const j = L[m]; if (!seen[j] && own[j] === p && cnt[j] === cap[j] - 1) { seen[j] = 1; st.push(j); } }
      }
      if (len > 1) v += 2 * len;
    }
    return v;
  }

  /* One-ply greedy choice: exactly what the original computer player does. */
  function greedyMoves(s, geo, p) {
    let best = -Infinity, list = [];
    const scored = [];
    for (const m of legalMoves(s, p)) {
      const c = cloneState(s);
      applyMove(c, geo, m, p);
      const v = boardValue(c, geo, p);
      scored.push([m, v]);
      if (v > best) { best = v; list = [m]; } else if (v === best) list.push(m);
    }
    return { best: list, scored };
  }

  /* Look-ahead player: iterative-deepening alpha-beta on a symmetric version
     of the same heuristic. */
  function searchMove(s, geo, p, opts, rng) {
    const deadline = Date.now() + (opts.timeMs || 600), maxDepth = opts.maxDepth || 4;
    let nodes = 0, timeUp = false;
    const evalFor = (st, pl) => {
      const a = boardValue(st, geo, pl);
      if (a >= 10000 || a <= -10000) return a;
      return a - boardValue(st, geo, 3 - pl);
    };
    const children = (st, pl) => {
      const out = [];
      for (const m of legalMoves(st, pl)) {
        const c = cloneState(st);
        const w = applyMove(c, geo, m, pl);
        out.push({ m, st: c, w, v: w === pl ? 10000 : evalFor(c, pl) });
      }
      out.sort((a, b) => b.v - a.v);
      return out;
    };
    function negamax(st, pl, depth, alpha, beta) {
      if ((++nodes & 255) === 0 && Date.now() > deadline) { timeUp = true; return 0; }
      const kids = children(st, pl);
      if (depth <= 1) return kids.length ? kids[0].v : -10000;
      let best = -Infinity;
      const width = Math.min(kids.length, opts.width || 14);
      for (let k = 0; k < width; k++) {
        const c = kids[k];
        const v = c.w === pl ? 10000 + depth : -negamax(c.st, 3 - pl, depth - 1, -beta, -alpha);
        if (timeUp) return 0;
        if (v > best) best = v;
        if (v > alpha) alpha = v;
        if (alpha >= beta) break;
      }
      return best;
    }
    const root = children(s, p);
    if (!root.length) return -1;
    let choice = root.filter(c => c.v === root[0].v).map(c => c.m), depthDone = 1;
    if (s.moves >= 2) {
      for (let depth = 2; depth <= maxDepth; depth++) {
        let best = -Infinity, list = [], alpha = -Infinity;
        const width = Math.min(root.length, depth === 2 ? 40 : 24);
        for (let k = 0; k < width; k++) {
          const c = root[k];
          const v = c.w === p ? 10000 + depth : -negamax(c.st, 3 - p, depth - 1, -Infinity, -alpha + 1);
          if (timeUp) break;
          c.deep = v;
          if (v > best) { best = v; list = [c.m]; } else if (v === best) list.push(c.m);
          if (v > alpha) alpha = v;
        }
        if (timeUp) break;
        choice = list; depthDone = depth;
        root.sort((a, b) => (b.deep === undefined ? -1e9 : b.deep) - (a.deep === undefined ? -1e9 : a.deep));
        if (best >= 10000 || best <= -10000) break;
      }
    }
    return { move: choice[Math.floor(rng() * choice.length)], depth: depthDone, nodes };
  }

  /* level 1: playful (often picks at random), level 2: the original greedy
     heuristic, level 3: looks a few moves ahead. */
  function chooseMove(s, geo, p, level, rng) {
    rng = rng || Math.random;
    const legal = legalMoves(s, p);
    if (!legal.length) return -1;
    if (level <= 1) {
      if (rng() < 0.4) return legal[Math.floor(rng() * legal.length)];
      const g = greedyMoves(s, geo, p).best;
      return g[Math.floor(rng() * g.length)];
    }
    if (level === 2) {
      const g = greedyMoves(s, geo, p).best;
      return g[Math.floor(rng() * g.length)];
    }
    return searchMove(s, geo, p, { timeMs: 650, maxDepth: 4, width: 12 }, rng).move;
  }

  return { mulberry32, generatePond, newState, cloneState, legalMoves, isLegal, winnerOf, applyMove,
           boardValue, greedyMoves, searchMove, chooseMove };
}
if (typeof module !== 'undefined') module.exports = PondCore;
