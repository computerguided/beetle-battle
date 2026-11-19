// Sanity tests for pond generation, the rules engine and the computer players.
//   node lily_pond/tools/test_core.js [svg-output-dir]
const fs = require('fs'), path = require('path');
const core = require('../src/core.js')();

let fails = 0;
const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL', msg); } };

// ---- pond generation ----
for (const dim of [3, 5, 7, 9, 11]) {
  let att = 0, nSum = 0, degHist = [0, 0, 0, 0, 0], t0 = Date.now(), worst = 0;
  const runs = 200;
  for (let seed = 1; seed <= runs; seed++) {
    const t1 = Date.now();
    const p = core.generatePond(dim, seed * 1013);
    worst = Math.max(worst, Date.now() - t1);
    att += p.attempts; nSum += p.n;
    // invariants
    const seen = new Set([0]), st = [0];
    while (st.length) { const a = st.pop(); for (const b of p.nbr[a]) if (!seen.has(b)) { seen.add(b); st.push(b); } }
    check(seen.size === p.n, `dim ${dim} seed ${seed}: not connected`);
    for (let i = 0; i < p.n; i++) {
      check(p.cap[i] >= 2 && p.cap[i] <= 4, `dim ${dim} seed ${seed}: degree ${p.cap[i]}`);
      degHist[p.cap[i]]++;
      for (const j of p.nbr[i]) check(p.nbr[j].includes(i), 'asymmetric');
      for (let j = i + 1; j < p.n; j++) {
        const d = Math.hypot(p.x[i] - p.x[j], p.y[i] - p.y[j]), touch = p.nbr[i].includes(j);
        if (touch) check(d <= (p.r[i] + p.r[j]) * 1.036, 'neighbours apart');
        else check(d >= p.r[i] + p.r[j] + 0.269, `strangers too close ${d - p.r[i] - p.r[j]}`);
      }
    }
  }
  const tot = degHist[2] + degHist[3] + degHist[4];
  console.log(`dim ${dim}: avg pads ${(nSum / runs).toFixed(1)}, avg attempts ${(att / runs).toFixed(1)}, ` +
    `deg2/3/4 ${degHist.slice(2).map(v => (100 * v / tot).toFixed(0) + '%').join(' ')}, ` +
    `avg ${((Date.now() - t0) / runs).toFixed(1)} ms, worst ${worst} ms`);
}

// ---- engine + players ----
function play(geo, levels, seed, maxMoves = 4000) {
  const rng = core.mulberry32(seed), s = core.newState(geo);
  let p = 1, w = 0;
  while (!w && s.moves < maxMoves) {
    const m = levels[p] === 0 ? (l => l[Math.floor(rng() * l.length)])(core.legalMoves(s, p))
                              : core.chooseMove(s, geo, p, levels[p], rng);
    check(core.isLegal(s, m, p), 'illegal move');
    w = core.applyMove(s, geo, m, p);
    let t1 = 0, t2 = 0;
    for (let i = 0; i < geo.n; i++) { if (s.own[i] === 1) t1 += s.cnt[i]; if (s.own[i] === 2) t2 += s.cnt[i]; check((s.cnt[i] === 0) === (s.own[i] === 0), 'owner/count mismatch'); }
    check(t1 === s.b[1] && t2 === s.b[2], 'frog bookkeeping');
    check(t1 + t2 === s.moves, 'frogs are conserved');
    if (!w) for (let i = 0; i < geo.n; i++) check(s.cnt[i] < geo.cap[i], 'unstable pad left behind');
    p = 3 - p;
  }
  return { w, moves: s.moves };
}
function match(dim, la, lb, games) {
  let a = 0, mv = 0, t0 = Date.now();
  for (let g = 0; g < games; g++) {
    const geo = core.generatePond(dim, 5000 + g * 31);
    const first = g % 2 === 0;                       // alternate who starts
    const r = play(geo, first ? [0, la, lb] : [0, lb, la], 99 + g);
    check(r.w !== 0, 'game did not finish');
    if ((r.w === 1) === first) a++;
    mv += r.moves;
  }
  console.log(`dim ${dim}: level ${la} beats level ${lb} in ${a}/${games} games, avg ${(mv / games).toFixed(0)} moves, ${((Date.now() - t0) / mv).toFixed(1)} ms/move`);
}
match(5, 2, 0, 40);
match(5, 1, 0, 40);
match(5, 2, 1, 40);
match(7, 2, 0, 20);
if (!process.argv.includes('--quick')) { match(5, 3, 2, 12); match(7, 3, 2, 6); }

// ---- optional pictures ----
const out = process.argv.find(a => a.startsWith('--svg='));
if (out) {
  const dir = out.slice(6);
  for (const dim of [3, 5, 7, 9, 11]) for (const seed of [1, 2, 3]) {
    const p = core.generatePond(dim, seed * 77);
    const m = Math.max(...p.x.map(Math.abs), ...p.y.map(Math.abs)) + 1;
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-m} ${-m} ${2 * m} ${2 * m}" width="700" height="700"><rect x="${-m}" y="${-m}" width="${2 * m}" height="${2 * m}" fill="#234"/>`;
    for (let i = 0; i < p.n; i++) for (const j of p.nbr[i]) if (j > i) svg += `<line x1="${p.x[i]}" y1="${p.y[i]}" x2="${p.x[j]}" y2="${p.y[j]}" stroke="#fff" stroke-width="0.04"/>`;
    for (let i = 0; i < p.n; i++) svg += `<circle cx="${p.x[i]}" cy="${p.y[i]}" r="${p.r[i]}" fill="${['', '', '#7c5', '#4a4', '#283'][p.cap[i]]}" fill-opacity="0.8"/>`;
    svg += '</svg>';
    fs.writeFileSync(path.join(dir, `pond_${dim}_${seed}.svg`), svg);
  }
}
console.log(fails ? `${fails} FAILURES` : 'all checks passed');
process.exit(fails ? 1 : 0);
