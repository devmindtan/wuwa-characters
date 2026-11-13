"""Build data/mechanics.json from the canonical character data.

Each mechanic keeps a short Vietnamese summary plus the first grounded snippet
from the actual kit so the UI never invents explanations.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
OUT = ROOT / 'data' / 'mechanics.json'

CURATED_FILE = ROOT / 'data' / 'mechanics_curated.json'


def load_curated(path=CURATED_FILE):
    """Hand-written content lives in data/mechanics_curated.json (VI/EN side by side)."""
    data = json.loads(path.read_text(encoding='utf-8'))
    terms = data['terms']
    missing = [t['term'] for t in terms if not t.get('vi') or not t.get('en')]
    assert not missing, f'mechanics_curated.json: missing vi/en for {missing}'
    curated = {t['term']: (t['vi'], t['kind']) for t in terms}
    summary_en = {t['term']: t['en'] for t in terms}
    owners = {}
    for t in terms:
        if t.get('owner'):
            owners.setdefault(t['owner'], []).append(t['term'])
    wiki = {t['term'] for t in terms if t.get('source') == 'wiki'}
    aliases = {t['term']: list(t['aliases']) for t in terms if t.get('aliases')}
    return curated, summary_en, owners, wiki, data['no_link'], aliases


# CURATED: term -> (summary_vi, kind). OWNERS: Resonator-specific mechanics only link on their
# owners' pages, so a common word (e.g. "Manifest" inside Hsin's "Heart Manifest") never opens
# another character's explanation. NO_LINK: names that merely contain a mechanic's name
# ("Unison Boon") are matched first and rendered as plain text. ALIASES: inflected forms.
CURATED, SUMMARY_EN, OWNERS, WIKI_TERMS, NO_LINK, ALIASES = load_curated()
OWNER_OF = {term: slug for slug, terms in OWNERS.items() for term in terms}


# ---- automatic kit terms -------------------------------------------------
# Named states/resources of a Resonator's own kit (Phrolova's "Aftersound",
# "Resolving Chord"...). They are detected from the English text and explained
# only by quoting the defining lines of the data (never a written summary).
_W = r"[A-Z][A-Za-z'’\-]*"
_NAME = rf"{_W}(?:\s(?:of\s|the\s|and\s|in\s|de\s|to\s)?{_W})*"
AUTO_PATTERNS = [
    ('mode', rf"({_NAME})\s(?:state|status)\b"),
    ('mode', rf"({_NAME}\s(?:Mode|Form|Stance))\b"),
    ('mode', rf"\b(?:enters?|entering)\s(?:the\s|into\s)?({_NAME})"),
    ('resource', rf"\bstacks?\sof\s({_NAME})"),
    ('resource', rf"({_NAME})\sstacks?\b"),
    ('resource', rf"\bpoints?\sof\s({_NAME})"),
    ('status', rf"\b(?:sends?|sending|puts?|putting)\s(?:the\s)?(?:targets?|enemies|them|it)\sinto\s({_NAME})"),
    ('status', rf"\b(?:inflicts?|inflicting|applies|applying|removing|removes)\s({_NAME})"),
    ('status', rf"({_NAME})\s(?:is|are)\striggered\b"),
    # named resources the game writes in quotes: "Cruelty", "Killing Intent", "Readiness"
    ('resource', rf"[\"“]({_NAME})[\"”]"),
    ('status', rf"({_NAME}\s(?:Mark|Marks|Field|Zone|Energy|Points|Core|Cores|Bullets))\b"),
    ('resource', rf"\b(?:consumes?|consuming|obtains?|obtaining)\s(?:all\s|up\sto\s)?(?:\d+\s)?(?:points?\sof\s|stacks?\sof\s)?({_NAME})"),
]
LEAD_DROP = re.compile(r"^(?:(?:The|In|Enter|Entering|Exit|Exiting|Leave|Leaving|Ending|Switching|Active|Available|"
                       r"Consuming|During|Upon|After|While|When|Under|Casting|Hold|Press|Each|Every|If|Obtain|Obtains|Inherits|Resonance Liberation|"
                       r"Resonance Skill|Forte Circuit|Intro Skill|Outro Skill|Basic Attack|Heavy Attack)\s)+")
AUTO_STOP = set("""All Max HP Shield Cooldown Parry Sprint STA DMG ATK DEF HP Crit Echo Resonator Resonators Energy Concerto
Co-op Mode Walking Mode Aiming Mode Wind Voice Mind Blazes Cooldown Photo Dodge Counter Mid-air Attack Plunging Attack
Basic Attack Heavy Attack Resonance Skill Resonance Liberation Intro Skill Outro Skill Forte Circuit Inherent Skill
Havoc Fusion Glacio Aero Electro Spectro Physical Tune Break Boost Negative Status Unbound""".split('\n'))
AUTO_STOP = {w.strip() for line in AUTO_STOP for w in [line]} | {
    'All', 'Max HP', 'Shield', 'Cooldown', 'Parry', 'Sprint', 'STA', 'Co-op Mode', 'Walking Mode', 'Wind', 'Voice',
    'Mind', 'Blazes', 'Photo', 'Unbound', 'Avatar', 'Capacity', 'Overload', 'Overlimit', 'Enrichment',
    'Each', 'The', 'This', 'Every', 'Form', 'Breath', 'Laser', 'Stamina', 'Energy'}
AUTO_BAD_WORD = {'DMG', 'ATK', 'DEF', 'HP', 'Amplifies', 'Resonance', 'Liberation', 'Attack', 'Skill'}
DEFINING = re.compile(r"\b(enters?|activates?|gains?|obtains?|grants?|can hold|up to|becomes?|is replaced|lasts?)\b", re.I)
SKILL_HEAD = re.compile(r'^(Basic|Heavy|Mid-air|Plunging|Dodge|Resonance|Intro|Outro|Enhanced|Forte|Normal|Avatar|During|Upward)\b')


def is_heading(line):
    return not line.startswith('• ') and len(line) < 72 and not re.search(r'[.!?]$', line)


def clean_term(raw, char):
    t = raw.strip()
    t = re.sub(r"^" + re.escape(char['name'].split()[0]) + r"(?:\s\w+)?['’]s\s", '', t)
    t = LEAD_DROP.sub('', t).strip()
    # "Shorekeeper's Energy", "Aemeath's Crit": a stat of the Resonator, not a named mechanic
    if any(re.search(re.escape(w) + r"['’]s\b", t) for w in char['name'].replace('(', ' ').replace(')', ' ').split()):
        return ''
    return t


def auto_terms(chars, taken):
    """Return {term: {kind, defs: {slug: ref}}} for kit terms not covered by CURATED/NO_LINK."""
    found = {}
    for c in chars:
        skill_names = {s['name'] for s in c['skills']}
        texts = [('skill', i, j, l) for i, sk in enumerate(c['skills']) for j, l in enumerate(sk['desc'])]
        texts += [('chain', n['node'], j, l) for n in c.get('resonance_chain', []) for j, l in enumerate(n['desc'])]
        cands = {}  # term -> (kind, ref, priority)

        def offer(term, kind, ref, prio):
            if (term in taken or term in AUTO_STOP or term in skill_names or len(term) < 3 or ' and ' in term
                    or not term[0].isupper() or len(term.split()) > 5 or AUTO_BAD_WORD & set(term.split())):
                return
            if term not in cands or prio < cands[term][2]:
                cands[term] = (kind, ref, prio)

        # 1) sub-headings inside skills define a named mechanic; quote the lines under it
        for i, sk in enumerate(c['skills']):
            lines = sk['desc']
            for j, l in enumerate(lines):
                if j == 0 or not is_heading(l) or SKILL_HEAD.match(l) or ' - ' in l or ':' in l or len(l.split()) > 4:
                    continue
                body = 0
                for k in range(j + 1, min(len(lines), j + 4)):
                    if is_heading(lines[k]):
                        break
                    body += 1
                if body:
                    offer(l.strip(), 'system', {'kind': 'skill', 'index': i, 'line': j + 1, 'n': body}, 0)
        # 2) phrase patterns; the quoted line is the most "defining" mention of the term
        kinds = {}
        for kind_src, idx, j, l in texts:
            for kind, pat in AUTO_PATTERNS:
                for m in re.finditer(pat, l):
                    kinds.setdefault(clean_term(m.group(1), c), kind)
        for term, kind in kinds.items():
            word = re.compile(r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])')
            best = None
            for kind_src, idx, j, l in texts:
                if not word.search(l):
                    continue
                forte = kind_src == 'skill' and c['skills'][idx].get('type') == 'Forte Circuit'
                direct = re.search(r"\b(enters?|activates?|gains?|obtains?|grants?|can hold|consumes?|triggers?)\s(?:the\s|a\s|an\s|up\sto\s|\d+\s|stacks?\sof\s|points?\sof\s)*"
                                   + re.escape(term) + r"(?![A-Za-z0-9])", l)
                score = (5 if direct else 0) + (2 if DEFINING.search(l) else 0) + (2 if forte else 0) \
                    - (4 if len(l) < 50 else 0) \
                    - (1 if l.startswith('• ') else 0)
                if best is None or score > best[0]:
                    best = (score, {'kind': kind_src, 'index': idx, 'line': j, 'n': 1})
            if best:
                ref = best[1]
                if ref['kind'] == 'skill':  # "…obtain Frost in the following ways:" -> quote the list too
                    lines = c['skills'][ref['index']]['desc']
                    if lines[ref['line']].rstrip().endswith(':'):
                        k = ref['line'] + 1
                        while k < len(lines) and k - ref['line'] <= 3 and lines[k].startswith('• '):
                            k += 1
                        ref['n'] = k - ref['line']
                offer(term, kind, ref, 1)
        blob = '\n'.join(l for *_, l in texts)
        def singular(w):
            return [w[:-3] + 'y', w[:-1]] if w.endswith('ies') else [w[:-1]] if w.endswith('s') else []
        for term, (kind, ref, _) in cands.items():
            plural = re.escape(term[:-1]) + 'ies' if term.endswith('y') else re.escape(term) + 's'
            if len(re.findall(r'(?<![A-Za-z0-9])(?:' + plural + '|' + re.escape(term) + r')(?![A-Za-z0-9])', blob)) < 2:
                continue  # mentioned once (only its heading): nothing to link
            if any(x in cands or x in taken for x in singular(term)):
                continue  # plural of a known term: linked through its alias
            longer = [x for x in cands if x != term and term in x]
            rest = blob
            for x in sorted(longer, key=len, reverse=True):
                rest = rest.replace(x, '')
            if longer and not re.search(r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])', rest):
                continue  # only ever part of a longer name ("Wide Field" in "Wide Field Observation Mode")
            e = found.setdefault(term, {'kind': kind, 'defs': {}})
            e['defs'][c['slug']] = ref
    # a shorter term fully contained in a longer auto term of the same Resonator is kept:
    # the UI matches the longest phrase first.
    return found


def term_in(term, text):
    return re.search(r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])', text) is not None


def main():
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    chars = payload['characters']
    mechanics = []
    for term, (summary, kind) in CURATED.items():
        count = 0
        users = []
        sample = ''
        sample_en = ''
        owner = OWNER_OF.get(term)
        for c in chars:
            if owner and c['slug'] != owner:
                continue
            hit = 0
            texts = [(en, vi) for s in c['skills'] for en, vi in zip(s['desc'], s['desc_vi'])]
            texts += [(en, vi) for n in c.get('resonance_chain', []) for en, vi in zip(n['desc'], n['desc_vi'])]
            for en, vi in texts:
                if term_in(term, en) or term_in(term, vi):
                    hit += 1
                    if not sample:
                        sample = vi if term_in(term, vi) else en
                    if not sample_en and term_in(term, en):
                        sample_en = en
            if hit:
                count += hit
                users.append(c['slug'])
                if not sample:
                    sample = f'{c["name"]} — {hit} lần'
        if not count:
            continue
        mechanics.append({
            'term': term,
            'kind': kind,
            'summary_vi': summary,
            'summary_en': SUMMARY_EN[term],
            'sample_en': sample_en[:320],
            'sample_vi': sample[:320],
            'count': count,
            'characters': users,
            'owners': [owner] if owner else [],
        })
    for m in mechanics:
        if m['term'] in WIKI_TERMS:
            m['source'] = 'wiki'
        if m['term'] in ALIASES:
            m['aliases'] = list(ALIASES[m['term']])
    taken = set(CURATED) | set(NO_LINK)
    autos = auto_terms(chars, taken)
    # Another Resonator's kit may mention someone else's kit term (Phrolova: "…the target's
    # Hazy Dream state" is Cantarella's). Link it there too, quoting the owner's definition.
    for term, e in autos.items():
        if len(term.split()) < 2:
            continue  # single words ("Prayer", "Zoom") are too ambiguous across kits
        # only when the other kit uses it as a state/stack ("Hazy Dream state"), not as part of a move name
        word = re.compile(r"(?:\bstacks?\sof\s|\b(?:target|enemy)['’]s\s)" + re.escape(term) + r"(?![A-Za-z0-9])|(?<![A-Za-z0-9])"
                          + re.escape(term) + r"\s(?:state|status|stacks?)\b")
        e['refs'] = sorted(c['slug'] for c in chars if c['slug'] not in e['defs'] and any(
            word.search(l) for s in c['skills'] + c.get('resonance_chain', []) for l in s['desc']))
    # The quoted definition is stored with the term, so a page can quote another Resonator's
    # kit (Phrolova quoting Cantarella's Hazy Dream) without loading that Resonator.
    by_slug = {c['slug']: c for c in chars}
    for term, e in autos.items():
        for slug, ref in e['defs'].items():
            c = by_slug[slug]
            src = c['skills'][ref['index']] if ref['kind'] == 'skill' else next(
                n for n in c['resonance_chain'] if n['node'] == ref['index'])
            vi_lines = src.get('desc_vi') or src['desc']
            pick = lambda lines: ' '.join(l[2:] if l.startswith('• ') else l
                                          for l in lines[ref['line']:ref['line'] + ref.get('n', 1)])
            ref['title'] = src['name'] if ref['kind'] == 'skill' else f"S{src['node']} · {src['name']}"
            ref['text_en'] = pick(src['desc'])
            ref['text_vi'] = pick(vi_lines)
    for term, e in sorted(autos.items()):
        users = sorted(set(e['defs']) | set(e.get('refs', [])))
        mechanics.append({
            'term': term,
            'kind': e['kind'],
            'auto': True,
            'defs': e['defs'],
            'count': len(users),
            'characters': users,
            'owners': users,
        })
    # plural forms used in the text ("Volatile Notes") link to the singular term
    all_text = '\n'.join(l for c in chars for s in c['skills'] + c.get('resonance_chain', []) for l in s['desc'])
    for m in mechanics:
        term = m['term']
        for plural in ([term[:-1] + 'ies'] if term.endswith('y') else []) + [term + 's']:
            if (not term.endswith('s') and term_in(plural, all_text) and plural not in m.get('aliases', [])
                    and plural not in {x['term'] for x in mechanics}):
                m.setdefault('aliases', []).append(plural)
    print(f'auto kit terms: {len(autos)}')
    missing_owner = [t for t in OWNER_OF if t not in {m['term'] for m in mechanics}]
    if missing_owner:
        print('warning: owner terms not found in data:', missing_owner)
    mechanics.sort(key=lambda m: (-m['count'], m['term']))
    OUT.write_text(json.dumps({'mechanics': mechanics, 'no_link': NO_LINK}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wrote {OUT} with {len(mechanics)} mechanics')


if __name__ == '__main__':
    main()
