import json, re, time, urllib.parse, urllib.request, collections

BASE = '/home/devmindtan/wuwa-characters/'
new = json.load(open(BASE + 'data_list.json', encoding='utf-8'))
old = json.load(open(BASE + 'data_vi.json', encoding='utf-8'))
old_by_slug = {c['slug']: c for c in old}

# cache of existing translations keyed by (type, name)
cache = {}
for c in old:
    for stype, s in c['skills'].items():
        cache[(stype, s['name'])] = (s.get('desc', []), s.get('desc_vi', []))

# ---------- glossary ----------
manual = [
    "Basic Attack","Heavy Attack","Mid-air Attack","Midair Attack","Plunging Attack",
    "Dodge Counter","Resonance Skill","Resonance Liberation","Forte Circuit","Inherent Skill",
    "Intro Skill","Outro Skill","Echo Skill","Coordinated Attack","Coordinated Attacks",
    "Normal Attack","Normal Attacks","Normal Attack Button","Heavy Attack Stage",
    "Basic Attack Stage","Basic Attack DMG","Heavy Attack DMG","Resonance Skill DMG",
    "Resonance Liberation DMG","Echo Skill DMG","Concerto Energy","Resonance Energy",
    "Energy Regen","Concerto","Forte","Stamina","STA","ATK","DEF","HP","Max HP","DMG",
    "CRIT Rate","Crit. Rate","CRIT DMG","Crit. DMG","Healing Bonus","Shield",
    "All-DMG Amplification","DMG Amplification","DMG Bonus","DMG Deepen","DMG Multiplier",
    "Resonance Rate","Resonance Mode","Resonance Chain","Sequence Node","Vibration Strength",
    "Aero DMG","Havoc DMG","Spectro DMG","Electro DMG","Fusion DMG","Glacio DMG",
    "Aero Erosion","Spectro Frazzle","Havoc Bane","Fusion Burst","Glacio Chafe","Electro Flare",
    "Tune Strain","Tune Rupture","Tune Break","Off-Tune Level","Negative Status",
    "Blossom Mode","Vining Waltz","Blazing Waltz","Crimson Blossom","Floral Ravage",
    "Deathblade Gear","Hounds Roar","Incarnation","Ordination Glow","Solar Flare","Stella Glamor",
    "Unison","Eras in Unity","True Sight","Fiery Feather","Enflamement","Qingloong Mode",
    "Lance of Qingloong","Emerald Storm","Striding Lion","Lion's Vigor","Aflame","Bravo",
    "Theatrical Moment","Returned from Ashes","Death Knell","Twilight Tango","Deconstruction",
    "Moldable Crystal","Tinted Crystal","Final Bow","Mirage","Hazy Dream","Trance","Shiver",
    "Dreamweaver","Diffusion","Sword of Divinity's Shadow","Sword of Discord's Shadow",
    "Sword of Virtue's Shadow","Fleurdelys","Manifest","Conviction","Heart of Virtue",
    "Mandate of Divinity","Power of Discord","Solo Concert","Ensemble Sylph","Ensemble Sylphs",
    "Musical Essence","Recital","Symphonic Poem","Quadruple Downbeat","Chainsaw Mode","Sawring",
    "Woven Myriad","Unseen Snare","Thread of Bane","Sight of Unraveling",
    "Resonant Thread of Closure","Intuition","Hypercube","Law of Reigns","Divergence",
    "Performance Capacity","Decipher","Ephemeral Transcendence","Qin Heart","Sword Cadence",
    "Stringblade","Sword Flight","Severing Note","Beyond Imagination","Real Fantasy",
    "Commedia Improvviso","Inferno Mode","Redundant Energy","Standard Defense Protocol",
    "Crisis Response Protocol","Pinpoint Strike","Rocksteady Defense","Strategic Parry",
    "Resolving Caliber","Timed Counters","Frostfall","Fortune Rolling","Lucky Draw",
    "Antique Appraisal","Thunder Wedge","Thunder Field","Rumbling Spark","Lightning Infused",
    "Leihuangquan","Trigram","Yin-Yang Balance","Five Thunders Spell Array","Remnant Entities",
    "Concentration","Euphonia","You'tan","Outer Stellarealm","Inner Stellarealm",
    "Supernal Stellarealm","Collapsed Core","Deductive Data","Empirical Data",
    "Dim Star Butterflies","Photosynthesis Mark","Photosynthesis Energy","Starflower Blooms",
    "Verdant Growth","Illusion Breaker","Omega Storm","Echoing Orchestra","Resonating Slashes",
    "Shimmer","Umbra","Dark Surge","Devastation","Wingblade","Lifetaker","Thwackblade",
    "Starlume Acceleration","Heavenfall Edict","Stardust Resonance","Overdrive","Finale",
    "Unbound","Spectro","Havoc","Aero","Electro","Fusion","Glacio",
    "Form Switch","Stage","Charged I","Charged II","Charged III","S0","S1","S2","S3","S4","S5","S6",
    "Resonator","Resonators","Stagnate","Stagnation","Stats","Healing","DPS",
    "Lumiflow","Overflow","Optical Sampling Stage","Spark Collision","Kaleidoscopic Parade",
    "Ground Heavy Attack","Mid-air Heavy Attack","Graffiti Blast",
]
stop = {'The','This','That','These','Those','When','While','After','Before','If','Each','All','Any',
        'Every','Can','May','Will','Would','Should','Must','Perform','Deal','Deals','Press','Hold',
        'Consume','Consumes','Gain','Gains','Increase','Increases','Reduce','Reduces','Attack','Attacks',
        'Cast','Casting','Enter','Enters','Switch','Switching','Using','Use','Upon','Within','During',
        'Only','Up','For','In','At','On','By','To','Of','As','It','She','He','They','Their','His','Her',
        'Its','A','An','And','Or','But','Not','No','Yes','With','From','Into','Then','Also',
        'Additionally','However','Pressing','Release','Air','Damage','Pressing Normal Attack',
        'Release Normal Attack'}
