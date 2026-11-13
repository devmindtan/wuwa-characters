"""Stamp public/index.html with a content hash of the CSS/JS (?v=...), so browsers drop old copies.

  python scripts/stamp_assets.py          # rewrite index.html if the stamp is stale
  python scripts/stamp_assets.py --check  # exit 1 if stale (used by the pre-commit hook and tests)
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'public'
INDEX = PUBLIC / 'index.html'
STAMPED = re.compile(r'((?:href|src)="(?:styles\.css|js/main\.js))\?v=[^"]*"')


def asset_hash():
    h = hashlib.sha256()
    for f in [PUBLIC / 'styles.css', *sorted((PUBLIC / 'js').glob('*.js'))]:
        h.update(f.relative_to(PUBLIC).as_posix().encode() + b'\0' + f.read_bytes())
    return h.hexdigest()[:10]


def stamped(html, v):
    return STAMPED.sub(lambda m: f'{m.group(1)}?v={v}"', html)


def main():
    html = INDEX.read_text(encoding='utf-8')
    assert len(STAMPED.findall(html)) == 2, 'index.html must load styles.css?v= and js/main.js?v='
    new = stamped(html, asset_hash())
    if new == html:
        print('index.html stamp is current')
        return 0
    if '--check' in sys.argv:
        print('✗ public/index.html: ?v= cũ, chạy python scripts/stamp_assets.py rồi stage lại index.html')
        return 1
    INDEX.write_text(new, encoding='utf-8')
    print(f'stamped index.html with v={asset_hash()}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
