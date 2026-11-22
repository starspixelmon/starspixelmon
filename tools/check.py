"""
Stars Pixelmon · verificação do site (Python 3 + Pillow)

    python tools/check.py

Confere, em todas as páginas do site (os .html da raiz do projeto):
  - links e imagens apontam para arquivos/âncoras que existem (inclusive entre páginas)
  - nenhuma imagem PNG fora os favicons; width/height batem com a proporção real do arquivo
  - um único <h1> e nenhum nível de título pulado (h2 -> h4)
  - <title> até 60 caracteres e description até 155 (páginas indexáveis)
  - canonical absoluto, og:url igual ao canonical, og:image absoluto
  - JSON-LD válido
  - sitemap.xml lista exatamente as páginas indexáveis
  - tags HTML abertas e fechadas corretamente
Sai com código 1 se encontrar problemas.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

SITE = Path(__file__).resolve().parent.parent   # o site fica na raiz do projeto
DOMAIN = 'https://starspixelmon.com.br'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
OPTIONAL_END = {'p', 'li', 'dt', 'dd', 'option'}
problems = []


def err(page, msg):
    problems.append(f'{page}: {msg}')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.ids, self.refs, self.imgs, self.heads = [], set(), [], [], []
        self.meta, self.links, self.jsonld, self._ld, self.title, self._t = {}, {}, [], None, '', False
        self.balance = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        for k in ('href', 'src', 'data-fallback'):
            if a.get(k) is not None:
                self.refs.append((tag, k, a[k]))
        if tag == 'img':
            self.imgs.append(a)
        if re.fullmatch(r'h[1-6]', tag):
            self.heads.append(int(tag[1]))
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key:
                self.meta[key] = a.get('content', '')
        if tag == 'link' and a.get('rel'):
            self.links[a['rel']] = a.get('href', '')
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self._ld = ''
        if tag == 'title':
            self._t = True
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == 'title':
            self._t = False
        if tag == 'script' and self._ld is not None:
            self.jsonld.append(self._ld)
            self._ld = None
        while self.stack and self.stack[-1][0] != tag and self.stack[-1][0] in OPTIONAL_END:
            self.stack.pop()
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.balance.append(f'</{tag}> sem abertura (linha {self.getpos()[0]})')

    def handle_data(self, data):
        if self._ld is not None:
            self._ld += data
        if self._t:
            self.title += data


pages = sorted(SITE.glob('*.html'))
parsed = {}
for p in pages:
    pg = Page()
    pg.feed(p.read_text(encoding='utf-8'))
    parsed[p.name] = pg

indexable = []
for name, pg in parsed.items():
    noindex = 'noindex' in pg.meta.get('robots', '')
    base_root = name == '404.html'   # usa <base href="/">
    for tag, attr, v in pg.refs:
        if v.startswith(('http://', 'https://', 'mailto:', 'data:')) or v.startswith('#i-'):
            continue
        if v.startswith('#'):
            if v[1:] and v[1:] not in pg.ids:
                err(name, f'âncora inexistente {v}')
            continue
        path, _, frag = v.partition('#')
        path = path.split('?')[0]
        if not path:
            continue
        target = SITE / path.lstrip('/')
        if not target.exists():
            err(name, f'arquivo inexistente {v}')
            continue
        if frag and target.suffix == '.html' and frag not in parsed[target.name].ids:
            err(name, f'âncora inexistente em {v}')
        if target.suffix == '.png' and 'favicon' not in target.name:
            err(name, f'imagem PNG {v}')
    for img in pg.imgs:
        src = img.get('src', '')
        if src.startswith('data:'):
            continue
        f = SITE / src
        if not img.get('width') or not img.get('height'):
            err(name, f'img sem width/height {src}')
        elif Image and f.exists():
            w, h = Image.open(f).size
            if abs(int(img['width']) / int(img['height']) - w / h) > 0.02:
                err(name, f'proporção errada {src}: {img["width"]}x{img["height"]} vs {w}x{h}')
        for part in filter(None, (x.strip() for x in img.get('srcset', '').split(','))):
            url, _, desc = part.partition(' ')
            g = SITE / url
            if not g.exists():
                err(name, f'srcset inexistente {url}')
            elif Image and desc.endswith('w') and Image.open(g).size[0] != int(desc[:-1]):
                err(name, f'srcset {url}: descritor {desc} difere da largura real')
        if img.get('srcset') and not img.get('sizes'):
            err(name, f'srcset sem sizes {src}')
        if 'alt' not in img:
            err(name, f'img sem alt {src}')
    if pg.heads.count(1) != 1:
        err(name, f'{pg.heads.count(1)} <h1>')
    for a, b in zip(pg.heads, pg.heads[1:]):
        if b > a + 1:
            err(name, f'título pulado h{a} -> h{b}')
    for block in pg.jsonld:
        try:
            json.loads(block)
        except ValueError as e:
            err(name, f'JSON-LD inválido: {e}')
    for b in pg.balance:
        err(name, b)
    if pg.stack:
        err(name, f'tags não fechadas: {pg.stack[-3:]}')
    if not noindex:
        indexable.append(pg.links.get('canonical', ''))
        t, d = pg.title.strip(), pg.meta.get('description', '')
        if len(t) > 60:
            err(name, f'title com {len(t)} caracteres')
        if not 50 <= len(d) <= 155:
            err(name, f'description com {len(d)} caracteres')
        c = pg.links.get('canonical', '')
        if not c.startswith(DOMAIN):
            err(name, 'canonical ausente ou relativo')
        if pg.meta.get('og:url') != c:
            err(name, 'og:url diferente do canonical')
        if not pg.meta.get('og:image', '').startswith(DOMAIN):
            err(name, 'og:image ausente ou relativo')
        for ld in pg.jsonld:
            for u in re.findall(r'"(https://starspixelmon\.com\.br/[^"#]+)"', ld):
                if not (SITE / u.replace(DOMAIN + '/', '')).exists():
                    err(name, f'JSON-LD aponta para arquivo inexistente {u}')

sitemap = set(re.findall(r'<loc>([^<]+)</loc>', (SITE / 'sitemap.xml').read_text(encoding='utf-8')))
if sitemap != set(indexable):
    err('sitemap.xml', f'diferença: {sorted(sitemap ^ set(indexable))}')
for u in sitemap:
    f = SITE / (u.replace(DOMAIN + '/', '') or 'index.html')
    if not f.exists():
        err('sitemap.xml', f'URL sem arquivo {u}')

for f in (SITE / 'img').rglob('*.png'):   # só as imagens do site (assets/ e bases/ têm PNG de propósito)
    if 'favicon' not in f.name:
        err('img', f'PNG restante {f.relative_to(SITE)}')

for css in (SITE / 'css').glob('*.css'):
    for u in re.findall(r'url\(["\']?([^"\')]+)', css.read_text(encoding='utf-8')):
        if not u.startswith(('data:', 'http', '#')) and not (css.parent / u).exists():
            err(css.name, f'url() inexistente {u}')

print(f'{len(pages)} páginas, {len(indexable)} indexáveis')
print('\n'.join(problems) if problems else 'Nenhum problema encontrado.')
sys.exit(1 if problems else 0)
