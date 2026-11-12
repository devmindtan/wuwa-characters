"""Apply hand-reviewed Vietnamese re-translations of skill description lines.

data/translations/skill_overrides_vi.json holds lines whose machine translation
had translated in-game proper names (e.g. "Cruelty" -> "Tàn ác"). Each entry is
applied only while the stored English line still matches the data, so a changed
source line is reported instead of silently getting a stale translation.

Usage:
    python scripts/apply_overrides.py
    python scripts/check_names.py      # should report (close to) 0 lines afterwards
"""

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
OVR = ROOT / 'data' / 'translations' / 'skill_overrides_vi.json'


def main() -> None:
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    by_slug = {c['slug']: c for c in payload['characters']}
    applied = unchanged = stale = 0
    for o in json.loads(OVR.read_text(encoding='utf-8')):
        c = by_slug.get(o['slug'])
        skill = next((s for s in (c or {}).get('skills', []) if s['name'] == o['skill']), None)
        if not skill or o['line'] >= len(skill['desc']) or skill['desc'][o['line']] != o['en']:
            stale += 1
            print('stale (English changed):', o['slug'], '/', o['skill'], 'line', o['line'])
            continue
        if skill['desc_vi'][o['line']] == o['vi']:
            unchanged += 1
            continue
        skill['desc_vi'][o['line']] = o['vi']
        applied += 1
    print(f'applied {applied}, already applied {unchanged}, stale {stale}')
    if applied:
        payload['meta']['updated'] = datetime.date.today().isoformat()
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
