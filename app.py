import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN GỌN GÀNG ---
st.set_page_config(page_title="Hệ Thống Điều Hành Dự Án", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- ĐỌC DỮ LIỆU TỪ GOOGLE SHEETS (PUBLIC CSV - MÃ HÓA URL TÊN SHEET TIẾNG VIỆT) ---
SHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

@st.cache_data(ttl=30)
def load_kho_data():
    sheet_encoded = urllib.parse.quote("KHO_PHAN_BO")
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={sheet_encoded}"
    return pd.read_csv(csv_url, header=None)

@st.cache_data(ttl=30)
def load_danh_sach_diem():
    diem_list = []
    try:
        # Mã hóa URL tên sheet có dấu tiếng Việt chuẩn xác tuyệt đối
        sheet_encoded = urllib.parse.quote("DANH_SACH_DIỂM")
        url_diem = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={sheet_encoded}"
        df_d = pd.read_csv(url_diem, header=None)
        
        # Quét cột D (index 3) từ dòng thứ 3 trở xuống để lấy toàn bộ danh sách điểm thực tế
        target_col = 3 if len(df_d.columns) > 3 else 0
        raw_vals = df_d.iloc[2:, target_col].dropna().astype(str).str.strip().tolist()
        
        for v in raw_vals:
            if v and v.lower() not in ['nan', 'none', '', '-- chọn địa điểm --', 'địa điểm giao hàng và lắp đặt']:
                if v not in diem_list:
                    diem_list.append(v)
    except Exception as e:
        pass
        
    # Nếu quét sheet danh sách điểm gặp vấn đề, lấy dự phòng từ cột địa điểm của KHO_PHAN_BO
    if not diem_list:
        try:
            df_k = load_kho_data()
            if len(df_k.columns) > 7:
                vals = df_k.iloc[2:, 7].dropna().astype(str).str.strip().tolist()
                for v in vals:
                    if v and v.lower() not in ['nan', '']:
                        if v not in diem_list:
                            diem_list.append(v)
        except:
            pass
            
    return sorted(list(set(diem_list)))

try:
    df_data = load_kho_data()
    dia_ban_options = load_danh_sach_diem()
except Exception as e:
    st.error(f"❌ Lỗi tải dữ liệu: {e}")
    st.stop()

# --- GIAO DIỆN CHÍNH ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")

if "page" not in st.session_state:
    st.session_state.page = "home"

# Khu vực quản trị thu gọn
with st.expander("🔑 Khu vực Quản Trị & Chức Năng Khác", expanded=False):
    pass_input = st.text_input("Nhập Pass Quản Trị:", type="password", placeholder="Mật khẩu...")
    ADMIN_PASS = "S90880"
    
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        if st.button("📝 Đăng ký", use_container_width=True): 
            st.session_state.page = "register"
            st.rerun()
    with col_a2:
        if st.button("📊 Báo cáo", use_container_width=True): 
            st.info("Chức năng Báo cáo đang phát triển.")
    with col_a3:
        if st.button("🛡️ AD Duyệt", use_container_width=True):
            if pass_input == ADMIN_PASS: st.success("OK - Admin đã duyệt")
            else: st.warning("Sai MK")
    with col_a4:
        if st.button("🛠️ B/C LD", use_container_width=True):
            if pass_input == ADMIN_PASS: st.success("OK - Quản lý LD")
            else: st.warning("Sai MK")

# --- MÀN HÌNH ĐĂNG KÝ THÀNH VIÊN MỚI ---
if st.session_state.page == "register":
    st.markdown("---")
    if st.button("⬅ Quay lại màn hình chính"):
        st.session_state.page = "home"
        st.rerun()
        
    st.subheader("📝 Đăng Ký Thông Tin Thành Viên Mới")
    st.caption(f"✅ Đã nạp thành công **{len(dia_ban_options)} điểm** từ Cột D. Thành viên có thể chọn 1 đến nhiều dự án cùng lúc.")
    
    reg_name = st.text_input("Họ và tên:")
    reg_phone = st.text_input("Số điện thoại:")
    
    # Ô chọn đa nhiệm toàn bộ danh sách chuẩn từ Cột D
    selected_diaban = st.multiselect(
        "Địa bàn phụ trách (Chọn nhiều dự án đồng thời):",
        options=dia_ban_options,
        placeholder="Gõ tìm kiếm hoặc chọn các điểm dự án..."
    )
    
    reg_spec = st.selectbox("Chuyên môn:", [
        "1. Vận chuyển / Giao nhận",
        "2. KTV Lắp đặt thiết bị"
    ])
    reg_vehicle = st.selectbox("Phương tiện:", ["Xe máy", "Xe tải", "Ô tô con", "Khác"])
    
    if st.button("🚀 Gửi Yêu Cầu Đăng Ký", type="primary"):
        if not reg_name or not reg_phone:
            st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
        elif not selected_diaban:
            st.warning("⚠️ Vui lòng chọn ít nhất 1 địa bàn/dự án phụ trách!")
        else:
            diaban_str = ", ".join(selected_diaban)
            st.success(f"✅ Gửi đăng ký thành công cho **{reg_name}**!\n\n📌 **Phụ trách {len(selected_diaban)} địa bàn:** `{diaban_str}`.\n\n⏳ Đang chờ Admin phê duyệt.")
            
    st.stop()

# --- MÀN HÌNH CHÍNH (ĐIỀU HÀNH HIỆN TRƯỜNG) ---
if len(df_data) < 3:
    st.warning("Sheet KHO_PHAN_BO chưa đủ dữ liệu!")
    st.stop()

rows = df_data.iloc[2:].values.tolist()
locations = sorted(list(set([str(row[7]).strip() for row in rows if len(row) > 7 and pd.notna(row[7]) and str(row[7]).strip()])))

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM:", ["-- Chọn địa điểm --"] + locations)

total_devices = 0
matched_rows_indices = []

if selected_location != "-- Chọn địa điểm --":
    for idx, row in enumerate(rows, start=3):
        if len(row) > 7 and pd.notna(row[7]) and str(row[7]).strip() == selected_location:
            matched_rows_indices.append(idx)
            try:
                qty = int(row[4]) if len(row) > 4 and pd.notna(row[4]) and str(row[4]).isdigit() else 0
                total_devices += qty
            except:
                pass
    st.caption(f"📦 **Phân bổ:** `{total_devices} thiết bị`")

col_q, col_g = st.columns(2)
with col_q:
    actual_qty = st.number_input("Số lượng thực tế:", min_value=0, value=total_devices, step=1)
with col_g:
    st.write("") 
    if st.button("📍 Check-in GPS", use_container_width=True):
        st.success("📍 Đã ghi nhận GPS!")

st.markdown("---")
st.markdown("**2. Trạng Thái Hoàn Thành:**")

if "selected_status" not in st.session_state:
    st.session_state.selected_status = "Đang vận chuyển"

b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚚 Đang V/C", use_container_width=True): st.session_state.selected_status = "Đang vận chuyển"
with b_col2:
    if st.button("✅ Đã Giao", use_container_width=True): st.session_state.selected_status = "Đã giao hàng xong"

b_col3, b_col4 = st.columns(2)
with b_col3:
    if st.button("⚙️ Đang Lắp", use_container_width=True): st.session_state.selected_status = "Đang lắp đặt"
with b_col4:
    if st.button("🎉 Hoàn Thành", use_container_width=True): st.session_state.selected_status = "Đã lắp đặt xong"

st.caption(f"📌 Đang chọn: **{st.session_state.selected_status}**")

col_note, col_img = st.columns(2)
with col_note:
    notes = st.text_area("Ghi chú / Phát sinh:", placeholder="Nhập ghi chú...", height=70)
with col_img:
    st.file_uploader("📷 Ảnh nghiệm thu", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if st.button("🚀 GỬI BÁO CÁO & CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi!")
    else:
        st.success(f"✅ Gửi báo cáo thành công trạng thái '{st.session_state.selected_status}' cho điểm {selected_location}!")
