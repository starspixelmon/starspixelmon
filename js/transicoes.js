/* transicoes.js · Stars Pixelmon
   Arte do Starian que "voa" entre a Starian Dex (home) e a página do Starian, nos dois sentidos.
   Carregado no <head> sem defer: o evento pagereveal precisa estar ouvido antes da primeira pintura.
   O CSS (css/style.css, "TROCA DE PÁGINA") cuida do resto da transição. Sem suporte: nada acontece. */
(() => {
  'use strict';
  if (!('onpagereveal' in window)) return;
  const NAME = 'starian-art';
  const slug = (url) => { const m = /starian-([a-z0-9-]+)\.html/.exec(url || ''); return m ? m[1] : null; };

  /* arte do card da Dex que leva ao Starian (null se o card estiver escondido pelo filtro) */
  const cardArt = (s, onlyVisible) => {
    const a = document.querySelector(`#dex-grid a[href="starian-${s}.html"]`);
    const card = a && a.closest('.starian');
    if (!card || card.hidden) return null;
    const img = card.querySelector('.starian__art > img');
    if (!img || !onlyVisible) return img;
    const r = img.getBoundingClientRect();
    return r.bottom > 0 && r.top < innerHeight ? img : null;   // fora da tela: só o fade normal
  };
  const tag = (img, vt) => {
    if (!img) return;
    img.style.viewTransitionName = NAME;
    vt.finished.finally(() => { img.style.viewTransitionName = ''; });
  };

  /* saindo da home para um Starian */
  addEventListener('pageswap', (e) => {
    if (!e.viewTransition || !e.activation || !e.activation.entry) return;
    const s = slug(e.activation.entry.url);
    if (s && !slug(location.pathname)) tag(cardArt(s, true), e.viewTransition);
  });

  /* chegando na home vindo de um Starian (botão voltar ou link "Starians") */
  addEventListener('pagereveal', (e) => {
    if (!e.viewTransition || !window.navigation || !navigation.activation || !navigation.activation.from) return;
    const s = slug(navigation.activation.from.url);
    if (s && !slug(location.pathname)) tag(cardArt(s, false), e.viewTransition);
  });
})();