cnt = collections.Counter()
for c in new:
    for s in c['skills']:
        for line in s['desc']:
            for m in re.findall(r"\b[A-Z][a-zA-Z'’]*(?:\s+(?:of|the|and|in|to|with|from)?\s*[A-Z][a-zA-Z'’]*){1,5}", line):
                if m.split()[0] in stop: continue
                cnt[m] += 1
manual.extend([k for k, v in cnt.items() if v >= 3])
for c in new:
    manual.append(c['name'])
    manual.append(c['name'].split(' (')[0])
    for s in c['skills']:
        manual.append(s['name'])

seen = set(); terms = []
for t in sorted(set(manual), key=lambda x: (-len(x), x)):
    t = t.strip()
    if len(t) < 2: continue
    k = t.lower()
    if k in seen: continue
    seen.add(k); terms.append(t)

token_map = {t: f"[[{i}]]" for i, t in enumerate(terms)}
token_rev = {v: k for k, v in token_map.items()}
pattern = re.compile(r'(?<![A-Za-z])(' + '|'.join(re.escape(t) for t in terms) + r')(?![A-Za-z])')

def protect(text):
    return pattern.sub(lambda m: token_map.get(m.group(0), m.group(0)), text)

FIX = [
    (r'\bChia\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)', r'Gây \1'),
    (r'\bgiao dịch\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)', r'gây \1'),
    (r'\bxử lý\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)', r'gây \1'),
    (r'\bLuồng ánh sáng\b', 'Lumiflow'),
    (r'\bLuồng sáng\b', 'Lumiflow'),
    (r'\bLuminflow\b', 'Lumiflow'),
    (r'\bLấy mẫu quang học Stage\b', 'Optical Sampling Stage'),
    (r'\bva chạm tia lửa\b', 'Spark Collision'),
    (r'-\s*Mặt đất Heavy Attack', '- Ground Heavy Attack'),
    (r'-\s*Giữa không trung Heavy Attack', '- Mid-air Heavy Attack'),
    (r'\bGiữa không trung Heavy Attack\b', 'Mid-air Heavy Attack'),
    (r'\bkhoản phí\b', 'lượt sạc'),
    (r'\bđiện tích\b', 'charge'),
    (r'\bPhát hành\b', 'Thả'),
    (r'\bBộ cộng hưởng\b', 'Resonator'),
    (r'\bBiểu hiện\b', 'Manifest'),
    (r'\bBiểu hiện hóa\b', 'Manifestation'),
]

