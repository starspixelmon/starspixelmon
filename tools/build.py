"""
Stars Pixelmon · manutenção do site (Python 3, sem dependências)

    python tools/build.py

O que faz, nesta ordem:
  1. Gera uma página por Starian (starians/<id>/index.html, endereço /starians/<id>) a partir de tools/data/starians.json.
  2. Copia os blocos comuns de tools/layout/ para TODAS as páginas do site (PAGES abaixo), entre os marcadores:
        <!-- @head --> ... <!-- /@head -->         (ícones, fontes, CSS)
        <!-- @header --> ... <!-- /@header -->     (céu, cabeçalho e menu)
        <!-- @footer --> ... <!-- /@footer -->     (rodapé)
        <!-- @scripts --> ... <!-- /@scripts -->   (JS)
     O link do menu da página atual recebe aria-current="page" (vem de <body data-page="...">).
  3. Refaz sitemap.xml com todas as páginas que não têm "noindex".

URLs limpas (sem .html): cada página é uma pasta com index.html e todo caminho começa na raiz ("/css/...").
Por isso o site precisa de um servidor para abrir (Live Server no VS Code, ou python -m http.server).
O .htaccess redireciona os endereços antigos (.html) para os novos. Rode o build depois de mudar
qualquer coisa em tools/layout/ ou tools/data/. Ao mudar CSS ou JS, suba VERSION para o navegador
não usar a versão antiga do cache.
"""
import datetime
import html
import json
import re
from pathlib import Path

SITE_URL = 'https://starspixelmon.com.br'   # domínio oficial (canonical, sitemap, Open Graph)
VERSION = '78'                                # suba ao alterar css/style.css ou js/*.js

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT                                   # o site fica na raiz do projeto (pronto para GitHub Pages)
TOOLS = ROOT / 'tools'
BLOCKS = ('head', 'header', 'footer', 'scripts')
def write_if_changed(path, text):
    """grava só se o conteúdo mudou: preserva a data do arquivo, que vira o lastmod do sitemap"""
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')
    return True


def esc(text):
    return html.escape(str(text), quote=True)


def size_attrs(src, default=(32, 32)):
    """width/height reais da imagem (lê com Pillow, se instalado; sem ele, usa o padrão)"""
    try:
        from PIL import Image
        with Image.open(SITE / src) as im:
            w, h = im.size
    except Exception:
        w, h = default
    return f'width="{w}" height="{h}"'


def site_pages():
    """todas as páginas do site: as .html da raiz (home, 404, starian.html) + cada pasta com index.html"""
    pages = list(SITE.glob('*.html'))
    pages += [p for p in SITE.glob('*/index.html') if p.parent.name not in ('tools', 'assets', 'bases')]
    pages += list(SITE.glob('starians/*/index.html'))
    return sorted(pages)


# ══════════════════════════════════════════════════════════════════════════
# 1. Páginas dos Starians
# ══════════════════════════════════════════════════════════════════════════
def badges(tags):
    return '\n'.join(
        f'            <li class="badge{" badge--" + cor if cor else ""}">{esc(nome)}</li>' for nome, cor in tags
    )


def mini(s, numero, atual=False):
    current = ' aria-current="page"' if atual else ''
    estado = ' is-current' if atual else ''
    return (
        f'        <li><a class="sd-mini tile tile--{s["cor"]}{estado}" href="/starians/{s["id"]}"{current}>'
        f'<img class="px" src="/{s["sprites"][0][1]}" {size_attrs(s["sprites"][0][1])} alt="">'
        f'<span><small>#{numero:03d}</small>{esc(s["nome"])}</span></a></li>'
    )


# ══════════════════════════════════════════════════════════════════════════
# 1b. Ficha completa do Starian (dados do StarianBuilder em tools/data/fichas.json)
# ══════════════════════════════════════════════════════════════════════════
SOON = '''      <aside class="highlight tile tile--indigo sd-soon">
        <img class="px highlight__icon" src="/img/px/cadeado-aberto.webp" width="16" height="16" alt="">
        <div>
          <h2>Ficha completa em breve</h2>
          <p>Tipo, habilidades, ataques e stats chegam com a Starian Dex completa.</p>
        </div>
      </aside>
'''


