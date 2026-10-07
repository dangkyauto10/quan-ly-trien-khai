import streamlit as st
import datetime

# Cấu hình trang
st.set_page_config(page_title="Hệ thống Điều hành Hiện trường - Dự án", page_icon="🚀", layout="centered")

# Mật khẩu bảo vệ cho Admin và Link báo cáo
SECURE_PASS = "880880"

# Giao diện tiêu đề chính
st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH & BÁO CÁO HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

# 4 NÚT ĐIỀU HƯỚNG CHÍNH Ở TRÊN CÙNG
col1, col2, col3, col4 = st.columns(4)

with col1:
    btn_dang_ky = st.button("📝 Đăng ký", use_container_width=True)
with col2:
    btn_bao_cao = st.button("📊 Báo cáo", use_container_width=True)
with col3:
    btn_admin = st.button("🔒 Admin duyệt", use_container_width=True)
with col4:
    btn_link = st.button("📈 Link báo cáo", use_container_width=True)

# Quản lý trạng thái tab đang chọn (mặc định là Báo cáo)
if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "Bao_cao"

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
        
        submitted = st.form_submit_button("Gửi đăng ký", type="primary")
        if submitted:
            if not ten_thanh_vien or not sdt:
                st.warning("⚠️ Vui lòng điền đầy đủ họ tên và số điện thoại!")
            else:
                st.success("🎉 Đăng ký thành công! Vui lòng chờ Admin duyệt tài khoản.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### 📊 BÁO CÁO NHIỆM VỤ HIỆN TRƯỜNG")
    
    # Giả lập danh sách ánh xạ từ Sheet QUAN_LY_DOI (Cột B) và DANH_SACH_DIEM (Cột D)
    danh_sach_doi = ["-- Chọn tên đội --", "Nguyễn Văn Thiện - Đội 01", "Trần Văn C - Đội 02", "Đội Kỹ Thuật Tổng Hợp"]
    danh_sach_diem = ["-- Chọn địa điểm giao / lắp --", "Xã Sùng Máng (DA880)", "Phường Nông Tiến (DA880)", "Xã Đường Thượng (DA880)", "Xã Nà Hang (DA880)"]
    
    # Tên đội (Searchable Dropdown tự động gợi ý khi gõ)
    doi_thuc_hien = st.selectbox("👥 Chọn Tên đội vận chuyển / lắp đặt *", danh_sach_doi)
    
    # Điểm giao hàng & lắp đặt (Searchable Dropdown tự động gợi ý khi gõ)
    diem_giao_lap = st.selectbox("📍 Chọn Điểm giao hàng & Lắp đặt *", danh_sach_diem)
    
    # Hiển thị số lượng thiết bị cố định theo điểm (Lấy từ KHO_PHAN_BO, không cho sửa)
    so_luong_co_dinh = 3  # Giá trị mẫu theo điểm chọn
    if diem_giao_lap != "-- Chọn địa điểm giao / lắp --":
        st.info(filename if 'filename' in locals() else f"📦 Số lượng thiết bị phân bổ tại điểm này: **{so_luong_co_dinh} bộ/chiếc** (Cố định từ Kho)")
        so_luong_hien_tai = st.number_input("Số lượng thiết bị áp dụng báo cáo", value=so_luong_co_dinh, disabled=True)
    else:
        so_luong_hien_tai = 0
        
    st.markdown("---")
    st.markdown("📷 **Chụp ảnh hiện trường** (Hỗ trợ camera sau/trước của thiết bị):")
    # Cho phép chụp trực tiếp từ camera (mặc định sau) hoặc tải ảnh lên
    camera_file = st.camera_input("Chụp ảnh thực tế")
    uploaded_file = st.file_uploader("Hoặc tải ảnh từ thiết bị lên", type=["jpg", "png", "jpeg"])
    
    st.markdown("---")
    st.markdown("📍 **Xác thực GPS hiện trường:**")
    if "gps_checked_bc" not in st.session_state:
        st.session_state.gps_checked_bc = False
        
    if not st.session_state.gps_checked_bc:
        if st.button("📍 Check-in GPS Tọa độ Hiện trường"):
            st.session_state.gps_checked_bc = True
            st.success("📍 Check-in GPS thành công (Lat: 21.82, Long: 105.21)!")
            st.rerun()
    else:
        st.success("✅ Đã xác thực vị trí GPS hiện trường.")
        
        st.markdown("### 🎛️ Chọn thao tác báo cáo hoàn thành:")
        col_b1, col_b2, col_b3 = st.columns(3)
        
        with col_b1:
            if st.button("✅ ĐÃ GIAO XONG", type="primary", use_container_width=True):
                if doi_thuc_hien == danh_sach_doi[0] or diem_giao_lap == danh_sach_diem[0]:
                    st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
                else:
                    st.success("🎉 Đã gửi báo cáo: ĐÃ GIAO XONG thành công!")
                    st.session_state.gps_checked_bc = False
        with col_b2:
            if st.button("✅ ĐÃ LẮP XONG", type="primary", use_container_width=True):
                if doi_thuc_hien == danh_sach_doi[0] or diem_giao_lap == danh_sach_diem[0]:
                    st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
                else:
                    st.success("🎉 Đã gửi báo cáo: ĐÃ LẮP XONG thành công!")
                    st.session_state.gps_checked_bc = False
        with col_b3:
            if st.button("🚀 ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
                if doi_thuc_hien == danh_sach_doi[0] or diem_giao_lap == danh_sach_diem[0]:
                    st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
                else:
                    st.success("🎉 Đã gửi báo cáo TRỌN GÓI: ĐÃ GIAO VÀ LẮP XONG thành công!")
                    st.session_state.gps_checked_bc = False

# ================= 3. TAB ADMIN DUYỆT (BẢO MẬT PASS: 880880) =================
elif st.session_state.nav_tab == "Admin":
    st.markdown("### 🔒 KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    
    if pass_input == SECURE_PASS:
        st.success("🔓 Đăng nhập Admin thành công!")
        st.markdown("#### Danh sách thành viên chờ duyệt:")
        st.write("- [Chờ duyệt] Nguyễn Văn A - Đội Vận Chuyển (SĐT: 0912345678)")
        st.write("- [Chờ duyệt] Lê Văn B - Đội Lắp Đặt (SĐT: 0987654321)")
        
        col_duyet1, col_duyet2 = st.columns(2)
        with col_duyet1:
            if st.button("✅ Duyệt tất cả tài khoản"):
                st.success("Đã phê duyệt thành công các thành viên!")
        with col_duyet2:
            if st.button("❌ Từ chối"):
                st.info("Đã từ chối các yêu cầu.")
    elif pass_input != "":
        st.error("❌ Sai mật khẩu bảo mật! Vui lòng thử lại (Pass: 880880).")
    else:
        st.info("Vui lòng nhập mật khẩu `880880` để tiếp tục.")

# ================= 4. TAB LINK BÁO CÁO (BẢO MẬT PASS: 880880) =================
elif st.session_state.nav_tab == "Link":
    st.markdown("### 📈 TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    
    if pass_link == SECURE_PASS:
        st.success("🔓 Xác thực thành công!")
        st.markdown("---")
        st.markdown("📊 **Hệ thống Dashboard tiến độ thời gian thực (Real-time):**")
        st.markdown("- 🚚 Tổng số điểm đã giao hàng: **28 / 126 điểm**")
        st.markdown("- 🔧 Tổng số điểm đã lắp đặt xong: **15 / 126 điểm**")
        st.markdown("- 🔗 [Bấm vào đây để mở trực tiếp Google Sheets Tổng hợp Hệ thống Điều Hành](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "":
        st.error("❌ Sai mật khẩu truy cập! (Pass: 880880).")
    else:
        st.info("Vui lòng nhập mật khẩu `880880` để xem link báo cáo.")
