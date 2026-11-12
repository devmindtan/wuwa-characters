"""Find Vietnamese description lines where an in-game proper name from the
English line (skill/state/item names, quoted terms) went missing, i.e. was
translated by the machine instead of being kept in English.

Usage:
    python scripts/check_names.py                 # summary
    python scripts/check_names.py --export FILE   # flagged lines as JSON for re-translation
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
MECH = ROOT / 'data' / 'mechanics.json'

# Capitalised words that are ordinary English / UI words (or fine to translate),
# not in-game proper names.
COMMON = set('''I A An The When While If After Before During Upon Each Every This That These Those It Its They Their He His She Her
You Your We Our All Any Some Both No Not Only Then Otherwise Additionally Also However Once Within Until
Deal Deals Dealing Gain Gains Grant Grants Cast Casts Casting Press Pressing Hold Holding Release Releasing Use Using Perform Performs
Can Cannot Will Increase Increases Reduce Reduces Restore Restores Consume Consumes Inflict Inflicts Trigger Triggers Enter Enters
Switch Switching Tap Long Short Jump Jumping Character Characters Cooldown Damage Attribute Attributes Utility Button Normal Target Targets
Enemy Enemies Ally Allies Team Party Member Members Level Levels Point Points Lv First Second Third Next Last Max Min Total
Note Notes Tip Tips Effect Effects Mode Modes State States Form Forms Stage Stages Phase Type Types Area Range Field Time Times
Dodging Dodged Sprint Sprinting Climbing Gliding Swimming Grappling Ground Air Mid Basic Heavy Attack Attacks Skill Skills Liberation
Resonance Resonator Resonators Intro Outro Forte Circuit Inherent Echo Echoes Dodge Counter Plunging Coordinated Stamina
DMG ATK DEF HP STA Crit Rate Bonus Energy Concerto Shield Amplified Amplification Healing Off Tune Negative Status Statuses
Spectro Havoc Aero Electro Fusion Glacio Frazzle Erosion Bane Burst Chafe Flare Strain Rupture Break Interfered Shifting Shift
Unison Response Boon Amplify Amplifies Physical For Gain When Every Deepen Multiplier Multipliers'''.split())


def candidates(en: str, extra: list[str]) -> set[str]:
    out = set(re.findall(r'"([^"]+)"', en))
    out |= {t for t in extra if re.search(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])', en)}
    # Capitalised runs not at sentence start: "Crimson Bud", "Thunder Uprising", "Cruelty"
    for m in re.finditer(r"(?<=[a-z0-9,;:)] )((?:[A-Z][\w'’]*(?:-[A-Z]?[\w'’]+)*)(?: (?:of|the|in|to|and|for|a|on|-) ?[A-Z][\w'’]*| [A-Z][\w'’]*)*)", en):
        run = re.sub(r"['’]s$", '', m.group(1)).strip()
        words = re.findall(r"[A-Z][\w'’]*", run)
        if words and not all(w.rstrip("'’s") in COMMON or w in COMMON for w in words):
            out.add(run)
    return out


def present(term: str, vi: str) -> bool:
    """Kept in VI. Checked word by word so "Qin Heart and Sword Cadence" passes for
    "Qin Heart và Sword Cadence"; ordinary words and plural "s" are tolerated."""
    v = vi.lower()
    t = term.lower()
    if t in v or t.rstrip('s') in v or (t + 's') in v:
        return True
    words = [re.sub(r"['’]s?$", '', w) for w in re.findall(r"[A-Z][\w'’-]*", term)]
    words = [w for w in words if w and w not in COMMON and w not in VERBISH]
    return all(w.lower() in v or w.lower().rstrip('s') in v for w in words)


# Capitalised verbs/numbers at the start of clauses (translated on purpose).
VERBISH = set('Enter Apply Hits Hitting Batter Throw Stagnating Stagnates Stagnate Four Three Two One Critical Hit Running Walk CD In'.split())


def flagged_lines(payload, mech_terms):
    out = []
    names = {w for c in payload['characters'] for w in re.findall(r"[A-Z][\w'’]+", c['name'])}
    COMMON.update(names)
    for c in payload['characters']:
        own = [s['name'] for s in c['skills']] + [n['name'] for n in c.get('resonance_chain', [])]
        for si, s in enumerate(c['skills']):
            for li, (en, vi) in enumerate(zip(s['desc'], s['desc_vi'])):
                miss = sorted(t for t in candidates(en, own + mech_terms) if not present(t, vi))
                # A quoted name must survive every time: "Cruelty" kept once but
                # translated ("Tàn ác") elsewhere on the same line is still a miss.
                for q in set(re.findall(r'"([^"]+)"', en)):
                    if vi.count(q.rstrip('s')) < en.count(f'"{q}"') and q not in miss:
                        miss.append(q)
                if miss:
                    out.append({'slug': c['slug'], 'skill': si, 'line': li, 'name': s['name'],
                                'missing': miss, 'en': en, 'vi': vi})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--export')
    args = ap.parse_args()
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    mech_terms = [m['term'] for m in json.loads(MECH.read_text(encoding='utf-8'))['mechanics']]
    rows = flagged_lines(payload, mech_terms)
    total = sum(len(s['desc']) for c in payload['characters'] for s in c['skills'])
    print(f'{len(rows)} of {total} VI skill lines miss an in-game name '
          f'({len({r["slug"] for r in rows})} characters)')
    if args.export:
        Path(args.export).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
        print('exported to', args.export)


if __name__ == '__main__':
    main()