def postprocess(text):
    text = text.replace('\u200b', '')
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'[ \t]+', ' ', text)
    for a, b in FIX:
        text = re.sub(a, b, text, flags=re.I)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip()

def clean_line(s):
    s = postprocess(s.strip())
    if not s: return s
    if s.startswith('• '):
        rest = s[2:].strip()
        if rest: rest = rest[0].upper() + rest[1:]
        s = '• ' + rest
    else:
        s = s[0].upper() + s[1:]
    return s

def restore(text):
    text = re.sub(r'\[\{\d+\}\]|\[\[\d+\]\]', lambda m: token_rev.get(m.group(0), m.group(0)), text)
    return postprocess(text)

def translate_batch(texts):
    params = [('client','gtx'),('sl','en'),('tl','vi'),('dt','t')]
    for t in texts:
        params.append(('q', protect(t)))
    url = "https://translate.googleapis.com/translate_a/t?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            if isinstance(out, str): out = [out]
            return [restore(x) for x in out]
        except Exception as e:
            last = e
            time.sleep(3 + attempt*4)
    raise last

# ---------- apply ----------
missing = []
for c in new:
    o = old_by_slug.get(c['slug'], {})
    c['img_icon'] = o.get('img_icon', c['img_icon'])
    c['img_card'] = o.get('img_card', c['img_card'])
    c['img_full'] = o.get('img_full', c['img_full'])
    c['intro_vi'] = o.get('intro_vi', '')
    for s in c['skills']:
        s['desc'] = [clean_line(x) for x in s['desc'] if x.strip()]
        hit = cache.get((s['type'], s['name']))
        if hit and [y.strip() for y in hit[0]] == [x.strip() for x in s['desc']] and hit[1]:
            s['desc_vi'] = [clean_line(x) for x in hit[1] if x.strip()]
        else:
            s['desc_vi'] = None
            missing.append(s)

print('skills total', sum(len(c['skills']) for c in new), 'need translation', len(missing), flush=True)

# translate missing
tasks = []
for s in missing:
    joined = '\n'.join(s['desc'])
    tasks.append((s, joined))

results = {}
i = 0
while i < len(tasks):
    batch, size = [], 0
    while i < len(tasks) and len(batch) < 4:
        enc = len(urllib.parse.quote(tasks[i][1]))
        if batch and size + enc > 4200: break
        batch.append(tasks[i]); size += enc; i += 1
    texts = [b[1] for b in batch]
    try:
        outs = translate_batch(texts)
        if len(outs) != len(batch):
            outs = [translate_batch([t])[0] for t in texts]
        for (s, _), o in zip(batch, outs):
            results[id(s)] = o
    except Exception as e:
        print('FAIL', i, e, flush=True)
        for s, t in batch:
            try:
                results[id(s)] = translate_batch([t])[0]
            except Exception:
                results[id(s)] = '\n'.join(s['desc'])
    time.sleep(0.25)

for s in missing:
    o = results.get(id(s), '\n'.join(s['desc']))
    s['desc_vi'] = [clean_line(x) for x in o.split('\n') if x.strip()]

json.dump(new, open(BASE + 'data_vi2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote data_vi2.json', flush=True)
