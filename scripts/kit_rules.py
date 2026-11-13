"""Keyword rules over a Resonator's English kit text.

Single source for what used to run in the browser: named sub-moves, kit traits (with the
exact evidence lines) and the role labels of each Resonator for a mechanic. The output is
written to data/kit_index.json by scripts/build_index.py; the UI only renders it.
Regexes use re.ASCII so \\w and \\b behave like the JavaScript versions they replaced.
"""

import re

A = re.ASCII
AI = re.ASCII | re.IGNORECASE


def kit_lines(c):
    """(target, title, line_index, line, ref) for every English line of skills + Resonance Chain."""
    for i, s in enumerate(c.get('skills') or []):
        for li, line in enumerate(s.get('desc') or []):
            yield 'skill-%d' % i, s['name'], li, line, ('skill', i)
    for n in c.get('resonance_chain') or []:
        for li, line in enumerate(n.get('desc') or []):
            yield 'chain-%d' % n['node'], 'S%d · %s' % (n['node'], n['name']), li, line, ('chain', n['node'])


# ---- named sub-moves ("Basic Attack Hounds Roar", Heavy Attack "Mercy", "to cast X") ----
MOVE_TYPES = ('(?:Basic Attack|Heavy Attack|Mid-air Attack|Dodge Counter|Plunging Attack|Resonance Skill|'
              'Resonance Liberation|Intro Skill|Outro Skill|Forte Circuit|Inherent Skill|Echo Skill|'
              'Enhanced Heavy Attack|Enhanced Basic Attack)')
MOVE_CAP = r"""(?:[A-Z][\w'’!?-]*:?)(?:(?:\s(?:of|the|in|a|to|for|is|on|by|from|and|with)){0,2}\s[A-Z"][\w'’!?"-]*:?)*"""
MOVE_QUOTED = re.compile(MOVE_TYPES + r'\s+"([^"]+)"', A)
MOVE_DASHED = re.compile('(' + MOVE_TYPES + r'\s+-\s+' + MOVE_CAP + ')', A)
MOVE_PLAIN = re.compile(MOVE_TYPES + r'\s+(' + MOVE_CAP + ')', A)
MOVE_CAST_CAP = r"[A-Z][\w'’!?-]*(?:(?:\s(?:of|the|in|a|to|for|is|on|by|from|and|with)){0,2}\s[A-Z][\w'’!?-]*)*"
MOVE_CAST = re.compile(r'\b(?:[Cc]ast|[Cc]asts|[Cc]asting|[Pp]erform|[Pp]erforms|[Pp]erforming)\s+(?:the\s)?('
                       + MOVE_CAST_CAP + ')', A)
MOVE_CAST_SKIP = re.compile(r"^(?:Basic|Heavy|Mid-air|Mid-Air|Dodge|Plunging|Resonance|Intro|Outro|Forte|Inherent|Echo|"
                            r"Enhanced|Normal|Stage|Sprint|Tune)\b|\b(?:Attack|Skill|Attacks)\b|['’]s$", A)
MOVE_SKIP = {'Stage', 'DMG', 'Damage', 'Bonus', 'Multiplier', 'Cooldown', 'Concerto', 'Resonance', 'Skill', 'Attack',
             'Liberation', 'Intro', 'Outro', 'Forte', 'Circuit', 'Heavy', 'Basic', 'Dodge', 'Counter', 'Mid-air',
             'Plunging', 'Echo', 'Inherent', 'I', 'II', 'III', 'IV', 'V'}
DEFINES = re.compile(r'(replaced (?:with|by)|becomes? available|is available|to cast|to perform|can be cast|enters?|summons?)', AI)
RUN_ON = re.compile(r'\s(?:Casting|Performing|Pressing|Holding|Using|Press|Hold|Use|When|While|After)\b.*$', A)


