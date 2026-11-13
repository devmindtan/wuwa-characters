"""API contract used by the frontend (public/js/main.js, detail.js)."""
import pytest
from fastapi.testclient import TestClient

from app.main import SUMMARY_FIELDS, app


@pytest.fixture(scope='module')
def client():
    return TestClient(app)


def test_summary_is_small_and_complete(client, characters):
    body = client.get('/api/summary').json()
    assert body['meta']['patch'] and body['meta']['characters'] == len(characters)
    assert len(body['characters']) == len(characters)
    for c in body['characters']:
        assert set(c) == set(SUMMARY_FIELDS), c['slug']


def test_search_covers_skill_text(client):
    search = client.get('/api/search').json()
    assert 'aftersound' in search['phrolova']
    assert all(text == text.lower() for text in search.values())


def test_character_detail_and_404(client):
    assert client.get('/api/characters/jinhsi').json()['skills']
    assert client.get('/api/characters/khong-co').status_code == 404


def test_index_and_mechanics(client):
    index = client.get('/api/index').json()
    assert {'rules', 'chars', 'mech_users'} <= set(index)
    mech = client.get('/api/mechanics').json()
    hazy = next(m for m in mech['mechanics'] if m['term'] == 'Hazy Dream')
    ref = hazy['defs']['cantarella']
    assert ref['text_en'] and ref['text_vi'] and ref['title']  # quoted on Phrolova's page without loading Cantarella


def test_api_is_gzipped(client):
    r = client.get('/api/summary', headers={'Accept-Encoding': 'gzip'})
    assert r.status_code == 200
    r = client.get('/api/search', headers={'Accept-Encoding': 'gzip'})
    assert r.headers.get('content-encoding') == 'gzip'
