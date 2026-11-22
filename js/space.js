/* space.js · o céu do Stars Pixelmon (fundo fixo de todas as seções)
   · canvas de estrelas: cintilam devagar, fazem parallax com o ponteiro e com a rolagem e esticam em rastro quando a
     página rola rápido (adaptado do céu do portfólio, recolorido para a paleta do servidor)
   · estrelas cadentes de vez em quando
   · estrelinhas de 4 pontas em pixel (as mesmas do menu do servidor), em CSS: só opacidade e escala
   · nebulosas sobem com a rolagem
   Tudo pausa com a aba oculta e respeita "reduzir movimento". */
(() => {
  'use strict';

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const space = document.querySelector('.space');
  if (!space) return;

  /* ══════════ ESTRELINHAS DE PIXEL ══════════ */
  const STAR4 = '<svg viewBox="0 0 7 7" aria-hidden="true"><path fill="currentColor" d="M3 0h1v2h1v1h2v1H5v1H4v2H3V5H2V4H0V3h2V2h1z"/></svg>';
  const holder = space.querySelector('.space__sparkles');
  if (holder) {
    const n = window.innerWidth < 700 ? 18 : 34;
    const tones = ['', '', 'spark--lilac', 'spark--white'];
    let html = '';
    for (let i = 0; i < n; i++) {
      const s = 8 + Math.round(Math.random() * 3) * 5;
      html += `<span class="spark ${tones[i % tones.length]}" style="left:${(Math.random() * 100).toFixed(2)}%;top:${(Math.random() * 100).toFixed(2)}%;--s:${s}px;--d:${(3.5 + Math.random() * 5).toFixed(2)}s;--delay:${(-Math.random() * 8).toFixed(2)}s;--o:${(.55 + Math.random() * .45).toFixed(2)}">${STAR4}</span>`;
    }
    holder.innerHTML = html;
  }

  /* ══════════ CÉU EM CANVAS ══════════ */
  const canvas = space.querySelector('.space__stars');
  const c = canvas && canvas.getContext('2d');
  if (!c) return;
  const tints = ['255,255,255', '255,255,255', '255,255,255', '252,222,116', '201,155,255', '85,191,236'];
  const count = fine ? 340 : 160;
  const stars = Array.from({ length: count }, () => ({
    x: Math.random(), y: Math.random(), z: .15 + Math.pow(Math.random(), 2.2) * .85,
    ph: Math.random() * 6.283, sp: .3 + Math.random() * 1.2, tint: tints[(Math.random() * tints.length) | 0]
  }));
  let w = 0, h = 0, mx = 0, my = 0, tmx = 0, tmy = 0, lastY = window.scrollY, vel = 0, raf = 0;
  const meteors = [];
  let nextMeteor = performance.now() + 2500;

  const resize = () => {
    const d = Math.min(window.devicePixelRatio || 1, fine ? 1.5 : 1);
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = Math.round(w * d); canvas.height = Math.round(h * d);
    c.setTransform(d, 0, 0, d, 0, 0);
  };
  if (fine && !reduce) window.addEventListener('pointermove', (e) => { tmx = e.clientX / w - .5; tmy = e.clientY / h - .5; }, { passive: true });

  const draw = (now) => {
    const y = window.scrollY;
    vel += ((y - lastY) - vel) * .25; lastY = y;
    const trail = reduce ? 0 : Math.min(Math.abs(vel) * .35, 30) * (vel > 0 ? 1 : -1);
    mx += (tmx - mx) * .04; my += (tmy - my) * .04;
    c.clearRect(0, 0, w, h);
    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      const px = (((s.x * w - mx * 34 * s.z) % w) + w) % w;
      const py = (((s.y * h - y * s.z * .12 - my * 24 * s.z) % h) + h) % h;
      const tw = reduce ? .85 : .55 + .45 * Math.sin(now * .001 * s.sp + s.ph);
      const size = s.z > .75 ? 2 : s.z > .4 ? 1.5 : 1;
      const col = `rgba(${s.tint},${(.18 + .72 * s.z) * tw})`;
      if (Math.abs(trail) > 1.5) {
        c.strokeStyle = col; c.lineWidth = size;
        c.beginPath(); c.moveTo(px, py); c.lineTo(px, py + trail * s.z); c.stroke();
      } else {
        c.fillStyle = col;
        c.fillRect(Math.round(px), Math.round(py), size, size);
        /* as estrelas mais próximas ganham uma cruz de pixel quando brilham mais */
        if (s.z > .85 && tw > .9) { c.fillRect(Math.round(px) - 2, Math.round(py), size + 4, 1); c.fillRect(Math.round(px), Math.round(py) - 2, 1, size + 4); }
      }
    }
    /* estrelas cadentes */
    if (!reduce && now > nextMeteor) {
      meteors.push({ x: Math.random() * w * .8 + w * .1, y: Math.random() * h * .35, vx: -(5 + Math.random() * 4), vy: 2.4 + Math.random() * 2, life: 1 });
      nextMeteor = now + 3500 + Math.random() * 6000;
    }
    for (let i = meteors.length - 1; i >= 0; i--) {
      const m = meteors[i];
      m.x += m.vx; m.y += m.vy; m.life -= .012;
      if (m.life <= 0) { meteors.splice(i, 1); continue; }
      const g = c.createLinearGradient(m.x, m.y, m.x - m.vx * 14, m.y - m.vy * 14);
      g.addColorStop(0, `rgba(255,246,200,${m.life})`); g.addColorStop(.35, `rgba(249,203,17,${m.life * .55})`); g.addColorStop(1, 'rgba(160,20,224,0)');
      c.strokeStyle = g; c.lineWidth = 2;
      c.beginPath(); c.moveTo(m.x, m.y); c.lineTo(m.x - m.vx * 14, m.y - m.vy * 14); c.stroke();
      c.fillStyle = `rgba(255,255,255,${m.life})`; c.fillRect(Math.round(m.x) - 1, Math.round(m.y) - 1, 3, 3);
    }
  };
  const loop = (now) => { raf = 0; draw(now); if (!document.hidden) raf = requestAnimationFrame(loop); };

  resize();
  window.addEventListener('resize', () => { resize(); if (reduce) draw(performance.now()); });
  if (reduce) draw(performance.now());
  else {
    raf = requestAnimationFrame(loop);
    document.addEventListener('visibilitychange', () => {
      space.classList.toggle('is-paused', document.hidden);
      if (!document.hidden && !raf) raf = requestAnimationFrame(loop);
    });
  }

  /* ══════════ NEBULOSAS SOBEM COM A ROLAGEM (só transform) ══════════ */
  const neb = space.querySelector('.space__nebula');
  if (neb && !reduce) {
    let queued = false;
    window.addEventListener('scroll', () => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const p = max > 0 ? window.scrollY / max : 0;
        neb.style.transform = `translate3d(0, ${(-p * 14).toFixed(2)}%, 0)`;
      });
    }, { passive: true });
  }
})();
