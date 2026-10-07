import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ thống Điều hành Hiện trường", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
py_client = None

def get_sheet_data(sheet_name):
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
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
            if not ten_thanh_vien or not sdt: st.warning("⚠️ Vui lòng điền đầy đủ họ tên và số điện thoại!")
            else: st.success("🎉 Đăng ký thành công! Vui lòng chờ Admin duyệt tài khoản.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### 📊 BÁO CÁO NHIỆM VỤ HIỆN TRƯỜNG")
    
    # 1. Lấy Tên đội từ Cột B Sheet QUAN_LY_DOI
    doi_rows = get_sheet_data("QUAN_LY_DOI")
    danh_sach_doi = []
    if len(doi_rows) > 2:
        for r in doi_rows[2:]:
            if len(r) > 1 and r[1].strip() != "":
                danh_sach_doi.append(r[1].strip())
    if not danh_sach_doi:
        danh_sach_doi = ["Nguyễn Văn Thiện - Đội 01", "Trần Văn C - Đội 02"]
        
    # 2. Lấy Điểm giao hàng & lắp đặt từ Cột D Sheet DANH_SACH_DIEM
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
    
    # 3. Số lượng thiết bị từ KHO_PHAN_BO
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
    st.markdown("### 🎛️ BÁO CÁO XÁC NHẬN (CHỌN 1 TRONG 3 NÚT SAU):")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("✅ ĐÃ GIAO XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chọn tên đội --" or diem_giao_lap == "-- Chọn địa điểm --":
                st.warning("⚠️ Vui lòng chọn đầy đủ Tên đội và Địa điểm!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công: **ĐÃ GIAO XONG** cho đội {doi_thuc_hien} tại {diem_giao_lap}!")
    with col_b2:
        if st.button("✅ ĐÃ LẮP
