"""Context-aware fix pass for the Vietnamese skill descriptions.

Machine translation turned many in-game proper nouns into Vietnamese
("Huntress" -> "Nữ Thợ Săn", "Compose" -> "Soạn thư", ...). The project rule is
that skill names and game terms stay in English, so this script restores them.

Every rule is gated on the aligned English line: a Vietnamese rendering is only
replaced when the same line in the source contains the English term. That keeps
the pass grounded in the source data instead of guessing.

Usage:
    python scripts/fix_context.py --dry-run   # print every replacement
    python scripts/fix_context.py             # write data/characters.json
"""

import argparse
import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'characters.json'
DATE = datetime.date.today().isoformat()

# (vi pattern, en must match, replacement)
TERM_RULES = [
    # --- in-game stat terms that must stay English (over-translated by MT) ---
    (r'(?:Tiền|Phần) thưởng ((?:Spectro|Havoc|Aero|Electro|Fusion|Glacio) DMG)', r'\bDMG Bonus\b', r'\1 Bonus'),
    (r'DMG (?:Phần|Tiền) thưởng', r'\bDMG Bonus\b', 'DMG Bonus'),
    (r'ATK (?:Phần|Tiền) thưởng', r'\bATK Bonus\b', 'ATK Bonus'),
    (r'Nhận thêm (\d+%) (Spectro|Havoc|Aero|Electro|Fusion|Glacio) DMG(?! Bonus)', r'\bGain \d+% \w+ DMG Bonus', r'Nhận \1 \2 DMG Bonus'),
    (r'đều được Khuếch đại DMG thêm (\d+%)', r'DMG Amplified', r'đều có DMG được Amplified thêm \1'),
    (r'được khuếch đại thêm (\d+(?:[.,]\d+)?%)', r'\bAmplified\b', r'được Amplified thêm \1'),
    (r'được khuếch đại (\d+(?:[.,]\d+)?%)', r'\bAmplified\b', r'được Amplified thêm \1'),
    (r'khuếch đại (\d+%) ([\w .-]+? DMG)', r'\bDMG Amplification\b', r'\1 \2 Amplification'),
    (r'DMG Khuếch đại', r'\bDMG Amplification\b', 'DMG Amplification'),
    (r'Tất cả DMG', r'\bAll DMG\b', 'All DMG'),
    (r'Trạng thái Tiêu cực', r'\bNegative Status', 'Negative Status'),
    (r'Tắt-Tune', r'\bOff-Tune\b', 'Off-Tune'),
    (r'Mid-air Tấn công', r'\bMid-air Attack', 'Mid-air Attack'),
    (r'Tấn công trên không(?! trung)', r'\bMid-air Attacks?\b', 'Mid-air Attack'),
    (r'\blá chắn\b', r'\bShield', 'Shield'),
    (r'Huyền Linh', r'\bXuanling\b', 'Xuanling'),
    (r'Ngôi sao của Chamuel', r"Chamuel.s Star", "Chamuel's Star"),
    (r'Phân tán', r'\bDispersion\b', 'Dispersion'),
    (r'\bNé\b(?! tránh)', r'\bDodge\b', 'Dodge'),
    # --- "stack" as a noun is "tầng" (the verb "cộng dồn" stays) ---
    (r'điểm cộng dồn', r'\bstacks?\b', 'tầng'),
    (r'ngăn xếp', r'\bstacks?\b', 'tầng'),
    (r'(\d+) cộng dồn\b', r'\bstacks?\b', r'\1 tầng'),
    (r'\b(mỗi|tất cả|các) cộng dồn\b', r'\bstacks?\b', r'\1 tầng'),
    (r'Phần thưởng DMG Multiplier', r'\bbonus DMG Multiplier\b', 'DMG Multiplier cộng thêm'),
    (r'mang lại phần thưởng DMG Multiplier', r'\bbonus DMG Multiplier\b', 'mang lại DMG Multiplier cộng thêm'),
    (r'các phần thưởng sau', r'\bbonuses\b', 'các hiệu ứng cộng thêm sau'),
    (r'Khuếch đại', r'\bAmp\w*fy|\bAmplifies\b', 'Amplify'),
    (r'Xuân Linh', r'\bXuanling\b', 'Xuanling'),
    (r'được xử lý trực tiếp bởi', r'\bdirectly dealt by\b', 'gây ra trực tiếp bởi'),
    (r'Outro Skill của Outro Skill', r"Galbrena's Normal Attack", 'Outro Skill của Galbrena'),
    (r"Amplify Resonator's (\w+) DMG đến", r"Amplify the incoming Resonator's \w+ DMG", r'Amplify \1 DMG của Resonator đến'),
    (r'Trước Yangyang: Basic Attack', r"Xuanling's Basic Attack", 'Trước khi Yangyang: Xuanling dùng Basic Attack'),
    (r'(?:là )?không thể xếp chồng(?: lên nhau)?', r'stack', lambda m: ('K' if m.group(0)[0] == 'K' else 'k') + 'hông cộng dồn'),
    (r'xếp chồng', r'\bstack', 'cộng dồn'),
    # --- "deal"/"switched out" mistranslations (AGENTS.md §2) ---
    (r'được xử lý bởi', r'\bdealt by\b', 'gây ra bởi'),
    (r'do (\S+) xử lý', r'\bdealt by\b', r'do \1 gây ra'),
    (r'DMG lấy từ', r'\bDMG taken from\b', 'DMG phải nhận từ'),
    (r'tắt sân đấu', r'\bswitched off\b', 'rời sân'),
    (r'\bbị tắt\b', r'\bswitched (?:out|off)\b', 'rời sân'),
    (r'\b(Resonator) tắt\b', r'\bswitched (?:out|off)\b', r'\1 rời sân'),

    # --- Resonator / Resonance naming ---
    (r'Người cộng hưởng', r'Res\w*ators?\b', 'Resonators'),
    (r'Cộng hưởng Apex', r'\bApex Resonance\b', 'Apex Resonance'),
    (r'Heavy Attack Cộng hưởng', r'\bHeavy Attack Resonance\b', 'Heavy Attack Resonance'),
    (r'Vòng quay cộng hưởng', r'\bResonating Spin\b', 'Resonating Spin'),
    (r'Tiếng (?:vang|vọng) cộng hưởng', r'\bResonating Echoes\b', 'Resonating Echoes'),
    (r'Mạch cộng hưởng Sinner\'s Mark', r'\bResonance Circuit Sinner\'s Mark\b', "Resonance Circuit Sinner's Mark"),
    # --- Zani ---
    (r'Bình minh', r'\b(?:Daybreak|Dawning)\b', None),  # ordered, see ordered_daybreak
    (r'Siêu phàm là Mặt trời', r'\bSublime is the Sun\b', 'Sublime is the Sun'),
    (r'Sublime là Mặt trời', r'\bSublime is the Sun\b', 'Sublime is the Sun'),
    (r'Thanh kiếm của Lời thề vĩnh cửu', r'\bSword of Eternal Oath\b', 'Sword of Eternal Oath'),
    (r'Khúc dạo đầu', r'\bOverture\b', 'Overture'),
    (r'Bước lùi', r'\bBackstep\b', 'Backstep'),
    (r'Undying Sunlight: Tấn công', r'Undying Sunlight: Strike', 'Undying Sunlight: Strike'),
    (r'Undying Sunlight: Đánh', r'Undying Sunlight: Strike', 'Undying Sunlight: Strike'),
    (r'Undying Sunlight: (?:Bước nhảy|Nhảy)', r'Undying Sunlight: Leap', 'Undying Sunlight: Leap'),
    (r'Aureole of Execution: Nhẫn', r'Aureole of Execution: Ring', 'Aureole of Execution: Ring'),
    (r'Aureole of Execution: Vi phạm', r'Aureole of Execution: Breach', 'Aureole of Execution: Breach'),
    (r'Aureole of Execution: (?:Ánh sáng chói|Ánh chói|Chói)', r'Aureole of Execution: Glare', 'Aureole of Execution: Glare'),
    (r'Severing Note: Phán quyết', r'Severing Note: Judgement', 'Severing Note: Judgement'),
    (r'\bCơ Khí\b', r'\bMech\b', 'Mech'),
    (r'Màn đêm buông xuống', r'\bNightfall\b', 'Nightfall'),
    (r'Ngọn lửa tội lỗi', r'\bSinflame\b', 'Sinflame'),
    (r'Ngọn lửa tẩy rửa', r'\bPurging Flame\b', 'Purging Flame'),
    (r'Ngọn lửa Thanh lọc', r'\bPurging Flame\b', 'Purging Flame'),
    (r'lửa tẩy', r'\bPurging Flame\b', 'Purging Flame'),
    (r'Ngọn lửa', r'\bBlazes?\b', 'Blaze'),
    (r'Hành động có mục tiêu', r'\bTargeted Action\b', 'Targeted Action'),

    # --- Hsin ---
    (r'Ánh sáng đêm', r'\bNightglow\b', 'Nightglow'),
    (r'Sấm sét', r'\bThunderglow\b', 'Thunderglow'),
    (r'Sắc lệnh', r'\bEdict\b', 'Edict'),

    # --- Phrolova ---
    (r'Soạn thư', r'\bCompose\b', 'Compose'),
    (r'Soạn thảo', r'\bCompose\b', 'Compose'),

    # --- Yinlin ---
    (r'Sấm sét Execution', r'\bLightning Execution\b', 'Lightning Execution'),

    # --- Buling ---
    (r'Trigram - Đạt được Núi', r'\bTrigram - Mountain\b', 'Trigram - Mountain'),
    (r'Trigram - Có được sấm sét', r'\bTrigram - Thunder\b', 'Trigram - Thunder'),
    (r'Trigram - (?:Đạt được|Có được|Nhận được) (?:Núi|núi)', r'\bTrigram - Mountain\b', 'Trigram - Mountain'),
    (r'Trigram - (?:Đạt được|Có được|Nhận được) (?:sấm sét|Sấm sét)', r'\bTrigram - Thunder\b', 'Trigram - Thunder'),
    (r'tiêu diệt 2', r'consume the highlighted 2', 'tiêu thụ 2'),
    (r'Ngọn lửa Thanh tẩy', r'\bPurging Flame\b', 'Purging Flame'),
    (r'Trigram - Núi', r'\bTrigram - Mountain\b', 'Trigram - Mountain'),
    (r'Trigram - sấm sét', r'\bTrigram - Thunder\b', 'Trigram - Thunder'),
    (r'2 Quái vật được đánh dấu - Núi', r'2 Trigrams - Mountain', '2 Trigrams - Mountain'),
    (r'2 Quái vật được đánh dấu - Sấm sét', r'2 Trigrams - Thunder', '2 Trigrams - Thunder'),
    (r'Bát [Qq]uái', r'\bTrigrams?\b', 'Trigram'),
    (r'Quái vật', r'\bTrigrams?\b', 'Trigram'),
    (r'\bNúi\b', r'\bTrigram - Mountain\b', 'Mountain'),
    (r'\bsấm sét\b', r'\bTrigram - Thunder\b', 'Thunder'),

    # --- Cartethyia ---
    (r'Bóng [Kk]iếm', r'\bSword Shadows\b', 'Sword Shadows'),

    # --- Galbrena ---
    (r'Máu đổi máu', r'\bBlood for Blood\b', 'Blood for Blood'),
    (r'Lấn chiếm', r'\bEncroach\b', 'Encroach'),
    (r'Tàn phá', r'\bRavage\b', 'Ravage'),

    # --- Rebecca ---
    (r'Nữ Thợ Săn', r'\bHuntress\b', 'Huntress'),
    (r'Thợ săn', r'\bHuntress\b', 'Huntress'),
    (r'\bRuột\b', r'\bGuts\b', 'Guts'),

    # --- Sigrika ---
    (r'Ấn thạch', r'\bRunes?\b', 'Rune'),
    (r'Tin tưởng', r'\bRune: Trust\b', 'Trust'),
    (r'Niềm tin', r'\bRune: Trust\b', 'Trust'),

    # --- Luuk Herssen / Jinhsi / misc proper nouns ---
    (r'Ảo tưởng', r'\bDelusion\b', 'Delusion'),
    (r'\bChất\b', r'\bSubstance\b', 'Substance'),
    (r'Nhiệt huyết', r'\bFervor\b', 'Fervor'),
    (r'Bệ Hạ', r'\bMajesty\b', 'Majesty'),
    (r'Hoàng thượng', r'\bMajesty\b', 'Majesty'),
    (r'Thăng thiên', r'\bAscendancy\b', 'Ascendancy'),
    (r'Thăng hoa', r'\bAscendancy\b', 'Ascendancy'),
    (r'Làm trì trệ', r'\bStagnat', 'Stagnate'),
    (r'\btrì trệ\b', r'\bStagnat', 'Stagnate'),
    (r'Lời thú tội', r'\bConfession\b', 'Confession'),
    (r'Xưng tội', r'\bConfession\b', 'Confession'),
    (r'Xá tội', r'\bAbsolution\b', 'Absolution'),
    (r'Lời xưng tội', r'\bConfession\b', 'Confession'),
    (r'Sẵn sàng', r'\bReadiness\b', 'Readiness'),
    (r'Tình cảm', r'\bSentience\b', 'Sentience'),
    (r'Sự hiển linh soi sáng', r'\bIlluminous Epiphany\b', 'Illuminous Epiphany'),
    (r'Tái sinh', r'\bReincarnate\b', 'Reincarnate'),
    (r'Trí tưởng tượng', r'\bImagination\b', 'Imagination'),
    (r'Tăng âm', r'\bTonic\b', 'Tonic'),
    (r'Sương Giá', r'\bBitterfrost\b', 'Bitterfrost'),
    (r'Cống hiến', r'\bDedication\b', 'Dedication'),
    (r'Bảo trợ', r'\bAuspice\b', 'Auspice'),
    (r'Bảo trợ', r'\bAuspices\b', 'Auspices'),
    (r'Đồ cổ', r'\bAntique\b', 'Antique'),
    (r'Dây Gió', r'\bWindstrings?\b', 'Windstrings'),
    (r'Soliskin tới Trợ giúp', r'Soliskin to the Aid', 'Soliskin to the Aid'),
    (r'Sợi đốt', r'\bIncandescence\b', 'Incandescence'),
    (r'Cung Trăng', r'\bMoonbow\b', 'Moonbow'),
    (r'Trạng thái ngưỡng', r'\bThreshold State\b', 'Threshold State'),
    (r'Chế độ cơ bản', r'\bBaseline Mode\b', 'Baseline Mode'),
    (r'Cố định', r'\bFixation\b', 'Fixation'),
    (r"Dấu ấn Lữ Khách", r"\bWayfarer's Mark\b", "Wayfarer's Mark"),
    (r'Dấu ấn của Người lữ hành', r"\bWayfarer's Mark\b", "Wayfarer's Mark"),
    (r'Phước lành', r'\bBlessing\b', 'Blessing'),
    (r'Đảo ngược', r'\bInversion\b', 'Inversion'),
    (r'Tăng dần', r'\bAscendant\b', 'Ascendant'),
    (r'\bSốc\b', r'\bShock\b', 'Shock'),
    (r'Tiểu Chu Thiên', r'\bMinor Zhoutian\b', 'Minor Zhoutian'),
    (r'Bài hát xuyên vũ trụ', r'\bSongs Across the Universe\b', 'Songs Across the Universe'),
    (r'BÙM! Pháo hoa!', r'BOOM! Fireworks!', 'BOOM! Fireworks!'),
    (r'Chế độ cộng hưởng', r'\bResonance Modes?\b', 'Resonance Mode'),
    (r'Chế độ Tiêu điểm Vàng', r'\bYellow Spotlight Mode\b', 'Yellow Spotlight Mode'),
    (r'Lấp lánh', r'\bGlitter\b', 'Glitter'),
    (r'Tia lửa', r'\bSparks\b', 'Sparks'),
    (r'Cô gái đạt được điều mình muốn!', r'\bA Girl Gets What She Wants!\b', 'A Girl Gets What She Wants!'),
    (r'Quá sốc', r'\bOvershock\b', 'Overshock'),
    (r'Phiền toái', r'\bAnnoyance\b', 'Annoyance'),
    (r'Khó chịu', r'\bAnnoyance\b', 'Annoyance'),
    (r'Phép thuật', r'\bConjuration\b', 'Conjuration'),
    (r'Cải tiến', r'\bImprovised\b', 'Improvised'),
    (r'Cải tiến', r'\bRevamp\b', 'Revamp'),
    (r'Khả năng tiêu diệt', r'\bEradication\b', 'Eradication'),
    (r'(Spectro|Havoc|Aero|Electro|Fusion|Glacio) sát thương', r'(?:Spectro|Havoc|Aero|Electro|Fusion|Glacio) DMG', r'\1 DMG'),
    (r'Tiêu diệt', r'\bEradication\b', 'Eradication'),
    (r'Sự (?:tàn phá|Ravage)', r'\bRavage\b', 'Ravage'),
    (r'Sự (?:tiêu diệt|Eradication)', r'\bEradication\b', 'Eradication'),
    (r'Sawring - (?:Quá trình xóa|Xóa)', r'\bSawring - Eradication\b', 'Sawring - Eradication'),
    (r'Sự (?:thăng thiên|thăng hoa|Ascendancy)', r'\bAscendancy\b', 'Ascendancy'),
    (r'Tuyển (?:nữ thợ săn|Huntress)\s*', r'\bHuntress\b', ''),
    (r'Nữ thợ săn', r'\bHuntress\b', 'Huntress'),
    (r'Tuyển nữ thợ săn', r'\bHuntress\b', 'Huntress'),
    (r'Gan dạ', r'\bGuts\b', 'Guts'),
    (r'Hỗ trợ', r'\bParry\b', 'Parry'),
    (r'Tình cảnh', r'\bSituation\b', 'Situation'),
]

