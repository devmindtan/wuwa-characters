# Wuthering Waves Character Archive — Project Rules

## 1. Phiên bản dữ liệu (bắt buộc)

- `meta.patch` là **bản game mới nhất hiện tại** (đang là **3.8**, phát hành 12/11/2026). Đây là phiên bản duy nhất UI hiển thị; nhân vật không có `version` riêng.
- Khi game ra bản mới: kiểm tra bản mới nhất từ nguồn chính thức/tin tức, cập nhật `meta.patch` và `meta.updated`.
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
- Giao diện có công tắc VI | EN cho toàn trang (lưu trong localStorage). Không viết cứng chuỗi giao diện trong HTML/JS: thêm key vào `public/i18n.js` (cả `vi` và `en`) rồi dùng `t()` / `data-i18n`.
  - VI: mọi tiêu đề, nhãn, nút là tiếng Việt; chỉ tên riêng trong game (tên kỹ năng, loại kỹ năng, nguyên tố, cơ chế, vật phẩm) giữ tiếng Anh. Tiêu đề tab có dòng nhỏ ghi thuật ngữ gốc (Forte, Combat Skills, Resonance Chain...).
  - EN: không còn chữ tiếng Việt nào (trừ tên tác giả). Dữ liệu cần cả hai bản: `summary_vi`/`summary_en` cho cơ chế, `used_for`/`used_for_en` cho references.

## 3. Kiến trúc

- `data/characters.json` là nguồn dữ liệu canonical (JSON, `meta.patch` = bản game hiện tại).
- `app/main.py` là FastAPI server, mở port và trả JSON cho frontend. Frontend không nhúng dữ liệu, chỉ gọi API.
- `public/` chứa HTML/CSS/JS tĩnh. Không chỉnh sửa trực tiếp file sinh tự động (nếu có).
- `scripts/` chứa pipeline extract/dịch/review. Chạy script bằng Python trong `.venv`.
- Dữ liệu bổ sung từ Wuthering Waves Wiki (Fandom, qua MediaWiki API công khai): `scripts/fetch_wiki.py` (cache vào `data/wiki_raw.json`, không commit) → `scripts/merge_wiki.py` ghi `resonance_chain`, `materials`, `references` vào `data/characters.json`.
- Bản dịch Resonance Chain nằm ở `data/translations/resonance_chain_vi.json` (khóa theo tên node, kèm bản EN gốc). Khi EN trên wiki đổi, bản dịch cũ tự bị bỏ và `merge_wiki.py --export-missing FILE` liệt kê node cần dịch lại; dịch xong chạy `review.py` (kiểm tra số dòng và các con số khớp EN).
- Không vượt rào chặn bot (Cloudflare/403) của bất kỳ nguồn nào; nguồn chặn thì dùng nguồn khác hoặc nhờ người dùng.
- Mỗi nhân vật phải có `references` liệt kê nguồn đã dùng cho từng phần dữ liệu.
- Hệ số kỹ năng Lv1–10 (`skills[].scaling`) lấy từ template `Skill Scaling` trên trang từng kỹ năng của wiki, chỉ nhận khi `resonator` của trang khớp nhân vật; giữ nguyên chuỗi giá trị của wiki (ví dụ `31.74%+47.60`), không tự quy đổi. Chi phí từng cấp (`level_costs`) lấy từ trang `<Resonator>/Combat`.
- Chưa có nguồn cho giá trị các nút Stat Bonus trong skill tree: không tự điền số.
- Chạy dự án: `./run.sh` → `http://127.0.0.1:8000`.
- API tối thiểu: `/api/meta`, `/api/characters`, `/api/characters/{slug}`, `/api/mechanics`, `/api/changes`.

## 4. Hiển thị kỹ năng

- Trong mô tả kỹ năng, nếu nhắc tới **tên một kỹ năng khác của cùng nhân vật**, phải tạo liên kết; bấm vào phải cuộn tới đúng section kỹ năng đó và làm nổi bật.
- Nếu nhắc tới **cơ chế đặc biệt** (Tune Strain, Incarnation, Kaleidoscopic Parade, Off-Tune Level...), phải mở bảng/dialog giải thích, kèm các vị trí xuất hiện trong bộ kỹ năng.
- Không link trùng lặp trong cùng một cụm từ; ưu tiên khớp tên dài trước.
- Cơ chế riêng của một nhân vật phải khai báo chủ trong `OWNERS` (`scripts/build_mechanics.py`); UI chỉ link cơ chế đó trên trang của chủ (ví dụ "Manifest" của Cartethyia không được link trong "Heart Manifest" của Hsin).
- Tên riêng chỉ *chứa* tên một cơ chế (Unison Boon, Unison Response, Tune Rupture Response...) phải nằm trong `NO_LINK` để không bị link nhầm; nếu đó là cơ chế quan trọng thì thêm vào `CURATED` với tóm tắt bám dữ liệu.
- Cụm "<Nguyên tố> DMG" (kèm Bonus/Amplification/RES) được tô màu nguyên tố chính thức (Glacio #41AEFB, Fusion #F0744E, Electro #B46BFF, Aero #55FFB5, Spectro #F8E56C, Havoc #E649A6), chỉ đổi màu, không in đậm.
- Sau khi sửa `CURATED`/`OWNERS`/`NO_LINK`, chạy `python scripts/build_mechanics.py` để sinh lại `data/mechanics.json`.
- Popup cơ chế liệt kê các Resonators có cơ chế đó (tính trên trình duyệt từ mô tả EN của kỹ năng + Resonance Chain). Vai trò (Gây/kích hoạt, Tăng tầng/giới hạn, Tăng sát thương, Tận dụng/tiêu hao, Hồi) là phân loại tự động theo từ khóa; UI phải ghi rõ điều này.

## 5. Kiểm chứng trước khi báo xong

- `python scripts/review.py` phải pass (hoặc ghi rõ ngoại lệ đã kiểm tra).
- Test API bằng `curl` và test UI bằng Playwright ở desktop + mobile.
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
