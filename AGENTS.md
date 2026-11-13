# Wuthering Waves Character Archive — Project Rules

## 1. Phiên bản dữ liệu (bắt buộc)

- `meta.patch` là **bản game mới nhất hiện tại** (đang là **3.8**, phát hành 12/11/2026). Đây là phiên bản duy nhất UI hiển thị; nhân vật không có `version` riêng.
- Khi game ra bản mới: kiểm tra bản mới nhất từ nguồn chính thức/tin tức, cập nhật `meta.patch` và `meta.updated`.
  Đồng thời cập nhật số patch/số Resonators trong thẻ `og:*`/`twitter:*`/`<title>` của `public/index.html` và trong `scripts/og/og.html`, rồi chạy `node scripts/og/render.js` để tạo lại `public/assets/og-image.jpg` (ảnh xem trước khi chia sẻ link, 1200×630, domain `https://wuwa-characters.vercel.app/`).
- `changes` của mỗi nhân vật **chỉ ghi khi thông tin của nhân vật trong game thay đổi** (kỹ năng, chỉ số, mô tả gốc EN, ảnh...). Entry: `{ "version": "<bản game>", "date", "note" }`. Không có thay đổi thì để `[]`; UI ẩn mục lịch sử khi rỗng.
- Việc nội bộ của dự án (sửa bản dịch `desc_vi`/`intro_vi`, rà soát, đổi giao diện) **không** ghi vào `changes`.
- Giữ nguyên lịch sử `changes` cũ, chỉ thêm entry mới. Chỉ xóa/sửa entry khi người dùng yêu cầu rõ (commit với `ALLOW_HISTORY_REWRITE=1`).
- Mỗi lần sửa `data/characters.json`, cập nhật `meta.updated`.

## 2. Dịch thuật

- Tên kỹ năng, tên nhân vật và thuật ngữ game giữ nguyên tiếng Anh; phần mô tả là tiếng Việt.
- **Không publish bản dịch máy thô.** Sau khi dịch phải chạy `python scripts/review.py` và rà soát ngữ cảnh thủ công:
  - Đọc toàn bộ dòng bị script đánh dấu.
  - Đọc thêm tối thiểu 10 mục ngẫu nhiên hoặc các mục quan trọng (Resonance Liberation, Forte Circuit, Intro/Outro).
  - Sửa các câu sai nghĩa do dịch máy (ví dụ "Deal DMG" bị dịch thành "giao dịch/thỏa thuận/chia").
- Thuật ngữ cố định: luôn viết **Resonators** (không dùng "cộng hưởng giả", "Bộ cộng hưởng", "Đồ cộng hưởng"). Các thuật ngữ khác lấy theo `data/mechanics.json` và glossary trong `scripts/glossary.py`.
- Giải thích cơ chế phải bám vào dữ liệu nguồn; không tự bịa. Nếu chỉ là tóm tắt, ghi rõ "Tóm tắt".
- Tooltip dùng component tùy chỉnh trong `public/js/tooltip.js` (hiện sau ~60ms, tự nằm trong dialog nếu cần): đặt `data-tip="..."` (hoặc `title`, sẽ tự chuyển), không dựa vào tooltip gốc của trình duyệt.
- Giao diện có công tắc VI | EN cho toàn trang (lưu trong localStorage). Không viết cứng chuỗi giao diện trong HTML/JS: thêm key vào `public/js/i18n.js` (cả `vi` và `en`) rồi dùng `t()` / `data-i18n`.
  - VI: mọi tiêu đề, nhãn, nút là tiếng Việt; chỉ tên riêng trong game (tên kỹ năng, loại kỹ năng, nguyên tố, cơ chế, vật phẩm) giữ tiếng Anh. Tiêu đề tab có dòng nhỏ ghi thuật ngữ gốc (Forte, Combat Skills, Resonance Chain...).
  - EN: không còn chữ tiếng Việt nào (trừ tên tác giả). Dữ liệu cần cả hai bản: `summary_vi`/`summary_en` cho cơ chế, `used_for`/`used_for_en` cho references.

## 3. Kiến trúc

