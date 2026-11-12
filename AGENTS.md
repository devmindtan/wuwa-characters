# Wuthering Waves Character Archive — Project Rules

## 1. Phiên bản dữ liệu (bắt buộc)

- Mốc gốc của dự án là **patch 3.7** (dữ liệu trích ngày 12/11/2026). Mọi hồ sơ mặc định có `version: "3.7"`.
- Từ nay, bất kỳ lần query/cập nhật nào **thay đổi nội dung của một nhân vật** (kỹ năng, mô tả, chỉ số, ảnh, intro...) đều phải:
  1. Tăng `version` của nhân vật đó lên patch tương ứng.
  2. Thêm một entry vào `changes`: `{ "version", "date", "note" }` mô tả ngắn thay đổi.
  3. Cập nhật `meta.patch` và `meta.updated` trong `data/characters.json`.
- Không được sửa dữ liệu nhân vật mà không ghi version. API và UI phải hiển thị patch hiện tại và version của từng nhân vật.
- Khi lên patch mới: giữ nguyên lịch sử `changes`, không ghi đè. Chỉ thêm entry mới.
- Nếu query chỉ đọc/tìm kiếm, không thay đổi dữ liệu thì không cần tăng version.

## 2. Dịch thuật

- Tên kỹ năng, tên nhân vật và thuật ngữ game giữ nguyên tiếng Anh; phần mô tả là tiếng Việt.
- **Không publish bản dịch máy thô.** Sau khi dịch phải chạy `python scripts/review.py` và rà soát ngữ cảnh thủ công:
  - Đọc toàn bộ dòng bị script đánh dấu.
  - Đọc thêm tối thiểu 10 mục ngẫu nhiên hoặc các mục quan trọng (Resonance Liberation, Forte Circuit, Intro/Outro).
  - Sửa các câu sai nghĩa do dịch máy (ví dụ "Deal DMG" bị dịch thành "giao dịch/thỏa thuận/chia").
- Thuật ngữ cố định: luôn viết **Resonators** (không dùng "cộng hưởng giả", "Bộ cộng hưởng", "Đồ cộng hưởng"). Các thuật ngữ khác lấy theo `data/mechanics.json` và glossary trong `scripts/glossary.py`.
- Giải thích cơ chế phải bám vào dữ liệu nguồn; không tự bịa. Nếu chỉ là tóm tắt, ghi rõ "Tóm tắt".

## 3. Kiến trúc

- `data/characters.json` là nguồn dữ liệu canonical (JSON, có version).
- `app/main.py` là FastAPI server, mở port và trả JSON cho frontend. Frontend không nhúng dữ liệu, chỉ gọi API.
- `public/` chứa HTML/CSS/JS tĩnh. Không chỉnh sửa trực tiếp file sinh tự động (nếu có).
- `scripts/` chứa pipeline extract/dịch/review. Chạy script bằng Python trong `.venv`.
- Chạy dự án: `./run.sh` → `http://127.0.0.1:8000`.
- API tối thiểu: `/api/meta`, `/api/characters`, `/api/characters/{slug}`, `/api/mechanics`, `/api/changes`.

## 4. Hiển thị kỹ năng

- Trong mô tả kỹ năng, nếu nhắc tới **tên một kỹ năng khác của cùng nhân vật**, phải tạo liên kết; bấm vào phải cuộn tới đúng section kỹ năng đó và làm nổi bật.
- Nếu nhắc tới **cơ chế đặc biệt** (Tune Strain, Incarnation, Kaleidoscopic Parade, Off-Tune Level...), phải mở bảng/dialog giải thích, kèm các vị trí xuất hiện trong bộ kỹ năng.
- Không link trùng lặp trong cùng một cụm từ; ưu tiên khớp tên dài trước.

## 5. Kiểm chứng trước khi báo xong

- `python scripts/review.py` phải pass (hoặc ghi rõ ngoại lệ đã kiểm tra).
- Test API bằng `curl` và test UI bằng Playwright ở desktop + mobile.
- Kiểm tra thực tế: mở chi tiết, bấm link kỹ năng, mở popup cơ chế, đổi EN/VI, back, filter.
- Không tuyên bố "đã kiểm tra" nếu chưa chạy lệnh thật.
