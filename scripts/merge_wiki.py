"""Merge cached wiki data (data/wiki_raw.json) into data/characters.json.

Adds per character:
  resonance_chain  [{node, name, desc[], desc_vi[], img}]   (S1..S6)
  materials        {ascension, forte, inherent, stat_bonus} -> {label, items[{name, qty, rarity, img}]}
  references       [{title, url, used_for}]
  signature_weapon {name, type, stat_type, rank_name, passive[] ({N} placeholders), passive_vi[],
                    ranks{N: [R1..R5]}, description[], description_vi[], stats[], ascension[], img}

Vietnamese lines come from data/translations/resonance_chain_vi.json, keyed by
node name and only applied when the stored English text still matches.

Usage:
    python scripts/fetch_wiki.py && python scripts/merge_wiki.py
    python scripts/merge_wiki.py --export-missing out.json   # EN lines still needing VI
    python scripts/merge_wiki.py --export-missing-weapons out.json  # weapon effect/description needing VI
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikitext import clean  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
CACHE = ROOT / 'data' / 'wiki_raw.json'
VI = ROOT / 'data' / 'translations' / 'resonance_chain_vi.json'
WEAPON_VI = ROOT / 'data' / 'translations' / 'weapons_vi.json'
WIKI = 'https://wutheringwaves.fandom.com/wiki/'

COST_KEYS = [
    ('ascension', lambda label: '✦' in label),
    ('forte', lambda label: 'Main Forte' in label),
    ('inherent', lambda label: 'Inherent' in label),
    ('stat_bonus', lambda label: 'Stat Bonus' in label),
]


def wiki_url(title):
    return WIKI + title.replace(' ', '_')


def thumb(url, width=96):
    if not url:
        return ''
    return url.replace('/revision/latest', f'/revision/latest/scale-to-width-down/{width}', 1)


def lines_of(src):
    # Wiki uses "- item" lines for lists; the archive renders "• item" as <li>.
    return ['• ' + l[2:].strip() if l.startswith('- ') else l for l in clean(src)]


VAR = re.compile(r'\(var(\d)\)')


def weapon_lines(src):
    """Weapon effect wikitext -> lines; "(varN)" becomes the placeholder "{N}"."""
    return [VAR.sub(r'{\1}', l) for l in lines_of(src)]


def weapon_of(sw, images, wvi, missing):
    """Cached wiki weapon -> the archive's signature_weapon object.

    passive: EN effect lines with {N} placeholders, ranks: {N: [R1..R5]}; the UI fills the
    placeholders for the chosen rank. Vietnamese comes from weapons_vi.json and is
    only used while its stored English still matches.
    """
    effect = weapon_lines(sw.get('effect_src', ''))
    # The wiki writes either "(var1)%" with "12" or "(var1)" with "12%": store bare
    # numbers and keep the "%" in the text, so "{1}%" always renders as "12%".
    ranks = {}
    for n, vals in sw.get('ranks', {}).items():
        ranks[n] = [v.strip().rstrip('%') for v in vals]
        if any(v.strip().endswith('%') for v in vals):
            effect = [re.sub(r'\{' + n + r'\}(?!%)', '{' + n + '}%', line) for line in effect]
    desc = lines_of(sw.get('description_src', ''))
    tr = wvi.get(sw['name'], {})
    ok_eff = tr.get('effect_en') == effect and len(tr.get('effect', [])) == len(effect)
    ok_desc = tr.get('description_en') == desc and len(tr.get('description', [])) == len(desc)
    if not (ok_eff and ok_desc):
        missing[sw['name']] = {'effect_en': effect, 'description_en': desc,
                               'effect': tr.get('effect', []) if ok_eff else [],
                               'description': tr.get('description', []) if ok_desc else []}
    img = lambda key: thumb(images.get(key.replace('_', ' '), ''), 80)
    return {
        'name': sw['name'],
        'type': sw.get('type', ''),
        'rarity': sw.get('rarity', 5),
        'stat_type': sw.get('stat_type', ''),
        'rank_name': sw.get('rank_name', ''),
        'passive': effect,
        'passive_vi': tr['effect'] if ok_eff else [],
        'ranks': ranks,
        'description': desc,
        'description_vi': tr['description'] if ok_desc else [],
        'stats': sw.get('stats', []),
        'ascension': [{'label': st['label'], 'items': [
            {'name': it['name'], 'qty': it['qty'], 'rarity': it['rarity'], 'img': img(it['image_key'])}
            for it in st['items']]} for st in sw.get('ascension', [])],
        'img': thumb(images.get(sw.get('image_key', '').replace('_', ' '), ''), 128),
        'source': sw.get('source', ''),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--export-missing', metavar='FILE')
    ap.add_argument('--export-missing-weapons', metavar='FILE',
                    help='signature weapons whose VI effect/description is missing or outdated')
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding='utf-8'))
    raw = json.loads(CACHE.read_text(encoding='utf-8'))
    vi = json.loads(VI.read_text(encoding='utf-8')) if VI.exists() else {}
    wvi = json.loads(WEAPON_VI.read_text(encoding='utf-8')) if WEAPON_VI.exists() else {}
    missing_w = {}
    images = raw['images']
    missing = {}

    for c in payload['characters']:
        w = raw['characters'].get(c['name'])
        if not w:
            print('no wiki data for', c['name'])
            continue

        chain = []
        for i, title in enumerate(w['nodes'], 1):
            node = raw['nodes'].get(title, {})
            desc = lines_of(node.get('description', ''))
            tr = vi.get(title)
            ok = tr and tr.get('en') == desc and len(tr.get('vi', [])) == len(desc)
            if not ok:
                missing[title] = {'resonator': c['name'], 'node': i, 'en': desc}
            chain.append({
                'node': i,
                'name': title,
                'desc': desc,
                'desc_vi': tr['vi'] if ok else [],
                'img': thumb(images.get(node.get('image', ''), '')),
            })
        c['resonance_chain'] = chain

        materials = {}
        for block in w['costs']:
            for key, match in COST_KEYS:
                if key not in materials and match(block['label']):
                    materials[key] = {
                        'label': block['label'],
                        'items': [{
                            'name': it['name'],
                            'qty': it['qty'],
                            'rarity': it['rarity'],
                            'img': thumb(images.get(it['image_key'].replace('_', ' '), ''), 80),
                        } for it in block['items']],
                    }
        c['materials'] = materials

        # Lv1-10 multipliers per skill, only from a skill page of this resonator.
        owner = w['title'].split('-')[0]  # "Rover-Aero" -> "Rover"
        for sk in c['skills']:
            sc = raw.get('scaling', {}).get(sk['name'])
            same = sc and (not sc['resonator'] or sc['resonator'] in (w['title'], owner))
            if same and sc['rows']:
                sk['scaling'] = {'rows': sc['rows'], 'source': wiki_url(sk['name'])}
            else:
                sk.pop('scaling', None)
            icon = thumb(images.get(sc.get('image', ''), ''), 96) if same else ''
            if icon:
                sk['icon'] = icon
            else:
                sk.pop('icon', None)

        level_costs = {}
        combat = raw.get('combat', {}).get(c['name'], {})
        for key, rows in combat.get('level_costs', {}).items():
            level_costs[key] = [{
                'level': r['level'],
                'ascension': r['ascension'],
                'items': [{'name': it['name'], 'qty': it['qty'], 'rarity': it['rarity'],
                           'img': thumb(images.get(it['image_key'].replace('_', ' '), ''), 80)} for it in r['items']],
            } for r in rows]
        c['level_costs'] = level_costs

        sw = raw.get('signature_weapons', {}).get(c['name'])
        c['signature_weapon'] = weapon_of(sw, images, wvi, missing_w) if sw else None

        refs = [{'title': f"prydwen.gg — {c['name']}", 'url': c['source'],
                 'used_for': 'Kỹ năng, mô tả nhân vật, hình ảnh',
                 'used_for_en': 'Skills, character description, images'}]
        main_page = w['pages'][0] if w['pages'] else w['title']
        shared = [p for p in w['pages'] if p == 'Rover']
        uses, uses_en = [], []
        if chain:
            uses.append('Resonance Chain'); uses_en.append('Resonance Chain')
        if materials:
            uses.append('nguyên liệu nâng kỹ năng' if shared else 'nguyên liệu')
            uses_en.append('skill upgrade materials' if shared else 'materials')
        refs.append({'title': f'Wuthering Waves Wiki — {main_page}', 'url': wiki_url(main_page),
                     'used_for': ', '.join(uses), 'used_for_en': ', '.join(uses_en)})
        if combat.get('page') and (level_costs or any('scaling' in sk for sk in c['skills'])):
            refs.append({'title': f"Wuthering Waves Wiki — {combat['page']}", 'url': wiki_url(combat['page']),
                         'used_for': 'hệ số kỹ năng Lv1–10 (Attribute Scaling, xem thêm trang từng kỹ năng), '
                                     'chi phí nâng cấp theo từng cấp',
                         'used_for_en': 'skill multipliers Lv1–10 (Attribute Scaling, see each skill page), '
                                        'per-level upgrade costs'})
        for page in shared:
            refs.append({'title': f'Wuthering Waves Wiki — {page}', 'url': wiki_url(page),
                         'used_for': 'nguyên liệu đột phá (dùng chung cho mọi dạng Rover)',
                         'used_for_en': 'ascension materials (shared by every Rover form)'})
        if sw:
            refs.append({'title': f"Wuthering Waves Wiki — {sw['name']}", 'url': sw['source'],
                         'used_for': 'vũ khí trấn phái',
                         'used_for_en': 'signature weapon'})
        c['references'] = refs

    payload['meta']['updated'] = datetime.date.today().isoformat()
    payload['meta']['wiki_source'] = 'https://wutheringwaves.fandom.com/'
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')

    chars = payload['characters']
    print(f"chain nodes: {sum(len(c.get('resonance_chain', [])) for c in chars)}, "
          f"translated: {sum(1 for c in chars for n in c.get('resonance_chain', []) if n['desc_vi'])}, "
          f"missing VI: {len(missing)}")
    print('no chain:', [c['name'] for c in chars if not c.get('resonance_chain')])
    print('skills with scaling:', sum(1 for c in chars for s in c['skills'] if 'scaling' in s), '/',
          sum(len(c['skills']) for c in chars))
    print('no level costs:', [c['name'] for c in chars if not c.get('level_costs')])
    print('incomplete materials:', [c['name'] for c in chars if len(c.get('materials', {})) < 4])
    if args.export_missing:
        Path(args.export_missing).write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding='utf-8')
        print('exported', len(missing), 'nodes to', args.export_missing)
    print('signature weapons:', sum(1 for c in chars if c.get('signature_weapon')), 'missing VI:', len(missing_w))
    if args.export_missing_weapons:
        Path(args.export_missing_weapons).write_text(json.dumps(missing_w, ensure_ascii=False, indent=1), encoding='utf-8')
        print('exported', len(missing_w), 'weapons to', args.export_missing_weapons)


if __name__ == '__main__':
    main()