def moves_of(c, mechanic_names):
    """Named sub-moves of one Resonator -> the line that best defines each one."""
    skill_names = {s['name'] for s in c.get('skills') or []}
    found = {}

    def add(name, ref):
        # Source lines sometimes run two sentences together ("…: Huntress Casting Comin' in Hot").
        name = RUN_ON.sub('', name)
        name = re.sub(r'\s+Stage\s*$', '', name, flags=A)
        name = re.sub(r'[\s:!]+$', '', name, flags=A).strip()
        name = re.sub(r"['’]s$", '', name)  # "Ephemeral Realm's DMG" names Ephemeral Realm
        tail = ' - '.join(name.split(' - ')[1:]) if ' - ' in name else name
        if (len(name) < 3 or name in skill_names or tail in skill_names
                or name in mechanic_names or tail in mechanic_names):
            return
        # "Heavy Attack - X" names legitimately start with a skill-type word; only plain names are filtered.
        if ' - ' not in name and name.split(' ')[0] in MOVE_SKIP:
            return
        cur = found.get(name)
        if not cur or (ref['defines'] and not cur['defines']):
            found[name] = ref

    for _target, title, li, line, (kind, index) in kit_lines(c):
        ref = {'kind': kind, 'index': index, 'line': li, 'title': title, 'defines': bool(DEFINES.search(line))}
        for rx in (MOVE_QUOTED, MOVE_DASHED, MOVE_PLAIN):
            for m in rx.finditer(line):
                add(m.group(1), dict(ref))
        for m in MOVE_CAST.finditer(line):
            if not MOVE_CAST_SKIP.search(m.group(1)):
                add(m.group(1), dict(ref))
    return {name: {k: v for k, v in ref.items() if k != 'defines'} for name, ref in found.items()}


# ---- kit traits -----------------------------------------------------------------------
TEAM_RX = re.compile(r"(?:\b(?:all|other)\s(?:nearby\s)?Resonators\b|Resonators?\s(?:on|in)\s(?:the\s)?(?:team|party)|"
                     r"\b(?:all|the)\steam\b|\b(?:team|party) members?\b|\bcharacters on (?:a\s)?nearby teams?\b|"
                     r"\bResonator on the field\b|incoming Resonator|next Resonator|\bteammates?\b)[^.]*"
                     r"\b(?:increase[sd]?|gains?|Amplif\w*|Bonus|boost\w*|deals? \d+(?:\.\d+)?% more)\b", AI)
_ENERGY_WORD = re.compile(r'\b(?:Resonance Energy|Concerto Energy|Energy Regen)\b', A)
_ENERGY_VERB = re.compile(r'\b(?:restor\w*|recover\w*|regenerat\w*|gains?|grants?|obtain\w*|increas\w*|refund\w*|'
                          r'does not consume)\b', AI)
_DMG_NEGATED = re.compile(r'\bnot (?:be )?affected by\b[^.]{0,20}\b(?:DMG Bonus|DMG Amplif)', AI)
_DMG_UP = re.compile(r'\b(?:DMG Bonus|DMG Amplif\w*|DMG Deepen)\b|\bDMG (?:dealt )?(?:is |are )?(?:increased|Amplified)\b|'
                     r'\bDMG Multiplier\b[^.]{0,60}\bincreased\b|\bincreases? (?:the )?DMG\b|'
                     r'\bdeals? (?:\d+(?:\.\d+)?% )?(?:more|additional|increased) DMG\b|\bATK (?:is )?increased\b|'
                     r'\bincreases? [^.]{0,15}\bATK\b', A)

