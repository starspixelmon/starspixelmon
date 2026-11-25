"""
Stars Pixelmon · importa a ficha completa dos Starians do StarianBuilder (Python 3, sem dependências)

    python tools/importar_starianbuilder.py

Lê os projetos do StarianBuilder (pasta starianbuilder/, fora do Git: tem o executável, backups e arquivos
do jogo) e grava tools/data/fichas.json, só com o que a página de cada Starian mostra.
Rode de novo sempre que um Starian mudar no StarianBuilder, e depois rode tools/build.py.

Só entram os Starians que já estão no site (tools/data/starians.json): os que ainda não foram lançados
continuam fora, para não vazar nada.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / 'starianbuilder' / 'projects'
OUT = ROOT / 'tools' / 'data' / 'fichas.json'

TIPOS = {
    'NORMAL': 'Normal', 'FIRE': 'Fogo', 'WATER': 'Água', 'GRASS': 'Planta', 'ELECTRIC': 'Elétrico', 'ICE': 'Gelo',
    'FIGHTING': 'Lutador', 'POISON': 'Venenoso', 'GROUND': 'Terrestre', 'FLYING': 'Voador', 'PSYCHIC': 'Psíquico',
    'BUG': 'Inseto', 'ROCK': 'Pedra', 'GHOST': 'Fantasma', 'DRAGON': 'Dragão', 'DARK': 'Sombrio', 'STEEL': 'Aço',
    'FAIRY': 'Fada',
}
CATEGORIAS = {'PHYSICAL': 'Físico', 'SPECIAL': 'Especial', 'STATUS': 'Status'}
GRUPOS_OVO = {
    'UNDISCOVERED': 'Não cruza', 'MONSTER': 'Monstro', 'FAIRY': 'Fada', 'AMORPHOUS': 'Amorfo', 'GRASS': 'Planta',
    'DRAGON': 'Dragão', 'MINERAL': 'Mineral', 'HUMAN_LIKE': 'Humanoide', 'FIELD': 'Campo', 'FLYING': 'Voador',
    'WATER_1': 'Água 1', 'WATER_2': 'Água 2', 'WATER_3': 'Água 3', 'BUG': 'Inseto', 'DITTO': 'Ditto',
}
CRESCIMENTO = {
    'FAST': 'Rápido', 'MEDIUM_FAST': 'Médio-rápido', 'MEDIUM_SLOW': 'Médio-lento', 'SLOW': 'Lento',
    'ERRATIC': 'Errático', 'FLUCTUATING': 'Flutuante',
}
ATRIBUTOS = [('hp', 'HP'), ('attack', 'Atk'), ('defense', 'Def'), ('special_attack', 'SpA'),
             ('special_defense', 'SpD'), ('speed', 'Spe')]
SIGLAS = {'hp': 'HP', 'attack': 'Atk', 'defense': 'Def', 'special_attack': 'SpA', 'special_defense': 'SpD', 'speed': 'Spe',
          'atk': 'Atk', 'def': 'Def', 'spa': 'SpA', 'spd': 'SpD', 'spe': 'Spe'}
# natureza: (sobe, desce)
NATUREZAS = {
    'LONELY': ('Atk', 'Def'), 'BRAVE': ('Atk', 'Spe'), 'ADAMANT': ('Atk', 'SpA'), 'NAUGHTY': ('Atk', 'SpD'),
    'BOLD': ('Def', 'Atk'), 'RELAXED': ('Def', 'Spe'), 'IMPISH': ('Def', 'SpA'), 'LAX': ('Def', 'SpD'),
    'TIMID': ('Spe', 'Atk'), 'HASTY': ('Spe', 'Def'), 'JOLLY': ('Spe', 'SpA'), 'NAIVE': ('Spe', 'SpD'),
    'MODEST': ('SpA', 'Atk'), 'MILD': ('SpA', 'Def'), 'QUIET': ('SpA', 'Spe'), 'RASH': ('SpA', 'SpD'),
    'CALM': ('SpD', 'Atk'), 'GENTLE': ('SpD', 'Def'), 'SASSY': ('SpD', 'Spe'), 'CAREFUL': ('SpD', 'SpA'),
}
LOCAIS = {'Land': 'no chão', 'Manmade': 'em construções', 'Underground': 'no subterrâneo', 'Water': 'na água',
          'Air': 'no ar', 'Seafloor': 'no fundo do mar', 'Lava': 'na lava'}
# grupos de biomas do Pixelmon (#pixelmon:spawning/...): o texto vem depois de "Biomas"
GRUPOS_BIOMA = {
    'all_forests': 'de Florestas', 'flowery': 'Floridos', 'mesas': 'de Mesas',
    'freezing': 'Congelados', 'oceanic': 'Oceânicos', 'mountainous_forests': 'de Florestas Montanhosas',
    'freezing_mountains': 'de Montanhas Congeladas', 'mushroom': 'de Cogumelos', 'end': 'do End',
    'hellish': 'do Nether', 'flat_freezing': 'Planos Congelados', 'freezing_land': 'de Terra Congelada',
    'plains': 'de Planícies', 'deserts': 'de Deserto', 'jungles': 'de Selva', 'swamps': 'de Pântano',
    'beaches': 'de Praia', 'rivers': 'de Rio', 'taigas': 'de Taiga', 'savannas': 'de Savana',
    'mountains': 'de Montanhas', 'caves': 'de Cavernas', 'oceans': 'Oceânicos', 'nether': 'do Nether',
}
# biomas individuais do Minecraft (minecraft:...)
BIOMAS_MC = {
    'plains': 'Planície', 'sunflower_plains': 'Planície de Girassóis', 'forest': 'Floresta',
    'flower_forest': 'Floresta Florida', 'birch_forest': 'Floresta de Bétulas', 'dark_forest': 'Floresta Escura',
    'taiga': 'Taiga', 'snowy_taiga': 'Taiga Nevada', 'jungle': 'Selva', 'bamboo_jungle': 'Selva de Bambu',
    'desert': 'Deserto', 'savanna': 'Savana', 'badlands': 'Mesa', 'swamp': 'Pântano',
    'mangrove_swamp': 'Pântano de Mangue', 'beach': 'Praia', 'river': 'Rio', 'ocean': 'Oceano',
    'deep_ocean': 'Oceano Profundo', 'warm_ocean': 'Oceano Quente', 'frozen_ocean': 'Oceano Congelado',
    'snowy_plains': 'Planície Nevada', 'ice_spikes': 'Picos de Gelo', 'meadow': 'Prado',
    'cherry_grove': 'Bosque de Cerejeiras', 'mushroom_fields': 'Campos de Cogumelos',
    'dripstone_caves': 'Cavernas de Espeleotemas', 'lush_caves': 'Cavernas Exuberantes', 'deep_dark': 'Escuridão Profunda',
    'nether_wastes': 'Devastação do Nether', 'the_end': 'O End',
}
HORARIOS = {'DAY': 'de dia', 'NIGHT': 'à noite', 'DAWN': 'ao amanhecer', 'DUSK': 'ao entardecer'}
CLIMAS = {'CLEAR': 'tempo limpo', 'RAIN': 'chuva', 'STORM': 'tempestade'}
# habilidades padrão usadas pelos Starians (as próprias do Stars vêm com descrição do StarianBuilder)
HABILIDADES = {
    'Blaze': 'Com pouca vida, fortalece os golpes do tipo Fogo.',
    'Intimidate': 'Ao entrar em batalha, reduz o Ataque dos oponentes.',
    'Strong Jaw': 'Fortalece golpes de mordida.',
    'Levitate': 'Flutua: fica imune a golpes do tipo Terrestre.',
    'Magnet Pull': 'Impede que oponentes do tipo Aço fujam ou sejam trocados.',
    'Lightning Rod': 'Atrai golpes elétricos, fica imune a eles e aumenta o SpA.',
    'Harvest': 'Pode recuperar a berry usada ao fim de cada turno.',
    'Natural Cure': 'Cura problemas de status ao sair da batalha.',
    'Magic Guard': 'Só recebe dano de golpes diretos.',
    'Sturdy': 'Com a vida cheia, não é derrotado com um golpe só.',
    'Rock Head': 'Não sofre dano de recuo.',
}


# tabela de tipos (golpe -> defensor: multiplicador; o que não aparece vale 1x)
EFETIVIDADE = {
    'NORMAL': {'ROCK': .5, 'GHOST': 0, 'STEEL': .5},
    'FIRE': {'FIRE': .5, 'WATER': .5, 'GRASS': 2, 'ICE': 2, 'BUG': 2, 'ROCK': .5, 'DRAGON': .5, 'STEEL': 2},
    'WATER': {'FIRE': 2, 'WATER': .5, 'GRASS': .5, 'GROUND': 2, 'ROCK': 2, 'DRAGON': .5},
    'ELECTRIC': {'WATER': 2, 'ELECTRIC': .5, 'GRASS': .5, 'GROUND': 0, 'FLYING': 2, 'DRAGON': .5},
    'GRASS': {'FIRE': .5, 'WATER': 2, 'GRASS': .5, 'POISON': .5, 'GROUND': 2, 'FLYING': .5, 'BUG': .5, 'ROCK': 2, 'DRAGON': .5, 'STEEL': .5},
    'ICE': {'FIRE': .5, 'WATER': .5, 'GRASS': 2, 'ICE': .5, 'GROUND': 2, 'FLYING': 2, 'DRAGON': 2, 'STEEL': .5},
    'FIGHTING': {'NORMAL': 2, 'ICE': 2, 'POISON': .5, 'FLYING': .5, 'PSYCHIC': .5, 'BUG': .5, 'ROCK': 2, 'GHOST': 0, 'DARK': 2, 'STEEL': 2, 'FAIRY': .5},
    'POISON': {'GRASS': 2, 'POISON': .5, 'GROUND': .5, 'ROCK': .5, 'GHOST': .5, 'STEEL': 0, 'FAIRY': 2},
    'GROUND': {'FIRE': 2, 'ELECTRIC': 2, 'GRASS': .5, 'POISON': 2, 'FLYING': 0, 'BUG': .5, 'ROCK': 2, 'STEEL': 2},
    'FLYING': {'ELECTRIC': .5, 'GRASS': 2, 'FIGHTING': 2, 'BUG': 2, 'ROCK': .5, 'STEEL': .5},
    'PSYCHIC': {'FIGHTING': 2, 'POISON': 2, 'PSYCHIC': .5, 'DARK': 0, 'STEEL': .5},
    'BUG': {'FIRE': .5, 'GRASS': 2, 'FIGHTING': .5, 'POISON': .5, 'FLYING': .5, 'PSYCHIC': 2, 'GHOST': .5, 'DARK': 2, 'STEEL': .5, 'FAIRY': .5},
    'ROCK': {'FIRE': 2, 'ICE': 2, 'FIGHTING': .5, 'GROUND': .5, 'FLYING': 2, 'BUG': 2, 'STEEL': .5},
    'GHOST': {'NORMAL': 0, 'PSYCHIC': 2, 'GHOST': 2, 'DARK': .5},
    'DRAGON': {'DRAGON': 2, 'STEEL': .5, 'FAIRY': 0},
    'DARK': {'FIGHTING': .5, 'PSYCHIC': 2, 'GHOST': 2, 'DARK': .5, 'FAIRY': .5},
    'STEEL': {'FIRE': .5, 'WATER': .5, 'ELECTRIC': .5, 'ICE': 2, 'ROCK': 2, 'STEEL': .5, 'FAIRY': 2},
    'FAIRY': {'FIRE': .5, 'FIGHTING': 2, 'POISON': .5, 'DRAGON': 2, 'DARK': 2, 'STEEL': .5},
}
FAIXAS = [(4, 'Muito fraco (4×)'), (2, 'Fraco (2×)'), (.5, 'Resiste (½×)'), (.25, 'Resiste muito (¼×)'), (0, 'Imune (0×)')]


def fraquezas(tipos):
    """agrupa os 18 tipos de golpe pelo dano que causam neste Starian (sem contar habilidades)"""
    grupos = []
    for valor, rotulo in FAIXAS:
        ts = []
        for atk in EFETIVIDADE:
            m = 1
            for d in tipos:
                m *= EFETIVIDADE[atk].get(d, 1)
            if m == valor:
                ts.append({'nome': TIPOS[atk], 'id': atk.lower()})
        if ts:
            grupos.append({'rotulo': rotulo, 'tipos': ts})
    return grupos


def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))


ITENS_HIFEN = {'Heavy Duty Boots': 'Heavy-Duty Boots', 'King S Rock': "King's Rock"}   # grafia oficial


def nome_item(i):
    nome = ' '.join(w.capitalize() for w in (i or '').split(':')[-1].split('_')) if i else ''
    return ITENS_HIFEN.get(nome, nome)


# texto da build no formato de exportação do Showdown (o mesmo que os jogadores colam em outras ferramentas)
SHOWDOWN_EVS = [('hp', 'HP'), ('atk', 'Atk'), ('def', 'Def'), ('spa', 'SpA'), ('spd', 'SpD'), ('spe', 'Spe')]


def com_alt(*valores):
    """junta a opção principal e as alternativas com barra, sem repetir nem deixar vazio: "Psychic / Psyshock" """
    vistos = []
    for v in valores:
        if v and v not in vistos:
            vistos.append(v)
    return ' / '.join(vistos)


def evs_txt(evs, siglas):
    return ' / '.join(f"{evs[k]} {s}" for k, s in siglas if evs.get(k))


def ivs_txt(ivs, siglas):
    return ' / '.join(f"{ivs[k]} {s}" for k, s in siglas if ivs.get(k, 31) != 31)


def golpes_alt(b):
    """cada golpe com as alternativas da mesma linha: "Knock Off / Flamethrower / Toxic" """
    alts = b.get('move_alternatives') or []
    return [com_alt(g, *(alts[i] if i < len(alts) else [])) for i, g in enumerate(b['moves']) if g]


def texto_build(especie, b):
    """build no formato de exportação do Showdown; alternativas separadas por barra"""
    nome = especie
    if b.get('nickname'):
        nome = f"{b['nickname']} ({especie})"
    if b.get('gender') in ('M', 'F', 'MALE', 'FEMALE'):
        nome += f" ({b['gender'][0]})"
    item = com_alt(nome_item(b.get('item')), nome_item(b.get('alternative_item')))
    linhas = [nome + (f' @ {item}' if item else '')]
    hab = com_alt(b.get('ability'), b.get('alternative_ability'))
    if hab:
        linhas.append(f'Ability: {hab}')
    if b.get('level') and b['level'] != 100:
        linhas.append(f"Level: {b['level']}")
    if b.get('shiny'):
        linhas.append('Shiny: Yes')
    if b.get('happiness') not in (None, 255):
        linhas.append(f"Happiness: {b['happiness']}")
    evs = com_alt(evs_txt(b['evs'], SHOWDOWN_EVS), evs_txt(b.get('alternative_evs') or {}, SHOWDOWN_EVS))
    if evs:
        linhas.append(f'EVs: {evs}')
    if b.get('tera_type'):
        linhas.append(f"Tera Type: {b['tera_type'].capitalize()}")
    nat = com_alt((b.get('nature') or '').capitalize(), (b.get('alternative_nature') or '').capitalize())
    if nat:
        linhas.append(f'{nat} Nature')
    ivs = com_alt(ivs_txt(b['ivs'], SHOWDOWN_EVS), ivs_txt(b.get('alternative_ivs') or {}, SHOWDOWN_EVS))
    if ivs:
        linhas.append(f'IVs: {ivs}')
    linhas += [f'- {g}' for g in golpes_alt(b)]
    return '\n'.join(linhas)


def legivel(slug):
    """fallback para o que não está nas tabelas: "birch_forest" → "Birch Forest" """
    return ' '.join(w.capitalize() for w in slug.split('_'))


def biomas_txt(tags):
    """#pixelmon:spawning/x = grupo de biomas ("em Biomas de Florestas");
    minecraft:x = bioma individual ("no bioma Planície", "nos biomas Planície e Savana")"""
    def juntar(itens):
        return itens[0] if len(itens) == 1 else ', '.join(itens[:-1]) + ' e ' + itens[-1]
    grupos, biomas = [], []
    for tag in tags:
        slug = tag.split('/')[-1].split(':')[-1]
        if tag.lstrip('#').startswith('pixelmon:spawning/'):
            grupos.append('Biomas ' + GRUPOS_BIOMA.get(slug, 'de ' + legivel(slug)))
        else:
            biomas.append(BIOMAS_MC.get(slug, legivel(slug)))
    partes = []
    if grupos:
        partes.append(juntar([f'em {g}' for g in sorted(grupos)]))
    if biomas:
        biomas.sort()
        partes.append(('no bioma ' if len(biomas) == 1 else 'nos biomas ') + juntar(biomas))
    return ' e '.join(partes)


def habilidade(nome, custom):
    if not nome:
        return None
    c = custom.get(nome)
    return {'nome': nome, 'propria': bool(c), 'efeito': (c or HABILIDADES.get(nome, ''))}


def main():
    site = ler(ROOT / 'tools' / 'data' / 'starians.json')['starians']
    publicos = {s['nome'].lower(): s['id'] for s in site}
    custom = {}
    for f in (PROJ / 'abilities').glob('*.json'):
        a = ler(f)
        if a.get('description') and not re.fullmatch(r'[A-Za-z]{1,6}', a.get('description', '')):   # ignora testes ("Defg")
            nome = re.sub(r'(?<!^)(?=[A-Z])', ' ', a['effect']['id'].removeprefix('Stars'))
            custom[nome] = a['description']
    por_nome = {}
    for f in sorted((PROJ / 'starians').glob('*.starian.json')):
        d = ler(f)
        por_nome[d['identity']['name']] = d

    fichas = {}
    for nome, d in por_nome.items():
        sid = publicos.get(nome.lower())
        if not sid:
            continue                     # ainda não lançado no site
        t, ab, cap, ovo = d['types'], d['abilities'], d['capture_experience'], d['breeding']
        stats = [{'nome': rot, 'valor': d['base_stats'][k]} for k, rot in ATRIBUTOS]
        evo_para = [{'nome': e['evolves_to'],
                     'como': (f"Nível {e['level']}" if e.get('level') else
                              f"Usar {nome_item(e['item'])}" if e.get('item') else 'Evolução especial')}
                    for e in d['evolution']['evolutions']]
        spawns = []
        for s in d['spawn']['spawn_infos']:
            c = s['condition']
            partes = [', '.join(LOCAIS.get(l, l) for l in s['location_types'])]
            if c.get('biomes'):
                partes.append(biomas_txt(c['biomes']))   # "em Biomas Floridos e em Biomas de Mesas"
            if c.get('times'):
                partes.append(', '.join(HORARIOS.get(h, h) for h in c['times']))
            if c.get('weathers'):
                partes.append('com ' + ', '.join(CLIMAS.get(w, w) for w in c['weathers']))
            if c.get('min_y') is not None or c.get('max_y') is not None:
                partes.append(f"altura Y {c.get('min_y') if c.get('min_y') is not None else '…'} a {c.get('max_y') if c.get('max_y') is not None else '…'}")
            onde = ', '.join(p for p in partes if p)
            spawns.append({'onde': onde[:1].upper() + onde[1:], 'niveis': f"{s['min_level']} a {s['max_level']}"})
        golpe = None
        if d.get('custom_move_enabled') and d.get('custom_move'):
            m = d['custom_move']
            golpe = {'nome': m['name'], 'tipo': TIPOS.get(m['attack_type'], m['attack_type']), 'tipo_id': m['attack_type'].lower(),
                     'categoria': CATEGORIAS.get(m['attack_category'], m['attack_category']),
                     'poder': m['base_power'] or '—', 'precisao': f"{m['accuracy']}%" if m.get('accuracy') else '—',
                     'pp': m['pp_base'], 'descricao': m.get('description', '')}
        ms = d['moveset']
        por_nivel = {}
        tem_pre = bool(d['evolution']['pre_evolutions'])
        for e in ms['level_up_moves']:
            nv = e['level'] if (e['level'] or tem_pre) else 1       # nível 0 sem pré-evolução = já nasce sabendo
            por_nivel.setdefault(nv, []).extend(e['attacks'])
        nivel = [{'nivel': 'Ao evoluir' if nv == 0 else str(nv), 'golpes': sorted(set(g), key=g.index)}
                 for nv, g in sorted(por_nivel.items())]
        tms = sorted({m for k, v in ms.items() if k.startswith(('tm_moves', 'hm_moves')) for m in v})
        builds = []
        for b in d['recommended_movesets']:
            def natureza(n):
                ef = NATUREZAS.get(n or '')
                return f"{n.capitalize()} (+{ef[0]} −{ef[1]})" if ef else (n or '').capitalize()
            builds.append({
                'titulo': b['title'],
                'item': com_alt(nome_item(b.get('item')), nome_item(b.get('alternative_item'))),
                'habilidade': com_alt(b.get('ability'), b.get('alternative_ability')),
                'natureza': com_alt(natureza(b.get('nature')), natureza(b.get('alternative_nature'))),
                'evs': com_alt(evs_txt(b['evs'], [(k, SIGLAS[k]) for k in b['evs']]),
                               evs_txt(b.get('alternative_evs') or {}, [(k, SIGLAS[k]) for k in (b.get('alternative_evs') or {})])),
                'ivs': com_alt(ivs_txt(b['ivs'], [(k, SIGLAS[k]) for k in b['ivs']]),
                               ivs_txt(b.get('alternative_ivs') or {}, [(k, SIGLAS[k]) for k in (b.get('alternative_ivs') or {})])),
                'golpes': golpes_alt(b),
                'texto': texto_build(nome, b),
            })
        fichas[sid] = {
            'pokedex': ((d.get('identity') or {}).get('pokedex_description') or '').strip(),
            # ex.: "Estrela", "Garra Branca"; preposições em minúscula ("Olhos Da Noite" → "Olhos da Noite")
            'categoria': ' '.join(w.lower() if i and w.lower() in ('da', 'de', 'do', 'das', 'dos', 'e') else w
                                  for i, w in enumerate(((d.get('identity') or {}).get('category') or '').split())),
            'tipos': [{'nome': TIPOS[t[k]], 'id': t[k].lower()} for k in ('primary', 'secondary') if t.get(k)],
            'atributos': stats, 'total': sum(s['valor'] for s in stats),
            'fraquezas': fraquezas([t[k] for k in ('primary', 'secondary') if t.get(k)]),
            'habilidades': [h for h in [habilidade(ab['ability_1'], custom) and {**habilidade(ab['ability_1'], custom), 'slot': 'Habilidade'},
                                        habilidade(ab['ability_2'], custom) and {**habilidade(ab['ability_2'], custom), 'slot': 'Habilidade'},
                                        habilidade(ab['hidden_ability'], custom) and {**habilidade(ab['hidden_ability'], custom), 'slot': 'Oculta'}] if h],
            'golpe_exclusivo': golpe,
            'evolui_para': evo_para,
            'spawns': spawns,
            'dados': [
                ['Altura', f"{d['physical']['height']:.2f} m".replace('.', ',')],
                ['Peso', f"{d['physical']['weight']:.1f} kg".replace('.', ',')],
                ['Taxa de captura', str(cap['catch_rate'])],
                ['Crescimento', CRESCIMENTO.get(cap['experience_group'], cap['experience_group'])],
                ['EVs ao derrotar', ', '.join(f"{v} {SIGLAS[k]}" for k, v in d['ev_yield'].items() if v)],
                ['Gênero', 'Sem gênero' if ovo['male_percentage'] is None else f"{ovo['male_percentage']:g}% macho".replace('.', ',')],
                ['Grupo de ovo', ' e '.join(GRUPOS_OVO.get(g, g) for g in (ovo['egg_group_1'], ovo['egg_group_2']) if g)],
                ['Ciclos de ovo', str(ovo['egg_cycles'])],
            ],
            'golpes_nivel': nivel,
            'golpes_ovo': sorted(set(ms.get('egg_moves', []))),
            'golpes_tutor': sorted(set(ms.get('tutor_moves', []))),
            'golpes_tm': tms,
            'builds': builds,
        }
    # ajustes do site por cima do StarianBuilder:
    # a linha do Lumi mostra as mesmas habilidades em todas as fases (as do Lumistar, com a Radiant Mane)
    for sid in ('lumi', 'luminix'):
        if sid in fichas and 'lumistar' in fichas:
            fichas[sid]['habilidades'] = fichas['lumistar']['habilidades']
    OUT.write_text(json.dumps(fichas, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'fichas.json: {", ".join(fichas)} ({len(fichas)} de {len(site)} Starians do site)')


if __name__ == '__main__':
    main()