def tipo_li(t):
    return f'<li class="type type--{t["id"]}">{esc(t["nome"])}</li>'


def faixa(v):
    """faixa do atributo (cor da barra)"""
    return 'low' if v < 60 else 'mid' if v < 90 else 'high' if v < 120 else 'top'


def card(cor, titulo, corpo, extra=''):
    return (f'        <article class="tile tile--{cor} sd-card{extra}">\n'
            f'          <h3 class="sd-card__title">{titulo}</h3>\n{corpo}\n        </article>')


def lista_dl(pares, classe='sd-data'):
    linhas = ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in pares if v)
    return f'          <dl class="{classe}">{linhas}</dl>'


def secao(sid, titulo, corpo, acao=''):
    """seção da ficha; acao = botão no cabeçalho, à direita do título (ex.: "Copiar builds")"""
    cab = f'        <h2 class="subhead" id="{sid}">{titulo}</h2>'
    if acao:
        cab = f'        <div class="sd-block__head">\n  {cab}\n          {acao}\n        </div>'
    return (f'\n      <section class="sd-block" aria-labelledby="{sid}">\n'
            f'{cab}\n{corpo}\n      </section>\n')


def ficha_html(s, f, fichas):
    if not f:
        return ''
    cor = s['cor']

    # ── Em batalha
    stats = ''.join(
        f'<div class="stats__row stats__row--{faixa(a["valor"])}"><dt>{esc(a["nome"])}</dt>'
        f'<dd><span class="stats__num">{a["valor"]}</span><span class="stats__bar" style="--v:{a["valor"]}" aria-hidden="true"></span></dd></div>'
        for a in f['atributos'])
    stats += f'<div class="stats__row stats__row--total"><dt>Total</dt><dd><span class="stats__num">{f["total"]}</span></dd></div>'
    tipos = f'          <ul class="types">{"".join(tipo_li(t) for t in f["tipos"])}</ul>'
    c_tipo = card(cor, 'Tipo e atributos base', tipos + f'\n          <dl class="stats">{stats}</dl>')

    habs = ''
    for h in f['habilidades']:
        selo = ' <span class="badge badge--violet">Exclusiva do Stars</span>' if h['propria'] else ''
        efeito = f'<p>{esc(h["efeito"])}</p>' if h['efeito'] else ''
        habs += f'<li><span class="abilities__slot">{esc(h["slot"])}</span><b>{esc(h["nome"])}</b>{selo}{efeito}</li>'
    c_hab = card(cor, 'Habilidades', f'          <ul class="abilities">{habs}</ul>')
    # fraquezas e resistências (tabela de tipos; habilidades não entram na conta)
    linhas_f = ''.join(
        f'<div><dt>{esc(gr["rotulo"])}</dt><dd><ul class="types types--sm">{"".join(tipo_li(t) for t in gr["tipos"])}</ul></dd></div>'
        for gr in f.get('fraquezas', []))
    c_fraq = card(cor, 'Fraquezas e resistências',
                  f'          <dl class="sd-weak">{linhas_f}</dl>\n'
                  f'          <p class="sd-note sd-note--sm">Pela tabela de tipos, sem contar habilidades.</p>')
    # golpe exclusivo: linha própria em largura total (nome e números de um lado, descrição do outro)
    c_golpe = ''
    g = f.get('golpe_exclusivo')
    if g:
        # o título "Golpe exclusivo" fica dentro da coluna da esquerda: o efeito, à direita, ocupa a altura toda do card
        corpo = (f'          <div class="sd-move">\n          <div class="sd-move__head"><h3 class="sd-card__title">Golpe exclusivo</h3>'
                 f'<p class="sd-move__name">{esc(g["nome"])}</p>'
                 f'<ul class="types"><li class="type type--{g["tipo_id"]}">{esc(g["tipo"])}</li>'
                 f'<li class="type type--cat">{esc(g["categoria"])}</li></ul>'
                 + lista_dl([('Poder', str(g['poder'])), ('Precisão', g['precisao']), ('PP', str(g['pp']))], 'sd-move__nums').strip()
                 + '</div>\n'
                 + (f'          <div class="sd-move__desc"><p class="sd-move__label">Efeito</p><p>{esc(g["descricao"])}</p></div>\n' if g['descricao'] else '')
                 + '          </div>')
        c_golpe = f'\n        <article class="tile tile--{cor} sd-card sd-card--wide">\n{corpo}\n        </article>'
    # atributos à esquerda; fraquezas + habilidades empilhadas à direita (alturas parecidas); golpe embaixo
    batalha = secao('batalha-titulo', 'Em batalha',
                    f'        <div class="sd-grid">\n{c_tipo}\n        <div class="sd-stack">\n{c_fraq}\n{c_hab}\n'
                    f'        </div>{c_golpe}\n        </div>')

    # ── Captura e criação
    if f['spawns']:
        onde = ''.join(f'<li>{esc(sp["onde"])}. <b>Níveis {esc(sp["niveis"])}</b></li>' for sp in f['spawns'])
        onde = f'          <ul class="sd-list">{onde}</ul>'
    else:
        onde = '          <p class="sd-note">Não aparece na natureza.</p>'
    evo = [f'Evolui para <b>{esc(e["nome"])}</b> ({esc(e["como"])})' for e in f['evolui_para']]
    for outro, fo in fichas.items():
        for e in fo.get('evolui_para', []):
            if e['nome'].lower() == s['nome'].lower():
                evo.insert(0, f'Evolui de <b>{esc(outro.capitalize())}</b> ({esc(e["como"])})')
    evo_html = (f'          <ul class="sd-list">{"".join(f"<li>{x}</li>" for x in evo)}</ul>' if evo
                else '          <p class="sd-note">Não evolui.</p>')
    # linha 1: onde encontrar + evolução (mesma altura) · linha 2: dados em blocos, largura total
    criacao = secao('captura-titulo', 'Captura e criação',
                    '        <div class="sd-grid">\n'
                    + card(cor, 'Onde encontrar', onde) + '\n' + card(cor, 'Evolução', evo_html) + '\n'
                    + card(cor, 'Dados', lista_dl(f['dados'], 'sd-tiles'), ' sd-card--wide') + '\n        </div>')

    # ── Golpes
    # por nível: lista em colunas (quantas couberem na largura), em vez de uma tabela comprida
    linhas = ''.join(f'<div><dt><small>Nv.</small> {esc(n["nivel"])}</dt><dd>{esc(", ".join(n["golpes"]))}</dd></div>'
                     for n in f['golpes_nivel'])
    total_nv = sum(len(n['golpes']) for n in f['golpes_nivel'])
    blocos = [f'        <details class="tile tile--{cor} sd-moves" open>\n'
              f'          <summary><h3>Por nível <small>{total_nv}</small></h3></summary>\n'
              f'          <dl class="lvl-list">{linhas}</dl>\n        </details>']
    for titulo, chave in (('Por ovo', 'golpes_ovo'), ('Com tutor', 'golpes_tutor'), ('Por TM', 'golpes_tm')):
        if f.get(chave):
            itens = ''.join(f'<li>{esc(x)}</li>' for x in f[chave])
            blocos.append(f'        <details class="tile tile--{cor} sd-moves">\n'
                          f'          <summary><h3>{titulo} <small>{len(f[chave])}</small></h3></summary>\n'
                          f'          <ul class="move-list">{itens}</ul>\n        </details>')
    golpes = secao('golpes-titulo', 'Golpes', '\n'.join(blocos))

    # ── Builds recomendadas
    builds = ''
    if f['builds']:
        cards = []
        for b in f['builds']:
            def opcoes(v):
                """cada opção inteira (ex.: "Timid (+Spe −Atk)") não quebra; se faltar espaço, quebra só na barra"""
                return ' / '.join(f'<span class="nw">{esc(x)}</span>' for x in v.split(' / '))
            gs = ''.join(f'<li>{opcoes(g)}</li>' for g in b['golpes'])   # alternativas já vêm com barra: "Psychic / Psyshock"
            pares = [('Item', b['item']), ('Habilidade', b['habilidade']), ('Natureza', b['natureza']),
                     ('EVs', b['evs']), ('IVs', b.get('ivs', ''))]
            dados = ''.join(f'<div><dt>{k}</dt><dd>{opcoes(v)}</dd></div>' for k, v in pares if v)
            corpo = ('          <div class="sd-build__body">\n'
                     f'          <dl class="sd-data sd-build__data">{dados}</dl>'
                     f'\n          <ol class="sd-build__moves">{gs}</ol>\n          </div>')
            # cada card tem o próprio botão, no rodapé do card; o texto copiado fica escondido no card
            rodape = ('\n          <div class="sd-build__foot"><button class="btn btn--ghost btn--sm" type="button" data-copy-build>'
                      '<svg aria-hidden="true"><use href="#i-copy"/></svg><span>Copiar build</span></button></div>'
                      f'\n          <pre class="sd-build__export" hidden>{esc(b["texto"])}</pre>') if b.get('texto') else ''
            extra = ' sd-build' + (' sd-card--wide' if len(f['builds']) == 1 else '')   # uma build só: largura total
            cards.append(card(cor, esc(b['titulo']), corpo + rodape, extra))
        titulo = 'Builds recomendadas' if len(cards) > 1 else 'Build recomendada'
        builds = secao('builds-titulo', titulo, '        <div class="sd-grid">\n' + '\n'.join(cards) + '\n        </div>')

    # ordem: em batalha, build recomendada, captura e criação, golpes
    return batalha + builds + criacao + golpes


