"""FastAPI entrypoint for the Wuthering Waves Resonators archive."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PUBLIC = ROOT / 'public'

app = FastAPI(title='Wuthering Waves Resonators Archive')
# /api/characters is ~2 MB of JSON; gzip cuts it to a fraction for every visitor.
app.add_middleware(GZipMiddleware, minimum_size=1024)


def load_json(name: str) -> dict:
    with open(DATA / name, encoding='utf-8') as fh:
        return json.load(fh)


def character_payload() -> dict:
    return load_json('characters.json')


def meta_payload() -> dict:
    payload = character_payload()
    characters = payload['characters']
    meta = dict(payload['meta'])
    meta['characters'] = len(characters)
    meta['skills'] = sum(len(c['skills']) for c in characters)
    meta['changed_characters'] = sum(1 for c in characters if c.get('changes'))
    return meta


@app.get('/api/health')
def health():
    return {'ok': True, 'patch': meta_payload()['patch']}


@app.get('/api/meta')
def meta():
    return meta_payload()


@app.get('/api/characters')
def characters():
    payload = character_payload()
    return {'meta': meta_payload(), 'characters': payload['characters']}


SUMMARY_FIELDS = ('slug', 'name', 'rarity', 'element', 'weapon', 'img_icon', 'img_card', 'img_full')


@app.get('/api/summary')
def summary():
    # What the list page needs to render at once (~15 KB instead of the full ~2.6 MB).
    payload = character_payload()
    return {'meta': meta_payload(), 'characters': [{k: c.get(k) for k in SUMMARY_FIELDS} for c in payload['characters']]}


def search_text(c: dict) -> str:
    parts = [c['name'], c['slug'], c.get('element') or '', c.get('weapon') or '', c.get('intro') or '', c.get('intro_vi') or '']
    parts += [ch.get('note', '') for ch in c.get('changes') or []]
    for s in (c.get('skills') or []) + (c.get('resonance_chain') or []):
        parts += [s['name'], *(s.get('desc_vi') or []), *(s.get('desc') or [])]
    return ' '.join(parts).lower()


@app.get('/api/search')
def search():
    # Full-text search blob per Resonator (names, intros, skills, Resonance Chain, EN + VI).
    return {c['slug']: search_text(c) for c in character_payload()['characters']}


@app.get('/api/characters/{slug}')
def character(slug: str):
    payload = character_payload()
    for c in payload['characters']:
        if c['slug'] == slug:
            return c
    raise HTTPException(status_code=404, detail='Character not found')


@app.get('/api/mechanics')
def mechanics():
    return load_json('mechanics.json')


@app.get('/api/index')
def kit_index():
    # Derived by scripts/build_index.py: sub-moves, kit traits with evidence, mechanic users.
    return load_json('kit_index.json')


@app.get('/api/changes')
def changes():
    payload = character_payload()
    # Only characters whose in-game info changed have entries.
    entries = [
        {'slug': c['slug'], 'name': c['name'], 'changes': c['changes']}
        for c in payload['characters'] if c.get('changes')
    ]
    return {'meta': payload['meta'], 'entries': entries}


@app.get('/api/version')
def version():
    meta = meta_payload()
    return {'patch': meta['patch'], 'updated': meta['updated']}


# Vercel serves public/ from its CDN, so only mount it for local/Uvicorn runs.
class RevalidatingStatic(StaticFiles):
    """Same cache policy as vercel.json: HTML/CSS/JS always revalidate, so a browser never
    pairs a new app.js with a stale styles.css; downloaded images may be cached for a week."""

    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        if path.startswith('assets/'):
            resp.headers['Cache-Control'] = 'public, max-age=604800'
        else:
            resp.headers['Cache-Control'] = 'no-cache'
        return resp


if not os.environ.get('VERCEL'):
    app.mount('/', RevalidatingStatic(directory=str(PUBLIC), html=True), name='public')
