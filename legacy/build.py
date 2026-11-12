import json, re, html

with open('/home/devmindtan/wuwa-characters/data_vi.json', encoding='utf-8') as f:
    data = json.load(f)

# ---- light post-processing of the machine translation ----
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
def clean_line(s):
    s = s.strip()
    if not s: return s
    for a, b in FIX:
        s = re.sub(a, b, s, flags=re.I)
    # bullet: capitalize after the bullet
    if s.startswith('• '):
        rest = s[2:].strip()
        if rest: rest = rest[0].upper() + rest[1:]
        s = '• ' + rest
    else:
        s = s[0].upper() + s[1:]
    s = re.sub(r'\s+([.,;:!?])', r'\1', s)
    s = re.sub(r'\.\.+', '.', s)
    return s

INTRO_FIX = [
    (r'Thẩm phán của Jinzhou', 'Magistrate của Jinzhou'),
    (r'Người bạn đời đầu tiên', 'First Mate'),
    (r'Quỷ Độc', 'the Bane'),
    (r'Điều tra viên chính', 'Principal Investigator'),
    (r'nhà tư vấn', 'cố vấn'),
    (r'nhà diễn thuyết', 'diễn giả'),
]
for c in data:
    for s in c['skills']:
        s['desc_vi'] = [clean_line(x) for x in s.get('desc_vi', []) if x.strip()]
        s['desc'] = [clean_line(x) for x in s.get('desc', []) if x.strip()]
    intro = c.get('intro_vi') or ''
    for a, b in INTRO_FIX:
        intro = re.sub(a, b, intro, flags=re.I)
    c['intro_vi'] = intro.strip()

# ---- element / weapon labels ----
EL_VI = {'Spectro':'Quang Phổ','Havoc':'Hỗn Độn','Aero':'Khí','Electro':'Lôi','Fusion':'Nhiệt','Glacio':'Băng'}
WEAP_VI = {'Sword':'Kiếm','Broadblade':'Đại Kiếm','Pistols':'Súng Lục','Gauntlets':'Găng Tay','Rectifier':'Pháp Khí'}
SKILL_VI = {
    'Basic Attack':'Tấn công thường',
    'Resonance Skill':'Kỹ năng cộng hưởng',
    'Resonance Liberation':'Giải phóng cộng hưởng',
    'Forte Circuit':'Mạch Forte',
    'Inherent Skill':'Kỹ năng nội tại',
    'Intro Skill':'Kỹ năng nhập trận',
    'Outro Skill':'Kỹ năng kết trận',
}
for c in data:
    c['elementVi'] = EL_VI.get(c['element'], c['element'])
    c['weaponVi'] = WEAP_VI.get(c['weapon'], c['weapon'])

# featured = Jinhsi if available
featured = next((c for c in data if c['slug'] == 'jinhsi'), data[0])

data_json = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
el_json = json.dumps(EL_VI, ensure_ascii=False)
weap_json = json.dumps(WEAP_VI, ensure_ascii=False)
skill_json = json.dumps(SKILL_VI, ensure_ascii=False)

page = r'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wuthering Waves — Danh bộ Cộng Hưởng Giả</title>
<meta name="description" content="Tổng hợp hồ sơ và bộ kỹ năng của 61 nhân vật Wuthering Waves bằng tiếng Việt.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23070b0e'/%3E%3Crect x='16' y='4' width='17' height='17' transform='rotate(45 16 12.5)' fill='%23d6c4a1'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --ink:#070b0e; --deep:#0a1218; --panel:#0f1a22; --panel2:#13222c;
  --line:rgba(214,196,161,.14); --line2:rgba(214,196,161,.28);
  --text:#e9eef2; --muted:#90a4b4; --soft:#c9d6df;
  --gold:#d6c4a1; --gold2:#f0e3c7;
  --spectro:#f4e6a4; --havoc:#d38af0; --aero:#7de8c0; --electro:#b5a6ff; --fusion:#ff9a7c; --glacio:#9ed8ff;
  --r5:#f0d79a; --r4:#b79cff;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:
  radial-gradient(1100px 600px at 78% -10%, rgba(214,196,161,.10), transparent 60%),
  radial-gradient(900px 500px at 12% 8%, rgba(125,232,192,.06), transparent 55%),
  linear-gradient(180deg,var(--ink),var(--deep) 48%,#070c10);
  color:var(--text);font-family:"Be Vietnam Pro",system-ui,sans-serif;min-height:100vh}
