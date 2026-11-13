"""Fetch Resonance Chain + material costs from the Wuthering Waves Fandom wiki.

Uses the public MediaWiki API (https://wutheringwaves.fandom.com/api.php),
politely (sequential requests, short pause), and caches every response in
data/wiki_raw.json (gitignored) so reruns only fetch what is missing.

Usage:
    python scripts/fetch_wiki.py            # fetch missing pages, write cache
    python scripts/fetch_wiki.py --refresh  # ignore cache, refetch everything

Then run scripts/merge_wiki.py to write the results into data/characters.json.
"""

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
CACHE = ROOT / 'data' / 'wiki_raw.json'
API = 'https://wutheringwaves.fandom.com/api.php'
UA = {'User-Agent': 'wuwa-characters-archive/1.0 (fan archive; MediaWiki API)'}
PAUSE = 0.4

# Our character name -> wiki page title, where they differ.
TITLES = {
    'Rover (Aero)': 'Rover-Aero',
    'Rover (Electro)': 'Rover-Electro',
    'Rover (Havoc)': 'Rover-Havoc',
    'Rover (Spectro)': 'Rover-Spectro',
    'Yangyang (Xuanling)': 'Yangyang: Xuanling',
    'The Shorekeeper': 'Shorekeeper',
}
# Rover forms share one ascension cost, listed on the common "Rover" page.
ASCENSION_FROM = {f'Rover ({e})': 'Rover' for e in ('Aero', 'Electro', 'Havoc', 'Spectro')}


def api(**params):
    params.setdefault('format', 'json')
    url = API + '?' + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                out = json.load(r)
            time.sleep(PAUSE)
            return out
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)


def page_html(title):
    d = api(action='parse', page=title, prop='text', redirects=1)
    if 'error' in d:
        return None
    return d['parse']['text']['*']


