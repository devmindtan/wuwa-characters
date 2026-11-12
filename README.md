# Wuthering Waves — Resonators Archive

Tra cứu hồ sơ và toàn bộ bộ kỹ năng của **61 Resonators** Wuthering Waves bằng tiếng Việt, có quản lý phiên bản theo patch.

- Tên nhân vật, tên kỹ năng và thuật ngữ game giữ nguyên tiếng Anh; phần mô tả được Việt hóa và rà soát ngữ cảnh. Có nút **Bản gốc EN** để đối chiếu.
- Trong mô tả kỹ năng, tên kỹ năng khác của cùng nhân vật là liên kết cuộn tới đúng mục; thuật ngữ cơ chế (Incarnation, Tune Strain…) mở bảng giải thích kèm các vị trí xuất hiện.
- Dữ liệu hiện tại: **patch 3.7**, trích ngày 12/11/2026 từ [prydwen.gg](https://www.prydwen.gg/wuthering-waves/characters).

## Chạy dự án

Cần Python 3 (đã chạy trên 3.12).

```bash
./run.sh
```

Lần đầu, script tự tạo `.venv` và cài `requirements.txt`. Sau đó mở <http://127.0.0.1:8000>. Server chạy với `--reload`, sửa code là tự nạp lại.

## API

| Endpoint | Trả về |
|---|---|
| `GET /api/meta` | Patch hiện tại, ngày cập nhật, số nhân vật/kỹ năng, các version đang có |
| `GET /api/characters` | `meta` + danh sách đầy đủ nhân vật |
| `GET /api/characters/{slug}` | Một nhân vật (404 nếu không có), ví dụ `/api/characters/jinhsi` |
| `GET /api/mechanics` | Danh sách cơ chế/thuật ngữ và phần giải thích |
| `GET /api/changes` | Lịch sử thay đổi theo từng nhân vật |
| `GET /api/version` | Patch, ngày cập nhật, các version |
| `GET /api/health` | Kiểm tra server |

Frontend không nhúng dữ liệu, mọi thứ đều lấy qua API.

## Cấu trúc

```
app/main.py            FastAPI: API + phục vụ thư mục public/
data/characters.json   Dữ liệu canonical (có version từng nhân vật)
data/mechanics.json    Cơ chế/thuật ngữ, sinh bởi scripts/build_mechanics.py
public/                Giao diện tĩnh (index.html, app.js, styles.css)
scripts/               Pipeline trích xuất, dịch, rà soát
legacy/                Bản dựng cũ, chỉ để tham khảo
.githooks/             Hook kiểm tra trước khi commit
AGENTS.md              Quy tắc dự án (bắt buộc đọc trước khi sửa)
```

## Dữ liệu và phiên bản

Mỗi nhân vật có `version` và `changes`:

```json
{
  "slug": "jinhsi",
  "version": "3.7",
  "updated": "2026-11-12",
  "changes": [
    { "version": "3.7", "date": "2026-11-12", "note": "Khởi tạo dữ liệu tại patch 3.7" }
  ]
}
```

Khi sửa nội dung một nhân vật (kỹ năng, mô tả, ảnh, intro…):

1. Tăng `version` của nhân vật lên patch tương ứng.
2. **Thêm** một entry vào `changes`; không sửa hay xóa entry cũ.
3. Cập nhật `meta.patch` và `meta.updated` trong `data/characters.json`.

Chi tiết xem [AGENTS.md](AGENTS.md) §1.

## Pipeline dữ liệu

Chạy bằng Python trong `.venv`:

| Script | Việc làm |
|---|---|
| `scripts/extract.py` | Tải trang nhân vật từ prydwen.gg, ghi `data/en_raw.json` (file local, không commit). Cần thêm `beautifulsoup4`. |
| `scripts/fix_context.py` | Khôi phục tên riêng/thuật ngữ bị dịch máy về tiếng Anh, dựa trên dòng EN tương ứng. Dùng `--dry-run` để xem trước. |
| `scripts/build_mechanics.py` | Sinh `data/mechanics.json` từ dữ liệu nhân vật. |
| `scripts/review.py` | Kiểm tra chất lượng bản dịch, glossary, version và schema. `--sample N` in N dòng ngẫu nhiên để đọc tay. |
| `scripts/glossary.py` | Glossary và quy tắc hậu xử lý dùng chung. |

Không publish bản dịch máy thô: sau khi dịch phải chạy `python scripts/review.py`, đọc hết các dòng bị đánh dấu và rà thêm một mẫu ngẫu nhiên (xem [AGENTS.md](AGENTS.md) §2).

## Đóng góp

Bật hook một lần sau khi clone:

```bash
git config core.hooksPath .githooks
```

- `pre-commit` chặn commit khi JSON hỏng, `review.py` fail, nhân vật đổi nội dung mà thiếu entry `changes`, lịch sử `changes` bị sửa, `meta.updated` chưa cập nhật, lỗi cú pháp JS/Python, hoặc stage nhầm file local.
- `commit-msg` yêu cầu dạng `<type>(<scope>): <tóm tắt>`, ví dụ `ui(detail): sửa popup cơ chế`. Các type: `feat`, `fix`, `data`, `i18n`, `ui`, `api`, `docs`, `chore`, `refactor`, `test`.

Trước khi mở PR, kiểm tra API bằng `curl` và giao diện ở cả desktop lẫn mobile: mở chi tiết, bấm link kỹ năng, mở popup cơ chế, đổi EN/VI, back, filter. Quy trình đầy đủ ở [AGENTS.md](AGENTS.md) §5–6.

## Nguồn

Dữ liệu tham chiếu từ [prydwen.gg](https://www.prydwen.gg/wuthering-waves/characters). Wuthering Waves và các tài sản liên quan thuộc về Kuro Games; đây là dự án tra cứu phi thương mại của người hâm mộ.