body::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.18;background-image:
  linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
  background-size:56px 56px;mask-image:radial-gradient(circle at 50% 20%,#000 20%,transparent 92%)}
a{color:inherit}
.wrap{max-width:1320px;margin:0 auto;padding:0 24px}
.kicker{margin:0 0 12px;font-size:11px;letter-spacing:.28em;text-transform:uppercase;color:var(--gold)}
h1,h2,h3{font-family:"Cormorant Garamond",serif;font-weight:600;letter-spacing:.01em}
.site-head{display:flex;justify-content:space-between;align-items:center;padding:20px 0;border-bottom:1px solid var(--line);position:relative;z-index:2}
.brand{display:flex;align-items:center;gap:12px;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--soft)}
.brand b{color:var(--gold);font-weight:600}
.brand .dot{width:7px;height:7px;background:var(--gold);transform:rotate(45deg);display:inline-block}
.head-meta{font-size:12px;color:var(--muted);letter-spacing:.06em}

.hero{display:grid;grid-template-columns:1.05fr .95fr;gap:30px;align-items:center;padding:54px 0 44px;border-bottom:1px solid var(--line);position:relative}
.hero h1{font-size:clamp(46px,7vw,92px);line-height:.9;margin:0 0 20px;color:var(--gold2)}
.hero h1 em{font-style:italic;color:var(--text)}
.lede{max-width:56ch;color:var(--muted);line-height:1.8;font-size:15px;margin:0 0 24px}
.hero-stats{display:flex;gap:28px;flex-wrap:wrap}
.hero-stats div{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
.hero-stats strong{display:block;font-family:"Cormorant Garamond",serif;font-size:34px;line-height:1;color:var(--gold2);letter-spacing:0}
.hero-art{position:relative;height:420px;display:flex;align-items:flex-end;justify-content:center}
.hero-art::before{content:"";position:absolute;width:65%;height:65%;border:1px solid var(--line2);transform:rotate(45deg);top:5%;right:8%}
.hero-art img{max-height:420px;max-width:100%;object-fit:contain;filter:drop-shadow(0 26px 40px rgba(0,0,0,.55));position:relative;z-index:1}
.hero-art .art-tag{position:absolute;right:0;bottom:6px;z-index:2;text-align:right;font-size:12px;color:var(--muted);line-height:1.6}
.hero-art .art-tag b{display:block;color:var(--gold2);font-family:"Cormorant Garamond",serif;font-size:24px;font-style:italic}

.toolbar{position:sticky;top:0;z-index:20;margin:22px 0 20px;padding:14px;background:rgba(10,18,24,.82);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:14px}
.toolbar-grid{display:grid;grid-template-columns:1.6fr repeat(3,minmax(150px,1fr));gap:10px}
input,select{width:100%;background:rgba(255,255,255,.03);color:var(--text);border:1px solid var(--line);border-radius:9px;padding:12px 13px;font:inherit;outline:none;transition:border-color .18s, box-shadow .18s}
input::placeholder{color:#6f8494}
input:focus,select:focus{border-color:var(--line2);box-shadow:0 0 0 3px rgba(214,196,161,.10)}
.toolbar-foot{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:10px;color:var(--muted);font-size:12px;letter-spacing:.04em}
.toolbar-foot strong{color:var(--gold2)}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:14px}
.card{position:relative;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:linear-gradient(180deg,rgba(19,34,44,.9),rgba(13,24,31,.98));cursor:pointer;transition:transform .18s,border-color .18s,box-shadow .18s;outline:none}
.card:hover,.card:focus-visible{transform:translateY(-4px);border-color:var(--line2);box-shadow:0 16px 36px rgba(0,0,0,.34)}
.card-media{position:relative;aspect-ratio:3/4;overflow:hidden;background:
  radial-gradient(circle at 50% 18%,var(--tint-soft,rgba(214,196,161,.16)),transparent 62%),
  linear-gradient(180deg,rgba(255,255,255,.035),rgba(0,0,0,.18))}
.card-media img{width:100%;height:100%;object-fit:cover;object-position:top center;display:block;transition:transform .35s ease}
.card:hover .card-media img{transform:scale(1.045)}
.card-media::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 46%,rgba(7,11,14,.88) 100%)}
.card-badge{position:absolute;top:10px;left:10px;z-index:2;font-size:10px;letter-spacing:.14em;text-transform:uppercase;padding:5px 8px;border:1px solid rgba(255,255,255,.18);border-radius:999px;background:rgba(7,11,14,.62);backdrop-filter:blur(4px);color:var(--soft)}
.card-rarity{position:absolute;top:10px;right:10px;z-index:2;font-size:12px;letter-spacing:.1em;color:var(--r5);text-shadow:0 1px 6px rgba(0,0,0,.8)}
.card-rarity.r4{color:var(--r4)}
.card-info{position:absolute;left:0;right:0;bottom:0;z-index:2;padding:14px 14px 13px}
.card-info h3{font-size:26px;line-height:1;margin:0 0 6px;color:var(--gold2)}
.card-info p{margin:0;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.card-info p b{color:var(--soft);font-weight:500}
.card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--el,var(--gold));opacity:.8;z-index:3}