# Plain verb/phrasing fixes applied to every VI line.
VERB_RULES = [
    (r'\bĐang truyền\b', 'Đang thi triển'),
    (r'\bđang truyền\b', 'đang thi triển'),
    (r'\bTruyền\b', 'Thi triển'),
    (r'\btruyền\b', 'thi triển'),
    (r'\bĐang đúc\b', 'Đang thi triển'),
    (r'\bđang đúc\b', 'đang thi triển'),
    (r'\bĐúc\b', 'Thi triển'),
    (r'\bđúc\b', 'thi triển'),
    (r'với cái giá là', 'tiêu hao'),
    (r'Trường hợp này của DMG', 'Lượng sát thương này'),
    (r'sát thương của trường hợp này', 'lượng sát thương này'),
    (r'[Tt]rường hợp này của DMG', 'lượng sát thương này'),
    (r'[Tt]rường hợp DMG này', 'lượng sát thương này'),
    (r'các trường hợp bổ sung của (Tune Rupture DMG)', r'các lần \1 bổ sung'),
    (r'1 phiên bản của (Glacio DMG)', r'1 lần \1'),
    (r'Mỗi diễn viên của Oblivion', 'Mỗi lần thi triển Oblivion'),
    (r'bị rời sân', 'rời sân'),
    (r'Làm mục tiêu bị (?:trì trệ|đình trệ|Stagnate)', 'Stagnate mục tiêu'),
    (r'\bniệm phép\b', 'thi triển kỹ năng'),
    (r'\bniệm\b', 'thi triển'),
    (r'tắt trường', 'rời sân'),
    (r'\bthiệt hại\b', 'sát thương'),
    (r'thiệt hại', 'sát thương'),
    (r'chuyển đổi ký tự', 'chuyển đổi Resonator'),
    (r'Chuyển đổi ký tự', 'Chuyển đổi Resonator'),
    (r'(\d+) trường hợp (Tune Rupture DMG)', r'\1 lần \2'),
    (r'trường hợp sát thương', 'lượng sát thương'),
    (r'Trường hợp sát thương', 'Lượng sát thương'),
    (r'Trường hợp thiệt hại', 'Lượng sát thương'),
    (r'\bNhân vật\b', 'Resonator'),
    (r'\bnhân vật\b', 'Resonator'),
]

