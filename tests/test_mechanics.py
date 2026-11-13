"""Golden cases for data/mechanics.json: every case here was a real bug or request."""
import build_mechanics


def test_mechanics_json_is_up_to_date(tmp_path, monkeypatch, mechanics):
    # Rebuilding from the current sources must not change the committed file.
    out = tmp_path / 'mechanics.json'
    monkeypatch.setattr(build_mechanics, 'OUT', out)
    build_mechanics.main()
    assert out.read_text(encoding='utf-8') == (build_mechanics.ROOT / 'data' / 'mechanics.json').read_text(encoding='utf-8'), \
        'data/mechanics.json is stale: run python scripts/build_mechanics.py'


def test_every_curated_term_has_both_languages(mechanics):
    by_term, _ = mechanics
    for m in by_term.values():
        if m.get('auto'):
            assert m['defs'], m['term']
        else:
            assert m['summary_vi'] and m['summary_en'], m['term']


def test_kit_terms_link_on_owner_pages(mechanics):
    by_term, _ = mechanics
    assert 'phrolova' in by_term['Aftersound']['owners']
    assert 'phrolova' in by_term['Resolving Chord']['owners']
    assert 'calcharo' in by_term['Cruelty']['owners']
    assert 'cantarella' in by_term['Jolt']['owners']


def test_cross_character_kit_term(mechanics):
    by_term, _ = mechanics
    hazy = by_term['Hazy Dream']
    assert 'phrolova' in hazy['owners'] and 'cantarella' in hazy['defs'] and 'phrolova' not in hazy['defs']
    # names that merely contain another kit's term are not cross-linked
    assert 'jianxin' not in by_term['Primordial Qi']['owners']


def test_owner_only_terms(mechanics):
    by_term, _ = mechanics
    assert by_term['Manifest']['owners'] == ['cartethyia']  # not inside Hsin's "Heart Manifest"


def test_no_junk_kit_terms(mechanics):
    by_term, _ = mechanics
    for junk in ['Each', 'The', 'This', 'Every', 'Stamina', 'Energy', 'Wide Field', "Shorekeeper's Energy", 'Havoc DMG']:
        assert junk not in by_term, junk


def test_definition_quotes_prefer_defining_line(mechanics, characters):
    by_term, _ = mechanics
    chars = {c['slug']: c for c in characters}
    ref = by_term['Resolving Chord']['defs']['phrolova']
    line = chars['phrolova']['skills'][ref['index']]['desc'][ref['line']]
    assert 'activates the Resolving Chord state' in line


def test_plural_aliases(mechanics):
    by_term, _ = mechanics
    assert 'Volatile Notes' in by_term['Volatile Note']['aliases']
    assert 'Melodies' in by_term['Melody']['aliases']
    assert {'Stagnates', 'Stagnation'} <= set(by_term['Stagnate']['aliases'])


def test_negative_status_summaries_are_complete(mechanics):
    by_term, _ = mechanics
    assert '3 tầng' in by_term['Havoc Bane']['summary_vi'] and '2% DEF' in by_term['Havoc Bane']['summary_vi']
    assert '3 times' in by_term['Havoc Bane']['summary_en']
    for term in ['Fusion Burst', 'Glacio Chafe', 'Electro Flare', 'Aero Erosion', 'Spectro Frazzle']:
        assert '\n• ' in by_term[term]['summary_vi'] and '\n• ' in by_term[term]['summary_en'], term
        assert by_term[term]['source'] == 'wiki'


def test_curated_file_schema(characters):
    import json
    data = json.loads(build_mechanics.CURATED_FILE.read_text(encoding='utf-8'))
    slugs = {c['slug'] for c in characters}
    kinds = {'resource', 'system', 'status', 'mode', 'skill', 'summon', 'stat'}
    seen = set()
    for t in data['terms']:
        assert t['term'] not in seen, f"duplicate term {t['term']}"
        seen.add(t['term'])
        assert t['kind'] in kinds, t
        assert t.get('owner') is None or t['owner'] in slugs, t
        assert t.get('source') in (None, 'wiki'), t
