"""Golden cases for data/kit_index.json (scripts/kit_rules.py): each one was a real bug or request."""
import json

import build_index
import kit_rules


def test_kit_index_is_up_to_date(characters):
    mech = json.loads(build_index.MECH.read_text(encoding='utf-8'))
    fresh = build_index.build(characters, mech)
    committed = json.loads(build_index.OUT.read_text(encoding='utf-8'))
    assert fresh == committed, 'data/kit_index.json is stale: run python scripts/build_index.py'


def _index():
    return json.loads(build_index.OUT.read_text(encoding='utf-8'))


def test_sub_moves():
    moves = _index()['chars']
    assert 'Movement of Fate and Finality' in moves['phrolova']['moves']  # "…to cast X" with "and"
    assert any('Hounds Roar' in m for m in moves['calcharo']['moves'])
    assert "Comin' in Hot" in moves['rebecca']['moves']
    for v in moves.values():
        for name in v['moves']:
            assert name.split(' ')[0] not in {'Stage', 'Sprint'} and not name.endswith("'s"), name


def test_traits_with_evidence():
    chars = _index()['chars']
    assert {'heal', 'shield', 'team', 'energy'} <= set(chars['verina']['traits'])
    assert {'heal', 'team', 'revive'} <= set(chars['the-shorekeeper']['traits'])
    assert {'cc', 'echo', 'dmgup'} <= set(chars['phrolova']['traits'])
    for ev in chars['phrolova']['traits']['cc']:
        assert ev['target'].startswith(('skill-', 'chain-')) and isinstance(ev['lineIndex'], int)


def test_trait_false_positives(characters):
    chars = _index()['chars']
    # a line listing every Negative Status is a generic rule, not a kit trait
    assert 'electro_flare' not in chars['cartethyia']['traits']
    assert 'electro_flare' not in chars['rover-aero']['traits']
    # Carlotta's "Fatal Finale" is a move name, not fatal-damage protection
    assert 'revive' not in chars['carlotta']['traits']
    # "Intro Skill - Summon and Smite" is a skill name, not a summon
    by_slug = {c['slug']: c for c in characters}
    for ev in chars['buling']['traits'].get('summon', []):
        kind, idx = ev['target'].split('-')
        src = by_slug['buling']['skills'][int(idx)] if kind == 'skill' else next(
            n for n in by_slug['buling']['resonance_chain'] if n['node'] == int(idx))
        assert 'Summon and Smite' not in src['desc'][ev['lineIndex']] or 'summon' in src['desc'][ev['lineIndex']].replace('Summon and Smite', '').lower()


def test_dmgup_rules():
    rule = dict((k, r) for k, r, _ in kit_rules.TRAIT_RULES)['dmgup']
    assert rule('Casting this skill increases the DMG of Basic Attack by 30%.')
    assert not rule('Deal fixed Spectro DMG, considered Basic Attack DMG that is not affected by any DMG Bonus.')
    assert not rule('After a Resonator in the team deals Tune Break DMG, all Resonators in the team deal 20% more DMG for 20s.')


def test_mechanic_users_respect_no_link_and_owners():
    users = _index()['mech_users']
    unison = {u['slug'] for u in users['Unison']}
    assert {'hsin', 'suoming'} <= unison
    assert [u['slug'] for u in users['Manifest']] == ['cartethyia']
    assert all(set(u['roles']) <= {'apply', 'stack', 'amplify', 'use', 'restore'} for v in users.values() for u in v)
