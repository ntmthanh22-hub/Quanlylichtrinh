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

def tao_anh_tu_dataframe_phan(dataframe, tieu_de_phan):
    df_export = dataframe.copy()
    for col in df_export.columns:
        if col not in ["Ngày thứ", "Ngày cụ thể", COUNT_COL]:
            df_export[col] = df_export[col].astype(str).str.replace("✔️ Thực hiện", "[Thực hiện]")

    row_height = 45
    header_height = 60
    img_width = 1200
    img_height = header_height + (len(df_export) + 1) * row_height + 40
     
    image = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
     
    try:
        if os.name == 'nt':
            font = ImageFont.truetype("arial.ttf", 18)
            font_bold = ImageFont.truetype("arialbd.ttf", 18)
            font_title = ImageFont.truetype("arialbd.ttf", 22)
        else:
            font = ImageFont.truetype("DejaVuSans.ttf", 18)
            font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font

    draw.text((20, 20), f"BANG LICH TRINH SUC KHOE - {tieu_de_phan}", fill=(24, 119, 242), font=font_title)
     
    columns = list(df_export.columns)
    x_start = 20
    y_start = 65
    col_width = (img_width - 40) / len(columns)
     
    for col_idx, col_name in enumerate(columns):
        draw.rectangle([x_start + col_idx * col_width, y_start, x_start + (col_idx + 1) * col_width, y_start + 40], fill=(240, 242, 246), outline=(200, 200, 200))
        draw.text((x_start + col_idx * col_width + 10, y_start + 10), str(col_name), fill=(0, 0, 0), font=font_bold)
         
    curr_y = y_start + 40
    for row_idx, row in df_export.iterrows():
        bg_color = (255, 230, 230) if row.get(COUNT_COL, 0) >= 2 else (255, 255, 255)
        for col_idx, col_name in enumerate(columns):
            draw.rectangle([x_start + col_idx * col_width, curr_y, x_start + (col_idx + 1) * col_width, curr_y + row_height], fill=bg_color, outline=(220, 220, 220))
            val = str(row[col_name])
            draw.text((x_start + col_idx * col_width + 10, curr_y + 12), val, fill=(50, 50, 50), font=font)
        curr_y += row_height
         
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf

if total_days <= 30:
    st.markdown("Lịch trình ngắn (<= 30 ngày), hệ thống xuất thành **1 ảnh duy nhất** với cỡ chữ lớn, rõ ràng:")
    img_bytes = tao_anh_tu_dataframe_phan(df, "TOAN BO LICH TRINH")
    st.download_button(
        label="🖼️ Tải xuống Bảng Lịch Trình (.png)",
        data=img_bytes,
        file_name="bang_lich_trinh_chi_tiet.png",
        mime="image/png",
        help="Tải ảnh toàn bộ lịch trình với cỡ chữ lớn, dễ nhìn."
    )
else:
    st.markdown(f"Lịch trình dài ({total_days} ngày > 30 ngày), hệ thống đã tự động chia thành **2 phần riêng biệt**:")
     
    mid_index = len(df) // 2
    df_part1 = df.iloc[:mid_index]
    df_part2 = df.iloc[mid_index:]

    col_img1, col_img2 = st.columns(2)

    with col_img1:
        img_bytes_1 = tao_anh_tu_dataframe_phan(df_part1, "PHAN 1 (Nua dau)")
        st.download_button(
            label="🖼️ Tải ảnh Phần 1 (Nửa đầu)",
            data=img_bytes_1,
            file_name="lich_trinh_phan_1.png",
            mime="image/png",
            help="Tải ảnh nửa đầu lịch trình."
        )

    with col_img2:
        img_bytes_2 = tao_anh_tu_dataframe_phan(df_part2, "PHAN 2 (Nua sau)")
        st.download_button(
            label="🖼️ Tải ảnh Phần 2 (Nửa sau)",
            data=img_bytes_2,
            file_name="lich_trinh_phan_2.png",
            mime="image/png",
            help="Tải ảnh nửa sau lịch trình."
        )

# =====================================================================
# PHẦN 4: THỐNG KÊ SỐ LƯỢNG TRUY CẬP
# =====================================================================
st.markdown("---")
with st.expander("📈 Thống kê số lượng người truy cập"):
    total_visits, _ = lay_lich_su_truy_cap()
    st.metric("Tổng số lượt truy cập phần mềm", f"{total_visits} lượt")
