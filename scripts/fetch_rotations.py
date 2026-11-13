"""Fetch the "Rotation & How to Play" section of each Resonator's prydwen.gg page.

Only the rotation section is kept (cached in data/rotations_raw.json, gitignored):
every heading with its intro paragraph, ordered step list and notes. Requests are
sequential with a pause; a page that answers with an error is skipped, never retried
around a block.

Usage:
    python scripts/fetch_rotations.py            # fetch pages not cached yet
    python scripts/fetch_rotations.py --refresh  # refetch everything
Then run scripts/build_combos.py.
"""

import argparse
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
CACHE = ROOT / 'data' / 'rotations_raw.json'
URL = 'https://www.prydwen.gg/wuthering-waves/characters/{slug}'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) wuwa-characters-archive/1.0', 'Accept-Language': 'en-US,en;q=0.9'}
PAUSE = 1.0


def text(s):
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s).replace('​', '')
    return re.sub(r'\s+', ' ', s).strip()


def rotation_section(page):
    """HTML of the "Rotation" content header (Gameplay and teams) up to the next header."""
    for m in re.finditer(r'<div class="content-header[^"]*">((?:(?!</div>).)*)</div>', page, re.S):
        if text(m.group(1)) == 'Rotation':
            end = page.find('<div class="content-header', m.end())
            return page[m.end():end if end > 0 else None]
    return ''


def parse_section(seg):
    """-> [{title, intro[], steps[], notes[]}]; callouts become notes of the current block."""
    blocks = []
    cur = {'title': '', 'intro': [], 'steps': [], 'notes': []}
    for m in re.finditer(r'<(h[3-6])[^>]*>(.*?)</\1>|<(ul|ol)>(.*?)</\3>|<p[^>]*>(.*?)</p>', seg, re.S):
        if m.group(1):
            title = text(m.group(2))
            if cur['steps'] or cur['intro'] or cur['notes'] or cur['title']:
                blocks.append(cur)
            cur = {'title': title, 'intro': [], 'steps': [], 'notes': []}
        elif m.group(3):
            items = [text(li) for li in re.findall(r'<li[^>]*>(.*?)</li>', m.group(4), re.S)]
            cur['steps'] += [s for s in items if s]
        else:
            p = text(m.group(5))
            if not p or re.search(r'</li>', m.group(0)):
                continue
            if len(p) <= 60 and p.endswith(':') and re.match(r'\s*<(ul|ol)>', seg[m.end():]):
                # "S6 Rotation:" written as a paragraph right above its list
                if cur['steps'] or cur['intro'] or cur['notes'] or cur['title']:
                    blocks.append(cur)
                cur = {'title': p.rstrip(':').strip(), 'intro': [], 'steps': [], 'notes': []}
                continue
            (cur['notes'] if cur['steps'] else cur['intro']).append(p)
    blocks.append(cur)
    return [b for b in blocks if b['title'] or b['steps'] or b['intro']]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true')
    args = ap.parse_args()
    slugs = [c['slug'] for c in json.loads(DATA.read_text(encoding='utf-8'))['characters']]
    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text(encoding='utf-8'))
    for slug in slugs:
        if slug in cache:
            continue
        url = URL.format(slug=slug)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                page = r.read().decode('utf-8', 'ignore')
        except Exception as e:  # blocked or missing: skip, do not work around it
            print(f'{slug:22} skipped ({e})')
            time.sleep(PAUSE)
            continue
        blocks = parse_section(rotation_section(page))
        cache[slug] = {'url': url, 'fetched': time.strftime('%Y-%m-%d'), 'blocks': blocks}
        print(f"{slug:22} blocks={len(blocks)} steps={sum(len(b['steps']) for b in blocks)}", flush=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
        time.sleep(PAUSE)
    print('cached', len(cache), '/', len(slugs))


if __name__ == '__main__':
    main()
