"""Download fixed images (icons, character cards) into public/assets/ and point
data/characters.json at the local copies, so the site does not wait on
third-party CDNs.

Localised:
  skills[].icon                -> assets/skills/<name>.<ext>
  resonance_chain[].img        -> assets/chain/<name>.<ext>
  materials / level_costs img  -> assets/items/<name>.<ext>
  img_icon, img_card           -> assets/chars/<slug>_<kind>.<ext>
img_full (large art, ~420 KB each) stays remote on purpose.

Run after scripts/merge_wiki.py (which writes remote wiki URLs):
    python scripts/fetch_assets.py            # download missing files + rewrite paths
    python scripts/fetch_assets.py --check    # only report what is missing
"""

import argparse
import datetime
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
PUBLIC = ROOT / 'public'
UA = {'User-Agent': 'wuwa-characters-archive/1.0 (fan archive; asset mirror)', 'Accept': 'image/webp,image/png,image/*'}
EXT = {'image/webp': '.webp', 'image/png': '.png', 'image/jpeg': '.jpg'}
PAUSE = 0.05


def local_name(url: str, folder: str) -> str:
    """Stable file stem from the remote URL (wiki file name or prydwen file name)."""
    path = urllib.parse.urlparse(url).path
    if '/revision/' in path:  # .../images/a/ab/Skill_Foo.png/revision/latest/...
        path = path.split('/revision/')[0]
    stem = urllib.parse.unquote(path.rsplit('/', 1)[-1]).rsplit('.', 1)[0]
    stem = re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')
    return f'assets/{folder}/{stem}'


def fetch(url: str, rel_stem: str, existing: dict) -> str | None:
    if rel_stem in existing:
        return existing[rel_stem]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                body = r.read()
                ext = EXT.get(r.headers.get_content_type(), '')
            break
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print('  failed:', url, e)
                return None
            time.sleep(1 + attempt)
    if not ext or len(body) < 100:
        print('  not an image:', url)
        return None
    rel = rel_stem + ext
    out = PUBLIC / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(body)
    existing[rel_stem] = rel
    time.sleep(PAUSE)
    return rel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    payload = json.loads(DATA.read_text(encoding='utf-8'))
    existing = {str(p.relative_to(PUBLIC).with_suffix('')): str(p.relative_to(PUBLIC))
                for p in (PUBLIC / 'assets').glob('*/*') if p.suffix in ('.webp', '.png', '.jpg')}

    # (container, key, folder, stem-override)
    targets = []
    for c in payload['characters']:
        for kind in ('icon', 'card'):
            targets.append((c, f'img_{kind}', 'chars', f"assets/chars/{c['slug']}_{kind}"))
        sw = c.get('signature_weapon')
        if sw and sw.get('img'):
            targets.append((sw, 'img', 'weapons', f"assets/weapons/{c['slug']}_sig"))
        for step in (sw or {}).get('ascension', []):
            for it in step['items']:
                if it.get('img'):
                    targets.append((it, 'img', 'items', None))
        for s in c['skills']:
            if s.get('icon'):
                targets.append((s, 'icon', 'skills', None))
        for n in c.get('resonance_chain', []):
            if n.get('img'):
                targets.append((n, 'img', 'chain', None))
        blocks = list(c.get('materials', {}).values())
        blocks += [r for rows in c.get('level_costs', {}).values() for r in rows]
        for b in blocks:
            for it in b['items']:
                if it.get('img'):
                    targets.append((it, 'img', 'items', None))

    remote = [(obj, key, folder, stem) for obj, key, folder, stem in targets if str(obj[key]).startswith('http')]
    print(f'{len(targets)} image fields, {len(remote)} still remote')
    if args.check:
        return

    done = failed = 0
    for obj, key, folder, stem in remote:
        rel = fetch(obj[key], stem or local_name(obj[key], folder), existing)
        if rel:
            obj[key] = rel
            done += 1
        else:
            failed += 1
    print(f'localised {done}, failed {failed}, files on disk {len(existing)}')
    if done:
        payload['meta']['updated'] = datetime.date.today().isoformat()
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')
        print('updated', DATA)


if __name__ == '__main__':
    main()
