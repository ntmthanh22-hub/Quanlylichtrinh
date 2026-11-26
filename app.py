import streamlit as st
import pandas as pd
import datetime
import os
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(
    page_title="CRT Hệ thống quản lí lịch trình",
    page_icon="💊",
    layout="wide"
)

# =====================================================================
# PHẦN 0: CƠ SỞ DỮ LIỆU BỀN VỮNG (SQLITE) & LỊCH SỬ TRUY CẬP
# =====================================================================
DB_FILE = "health_schedule.db"
LOG_FILE = "access_log.txt"
COUNT_COL = "Số hoạt động trong một ngày"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cycle INTEGER NOT NULL,
            start_date TEXT NOT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM activities')
    if cursor.fetchone()[0] == 0:
        default_date = datetime.date.today().strftime("%Y-%m-%d")
        cursor.executemany('INSERT INTO activities (name, cycle, start_date) VALUES (?, ?, ?)', [
            ("Uống Vitamin D3", 2, default_date),
            ("Tập thể lực (Gym)", 3, default_date),
            ("Đi đánh cầu lông", 5, default_date)
        ])
        conn.commit()
    conn.close()

def load_activities_db():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT name, cycle, start_date FROM activities')
    rows = cursor.fetchall()
    conn.close()
    activities = []
    for r in rows:
        activities.append({
            "name": r[0],
            "cycle": r[1],
            "start_date": datetime.datetime.strptime(r[2], "%Y-%m-%d").date()
        })
    return activities

