"""FastAPI entrypoint for the Wuthering Waves Resonators archive."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PUBLIC = ROOT / 'public'

app = FastAPI(title='Wuthering Waves Resonators Archive')


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
if not os.environ.get('VERCEL'):
    app.mount('/', StaticFiles(directory=str(PUBLIC), html=True), name='public')
