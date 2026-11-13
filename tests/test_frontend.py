"""Static checks on public/: i18n parity and the asset stamp."""
import re
from pathlib import Path

import stamp_assets

I18N = Path(__file__).resolve().parent.parent / 'public' / 'js' / 'i18n.js'


def _keys(block):
    return set(re.findall(r'^    ([A-Za-z_][\w]*):', block, re.M))


def test_i18n_vi_en_have_the_same_keys():
    src = I18N.read_text(encoding='utf-8')
    vi_start, en_start = src.index('\n  vi: {'), src.index('\n  en: {')
    vi, en = _keys(src[vi_start:en_start]), _keys(src[en_start:])
    assert vi, 'no vi keys parsed'
    assert not (vi - en), f'missing in en: {sorted(vi - en)}'
    assert not (en - vi), f'missing in vi: {sorted(en - vi)}'


def test_index_html_asset_stamp_is_current():
    html = stamp_assets.INDEX.read_text(encoding='utf-8')
    assert stamp_assets.stamped(html, stamp_assets.asset_hash()) == html, 'run python scripts/stamp_assets.py'
