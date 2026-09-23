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
