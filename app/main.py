"""FastAPI entrypoint for the Wuthering Waves Resonators archive."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PUBLIC = ROOT / 'public'

app = FastAPI(title='Wuthering Waves Resonators Archive', version='3.7')


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
    meta['versions'] = sorted({c['version'] for c in characters})
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
    entries = []
    for c in payload['characters']:
        entries.append({
            'slug': c['slug'],
            'name': c['name'],
            'version': c['version'],
            'updated': c.get('updated', ''),
            'changes': c.get('changes', []),
        })
    return {'meta': payload['meta'], 'entries': entries}


@app.get('/api/version')
def version():
    meta = meta_payload()
    return {'patch': meta['patch'], 'updated': meta['updated'], 'versions': meta['versions']}


app.mount('/', StaticFiles(directory=str(PUBLIC), html=True), name='public')
