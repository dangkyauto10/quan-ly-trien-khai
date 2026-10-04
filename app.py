import streamlit as st
import pandas as pd
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

SHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

# --- HÀM TẢI DỮ LIỆU ĐĂNG KÝ ĐỂ ADMIN DUYỆT ---
@st.cache_data(ttl=5)
def load_dang_ky_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=ĐĂNG_KÝ_THÀNH_VIÊN"
        return pd.read_csv(url, header=None)
    except:
        try:
            url_alt = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
            return pd.read_csv(url_alt, header=None)
        except:
            return pd.DataFrame()

# --- QUẢN LÝ TRANG & TRẠNG THÁI ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# --- GIAO DIỆN CHÍNH ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")

# Khu vực quản trị thu gọn
with st.expander("🔑 Khu vực Quản Trị & Chức Năng Khác", expanded=False):
    pass_input = st.text_input("Nhập Pass Quản Trị:", type="password", placeholder="Mật khẩu...")
    ADMIN_PASSWORDS = ["S90880", "880880"]
    
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        if st.button("📝 Đăng ký", use_container_width=True): 
            st.session_state.page = "register"
            st.session_state.admin_mode = False
            st.rerun()
    with col_a2:
        if st.button("📊 Báo cáo", use_container_width=True): 
            st.info("Chức năng Báo cáo đang phát triển.")
    with col_a3:
        if st.button("🛡️ AD Duyệt", use_container_width=True):
            if pass_input in ADMIN_PASSWORDS: 
                st.session_state.admin_mode = True
                st.session_state.page = "home"
                st.success("✅ Xác thực Admin thành công!")
            else: 
                st.warning("Sai MK")
    with col_a4:
        if st.button("🛠️ B/C LD", use_container_width=True):
            if pass_input in ADMIN_PASSWORDS: 
                st.info("Chức năng Báo cáo Lãnh đạo đang phát triển.")
            else: 
                st.warning("Sai MK")

# --- NẾU ADMIN BẤM DUYỆT (HIỂN THỊ DANH SÁCH CHỜ DUYỆT TRÊN ĐIỆN THOẠI) ---
if st.session_state.admin_mode:
    st.markdown("---")
    st.subheader("🛡️ Phê Duyệt Đăng Ký Trực Tiếp Trên Điện Thoại")
    st.caption("Danh sách thành viên đăng ký tham gia từ hiện trường được tải trực tiếp từ Google Sheets.")
    
    df_dk = load_dang_ky_data()
    
    if df_dk.empty or len(df_dk) < 3:
        st.info("📭 Hiện tại chưa có dữ liệu đăng ký mới trong Google Sheets.")
    else:
        rows_dk = df_dk.iloc[2:].values.tolist()
        
        for idx, r in enumerate(rows_dk):
            if len(r) > 2 and pd.notna(r[1]):
                thoi_gian = str(r[0]) if len(r) > 0 and pd.notna(r[0]) else "---"
                ho_ten = str(r[1]) if len(r) > 1 and pd.notna(r[1]) else "---"
                sdt = str(r[2]) if len(r) > 2 and pd.notna(r[2]) else "---"
                chuyen_mon = str(r[4]) if len(r) > 4 and pd.notna(r[4]) else "---"
                phuong_tien = str(r[5]) if len(r) > 5 and pd.notna(r[5]) else "---"
                trang_thai = str(r[6]) if len(r) > 6 and pd.notna(r[6]) else "Chờ duyệt"
                
                with st.container():
                    st.markdown(f"""
                    📌 **Họ tên:** {ho_ten} (`{sdt}`)  
                    🕒 **Thời gian:** {thoi_gian}  
                    ⚙️ **Chuyên môn:** {chuyen_mon} | **Xe:** {phuong_tien}  
                    📌 **Trạng thái hiện tại:** `{trang_thai}`
                    """)
                    
                    c_duyet, c_tuchoi = st.columns(2)
                    with c_duyet:
                        if st.button(f"✅ Duyệt ngay", key=f"app_{idx}"):
                            st.success(f"Đã duyệt thành công cho {ho_ten}!")
                    with c_tuchoi:
                        if st.button(f"❌ Từ chối", key=f"rej_{idx}"):
                            st.warning(f"Đã từ chối yêu cầu của {ho_ten}.")
                    st.markdown("---")
                    
    if st.button("⬅ Thoát chế độ Quản Trị"):
        st.session_state.admin_mode = False
        st.rerun()
    st.stop()

# --- MÀN HÌNH ĐĂNG KÝ THÀNH VIÊN ---
if st.session_state.page == "register":
    st.markdown("---")
    if st.button("⬅ Quay lại màn hình chính"):
        st.session_state.page = "home"
        st.rerun()
        
    st.subheader("📝 Đăng Ký Thành Viên")
    
    with st.form("register_form"):
        reg_name = st.text_input("Họ và tên thành viên:")
        reg_phone = st.text_input("Số điện thoại liên hệ:")
        
        reg_spec = st.selectbox("Chuyên môn thực hiện:", [
            "1. Vận chuyển / Giao nhận thiết bị",
            "2. KTV Lắp đặt hiện trường"
        ])
        reg_vehicle = st.selectbox("Phương tiện di chuyển:", ["Xe máy", "Xe tải", "Ô tô con", "Khác"])
        
        submitted = st.form_submit_button("🚀 GỬI YÊU CẦU ĐĂNG KÝ", type="primary")
        if submitted:
            if not reg_name or not reg_phone:
                st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            else:
                st.success(f"✅ Gửi đăng ký thành công cho **{reg_name}**!")
                
    st.stop()

# --- MÀN HÌNH CHÍNH: ĐIỀU HÀNH HIỆN TRƯỜNG ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM:", ["-- Chọn địa điểm --", "Điểm số 1", "Điểm số 2"])

total_devices = 10  # Mặc định an toàn

col_q, col_g = st.columns(2)
with col_q:
    actual_qty = st.number_input("Số lượng thực tế:", min_value=0, value=total_devices, step=1)
with col_g:
    st.write("") 
    if st.button("📍 Check-in GPS", use_container_width=True):
        st.success("📍 Đã ghi nhận GPS!")

# --- TRẠNG THÁI & BÁO CÁO ---
st.markdown("---")
st.markdown("**2. Trạng Thái Hoàn Thành:**")

if "selected_status" not in st.session_state:
    st.session_state.selected_status = "Đang vận chuyển"

b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚚 Đang V/C", use_container_width=True): st.session_state.selected_status = "Đang vận chuyển"
with b_col2:
    if st.button("✅ Đã Giao", key="btn_giao", use_container_width=True): st.session_state.selected_status = "Đã giao hàng xong"

b_col3, b_col4 = st.columns(2)
with b_col3:
    if st.button("⚙️ Đang Lắp", key="btn_lap", use_container_width=True): st.session_state.selected_status = "Đang lắp đặt"
with b_col4:
    if st.button("🎉 Hoàn Thành", key="btn_ht", use_container_width=True): st.session_state.selected_status = "Đã lắp đặt xong"

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
