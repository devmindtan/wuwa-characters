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

    images = cache.setdefault('images', {})
    files = {n['image'] for n in node_src.values() if n['image']}
    files |= {i['image_key'].replace('_', ' ') for c in chars.values() for b in c['costs'] for i in b['items']}
    need = sorted(files - set(images))
    images.update(image_urls(need))
    print('images:', len(images), 'missing:', sorted(files - set(images))[:10])
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
