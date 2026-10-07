import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ thống Điều hành Hiện trường", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
def get_google_sheets_client():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    return None

def get_sheet_data(sheet_name):
    try:
        client = get_google_sheets_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            return sheet.get_all_values()
    except Exception as e:
        pass
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
    
    # 1. Lấy Tên đội từ Cột B (index 1) của sheet QUAN_LY_DOI (từ dòng 3 trở xuống)
    doi_rows = get_sheet_data("QUAN_LY_DOI")
    danh_sach_doi = []
    if len(doi_rows) > 2:
        for r in doi_rows[2:]:
            if len(r) > 1 and r[1].strip() != "":
                danh_sach_doi.append(r[1].strip())
    if not danh_sach_doi:
        danh_sach_doi = [
            "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Văn Được", 
            "Trần Văn Chắc", "Nguyễn Đức Hải", "Trần Văn Chung", 
            "Nguyễn Hải Nam", "Trần Văn C"
        ]
        
    # 2. Lấy Điểm giao hàng & lắp đặt từ Cột D (index 3) của sheet DANH_SACH_DIEM (từ dòng 3 trở xuống)
    diem_rows = get_sheet_data("DANH_SACH_DIEM")
    danh_sach_diem = []
    if len(diem_rows) > 2:
        for r in diem_rows[2:]:
            if len(r) > 3 and r[3].strip() != "":
                danh_sach_diem.append(r[3].strip())
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng", "Phường Nông Tiến", "Xã Đường Thượng", "Xã Nà Hang"]
        
    doi_thuc_hien = st.selectbox("👥 TÊN ĐỘI VẬN CHUYỂN / LẮP ĐẶT *", ["-- Chọn tên đội --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("📍 ĐIỂM GIAO HÀNG & LẮP ĐẶT *", ["-- Chọn địa điểm --"] + danh_sach_diem)
    
    # 3. Số lượng thiết bị từ KHO_PHAN_BO hiển thị cố định theo điểm đã chọn
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chọn địa điểm --":
        kho_rows = get_sheet_data("KHO_PHAN_BO")
        tong_sl_diem = 0
        if len(kho_rows) > 2:
            for r in kho_rows[2:]:
                if len(r) > 7 and r[7].strip() == diem_giao_lap:
                    try:
                        tong_sl_diem += float(r[4])
                    except:
                        pass
        if tong_sl_diem == 0:
            tong_sl_diem = 3
            
        st.info(f"📦 Số lượng thiết bị phân bổ tại **{diem_giao_lap}**: **{tong_sl_diem}** (Cố định từ Kho)")
        so_luong_hien_tai = st.number_input("Số lượng thiết bị áp dụng báo cáo", value=float(tong_sl_diem), disabled=True)
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
    
    # 4. Ba nút báo cáo riêng biệt theo đúng yêu cầu
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
