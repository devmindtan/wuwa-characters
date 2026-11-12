"""Build data/mechanics.json from the canonical character data.

Each mechanic keeps a short Vietnamese summary plus the first grounded snippet
from the actual kit so the UI never invents explanations.
"""

import json
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
    'Unison': ('Cơ chế cộng hưởng/phối hợp của Hsin, mở Unison Response.', 'mode'),
    'Deathblade Gear': ('Trạng thái sau Resonance Liberation của Calcharo, thay đổi bộ chiêu.', 'mode'),
    'Fleurdelys': ('Dạng biến đổi của Cartethyia khi HP dưới 50%, mở khóa chiêu mới.', 'mode'),
    'Manifest': ('Trạng thái Cartethyia nhận sau khi biến thành Fleurdelys.', 'mode'),
    'Reminiscence': ('Trạng thái đặc biệt của Lucilla, thay đổi Intro/Resonance Skill.', 'mode'),
    'Trace': ('Tài nguyên tích lũy của Lucilla.', 'resource'),
    'Photos': ('Ba biểu tượng Lucilla cần thu thập để mở Resonance Liberation.', 'resource'),
    'Payload': ('Resonance Skill dạng lao tới của Lucy.', 'skill'),
    'Hack': ('Trạng thái đánh dấu mục tiêu của Lucy, có thể gây Shift.', 'system'),
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


def main():
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    chars = payload['characters']
    mechanics = []
    for term, (summary, kind) in CURATED.items():
        count = 0
        users = []
        sample = ''
        for c in chars:
            hit = 0
            for s in c['skills']:
                for en, vi in zip(s['desc'], s['desc_vi']):
                    if term in en or term in vi:
                        hit += 1
                        if not sample:
                            sample = vi if term in vi else en
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
        })
    mechanics.sort(key=lambda m: (-m['count'], m['term']))
    OUT.write_text(json.dumps({'mechanics': mechanics}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wrote {OUT} with {len(mechanics)} mechanics')


if __name__ == '__main__':
    main()
