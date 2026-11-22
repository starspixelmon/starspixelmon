"""
Stars Pixelmon · manutenção do site (Python 3, sem dependências)

    python tools/build.py

O que faz, nesta ordem:
  1. Gera uma página por Starian (starian-<id>.html, na raiz) a partir de tools/data/starians.json.
  2. Copia os blocos comuns de tools/layout/ para TODAS as páginas .html da raiz, entre os marcadores:
        <!-- @head --> ... <!-- /@head -->         (ícones, fontes, CSS)
        <!-- @header --> ... <!-- /@header -->     (céu, cabeçalho e menu)
        <!-- @footer --> ... <!-- /@footer -->     (rodapé)
        <!-- @scripts --> ... <!-- /@scripts -->   (JS)
     O link do menu da página atual recebe aria-current="page" (vem de <body data-page="...">).
  3. Refaz sitemap.xml com todas as páginas que não têm "noindex".

As páginas continuam HTML puro: abrem direto do arquivo, sem servidor. Rode o build depois de mudar
qualquer coisa em tools/layout/ ou tools/data/. Ao mudar CSS ou JS, suba VERSION para o navegador
não usar a versão antiga do cache.
"""
import datetime
import html
import json
import re
from pathlib import Path

SITE_URL = 'https://starspixelmon.com.br'   # domínio oficial (canonical, sitemap, Open Graph)
VERSION = '40'                                # suba ao alterar css/style.css ou js/*.js

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT                                   # o site fica na raiz do projeto (pronto para GitHub Pages)
TOOLS = ROOT / 'tools'
BLOCKS = ('head', 'header', 'footer', 'scripts')
def write_if_changed(path, text):
    """grava só se o conteúdo mudou: preserva a data do arquivo, que vira o lastmod do sitemap"""
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
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
        f'        <li><a class="sd-mini tile tile--{s["cor"]}{estado}" href="starian-{s["id"]}.html"{current}>'
        f'<img class="px" src="{s["sprites"][0][1]}" {size_attrs(s["sprites"][0][1])} alt="">'
        f'<span><small>#{numero:03d}</small>{esc(s["nome"])}</span></a></li>'
    )


def starian_page(s, lista):
    pos = lista.index(s)
    numero = pos + 1
    por_id = {x['id']: x for x in lista}
    anterior = lista[pos - 1]
    proximo = lista[(pos + 1) % len(lista)]
    url = f'{SITE_URL}/starian-{s["id"]}.html'
    titulo = f'{s["nome"]}: Starian #{numero:03d} | Stars Pixelmon'
    arte_abs = f'{SITE_URL}/{s["arte"]["src"]}'

    ficha = '\n'.join(
        f'          <div>\n            <dt>{esc(k)}</dt>\n            <dd>{esc(v)}</dd>\n          </div>' for k, v in s['ficha']
    )
    def cor_sprite(rotulo):
        return 'gold' if rotulo == 'Shiny' else (s['cor'] if rotulo == 'Normal' else 'ember')
    sprites = '\n'.join(
        f'        <li>\n          <figure class="sd-sprite tile tile--{cor_sprite(r)}">\n'
        f'            <img class="px" src="{src}" {size_attrs(src)} alt="Sprite {esc(r.lower())} de {esc(s["nome"])}" loading="lazy" decoding="async">\n'
        f'            <figcaption>{esc(r)}</figcaption>\n          </figure>\n        </li>'
        for r, src in s['sprites']
    )
    compra = ''
    if s.get('compra'):
        c = s['compra']
        compra = f'''
        <p class="btn-row">
          <a class="btn btn--play" href="index.html#loja" data-loja="{c["loja"]}">
            <svg aria-hidden="true"><use href="#i-cart"/></svg>{esc(c["rotulo"])}
          </a>
        </p>'''
    familia = ''
    if s.get('familia'):
        itens = '\n'.join(mini(por_id[f], lista.index(por_id[f]) + 1, por_id[f] is s) for f in s['familia'])
        familia = f'''
    <section class="sd-block" aria-labelledby="familia-titulo">
      <h2 class="subhead" id="familia-titulo">Família inicial</h2>
      <ol class="sd-family">
{itens}
      </ol>
    </section>
'''
    todos = '\n'.join(mini(x, i + 1, x is s) for i, x in enumerate(lista))
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
          <li><a href="index.html">Início</a></li>
          <li><a href="index.html#starians">Starians</a></li>
          <li aria-current="page">{esc(s["nome"])}</li>
        </ol>
      </nav>

      <div class="sd-hero">
        <figure class="sd-art tile tile--{s["cor"]}">
          <div class="starian__art">
            <img src="{s["arte"]["src"]}" width="{s["arte"]["w"]}" height="{s["arte"]["h"]}" alt="Arte oficial do Starian {esc(s["nome"])}" fetchpriority="high" decoding="async">
          </div>
        </figure>

        <div class="sd-info">
          <p class="eyebrow"><img class="px" src="img/px/museu.webp" width="16" height="16" alt="">Starian Dex · #{numero:03d}</p>
          <h1 class="pixel-title sd-name" id="starian-nome">{esc(s["nome"])}</h1>
          <ul class="badges sd-badges" aria-label="Categorias">
{badges(s["tags"])}
          </ul>
          <p class="sd-lead">{esc(s["resumo"])}</p>
          <p class="sd-text">{esc(s["texto"])}</p>
          <dl class="sd-facts tile tile--{s["cor"]}">
{ficha}
          </dl>{compra}
        </div>
      </div>

      <section class="sd-block" aria-labelledby="sprites-titulo">
        <h2 class="subhead" id="sprites-titulo">Sprites no jogo</h2>
        <ul class="sd-sprites">
{sprites}
        </ul>
      </section>
{familia}
      <aside class="highlight tile tile--indigo sd-soon">
        <img class="px highlight__icon" src="img/px/cadeado-aberto.webp" width="16" height="16" alt="">
        <div>
          <h2>Ficha completa em breve</h2>
          <p>Tipo, habilidades, ataques e stats chegam com a Starian Dex completa.</p>
        </div>
      </aside>

      <nav class="sd-pager" aria-label="Outros Starians">
        <a class="btn btn--ghost btn--sm" href="starian-{anterior["id"]}.html" rel="prev"><svg aria-hidden="true" style="transform:scaleX(-1)"><use href="#i-arrow"/></svg>{esc(anterior["nome"])}</a>
        <a class="btn btn--ghost btn--sm" href="starian-{proximo["id"]}.html" rel="next">{esc(proximo["nome"])}<svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </nav>

      <section class="sd-block" aria-labelledby="todos-titulo">
        <h2 class="subhead" id="todos-titulo">Todos os Starians</h2>
        <ul class="sd-strip">
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
    for s in lista:
        write_if_changed(SITE / f'starian-{s["id"]}.html', starian_page(s, lista))
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
    pages = sorted(SITE.glob('*.html'))
    for p in pages:
        sync_page(p, blocks)
    print(f'  blocos comuns aplicados em {len(pages)} páginas')
    build_sitemap(pages)
    print('ok')
