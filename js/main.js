/* main.js · Stars Pixelmon
   ══════════════════════════════════════════════════════════════════════════
   CONFIGURAÇÃO: tudo o que muda com frequência fica aqui, em um só lugar.
   - Deixe '' (vazio) enquanto não tiver o endereço: o botão continua levando para a página do próprio site.
   - Endereços que começam com https:// abrem em nova aba.
   ══════════════════════════════════════════════════════════════════════════ */
window.STARS = {
  ip: 'starspixelmon.com.br',                            // A CONFIRMAR: endereço para entrar no servidor

  /* LOJA OFICIAL (parceira). Todo botão de compra do site leva para cá. */
  loja: 'https://starspixelmon.centralcart.ai',          // loja oficial (CentralCart)
  /* Opcional: link direto de cada item. Vazio = usa o endereço da loja acima. */
  lojaItens: {
    vips: '',
    'vip-lunar': '',
    'vip-solar': '',
    'vip-astral': '',
    'vip-cosmo': '',
    'vip-estelar': '',
    passe: '',
    owlith: '',
    'shirlaw-selvagem': '',
    chaves: '',
    coins: '',
    tokens: ''
  },

  launcher: '',                                          // A CONFIRMAR: link de download do launcher Stars
  discord: 'https://discord.gg/8XNCDBH5BE',              // convite do Discord
  youtube: 'https://www.youtube.com/@starspixelmon',     // A CONFIRMAR (montado a partir do @starspixelmon)
  instagram: 'https://www.instagram.com/starspixelmon',  // A CONFIRMAR
  tiktok: 'https://www.tiktok.com/@starspixelmon'        // A CONFIRMAR
};

