"""Combo tab data (scripts/build_combos.py): step parsing and the kit lines a step activates."""
import json
import re

import pytest

from build_combos import parse_step, title_vi
from conftest import ROOT
from kit_rules import INPUT_LINE, kind_trigger, negated, outcomes_of


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


def test_outcomes_are_short_and_grounded():
    assert outcomes_of('When performing Basic Attack Stage 3, enter Reincarnate state.') == [
        ('Vào trạng thái Reincarnate', 'Enter Reincarnate')]
    assert ('+120% ATK', '+120% ATK') in outcomes_of('Gain 120% ATK increase.')
    assert ('+14 Aftersound', '+14 Aftersound') in outcomes_of('Casting Scarlet Coda grants 14 stacks of Aftersound.')
    # negations and timers are not results of the action
    assert outcomes_of("Waltz of Forsaken Depths does not consume Resonance Energy.") == []
    assert outcomes_of('Phrolova enters the Compose state every 25s.') == []
    assert negated('Casting this skill is considered as casting Echo Skill.', 'echo')


def flow_of_rot(combos, slug, title):
    return next(r for r in combos[slug]['rotations'] if r['title'] == title)['flow']


def test_phrolova_loop_reads_as_player_actions(combos):
    flow = flow_of_rot(combos, 'phrolova', 'Loop Rotation')
    says = [a['say_vi'] for a in flow]
    assert says[0].startswith('Đổi vào sân bằng Intro Skill')
    assert 'Đánh thường 3 đòn liên tiếp (đòn 1 → 3)' in says  # Basic 1, 2, 3 merged
    assert not any(a['say_vi'] == 'Lướt (Dash)' for a in flow)  # Dash that only cancels is folded in
    echo = next(a for a in flow if a['kind'] == 'echo')
    vis = [o['vi'] for o in echo['out']]
    assert 'Giảm 30% sát thương nhận vào' in vis  # Inherent Accidental
    assert any(o['cond'] == 4 for o in echo['out']) and any(o['cond'] == 'weapon' for o in echo['out'])
    lib = next(a for a in flow if a['kind'] == 'lib')
    assert {'Vào trạng thái Maestro', '+120% ATK'} <= {o['vi'] for o in lib['out']}
    coda = next(a for a in flow if 'Scarlet Coda' in a['say_en'])
    assert not any('Scarlet Coda' in o['en'] for o in coda['out'])  # how you get the move is not its result


def test_every_result_points_at_a_real_line(characters, combos):
    by = {c['slug']: c for c in characters}
    for slug, data in combos.items():
        for rot in data['rotations']:
            for a in rot['flow']:
                assert a['say_vi'] and a['say_en'] and a['token'], (slug, a)
                for o in a['out']:
                    line = line_of(by[slug], *o['ref'])
                    assert line and not INPUT_LINE.match(line), (slug, o)


def test_most_resonators_have_combos(combos):
    with_rot = [s for s, d in combos.items() if d['rotations']]
    assert len(with_rot) >= 55
    for d in combos.values():
        for rot in d['rotations']:
            if rot['title_vi']:
                assert not re.search(r'\bRotation\b', rot['title_vi'])


def test_cancel_notes_read_as_button_presses():
    from build_combos import HINT_VI, sub_vi
    assert sub_vi('Interrupt on first hit via Dash', HINT_VI) == 'Khi đòn trúng lần đầu thì bấm Dash để cắt phần còn lại'
    assert sub_vi('Cancel animation endlag via Ultimate', HINT_VI).startswith('Đòn vừa đánh xong thì bấm ngay R (Resonance Liberation)')
    assert sub_vi('Cancel animation on cast via Skill', HINT_VI) == 'Vừa ra đòn là bấm ngay E (Resonance Skill)'
    assert sub_vi('Instant Cancel', HINT_VI) == 'Bấm ngay thao tác tiếp theo, không chờ hết động tác'


def test_results_carry_what_the_summary_adds_up(combos):
    flow = flow_of_rot(combos, 'phrolova', 'Loop Rotation')
    strings = sum(o['qty'] for a in flow for o in a['out'] if o['name'] == 'Volatile Note - Strings')
    assert strings == 5  # Basic 3 twice + Movement of Fate and Finality three times
    states = [o['name'] for a in flow for o in a['out'] if o['cat'] == 'state']
    assert states.index('Reincarnate') < states.index('Maestro')
    outro = next(a for a in flow if a['kind'] == 'outro')
    assert all(o['cat'] == 'stat' for o in outro['out'])  # buffs handed to the next Resonator
