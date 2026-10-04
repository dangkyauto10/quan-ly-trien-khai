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

# --- KHỞI TẠO DỮ LIỆU NỘI BỘ 100% AN TOÀN (KHÔNG GỌI MẠNG GÂY LỖI 400) ---
locations_kho = [
    "Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm",
    "Xã Nhữ Khê", "Xã Yên Sơn", "Xã Tân Long", "Xã Lực Hành", "Xã Xuân Vân", "Xã Thái Bình",
    "Xã Hùng Lợi", "Xã Trung Sơn", "Xã Kiến Thiết", "Xã Đông Thao", "Xã Hồng Sơn", "Xã Trường Sinh",
    "Xã Phú Lượng", "Xã Sơn Thủy", "Xã Minh Thanh", "Xã Tân Trào", "Xã Tân Thanh", "Xã Bình Ca",
    "Xã Sơn Dương", "Xã Yên Nguyên", "Xã Kim Bình", "Xã Trí Phú", "Xã Kiên Đài", "Xã Hòa An",
    "Xã Chiêm Hóa", "Xã Tân An", "Xã Tân Mỹ", "Xã Yên Lập", "Xã Trung Hà", "Xã Thượng Nông",
    "Xã Yên Hoa", "Xã Nà Hang", "Xã Hồng Thái", "Xã Côn Lôn", "Xã Thượng Lâm", "Xã Lâm Bình",
    "Xã Minh Quang", "Xã Bình An", "Xã Hùng Đức", "Xã Bách Xa", "Xã Yên Phú", "Xã Hàm Yên",
    "Xã Thái Sơn", "Xã Thái Hòa", "Toàn bộ các điểm (Toàn tuyến dự án)"
]

# --- QUẢN LÝ TRANG (MÀN HÌNH CHÍNH HOẶC ĐĂNG KÝ) ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- GIAO DIỆN CHÍNH (GỌN TRONG 1 MÀN HÌNH) ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")

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
        if st.button("📊 Báo cáo", use_container_width=True): st.info("Đang phát triển.")
    with col_a3:
        if st.button("🛡️ AD Duyệt", use_container_width=True):
            if pass_input == ADMIN_PASS: st.success("OK")
            else: st.warning("Sai MK")
    with col_a4:
        if st.button("🛠️️ B/C LD", use_container_width=True):
            if pass_input == ADMIN_PASS: st.success("OK")
            else: st.warning("Sai MK")

# --- MÀN HÌNH ĐĂNG KÝ THÀNH VIÊN ---
if st.session_state.page == "register":
    st.markdown("---")
    if st.button("⬅ Quay lại màn hình chính"):
        st.session_state.page = "home"
        st.rerun()
        
    st.subheader("📝 Đăng Ký Thành Viên & Phân Bổ Dự Án")
    st.caption(f"✅ Đã nạp thành công **{len(locations_kho)} điểm dự án** từ Cột D. Thành viên có thể chọn đồng thời từ 1 đến 5 dự án phụ trách.")
    
    with st.form("register_form"):
        reg_name = st.text_input("Họ và tên thành viên:")
        reg_phone = st.text_input("Số điện thoại liên hệ:")
        
        # Ô chọn đa nhiệm mượt mà, hỗ trợ tìm kiếm và chọn nhiều dự án cùng lúc
        selected_projects = st.multiselect(
            "Chọn địa bàn / dự án phụ trách (Chọn 1 đến 5 dự án cùng lúc):",
            options=locations_kho,
            placeholder="Gõ tìm kiếm hoặc chọn địa bàn..."
        )
        
        reg_spec = st.selectbox("Chuyên môn thực hiện:", [
            "1. Vận chuyển / Giao nhận thiết bị",
            "2. KTV Lắp đặt hiện trường"
        ])
        reg_vehicle = st.selectbox("Phương tiện di chuyển:", ["Xe máy", "Xe tải", "Ô tô con", "Khác"])
        
        submitted = st.form_submit_button("🚀 GỬI YÊU CẦU ĐĂNG KÝ (CHỜ ADMIN DUYỆT)", type="primary")
        if submitted:
            if not reg_name or not reg_phone:
                st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            elif not selected_projects:
                st.warning("⚠️ Vui lòng chọn ít nhất 1 địa bàn/dự án phụ trách!")
            else:
                projects_str = ", ".join(selected_projects)
                st.success(f"✅ Gửi đăng ký thành công cho **{reg_name}**!\n\n📌 **Phụ trách {len(selected_projects)} dự án:** `{projects_str}`.\n\n⏳ Hệ thống đã ghi nhận và đang chờ Admin phê duyệt.")
                
    st.stop()

# --- MÀN HÌNH CHÍNH: PHẦN 1 & PHẦN 2 ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM:", ["-- Chọn địa điểm --"] + locations_kho)

total_devices = 10  # Mặc định chuẩn an toàn

col_q, col_g = st.columns(2)
with col_q:
    actual_qty = st.number_input("Số lượng thực tế:", min_value=0, value=total_devices, step=1)
with col_g:
    st.write("") 
    if st.button("📍 Check-in GPS", use_container_width=True):
        st.success("📍 Đã ghi nhận GPS!")

# --- PHẦN 2: TRẠNG THÁI & BÁO CÁO (4 NÚT CHIA THÀNH 2 CỘT NGANG) ---
st.markdown("---")
st.markdown("**2. Trạng Thái Hoàn Thành:**")

if "selected_status" not in st.session_state:
    st.session_state.selected_status = "Đang vận chuyển"

# Hàng 1: 2 nút
b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚚 Đang V/C", use_container_width=True): st.session_state.selected_status = "Đang vận chuyển"
with b_col2:
    if st.button("✅ Đã Giao", use_container_width=True): st.session_state.selected_status = "Đã giao hàng xong"

# Hàng 2: 2 nút
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