# (key, rule, keywords shown in the UI). A rule is a compiled regex or a function(line) -> bool.
TRAIT_RULES = [
    ('heal', re.compile(r'\bheal(?:s|ing|ed)?\b|\b(?:restores?|recovers?|regenerates?)\b[^.]{0,40}\bHP\b|Healing Bonus', AI),
     'heal, restore/recover … HP, Healing Bonus'),
    ('shield', re.compile(r'\bshields?\b', AI), 'shield'),
    ('cc', re.compile(r'\bStagnat\w*|\bpull(?:s|ing)?\b[^.]{0,25}\b(?:targets?|enemies)\b|\bimmobili[sz]\w*|'
                      r'\bVibration Strength\b|\bknocks?\s(?:back|up|down)\b', AI),
     'Stagnate, pull … targets, immobilize, Vibration Strength, knock back/up'),
    ('team', TEAM_RX,
     'all/other Resonators, party/team members, incoming/next Resonator … increase, gain, Amplify, Bonus'),
    ('debuff', re.compile(r'\b(?:reduc\w*|decreas\w*|ignor\w*|lower\w*)\b[^.]{0,40}\b(?:DEF|RES)\b|'
                          r'\b(?:DEF|RES)\b[^.]{0,20}\b(?:reduced|decreased|ignored)\b|'
                          r'\btakes?\s\d+(?:\.\d+)?%\s(?:more|increased)\sDMG', AI),
     'reduce/ignore … DEF/RES, take N% more DMG'),
    ('energy', lambda l: bool(_ENERGY_WORD.search(l) and _ENERGY_VERB.search(l)),
     'Resonance Energy / Concerto Energy / Energy Regen + restore, recover, regen, gain, grant, increase'),
    # own damage up (lines that buff the team are counted under "team" instead)
    ('dmgup', lambda l: not TEAM_RX.search(l) and not _DMG_NEGATED.search(l) and bool(_DMG_UP.search(l)),
     'DMG Bonus, DMG Amplified/Deepen, DMG increased, DMG Multiplier increased, more DMG, ATK increased'),
    ('crit', re.compile(r'\bCrit\.? (?:Rate|DMG)\b[^.]{0,30}\b(?:increased|increases?|by \d)|'
                        r'\bincreases? [^.]{0,20}\bCrit\.? (?:Rate|DMG)\b', AI),
     'Crit. Rate / Crit. DMG increased'),
    ('cdr', re.compile(r'\bcooldown\b[^.]{0,40}\b(?:reduced|decreased|reset|shortened)\b|'
                       r'\b(?:reduces?|resets?|shortens?)\b[^.]{0,40}\bcooldown\b', AI),
     'cooldown reduced/reset, reduces cooldown'),
    ('summon', re.compile(r'(?<!-\s)\b[Ss]ummon(?:s|ed|ing)?\b(?!\s+and\s+Smite)', A), 'summon'),
    ('transform', re.compile(r'\b(?:enters?|transforms?|switch(?:es)? to)\b[^.]{0,40}\b(?:state|Mode|Form|Stance)\b|'
                             r'\bis replaced (?:with|by)\b', A),
     'enter/transform/switch to … state, Mode, Form, Stance; is replaced with'),
    ('revive', re.compile(r'\bfatal (?:blow|damage|attack|hit)s?\b|\b[Rr]evives?\b|\bwill not be knocked out\b|'
                          r'\bis knocked out\b[^.]{0,40}\brevive', A),
     'fatal, revive, will not be knocked out'),
    ('defense', re.compile(r'Interruption Resistance|resistance to interruption|\bDMG Reduction\b|'
                           r'\bDMG taken\b[^.]{0,20}\breduced\b|\breduces?\b[^.]{0,20}\bDMG taken\b|\binvincib\w*|\bimmun\w*', AI),
     'Interruption Resistance, DMG taken reduced, DMG Reduction, invincible, immune'),
    ('coord', re.compile(r'\bCoordinated Attacks?\b', A), 'Coordinated Attack'),
    ('tune', re.compile(r'\b(?:Tune Break|Tune Strain|Tune Rupture|Off-Tune)\b', A),
     'Tune Break, Tune Strain, Tune Rupture, Off-Tune'),
    ('offfield', re.compile(r'\bnot the active Resonator\b|\boff-field\b', AI), 'not the active Resonator, off-field'),
    ('echo', re.compile(r'\bEcho Skill DMG\b', A), 'Echo Skill DMG'),
]
NEGATIVE_STATUSES = ['Spectro Frazzle', 'Aero Erosion', 'Havoc Bane', 'Fusion Burst', 'Glacio Chafe', 'Electro Flare']
STATUS_KEYS = {s.lower().replace(' ', '_'): s for s in NEGATIVE_STATUSES}
for _key, _name in STATUS_KEYS.items():
    TRAIT_RULES.append((_key, re.compile(r'\b' + _name + r'\b', A), _name))
