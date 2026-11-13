import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope='session')
def characters():
    return json.loads((ROOT / 'data' / 'characters.json').read_text(encoding='utf-8'))['characters']


@pytest.fixture(scope='session')
def mechanics():
    data = json.loads((ROOT / 'data' / 'mechanics.json').read_text(encoding='utf-8'))
    return {m['term']: m for m in data['mechanics']}, data
