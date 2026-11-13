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

CURATED = {
    # ---- global systems ----
    'Concerto Energy': ('Thanh năng lượng thể hiện mức sẵn sàng của Outro Skill (Resonator rời sân) và Intro Skill (Resonator vào sân).', 'resource'),
    'Resonance Energy': ('Tài nguyên khi đầy cho phép thi triển Resonance Liberation.', 'resource'),
    'Resonance Mode': ('Cơ chế cho phép Resonator chuyển giữa các chế độ gây hiệu ứng/loại sát thương khác nhau.', 'system'),
    'Off-Tune Level': ('Thanh tích lũy trên mục tiêu bị Tune Strain; khi đầy có thể kích hoạt Tune Break.', 'system'),
    'Tune Strain': ('Một nhánh của cơ chế Tune Break: Tune Strain - Shifting đánh dấu mục tiêu; khi mục tiêu bị Tune Break, dấu chuyển thành Tune Strain - Interfered và Resonator có Tune Strain Response gây thêm sát thương lên mục tiêu đó.', 'system'),
    'Tune Break': ('Loại Forte có thể kích hoạt thủ công khi kẻ địch vào trạng thái Mistune. Có ba nhánh: Tune Strain, Tune Rupture và Hack.', 'system'),
    'Tune Rupture': ('Một nhánh của cơ chế Tune Break: Tune Rupture - Shifting đánh dấu mục tiêu; khi mục tiêu bị Tune Break, dấu phát nổ gây một đòn sát thương lớn và mục tiêu chuyển sang Tune Rupture - Interfered.', 'system'),
    'Tune Break Boost': ('Chỉ số tăng hiệu quả Tune Break; Resonator có Tune Strain Response nhận thêm tổng sát thương từ Tune Break Boost.', 'stat'),
    'Negative Status': ('Các hiệu ứng sát thương theo thời gian và hiệu ứng bất lợi có thể cộng dồn, áp lên cả kẻ địch lẫn Resonator: Spectro Frazzle, Aero Erosion, Havoc Bane, Fusion Burst, Glacio Chafe, Electro Flare.', 'status'),
    'Spectro Frazzle': ('Negative Status hệ Spectro (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Aero Erosion': ('Negative Status hệ Aero (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Havoc Bane': ('Negative Status hệ Havoc (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Fusion Burst': ('Negative Status hệ Fusion (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Glacio Chafe': ('Negative Status hệ Glacio (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Electro Flare': ('Negative Status hệ Electro (có thể cộng dồn). Tác dụng cụ thể theo từng bộ kỹ năng: xem các đoạn trích bên dưới.', 'status'),
    'Coordinated Attack': ('Đòn đánh bổ trợ do Resonator không trực tiếp điều khiển (ngoài sân) tự động thực hiện cùng Resonator đang trên sân.', 'system'),
    'Echo Skill': ('Kỹ năng chủ động đến từ Echo đặt ở ô chính; một số Resonator (như Phrolova, Qiuyuan) có đòn được tính là Echo Skill DMG.', 'system'),
    'Vibration Strength': ('Cơ chế trên kẻ địch: giảm Vibration Strength để buộc kẻ địch vào trạng thái bất động một thời gian và chịu thêm sát thương.', 'system'),
    'All-DMG Amplification': ('Tăng sát thương của mọi loại đòn đánh.', 'stat'),
    'DMG Amplification': ('Hệ số khuếch đại sát thương cuối, khác với DMG Bonus.', 'stat'),
    'Stagnate': ('Làm chậm các mục tiêu trong một phạm vi nhất định (vai trò chiến đấu Stagnation).', 'status'),
    'Interfered': ('Trạng thái của kẻ địch sau khi bị Tune Break khi đang mang dấu Shifting (Tune Strain - Interfered / Tune Rupture - Interfered); các Resonator có Response tương ứng sẽ phản ứng lên mục tiêu này.', 'status'),
    'Shifting': ('Dấu Tune Strain - Shifting / Tune Rupture - Shifting một số Resonator gây lên kẻ địch; tự nó không có tác dụng, khi mục tiêu bị Tune Break thì chuyển thành Interfered. Kéo dài 25 giây.', 'status'),
    'Mistune': ('Trạng thái của kẻ địch cho phép kích hoạt Tune Break thủ công.', 'status'),
    'Interruption Resistance': ('Chỉ số ẩn: khả năng của Resonator hoặc kẻ địch không bị đòn của đối phương làm gián đoạn.', 'stat'),

    # ---- resonator-specific modes ----
    'Incarnation': ('Trạng thái biến đổi của Jinhsi; thay Basic/Heavy/Resonance Skill và Dodge bằng phiên bản Incarnation, kết thúc sau Incarnation - Basic Attack Stage 4.', 'mode'),
    'Ordination Glow': ('Hiệu ứng Jinhsi nhận sau khi kết thúc Incarnation, tăng sát thương cho bộ chiêu.', 'mode'),
    'Eras in Unity': ('Hiệu ứng cộng hưởng Jinhsi cấp cho các Resonator gần đó khi có mặt trong đội.', 'mode'),
    'Form Switch': ('Chuyển đổi giữa Aemeath và Mech; mỗi dạng có bộ chiêu và cơ chế riêng.', 'mode'),
    'Stardust Resonance': ('Trạng thái buff Aemeath nhận sau Resonance Liberation.', 'mode'),
    'Heavenfall Edict': ('Trạng thái nâng cấp Heavy Attack của Aemeath sau Resonance Liberation.', 'mode'),
    'Kaleidoscopic Parade': ('Trạng thái thay thế bộ chiêu của Lynae, gồm Basic/Heavy/Dodge Counter riêng.', 'mode'),
    'Blossom Mode': ('Trạng thái chiến đấu đặc biệt của Camellya.', 'mode'),
    'Crimson Blossom': ('Cộng dồn/hiệu ứng đặc biệt trong Blossom Mode của Camellya.', 'mode'),
    'Inferno Mode': ('Trạng thái đặc biệt của Zani, thay đổi Resonance Skill và bộ chiêu.', 'mode'),
    'Chainsaw Mode': ('Trạng thái đặc biệt của Chisa; một số kỹ năng bị khóa khi ở trạng thái này.', 'mode'),
    'True Sight': ('Trạng thái Changli nhận sau Basic Attack Stage 4, kéo dài 12 giây.', 'mode'),
    'Unison': ('Hiệu ứng/Resonance Mode dùng chung của một số Resonators (Hsin, Jinhsi, Suoming, Lily…); khi có Unison có thể kích hoạt Unison Response. Tóm tắt từ bộ kỹ năng.', 'mode'),
    'Heart Manifest': ('Trạng thái của Hsin: thi triển Formshift để mở Manifold Sanctum, Hsin chuyển sang Illumining Form và vào Heart Manifest; trở lại Answering Form thì rời trạng thái này. Tóm tắt từ bộ kỹ năng.', 'mode'),
    'Deathblade Gear': ('Trạng thái sau Resonance Liberation của Calcharo, thay đổi bộ chiêu.', 'mode'),
    'Fleurdelys': ('Dạng biến đổi của Cartethyia khi HP dưới 50%, mở khóa chiêu mới.', 'mode'),
    'Manifest': ('Trạng thái Cartethyia nhận sau khi biến thành Fleurdelys.', 'mode'),
    'Reminiscence': ('Trạng thái đặc biệt của Lucilla, thay đổi Intro/Resonance Skill.', 'mode'),
    'Trace': ('Tài nguyên tích lũy của Lucilla.', 'resource'),
    'Photos': ('Ba biểu tượng Lucilla cần thu thập để mở Resonance Liberation.', 'resource'),
    'Payload': ('Resonance Skill dạng lao tới của Lucy.', 'skill'),
    'Hack': ('Hiệu ứng lên mục tiêu, dùng bởi Lucy và Rebecca (Hack - Shifting, Hack - Interfered). Tóm tắt từ bộ kỹ năng.', 'system'),
    'Spoofing Program': ('Các hiệu ứng Lucy chọn trong Protocol Interface, tiêu tốn RAM.', 'system'),
    'Protocol Interface': ('Giao diện kỹ năng của Lucy trong Resonance Liberation.', 'system'),
    'Algorithm Compaction': ('Trạng thái thay đổi Basic Attack của Lucy.', 'mode'),
    'Ichor Blade': ('Lưỡi kiếm Luuk Herssen triệu hồi.', 'summon'),
    'Afflatus': ('Tài nguyên tích lũy của Zhezhi.', 'resource'),
    'Lumiflow': ('Tài nguyên tích lũy của Lynae, dùng cho Spark Collision.', 'resource'),
    'Overflow': ('Thanh tài nguyên đầy trong Optical Sampling Stage của Lynae.', 'resource'),
    'Optical Sampling Stage': ('Pha tích lũy Overflow của Lynae.', 'system'),
    'Spark Collision': ('Đòn đánh đặc biệt của Lynae, mạnh dần theo Lumiflow.', 'skill'),
    'Golden Reflux': ('Cơ chế cộng dồn/lượt sạc của Luuk Herssen.', 'system'),
    'Solo Concert': ('Trạng thái biểu diễn của Ciaccona sau Basic Attack Stage 4.', 'mode'),
    'Ensemble Sylph': ('Cơ chế triệu hồi/cộng hưởng của Ciaccona.', 'summon'),
    'Ephemeral Transcendence': ('Trạng thái đặc biệt của Qingxiao sau khi tiêu hao Qin Heart và Sword Cadence.', 'mode'),
    'Qin Heart': ('Tài nguyên tích lũy của Qingxiao.', 'resource'),
    'Sword Cadence': ('Tài nguyên tích lũy của Qingxiao.', 'resource'),
    'Stringblade': ('Dạng vũ khí/chiêu thức của Qingxiao.', 'skill'),
    'Involuntary Sharing': ('Hiệu ứng Lucy cấp cho Resonator trong đội, cho phép thấy mục tiêu sau vật cản.', 'system'),
}


# Resonator-specific mechanics: only linked on their owners' pages, so a common
# word (e.g. "Manifest" inside Hsin's "Heart Manifest") never opens another
# character's explanation. Terms not listed here are shared/global.
OWNERS = {
    'jinhsi': ['Incarnation', 'Ordination Glow', 'Eras in Unity'],
    'aemeath': ['Form Switch', 'Stardust Resonance', 'Heavenfall Edict'],
    'lynae': ['Kaleidoscopic Parade', 'Lumiflow', 'Overflow', 'Optical Sampling Stage', 'Spark Collision'],
    'camellya': ['Blossom Mode', 'Crimson Blossom'],
    'zani': ['Inferno Mode'],
    'chisa': ['Chainsaw Mode'],
    'changli': ['True Sight'],
    'hsin': ['Heart Manifest'],
    'calcharo': ['Deathblade Gear'],
    'cartethyia': ['Fleurdelys', 'Manifest'],
    'lucilla': ['Reminiscence', 'Trace', 'Photos'],
    'lucy': ['Payload', 'Spoofing Program', 'Protocol Interface', 'Algorithm Compaction', 'Involuntary Sharing'],
    'luuk-herssen': ['Ichor Blade', 'Golden Reflux'],
    'zhezhi': ['Afflatus'],
    'ciaccona': ['Solo Concert', 'Ensemble Sylph'],
    'qingxiao': ['Ephemeral Transcendence', 'Qin Heart', 'Sword Cadence', 'Stringblade'],
}
# English summaries (same meaning as the Vietnamese ones above) for the EN UI.
SUMMARY_EN = {
    'Concerto Energy': "Gauge showing how ready the outgoing Resonator's Outro Skill and the incoming Resonator's Intro Skill are.",
    'Resonance Energy': 'Resource that, when maxed out, allows Resonance Liberation to be cast.',
    'Resonance Mode': 'Mechanic that lets Resonators switch between applying different statuses / dealing different damage types.',
    'Off-Tune Level': 'Gauge built up on a target affected by Tune Strain; when full, Tune Break can be triggered.',
    'Tune Strain': 'A subset of Tune Break: Tune Strain - Shifting marks the target; once it is Tune Broken the mark becomes Tune Strain - Interfered and Resonators with Tune Strain Response deal more damage to it.',
    'Tune Break': 'A Forte type that can be triggered manually once an enemy enters the Mistune state. Three branches: Tune Strain, Tune Rupture and Hack.',
    'Tune Rupture': 'A subset of Tune Break: Tune Rupture - Shifting marks the target; once it is Tune Broken the mark detonates for one massive hit and the target enters Tune Rupture - Interfered.',
    'Tune Break Boost': 'Stat that strengthens Tune Break; Resonators with Tune Strain Response gain total DMG increase from Tune Break Boost.',
    'Negative Status': 'Stackable damage-over-time effects and debuffs that can hit both enemies and Resonators: Spectro Frazzle, Aero Erosion, Havoc Bane, Fusion Burst, Glacio Chafe, Electro Flare.',
    'Spectro Frazzle': 'Spectro Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Aero Erosion': 'Aero Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Havoc Bane': 'Havoc Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Fusion Burst': 'Fusion Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Glacio Chafe': 'Glacio Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Electro Flare': 'Electro Negative Status (stackable). Its exact effect depends on each kit: see the quotes below.',
    'Coordinated Attack': 'Supplemental attack automatically executed by off-field Resonators alongside the on-field Resonator.',
    'Echo Skill': 'Active skill from the Echo in the main slot; some Resonators (e.g. Phrolova, Qiuyuan) have attacks counted as Echo Skill DMG.',
    'Vibration Strength': 'Enemy mechanic: reducing Vibration Strength forces the enemy into an immobilized state for a while, taking increased damage.',
    'All-DMG Amplification': 'Increases the damage of every type of attack.',
    'DMG Amplification': 'Final damage amplification multiplier, separate from DMG Bonus.',
    'Stagnate': 'Slows down targets within a certain range (Stagnation combat role).',
    'Interfered': 'Enemy state after a target marked with Shifting is Tune Broken (Tune Strain - Interfered / Tune Rupture - Interfered); Resonators with the matching Response react to it.',
    'Shifting': 'Tune Strain - Shifting / Tune Rupture - Shifting mark applied by some Resonators; it does nothing on its own and turns into Interfered when the target is Tune Broken. Lasts 25s.',
    'Mistune': 'Enemy state in which Tune Break can be triggered manually.',
    'Interruption Resistance': "Hidden attribute: a Resonator's or enemy's ability not to be interrupted by the opponent's attacks.",
    'Incarnation': "Jinhsi's transformed state; replaces Basic/Heavy/Resonance Skill and Dodge with Incarnation versions, ending after Incarnation - Basic Attack Stage 4.",
    'Ordination Glow': "Effect Jinhsi gains after Incarnation ends, boosting her moveset.",
    'Eras in Unity': 'Resonance effect Jinhsi grants nearby Resonators while she is in the team.',
    'Form Switch': 'Switching between Aemeath and Mech; each form has its own moveset and mechanics.',
    'Stardust Resonance': 'Buff state Aemeath gains after Resonance Liberation.',
    'Heavenfall Edict': "Aemeath's enhanced Heavy Attack state after Resonance Liberation.",
    'Kaleidoscopic Parade': "Lynae's alternate moveset state with its own Basic/Heavy/Dodge Counter.",
    'Blossom Mode': "Camellya's special combat state.",
    'Crimson Blossom': "Stacks/special effect in Camellya's Blossom Mode.",
    'Inferno Mode': "Zani's special state that changes her Resonance Skill and moveset.",
    'Chainsaw Mode': "Chisa's special state; some skills are locked while in it.",
    'True Sight': 'State Changli gains after Basic Attack Stage 4, lasting 12s.',
    'Unison': 'Effect/Resonance Mode shared by some Resonators (Hsin, Jinhsi, Suoming, Lily…); with Unison, Unison Response can be triggered. Summary from the kits.',
    'Heart Manifest': "Hsin's state: casting Formshift unfurls the Manifold Sanctum, Hsin turns into Illumining Form and enters Heart Manifest; returning to Answering Form exits it. Summary from the kit.",
    'Deathblade Gear': "Calcharo's state after Resonance Liberation that changes his moveset.",
    'Fleurdelys': "Cartethyia's transformed form when HP drops below 50%, unlocking new moves.",
    'Manifest': 'State Cartethyia gains after turning into Fleurdelys.',
    'Reminiscence': "Lucilla's special state that changes her Intro/Resonance Skill.",
    'Trace': "Lucilla's accumulated resource.",
    'Photos': 'Three icons Lucilla collects to unlock her Resonance Liberation.',
    'Payload': "Lucy's dash-type Resonance Skill.",
    'Hack': 'Effect on targets used by Lucy and Rebecca (Hack - Shifting, Hack - Interfered). Summary from the kits.',
    'Spoofing Program': "Effects Lucy selects in the Protocol Interface, costing RAM.",
    'Protocol Interface': "Lucy's skill interface during Resonance Liberation.",
    'Algorithm Compaction': "State that changes Lucy's Basic Attack.",
    'Ichor Blade': 'Blade summoned by Luuk Herssen.',
    'Afflatus': "Zhezhi's accumulated resource.",
    'Lumiflow': "Lynae's accumulated resource, used for Spark Collision.",
    'Overflow': "Resource gauge filled during Lynae's Optical Sampling Stage.",
    'Optical Sampling Stage': "Lynae's phase for building up Overflow.",
    'Spark Collision': "Lynae's special attack, stronger with more Lumiflow.",
    'Golden Reflux': "Luuk Herssen's stacking/charge mechanic.",
    'Solo Concert': "Ciaccona's performance state after Basic Attack Stage 4.",
    'Ensemble Sylph': "Ciaccona's summon/resonance mechanic.",
    'Ephemeral Transcendence': "Qingxiao's special state after consuming Qin Heart and Sword Cadence.",
    'Qin Heart': "Qingxiao's accumulated resource.",
    'Sword Cadence': "Qingxiao's accumulated resource.",
    'Stringblade': "Qingxiao's weapon form / moveset.",
    'Involuntary Sharing': 'Effect Lucy grants team Resonators, letting them see targets behind obstacles.',
}
# Summaries taken from the Wuthering Waves Wiki "Terminology" pages.
WIKI_TERMS = {'Concerto Energy', 'Resonance Energy', 'Resonance Mode', 'Tune Strain', 'Tune Break', 'Tune Rupture',
              'Tune Break Boost', 'Negative Status', 'Spectro Frazzle', 'Aero Erosion', 'Havoc Bane', 'Fusion Burst',
              'Glacio Chafe', 'Electro Flare', 'Coordinated Attack', 'Echo Skill', 'Vibration Strength', 'Stagnate',
              'Interfered', 'Shifting', 'Mistune', 'Interruption Resistance'}
missing_en = [t for t in CURATED if t not in SUMMARY_EN]
assert not missing_en, f'SUMMARY_EN missing: {missing_en}'

# Distinct named things that merely contain a mechanic's name. They are matched
# first (longest match wins) and rendered as plain text, so e.g. "Unison" inside
# "Unison Boon" does not open the Unison explanation.
NO_LINK = [
    'Unison Boon', 'Unison Response', 'Unison Reponse', 'Manifold Unison',
    'Tune Rupture Response', 'Hack Response',
]
# Inflected forms that should link to the same mechanic.
ALIASES = {'Stagnate': ['Stagnates', 'Stagnated', 'Stagnating', 'Stagnation']}
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
