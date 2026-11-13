"""Signature weapons: processed in-page data (stats, R1-R5 effect, VI), not just a wiki link."""
import re

from merge_wiki import weapon_of

PH = re.compile(r'\{(\d)\}')


def raw(effect_src, ranks):
    return {'name': 'Test Blade', 'type': 'Sword', 'stat_type': 'Crit. Rate', 'rank_name': 'Test',
            'effect_src': effect_src, 'ranks': ranks, 'description_src': 'Lore.<br>More lore.',
            'stats': [], 'ascension': [], 'image_key': ''}


def test_percent_written_either_way_renders_the_same():
    # The wiki has both "(var1)%" + "12" (Everbright Polestar) and "(var1)" + "12%" (Lethean Elegy).
    a = weapon_of(raw('Increases [[ATK]] by (var1)%.', {'1': ['12', '15', '18', '21', '24']}), {}, {}, {})
    b = weapon_of(raw('Increases [[ATK]] by (var1).', {'1': ['12%', '15%', '18%', '21%', '24%']}), {}, {}, {})
    assert a['passive'] == b['passive'] == ['Increases ATK by {1}%.']
    assert a['ranks'] == b['ranks'] == {'1': ['12', '15', '18', '21', '24']}
    assert a['description'] == ['Lore.', 'More lore.']


def test_vi_only_used_while_english_matches():
    tr = {'Test Blade': {'effect_en': ['Increases ATK by {1}%.'], 'effect': ['Tăng {1}% ATK.'],
                         'description_en': ['Old lore.'], 'description': ['Truyện cũ.']}}
    missing = {}
    w = weapon_of(raw('Increases ATK by (var1)%.', {'1': ['12'] * 5}), {}, tr, missing)
    assert w['passive_vi'] == ['Tăng {1}% ATK.']
    assert w['description_vi'] == []  # EN changed on the wiki -> re-translate
    assert 'Test Blade' in missing


def test_every_signature_weapon_is_complete(characters):
    weapons = [c['signature_weapon'] for c in characters if c.get('signature_weapon')]
    assert len(weapons) >= 40
    for w in weapons:
        assert not w['img'].startswith('http'), w['name']
        assert w['passive'] and len(w['passive_vi']) == len(w['passive']), w['name']
        for en, vi in zip(w['passive'], w['passive_vi']):
            assert sorted(PH.findall(en)) == sorted(PH.findall(vi)), w['name']
            assert set(PH.findall(en)) <= set(w['ranks']), w['name']
        assert all(len(v) == 5 and not any(x.endswith('%') for x in v) for v in w['ranks'].values()), w['name']
        assert '%%' not in ''.join(w['passive']), w['name']
        if w['stats']:
            assert w['stats'][-1]['level'] == '90/90', w['name']
            assert len(w['ascension']) == 6, w['name']
            assert all(not it['img'].startswith('http') for st in w['ascension'] for it in st['items']), w['name']


def test_phrolova_weapon_values(characters):
    w = next(c for c in characters if c['slug'] == 'phrolova')['signature_weapon']
    assert w['name'] == 'Lethean Elegy'
    assert w['ranks']['1'] == ['12', '15', '18', '21', '24']
    assert w['stats'][-1] == {'ascension': '6✦', 'level': '90/90', 'atk': '587', 'sub': '24.3%'}
