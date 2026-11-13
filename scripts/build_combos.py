"""Build data/combos.json: prydwen.gg rotations, each step linked to the kit lines it activates.

Input: data/rotations_raw.json (scripts/fetch_rotations.py) + data/characters.json.
Only the step lists are kept (the source's prose stays on prydwen, linked from the UI).
For every step the build records which lines of the kit, Resonance Chain and signature
weapon it triggers, as references [target, line] the UI resolves against the profile
data ("skill-3", "chain-1", "weapon"). Matching is keyword based (scripts/kit_rules.py)
and the UI labels it as automatic.

Output per Resonator:
  {source, rotations: [{title, title_vi, steps: [{text, label, kind, hint, hint_vi, n, refs}]}],
   triggers: [[target, line], ...]}   # every conditional kit line, to show what a rotation leaves unused
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_rules import (EFFECT_RX, INPUT_LINE, KIND_REF, KIND_TYPE, is_heading, kind_trigger,  # noqa: E402
                       name_trigger, negated, step_kind)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
RAW = ROOT / 'data' / 'rotations_raw.json'
OUT = ROOT / 'data' / 'combos.json'

STEP = re.compile(r'^(?P<head>[^()]*)\s*(?:\((?P<hint>[^()]*(?:\([^()]*\)[^()]*)*)\))?\s*(?P<tail>[^()]*)$')
STATE_ENTRY = re.compile(r"\b(?:enters?|entering|activates?|activating|into)\s+(?:the\s+)?([A-Z][\w'’-]*(?:\s[A-Z][\w'’-]*){0,3})"
                         r"(?:\s(?:state|Mode|Form|Stance))?", re.ASCII)

# Rotation titles: the common words in Vietnamese, names stay as they are.
TITLE_VI = [
    (r'\bRotations?\b', 'Combo'), (r'\bOpener\b', 'Mở đầu'), (r'\bLoop\b', 'Vòng lặp'), (r'\bStandard\b', 'Chuẩn'),
    (r'\bQuickswap\b', 'Đổi nhanh'), (r'\bBasic\b', 'Cơ bản'), (r'\bAdvanced\b', 'Nâng cao'), (r'\bSimple\b', 'Đơn giản'),
    (r'\bAlternative\b', 'Thay thế'), (r'\bExtended\b', 'Kéo dài'), (r'\bWithout\b', 'Không có'), (r'\bWith\b', 'Có'),
    (r'\bFirst\b', 'Đầu tiên'), (r'\band\b', 'và'), (r'\bor\b', 'hoặc'),
    (r'\bEasy\b', 'Dễ'), (r'\bFastest\b', 'Nhanh nhất'), (r'\bExpert\b', 'Chuyên sâu'), (r'\bOptimized\b', 'Tối ưu'),
    (r'\bMax Potential\b', 'Tối đa sức mạnh'), (r'\bMain\b', 'Chính'), (r'\bSingle\b', 'Một'), (r'\bNo\b', 'Không có'),
    (r'\bDouble\b', 'Hai'), (r'\bWarm Up\b', 'Khởi động'), (r'\bConcerto\b', 'Concerto'), (r'\bBurst Combo\b', 'Bộc phá'), (r'\bCombo\b', ''), (r'\bApproach\b', 'Cách'),
]
# Lists under these headings are advice, not a sequence of inputs.
NOT_A_ROTATION = re.compile(r'Priority|Tips|Tricks|Notes?\b|Mechanics|Overview', re.I)
# Words that may stay in English inside a Vietnamese title (game terms, codes).
TITLE_KEEP = re.compile(r"^(?:[SR]\d\+?|S\d-S\d|S\dR\d\+?|\d+|Forte|Intro|Outro|Iai|DPS|Skill|Echo|Basic|Heavy|"
                        r"Electro|Flare|Aero|Erosion|Havoc|Bane|Spectro|Frazzle|Fusion|Glacio|Chafe|Hybrid|Nightfall|"
                        r"Conversion|Outburst|Skip|Unison|Tune|Strain|Rupture|Low|High)$")
# Step hints ("Cancel animation endlag via Echo"): common patterns in Vietnamese, X = the action named.
HINT_VI = [
    (r'^Cancel animation endlag (?:via|by) (.+)$', r'Hủy hồi chiêu animation bằng \1'),
    (r'^Cancel animation on cast via (.+)$', r'Hủy animation ngay khi ra đòn bằng \1'),
    (r'^Animation cancel on cast via (.+)$', r'Hủy animation ngay khi ra đòn bằng \1'),
    (r'^Cancel animation (?:instantly|as soon as possible|near-instantly) via (.+)$', r'Hủy animation ngay lập tức bằng \1'),
    (r'^(?:Instantly interrupt|Interrupt instantly|Interrupt animation instantly|Instantly interrupt animation) via (.+)$',
     r'Ngắt ngay lập tức bằng \1'),
    (r'^Cancel animation on (?:first )?hit via (.+)$', r'Hủy animation khi đòn trúng bằng \1'),
    (r'^Interrupt on (?:first|1st) hit via (.+)$', r'Ngắt ở đòn trúng đầu tiên bằng \1'),
    (r'^Interrupt (?:after|at) (?:first|1st) hit via (.+)$', r'Ngắt sau đòn trúng đầu tiên bằng \1'),
    (r'^Interrupt on cast via (.+)$', r'Ngắt ngay khi ra đòn bằng \1'),
    (r'^(?:Optionally )?(\w+) Cancel$', r'Hủy bằng \1'),
    (r'^Optionally (\w+) Cancel$', r'Có thể hủy bằng \1'),
    (r'^Instant Cancel$', 'Hủy ngay lập tức'),
    (r'^instant cancel$', 'Hủy ngay lập tức'),
    (r'^swap$', 'Đổi nhân vật'),
    (r'^Swap$', 'Đổi nhân vật'),
    (r'^(\d+)\s*(?:times|Times|x)$', r'\1 lần'),
    (r'^(\d+)x$', r'\1 lần'),
    (r'^Full Channel$', 'Giữ hết thời gian vận'),
    (r'^Full Charge$', 'Tụ lực tối đa'),
    (r'^happens automatically off-field$', 'Tự động diễn ra khi ở ngoài sân'),
    (r'^Cast automatically$', 'Tự động thi triển'),
    (r'^pre-rotation$', 'Trước khi vào combo'),
    (r'^If Available$', 'Nếu có sẵn'),
    (r'^Enter (.+)$', r'Vào \1'),
    (r'^Switch to (.+) form$', r'Chuyển sang dạng \1'),
    (r'^Transform to (.+)$', r'Biến thành \1'),
    (r'^Either form$', 'Dạng nào cũng được'),
    (r'^Full Power$', 'Toàn lực'),
    (r'^Half Power$', 'Nửa lực'),
    (r'^Use to Cancel Endlag$', 'Dùng để hủy hồi chiêu animation'),
    (r'^Optionally Swap Cancel and immediately back$', 'Có thể đổi nhân vật để hủy rồi đổi lại ngay'),
    # anything else naming how to cancel: the general idea in Vietnamese, the exact timing in the EN tooltip
    (r'^(?:Animation cancel|Cancel(?: 2nd)? animation)\b.*\b(?:via|by) (?:Hold )?(\w+)(?: then \w+)?$', r'Hủy animation bằng \1'),
    (r'^(?:Interrupt|Instantly interrupt)\b.*\b(?:via|by) (\w+)\b.*$', r'Ngắt animation bằng \1'),
    (r'^Swap[- ]Cancel\b.*$', 'Hủy bằng đổi nhân vật'),
]
KIND_WORD = {'Skill': 'Resonance Skill', 'Ultimate': 'Resonance Liberation', 'Heavy': 'Heavy Attack', 'Echo': 'Echo',
             'Dash': 'Dash', 'Jump': 'Jump', 'Swap': 'Swap', 'Intro': 'Intro Skill', 'Outro': 'Outro Skill'}


def sub_vi(text, table):
    for rx, rep in table:
        out, n = re.subn(rx, rep, text)
        if n:
            return out
    return ''


def title_vi(title):
    """"Opener Rotation" -> "Combo mở đầu"; '' unless every remaining word is Vietnamese or a game term."""
    rest = re.sub(r'\bRotations?\b|[:“”"]', ' ', title, flags=re.I)
    for rx, rep in TITLE_VI:
        if rep != 'Combo':
            rest = re.sub(rx, rep.lower() if rep else rep, rest, flags=re.I)
    rest = re.sub(r'\s+', ' ', rest).strip()
    words = [w.strip("()[]/,.") for w in re.split(r'[\s/]+', rest)]
    words = [w for w in words if re.match(r'[A-Za-z]', w)]
    vi_words = {w.lower() for _, rep in TITLE_VI for w in rep.split()}
    english = [w for w in words if not TITLE_KEEP.match(w) and not re.search(r'[à-ỹđ]', w, re.I)
               and w.lower() not in vi_words]
    if english:
        return ''
    return ('Combo ' + rest).strip()


def parse_step(raw):
    m = STEP.match(raw.strip())
    head = (m.group('head') if m else raw).strip().rstrip(':')
    hint = (m.group('hint') or '').strip() if m else ''
    tail = (m.group('tail') or '').strip() if m else ''
    if tail:  # "Basic 3 (x) then Dash" - keep the remainder visible
        hint = (hint + ' · ' + tail).strip(' ·')
    count = None
    cm = re.search(r'(?:^|\s)[x×](\d+)$|\s(\d+)\s*(?:times|x)$', head, re.I)
    if cm:
        count = int(cm.group(1) or cm.group(2))
        head = head[:cm.start()].strip()
    cond = ''
    cm2 = re.match(r'^(\(?OPTIONAL\)?:?|Opener only:|If [^:]{2,40}:)\s*', head, re.I)
    if cm2:  # "If on Moonlit Clouds: Echo", "(OPTIONAL) Heavy: X"
        cond, head = cm2.group(1).strip(' :()'), head[cm2.end():]
    kind = step_kind(head)
    name = ''
    state = ''
    if kind is None:
        # "Incarnation: Basic P1" / "Incarnation Basic P1": a move performed inside a named state
        words = re.split(r'(?::\s*|\s+)', head)
        for cut in (1, 2):
            rest = ' '.join(words[cut:])
            if len(words) > cut and step_kind(rest) and all(re.match(r'[A-Z]', w) for w in words[:cut]):
                state, head = ' '.join(words[:cut]), rest
                kind = step_kind(head)
                break
    if ':' in head:
        name = head.split(':', 1)[1].strip()
    stage = None
    sm = re.match(r'^(?:Basic|Normal Attack|Basic Attack)\s+P?(\d)\b', head, re.I)
    label = (state + ': ' if state else '') + head
    if sm:
        stage = int(sm.group(1))
    hm = re.search(r'\b(\d+)\s*(?:times|Times)\b|^(\d+)x$', hint)
    if hm and count is None:
        count = int(hm.group(1) or hm.group(2))
    return {'label': label, 'kind': kind, 'name': name, 'state': state, 'cond': cond, 'stage': stage, 'hint': hint,
            'n': count}


def subsections(lines):
    """[(heading or '', [(li, line)])] for one skill's description."""
    out = [('', [])]
    for li, line in enumerate(lines):
        nxt = lines[li + 1] if li + 1 < len(lines) else ''
        if is_heading(line) and nxt and not is_heading(nxt):
            out.append((line, []))
        else:
            out[-1][1].append((li, line))
    return [s for s in out if s[0] or s[1]]