_STATUS_ANY = re.compile('|'.join(NEGATIVE_STATUSES), A)


def _hit(rule, line):
    return rule(line) if callable(rule) else bool(rule.search(line))


def traits_of(c):
    """trait key -> evidence [{target, title, lineIndex}] in kit order."""
    out = {}
    for target, title, li, line, _ref in kit_lines(c):
        # a line naming 3+ Negative Statuses is a generic "any Negative Status" rule, not a trait of the kit
        generic = len(set(_STATUS_ANY.findall(line))) >= 3
        for key, rule, _kw in TRAIT_RULES:
            if generic and key in STATUS_KEYS:
                continue
            if _hit(rule, line):
                out.setdefault(key, []).append({'target': target, 'title': title, 'lineIndex': li})
    return out


# ---- role labels of a Resonator for one mechanic ------------------------------------------
ROLE_RULES = [
    ('apply', re.compile(r'\b(inflicts?|inflicted|appl(y|ies)|triggers?|triggered|grants?|gains?|enters?|causes?|summons?)\b', AI),
     'inflict, apply, trigger, grant, gain, enter, cause, summon'),
    ('stack', re.compile(r'(stack limit|max(imum)?( stack| number of stacks)|additional(ly)?[^.]*\bstacks?\b|'
                         r'\bstacks?\b[^.]*\b(increased|doubled)\b)', AI),
     'stack limit, max stacks, additional stacks, stacks increased/doubled'),
    ('amplify', re.compile(r'(amplif|dmg bonus|dmg multiplier|more dmg|increased dmg|take[s]? \d+(\.\d+)?% (more|increased))', AI),
     'Amplified, DMG Bonus, DMG Multiplier, more/increased DMG'),
    ('use', re.compile(r'(consum|\bremov|affected by|inflicted with|targets? with|has \d+ stacks)', AI),
     'consume, remove, affected by, inflicted with, targets with, has N stacks'),
    ('restore', re.compile(r'(restor|recover|regen)', AI), 'restore, recover, regen'),
]


def mechanic_users(m, chars, no_link):
    """Resonators whose kit mentions mechanic m: [{slug, roles, target, line, count}], most mentions first."""
    names = [m['term']] + list(m.get('aliases') or [])
    word = re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(re.escape(n) for n in names) + r')(?![A-Za-z0-9])', A)
    blockers = [t for t in no_link if m['term'] in t]  # "Unison Boon" is not "Unison"
    owners = m.get('owners') or []
    users = []
    for c in chars:
        if owners and c['slug'] not in owners:
            continue
        roles, target, line_at, count = [], None, None, 0
        for tgt, _title, li, line, _ref in kit_lines(c):
            probe = line
            for b in blockers:
                probe = probe.replace(b, '')
            if not word.search(probe):
                continue
            count += 1
            if target is None:
                target, line_at = tgt, li
            for key, rx, _kw in ROLE_RULES:
                if key not in roles and rx.search(line):
                    roles.append(key)
        if count:
            users.append({'slug': c['slug'], 'name': c['name'], 'roles': roles, 'target': target, 'line': line_at,
                          'count': count})
    users.sort(key=lambda u: (-u['count'], u['name'].casefold()))
    for u in users:
        del u['name']
    return users
