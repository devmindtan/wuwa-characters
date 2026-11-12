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
    'Concerto Energy': ('Năng lượng tích lũy khi chiến đấu, dùng để thi triển Outro Skill khi chuyển Resonator.', 'resource'),
    'Resonance Energy': ('Năng lượng dùng để thi triển Resonance Liberation.', 'resource'),
    'Resonance Mode': ('Chế độ cộng hưởng riêng của từng Resonator, thay đổi hiệu ứng của bộ kỹ năng.', 'system'),
    'Off-Tune Level': ('Thanh tích lũy trên mục tiêu bị Tune Strain; khi đầy có thể kích hoạt Tune Break.', 'system'),
    'Tune Strain': ('Dấu ấn lên mục tiêu; đòn đánh tiếp theo có thể làm đầy Off-Tune Level và kích hoạt Tune Break/Tune Rupture.', 'system'),
    'Tune Break': ('Đòn/hiệu ứng kích hoạt khi Off-Tune Level của mục tiêu đã đầy.', 'system'),
    'Tune Rupture': ('Phản ứng khi phá vỡ Tune Strain, gây sát thương hoặc hiệu ứng theo bộ kỹ năng.', 'system'),
    'Tune Break Boost': ('Chỉ số tăng sát thương Tune Break của một số Resonator.', 'stat'),
    'Negative Status': ('Hiệu ứng bất lợi gây lên mục tiêu, gồm Spectro Frazzle, Aero Erosion, Havoc Bane, Fusion Burst, Glacio Chafe, Electro Flare...', 'status'),
    'Spectro Frazzle': ('Negative Status hệ Spectro, gây sát thương theo thời gian/làm suy yếu mục tiêu.', 'status'),
    'Aero Erosion': ('Negative Status hệ Aero, tích lũy trên mục tiêu và gây sát thương.', 'status'),
    'Havoc Bane': ('Negative Status hệ Havoc, làm mục tiêu nhận thêm sát thương.', 'status'),
    'Fusion Burst': ('Negative Status hệ Fusion, phát nổ gây sát thương.', 'status'),
    'Glacio Chafe': ('Negative Status hệ Glacio, làm chậm/giảm hiệu suất mục tiêu.', 'status'),
    'Electro Flare': ('Negative Status hệ Electro, gây sát thương lan.', 'status'),
    'Coordinated Attack': ('Đòn đánh phối hợp, kích hoạt ngoài lượt điều khiển của Resonator.', 'system'),
    'Echo Skill': ('Kỹ năng có nguồn gốc từ Echo, được tính là Echo Skill DMG.', 'system'),
    'Vibration Strength': ('Độ bền kháng khống chế của mục tiêu; giảm về 0 thì mục tiêu bị choáng.', 'system'),
    'All-DMG Amplification': ('Tăng sát thương của mọi loại đòn đánh.', 'stat'),
    'DMG Amplification': ('Hệ số khuếch đại sát thương cuối, khác với DMG Bonus.', 'stat'),

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
# Distinct named things that merely contain a mechanic's name. They are matched
# first (longest match wins) and rendered as plain text, so e.g. "Unison" inside
# "Unison Boon" does not open the Unison explanation.
NO_LINK = [
    'Unison Boon', 'Unison Response', 'Unison Reponse', 'Manifold Unison',
    'Tune Rupture Response', 'Hack Response',
]
OWNER_OF = {term: slug for slug, terms in OWNERS.items() for term in terms}


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
            'sample_vi': sample[:320],
            'count': count,
            'characters': users,
            'owners': [owner] if owner else [],
        })
    missing_owner = [t for t in OWNER_OF if t not in {m['term'] for m in mechanics}]
    if missing_owner:
        print('warning: owner terms not found in data:', missing_owner)
    mechanics.sort(key=lambda m: (-m['count'], m['term']))
    OUT.write_text(json.dumps({'mechanics': mechanics, 'no_link': NO_LINK}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wrote {OUT} with {len(mechanics)} mechanics')


if __name__ == '__main__':
    main()
