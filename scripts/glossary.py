"""Glossary + post-processing rules shared by translation and review scripts."""

import re

# Vietnamese machine-translation fixes. Applied to every description line.
FIX = [
    (r'với cái giá phải trả là', 'tiêu hao'),
    (r'\btruyền Basic Attack\b', 'thi triển Basic Attack'),
    (r'\bNhập Stardust\b', 'vào Stardust'),
    (r'\bNhập Heavenfall\b', 'vào Heavenfall'),
    (r'\bÁnh hào quang tràn trề\b', 'Overflowing Radiance'),
    (r'\bTràn ánh sáng\b', 'Overflowing Radiance'),
    (r'\bTràn Ánh Sáng\b', 'Overflowing Radiance'),
    (r'\bÁnh sáng nóng sáng\b', 'Incandescence'),
    (r'\btấn công tích điện\b', 'Charged Attack'),
    (r'\bGiải phóng sức mạnh của lời kêu gọi\b', 'Giải phóng sức mạnh triệu hồi'),
    (r'\bgửi ([A-Za-z][A-Za-z \-\']+) vào\b', r'đưa \1 vào'),
    (r'\bChia bài\b', 'Gây'),
    (r'\b(?:Thỏa thuận|Giải quyết|Xử lý|Giao dịch)\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)', r'gây \1'),
    (r'\bTất cả DMG Bonus\b', 'All DMG Bonus'),
    (r'\bChuông cộng hưởng\b', 'Resonant Chime'),
    (r'\bTâm Linh Lưỡi Liềm\b', 'Crescent Divinity'),
    (r'\bGiao dịch đã được sửa\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)\b', r'Gây \1 cố định'),
    (r'\bXử lý một trường hợp\s+((?:[A-Z][a-zA-Z]*\s+)?DMG)\b', r'Gây một lần \1'),
    (r'"Quyết tâm"', '"Resolve"'),
    (r'"Giải quyết"', '"Resolve"'),
    (r'\bGiai điệu\b', 'Melody'),
    (r'\bDịch chuyển\b', 'Shift'),
    (r'\bBị can thiệp\b', 'Interfered'),
    (r'\bĐồ cộng hưởng\b', 'Resonator'),
    (r'\bBộ cộng hưởng\b', 'Resonator'),
    (r'\bcộng hưởng giả\b', 'Resonators'),
    (r'\bCộng hưởng giả\b', 'Resonators'),
    (r'\bCộng Hưởng Giả\b', 'Resonators'),
    (r'\bHồi tưởng\b', 'Reminiscence'),
    (r'\bDấu vết\b', 'Trace'),
    (r'\bQuá tải\b', 'Overload'),
    (r'\bBồi thường\b', 'Compensate'),
    (r'\bTải trọng\b', 'Payload'),
    (r'\bBế tắc\b', 'Deadlock'),
    (r'\bChia sẻ không tự nguyện\b', 'Involuntary Sharing'),
    (r'\bCắt bỏ\b', 'Resection'),
    (r'\bTốc biến\b', 'Flash'),
    (r'\bcả 3 Ảnh\b', 'cả 3 Photos'),
]

INTRO_FIX = [
    (r'Thẩm phán của Jinzhou', 'Magistrate của Jinzhou'),
    (r'Người bạn đời đầu tiên', 'First Mate'),
    (r'Quỷ Độc', 'the Bane'),
    (r'Điều tra viên chính', 'Principal Investigator'),
    (r'nhà tư vấn', 'cố vấn'),
    (r'nhà diễn thuyết', 'diễn giả'),
]

# Phrases that must never appear in published Vietnamese text.
BANNED = [
    'cộng hưởng giả',
    'Cộng hưởng giả',
    'Cộng Hưởng Giả',
    'Bộ cộng hưởng',
    'Đồ cộng hưởng',
    'Thỏa thuận ',
    'Giao dịch ',
    'Chia bài',
    'Chia sẻ không tự nguyện',
    'Bị can thiệp',
    'Dịch chuyển',
    'Tải trọng',
    'Bồi thường',
    'Dấu vết',
    'Hồi tưởng',
    'Giai điệu',
    'Quá tải',
    'Bát quái',
    'Bát Quái',
    'Cơ Khí',
    'Ấn thạch',
    'Nhiệt huyết',
    'Nhiệt Huyết',
    'Bệ Hạ',
    'Bệ hạ',
    'Hoàng thượng',
    'Nữ Thợ Săn',
    'Nữ thợ săn',
    'Màn đêm buông xuống',
    'Ngọn lửa tội lỗi',
    'Tăng âm',
    'Sự thăng thiên',
    'Sự thăng hoa',
    'Trigram - Núi',
]


def apply_fixes(text: str) -> str:
    for pattern, repl in FIX:
        text = re.sub(pattern, repl, text, flags=re.I)
    return text


def clean_line(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = apply_fixes(text)
    if text.startswith('• '):
        rest = text[2:].strip()
        if rest:
            rest = rest[0].upper() + rest[1:]
        text = '• ' + rest
    else:
        text = text[0].upper() + text[1:]
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'\.\.+', '.', text)
    return text


def clean_intro(text: str) -> str:
    text = (text or '').strip()
    for pattern, repl in INTRO_FIX:
        text = re.sub(pattern, repl, text, flags=re.I)
    return text
