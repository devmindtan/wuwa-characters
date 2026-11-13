# Wuthering Waves — Resonators Archive

Tra cứu hồ sơ, bộ kỹ năng (Skill Tree có icon gốc, thanh kéo hệ số Lv1–10), Resonance Chain (S1–S6), nguyên liệu và chi phí nâng cấp từng cấp của **61 Resonators** Wuthering Waves bằng tiếng Việt, theo bản game hiện tại.

- Giao diện song ngữ với công tắc **VI | EN** cho toàn trang. Ở VI, tên riêng trong game (kỹ năng, nguyên tố, cơ chế) giữ tiếng Anh, phần mô tả được Việt hóa và rà soát ngữ cảnh; ở EN toàn bộ là bản gốc tiếng Anh.
- Trong mô tả kỹ năng, tên kỹ năng khác của cùng nhân vật là liên kết cuộn tới đúng mục; thuật ngữ cơ chế (Incarnation, Tune Strain…) mở bảng giải thích kèm các vị trí xuất hiện và danh sách các Resonators khác có cùng cơ chế (lọc theo vai trò: gây, tăng tầng, tăng sát thương, tận dụng…).
- Dữ liệu theo **bản game 3.8** (phát hành 12/11/2026). Kỹ năng tham chiếu từ [prydwen.gg](https://www.prydwen.gg/wuthering-waves/characters); Resonance Chain và nguyên liệu từ [Wuthering Waves Wiki](https://wutheringwaves.fandom.com/). Mỗi nhân vật có mục **Tham khảo** ghi rõ nguồn của từng phần.

## Chạy dự án

Cần Python 3 (đã chạy trên 3.12).

```bash
./run.sh
```

Lần đầu, script tự tạo `.venv` và cài `requirements.txt`. Sau đó mở <http://127.0.0.1:8000>. Server chạy với `--reload`, sửa code là tự nạp lại.

## API

| Endpoint | Trả về |
|---|---|
| `GET /api/meta` | Bản game hiện tại, ngày cập nhật, số nhân vật/kỹ năng, số nhân vật có thay đổi |
| `GET /api/characters` | `meta` + danh sách đầy đủ nhân vật |
| `GET /api/characters/{slug}` | Một nhân vật (404 nếu không có), ví dụ `/api/characters/jinhsi` |
| `GET /api/mechanics` | Danh sách cơ chế/thuật ngữ và phần giải thích |
| `GET /api/changes` | Các nhân vật có thay đổi thông tin trong game, kèm lịch sử |
| `GET /api/version` | Bản game hiện tại và ngày cập nhật |
| `GET /api/health` | Kiểm tra server |

Frontend không nhúng dữ liệu, mọi thứ đều lấy qua API.

## Cấu trúc

```
app/main.py            FastAPI: API + phục vụ thư mục public/
data/characters.json   Dữ liệu canonical (meta.patch = bản game hiện tại)
data/mechanics.json    Cơ chế/thuật ngữ, sinh bởi scripts/build_mechanics.py
data/translations/     Bản dịch tiếng Việt của Resonance Chain (kèm bản EN gốc để đối chiếu)
public/                Giao diện tĩnh (index.html, app.js, styles.css)
public/assets/icons/   Icon nguyên tố và vũ khí gốc của game (dùng làm favicon, thẻ, bộ lọc)
scripts/               Pipeline trích xuất, dịch, rà soát
legacy/                Bản dựng cũ, chỉ để tham khảo
.githooks/             Hook kiểm tra trước khi commit
AGENTS.md              Quy tắc dự án (bắt buộc đọc trước khi sửa)
```

## Dữ liệu và phiên bản

`meta.patch` trong `data/characters.json` là bản game mới nhất hiện tại; giao diện chỉ hiển thị phiên bản này.

Mỗi nhân vật có `changes`, **chỉ ghi khi thông tin nhân vật trong game thay đổi** (kỹ năng, chỉ số, mô tả gốc, ảnh…). Không có thay đổi thì để `[]` và trang chi tiết không hiện mục lịch sử:

```json
{
  "slug": "jinhsi",
  "changes": [
    { "version": "3.9", "date": "2026-12-23", "note": "Ví dụ: tăng hệ số Resonance Liberation" }
  ]
}
```

- Sửa bản dịch tiếng Việt hay giao diện không ghi vào `changes`.
- Chỉ thêm entry mới, không sửa/xóa entry cũ.
- Khi game ra bản mới, cập nhật `meta.patch` và `meta.updated`.

Chi tiết xem [AGENTS.md](AGENTS.md) §1.

## Pipeline dữ liệu

Chạy bằng Python trong `.venv`:

| Script | Việc làm |
|---|---|
| `scripts/extract.py` | Tải trang nhân vật từ prydwen.gg, ghi `data/en_raw.json` (file local, không commit). Cần thêm `beautifulsoup4`. |
| `scripts/fix_context.py` | Khôi phục tên riêng/thuật ngữ bị dịch máy về tiếng Anh, dựa trên dòng EN tương ứng. Dùng `--dry-run` để xem trước. |
| `scripts/build_mechanics.py` | Sinh `data/mechanics.json` từ dữ liệu nhân vật. |
| `scripts/fetch_wiki.py` | Lấy Resonance Chain, tổng nguyên liệu, chi phí từng cấp (trang `/Combat`) và hệ số kỹ năng Lv1–10 (trang từng kỹ năng) từ [Wuthering Waves Wiki](https://wutheringwaves.fandom.com/) qua MediaWiki API công khai; cache ở `data/wiki_raw.json` (không commit). `--refresh` để lấy lại toàn bộ. |
| `scripts/merge_wiki.py` | Ghi `resonance_chain`, `materials`, `references` vào `data/characters.json`, ghép bản dịch từ `data/translations/`. `--export-missing FILE` xuất các node chưa có bản dịch. |
| `scripts/fetch_assets.py` | Tải icon kỹ năng, icon nút chuỗi, icon vật phẩm, ảnh icon/card nhân vật về `public/assets/` và trỏ dữ liệu về file nội bộ (ảnh full giữ remote). `--check` chỉ báo còn bao nhiêu ảnh remote. |
| `scripts/check_names.py` | Tìm dòng mô tả tiếng Việt làm mất tên riêng của game (ví dụ "Cruelty" bị dịch thành "Tàn ác"). |
| `scripts/apply_overrides.py` | Áp các dòng dịch lại thủ công từ `data/translations/skill_overrides_vi.json` (chỉ khi bản EN gốc còn khớp). |
| `scripts/review.py` | Kiểm tra chất lượng bản dịch (kỹ năng + Resonance Chain: số dòng, con số khớp EN), glossary, schema, nguyên liệu và references. `--sample N` in N dòng ngẫu nhiên để đọc tay. |
| `scripts/glossary.py` | Glossary và quy tắc hậu xử lý dùng chung. |

Không publish bản dịch máy thô: sau khi dịch phải chạy `python scripts/review.py`, đọc hết các dòng bị đánh dấu và rà thêm một mẫu ngẫu nhiên (xem [AGENTS.md](AGENTS.md) §2).

## Kiểm thử

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q tests          # dữ liệu + quy tắc nhận diện (ca mẫu)
./run.sh &                                    # rồi ở terminal khác:
node tests/e2e/smoke.js                       # UI desktop + mobile (Playwright + Chrome)
BASE_URL=https://wuwa-characters.vercel.app node tests/e2e/smoke.js   # kiểm tra bản production
```

## Đóng góp

Bật hook một lần sau khi clone:

```bash
git config core.hooksPath .githooks
```

- `pre-commit` chặn commit khi JSON hỏng, `review.py` hoặc pytest fail, thông tin game của nhân vật đổi mà thiếu entry `changes`, lịch sử `changes` bị sửa, `meta.updated` chưa cập nhật, lỗi cú pháp JS/Python, hoặc stage nhầm file local.
- `commit-msg` yêu cầu dạng `<type>(<scope>): <tóm tắt>`, ví dụ `ui(detail): sửa popup cơ chế`. Các type: `feat`, `fix`, `data`, `i18n`, `ui`, `api`, `docs`, `chore`, `refactor`, `test`.

Trước khi mở PR, kiểm tra API bằng `curl` và giao diện ở cả desktop lẫn mobile: mở chi tiết, bấm link kỹ năng, mở popup cơ chế, đổi EN/VI, back, filter. Quy trình đầy đủ ở [AGENTS.md](AGENTS.md) §5–6.

## Tác giả

**Nguyễn Khắc Minh Tân** · [devmind.tan@gmail.com](mailto:devmind.tan@gmail.com) · [GitHub](https://github.com/devmindtan/wuwa-characters) · [Facebook](https://www.facebook.com/tan.deptrai.104/)

## Nguồn

- Dữ liệu nhân vật: [prydwen.gg](https://www.prydwen.gg/wuthering-waves/characters).
- Icon nguyên tố và vũ khí: tải từ [Wuthering Waves Wiki (Fandom)](https://wutheringwaves.fandom.com/), là icon gốc trong game.
- Wuthering Waves, hình ảnh nhân vật và icon trong game thuộc bản quyền Kuro Games; đây là dự án tra cứu phi thương mại của người hâm mộ.