(() => {
  'use strict';
  const cfg = window.STARS;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const openOutside = (a, url) => {
    a.href = url;
    if (/^https?:/.test(url)) { a.target = '_blank'; a.rel = 'noopener'; }
  };

  /* ══════════ IP E LINKS (a partir da configuração) ══════════ */
  $$('[data-ip]').forEach(el => { el.textContent = cfg.ip; });

  /* data-link="discord" | "launcher" | "youtube" ... */
  $$('[data-link]').forEach(a => {
    const url = cfg[a.dataset.link];
    if (url) openOutside(a, url);
  });

  /* data-loja="" (loja) ou data-loja="vip-lunar" (item): leva à loja oficial */
  $$('[data-loja]').forEach(a => {
    const key = a.dataset.loja;
    const url = (key && cfg.lojaItens && cfg.lojaItens[key]) || cfg.loja;
    if (url) openOutside(a, url);
  });

  /* ══════════ COPIAR IP (com alternativa quando a área de transferência não está disponível) ══════════ */
  const copyText = (text) => {
    const legacy = () => new Promise((ok, fail) => {
      const t = document.createElement('textarea');
      t.value = text;
      t.setAttribute('readonly', '');
      t.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
      document.body.appendChild(t);
      t.select();
      try { document.execCommand('copy') ? ok() : fail(); } catch (e) { fail(e); }
      t.remove();
    });
    if (!navigator.clipboard || !window.isSecureContext) return legacy();
    /* a API moderna pode recusar (página sem foco, permissão) ou demorar: cai no método antigo */
    const timeout = new Promise((_, fail) => setTimeout(fail, 800));
    return Promise.race([navigator.clipboard.writeText(text), timeout]).catch(legacy);
  };

  /* "Copiar build" (página de cada Starian): copia a build do card no formato do Showdown */
  $$('[data-copy-build]').forEach(btn => {
    const label = $('span', btn);
    const base = label ? label.textContent : '';
    const box = btn.closest('.sd-build');
    const pre = box && $('.sd-build__export', box);   /* a build deste card */
    if (!pre) return;
    btn.addEventListener('click', () => {
      copyText(pre.textContent)
        .then(() => { btn.classList.add('is-done'); if (label) label.textContent = 'Copiado!'; })
        .catch(() => {
          /* sem acesso à área de transferência: mostra o texto selecionado para copiar à mão */
          pre.hidden = false;
          const r = document.createRange();
          r.selectNodeContents(pre);
          const s = getSelection();
          s.removeAllRanges();
          s.addRange(r);
          if (label) label.textContent = 'Selecione e copie';
        })
        .finally(() => {
          setTimeout(() => { btn.classList.remove('is-done'); if (label) label.textContent = base; }, 1800);
        });
    });
  });

  $$('[data-copy]').forEach(btn => {
    const label = $('span', btn);
    const base = label ? label.textContent : '';
    btn.addEventListener('click', () => {
      copyText(cfg.ip)
        .then(() => {
          btn.classList.add('is-done');
          if (label) label.textContent = 'Copiado!';
        })
        .catch(() => {
          if (label) label.textContent = 'Selecione e copie';
          const code = btn.parentElement && $('code', btn.parentElement);
          if (code) {
            const r = document.createRange();
            r.selectNodeContents(code);
            const s = getSelection();
            s.removeAllRanges();
            s.addRange(r);
          }
        })
        .finally(() => {
          setTimeout(() => { btn.classList.remove('is-done'); if (label) label.textContent = base; }, 1800);
        });
    });
  });

  /* ══════════ MENU MOBILE ══════════ */
  /* Tela cheia: o header continua por cima (o botão vira X), a página para de rolar (CSS, html:has)
     e o resto da página fica inerte enquanto o menu está aberto. */
  const header = $('.site-header');
  const menuBtn = $('.menu-btn');
  const mobileNav = $('#mobile-nav');
  if (header && menuBtn && mobileNav) {
    const behind = [$('main'), $('footer')].filter(Boolean);
    const icon = $('use', menuBtn);
    const isOpen = () => mobileNav.classList.contains('is-open');
    const setOpen = (open) => {
      if (open === isOpen()) return;
      mobileNav.classList.toggle('is-open', open);
      header.classList.toggle('is-open', open);
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
      if (icon) icon.setAttribute('href', open ? '#i-x' : '#i-menu');
      behind.forEach(el => { el.inert = open; });
      if (open) { const first = $('a', mobileNav); if (first) first.focus({ preventScroll: true }); }
    };
    menuBtn.addEventListener('click', () => setOpen(!isOpen()));
    $$('a', mobileNav).forEach(a => a.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isOpen()) { setOpen(false); menuBtn.focus(); } });
    /* virou desktop com o menu aberto: fecha, para não deixar a página travada */
    matchMedia('(min-width: 1141px)').addEventListener('change', (e) => { if (e.matches) setOpen(false); });
  }

  /* ══════════ MENU ACOMPANHA A ROLAGEM (scroll spy) ══════════
     Links do menu que apontam para uma seção DESTA página (ex.: /#faq na home) ficam destacados
     enquanto a seção está na tela. Fora delas, volta o destaque da própria página (aria-current="page"). */
  /* página de um endereço, sem "index.html" nem barra final: "/", "/como-jogar", "/starians/owlith" */
  const fileOf = (path) => path.replace(/index\.html$/, '').replace(/\/+$/, '') || '/';
  const here = fileOf(location.pathname);
  const navLinks = $$('.nav__links a, .mobile-nav a');
  const pageLinks = navLinks.filter(a => a.getAttribute('aria-current') === 'page');
  /* link para uma seção desta página, ou link de outra página com data-spy (ex.: "Loja" acende na seção #loja da home) */
  const spyId = (a) => a.dataset.spy || a.hash.slice(1);
  const hashLinks = navLinks.filter(a => a.hash && fileOf(a.pathname) === here && document.getElementById(a.hash.slice(1)));
  const spyLinks = navLinks.filter(a => hashLinks.includes(a) || (a.dataset.spy && document.getElementById(a.dataset.spy)));
  const spySections = $$('main section[id]');
  if (spyLinks.length && spySections.length) {
    /* link para esta mesma página vira âncora local: rola suave em vez de recarregar (a home pode abrir em "/") */
    hashLinks.forEach(a => a.setAttribute('href', a.hash));
    let active = null;
    const setActive = (id) => {
      if (id === active) return;
      active = id;
      const hits = spyLinks.filter(a => spyId(a) === id);
      spyLinks.forEach(a => { if (!hits.includes(a)) a.removeAttribute('aria-current'); });
      hits.forEach(a => a.setAttribute('aria-current', 'location'));
      pageLinks.forEach(a => {
        if (hits.includes(a)) return;   /* ex.: "Como jogar" na própria página: já acendeu pela seção */
        if (hits.length) a.removeAttribute('aria-current');
        else a.setAttribute('aria-current', 'page');
      });
    };
    let ticking = false;
    const update = () => {
      ticking = false;
      /* linha de leitura: logo abaixo do cabeçalho fixo, a 30% da altura da tela */
      const line = (header ? header.offsetHeight : 0) + window.innerHeight * 0.3;
      let current = null;
      spySections.forEach(sec => { if (sec.getBoundingClientRect().top <= line) current = sec.id; });
      /* fim da página: a última seção pode ser curta demais para alcançar a linha */
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
        current = spySections[spySections.length - 1].id;
      }
      setActive(current);
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ══════════ URL LIMPA: âncoras não ficam na barra de endereço ══════════
     Link para uma seção desta página (ex.: "/#loja" estando na home): rola até ela sem gravar "#loja" na URL.
     Chegando de outra página com âncora (ex.: "/como-jogar#guia"): rola até a seção e tira o "#guia" da barra.
     Sem JS, as âncoras funcionam do jeito normal do navegador. */
  const cleanUrl = () => history.replaceState(history.state, '', location.pathname + location.search);
  const goTo = (el) => {
    el.scrollIntoView({ behavior: reduce ? 'instant' : 'smooth', block: 'start' });
    if (el.tabIndex >= 0 || el.hasAttribute('tabindex')) el.focus({ preventScroll: true });   /* ex.: "Pular para o conteúdo" */
  };
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href*="#"]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || a.target === '_blank') return;
    if (a.origin !== location.origin || fileOf(a.pathname) !== here || !a.hash) return;
    const el = document.getElementById(decodeURIComponent(a.hash.slice(1)));
    if (!el) return;
    e.preventDefault();
    goTo(el);
    if (location.hash) cleanUrl();
  });
  if (location.hash) {
    const el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    /* espera as imagens carregarem (a posição da seção só fica certa depois), rola e limpa a URL */
    window.addEventListener('load', () => {
      if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
      cleanUrl();
    }, { once: true });
  }

  /* ══════════ FILTROS DA STARIAN DEX (seção #starians da home) ══════════ */
  const dex = $('#dex-grid');
  if (dex) {
    const chips = $$('[data-filter]');
    const cards = $$('.starian', dex);
    const count = $('#dex-count');
    const apply = (filter) => {
      let shown = 0;
      cards.forEach(card => {
        const show = filter === 'todos' || card.dataset.group.split(' ').includes(filter);
        card.hidden = !show;
        if (show) shown++;
      });
      chips.forEach(ch => ch.setAttribute('aria-pressed', String(ch.dataset.filter === filter)));
      if (count) count.textContent = shown === 1 ? '1 Starian' : `${shown} Starians`;
    };
    chips.forEach(ch => ch.addEventListener('click', () => apply(ch.dataset.filter)));
    apply('todos');
  }

  /* ══════════ CARROSSÉIS NO CELULAR: pontinhos de posição ══════════
     O carrossel em si é só CSS ([data-carousel] em style.css). Aqui: um ponto por parada de encaixe,
     o ponto da posição atual acende e tocar num ponto leva até ela. Fora do celular os pontos ficam escondidos. */
  const carousels = $$('[data-carousel]');
  const syncDots = [];
  carousels.forEach(list => {
    const dots = document.createElement('div');
    dots.className = 'carousel-dots';
    dots.setAttribute('aria-label', `Posição: ${list.getAttribute('aria-label') || 'lista'}`);
    list.after(dots);
    let stops = [];
    /* parada atual = a última cuja borda esquerda já passou do início da área visível (+ meio card de folga) */
    const current = () => {
      const start = list.getBoundingClientRect().left + (parseFloat(getComputedStyle(list).scrollPaddingLeft) || 0);
      let i = 0;
      stops.forEach((el, k) => { if (el.getBoundingClientRect().left <= start + el.offsetWidth / 2) i = k; });
      if (list.scrollLeft + list.clientWidth >= list.scrollWidth - 2) i = stops.length - 1;   /* chegou ao fim */
      return i;
    };
    const paint = () => {
      const i = current();
      $$('button', dots).forEach((b, k) => b.setAttribute('aria-current', String(k === i)));
    };
    const build = () => {
      stops = Array.from(list.children).filter(el => !el.hidden && getComputedStyle(el).scrollSnapAlign.includes('start'));
      dots.replaceChildren(...stops.map((el, k) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', `Ir para o item ${k + 1} de ${stops.length}`);
        b.addEventListener('click', () => {
          const pad = parseFloat(getComputedStyle(list).scrollPaddingLeft) || 0;
          const left = el.getBoundingClientRect().left - list.getBoundingClientRect().left + list.scrollLeft - pad;
          list.scrollTo({ left, behavior: reduce ? 'auto' : 'smooth' });
        });
        return b;
      }));
      dots.hidden = stops.length < 2;
      /* acessibilidade: faixa que rola de lado precisa ser alcançável pelo teclado (Tab + setas),
         mesmo quando os cards não têm link (chaves). Fora do carrossel, sai da ordem de Tab. */
      const rola = list.scrollWidth > list.clientWidth + 1;
      if (rola) list.tabIndex = 0; else list.removeAttribute('tabindex');
      paint();
    };
    let raf = 0;
    list.addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(paint); }, { passive: true });
    /* página de um Starian: a faixa "Todos os Starians" já abre mostrando o Starian atual */
    const toCurrent = () => {
      const cur = $('.is-current', list);
      if (!cur || list.scrollWidth <= list.clientWidth) return;
      const pad = parseFloat(getComputedStyle(list).scrollPaddingLeft) || 0;
      list.scrollLeft += cur.getBoundingClientRect().left - list.getBoundingClientRect().left - pad;
    };
    syncDots.push(() => { list.scrollLeft = 0; toCurrent(); build(); });
    toCurrent();
    build();
  });
  window.matchMedia('(max-width: 759px)').addEventListener('change', () => syncDots.forEach(fn => fn()));
  /* a Dex muda de tamanho com os filtros: refaz os pontos */
  $$('[data-filter]').forEach(ch => ch.addEventListener('click', () => syncDots.forEach(fn => fn())));

  /* ══════════ MODAL DE IMAGEM (kits dos VIPs na seção #vips da home): setas trocam, Esc fecha ══════════ */
  const lb = $('#lightbox');
  const zooms = $$('[data-zoom]');
  if (lb && zooms.length && typeof lb.showModal === 'function') {
    const img = $('.lightbox__img', lb);
    const cap = $('.lightbox__cap', lb);
    let current = 0;
    let opener = null;
    const show = (i) => {
      current = (i + zooms.length) % zooms.length;
      const src = $('img', zooms[current]);
      img.src = src.currentSrc || src.src;
      img.alt = src.alt;
      cap.textContent = src.alt;
    };
    zooms.forEach((z, i) => z.addEventListener('click', () => { opener = z; show(i); lb.showModal(); }));
    lb.addEventListener('click', (e) => {
      const action = e.target.closest('[data-lb]');
      if (action) {
        if (action.dataset.lb === 'close') lb.close();
        else show(current + (action.dataset.lb === 'next' ? 1 : -1));
        return;
      }
      if (e.target === lb || e.target.classList.contains('lightbox__fig')) lb.close();   // clique fora da imagem
    });
    lb.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); show(current + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(current - 1); }
    });
    lb.addEventListener('close', () => { if (opener) opener.focus(); });
  }

  /* ══════════ MENU GANHA PROFUNDIDADE AO ROLAR ══════════ */
  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ══════════ CARDS COM PROFUNDIDADE: inclinam e refletem a luz seguindo o ponteiro ══════════
     Vale para VIPs, destaques da loja, Dex, banner das caixas, moedas e chaves (inclusive os "Em breve"). Cards largos ganham perspectiva maior
     (inclinam menos). Só com mouse (não em toque) e sem "reduzir movimento". Reflexo: .has-glare (style.css). */
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (finePointer && !reduce) {
    $$('.vip, .offer, .starian, .bento--banner > *, .keys .product').forEach(card => {
      card.classList.add('has-glare');
      let raf = 0;
      card.addEventListener('pointermove', (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;
        const y = (e.clientY - r.top) / r.height;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          card.style.transition = 'transform .15s ease-out';
          card.style.transform = `perspective(${Math.max(900, Math.round(r.width * 2))}px) rotateX(${((.5 - y) * 6).toFixed(2)}deg) rotateY(${((x - .5) * 8).toFixed(2)}deg) translateY(-4px)`;
          card.style.setProperty('--gx', `${(x * 100).toFixed(1)}%`);
          card.style.setProperty('--gy', `${(y * 100).toFixed(1)}%`);
        });
      });
      card.addEventListener('pointerleave', () => {
        cancelAnimationFrame(raf);
        card.style.transition = 'transform .7s cubic-bezier(.22, 1, .36, 1)';
        card.style.transform = '';
      });
    });
  }

  /* ══════════ REVELAÇÃO AO ROLAR (cards irmãos entram em cascata) ══════════ */
  const reveal = $$('[data-reveal]');
  if (!reduce) {
    reveal.forEach(el => {
      const sibs = Array.from(el.parentElement.children).filter(c => c.hasAttribute('data-reveal'));
      const i = sibs.indexOf(el);
      if (i > 0) {
        el.style.transitionDelay = `${Math.min(i, 5) * 80}ms`;
        el.addEventListener('transitionend', () => { el.style.transitionDelay = ''; }, { once: true });
      }
    });
  }
  if (reduce || !('IntersectionObserver' in window)) {
    reveal.forEach(el => el.classList.add('is-in'));
  } else {
    let answered = false;
    const io = new IntersectionObserver((entries, obs) => {
      answered = true;
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('is-in'); obs.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    reveal.forEach(el => io.observe(el));
    /* segurança: se o observador nunca responder (navegador antigo, aba em segundo plano), nada fica escondido */
    setTimeout(() => { if (!answered) { io.disconnect(); reveal.forEach(el => el.classList.add('is-in')); } }, 2000);
  }

  /* ano do rodapé */
  $$('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });
})();