- `data/characters.json` là nguồn dữ liệu canonical (JSON, `meta.patch` = bản game hiện tại).
- `app/main.py` là FastAPI server, mở port và trả JSON cho frontend. Frontend không nhúng dữ liệu, chỉ gọi API.
- `public/` chứa HTML/CSS/JS tĩnh. JS là ES module trong `public/js/` (không cần bước build): `core.js` (state, DOM, tiện ích; không import gì để luôn nạp trước), `i18n.js`, `list.js`, `detail.js`, `kit.js` (các tab), `links.js` (linkify + nhảy tới đoạn), `mechanics.js` (popup cơ chế/đặc điểm), `tooltip.js`, `main.js` (khởi động). Module chỉ có tác dụng phụ phải được `import './x.js'` trong `main.js`. Sau khi sửa `public/styles.css` hoặc `public/js/*.js`, chạy `python scripts/stamp_assets.py` (ghi `?v=<hash>` vào `index.html`; hook chặn commit nếu quên). Không sửa tay `?v=`. Không chỉnh sửa trực tiếp file sinh tự động (nếu có).
- `scripts/` chứa pipeline extract/dịch/review. Chạy script bằng Python trong `.venv`.
- Dữ liệu bổ sung từ Wuthering Waves Wiki (Fandom, qua MediaWiki API công khai): `scripts/fetch_wiki.py` (cache vào `data/wiki_raw.json`, không commit) → `scripts/merge_wiki.py` ghi `resonance_chain`, `materials`, `references` vào `data/characters.json`.
- Bản dịch Resonance Chain nằm ở `data/translations/resonance_chain_vi.json` (khóa theo tên node, kèm bản EN gốc). Khi EN trên wiki đổi, bản dịch cũ tự bị bỏ và `merge_wiki.py --export-missing FILE` liệt kê node cần dịch lại; dịch xong chạy `review.py` (kiểm tra số dòng và các con số khớp EN).
- Không vượt rào chặn bot (Cloudflare/403) của bất kỳ nguồn nào; nguồn chặn thì dùng nguồn khác hoặc nhờ người dùng.
- Mỗi nhân vật phải có `references` liệt kê nguồn đã dùng cho từng phần dữ liệu.
- Thứ tự pipeline: `fetch_wiki.py` → `merge_wiki.py` → `fetch_assets.py` (tải icon kỹ năng/chuỗi/vật phẩm và ảnh icon/card nhân vật về `public/assets/`, trỏ dữ liệu về file nội bộ; ảnh full giữ remote vì nặng) → `apply_overrides.py` → `check_names.py` → `review.py` → `build_mechanics.py` (sinh `data/mechanics.json`) → `build_index.py` (sinh `data/kit_index.json`: đòn con, tag đặc điểm kèm dòng bằng chứng, Resonators của từng cơ chế + vai trò). Frontend không tự phân loại: mọi quy tắc từ khóa nằm trong `scripts/kit_rules.py`, UI chỉ hiển thị `/api/index`.
- Tên riêng trong game (trạng thái, đòn, tài nguyên, tên trong ngoặc kép như "Cruelty") không được dịch. `scripts/check_names.py` phát hiện dòng VI làm mất tên riêng của dòng EN; sửa bằng cách dịch lại dòng đó vào `data/translations/skill_overrides_vi.json` (kèm EN gốc) rồi chạy `apply_overrides.py`.
- Hệ số kỹ năng Lv1–10 (`skills[].scaling`) lấy từ template `Skill Scaling` trên trang từng kỹ năng của wiki, chỉ nhận khi `resonator` của trang khớp nhân vật; giữ nguyên chuỗi giá trị của wiki (ví dụ `31.74%+47.60`), không tự quy đổi. Chi phí từng cấp (`level_costs`) lấy từ trang `<Resonator>/Combat`.
- Chưa có nguồn cho giá trị các nút Stat Bonus trong skill tree: không tự điền số.
- Chạy dự án: `./run.sh` → `http://127.0.0.1:8000`.
- API tối thiểu: `/api/meta`, `/api/summary`, `/api/search`, `/api/characters`, `/api/characters/{slug}`, `/api/mechanics`, `/api/index`, `/api/changes`. Frontend chỉ tải `/api/summary` + `/api/mechanics` + `/api/index` lúc mở trang; `/api/search` tải ngầm; dữ liệu đầy đủ của một nhân vật tải khi mở hồ sơ (`/api/characters/{slug}`, có cache). Không để frontend cần dữ liệu đầy đủ của nhân vật khác: thứ gì cần (ví dụ đoạn trích định nghĩa chéo) phải sinh sẵn ở bước build.

