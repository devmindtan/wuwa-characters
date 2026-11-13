"""Combo tab data (scripts/build_combos.py): step parsing and the kit lines a step activates."""
import json
import re

import pytest

from build_combos import parse_step, title_vi
from conftest import ROOT
from kit_rules import INPUT_LINE, kind_trigger, negated


@pytest.fixture(scope='module')
def combos():
    return json.loads((ROOT / 'data' / 'combos.json').read_text(encoding='utf-8'))


def line_of(c, target, li):
    if target == 'weapon':
        return c['signature_weapon']['passive'][li]
    kind, n = target.split('-')
    if kind == 'skill':
        return c['skills'][int(n)]['desc'][li]
    return next(x for x in c['resonance_chain'] if x['node'] == int(n))['desc'][li]


@pytest.mark.parametrize('raw, label, kind, name, stage', [
    ('Basic 3 (Interrupt on first hit via Dash)', 'Basic 3', 'basic', '', 3),
    ('Basic: Movement of Fate and Finality (Cancel animation on cast via Skill)', 'Basic: Movement of Fate and Finality', 'basic', 'Movement of Fate and Finality', None),
    ('Heavy: Scarlet Coda (Cancel animation endlag via Ultimate)', 'Heavy: Scarlet Coda', 'heavy', 'Scarlet Coda', None),
    ('Hold Ultimate: Blade Liberation', 'Hold Ultimate: Blade Liberation', 'lib', 'Blade Liberation', None),
    ('Incarnation Basic P2', 'Incarnation: Basic P2', 'basic', '', 2),   # a move inside a named state
    ('Dash', 'Dash', 'move', '', None),
])
def test_parse_step(raw, label, kind, name, stage):
    st = parse_step(raw)
    assert (st['label'], st['kind'], st['name'], st['stage']) == (label, kind, name, stage)


def test_conditional_step_keeps_its_condition():
    st = parse_step('If on Moonlit Clouds: Echo')
    assert st['kind'] == 'echo' and st['cond'] == 'If on Moonlit Clouds'


def test_trigger_rules():
    echo = kind_trigger('echo')
    assert echo.search('Within 12s after dealing Echo Skill DMG, gain 32% Resonance Skill DMG Bonus')
    assert not echo.search('Echo Skill DMG is Amplified by 80%.')  # a buff, not "casting an Echo"
    basic3 = kind_trigger('basic', 3)
    assert basic3.search('When performing Basic Attack Stage 3, enter Reincarnate state.')
    assert not basic3.search('command Hecate to cast Basic Attack - Hecate')  # a named move, not Basic 3
    assert negated('switch to Phrolova without casting Intro Skill.', 'intro')
    assert INPUT_LINE.match('Press Normal Attack shortly after casting this skill to cast Basic Attack Stage 3.')


def test_title_vi():
    assert title_vi('Opener Rotation') == 'Combo mở đầu'
    assert title_vi('S0R1: Loop') == 'Combo S0R1 vòng lặp'
    assert title_vi('4 DEATH MESSENGER COMBO (DIFFICULTY = IMPOSSIBLE)') == ''  # untranslatable: keep EN


def test_phrolova_echo_step_activates_kit_chain_and_weapon(characters, combos):
    c = next(x for x in characters if x['slug'] == 'phrolova')
    loop = next(r for r in combos['phrolova']['rotations'] if r['title'] == 'Loop Rotation')
    echo = next(s for s in loop['steps'] if s['kind'] == 'echo')
    lines = [line_of(c, t, li) for t, li in echo['refs']]
    assert any(l.startswith('Casting Echo Skill grants increased resistance') for l in lines)  # Inherent Accidental
    assert any(t.startswith('chain-4') for t, _ in echo['refs'])  # S4
    assert any(t == 'weapon' for t, _ in echo['refs'])  # Lethean Elegy: after dealing Echo Skill DMG


def test_every_reference_resolves(characters, combos):
    by = {c['slug']: c for c in characters}
    for slug, data in combos.items():
        c = by[slug]
        for ref in data['triggers'] + [r for rot in data['rotations'] for st in rot['steps'] for r in st['refs']]:
            line = line_of(c, *ref)
            assert line and not INPUT_LINE.match(line), (slug, ref)


def test_most_resonators_have_combos(combos):
    with_rot = [s for s, d in combos.items() if d['rotations']]
    assert len(with_rot) >= 55
    for d in combos.values():
        for rot in d['rotations']:
            if rot['title_vi']:
                assert not re.search(r'\bRotation\b', rot['title_vi'])