.empty{padding:64px 20px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:14px}

/* ---------- full-page detail ---------- */
#detailView{display:none;padding-bottom:70px}
#detailView.open{display:block}
.detail-top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:20px 0 18px;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:30;background:rgba(7,11,14,.86);backdrop-filter:blur(12px)}
.btn{font:inherit;font-size:13px;color:var(--text);background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:9px;padding:10px 14px;cursor:pointer;transition:border-color .18s,background .18s}
.btn:hover{border-color:var(--line2);background:rgba(255,255,255,.07)}
.btn[aria-pressed="true"]{border-color:var(--gold);color:var(--gold2);background:rgba(214,196,161,.08)}
.profile{display:grid;grid-template-columns:minmax(280px,390px) 1fr;gap:44px;padding:38px 0 0;align-items:start}
.profile-art{position:sticky;top:92px}
.art-frame{position:relative;border:1px solid var(--line2);border-radius:14px;overflow:hidden;background:
  radial-gradient(circle at 50% 30%,var(--tint-soft,rgba(214,196,161,.18)),transparent 70%),
  linear-gradient(180deg,rgba(255,255,255,.04),rgba(0,0,0,.24))}
.art-frame::before{content:"";position:absolute;inset:10px;border:1px solid rgba(255,255,255,.10);border-radius:8px;pointer-events:none;z-index:2}
.art-frame img{width:100%;display:block;object-fit:contain}
.art-caption{display:flex;justify-content:space-between;gap:10px;margin-top:12px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.profile-head h1{font-size:clamp(52px,6vw,84px);line-height:.9;margin:0 0 18px;color:var(--gold2)}
.profile-tags{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}
.tag{font-size:11px;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:var(--soft)}
.tag.el{border-color:transparent;color:#081014;font-weight:600}
.intro{color:var(--muted);line-height:1.8;font-size:14.5px;max-width:70ch;margin:0 0 24px}
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 30px}
.stat{border:1px solid var(--line);border-radius:10px;padding:12px 13px;background:rgba(255,255,255,.02)}
.stat .k{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.stat .v{font-size:15px;font-weight:600;color:var(--soft)}
.stat .v small{display:block;font-size:10px;font-weight:400;color:var(--muted);letter-spacing:.06em;margin-top:2px}
.section-head{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:22px;margin-bottom:18px}
.section-head h2{font-size:38px;line-height:1;margin:0;color:var(--gold2)}
.note{font-size:11px;color:var(--muted);letter-spacing:.06em}
.skill{border-top:1px solid var(--line);padding:18px 0 20px}
.skill:first-child{border-top:none;padding-top:0}
.skill-head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:10px}
.skill-type{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(214,196,161,.32);border-radius:999px;padding:5px 9px;white-space:nowrap}
.skill-head h3{font-size:26px;line-height:1;margin:0;color:var(--text)}
.skill-body{color:var(--muted);font-size:14px;line-height:1.75;max-width:78ch}
.skill-body p{margin:0 0 8px}
.skill-body p.sub{color:var(--soft);font-weight:600;margin:12px 0 4px}
.skill-body ul{margin:4px 0 10px;padding-left:20px}
.skill-body li{margin:3px 0}
.skill-body li::marker{color:rgba(214,196,161,.6)}
.source{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);line-height:1.7}
.source a{color:var(--gold2);text-decoration:none;border-bottom:1px solid rgba(214,196,161,.35)}
footer.page-foot{margin-top:46px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;line-height:1.8}

