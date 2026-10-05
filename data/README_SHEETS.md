# Đồng bộ Google Sheets – InsideOut HEALTH v4

## Spreadsheet đã gắn sẵn
ID: `1fcR2HFA1E5jalJaZ2gsoIJVgT_INMBQgCRBGfwTuZDo`

Link: https://docs.google.com/spreadsheets/d/1fcR2HFA1E5jalJaZ2gsoIJVgT_INMBQgCRBGfwTuZDo

## Cách cấu hình (bắt buộc để sync thật)

1. Google Cloud Console → tạo project → Enable **Google Sheets API** + **Drive API**
2. Tạo **Service Account** → Download JSON key → đổi tên thành `credentials.json`
3. Copy `credentials.json` vào thư mục `data/` của app
4. Mở Google Sheet ở link trên → **Share** → thêm email của Service Account (quyền **Editor**)
5. (Tuỳ chọn) set env:
   ```bash
   export INSIDEOUT_SHEET_ID="1fcR2HFA1E5jalJaZ2gsoIJVgT_INMBQgCRBGfwTuZDo"
   export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
   ```
6. Cài thư viện:
   ```bash
   pip install gspread google-auth
   ```

## Sheets được tạo tự động

### Sheet `Assessments` (khi user hoàn thành form chi tiết)
Cột gồm:
- timestamp, email, ho_ten, dob, gioi_tinh, ton_giao, sdt, nghe_nghiep, nguoi_gioi_thieu
- sleep_hours, sleep_quality, sleep_difficulty
- nutri_meals, nutri_healthy, nutri_control
- move_freq, move_intensity
- bio_routine, bio_energy, bio_fluctuation
- emo_stress, emo_pressure, emo_understood, emo_share, emo_regulate, emo_express, emo_energy, emo_selfaware
- spirit_body_signal, spirit_selftime
- goals, want_coaching
- score_giac_ngu … score_tinh_than, score_avg, chart_image, chart_scores

`chart_image` là công thức `IMAGE(...)`, hiển thị radar chart trực tiếp trong Google
Sheet. `chart_scores` lưu lại thông số 6 trụ để dễ lọc và đối chiếu. Ảnh được tạo
qua QuickChart từ các điểm số của từng lần assessment.

### Sheet `Checkins` (mỗi lần check-in hàng ngày)
timestamp | email | name | mood | habit_done | habit_title | note | 6 scores

## Luồng user

1. **Đăng ký mới** → bắt buộc làm Assessment đầy đủ → tính điểm 6 trụ → lưu + sync Sheet → xem Bản đồ → chọn habit → dùng app
2. **Đăng nhập** (đã làm assessment) → vào Home luôn
3. **Đăng nhập** (chưa làm assessment) → bắt buộc làm Assessment trước
# Tài khoản và quyền admin

Tài khoản được lưu trong SQLite tại `data/insideout.db` theo mặc định. Bảng `users` có cột `email`, `data` và `role` riêng để dễ xem/chỉnh role trong công cụ quản lý DB. Để dùng PostgreSQL, cài các package trong `requirements.txt` và đặt biến môi trường `DATABASE_URL` thành URL kết nối PostgreSQL (ví dụ `postgresql://user:password@host:5432/dbname`). Khi khởi chạy, ứng dụng tự nhập tài khoản từ `data/users.json` nếu bảng tài khoản còn trống; mật khẩu được chuyển sang dạng băm. Bảng `users` đang dùng JSON cho các trường hồ sơ khác, còn `role` được tách cột.

Đặt `ADMIN_EMAIL` thành email tài khoản cần cấp quyền admin. Email này được cấp quyền khi tạo tài khoản hoặc đăng nhập; admin hiện tại cũng có thể cấp/thu hồi quyền trong mục **Quản trị**. Admin xem bản đồ mới nhất ở `/demo/maps` và các lần gửi đã đăng nhập ở `/admin/maps`. Các lần vẽ của khách chưa đăng nhập không được ghi vào lịch sử gắn với tài khoản.

## Đăng nhập bằng Google

1. Trong Google Cloud Console, tạo OAuth Client ID loại **Web application** và thêm domain ứng dụng vào **Authorized JavaScript origins**.
2. Thêm callback chính xác `https://ten-mien-cua-ban/auth/google/callback` vào **Authorized redirect URIs** (khi chạy local: `http://localhost:5000/auth/google/callback`).
3. Sao chép `.env.example` thành `.env`. Có thể nhập riêng `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET`, hoặc đặt `GOOGLE_OAUTH_CLIENT_FILE` trỏ tới JSON tải từ Google. Đặt `GOOGLE_REDIRECT_URI` trùng chính xác callback đã đăng ký. Nút Google luôn hiện; luồng xác thực chỉ hoạt động sau khi cấu hình OAuth.
4. Cài thư viện từ `requirements.txt` và khởi động lại Flask.

Đăng nhập Google dùng OpenID Connect `openid email profile`; chỉ email đã Google xác minh mới được nhận. Email trùng với tài khoản hiện tại sẽ đăng nhập vào tài khoản đó và giữ nguyên role.

## Quên mật khẩu

Trang `/forgot-password` gửi liên kết đặt mật khẩu mới qua SMTP. Đặt `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` và `MAIL_DEFAULT_SENDER` trong `.env`. Với Gmail, dùng `smtp.gmail.com`, cổng `587` và App Password (không dùng mật khẩu đăng nhập Gmail). Liên kết chỉ dùng một lần và hết hạn sau 30 phút. Không cấu hình SMTP thì form báo rõ cần thiết lập email trước.