# Corrupted placeholder tokens. Each entry is (slug, skill name, expected text, replacement).
# The machine translation replaced a word with a stray numeric token like "[[1167]".
TOKEN_FIXES = [
    ('ciaccona', "Singer's Triple Cadenza", 'một lượng [[420] nhất định', 'một lượng Concerto Energy nhất định'),
    ('encore', 'Black & White Woolies', '"[[956]]" của Encore', '"Dissonance" của Encore'),
    ('jingran', 'Malevolent Encounter', 'Chuyển sang [[1035] khác', 'Chuyển sang Resonator khác'),
    ('buling', 'Hexagram Calls, Lightning Falls', '20% [[1167] hiện tại', '20% HP hiện tại'),
    ('buling', 'Hexagram Calls, Lightning Falls', 'Buling hiện tại của HP dưới 1%', 'HP hiện tại của Buling dưới 1%'),
]


def ordered_daybreak(en: str, vi: str) -> str:
    """Daybreak and Dawning share the same Vietnamese rendering; align by order."""
    source = list(dict.fromkeys(re.findall(r'\b(Daybreak|Dawning)\b', en)))
    slots = vi.count('Bình minh')
    if not source or not slots:
        return vi
    parts = vi.split('Bình minh')
    out = parts[0]
    for i, tail in enumerate(parts[1:]):
        term = source[i] if i < len(source) else source[-1]
        out += term + tail
    return out