def starian_page(s, lista, fichas=None):
    pos = lista.index(s)
    numero = pos + 1
    por_id = {x['id']: x for x in lista}
    anterior = lista[pos - 1]
    proximo = lista[(pos + 1) % len(lista)]
    url = f'{SITE_URL}/starians/{s["id"]}'
    titulo = f'{s["nome"]}: Starian #{numero:03d} | Stars Pixelmon'
    arte_abs = f'{SITE_URL}/{s["arte"]["src"]}'

    # "Grupo" (Comum, Inicial…) + "Categoria" do StarianBuilder (Estrela, Garra Branca…) logo abaixo
    fx_id = (fichas or {}).get(s['id']) or {}
    cat, dex = fx_id.get('categoria'), fx_id.get('pokedex')
    linhas = []
    for k, v in s['ficha']:
        if k == 'Categoria':
            linhas.append(('Grupo', v))
            if cat:
                linhas.append(('Categoria', cat))
            if dex:
                linhas.append(('Descrição', dex))   # descrição da Pokédex (StarianBuilder)
        else:
            linhas.append((k, v))
    # a linha evolutiva já aparece em cards logo abaixo: não repete na ficha
    ficha = '\n'.join(
        f'          <div{" class=\"sd-facts__long\"" if k == "Descrição" else ""}>\n            <dt>{esc(k)}</dt>\n            <dd>{esc(v)}</dd>\n          </div>' for k, v in linhas
        if not (s.get('familia') and k == 'Linha evolutiva')
    )
    # sprites: faixa compacta no rodapé do card da arte
    sprites = '\n'.join(
        f'            <li><figure class="sd-sprite">'
        f'<img class="px" src="/{src}" {size_attrs(src)} alt="Sprite {esc(r.lower())} de {esc(s["nome"])}" loading="lazy" decoding="async">'
        f'<figcaption>{esc(r)}</figcaption></figure></li>'
        for r, src in s['sprites']
    )
    compra = ''
    if s.get('compra'):
        c = s['compra']
        compra = f'''
        <p class="btn-row">
          <a class="btn btn--play" href="/#loja" data-loja="{c["loja"]}">
            <svg aria-hidden="true"><use href="#i-cart"/></svg>{esc(c["rotulo"])}
          </a>
        </p>'''
    familia = ''
    if s.get('familia'):
        itens = '\n'.join(mini(por_id[f], lista.index(por_id[f]) + 1, por_id[f] is s) for f in s['familia'])
        familia = f'''          <section class="sd-side__block" aria-labelledby="familia-titulo">
            <h2 class="sd-side__title" id="familia-titulo">Linha evolutiva</h2>
            <ol class="sd-family">
{itens}
            </ol>
          </section>'''
    todos = '\n'.join(mini(x, i + 1, x is s) for i, x in enumerate(lista))
    fx = (fichas or {}).get(s['id'])
    detalhes = ficha_html(s, fx, fichas or {}) or SOON
    # tipo logo na ficha do topo (é a informação mais procurada)
    tipo_fato = ''
    if fx and fx.get('tipos'):
        tipo_fato = (f'          <div>\n            <dt>Tipo</dt>\n            <dd><ul class="types types--sm">'
                     f'{"".join(tipo_li(t) for t in fx["tipos"])}</ul></dd>\n          </div>\n')
    breadcrumb = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': f'{SITE_URL}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Starians', 'item': f'{SITE_URL}/#starians'},
            {'@type': 'ListItem', 'position': 3, 'name': s['nome'], 'item': url},
        ],
    }, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<!-- Página gerada por tools/build.py a partir de tools/data/starians.json. Edite os dados lá, não aqui. -->
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(s["seo"])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(s["seo"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{arte_abs}">
<meta property="og:image:alt" content="Arte do Starian {esc(s["nome"])}">
<!-- @head -->
<!-- /@head -->
<script type="application/ld+json">
{breadcrumb}
</script>
</head>
<body data-page="">
<!-- @header -->
<!-- /@header -->

<main id="conteudo" tabindex="-1">
  <article class="section" aria-labelledby="starian-nome">
    <div class="container">
      <nav class="crumbs" aria-label="Você está em">
        <ol>
          <li><a href="/">Início</a></li>
          <li><a href="/#starians">Starians</a></li>
          <li aria-current="page">{esc(s["nome"])}</li>
        </ol>
      </nav>

      <div class="sd-hero">
        <div class="sd-art tile tile--{s["cor"]}">
          <figure class="starian__art">
            <img src="/{s["arte"]["src"]}" width="{s["arte"]["w"]}" height="{s["arte"]["h"]}" alt="Arte oficial do Starian {esc(s["nome"])}" fetchpriority="high" decoding="async">
          </figure>
          <!-- sprites do jogo: faixa compacta no rodapé do card da arte -->
          <section class="sd-art__sprites" aria-labelledby="sprites-titulo">
            <p class="sd-art__label" id="sprites-titulo">Sprites no jogo</p>
            <ul class="sd-sprites">
{sprites}
            </ul>
          </section>
        </div>

        <!-- nome e resumo: no celular vêm antes da arte (logo abaixo do breadcrumb); no computador, à direita dela -->
        <div class="sd-intro">
          <p class="eyebrow"><img class="px" src="/img/px/museu.webp" width="16" height="16" alt="">Starian Dex · #{numero:03d}</p>
          <h1 class="pixel-title sd-name" id="starian-nome">{esc(s["nome"])}</h1>
          <ul class="badges sd-badges" aria-label="Categorias">
{badges(s["tags"])}
          </ul>
          <p class="sd-lead">{esc(s["resumo"])}</p>
          <p class="sd-text">{esc(s["texto"])}</p>
        </div>

        <div class="sd-info">
          <dl class="sd-facts tile tile--{s["cor"]}">
{tipo_fato}{ficha}
          </dl>{compra}
{familia}
        </div>
      </div>
{detalhes}
      <nav class="sd-pager" aria-label="Outros Starians">
        <a class="btn btn--ghost btn--sm" href="/starians/{anterior["id"]}" rel="prev"><svg aria-hidden="true" style="transform:scaleX(-1)"><use href="#i-arrow"/></svg>{esc(anterior["nome"])}</a>
        <a class="btn btn--ghost btn--sm" href="/starians/{proximo["id"]}" rel="next">{esc(proximo["nome"])}<svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </nav>

      <section class="sd-block" aria-labelledby="todos-titulo">
        <h2 class="subhead" id="todos-titulo">Todos os Starians</h2>
        <ul class="sd-strip" data-carousel aria-label="Todos os Starians">
{todos}
        </ul>
      </section>
    </div>
  </article>
</main>

<!-- @footer -->
<!-- /@footer -->
<!-- @scripts -->
<!-- /@scripts -->
</body>
</html>
'''


def build_starians():
    dados = json.loads((TOOLS / 'data' / 'starians.json').read_text(encoding='utf-8'))
    lista = dados['starians']
    arq = TOOLS / 'data' / 'fichas.json'   # gerado por tools/importar_starianbuilder.py
    fichas = json.loads(arq.read_text(encoding='utf-8')) if arq.exists() else {}
    for s in lista:
        write_if_changed(SITE / 'starians' / s['id'] / 'index.html', starian_page(s, lista, fichas))
    print(f'  {len(lista)} páginas de Starian geradas')


# ══════════════════════════════════════════════════════════════════════════
# 2. Blocos comuns
# ══════════════════════════════════════════════════════════════════════════
def load_blocks():
    out = {}
    for name in BLOCKS:
        text = (TOOLS / 'layout' / f'{name}.html').read_text(encoding='utf-8').replace('{{v}}', VERSION)
        out[name] = text.rstrip('\n')
    return out


def sync_page(path, blocks):
    text = path.read_text(encoding='utf-8')
    page = re.search(r'<body[^>]*\sdata-page="([^"]*)"', text)
    page = page.group(1) if page else ''
    for name, content in blocks.items():
        if name == 'header':
            content = content.replace('aria-current="page" ', '')
            content = re.sub(rf'(data-nav="{re.escape(page)}")', r'\1 aria-current="page"', content) if page else content
        pattern = re.compile(rf'(<!-- @{name} -->)(.*?)(<!-- /@{name} -->)', re.S)
        if not pattern.search(text):
            raise SystemExit(f'ERRO: {path.name} não tem o marcador <!-- @{name} -->')
        text = pattern.sub(lambda m: f'{m.group(1)}\n{content}\n{m.group(3)}', text)
    write_if_changed(path, text)


# ══════════════════════════════════════════════════════════════════════════
# 3. Sitemap
# ══════════════════════════════════════════════════════════════════════════
def build_sitemap(pages):
    urls = []
    for p in pages:
        text = p.read_text(encoding='utf-8')
        if re.search(r'<meta name="robots" content="[^"]*noindex', text):
            continue
        canonical = re.search(r'<link rel="canonical" href="([^"]+)"', text)
        if not canonical:
            raise SystemExit(f'ERRO: {p.name} não tem canonical')
        lastmod = datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()   # data da última mudança real
        urls.append((canonical.group(1), lastmod))
    urls.sort(key=lambda u: (u[0] != f'{SITE_URL}/', u[0]))
    body = '\n'.join(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n  </url>' for u, d in urls)
    write_if_changed(SITE / 'sitemap.xml',
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{body}\n</urlset>\n')
    print(f'  sitemap.xml com {len(urls)} URLs')


if __name__ == '__main__':
    print('Stars Pixelmon · build')
    build_starians()
    blocks = load_blocks()
    pages = site_pages()
    for p in pages:
        sync_page(p, blocks)
    print(f'  blocos comuns aplicados em {len(pages)} páginas')
    build_sitemap(pages)
    print('ok')
