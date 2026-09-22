"""
INSIDEOUT HEALTH – Demo v4
Full detailed assessment (form chuẩn) • Multi-step • Score engine • Google Sheets sync
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import os
import json
from copy import deepcopy

app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'insideout-health-demo-development-key'
)

# ─── Persistence (local JSON) ───────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'demo@insideout.health': {
            'password': 'demo123',
            'name': 'Anh Tuấn',
            'phone': '',
            'dob': '',
            'gender': '',
            'occupation': '',
            'referrer': '',
            'scores': {
                'giac_ngu': 4,
                'dinh_duong': 2,
                'van_dong': 3,
                'nhip_sinh_hoc': 1,
                'cam_xuc': 2,
                'tinh_than': 2
            },
            'score_history': [],
            'assessment_raw': {},
            'assessment_done': True,
            'habit': None,
            'checkins': [],
            'want_coaching': None,
            'goals': ''
        }
    }

def save_users(users_data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

users = load_users()

# ─── Google Sheets ──────────────────────────────────────────────────────────
# Spreadsheet ID từ link bạn gửi
SPREADSHEET_ID = os.environ.get(
    'INSIDEOUT_SHEET_ID',
    '1fcR2HFA1E5jalJaZ2gsoIJVgT_INMBQgCRBGfwTuZDo'
)
SHEET_NAME = 'Assessments'
CHECKIN_SHEET = 'Checkins'

def _get_gspread_client():
    import gspread
    from google.oauth2.service_account import Credentials
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
    if not creds_path:
        data_credentials = os.path.join(DATA_DIR, 'credentials.json')
        root_credentials = os.path.join(os.path.dirname(__file__), 'credentials.json')
        creds_path = data_credentials if os.path.exists(data_credentials) else root_credentials
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f'Không tìm thấy credentials: {creds_path}')
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)

def sync_assessment_to_sheets(user_email, user_data, raw, scores):
    """Append full assessment row to Google Sheet."""
    if not SPREADSHEET_ID:
        return False, 'Chưa cấu hình SPREADSHEET_ID'
    try:
        gc = _get_gspread_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet(SHEET_NAME)
        except Exception:
            ws = sh.add_worksheet(title=SHEET_NAME, rows=2000, cols=60)
            headers = [
                'timestamp', 'email', 'ho_ten', 'dob', 'gioi_tinh', 'sdt',
                'nghe_nghiep', 'nguoi_gioi_thieu',
                # Giấc ngủ
                'sleep_hours', 'sleep_quality', 'sleep_difficulty',
                # Dinh dưỡng
                'nutri_meals', 'nutri_healthy', 'nutri_control',
                # Vận động
                'move_freq', 'move_intensity',
                # Nhịp sinh học
                'bio_routine', 'bio_energy', 'bio_fluctuation',
                # Cảm xúc
                'emo_stress', 'emo_pressure', 'emo_understood', 'emo_share',
                'emo_regulate', 'emo_express', 'emo_energy', 'emo_selfaware',
                # Tinh thần
                'spirit_body_signal', 'spirit_selftime',
                # Goals
                'goals', 'want_coaching',
                # Computed scores
                'score_giac_ngu', 'score_dinh_duong', 'score_van_dong',
                'score_nhip_sinh_hoc', 'score_cam_xuc', 'score_tinh_than',
                'score_avg'
            ]
            ws.append_row(headers)

        row = [
            datetime.now().isoformat(timespec='seconds'),
            user_email,
            user_data.get('name', ''),
            raw.get('dob', ''),
            raw.get('gender', ''),
            raw.get('phone', ''),
            raw.get('occupation', ''),
            raw.get('referrer', ''),
            # Sleep
            raw.get('sleep_hours', ''),
            raw.get('sleep_quality', ''),
            raw.get('sleep_difficulty', ''),
            # Nutri
            raw.get('nutri_meals', ''),
            raw.get('nutri_healthy', ''),
            raw.get('nutri_control', ''),
            # Move
            raw.get('move_freq', ''),
            raw.get('move_intensity', ''),
            # Bio
            raw.get('bio_routine', ''),
            raw.get('bio_energy', ''),
            raw.get('bio_fluctuation', ''),
            # Emo
            raw.get('emo_stress', ''),
            raw.get('emo_pressure', ''),
            raw.get('emo_understood', ''),
            raw.get('emo_share', ''),
            raw.get('emo_regulate', ''),
            raw.get('emo_express', ''),
            raw.get('emo_energy', ''),
            raw.get('emo_selfaware', ''),
            # Spirit
            raw.get('spirit_body_signal', ''),
            raw.get('spirit_selftime', ''),
            # Goals
            raw.get('goals', ''),
            raw.get('want_coaching', ''),
            # Scores
            scores.get('giac_ngu', ''),
            scores.get('dinh_duong', ''),
            scores.get('van_dong', ''),
            scores.get('nhip_sinh_hoc', ''),
            scores.get('cam_xuc', ''),
            scores.get('tinh_than', ''),
            round(sum(scores.values()) / max(len(scores), 1), 2) if scores else ''
        ]
        ws.append_row(row)
        return True, 'Đã đồng bộ Assessment lên Google Sheet'
    except ImportError:
        return False, 'Cần cài: pip install gspread google-auth'
    except Exception as e:
        return False, f'Lỗi sync: {str(e)[:150]}'


def sync_checkin_to_sheets(user_email, payload):
    if not SPREADSHEET_ID:
        return False, 'Chưa cấu hình SPREADSHEET_ID'
    try:
        gc = _get_gspread_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet(CHECKIN_SHEET)
        except Exception:
            ws = sh.add_worksheet(title=CHECKIN_SHEET, rows=2000, cols=16)
            ws.append_row([
                'timestamp', 'email', 'name', 'mood', 'habit_done',
                'habit_title', 'note',
                'giac_ngu', 'dinh_duong', 'van_dong',
                'nhip_sinh_hoc', 'cam_xuc', 'tinh_than'
            ])
        row = [
            datetime.now().isoformat(timespec='seconds'),
            user_email,
            payload.get('name', ''),
            payload.get('mood', ''),
            payload.get('habit_done', ''),
            payload.get('habit_title', ''),
            payload.get('note', ''),
            payload.get('scores', {}).get('giac_ngu', ''),
            payload.get('scores', {}).get('dinh_duong', ''),
            payload.get('scores', {}).get('van_dong', ''),
            payload.get('scores', {}).get('nhip_sinh_hoc', ''),
            payload.get('scores', {}).get('cam_xuc', ''),
            payload.get('scores', {}).get('tinh_than', ''),
        ]
        ws.append_row(row)
        return True, 'Đã đồng bộ Check-in'
    except Exception as e:
        return False, str(e)[:120]


# ─── Domain constants ───────────────────────────────────────────────────────
PILLAR_NAMES = {
    'giac_ngu': 'Giấc ngủ',
    'dinh_duong': 'Dinh dưỡng',
    'van_dong': 'Vận động',
    'nhip_sinh_hoc': 'Nhịp sinh học',
    'cam_xuc': 'Cảm xúc',
    'tinh_than': 'Tinh thần'
}

PILLAR_ICONS = {
    'giac_ngu': '😴',
    'dinh_duong': '🥗',
    'van_dong': '🏃',
    'nhip_sinh_hoc': '🕰️',
    'cam_xuc': '😊',
    'tinh_than': '✨'
}

TINY_HABITS = {
    'giac_ngu': [
        {'id': 'sleep1', 'title': 'Tắt màn hình 30 phút trước khi ngủ', 'anchor': 'Sau khi đánh răng'},
        {'id': 'sleep2', 'title': 'Uống một ly nước ấm trước khi ngủ', 'anchor': 'Khi vào phòng ngủ'},
        {'id': 'sleep3', 'title': 'Ghi 1 điều biết ơn trước khi ngủ', 'anchor': 'Khi nằm xuống giường'},
    ],
    'dinh_duong': [
        {'id': 'nutri1', 'title': 'Uống 1 ly nước ngay sau khi thức dậy', 'anchor': 'Khi mở mắt'},
        {'id': 'nutri2', 'title': 'Ăn 1 loại rau xanh ở bữa trưa', 'anchor': 'Khi ngồi vào bàn ăn'},
        {'id': 'nutri3', 'title': 'Không dùng điện thoại khi ăn', 'anchor': 'Khi bắt đầu bữa ăn'},
    ],
    'van_dong': [
        {'id': 'move1', 'title': 'Đứng dậy và duỗi người 1 phút mỗi giờ', 'anchor': 'Khi hết 1 tiếng ngồi'},
        {'id': 'move2', 'title': 'Đi bộ 5 phút sau bữa trưa', 'anchor': 'Sau khi ăn xong'},
        {'id': 'move3', 'title': 'Leo cầu thang thay vì thang máy', 'anchor': 'Khi đến công ty'},
    ],
    'nhip_sinh_hoc': [
        {'id': 'bio1', 'title': 'Ngắm ánh sáng mặt trời 5 phút buổi sáng', 'anchor': 'Sau khi thức dậy'},
        {'id': 'bio2', 'title': 'Tắt thông báo sau 21h', 'anchor': 'Khi đồng hồ chỉ 21h'},
        {'id': 'bio3', 'title': 'Đặt điện thoại cách giường 1 mét', 'anchor': 'Khi chuẩn bị ngủ'},
    ],
    'cam_xuc': [
        {'id': 'emo1', 'title': 'Hít thở sâu 3 lần khi cảm thấy căng', 'anchor': 'Khi nhận thấy stress'},
        {'id': 'emo2', 'title': 'Viết 1 câu về cảm xúc hôm nay', 'anchor': 'Trước khi ngủ'},
        {'id': 'emo3', 'title': 'Gửi tin nhắn cảm ơn 1 người', 'anchor': 'Sau giờ làm việc'},
    ],
    'tinh_than': [
        {'id': 'spirit1', 'title': 'Dành 2 phút ngồi yên không làm gì', 'anchor': 'Buổi sáng trước khi mở điện thoại'},
        {'id': 'spirit2', 'title': 'Ghi lại 1 điều có ý nghĩa trong ngày', 'anchor': 'Khi kết thúc công việc'},
        {'id': 'spirit3', 'title': 'Nói 1 câu khích lệ bản thân', 'anchor': 'Khi nhìn vào gương'},
    ]
}

# ─── Full detailed questionnaire (matches your form) ────────────────────────
# Each question: id, type (choice|scale|text), label, options (list of {value, label} or scale 1-5)
# Scoring maps are used by compute_scores()

ASSESSMENT_SECTIONS = [
    {
        'id': 'profile',
        'title': 'Thông tin cá nhân',
        'icon': '👤',
        'intro': 'Để chúng tôi hiểu bạn hơn và cá nhân hóa Bản đồ.',
        'questions': [
            {
                'id': 'name',
                'type': 'text',
                'input_type': 'text',
                'label': 'Họ và tên',
                'placeholder': 'Nhập họ và tên của bạn',
                'required': True
            },
            {
                'id': 'dob',
                'type': 'text',
                'input_type': 'date',
                'label': 'Ngày / tháng / năm sinh',
                'required': True
            },
            {
                'id': 'gender',
                'type': 'choice',
                'label': 'Giới tính',
                'required': True,
                'options': [
                    {'value': 'Nam', 'label': 'Nam'},
                    {'value': 'Nữ', 'label': 'Nữ'},
                    {'value': 'Khác', 'label': 'Khác / Không muốn nói'},
                ]
            },
            {
                'id': 'phone',
                'type': 'text',
                'input_type': 'tel',
                'label': 'Số điện thoại (có Zalo)',
                'placeholder': '09xx xxx xxx',
                'required': True
            },
            {
                'id': 'occupation',
                'type': 'text',
                'input_type': 'text',
                'label': 'Nghề nghiệp / lĩnh vực',
                'placeholder': 'VD: Marketing, Sinh viên, Kinh doanh…',
                'required': True
            },
            {
                'id': 'referrer',
                'type': 'text',
                'input_type': 'text',
                'label': 'Tên người giới thiệu (nếu có)',
                'placeholder': 'Để trống nếu không có',
                'required': True
            },
        ]
    },
    {
        'id': 'giac_ngu',
        'title': 'Giấc ngủ',
        'icon': '😴',
        'intro': 'Hãy chọn theo thói quen giấc ngủ của bạn trong khoảng 3 tháng vừa qua.',
        'questions': [
            {
                'id': 'sleep_hours',
                'type': 'choice',
                'label': 'Bạn ngủ trung bình mỗi ngày bao nhiêu giờ?',
                'required': True,
                'options': [
                    {'value': '1', 'label': '< 4 giờ'},
                    {'value': '2', 'label': '4–5 giờ'},
                    {'value': '3', 'label': '5–6 giờ'},
                    {'value': '4', 'label': '6–7 giờ'},
                    {'value': '5', 'label': '7–8 giờ trở lên'},
                ]
            },
            {
                'id': 'sleep_quality',
                'type': 'scale',
                'label': 'Chất lượng giấc ngủ của bạn thế nào?',
                'hint': '1 = rất kém · 5 = rất tốt',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'sleep_difficulty',
                'type': 'choice',
                'label': 'Bạn có khó ngủ / thức giấc giữa đêm không?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Hầu như mỗi đêm'},
                    {'value': '2', 'label': 'Thường xuyên'},
                    {'value': '3', 'label': 'Thỉnh thoảng'},
                    {'value': '4', 'label': 'Hiếm khi'},
                    {'value': '5', 'label': 'Không bao giờ'},
                ]
            },
        ]
    },
    {
        'id': 'dinh_duong',
        'title': 'Dinh dưỡng',
        'icon': '🥗',
        'intro': 'Dựa trên thói quen ăn uống thường ngày trong khoảng 3 tháng qua.',
        'questions': [
            {
                'id': 'nutri_meals',
                'type': 'choice',
                'label': 'Bạn ăn đủ 3 bữa mỗi ngày không?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Không bao giờ'},
                    {'value': '2', 'label': 'Hiếm khi'},
                    {'value': '3', 'label': 'Thỉnh thoảng'},
                    {'value': '4', 'label': 'Thường xuyên'},
                    {'value': '5', 'label': 'Luôn luôn'},
                ]
            },
            {
                'id': 'nutri_healthy',
                'type': 'scale',
                'label': 'Bạn ăn thực phẩm tốt cho sức khỏe (rau, trái cây, ít dầu mỡ) với tần suất nào?',
                'hint': '1 = rất ít · 5 = rất thường xuyên',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'nutri_control',
                'type': 'scale',
                'label': 'Mức độ thèm ăn hoặc mất kiểm soát khi ăn?',
                'hint': '1 = mất kiểm soát nhiều · 5 = kiểm soát tốt',
                'required': True,
                'min': 1, 'max': 5
            },
        ]
    },
    {
        'id': 'van_dong',
        'title': 'Vận động',
        'icon': '🏃',
        'intro': 'Nhớ lại thói quen tập thể dục / vận động của bạn.',
        'questions': [
            {
                'id': 'move_freq',
                'type': 'choice',
                'label': 'Bạn vận động thể chất bao nhiêu lần/tuần?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Không'},
                    {'value': '2', 'label': '1–2 lần'},
                    {'value': '3', 'label': '2–3 lần'},
                    {'value': '4', 'label': '3–4 lần'},
                    {'value': '5', 'label': '4 lần trở lên'},
                ]
            },
            {
                'id': 'move_intensity',
                'type': 'scale',
                'label': 'Cường độ vận động',
                'hint': '1 = rất nhẹ · 5 = cường độ cao',
                'required': True,
                'min': 1, 'max': 5
            },
        ]
    },
    {
        'id': 'nhip_sinh_hoc',
        'title': 'Nhịp sinh học',
        'icon': '🕰️',
        'intro': 'Nhịp sinh học là “đồng hồ nội tại” 24 giờ của cơ thể. Hãy nhìn lại thói quen gần đây.',
        'questions': [
            {
                'id': 'bio_routine',
                'type': 'choice',
                'label': 'Bạn duy trì giờ giấc sinh hoạt mỗi ngày có đều không?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Rất thất thường'},
                    {'value': '2', 'label': 'Không đều đặn'},
                    {'value': '3', 'label': 'Thỉnh thoảng không đều'},
                    {'value': '4', 'label': 'Khá đều'},
                    {'value': '5', 'label': 'Rất đều đặn'},
                ]
            },
            {
                'id': 'bio_energy',
                'type': 'scale',
                'label': 'Bạn cảm thấy cơ thể mình năng lượng gần đây như thế nào?',
                'hint': '1 = rất thấp · 5 = tràn đầy',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'bio_fluctuation',
                'type': 'scale',
                'label': 'Mức năng lượng ban ngày của bạn dao động ra sao?',
                'hint': '1 = dao động rất mạnh · 5 = ổn định',
                'required': True,
                'min': 1, 'max': 5
            },
        ]
    },
    {
        'id': 'cam_xuc',
        'title': 'Cảm xúc',
        'icon': '😊',
        'intro': '"Những gì chúng ta chối bỏ trong cảm xúc sẽ xuất hiện trong cơ thể dưới dạng bệnh tật."',
        'questions': [
            {
                'id': 'emo_stress',
                'type': 'scale',
                'label': 'Mức độ căng thẳng',
                'hint': '1 = rất căng · 5 = rất nhẹ nhàng',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'emo_pressure',
                'type': 'choice',
                'label': 'Bạn có cảm thấy áp lực từ công việc / mối quan hệ / gia đình?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Rất nhiều'},
                    {'value': '2', 'label': 'Khá nhiều'},
                    {'value': '3', 'label': 'Một chút'},
                    {'value': '4', 'label': 'Gần như không'},
                    {'value': '5', 'label': 'Không áp lực'},
                ]
            },
            {
                'id': 'emo_understood',
                'type': 'scale',
                'label': 'Bạn cảm thấy bản thân được thấu hiểu và lắng nghe?',
                'hint': '1 = không hề · 5 = rất được thấu hiểu',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'emo_share',
                'type': 'choice',
                'label': 'Bạn có ai để chia sẻ khi mệt mỏi?',
                'required': True,
                'options': [
                    {'value': '5', 'label': 'Có'},
                    {'value': '1', 'label': 'Không'},
                    {'value': '3', 'label': 'Có nhưng không muốn chia sẻ'},
                ]
            },
            {
                'id': 'emo_regulate',
                'type': 'scale',
                'label': 'Bạn điều chỉnh được cảm xúc tiêu cực (lo âu, buồn, tủi thân…) ở mức nào?',
                'hint': '1 = rất khó · 5 = rất tốt',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'emo_express',
                'type': 'choice',
                'label': 'Bạn có xu hướng kìm nén hay bộc lộ cảm xúc?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Bộc lộ quá mức / Mất kiểm soát'},
                    {'value': '2', 'label': 'Kìm nén'},
                    {'value': '3', 'label': 'Cân bằng thụ động'},
                    {'value': '4', 'label': 'Cân bằng chủ động'},
                    {'value': '5', 'label': 'Linh hoạt'},
                ]
            },
            {
                'id': 'emo_energy',
                'type': 'choice',
                'label': 'Hiện tại bạn cảm thấy năng lượng cảm xúc ở mức nào?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Quá tải / kiệt sức'},
                    {'value': '2', 'label': 'Thường xuyên tiêu cực'},
                    {'value': '3', 'label': 'Dao động nhẹ'},
                    {'value': '4', 'label': 'Tích cực và khá ổn định'},
                    {'value': '5', 'label': 'Tích cực và ổn định'},
                ]
            },
            {
                'id': 'emo_selfaware',
                'type': 'scale',
                'label': 'Bạn hiểu rõ cảm xúc – nhu cầu của bản thân đến mức nào?',
                'hint': '1 = rất ít · 5 = rất rõ',
                'required': True,
                'min': 1, 'max': 5
            },
        ]
    },
    {
        'id': 'tinh_than',
        'title': 'Tinh thần',
        'icon': '✨',
        'intro': 'Tinh thần là tổng hòa nhận thức, ý chí và ý nghĩa. Hãy nhìn lại cách bạn chăm sóc phần này.',
        'questions': [
            {
                'id': 'spirit_body_signal',
                'type': 'scale',
                'label': 'Mức độ cơ thể báo hiệu stress (mệt, mất ngủ, đau đầu…)?',
                'hint': '1 = rất nhiều dấu hiệu · 5 = gần như không',
                'required': True,
                'min': 1, 'max': 5
            },
            {
                'id': 'spirit_selftime',
                'type': 'choice',
                'label': 'Bạn có dành thời gian cho bản thân (nghỉ, thiền, viết nhật ký…)?',
                'required': True,
                'options': [
                    {'value': '1', 'label': 'Không bao giờ'},
                    {'value': '2', 'label': 'Hiếm khi'},
                    {'value': '3', 'label': '1 lần/tuần'},
                    {'value': '4', 'label': 'Vài lần/tuần'},
                    {'value': '5', 'label': 'Hằng ngày'},
                ]
            },
        ]
    },
    {
        'id': 'goals',
        'title': 'Mục tiêu & Đồng hành',
        'icon': '🌱',
        'intro': 'Chia sẻ thêm để chúng tôi hỗ trợ bạn tốt hơn.',
        'questions': [
            {
                'id': 'goals',
                'type': 'textarea',
                'label': 'Mục tiêu bạn mong muốn cải thiện sau đánh giá này?',
                'placeholder': 'VD: Ngủ ngon hơn, giảm căng thẳng, vận động đều…',
                'required': True
            },
            {
                'id': 'want_coaching',
                'type': 'choice',
                'label': 'Bạn có muốn được tham vấn 1:1 với huấn luyện viên InsideOut Health?',
                'required': True,
                'options': [
                    {'value': 'Có', 'label': 'Có'},
                    {'value': 'Không', 'label': 'Không'},
                ]
            },
        ]
    },
]


def _to_num(val, default=3.0):
    """Parse answer to float in [1, 5]. Missing/invalid → default."""
    try:
        return max(1.0, min(5.0, float(val)))
    except Exception:
        return float(default)


def _weighted_avg(items):
    """
    items: list of (value, weight)
    Returns score rounded to 1 decimal, clamped [1.0, 5.0].
    """
    total_w = sum(w for _, w in items) or 1.0
    raw = sum(v * w for v, w in items) / total_w
    return round(max(1.0, min(5.0, raw)), 1)


def compute_scores(raw: dict) -> dict:
    """
    Công thức tính điểm Bản đồ Tâm – Thể (thang 1.0 – 5.0)

    Nguyên tắc:
    - Mọi câu đã được map sẵn: số càng cao = càng tốt.
    - Dùng trung bình có trọng số: câu quan trọng hơn (chất lượng, điều chỉnh,
      tần suất thực hành) được nhân hệ số lớn hơn.
    - Kết quả làm tròn 1 chữ số thập phân, kẹp trong [1.0, 5.0].

    Trọng số gợi ý (có thể chỉnh):
      1.0 = phụ   |  1.5 = chuẩn   |  2.0 = quan trọng
    """
    # ── Giấc ngủ ──────────────────────────────────────────────
    # Chất lượng & khó ngủ phản ánh tốt hơn số giờ thô.
    giac_ngu = _weighted_avg([
        (_to_num(raw.get('sleep_hours')),      1.0),  # số giờ
        (_to_num(raw.get('sleep_quality')),    2.0),  # chất lượng ★
        (_to_num(raw.get('sleep_difficulty')), 1.5),  # khó ngủ / thức giữa đêm
    ])

    # ── Dinh dưỡng ────────────────────────────────────────────
    # Ăn lành + kiểm soát quan trọng hơn “đủ 3 bữa” đơn thuần.
    dinh_duong = _weighted_avg([
        (_to_num(raw.get('nutri_meals')),   1.0),  # đủ 3 bữa
        (_to_num(raw.get('nutri_healthy')), 2.0),  # thực phẩm lành ★
        (_to_num(raw.get('nutri_control')), 1.5),  # kiểm soát khi ăn
    ])

    # ── Vận động ──────────────────────────────────────────────
    # Tần suất đều đặn quan trọng hơn cường độ một lần.
    van_dong = _weighted_avg([
        (_to_num(raw.get('move_freq')),      2.0),  # số lần/tuần ★
        (_to_num(raw.get('move_intensity')), 1.2),  # cường độ
    ])

    # ── Nhịp sinh học ─────────────────────────────────────────
    # Giờ giấc đều + năng lượng ổn định là cốt lõi.
    nhip_sinh_hoc = _weighted_avg([
        (_to_num(raw.get('bio_routine')),     2.0),  # giờ giấc đều ★
        (_to_num(raw.get('bio_energy')),      1.5),  # mức năng lượng
        (_to_num(raw.get('bio_fluctuation')), 1.3),  # dao động ban ngày
    ])

    # ── Cảm xúc ───────────────────────────────────────────────
    # Điều chỉnh cảm xúc + mức căng thẳng + năng lượng cảm xúc
    # được ưu tiên hơn các câu hỗ trợ (chia sẻ, thấu hiểu…).
    cam_xuc = _weighted_avg([
        (_to_num(raw.get('emo_stress')),     2.0),  # mức căng thẳng ★
        (_to_num(raw.get('emo_pressure')),   1.5),  # áp lực
        (_to_num(raw.get('emo_understood')), 1.0),  # được thấu hiểu
        (_to_num(raw.get('emo_share')),      1.0),  # có người chia sẻ
        (_to_num(raw.get('emo_regulate')),   2.0),  # điều chỉnh cảm xúc tiêu cực ★
        (_to_num(raw.get('emo_express')),    1.3),  # kìm nén / bộc lộ
        (_to_num(raw.get('emo_energy')),     1.8),  # năng lượng cảm xúc
        (_to_num(raw.get('emo_selfaware')),  1.5),  # tự nhận thức
    ])

    # ── Tinh thần ─────────────────────────────────────────────
    # Thời gian chăm sóc bản thân phản ánh thực hành rõ hơn.
    tinh_than = _weighted_avg([
        (_to_num(raw.get('spirit_body_signal')), 1.5),  # dấu hiệu stress cơ thể
        (_to_num(raw.get('spirit_selftime')),    2.0),  # thời gian cho bản thân ★
    ])

    return {
        'giac_ngu': giac_ngu,
        'dinh_duong': dinh_duong,
        'van_dong': van_dong,
        'nhip_sinh_hoc': nhip_sinh_hoc,
        'cam_xuc': cam_xuc,
        'tinh_than': tinh_than,
    }


def score_band(score: float) -> str:
    """Nhãn diễn giải nhanh cho 1 điểm trụ cột."""
    if score <= 2.0:
        return 'Cần quan tâm'
    if score <= 3.0:
        return 'Đang phục hồi'
    if score <= 4.0:
        return 'Ổn định'
    return 'Tốt'


def require_login():
    if 'user' not in session:
        return redirect(url_for('login'))
    return None


def require_assessment_done():
    """Redirect to assessment if logged-in user chưa hoàn thành bản đồ."""
    if 'user' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user'], {})
    if not user.get('assessment_done'):
        flash('Hãy hoàn thành Bản đồ Tâm – Thể để bắt đầu nhé.', 'info')
        return redirect(url_for('assessment'))
    return None


def get_guest_scores():
    """Scores from guest assessment stored in session (before login)."""
    return session.get('guest_scores')


def merge_guest_into_user(email):
    """When guest registers/logs in, attach pending assessment to their account."""
    guest_scores = session.pop('guest_scores', None)
    guest_raw = session.pop('guest_assessment_raw', None)
    guest_synced = session.pop('guest_assessment_synced', False)
    guest_habit = session.pop('guest_habit', None)
    if not guest_scores and not guest_raw:
        return False
    user = users.get(email)
    if not user:
        return False
    if guest_raw:
        user['assessment_raw'] = guest_raw
        for k in ('name', 'dob', 'gender', 'phone', 'occupation', 'referrer', 'goals', 'want_coaching'):
            if guest_raw.get(k):
                user[k] = guest_raw.get(k)
    if guest_scores:
        user['scores'] = guest_scores
        history = user.get('score_history', [])
        history.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'scores': deepcopy(guest_scores),
            'source': 'guest_assessment'
        })
        user['score_history'] = history[-12:]
        user['assessment_done'] = True
    if guest_habit:
        user['habit'] = guest_habit
    save_users(users)

    # Sync an assessment completed before registration after the user has an email.
    if guest_raw and guest_scores and not guest_synced:
        sync_assessment_to_sheets(email, user, guest_raw, guest_scores)

    return True


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user' in session:
        user = users.get(session['user'], {})
        if not user.get('assessment_done'):
            return redirect(url_for('assessment'))
        return redirect(url_for('home'))
    path = os.path.join(app.root_path, 'templates', 'landing_full.html')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if email in users and users[email]['password'] == password:
            session['user'] = email
            session['name'] = users[email]['name']
            merged = merge_guest_into_user(email)
            if merged:
                flash('Đã lưu Bản đồ của bạn vào tài khoản!', 'success')
                return redirect(url_for('map_result'))
            if not users[email].get('assessment_done'):
                flash('Chào mừng! Hãy hoàn thành Bản đồ để bắt đầu.', 'success')
                return redirect(url_for('assessment'))
            flash('Chào mừng bạn quay lại!', 'success')
            return redirect(url_for('home'))
        flash('Email hoặc mật khẩu không đúng. Thử demo@insideout.health / demo123', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        if not email or not password or not name:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
        elif email in users:
            flash('Email này đã được sử dụng.', 'error')
        else:
            users[email] = {
                'password': password,
                'name': name,
                'phone': '',
                'dob': '',
                'gender': '',
                'occupation': '',
                'referrer': '',
                'scores': {k: 0 for k in PILLAR_NAMES},
                'score_history': [],
                'assessment_raw': {},
                'assessment_done': False,
                'habit': None,
                'checkins': [],
                'want_coaching': None,
                'goals': ''
            }
            save_users(users)
            session['user'] = email
            session['name'] = name
            merged = merge_guest_into_user(email)
            if merged:
                flash('Đăng ký thành công! Bản đồ của bạn đã được lưu.', 'success')
                return redirect(url_for('map_result'))
            flash('Đăng ký thành công! Bắt đầu vẽ Bản đồ Tâm – Thể của bạn.', 'success')
            return redirect(url_for('assessment'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('index'))


@app.route('/home')
def home():
    redir = require_assessment_done()
    if redir:
        return redir
    user = users[session['user']]
    scores = user['scores']
    has_map = any(v > 0 for v in scores.values())
    return render_template('home.html',
                           name=session.get('name', 'Bạn'),
                           scores=scores,
                           pillar_names=PILLAR_NAMES,
                           pillar_icons=PILLAR_ICONS,
                           habit=user.get('habit'),
                           has_map=has_map,
                           checkin_count=len(user.get('checkins', [])))


@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    """Cho phép vẽ bản đồ TRƯỚC khi đăng nhập (guest)."""
    if request.method == 'POST':
        raw = {}
        for section in ASSESSMENT_SECTIONS:
            for q in section['questions']:
                qid = q['id']
                val = request.form.get(qid, '').strip()
                raw[qid] = val

        missing = [
            q['label'] for section in ASSESSMENT_SECTIONS
            for q in section['questions']
            if q.get('required') and not raw.get(q['id'])
        ]
        if missing:
            flash('Vui lòng hoàn thành tất cả câu hỏi bắt buộc trước khi xem bản đồ.', 'error')
            return render_template(
                'assessment.html',
                sections=ASSESSMENT_SECTIONS,
                pillar_names=PILLAR_NAMES,
                name=raw.get('name') or 'Bạn',
                is_guest=('user' not in session)
            )

        scores = compute_scores(raw)

        if 'user' in session and session['user'] in users:
            user = users[session['user']]
            user['name'] = raw.get('name') or user.get('name') or session.get('name', '')
            user['dob'] = raw.get('dob', '')
            user['gender'] = raw.get('gender', '')
            user['phone'] = raw.get('phone', '')
            user['occupation'] = raw.get('occupation', '')
            user['referrer'] = raw.get('referrer', '')
            user['goals'] = raw.get('goals', '')
            user['want_coaching'] = raw.get('want_coaching', '')
            user['assessment_raw'] = raw
            user['scores'] = scores
            history = user.get('score_history', [])
            history.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'scores': deepcopy(scores),
                'source': 'full_assessment'
            })
            user['score_history'] = history[-12:]
            user['assessment_done'] = True
            save_users(users)
            ok, msg = sync_assessment_to_sheets(session['user'], user, raw, scores)
            if ok:
                flash('Bản đồ Tâm – Thể đã sẵn sàng! Dữ liệu đã đồng bộ.', 'success')
            else:
                flash(f'Bản đồ đã sẵn sàng nhưng chưa lưu được Google Sheet: {msg}', 'error')
        else:
            # Guest: lưu tạm trong session, chưa cần tài khoản
            session['guest_scores'] = scores
            session['guest_assessment_raw'] = raw
            session['guest_name'] = raw.get('name') or session.get('guest_name') or 'Bạn'
            ok, msg = sync_assessment_to_sheets(
                '',
                {'name': raw.get('name', '')},
                raw,
                scores
            )
            session['guest_assessment_synced'] = ok
            if ok:
                flash('Bản đồ của bạn đã sẵn sàng và được lưu lại!', 'success')
            else:
                flash(f'Bản đồ đã sẵn sàng nhưng chưa lưu được Google Sheet: {msg}', 'error')

        return redirect(url_for('map_result'))

    # GET – form luôn mở, không bắt login
    if 'user' not in session:
        # Every guest visit to the assessment starts a clean, separate attempt.
        session.pop('guest_name', None)
        session.pop('guest_scores', None)
        session.pop('guest_assessment_raw', None)
        session.pop('guest_assessment_synced', None)
    display_name = session.get('name') if 'user' in session else 'Bạn'
    return render_template('assessment.html',
                           sections=ASSESSMENT_SECTIONS,
                           pillar_names=PILLAR_NAMES,
                           name=display_name,
                           is_guest=('user' not in session))


@app.route('/map')
def map_result():
    is_guest = 'user' not in session
    if is_guest:
        scores = get_guest_scores()
        if not scores or not any(scores.values()):
            flash('Hãy vẽ Bản đồ trước nhé — không cần đăng nhập.', 'info')
            return redirect(url_for('assessment'))
        name = session.get('guest_name', 'Bạn')
    else:
        redir = require_assessment_done()
        if redir:
            return redir
        user = users[session['user']]
        scores = user['scores']
        if not any(scores.values()):
            flash('Hãy hoàn thành Bản đồ trước nhé.', 'info')
            return redirect(url_for('assessment'))
        name = session.get('name', 'Bạn')

    lowest = min(scores, key=scores.get)
    return render_template('map.html',
                           name=name,
                           scores=scores,
                           pillar_names=PILLAR_NAMES,
                           pillar_icons=PILLAR_ICONS,
                           lowest=lowest,
                           habits=TINY_HABITS.get(lowest, []),
                           is_guest=is_guest)


@app.route('/choose-habit', methods=['POST'])
def choose_habit():
    habit_id = request.form.get('habit_id')
    pillar = request.form.get('pillar')
    chosen = None
    if pillar and habit_id:
        for h in TINY_HABITS.get(pillar, []):
            if h['id'] == habit_id:
                chosen = {
                    **h,
                    'pillar': pillar,
                    'started': datetime.now().strftime('%Y-%m-%d')
                }
                break

    if 'user' not in session:
        if chosen:
            session['guest_habit'] = chosen
            flash(f'Đã chọn: {chosen["title"]}. Đăng ký để lưu thói quen và check-in hằng ngày.', 'success')
        return redirect(url_for('register'))

    redir = require_assessment_done()
    if redir:
        return redir
    if chosen:
        users[session['user']]['habit'] = chosen
        save_users(users)
        flash(f'Bạn đã chọn thói quen: {chosen["title"]}. Chúc bạn kiên trì!', 'success')
    return redirect(url_for('home'))


@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    redir = require_assessment_done()
    if redir:
        return redir
    user = users[session['user']]
    if request.method == 'POST':
        mood = request.form.get('mood', '3')
        note = request.form.get('note', '').strip()
        habit_done = request.form.get('habit_done') == 'yes'
        checkin_data = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'mood': int(mood),
            'note': note,
            'habit_done': habit_done
        }
        user.setdefault('checkins', []).append(checkin_data)
        if habit_done and user.get('habit'):
            pillar = user['habit']['pillar']
            if user['scores'].get(pillar, 0) < 5:
                user['scores'][pillar] = round(min(5, float(user['scores'][pillar]) + 0.15), 2)
        save_users(users)
        ok, msg = sync_checkin_to_sheets(session['user'], {
            'name': session.get('name'),
            'mood': mood,
            'habit_done': 'yes' if habit_done else 'no',
            'habit_title': (user.get('habit') or {}).get('title', ''),
            'note': note,
            'scores': user['scores']
        })
        if ok:
            flash('Cảm ơn bạn đã check-in! Đã đồng bộ lên Google Sheet.', 'success')
        else:
            flash('Cảm ơn bạn đã check-in hôm nay!', 'success')
        return redirect(url_for('home'))
    return render_template('checkin.html',
                           name=session.get('name', 'Bạn'),
                           habit=user.get('habit'),
                           pillar_names=PILLAR_NAMES,
                           pillar_icons=PILLAR_ICONS)


@app.route('/trends')
def trends():
    redir = require_assessment_done()
    if redir:
        return redir
    user = users[session['user']]
    history = user.get('score_history', [])
    checkins = user.get('checkins', [])
    mood_by_day = {}
    for c in checkins[-30:]:
        day = c['date'][:10]
        mood_by_day.setdefault(day, []).append(c['mood'])
    mood_avg = {d: round(sum(v) / len(v), 1) for d, v in sorted(mood_by_day.items())}
    return render_template('trends.html',
                           name=session.get('name', 'Bạn'),
                           history=history,
                           mood_avg=mood_avg,
                           scores=user['scores'],
                           pillar_names=PILLAR_NAMES,
                           pillar_icons=PILLAR_ICONS,
                           checkin_count=len(checkins))


@app.route('/info')
def info():
    return render_template('info.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/api/sync-status')
def sync_status():
    configured = bool(SPREADSHEET_ID)
    has_creds = (
        os.path.exists(os.path.join(DATA_DIR, 'credentials.json')) or
        bool(os.environ.get('GOOGLE_CREDENTIALS_PATH'))
    )
    return jsonify({
        'configured': configured,
        'has_credentials': has_creds,
        'sheet_id': (SPREADSHEET_ID[:12] + '...') if SPREADSHEET_ID else None,
        'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}' if SPREADSHEET_ID else None
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
