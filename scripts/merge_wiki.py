"""Merge cached wiki data (data/wiki_raw.json) into data/characters.json.

Adds per character:
  resonance_chain  [{node, name, desc[], desc_vi[], img}]   (S1..S6)
  materials        {ascension, forte, inherent, stat_bonus} -> {label, items[{name, qty, rarity, img}]}
  references       [{title, url, used_for}]

Vietnamese lines come from data/translations/resonance_chain_vi.json, keyed by
node name and only applied when the stored English text still matches.

Usage:
    python scripts/fetch_wiki.py && python scripts/merge_wiki.py
    python scripts/merge_wiki.py --export-missing out.json   # EN lines still needing VI
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikitext import clean  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
CACHE = ROOT / 'data' / 'wiki_raw.json'
VI = ROOT / 'data' / 'translations' / 'resonance_chain_vi.json'
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--export-missing', metavar='FILE')
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding='utf-8'))
    raw = json.loads(CACHE.read_text(encoding='utf-8'))
    vi = json.loads(VI.read_text(encoding='utf-8')) if VI.exists() else {}
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

        refs = [{'title': f"prydwen.gg — {c['name']}", 'url': c['source'],
                 'used_for': 'Kỹ năng, mô tả nhân vật, hình ảnh'}]
        main_page = w['pages'][0] if w['pages'] else w['title']
        shared = [p for p in w['pages'] if p == 'Rover']
        uses = []
        if chain:
            uses.append('Resonance Chain')
        if materials:
            uses.append('nguyên liệu nâng kỹ năng' if shared else 'nguyên liệu')
        refs.append({'title': f'Wuthering Waves Wiki — {main_page}', 'url': wiki_url(main_page),
                     'used_for': ', '.join(uses)})
        for page in shared:
            refs.append({'title': f'Wuthering Waves Wiki — {page}', 'url': wiki_url(page),
                         'used_for': 'nguyên liệu đột phá (dùng chung cho mọi dạng Rover)'})
        c['references'] = refs

    payload['meta']['updated'] = datetime.date.today().isoformat()
    payload['meta']['wiki_source'] = 'https://wutheringwaves.fandom.com/'
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')

    chars = payload['characters']
    print(f"chain nodes: {sum(len(c.get('resonance_chain', [])) for c in chars)}, "
          f"translated: {sum(1 for c in chars for n in c.get('resonance_chain', []) if n['desc_vi'])}, "
          f"missing VI: {len(missing)}")
    print('no chain:', [c['name'] for c in chars if not c.get('resonance_chain')])
    print('incomplete materials:', [c['name'] for c in chars if len(c.get('materials', {})) < 4])
    if args.export_missing:
        Path(args.export_missing).write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding='utf-8')
        print('exported', len(missing), 'nodes to', args.export_missing)


if __name__ == '__main__':
    main()
