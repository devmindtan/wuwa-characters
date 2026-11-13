"""Build data/kit_index.json: everything the UI derives from the kit text.

- chars[slug].moves:  named sub-moves -> {kind, index, line, title} (the defining line)
- chars[slug].traits: kit trait key -> evidence [{target, title, lineIndex}]
- mech_users[term]:   Resonators whose kit mentions the mechanic, with role labels
- rules:              trait/role keys in display order with the keywords each rule looks for

Run after build_mechanics.py (it needs data/mechanics.json). Rules live in kit_rules.py.
"""

import json
from pathlib import Path

import kit_rules

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
MECH = ROOT / 'data' / 'mechanics.json'
OUT = ROOT / 'data' / 'kit_index.json'


def build(chars, mech):
    mechanics, no_link = mech['mechanics'], mech['no_link']
    names = {n for m in mechanics for n in [m['term'], *(m.get('aliases') or [])]} | set(no_link)
    return {
        'rules': {
            'traits': [{'key': k, 'kw': kw} for k, _rule, kw in kit_rules.TRAIT_RULES],
            'roles': [{'key': k, 'kw': kw} for k, _rx, kw in kit_rules.ROLE_RULES],
        },
        'chars': {c['slug']: {'moves': kit_rules.moves_of(c, names), 'traits': kit_rules.traits_of(c)} for c in chars},
        'mech_users': {m['term']: kit_rules.mechanic_users(m, chars, no_link) for m in mechanics},
    }


def main():
    chars = json.loads(DATA.read_text(encoding='utf-8'))['characters']
    mech = json.loads(MECH.read_text(encoding='utf-8'))
    index = build(chars, mech)
    OUT.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    moves = sum(len(v['moves']) for v in index['chars'].values())
    traits = sum(len(v['traits']) for v in index['chars'].values())
    print(f'wrote {OUT}: {moves} moves, {traits} trait tags, {len(index["mech_users"])} mechanics')


if __name__ == '__main__':
    main()