def text(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def parse_nodes(page):
    """Node 1..6 titles from the Resonance Chain navbox, in order."""
    nodes = {}
    for m in re.finditer(r'<small>Node (\d)</small>.*?<a href="/wiki/[^"]+" title="([^"]+)"', page, re.S):
        nodes.setdefault(int(m.group(1)), html.unescape(m.group(2)))
    return [nodes[i] for i in sorted(nodes)]


CARD = re.compile(
    r'<div class="card-container">.*?card-rarity-(\d).*?data-image-key="([^"]+)".*?'
    r'<span class="card-text card-font">\s*([\d,.]+)\s*</span>.*?'
    r'<span class="card-caption">\s*(.*?)</span>', re.S)


def parse_costs(page):
    """Every 'Total Cost (label)' block -> list of items."""
    blocks = []
    parts = re.split(r'<b>Total Cost</b>', page)
    for part in parts[1:]:
        label = text(re.match(r'\s*\(([^)]*)\)', part).group(1)) if re.match(r'\s*\(', part) else ''
        # A block ends where the next heading starts.
        body = re.split(r'<h[234]', part)[0]
        items = []
        for rarity, key, qty, cap in CARD.findall(body):
            items.append({'name': text(cap), 'qty': int(qty.replace(',', '').replace('.', '')),
                          'rarity': int(rarity), 'image_key': urllib.parse.unquote(html.unescape(key))})
        if items:
            blocks.append({'label': label, 'items': items})
    return blocks


SKILL_HEAD = re.compile(
    r'<tr><td>(?:(?!</tr>).)*?</td><td><a href="/wiki/[^"]+" title="[^"]+">([^<]+)</a></td>'
    r'<td><a href="/wiki/[^"]+" title="[^"]+">([^<]+)</a></td></tr>', re.S)


def cell_text(s):
    s = re.sub(r'<br\s*/?>', ' ', s)
    return text(s)


def parse_scaling(page):
    """Forte Table on <Resonator>/Combat -> [{name, type, rows[{label, values}]}]."""
    start = page.find('id="Details"')
    end = page.find('id="Skill_Costs"')
    if start < 0:
        return []
    seg = page[start:end if end > start else None]
    heads = list(SKILL_HEAD.finditer(seg))
    skills = []
    for i, h in enumerate(heads):
        body = seg[h.end(): heads[i + 1].start() if i + 1 < len(heads) else None]
        rows = []
        for tr in re.findall(r'<tr><th>(.*?)</th>(.*?)</tr>', body, re.S):
            label = text(tr[0])
            cells = [cell_text(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', tr[1], re.S)]
            if label and cells:
                rows.append({'label': label, 'values': cells})
        skills.append({'name': html.unescape(h.group(1)).strip(), 'type': html.unescape(h.group(2)).strip(), 'rows': rows})
    return skills


COST_SECTIONS = [('forte', 'Main_Forte'), ('inherent', 'Inherent_Skills'), ('stat_bonus', 'Stat_Bonuses')]


def parse_level_costs(page):
    """Per-level upgrade tables under "Skill Costs" -> {forte, inherent, stat_bonus}: [{level, ascension, items}].

    The tables follow each other on the page; rows restart at "1 → 2" for each
    table. Forte is the first 9-row group, Inherent and Stat Bonus are the last
    two 2-row groups (some pages repeat the Forte table per form).
    """
    i = page.find('id="Skill_Costs"')
    if i < 0:
        i = page.find('id="Main_Forte"')
    j = page.find('id="Resonance_Chain"', i)
    if i < 0:
        return {}
    seg = page[i:j if j > i else None]
    groups = []
    for tr in re.split(r'<tr', seg)[1:]:
        tr = tr.split('</tr>', 1)[0]
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        if len(tds) < 3 or '→' not in text(tds[0]):
            continue
        level = text(tds[0])
        items = []
        for rarity, k, qty, cap in CARD.findall(tr):
            name = re.sub(r'\s*\[[^\]]*\]\s*$', '', text(cap))
            items.append({'name': name, 'qty': int(qty.replace(',', '').replace('.', '')),
                          'rarity': int(rarity), 'image_key': urllib.parse.unquote(html.unescape(k))})
        if level.startswith('1 →') or not groups:
            groups.append([])
        groups[-1].append({'level': level, 'ascension': text(tds[1]), 'items': items})
    out = {}
    forte = next((g for g in groups if len(g) == 9), None)
    if forte:
        out['forte'] = forte
    small = [g for g in groups if len(g) == 2]
    if len(small) >= 2:
        out['inherent'], out['stat_bonus'] = small[-2], small[-1]
    return out


SCALING_PARAM = re.compile(r'^\s*\|\s*([^=|\n]+?)\s*=\s*(.*?)\s*$', re.M)


def parse_skill_scaling(src):
    """{{Skill Scaling}} wikitext -> {resonator, rows[{label, values}]} (values: 10 levels or 1 constant)."""
    m = re.search(r'\{\{Skill Scaling(.*?)\n\}\}', src, re.S)
    resonator = infobox(src, 'resonator')
    image = infobox(src, 'image').split('\n')[0].strip()
    if not m:
        return {'resonator': resonator, 'image': image, 'rows': []}
    params = dict(SCALING_PARAM.findall(m.group(1)))
    order = [x.strip() for x in params.get('order', '').split(',') if x.strip()]
    titles = [x.strip() for x in params.get('titles', '').split(',')]
    rows = []
    for idx, key in enumerate(order):
        raw = params.get(key, '').strip()
        if raw:
            values = [v.strip() for v in raw.split(';')]
        else:  # per-level form: key_1 ... key_10
            values = [params[f'{key}_{n}'].strip() for n in range(1, 11) if params.get(f'{key}_{n}', '').strip()]
            if not values:
                continue
        label = titles[idx] if idx < len(titles) else key
        rows.append({'label': label, 'values': values})
    return {'resonator': resonator, 'image': image, 'rows': rows}


def wikitext(titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = api(action='query', prop='revisions', rvprop='content', rvslots='main',
                titles='|'.join(titles[i:i + 50]), redirects=1)['query']
        back = {r['to']: r['from'] for r in d.get('redirects', []) + d.get('normalized', [])}
        for p in d['pages'].values():
            if 'revisions' in p:
                t = p['title']
                out[back.get(t, t)] = p['revisions'][0]['slots']['main']['*']
    return out


def image_urls(files):
    out = {}
    for i in range(0, len(files), 50):
        d = api(action='query', prop='imageinfo', iiprop='url',
                titles='|'.join('File:' + f for f in files[i:i + 50]))['query']
        back = {r['to']: r['from'] for r in d.get('normalized', [])}
        for p in d['pages'].values():
            if p.get('imageinfo'):
                t = back.get(p['title'], p['title'])
                out[t.split(':', 1)[1]] = p['imageinfo'][0]['url']
    return out


def infobox(src, field):
    m = re.search(r'^\s*\|\s*' + field + r'\s*=\s*(.*?)(?=^\s*\||^\}\})', src, re.S | re.M)
    return m.group(1).strip() if m else ''


# Wiki resonator name in weapon infobox -> our character name.
WIKI_TO_OUR = {
    'Rover-Aero': 'Rover (Aero)',
    'Rover-Electro': 'Rover (Electro)',
    'Rover-Havoc': 'Rover (Havoc)',
    'Rover-Spectro': 'Rover (Spectro)',
    'Shorekeeper': 'The Shorekeeper',
    'Yangyang: Xuanling': 'Yangyang (Xuanling)',
}


def fetch_signature_weapons(cache, our_names):
    """5★ signature weapons (weapon infobox |resonator=...) -> cache['signature_weapons']."""
    sig = cache.setdefault('signature_weapons', {})
    if sig:
        return sig
    titles = []
    cont = {}
    while True:
        d = api(action='query', list='categorymembers', cmtitle='Category:Weapons', cmlimit=500, **cont)
        for m in d['query']['categorymembers']:
            if m['ns'] == 0:
                titles.append(m['title'])
        if 'continue' in d:
            cont = {'cmcontinue': d['continue']['cmcontinue']}
        else:
            break
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = api(action='query', prop='revisions', rvprop='content', rvslots='main',
                titles='|'.join(batch), formatversion=2)
        for page in d['query']['pages']:
            revs = page.get('revisions')
            if not revs:
                continue
            wt = revs[0]['slots']['main']['content']
            if not re.search(r'^\|rarity\s*=\s*5', wt, re.M):
                continue
            m = re.search(r'^\|resonator\s*=\s*(.+)$', wt, re.M)
            if not m:
                continue
            res = re.sub(r'\[\[|\]\]', '', m.group(1)).strip()
            res = WIKI_TO_OUR.get(res, res)
            if not res or res.startswith('{{') or res.lower() in ('none', 'n/a', '') or res not in our_names:
                continue

            def field(name):
                return infobox(wt, name)
            effect = field('effect')
            for k in range(1, 9):
                v = field(f'eff_rank1_var{k}')
                if v:
                    effect = effect.replace(f'(var{k})%', v).replace(f'(var{k})', v)
            effect = re.sub(r'<br\s*/?>', '\n', effect)
            effect = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', effect)
            effect = re.sub(r'\[\[([^\]]+)\]\]', r'\1', effect)
            effect = re.sub(r'\{\{[^}]+\}\}', '', effect).strip()
            sig[res] = {
                'name': field('name') or page['title'],
                'type': field('type'),
                'rarity': 5,
                'stat_type': field('2nd_stat_type'),
                'rank_name': field('rank_name'),
                'effect': effect,
                'image_key': field('image').split('\n')[0].strip(),
                'source': f"https://wutheringwaves.fandom.com/wiki/{page['title'].replace(' ', '_')}",
            }
    return sig



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true')
    args = ap.parse_args()
    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text(encoding='utf-8'))
    chars = cache.setdefault('characters', {})
    names = [c['name'] for c in json.loads(DATA.read_text(encoding='utf-8'))['characters']]

    for name in names:
        if name in chars and chars[name].get('nodes'):
            continue
        title = TITLES.get(name, name)
        entry = {'title': title, 'nodes': [], 'costs': [], 'pages': []}
        for t in (title, title + '/Combat'):
            page = page_html(t)
            if not page:
                continue
            nodes, costs = parse_nodes(page), parse_costs(page)
            if nodes or costs:
                entry['pages'].append(t)
            entry['nodes'] = entry['nodes'] or nodes
            entry['costs'] = entry['costs'] or costs
            if entry['nodes'] and entry['costs']:
                break
        if name in ASCENSION_FROM and not any('✦' in b['label'] for b in entry['costs']):
            shared = [b for b in parse_costs(page_html(ASCENSION_FROM[name]) or '') if '✦' in b['label']]
            if shared:
                entry['costs'] = shared[:1] + entry['costs']
                entry['pages'].append(ASCENSION_FROM[name])
        chars[name] = entry
        print(f"{name:24} nodes={len(entry['nodes'])} cost blocks={len(entry['costs'])} pages={entry['pages']}", flush=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')

    combat = cache.setdefault('combat', {})
    for name in names:
        if combat.get(name, {}).get('level_costs'):
            continue
        title = chars[name]['title']
        used = title + '/Combat'
        costs = parse_level_costs(page_html(used) or '')
        if not costs and name in ASCENSION_FROM:  # Rover forms share one table
            used = ASCENSION_FROM[name] + '/Combat'
            costs = parse_level_costs(page_html(used) or '')
        combat[name] = {'page': used, 'level_costs': costs}
        print(f"{name:24} level costs={ {k: len(v) for k, v in combat[name]['level_costs'].items()} }", flush=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')

    # Per-skill Lv1-10 scaling from each skill page's {{Skill Scaling}}.
    scaling = cache.setdefault('scaling', {})
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    skill_names = sorted({s['name'] for c in payload['characters'] for s in c['skills']} - set(scaling))
    for title, src in wikitext(skill_names).items():
        scaling[title] = parse_skill_scaling(src)
    print('skill pages:', len(scaling), 'not found:', len(set(skill_names) - set(scaling)))
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')

    node_src = cache.setdefault('nodes', {})
    want = sorted({n for c in chars.values() for n in c['nodes']} - set(node_src))
    for title, src in wikitext(want).items():
        node_src[title] = {
            'description': infobox(src, 'description'),
            'level': infobox(src, 'level'),
            'resonator': infobox(src, 'resonator'),
            'image': infobox(src, 'image'),
        }
    print('node pages:', len(node_src), 'missing:', sorted(set(want) - set(node_src)))

    sig = fetch_signature_weapons(cache, set(names))
    print('signature weapons:', len(sig))
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')

    images = cache.setdefault('images', {})
    files = {n['image'] for n in node_src.values() if n['image']}
    files |= {s['image'] for s in scaling.values() if s.get('image')}
    files |= {i['image_key'].replace('_', ' ') for c in chars.values() for b in c['costs'] for i in b['items']}
    files |= {i['image_key'].replace('_', ' ') for c in combat.values() for rows in c['level_costs'].values()
              for r in rows for i in r['items']}
    files |= {w['image_key'].replace('_', ' ') for w in sig.values() if w.get('image_key')}
    need = sorted(files - set(images))
    images.update(image_urls(need))
    print('images:', len(images), 'missing:', sorted(files - set(images))[:10])
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