def save_activities_db(activities):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities')
    for act in activities:
        cursor.execute('INSERT INTO activities (name, cycle, start_date) VALUES (?, ?, ?)',
                       (act["name"], act["cycle"], act["start_date"].strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def ghi_nhan_truy_cap():
    thoi_gian = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Truy cập lúc: {thoi_gian}\n")
    except Exception:
        pass

def lay_lich_su_truy_cap():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return len(lines), lines
    return 0, []

if 'has_logged' not in st.session_state:
    ghi_nhan_truy_cap()
    st.session_state.has_logged = True


# =====================================================================
# PHẦN 1: LÕI THUẬT TOÁN TOÁN HỌC (CRT CHUẨN & EUCLID MỞ RỘNG)
# =====================================================================

def thuc_hien_euclid_mo_rong(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = thuc_hien_euclid_mo_rong(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y


def dinh_ly_phan_du_trung_hoa(a, m):
    M = 1
    for m_i in m:
        M *= m_i
     
    x = 0
    for a_i, m_i in zip(a, m):
        M_i = M // m_i
        gcd, e_i, _ = thuc_hien_euclid_mo_rong(M_i, m_i)
         
        if gcd != 1:
            raise ValueError(f"Các chu kỳ không nguyên tố cùng nhau tại m_i = {m_i}")
         
        x += a_i * M_i * e_i
         
    return x % M, M


# =====================================================================
# PHẦN 2: GIAO DIỆN WEB & QUẢN LÝ SIDEBAR
# =====================================================================

st.title("💊 Hệ thống quản lí lịch trình")
if 'activities' not in st.session_state:
    st.session_state.activities = load_activities_db()

with st.sidebar:
    st.header("⚙️ Thiết lập lịch trình & Hoạt động")
    
    global_start_date = st.date_input("📅 Ngày bắt đầu mô phỏng chung", datetime.date.today())
     
    st.markdown("---")
    st.markdown("Quản lý danh sách hoạt động:")
     
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Thêm"):
            st.session_state.activities.append({
                "name": "Hoạt động mới", 
                "cycle": 7, 
                "start_date": datetime.date.today()
            })
            save_activities_db(st.session_state.activities)
            st.rerun()
    with col_btn2:
        if len(st.session_state.activities) > 1 and st.button("🗑️ Xóa"):
            st.session_state.activities.pop()
            save_activities_db(st.session_state.activities)
            st.rerun()
          
    st.markdown("---")
     
    updated_activities = []
    for i, act in enumerate(st.session_state.activities):
        st.markdown(f"**Hoạt động {i+1}**")
        name = st.text_input("Tên hoạt động", value=act["name"], key=f"name_act_{i}")
        cycle = st.number_input("Chu kỳ (ngày)", min_value=1, max_value=60, value=int(act["cycle"]), key=f"cycle_act_{i}")
        start_d = st.date_input("Ngày bắt đầu riêng", value=act["start_date"], key=f"date_act_{i}")
        
        updated_activities.append({"name": name, "cycle": cycle, "start_date": start_d})
        st.markdown("---")
     
    if updated_activities != st.session_state.activities:
        st.session_state.activities = updated_activities
        save_activities_db(st.session_state.activities)

    total_days = st.slider("Số ngày mô phỏng lịch trình", min_value=10, max_value=120, value=30)

m = [act["cycle"] for act in st.session_state.activities]
names = [act["name"] for act in st.session_state.activities]
start_dates = [act["start_date"] for act in st.session_state.activities]

a = [(act_start - global_start_date).days for act_start in start_dates]

try:
    first_collision, system_period = dinh_ly_phan_du_trung_hoa(a, m)
    math_error = None
except ValueError as err:
    math_error = str(err)
    system_period = 1
    for val in m:
        system_period *= val

schedule_data = []
for i in range(total_days):
    current_day_index = i + 1
    actual_date = global_start_date + datetime.timedelta(days=i)
    date_str = actual_date.strftime("%d/%m/%Y")
     
    row = {
        "Ngày thứ": current_day_index,
        "Ngày cụ thể": date_str
    }
     
    active_count = 0
    for act in st.session_state.activities:
        name = act["name"]
        cycle = act["cycle"]
        act_start = act["start_date"]
        
        if cycle <= 0:
            cycle = 1
            
        if actual_date >= act_start:
            delta_days = (actual_date - act_start).days
            is_due = (delta_days % cycle == 0)
        else:
            is_due = False
            
        row[name] = "✔️ Thực hiện" if is_due else "-"
        if is_due:
            active_count += 1
            
    row[COUNT_COL] = active_count
    schedule_data.append(row)

df = pd.DataFrame(schedule_data)

# --- KHU VỰC HIỂN THỊ KẾT QUẢ TRÊN WEB ---
if math_error:
    st.error(f"⚠️ Lỗi toán học Định lý Phần dư Trung Hoa: {math_error}. Hệ thống yêu cầu các chu kỳ phải đôi một nguyên tố cùng nhau (GCD = 1).")

col1, col2, col3 = st.columns(3)
col1.metric("Chu kỳ lặp lại tổng thể (M)", f"{system_period} ngày")
col2.metric("Số lượng hoạt động quản lý", f"{len(names)} hoạt động")
col3.metric("Ngày cao điểm nhất", f"{df[COUNT_COL].max()} việc/ngày")

st.markdown("---")
st.subheader("📅 Bảng Lịch Trình Chi Tiết & Phân Tải Trọng")

def highlight_busy(s):
    if s[COUNT_COL] >= 2:
        return ['background-color: #ffe6e6'] * len(s)
    return [''] * len(s)

st.dataframe(df.style.apply(highlight_busy, axis=1), use_container_width=True)

# --- BẢNG LỜI NHẮC TRÙNG LỊCH ---
st.markdown("---")
st.subheader("🔔 Bảng Lời Nhắc: Các ngày tất cả hoạt động trùng lặp đồng thời")
df_all_collision = df[df[COUNT_COL] == len(names)]

if not df_all_collision.empty:
    st.success(f"Đã tìm thấy {len(df_all_collision)} mốc ngày trùng lịch toàn bộ!")
    st.dataframe(df_all_collision, use_container_width=True)
else:
    st.info("💡 Không có ngày nào trong khoảng mô phỏng hiện tại mà *tất cả* các hoạt động diễn ra cùng một lúc. Hãy tăng số ngày mô phỏng hoặc điều chỉnh chu kỳ để quan sát.")

# --- BIỂU ĐỒ TRỰC QUAN ---
st.markdown("---")
st.subheader("📊 Biểu đồ Phân bổ Tải lượng Công việc Sức khỏe theo Ngày")
st.bar_chart(df.set_index("Ngày cụ thể")[COUNT_COL])

# =====================================================================
# PHẦN 3: TÍNH NĂNG TẢI XUỐNG ẢNH TỰ ĐỘNG (HỖ TRỢ ĐA NỀN TẢNG)
# =====================================================================
st.markdown("---")
st.subheader("📥 Xuất Hình Ảnh Bảng Lịch Trình")


def tim_font_tieng_viet():
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    candidates = [
        os.path.join(base_dir, "DejaVuSans.ttf"),
        os.path.join(base_dir, "Roboto-Regular.ttf"),
        os.path.join(base_dir, "Arial.ttf"),
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def tao_anh_tu_dataframe_phan(dataframe, tieu_de_phan):
    df_export = dataframe.copy()
    for col in df_export.columns:
        if col not in ["Ngày thứ", "Ngày cụ thể", COUNT_COL]:
            df_export[col] = df_export[col].astype(str).str.replace("✔️ Thực hiện", "[Thực hiện]")

    font_path = tim_font_tieng_viet()

    def load_font(size):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font = load_font(18)
    font_bold = load_font(18)
    font_title = load_font(22)

    dummy_img = Image.new("RGB", (10, 10))
    dummy_draw = ImageDraw.Draw(dummy_img)

    def do_rong_chu(text, fnt):
        bbox = dummy_draw.textbbox((0, 0), str(text), font=fnt)
        return bbox[2] - bbox[0]

    columns = list(df_export.columns)
    padding_x = 24
    col_widths = []
    for col_name in columns:
        max_w = do_rong_chu(col_name, font_bold) + padding_x * 2
        for val in df_export[col_name]:
            w = do_rong_chu(val, font) + padding_x * 2
            if w > max_w:
                max_w = w
        col_widths.append(max(max_w, 130))

    row_height = 45
    header_height = 40
    top_margin = 65
    side_margin = 20
    img_width = int(sum(col_widths) + side_margin * 2)
    img_height = int(top_margin + header_height + len(df_export) * row_height + 40)

    image = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    draw.text(
        (side_margin, 20),
        f"BẢNG LỊCH TRÌNH SỨC KHỎE - {tieu_de_phan}",
        fill=(24, 119, 242),
        font=font_title,
    )

    x_curr = side_margin
    y_header = top_margin
    for col_idx, col_name in enumerate(columns):
        w = col_widths[col_idx]
        draw.rectangle(
            [x_curr, y_header, x_curr + w, y_header + header_height],
            fill=(240, 242, 246),
            outline=(200, 200, 200),
        )
        draw.text(
            (x_curr + 10, y_header + 10),
            str(col_name),
            fill=(0, 0, 0),
            font=font_bold,
        )
        x_curr += w

    curr_y = y_header + header_height
    for _, row in df_export.iterrows():
        bg_color = (255, 230, 230) if row.get(COUNT_COL, 0) >= 2 else (255, 255, 255)
        x_curr = side_margin
        for col_idx, col_name in enumerate(columns):
            w = col_widths[col_idx]
            draw.rectangle(
                [x_curr, curr_y, x_curr + w, curr_y + row_height],
                fill=bg_color,
                outline=(220, 220, 220),
            )
            val = str(row[col_name])
            draw.text(
                (x_curr + 10, curr_y + 12),
                val,
                fill=(50, 50, 50),
                font=font,
            )
            x_curr += w
        curr_y += row_height

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


st.caption("💡 Trên điện thoại: bạn có thể bấm nút tải về, hoặc **nhấn giữ trực tiếp vào ảnh hiển thị bên dưới** để lưu nhanh vào Album ảnh.")

if total_days <= 30:
    st.markdown("Lịch trình ngắn (<= 30 ngày), hệ thống xuất thành **1 ảnh duy nhất** với cỡ chữ lớn, rõ ràng:")
    img_bytes = tao_anh_tu_dataframe_phan(df, "TOÀN BỘ LỊCH TRÌNH")
    st.download_button(
        label="🖼️ Tải xuống Bảng Lịch Trình (.png)",
        data=img_bytes,
        file_name="bang_lich_trinh_chi_tiet.png",
        mime="image/png",
        help="Tải ảnh toàn bộ lịch trình với cỡ chữ lớn, dễ nhìn."
    )
    st.image(img_bytes, caption="Bảng lịch trình chi tiết", use_container_width=True)
else:
    st.markdown(f"Lịch trình dài ({total_days} ngày > 30 ngày), hệ thống đã tự động chia thành **2 phần riêng biệt**:")
     
    mid_index = len(df) // 2
    df_part1 = df.iloc[:mid_index]
    df_part2 = df.iloc[mid_index:]

    col_img1, col_img2 = st.columns(2)

    with col_img1:
        img_bytes_1 = tao_anh_tu_dataframe_phan(df_part1, "PHẦN 1 (NỬA ĐẦU)")
        st.download_button(
            label="🖼️ Tải ảnh Phần 1 (Nửa đầu)",
            data=img_bytes_1,
            file_name="lich_trinh_phan_1.png",
            mime="image/png",
            help="Tải ảnh nửa đầu lịch trình."
        )
        st.image(img_bytes_1, caption="Phần 1 (Nửa đầu)", use_container_width=True)

    with col_img2:
        img_bytes_2 = tao_anh_tu_dataframe_phan(df_part2, "PHẦN 2 (NỬA SAU)")
        st.download_button(
            label="🖼️ Tải ảnh Phần 2 (Nửa sau)",
            data=img_bytes_2,
            file_name="lich_trinh_phan_2.png",
            mime="image/png",
            help="Tải ảnh nửa sau lịch trình."
        )
        st.image(img_bytes_2, caption="Phần 2 (Nửa sau)", use_container_width=True)

# =====================================================================
# PHẦN 4: THỐNG KÊ SỐ LƯỢNG TRUY CẬP
# =====================================================================
st.markdown("---")
with st.expander("📈 Thống kê số lượng người truy cập"):
    total_visits, _ = lay_lich_su_truy_cap()
    st.metric("Tổng số lượt truy cập phần mềm", f"{total_visits} lượt")