def kit_units(c):
    """Every line a step can activate: (target, li, line, skill_type|None)."""
    for i, s in enumerate(c.get('skills') or []):
        for li, line in enumerate(s.get('desc') or []):
            yield 'skill-%d' % i, li, line, s.get('type')
    for n in c.get('resonance_chain') or []:
        for li, line in enumerate(n.get('desc') or []):
            yield 'chain-%d' % n['node'], li, line, None
    sw = c.get('signature_weapon') or {}
    for li, line in enumerate(sw.get('passive') or []):
        yield 'weapon', li, line, None


def effect_lines(section_lines):
    return [(li, line) for li, line in section_lines if EFFECT_RX.search(line) and not INPUT_LINE.match(line)]


def build_char(c, raw):
    units = list(kit_units(c))
    text_of = {(t, li): line for t, li, line, _ in units}
    skills = c.get('skills') or []
    subs = {i: subsections(s.get('desc') or []) for i, s in enumerate(skills)}
    by_heading = {}
    for i, ss in subs.items():
        for head, lines in ss:
            if head:
                by_heading.setdefault(head, []).append((i, lines))
    triggers = {}
    for kind in KIND_REF:
        triggers[kind] = kind_trigger(kind)

    def section_of(head, seen):
        refs = []
        for i, lines in by_heading.get(head, []):
            refs += [('skill-%d' % i, li) for li, _ in effect_lines(lines)]
        return refs

    def expand_states(refs, seen):
        """A line entering "X state" pulls in the effect lines listed under heading X."""
        out = list(refs)
        lines = {(t, li): l for t, li, l, _ in units}
        for ref in refs:
            for m in STATE_ENTRY.finditer(lines.get(ref, '')):
                head = m.group(1).strip()
                if head in by_heading and head not in seen:
                    seen.add(head)
                    out += section_of(head, seen)
        return out

    def step_refs(st):
        refs = []
        kind, name, stage = st['kind'], st['name'], st['stage']
        names = []
        if name:
            names = [name, re.sub(r'\s+\d+$', '', name)]
        if st.get('state'):
            names.append(st['state'])
        for nm in dict.fromkeys(n for n in names if len(n) > 2):
            rx = name_trigger(nm)
            refs += [(t, li) for t, li, line, _ in units if rx.search(line)]
            refs += section_of(nm, set())
        if kind in KIND_REF:
            rx = kind_trigger(kind, stage)
            refs += [(t, li) for t, li, line, _ in units if rx.search(line) and not negated(line, kind)]
        if kind in KIND_TYPE and not name:
            for i, s in enumerate(skills):
                if s.get('type') == KIND_TYPE[kind]:
                    top = subs[i][0][1] if subs[i] and not subs[i][0][0] else (subs[i][0][1] if subs[i] else [])
                    refs += [('skill-%d' % i, li) for li, _ in effect_lines(top)]
        refs = expand_states(list(dict.fromkeys(refs)), set(names))
        out, seen_text = [], set()
        for r in dict.fromkeys(refs):
            line = text_of.get(r, '')
            # headings, input instructions and repeated wording add nothing to "what this step activates"
            if not line or (is_heading(line) and r[0] != 'weapon') or INPUT_LINE.match(line) or line in seen_text:
                continue
            seen_text.add(line)
            out.append(list(r))
        return out

    rotations = []
    for b in raw.get('blocks', []):
        steps = [parse_step(s) for s in b['steps']]
        known = [s for s in steps if s['kind']]
        if NOT_A_ROTATION.search(b['title'] or '') or len(steps) < 3 or len(known) / len(steps) < 0.6:
            continue  # a list of tips, not a sequence of inputs
        out_steps = []
        for raw_text, st in zip(b['steps'], steps):
            out_steps.append({
                'text': raw_text, 'label': st['label'], 'kind': st['kind'] or 'other',
                'cond': st['cond'],
                'hint': st['hint'], 'hint_vi': sub_vi(st['hint'], HINT_VI) if st['hint'] else '',
                'n': st['n'], 'refs': step_refs(st) if st['kind'] not in (None, 'move') else [],
            })
        title = b['title'] or 'Rotation'
        rotations.append({'title': title, 'title_vi': title_vi(title), 'steps': out_steps})

    all_triggers = []
    for t, li, line, _ in units:
        if INPUT_LINE.match(line):
            continue
        if any(rx.search(line) and not negated(line, k) for k, rx in triggers.items()):
            all_triggers.append([t, li])
    return {'source': raw.get('url', ''), 'fetched': raw.get('fetched', ''), 'rotations': rotations,
            'triggers': all_triggers}


def build(chars, raw):
    return {c['slug']: build_char(c, raw[c['slug']]) for c in chars if c['slug'] in raw}


def main():
    chars = json.loads(DATA.read_text(encoding='utf-8'))['characters']
    raw = json.loads(RAW.read_text(encoding='utf-8'))
    out = build(chars, raw)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    rot = sum(len(v['rotations']) for v in out.values())
    steps = sum(len(r['steps']) for v in out.values() for r in v['rotations'])
    print(f'{len(out)} Resonators, {rot} rotations, {steps} steps -> {OUT.relative_to(ROOT)} '
          f'({OUT.stat().st_size // 1024} KB)')
    print('no rotation:', [s for s, v in out.items() if not v['rotations']])


if __name__ == '__main__':
    main()