def is_english_label(en: str) -> bool:
    """True for short title-case labels such as skill/state names."""
    text = en.strip()
    if not text or len(text) > 48 or '.' in text:
        return False
    words = text.replace("'", '').split()
    if len(words) < 1:
        return False
    kept = {'of', 'the', 'and', 'for', 'to', 'in', 'on', 'with', 'a', 'an', 'or', 'from', 'at', 'by'}
    for i, word in enumerate(words):
        if word in {'-', '–', '&'}:
            continue
        if i and word in kept:
            continue
        if not word[:1].isupper():
            return False
    return True


def apply_line(en: str, vi: str) -> str:
    for pattern, must, repl in TERM_RULES:
        if not re.search(must, en):
            continue
        if repl is None:
            vi = ordered_daybreak(en, vi)
            continue
        vi = re.sub(pattern, repl, vi, flags=re.I)
    if re.search(r'\b(?:Daybreak|Dawning)\b', en):
        vi = ordered_daybreak(en, vi)
    for pattern, repl in VERB_RULES:
        vi = re.sub(pattern, repl, vi)
    vi = vi.replace('ResonatorResonator', 'Resonator')
    if is_english_label(en):
        label = en.strip()
        if vi.startswith('• '):
            label = '• ' + label
        vi = label
    return vi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    payload = json.loads(DATA.read_text(encoding='utf-8'))
    characters = payload['characters']
    changes = []

    for c in characters:
        for s in c['skills']:
            for i, (en, vi) in enumerate(zip(s['desc'], s['desc_vi'])):
                new = apply_line(en, vi)
                for slug, skill, old, repl in TOKEN_FIXES:
                    if slug == c['slug'] and skill == s['name'] and old in new:
                        new = new.replace(old, repl)
                if new != vi:
                    changes.append((c['slug'], s['name'], vi, new))
                    s['desc_vi'][i] = new

    print(f'{len(changes)} lines changed in {len({x[0] for x in changes})} characters')
    if args.dry_run:
        for slug, skill, old, new in changes:
            print(f'\n[{slug} / {skill}]')
            print('  -', old)
            print('  +', new)
        print('\nDry run: nothing written.')
        return

    payload['meta']['updated'] = DATE
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Updated {DATA}')


if __name__ == '__main__':
    main()
