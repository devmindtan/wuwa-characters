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
stats = {'characters': 0, 'skills': 0, 'vi_lines': 0, 'chain_nodes': 0}


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
        # changes[] only records in-game info changes; it may be empty.
        if not isinstance(c.get('changes'), list):
            err(where, 'missing changes[] (use [] when nothing changed)')
        else:
            for ch in c['changes']:
                if not all(ch.get(k) for k in ('version', 'date', 'note')):
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
            check_vi_lines(label, s.get('desc_vi') or [], sample_pool)

        chain = c.get('resonance_chain')
        if chain is None:
            err(where, 'missing resonance_chain[] (use [] when the source has none)')
        for n in chain or []:
            stats['chain_nodes'] += 1
            label = f"{where}/S{n.get('node', '?')}/{n.get('name', '?')}"
            if not n.get('name') or not n.get('desc'):
                err(label, 'chain node missing name/desc')
            if len(n.get('desc_vi') or []) != len(n.get('desc') or []):
                err(label, 'chain node desc_vi missing or line count differs from desc')
            for e_line, v_line in zip(n.get('desc') or [], n.get('desc_vi') or []):
                missing = set(re.findall(r'\d+(?:\.\d+)?', e_line)) - set(re.findall(r'\d+(?:\.\d+)?', v_line))
                if missing:
                    err(label, f'numbers lost in translation: {sorted(missing)}')
            check_vi_lines(label, n.get('desc_vi') or [], sample_pool)

        mats = c.get('materials')
        if not isinstance(mats, dict):
            err(where, 'missing materials{}')
        else:
            for key, block in mats.items():
                for it in block.get('items', []):
                    if not it.get('name') or not isinstance(it.get('qty'), int) or it['qty'] <= 0:
                        err(f'{where}/materials/{key}', f'bad item {it}')
        sw = c.get('signature_weapon')
        if sw:
            check_weapon(f"{where}/weapon/{sw.get('name', '?')}", sw, sample_pool)

        if not c.get('references'):
            err(where, 'missing references[]')
        for ref in c.get('references') or []:
            if not str(ref.get('url', '')).startswith('https://'):
                err(where, f'reference without https url: {ref}')

    finish(args, sample_pool)


PLACEHOLDER = re.compile(r'\{(\d)\}')


def check_weapon(label, sw, sample_pool):
    """Signature weapon: R1-R5 values for every placeholder, VI keeps the placeholders and numbers."""
    for key in ('name', 'type', 'stat_type', 'img'):
        if not sw.get(key):
            err(label, f'missing {key}')
    ranks = sw.get('ranks') or {}
    used = {n for line in sw.get('passive') or [] for n in PLACEHOLDER.findall(line)}
    if not sw.get('passive'):
        err(label, 'empty passive')
    for n in used - set(ranks):
        err(label, f'placeholder {{{n}}} has no rank values')
    for n, vals in ranks.items():
        if len(vals) != 5 or not all(re.fullmatch(r'\d+(?:\.\d+)?', v) for v in vals):
            err(label, f'rank values for {{{n}}} must be 5 bare numbers: {vals}')
    for en_key, vi_key in (('passive', 'passive_vi'), ('description', 'description_vi')):
        en, vi = sw.get(en_key) or [], sw.get(vi_key) or []
        if len(en) != len(vi):
            err(label, f'{vi_key} missing or line count differs from {en_key}')
        for e_line, v_line in zip(en, vi):
            if sorted(PLACEHOLDER.findall(e_line)) != sorted(PLACEHOLDER.findall(v_line)):
                err(label, f'{vi_key}: placeholders differ from EN')
            plain = lambda t: set(re.findall(r'\d+(?:\.\d+)?', PLACEHOLDER.sub('', t)))
            if plain(e_line) - plain(v_line):
                err(label, f'{vi_key}: numbers lost in translation: {sorted(plain(e_line) - plain(v_line))}')
        check_vi_lines(label, vi, sample_pool)
    for row in sw.get('stats') or []:
        if not all(row.get(k) for k in ('ascension', 'level', 'atk', 'sub')):
            err(label, f'bad stats row {row}')
    for step in sw.get('ascension') or []:
        for it in step.get('items', []):
            if not it.get('name') or not isinstance(it.get('qty'), int) or it['qty'] <= 0:
                err(f'{label}/ascension', f'bad item {it}')


def check_vi_lines(label, lines, sample_pool):
    for line in lines:
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



def finish(args, sample_pool):
    print(f"Reviewed {stats['characters']} characters, {stats['skills']} skills, "
          f"{stats['chain_nodes']} Resonance Chain nodes, {stats['vi_lines']} VI lines.")
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