## 4. Hiển thị kỹ năng

- Trong mô tả kỹ năng, nếu nhắc tới **tên một kỹ năng khác của cùng nhân vật**, phải tạo liên kết; bấm vào phải cuộn tới đúng section kỹ năng đó và làm nổi bật.
- Nếu nhắc tới **cơ chế đặc biệt** (Tune Strain, Incarnation, Kaleidoscopic Parade, Off-Tune Level...), phải mở bảng/dialog giải thích, kèm các vị trí xuất hiện trong bộ kỹ năng.
- Không link trùng lặp trong cùng một cụm từ; ưu tiên khớp tên dài trước.
- Nội dung cơ chế do người viết nằm ở `data/mechanics_curated.json` (mỗi mục: `term`, `kind`, `vi`, `en`, `source`, `owner`, `aliases`; danh sách `no_link`). Cơ chế riêng của một nhân vật phải có `owner`; UI chỉ link cơ chế đó trên trang của chủ (ví dụ "Manifest" của Cartethyia không được link trong "Heart Manifest" của Hsin).
- Tên riêng chỉ *chứa* tên một cơ chế (Unison Boon, Unison Response, Tune Rupture Response...) phải nằm trong `no_link` để không bị link nhầm; nếu đó là cơ chế quan trọng thì thêm một mục vào `terms` với tóm tắt bám dữ liệu.
- Cụm "<Nguyên tố> DMG" (kèm Bonus/Amplification/RES) được tô màu nguyên tố chính thức (Glacio #41AEFB, Fusion #F0744E, Electro #B46BFF, Aero #55FFB5, Spectro #F8E56C, Havoc #E649A6), chỉ đổi màu, không in đậm.
- Sau khi sửa `data/mechanics_curated.json` hoặc quy tắc nhận diện, chạy `python scripts/build_mechanics.py` để sinh lại `data/mechanics.json` (test báo lỗi nếu file sinh ra bị cũ).
- Thuật ngữ riêng trong bộ kỹ năng (Aftersound, Resolving Chord, Trance...) được `build_mechanics.py` phát hiện tự động (tiêu đề con trong mô tả kỹ năng, mẫu "X state", "stacks/points of X", "enters X", "X Mode/Form/Stance"), chỉ link trên trang nhân vật có thuật ngữ đó. Popup chỉ trích nguyên văn dòng định nghĩa trong dữ liệu (`defs`), không viết tóm tắt. Từ rác thì thêm vào `AUTO_STOP`. Thuật ngữ kit của nhân vật A được nhắc trong kit nhân vật B dưới dạng trạng thái/tầng ("Hazy Dream state" của Cantarella trong mô tả Phrolova) cũng được link ở trang B, popup trích định nghĩa từ A và ghi tên A.
- Tóm tắt các cơ chế chung (Stagnate, Interfered, Tune Strain, Negative Status...) bám theo mục Terminology của Wuthering Waves Wiki (`"source": "wiki"`, UI ghi nguồn); không tự thêm tác dụng mà nguồn không ghi. Tóm tắt phải đủ thông tin quan trọng nhất: câu định nghĩa, rồi các dòng `• ` nêu giới hạn tầng mặc định, tác dụng mỗi tầng, điều kiện kích hoạt/xóa (UI hiển thị thành danh sách). Số liệu Negative Status lấy từ trang Negative Status của wiki (trích hướng dẫn trong game).
- Đòn con / kỹ năng con không có mục riêng (ví dụ "Basic Attack Hounds Roar", Heavy Attack "Mercy", "Heavy Attack - Thunderoar: Backstep") được nhận diện tự động trong `scripts/kit_rules.py` (`moves_of`) theo mẫu `<loại kỹ năng> <Tên>` và tạo link (gạch nét đứt). Popup giải thích chỉ trích nguyên văn câu định nghĩa trong dữ liệu (dòng "replaced with / to cast…", nếu không có thì lần nhắc đầu tiên), ghi rõ trích từ kỹ năng nào; không tự viết giải thích.
- "Đặc điểm bộ kỹ năng" (Hồi máu, Khống chế, Buff đồng đội, Negative Status...) được phân loại bằng `TRAIT_RULES` trong `scripts/kit_rules.py` (từ khóa trên mô tả EN của kỹ năng + Resonance Chain; cột thứ ba là từ khóa hiển thị cho người dùng). Mỗi tag phải giữ danh sách dòng bằng chứng; bấm tag mở popup liệt kê từng dòng và nhảy tới đúng dòng đó (`data-line`). UI ghi rõ là phân loại tự động. Dòng nêu từ 3 Negative Status trở lên là quy tắc chung, không tính cho tag nguyên tố.
- Đòn con dạng "cast/perform <Tên>" (ví dụ "to cast Movement of Fate and Finality") cũng được `moves_of` nhận diện (`MOVE_CAST`).
- Popup cơ chế liệt kê các Resonators có cơ chế đó (`mechanic_users` trong `scripts/kit_rules.py`, từ mô tả EN của kỹ năng + Resonance Chain). Vai trò (Gây/kích hoạt, Tăng tầng/giới hạn, Tăng sát thương, Tận dụng/tiêu hao, Hồi) là phân loại tự động theo từ khóa; UI phải ghi rõ điều này và có mục mở rộng "Các nhãn vai trò nghĩa là gì?" giải thích từng nhãn kèm từ khóa (từ khóa hiển thị lấy từ cột thứ ba của `ROLE_RULES`).

## 5. Kiểm chứng trước khi báo xong

- `python scripts/review.py` phải pass (hoặc ghi rõ ngoại lệ đã kiểm tra).
- `python -m pytest -q tests` phải pass (cài bằng `pip install -r requirements-dev.txt`). Mỗi lỗi phân loại/link đã sửa phải có một ca mẫu trong `tests/` để không tái phát.
- Test API bằng `curl` và test UI bằng `node tests/e2e/smoke.js` (desktop + mobile; cần server đang chạy, `PLAYWRIGHT_CORE` trỏ tới playwright-core nếu chưa cài global). Test viết thêm thì đưa vào `tests/`, không để ở thư mục tạm.
- Kiểm tra thực tế: mở chi tiết, đổi tab (Skill Tree / Bộ kỹ năng / Resonance Chain / Nguyên liệu), kéo thanh cấp, bấm link kỹ năng, mở popup cơ chế (danh sách Resonators, nhảy tới đoạn có hiệu ứng), đổi EN/VI, back, filter.
- Không tuyên bố "đã kiểm tra" nếu chưa chạy lệnh thật.

## 6. Quy trình Git commit

- Hook nằm trong repo tại `.githooks/`. Mỗi clone mới bật một lần: `git config core.hooksPath .githooks`.
- Trình tự cho mỗi thay đổi:
  1. `git status` + `git diff` — đọc lại toàn bộ diff, chỉ stage file liên quan (`git add <file>`, không `git add -A` mù).
  2. Chạy kiểm chứng ở §5 (review.py, curl API, Playwright desktop + mobile nếu đụng UI).
  3. Commit nhỏ, một mục đích mỗi commit. Thay đổi dữ liệu (`data/`) tách riêng khỏi thay đổi UI/code.
  4. Không `--no-verify` để lách hook; hook fail thì sửa nguyên nhân.
- Định dạng message (hook `commit-msg` kiểm tra): `<type>(<scope>): <tóm tắt>`, tóm tắt ≤ 72 ký tự.
  - type: `feat`, `fix`, `data`, `i18n`, `ui`, `api`, `docs`, `chore`, `refactor`, `test`.
  - Commit đổi thông tin game của nhân vật ghi bản game trong body, ví dụ: `data(jinhsi): cập nhật kỹ năng theo bản 3.9` + body `Game 3.9: ...`.
- Hook `pre-commit` tự kiểm tra: JSON trong `data/` hợp lệ; `scripts/review.py` pass khi `data/` hoặc `scripts/` đổi; thông tin game của nhân vật đổi (bỏ qua phần dịch tiếng Việt) phải có entry `changes` mới, lịch sử cũ không bị sửa, `meta.updated` được cập nhật; cú pháp JS/Python; không stage `.venv`, `__pycache__`, `data/en_raw.json`.
- Agent chỉ commit/push khi người dùng yêu cầu; làm trên `main` thì tạo branch trước nếu thay đổi lớn.