@media (max-width: 1000px){
  .hero{grid-template-columns:1fr;padding-top:38px}
  .hero-art{height:300px;order:-1}
  .hero-art img{max-height:300px}
  .profile{grid-template-columns:1fr;gap:28px}
  .profile-art{position:relative;top:0;max-width:420px}
  .stat-row{grid-template-columns:repeat(2,1fr)}
}
@media (max-width: 720px){
  .wrap{padding:0 16px}
  .toolbar-grid{grid-template-columns:1fr 1fr}
  .toolbar-grid input{grid-column:1/-1}
  .grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .card-info h3{font-size:22px}
  .hero h1{font-size:52px}
  .profile-head h1{font-size:54px}
  .section-head h2{font-size:32px}
  .detail-top{position:relative}
}
@media (max-width: 420px){
  .grid{grid-template-columns:1fr}
  .stat-row{grid-template-columns:1fr 1fr}
}
@media (prefers-reduced-motion: reduce){
  *{scroll-behavior:auto!important;transition:none!important}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="site-head">
    <div class="brand"><span class="dot"></span><span><b>Wuthering Waves</b> · Character Archive</span></div>
    <div class="head-meta">61 hồ sơ · tiếng Việt</div>
  </header>

  <main id="listView">
    <section class="hero">
      <div class="hero-copy">
        <p class="kicker">Solaris · Resonator Codex</p>
        <h1>Danh bộ<br><em>Cộng Hưởng Giả</em></h1>
        <p class="lede">Tra cứu thông tin và toàn bộ bộ kỹ năng của 61 nhân vật Wuthering Waves. Tên kỹ năng và thuật ngữ game được giữ nguyên tiếng Anh; phần mô tả đã được Việt hóa để dễ theo dõi.</p>
        <div class="hero-stats">
          <div><strong id="stat-count">61</strong>Nhân vật</div>
          <div><strong>6</strong>Nguyên tố</div>
          <div><strong>5</strong>Loại vũ khí</div>
        </div>
      </div>
      <div class="hero-art">
        <img src="__FEATURED_IMG__" alt="__FEATURED_NAME__">
        <div class="art-tag"><b>__FEATURED_NAME__</b>__FEATURED_TAGS__</div>
      </div>
    </section>

    <section class="toolbar" aria-label="Bộ lọc nhân vật">
      <div class="toolbar-grid">
        <input id="q" type="search" placeholder="Tìm theo tên, kỹ năng hoặc mô tả..." aria-label="Tìm kiếm">
        <select id="f-el" aria-label="Nguyên tố"><option value="">Mọi nguyên tố</option></select>
        <select id="f-weap" aria-label="Vũ khí"><option value="">Mọi vũ khí</option></select>
        <select id="f-r" aria-label="Độ hiếm">
          <option value="">Mọi độ hiếm</option>
          <option value="5">5★</option>
          <option value="4">4★</option>
        </select>
      </div>
      <div class="toolbar-foot">
        <span>Đang hiển thị <strong id="shown">0</strong> / 61 nhân vật</span>
        <span>Chọn một thẻ để mở hồ sơ đầy đủ.</span>
      </div>
    </section>

    <section id="grid" class="grid" aria-live="polite"></section>
    <div id="empty" class="empty" style="display:none">Không tìm thấy nhân vật phù hợp với bộ lọc hiện tại.</div>

    <footer class="page-foot">
      Dữ liệu tham chiếu từ <a href="https://www.prydwen.gg/wuthering-waves/characters" target="_blank" rel="noopener noreferrer">prydwen.gg</a>, trích xuất ngày 12/11/2026. Mô tả tiếng Việt là bản dịch tham khảo; thuật ngữ và tên kỹ năng giữ nguyên tiếng Anh để bảo toàn cơ chế game.
    </footer>
  </main>

  <main id="detailView" aria-live="polite">
    <div class="detail-top">
      <button class="btn" id="back">← Danh sách nhân vật</button>
      <button class="btn" id="toggle-en" aria-pressed="false">Bản gốc EN</button>
    </div>
    <article class="profile">
      <aside class="profile-art">
        <div class="art-frame" id="d-frame"><img id="d-img" alt=""></div>
        <div class="art-caption"><span id="d-element"></span><span id="d-weapon"></span></div>
      </aside>
      <div class="profile-body">
        <header class="profile-head">
          <p class="kicker">Hồ sơ cộng hưởng giả</p>
          <h1 id="d-name"></h1>
          <div class="profile-tags" id="d-tags"></div>
          <p class="intro" id="d-intro" hidden></p>
        </header>
        <div class="stat-row" id="d-stats"></div>
        <section>
          <div class="section-head">
            <h2>Bộ kỹ năng</h2>
            <span class="note">Tên kỹ năng &amp; thuật ngữ: EN · Mô tả: VI</span>
          </div>
          <div id="d-skills"></div>
        </section>
        <div class="source" id="d-source"></div>
      </div>
    </article>
    <footer class="page-foot">Bản dịch tiếng Việt có thể chưa phản ánh đầy đủ sắc thái cơ chế. Dùng nút “Bản gốc EN” để đối chiếu nguyên văn.</footer>
  </main>
</div>

<script>
const DATA = __DATA__;
const EL_VI = __EL_VI__;
const WEAP_VI = __WEAP_VI__;
const SKILL_VI = __SKILL_VI__;
const EL_COLOR = {Spectro:'var(--spectro)',Havoc:'var(--havoc)',Aero:'var(--aero)',Electro:'var(--electro)',Fusion:'var(--fusion)',Glacio:'var(--glacio)'};
const COLOR_HEX = {Spectro:'#f4e6a4',Havoc:'#d38af0',Aero:'#7de8c0',Electro:'#b5a6ff',Fusion:'#ff9a7c',Glacio:'#9ed8ff'};

const grid = document.getElementById('grid');
const empty = document.getElementById('empty');
const shown = document.getElementById('shown');
const listView = document.getElementById('listView');
const detailView = document.getElementById('detailView');
const q = document.getElementById('q');
const fEl = document.getElementById('f-el');
const fWeap = document.getElementById('f-weap');
const fR = document.getElementById('f-r');
const toggleEn = document.getElementById('toggle-en');
const backBtn = document.getElementById('back');

let current = null;
let showEn = false;
let savedScroll = 0;

const esc = s => (s??'').toString().replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const stars = r => r ? '★'.repeat(r) : '';
const elColor = el => COLOR_HEX[el] || '#d6c4a1';

function fillSelect(sel, values, labelFn){
  values.forEach(v=>{
    const o=document.createElement('option');
    o.value=v; o.textContent=labelFn(v); sel.appendChild(o);
  });
}
const els = [...new Set(DATA.map(c=>c.element).filter(Boolean))].sort();
const weaps = [...new Set(DATA.map(c=>c.weapon).filter(Boolean))].sort();
fillSelect(fEl, els, v => `${v} · ${EL_VI[v]||''}`);
fillSelect(fWeap, weaps, v => `${v} · ${WEAP_VI[v]||''}`);
document.getElementById('stat-count').textContent = DATA.length;

function cardHTML(c){
  const col = elColor(c.element);
  return `<article class="card" data-slug="${esc(c.slug)}" tabindex="0" role="button" aria-label="Mở hồ sơ ${esc(c.name)}" style="--el:${col};--tint-soft:${col}22">
    <div class="card-media">
      <img src="${esc(c.img_card || c.img_icon)}" alt="${esc(c.name)}" loading="lazy" onerror="this.onerror=null;this.src='${esc(c.img_icon)}'">
      <span class="card-badge">${esc(c.element)}</span>
      <span class="card-rarity ${c.rarity===4?'r4':''}">${stars(c.rarity)}</span>
    </div>
    <div class="card-info">
      <h3>${esc(c.name)}</h3>
      <p><b>${esc(c.element)}</b> · ${esc(c.weapon)}</p>
    </div>
  </article>`;
}

function apply(){
  const term = q.value.trim().toLowerCase();
  const el = fEl.value, w = fWeap.value, r = fR.value;
  const list = DATA.filter(c=>{
    if(el && c.element !== el) return false;
    if(w && c.weapon !== w) return false;
    if(r && String(c.rarity) !== r) return false;
    if(term){
      const blob = [c.name,c.slug,c.element,c.elementVi,c.weapon,c.weaponVi,c.intro,c.intro_vi,
        (c.skills||[]).map(s=>[s.name,(s.desc_vi||[]).join(' '),(s.desc||[]).join(' ')].join(' ')).join(' ')]
        .join(' ').toLowerCase();
      if(!blob.includes(term)) return false;
    }
    return true;
  }).sort((a,b)=> (b.rarity-a.rarity) || a.name.localeCompare(b.name));
  grid.innerHTML = list.map(cardHTML).join('');
  shown.textContent = list.length;
  empty.style.display = list.length ? 'none' : 'block';
}

function lineHTML(line){
  if(line.startsWith('• ')) return {li:true, text:line.slice(2)};
  const short = line.length < 72 && !/[.!?]$/.test(line);
  return {li:false, text:line, sub:short};
}

function renderSkills(){
  const c = current;
  if(!c) return;
  const list = c.skills || [];
  let out = '';
  for(const s of list){
    const lines = (showEn ? s.desc : s.desc_vi) || [];
    let body = '', inList = false;
    for(const line of lines){
      const l = lineHTML(line);
      if(l.li){
        if(!inList){ body += '<ul>'; inList = true; }
        body += `<li>${esc(l.text)}</li>`;
      } else {
        if(inList){ body += '</ul>'; inList = false; }
        body += `<p${l.sub?' class="sub"':''}>${esc(l.text)}</p>`;
      }
    }
    if(inList) body += '</ul>';
    if(!body) body = '<p>Chưa có mô tả chi tiết cho kỹ năng này.</p>';
    out += `<section class="skill">
      <div class="skill-head"><span class="skill-type">${esc(SKILL_VI[s.type]||s.type)}</span><h3>${esc(s.name)}</h3></div>
      <div class="skill-body">${body}</div>
    </section>`;
  }
  document.getElementById('d-skills').innerHTML = out;
}

function openDetail(slug){
  const c = DATA.find(x=>x.slug===slug);
  if(!c){ location.hash = '#/'; return; }
  current = c;
  showEn = false;
  toggleEn.setAttribute('aria-pressed','false');
  toggleEn.textContent = 'Bản gốc EN';
  const col = elColor(c.element);
  document.getElementById('d-frame').style.setProperty('--tint-soft', col + '22');
  const img = document.getElementById('d-img');
  img.src = c.img_full || c.img_card || c.img_icon;
  img.alt = c.name;
  img.onerror = ()=>{ img.onerror=null; img.src = c.img_icon; };
  document.getElementById('d-name').textContent = c.name;
  document.getElementById('d-element').textContent = `${c.element} · ${c.elementVi}`;
  document.getElementById('d-weapon').textContent = `${c.weapon} · ${c.weaponVi}`;
  document.getElementById('d-tags').innerHTML =
    `<span class="tag el" style="background:${col}">${esc(c.element)} · ${esc(c.elementVi)}</span>
     <span class="tag">${esc(c.weapon)} · ${esc(c.weaponVi)}</span>
     <span class="tag" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${stars(c.rarity)}</span>`;
  const introEl = document.getElementById('d-intro');
  if(c.intro_vi){ introEl.textContent = c.intro_vi; introEl.hidden = false; }
  else { introEl.textContent = ''; introEl.hidden = true; }
  document.getElementById('d-stats').innerHTML = `
    <div class="stat"><div class="k">Nguyên tố</div><div class="v" style="color:${col}">${esc(c.element)}<small>${esc(c.elementVi)}</small></div></div>
    <div class="stat"><div class="k">Vũ khí</div><div class="v">${esc(c.weapon)}<small>${esc(c.weaponVi)}</small></div></div>
    <div class="stat"><div class="k">Độ hiếm</div><div class="v" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${c.rarity ? c.rarity+'★' : '—'}</div></div>
    <div class="stat"><div class="k">Kỹ năng</div><div class="v">${(c.skills||[]).length}<small>mục chính</small></div></div>`;
  document.getElementById('d-source').innerHTML = `Nguồn tham khảo: <a href="${esc(c.source)}" target="_blank" rel="noopener noreferrer">${esc(c.source)}</a>`;
  renderSkills();
  savedScroll = window.scrollY;
  listView.style.display = 'none';
  detailView.classList.add('open');
  window.scrollTo(0,0);
  backBtn.focus({preventScroll:true});
}

function closeDetail(){
  current = null;
  listView.style.display = '';
  detailView.classList.remove('open');
  window.scrollTo(0, savedScroll || 0);
}

function route(){
  const m = location.hash.match(/^#\/nhan-vat\/(.+)$/);
  if(m) openDetail(decodeURIComponent(m[1]));
  else closeDetail();
}

grid.addEventListener('click', e=>{
  const card = e.target.closest('.card');
  if(card) location.hash = '#/nhan-vat/' + encodeURIComponent(card.dataset.slug);
});
grid.addEventListener('keydown', e=>{
  if(e.key==='Enter' || e.key===' '){
    const card = e.target.closest('.card');
    if(card){ e.preventDefault(); location.hash = '#/nhan-vat/' + encodeURIComponent(card.dataset.slug); }
  }
});
backBtn.addEventListener('click', ()=>{ location.hash = '#/'; });
toggleEn.addEventListener('click', ()=>{
  showEn = !showEn;
  toggleEn.setAttribute('aria-pressed', String(showEn));
  toggleEn.textContent = showEn ? 'Đang xem EN' : 'Bản gốc EN';
  renderSkills();
});
[q,fEl,fWeap,fR].forEach(el=>el.addEventListener('input', apply));
window.addEventListener('hashchange', route);
document.addEventListener('keydown', e=>{ if(e.key==='Escape' && current) location.hash = '#/'; });

apply();
route();
</script>
</body>
</html>'''

page = page.replace('__DATA__', data_json)
page = page.replace('__EL_VI__', el_json)
page = page.replace('__WEAP_VI__', weap_json)
page = page.replace('__SKILL_VI__', skill_json)
page = page.replace('__FEATURED_IMG__', html.escape(featured.get('img_full') or featured.get('img_card') or featured.get('img_icon') or ''))
page = page.replace('__FEATURED_NAME__', html.escape(featured['name']))
page = page.replace('__FEATURED_TAGS__', html.escape(f"{featured['element']} · {featured['weapon']}"))

with open('/home/devmindtan/wuwa-characters/index.html','w',encoding='utf-8') as f:
    f.write(page)
print('wrote index.html', len(page), 'bytes,', len(data), 'characters')
