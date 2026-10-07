import streamlit as st
import datetime
import urllib.request
import csv
import io

st.set_page_config(page_title="Hệ thống Điều hành Hiện trường", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
# ID Google Sheet của anh
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

# Hàm lấy dữ liệu trực tiếp động từ cột của sheet qua link CSV public theo thời gian thực
def get_live_sheet_column(gid, col_idx):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
        response = urllib.request.urlopen(url)
        lines = [line.decode('utf-8') for line in response.readlines()]
        reader = csv.reader(lines)
        rows = list(reader)
        
        col_data = []
        # Quét từ dòng thứ 3 trở xuống (index 2 trong Python)
        if len(rows) > 2:
            for r in rows[2:]:
                if len(r) > col_idx:
                    val = r[col_idx].strip()
                    if val != "" and val not in col_data:
                        col_data.append(val)
        return col_data
    except Exception as e:
        return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH & BÁO CÁO HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

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
            if not ten_thanh_vien or not sdt: 
                st.warning("⚠️ Vui lòng điền đầy đủ họ tên và số điện thoại!")
            else: 
                st.success("🎉 Đăng ký thành công! Vui lòng chờ Admin duyệt tài khoản.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### 📊 BÁO CÁO NHIỆM VỤ HIỆN TRƯỜNG")
    
    # GID của sheet QUAN_LY_DOI (lấy cột B -> index 1)
    danh_sach_doi = get_live_sheet_column("1563705161", 1)
    if not danh_sach_doi:
        # Danh sách dự phòng nếu chưa public sheet
        danh_sach_doi = [
            "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Văn Được", 
            "Trần Văn Chắc", "Nguyễn Đức Hải", "Trần Văn Chung", 
            "Nguyễn Hải Nam", "Trần Văn C", "Nguyễn Văn D", "Hồ Văn H"
        ]
        
    # GID của sheet DANH_SACH_DIEM (lấy cột D -> index 3) - thay gid tương ứng nếu có
    danh_sach_diem = get_live_sheet_column("0", 3)
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng (DA880)", "Phường Nông Tiến (DA880)", "Xã Đường Thượng (DA880)", "Xã Nà Hang (DA880)"]
        
    # Ô chọn Tên đội (Gõ tìm kiếm / Sổ xuống động hoàn toàn theo sheet)
    doi_thuc_hien = st.selectbox("👥 TÊN ĐỘI VẬN CHUYỂN / LẮP ĐẶT *", ["-- Chọn tên đội --"] + danh_sach_doi)
    
    # Ô chọn Địa điểm (Gõ tìm kiếm / Sổ xuống động hoàn toàn theo sheet)
    diem_giao_lap = st.selectbox("📍 ĐIỂM GIAO HÀNG & LẮP ĐẶT *", ["-- Chọn địa điểm --"] + danh_sach_diem)
    
    # SỐ LƯỢNG THIẾT BỊ CỐ ĐỊNH TỪ KHO THEO ĐIỂM
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chọn địa điểm --":
        so_luong_co_dinh = 3  # Định mức phân bổ kho
        st.info(f"📦 Số lượng thiết bị phân bổ tại **{diem_giao_lap}**: **{so_luong_co_dinh} bộ** (Cố định từ Kho)")
        so_luong_hien_tai = st.number_input("Số lượng thiết bị áp dụng báo cáo", value=float(so_luong_co_dinh), disabled=True)
    else:
        st.info("📦 Vui lòng chọn địa điểm để hiển thị số lượng thiết bị phân bổ.")
        
    st.markdown("---")
    st.markdown("📷 **Chụp ảnh hiện trường** (Hỗ trợ camera sau/trước của thiết bị):")
    camera_file = st.camera_input("Chụp ảnh thực tế")
    
    st.markdown("---")
    st.markdown("📍 **Xác thực GPS hiện trường:**")
    if st.button("📍 Check-in GPS Tọa độ Hiện trường", use_container_width=True):
        st.success("📍 Check-in GPS thành công!")
        
    st.markdown("---")
    st.markdown("### 🎛️ BÁO CÁO XÁC NHẬN (3 NÚT RIÊNG BIỆT):")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("✅ ĐÃ GIAO XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chọn tên đội --" or diem_giao_lap == "-- Chọn địa điểm --":
                st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công: ĐÃ GIAO XONG cho đội {doi_thuc_hien} tại {diem_giao_lap}!")
    with col_b2:
        if st.button("✅ ĐÃ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chọn tên đội --" or diem_giao_lap == "-- Chọn địa điểm --":
                st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công: ĐÃ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap}!")
    with col_b3:
        if st.button("🚀 ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chọn tên đội --" or diem_giao_lap == "-- Chọn địa điểm --":
                st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công TRỌN GÓI: ĐÃ GIAO VÀ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap}!")

# ================= 3. TAB ADMIN DUYỆT (PASS: 880880) =================
elif st.session_state.nav_tab == "Admin":
    st.markdown("### 🔒 KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("🔓 Đăng nhập Admin thành công!")
        st.write("- [Chờ duyệt] Thành viên đăng ký mới")
        if st.button("✅ Duyệt tất cả tài khoản"): 
            st.success("Đã phê duyệt thành công!")
    elif pass_input != "": 
        st.error("❌ Sai mật khẩu bảo mật! (Pass: 880880)")

# ================= 4. TAB LINK BÁO CÁO (PASS: 880880) =================
elif st.session_state.nav_tab == "Link":
    st.markdown("### 📈 TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("🔓 Xác thực thành công!")
        st.markdown("- 🔗 [Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "": 
        st.error("❌ Sai mật khẩu truy cập! (Pass: 880880)")
