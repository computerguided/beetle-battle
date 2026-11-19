/* =============================================================================
   Lily Pond — start-up and interface glue.
   ============================================================================= */
'use strict';

(async function main() {
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const LEVEL_NOTE = { 1: 'Hops about cheerfully and often forgets to think.', 2: 'The original Beetle Battle player: picks the move that looks best right now.', 3: 'Looks several moves ahead before it leaps.' };

  function fail(msg) { $('loadMsg').textContent = msg; }
  const canvas = $('pond');

  // ---- decode the embedded pictures ----
  const names = ['frog_red', 'frog_blue', 'frog_n', 'pad', 'pad_n', 'props', 'props_n', 'grass'];
  const images = {};
  try {
    await Promise.all(names.map(n => new Promise((res, rej) => {
      const im = new Image(); im.onload = () => res(); im.onerror = () => rej(new Error('could not decode ' + n));
      im.src = ASSETS[n]; images[n] = im;
    })));
  } catch (e) { fail('The pictures could not be loaded.'); throw e; }

  let renderer;
  try { renderer = new Renderer(canvas, images, ATLAS); }
  catch (e) { fail('This pond needs WebGL 2, which this browser does not offer.'); throw e; }
  renderer.resize();

  const sound = new Sound({ ambient: ASSETS.ambient, croak1: ASSETS.croak1, croak2: ASSETS.croak2, land1: ASSETS.land1, land2: ASSETS.land2, splash: ASSETS.splash, chorus: ASSETS.chorus });

  // ---- little frog portraits for the scoreboard, cut from the sprite sheet ----
  const fr = ATLAS.frog, cell = fr.cell, zoom = 38 / (cell * 0.62);
  for (const [id, key] of [['iconRed', 'frog_red'], ['iconBlue', 'frog_blue']]) {
    const el = $(id);
    el.style.backgroundImage = `url(${ASSETS[key]})`;
    el.style.backgroundSize = `${fr.size[0] * zoom}px ${fr.size[1] * zoom}px`;
    el.style.backgroundPosition = `${-(cell * 0.19) * zoom}px ${-(cell * 0.02) * zoom}px`;
  }

  const ui = {
    loadSettings() {
      let s = {};
      try { s = JSON.parse(localStorage.getItem('lily-pond-settings') || '{}'); } catch (e) { /* private mode */ }
      if (params.has('dim')) s.dim = +params.get('dim');
      if (![3, 5, 7, 9, 11].includes(s.dim)) delete s.dim;
      return s;
    },
    save(s) { try { localStorage.setItem('lily-pond-settings', JSON.stringify(s)); } catch (e) { /* ignore */ } },
    last: {},
    update(game, soft) {
      const s = game.settings, count = game.counts();
      for (const [p, n, side, who] of [[1, 'nRed', 'sideRed', 'whoRed'], [2, 'nBlue', 'sideBlue', 'whoBlue']]) {
        const el = $(n);
        if (el.textContent !== String(count[p])) { el.textContent = count[p]; el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
        $(side).classList.toggle('on', game.winner ? game.winner === p : game.turn === p);
        $(who).textContent = s.players[p] === 'ai' ? 'Computer' : (s.players[3 - p] === 'ai' ? 'You' : 'Player');
      }
      if (soft) return;
      const t = $('turn'), p = game.turn, ai = s.players[p] === 'ai', solo = s.players[1] !== s.players[2];
      let text, thinking = false;
      if (game.winner) text = `${TEAM[game.winner].name} wins`;
      else if (game.acting) text = solo && !ai ? 'Hop!' : `${TEAM[p].name} hops`;
      else if (ai) { text = `${TEAM[p].name} is thinking`; thinking = true; }
      else text = solo ? 'Your move' : `${TEAM[p].name} to move`;
      t.textContent = text; t.classList.toggle('thinking', thinking);
      document.title = `Lily Pond — ${text}`;
      seg('segDim', String(s.dim)); seg('segRed', s.players[1]); seg('segBlue', s.players[2]); seg('segLevel', String(s.level));
      $('dimNote').textContent = `About ${s.dim * s.dim} lily pads — this one has ${game.pond.n}.`;
      $('levelNote').textContent = LEVEL_NOTE[s.level];
    },
    setBanner(b) {
      const el = $('banner');
      if (!b) { el.hidden = true; return; }
      $('bannerTitle').textContent = b.title; $('bannerSub').textContent = b.sub;
      el.className = 'glass ' + (b.team === 1 ? 'red' : 'blue'); el.hidden = false;
    },
  };
  function seg(id, value) { for (const b of $(id).children) b.classList.toggle('sel', b.dataset.v === value); }

  const game = new Game(renderer, ATLAS, sound, ui);
  if (params.has('seed')) game.newGame(+params.get('seed'));
  window.lilyPond = game;                         // handy in the console

  // ---- controls ----
  const unlock = () => sound.unlock();
  const closePanels = () => { $('panelSet').hidden = true; $('panelHelp').hidden = true; };
  const newPond = () => { closePanels(); game.newGame(); };
  canvas.addEventListener('pointermove', e => game.pointerMove(e.clientX, e.clientY));
  canvas.addEventListener('pointerleave', () => { game.hover = -1; game.pointer = null; });
  canvas.addEventListener('pointerdown', e => { unlock(); closePanels(); game.pointerMove(e.clientX, e.clientY); game.click(e.clientX, e.clientY); if (e.pointerType !== 'mouse') game.hover = -1; });
  $('btnNew').onclick = () => { unlock(); newPond(); };
  $('btnNew2').onclick = () => { unlock(); newPond(); };
  $('btnAgain').onclick = () => { unlock(); newPond(); };
  $('btnSet').onclick = () => { unlock(); $('panelHelp').hidden = true; $('panelSet').hidden = !$('panelSet').hidden; };
  $('btnHelp').onclick = () => { unlock(); $('panelSet').hidden = true; $('panelHelp').hidden = !$('panelHelp').hidden; };
  const setMuted = m => { sound.setMuted(m); $('btnSound').classList.toggle('off', m); $('waves').style.display = m ? 'none' : ''; game.settings.muted = m; ui.save(game.settings); };
  $('btnSound').onclick = () => { unlock(); setMuted(!sound.muted); };
  if (game.settings.muted) setMuted(true);
  const choose = (id, fn) => $(id).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; unlock(); fn(b.dataset.v); ui.save(game.settings); ui.update(game); });
  choose('segDim', v => { game.settings.dim = +v; game.newGame(); });
  const setPlayer = (p, v) => { game.settings.players[p] = v; if (!game.winner && !game.acting) game.nextTurn(); };
  choose('segRed', v => setPlayer(1, v));
  choose('segBlue', v => setPlayer(2, v));
  choose('segLevel', v => { game.settings.level = +v; });
  window.addEventListener('keydown', e => {
    if (e.key === 'n' || e.key === 'N') newPond();
    else if (e.key === 'm' || e.key === 'M') setMuted(!sound.muted);
    else if (e.key === 'Escape') closePanels();
  });
  let resizeTimer = 0;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { renderer.resize(); game.layout(); }, 120); });

  // ---- the loop ----
  let last = performance.now(), slow = 0, frames = 0;
  function frame(now) {
    const raw = Math.max(0, (now - last) / 1000), dt = Math.min(raw, 0.05);
    last = now;
    // step the picture down a notch on machines that cannot keep up
    if (++frames > 90) { slow += raw > 0.03 ? 1 : -0.25; slow = Math.max(0, slow); if (slow > 45 && renderer.quality > 0.5) { renderer.quality -= 0.25; slow = 0; frames = 0; } }
    renderer.resize();
    game.update(dt);
    game.draw();
    renderer.render(game.time, dt);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  requestAnimationFrame(() => $('loading').classList.add('gone'));
})();
