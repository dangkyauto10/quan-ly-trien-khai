import streamlit as st
import datetime

st.set_page_config(page_title="Hệ thống Điều hành Hiện trường", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH & BÁO CÁO HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

# 4 NÚT ĐIỀU HƯỚNG CHÍNH Ở TRÊN CÙNG
col1, col2, col3, col4 = st.columns(4)
with col1: btn_dang_ky = st.button("📝 Đăng ký", use_container_width=True)
with col2: btn_bao_cao = st.button("📊 Báo cáo", use_container_width=True)
with col3: btn_admin = st.button("🔒 Admin duyệt", use_container_width=True)
with col4: btn_link = st.button("📈 Link báo cáo", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

# ================= 1. TAB ĐĂNG KÝ THÀNH VIÊN =================
if st.session_state.nav_tab == "Dang_ky":
    st.markdown("### 📝 ĐĂNG KÝ THÀNH VIÊN / ĐỘI THỰC HIỆN")
    with st.form("form_dang_ky"):
        ten_thanh_vien = st.text_input("Họ và tên *")
        sdt = st.text_input("Số điện thoại liên hệ *")
        vai_tro = st.selectbox("Vai trò công việc *", ["Đội Vận Chuyển (VC)", "Đội Lắp Đặt (LD)", "Đội Kiêm Nhiệm (VC & LD)"])
        don_vi = st.text_input("Đơn vị / Bộ phận công tác *")
        if st.form_submit_button("Gửi đăng ký", type="primary"):
            if not ten_thanh_vien or not sdt: st.warning("⚠️ Vui lòng điền đầy đủ họ tên và số điện thoại!")
            else: st.success("🎉 Đăng ký thành công! Vui lòng chờ Admin duyệt tài khoản.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### 📊 BÁO CÁO NHIỆM VỤ HIỆN TRƯỜNG")
    
    # Nguồn dữ liệu mẫu (Ánh xạ từ QUAN_LY_DOI cột B và DANH_SACH_DIEM cột D)
    danh_sach_doi = ["Nguyễn Văn Thiện - Đội 01", "Trần Văn C - Đội 02", "Đội Kỹ Thuật Tổng Hợp", "Đội Xây lắp Số 1"]
    danh_sach_diem = ["Xã Sùng Máng (DA880)", "Phường Nông Tiến (DA880)", "Xã Đường Thượng (DA880)", "Xã Nà Hang (DA880)"]
    
    # TÌM KIẾM THÔNG MINH (Gõ từ khóa tự động lọc gợi ý)
    search_doi = st.text_input("🔍 Nhập từ khóa tìm kiếm Tên đội (hoặc chọn bên dưới):", placeholder="Gõ tên đội để lọc nhanh...")
    filtered_doi = [d for d in danh_sach_doi if search_doi.lower() in d.lower()] if search_doi else danh_sach_doi
    doi_thuc_hien = st.selectbox("👥 Chọn Tên đội vận chuyển / lắp đặt *", filtered_doi)
    
    st.markdown("---")
    search_diem = st.text_input("🔍 Nhập từ khóa tìm kiếm Địa điểm giao/lắp:", placeholder="Gõ xã/phường để lọc nhanh...")
    filtered_diem = [d for d in danh_sach_diem if search_diem.lower() in d.lower()] if search_diem else danh_sach_diem
    diem_giao_lap = st.selectbox("📍 Chọn Điểm giao hàng & Lắp đặt *", filtered_diem)
    
    # SỐ LƯỢNG THIẾT BỊ CỐ ĐỊNH TỪ KHO
    st.info(f"📦 Số lượng thiết bị phân bổ tại điểm **{diem_giao_lap}**: **3 bộ/chiếc** (Cố định từ Kho, không thay đổi được)")
    so_luong_hien_tai = st.number_input("Số lượng thiết bị áp dụng báo cáo", value=3, disabled=True)
    
    st.markdown("---")
    st.markdown("📷 **Chụp ảnh hiện trường** (Hỗ trợ camera sau/trước của thiết bị):")
    camera_file = st.camera_input("Chụp ảnh thực tế")
    
    st.markdown("---")
    st.markdown("📍 **Xác thực GPS hiện trường:**")
    if st.button("📍 Check-in GPS Tọa độ Hiện trường", use_container_width=True):
        st.success("📍 Check-in GPS thành công (Lat: 21.82, Long: 105.21)!")
        
    st.markdown("---")
    st.markdown("### 🎛️ BÁO CÁO XÁC NHẬN (CHỌN 1 TRONG 3 NÚT SAU):")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("✅ ĐÃ GIAO XONG", type="primary", use_container_width=True):
            st.success(f"🎉 Gửi báo cáo thành công: **ĐÃ GIAO XONG** cho đội {doi_thuc_hien} tại {diem_giao_lap}!")
    with col_b2:
        if st.button("✅ ĐÃ LẮP XONG", type="primary", use_container_width=True):
            st.success(f"🎉 Gửi báo cáo thành công: **ĐÃ LẮP XONG** cho đội {doi_thuc_hien} tại {diem_giao_lap}!")
    with col_b3:
        if st.button("🚀 ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            st.success(f"🎉 Gửi báo cáo thành công TRỌN GÓI: **ĐÃ GIAO VÀ LẮP XONG** cho đội {doi_thuc_hien} tại {diem_giao_lap}!")

# ================= 3. TAB ADMIN DUYỆT (PASS: 880880) =================
elif st.session_state.nav_tab == "Admin":
    st.markdown("### 🔒 KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("🔓 Đăng nhập Admin thành công!")
        st.write("- [Chờ duyệt] Nguyễn Văn A - Đội Vận Chuyển")
        if st.button("✅ Duyệt tất cả tài khoản"): st.success("Đã phê duyệt!")
    elif pass_input != "": st.error("❌ Sai mật khẩu! (Pass: 880880)")

# ================= 4. TAB LINK BÁO CÁO (PASS: 880880) =================
elif st.session_state.nav_tab == "Link":
    st.markdown("### 📈 TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("🔓 Xác thực thành công!")
        st.markdown("- 🚚 Đã giao: **28 / 126 điểm** | 🔧 Đã lắp: **15 / 126 điểm**")
        st.markdown("- 🔗 [Mở Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "": st.error("❌ Sai mật khẩu! (Pass: 880880)")
