"""Translation quality gate.

Run after every translation/normalisation pass:
    python scripts/review.py
    python scripts/review.py --sample 12

Exits with code 1 when blocking issues are found. Manual context review is
still required: read the flagged lines and a random sample.
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from glossary import BANNED  # noqa: E402

DATA = ROOT / 'data' / 'characters.json'
MECHANICS = ROOT / 'data' / 'mechanics.json'
VOWELS = ''

errors = []
warnings = []
stats = {'characters': 0, 'skills': 0, 'vi_lines': 0}


def err(where, message):
    errors.append((where, message))


def warn(where, message):
    warnings.append((where, message))


def has_vietnamese(text):
    return any('\u00c0' <= ch <= '\u1ef9' for ch in text)


def is_label(line):
    stripped = line.lstrip('• ').strip()
    if len(stripped) < 4:
        return True
    if stripped.endswith(':'):
        return True
    # short headings / names such as "Resonance Mode - Tune Rupture"
    if len(stripped) < 60 and not re.search(r'[.!?]$', stripped):
        return True
    if stripped.count(' - ') >= 2:
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=0, help='print N random VI lines for manual review')
    args = parser.parse_args()

    payload = json.loads(DATA.read_text(encoding='utf-8'))
    meta = payload.get('meta', {})
    if not meta.get('patch'):
        err('meta', 'missing meta.patch')
    if not meta.get('updated'):
        err('meta', 'missing meta.updated')

    mechanics = {m['term'] for m in json.loads(MECHANICS.read_text(encoding='utf-8'))['mechanics']}
    sample_pool = []

    for c in payload.get('characters', []):
        stats['characters'] += 1
        where = c.get('slug', '?')
        for key in ('slug', 'name', 'element', 'weapon', 'img_icon', 'img_card', 'img_full'):
            if not c.get(key):
                err(where, f'missing {key}')
        if not c.get('version'):
            err(where, 'missing version')
        if not c.get('changes'):
            err(where, 'missing changes[]')
        else:
            for ch in c['changes']:
                if not all(k in ch for k in ('version', 'date', 'note')):
                    err(where, 'change entry missing version/date/note')
        if c.get('intro_vi') and any(b in c['intro_vi'] for b in BANNED):
            err(where, 'banned phrase in intro_vi')

        skills = c.get('skills') or []
        if not skills:
            err(where, 'no skills')
        seen = set()
        for s in skills:
            stats['skills'] += 1
            label = f"{where}/{s.get('type','?')}/{s.get('name','?')}"
            key = (s.get('type'), s.get('name'))
            if key in seen:
                err(label, 'duplicate skill (type,name)')
            seen.add(key)
            if not s.get('type') or not s.get('name'):
                err(label, 'missing type or name')
            for field in ('desc', 'desc_vi'):
                if not s.get(field):
                    err(label, f'empty {field}')
            for line in s.get('desc_vi') or []:
                stats['vi_lines'] += 1
                sample_pool.append((label, line))
                if re.search(r'\[\[\d+\]\]', line):
                    err(label, 'unreplaced placeholder token')
                if re.search(r'<[a-zA-Z/][^>]*>', line):
                    err(label, 'raw HTML markup')
                if '  ' in line:
                    warn(label, 'double space')
                if re.search(r'\s+[.,;:!?]', line):
                    warn(label, 'space before punctuation')
                for phrase in BANNED:
                    if phrase in line:
                        err(label, f'banned phrase: {phrase!r}')
                stripped = line.lstrip('• ').strip()
                if len(stripped) >= 60 and not has_vietnamese(stripped):
                    ascii_ratio = sum(1 for ch in stripped if ord(ch) < 128) / max(len(stripped), 1)
                    if ascii_ratio > 0.96 and not is_label(stripped):
                        err(label, 'long line without Vietnamese text (possible untranslated)')

    print(f"Reviewed {stats['characters']} characters, {stats['skills']} skills, {stats['vi_lines']} VI lines.")
    if warnings:
        print(f'\nWarnings ({len(warnings)}):')
        for where, message in warnings[:20]:
            print(f'  - {where}: {message}')
        if len(warnings) > 20:
            print(f'  ... {len(warnings) - 20} more')
    if errors:
        print(f'\nBlocking issues ({len(errors)}):')
        for where, message in errors[:40]:
            print(f'  - {where}: {message}')
        if len(errors) > 40:
            print(f'  ... {len(errors) - 40} more')
        print('\nFAIL: fix the issues above and re-run review.')
        sys.exit(1)

    print('\nPASS: glossary/version/schema checks clean.')
    if args.sample:
        print(f'\nManual context sample ({args.sample} lines):')
        for label, line in random.sample(sample_pool, min(args.sample, len(sample_pool))):
            print(f'  [{label}] {line[:240]}')
        print('\nRead these lines for meaning, not just terminology.')


if __name__ == '__main__':
    main()
