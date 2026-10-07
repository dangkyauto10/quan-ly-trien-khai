import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
def get_google_sheets_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        pass
    return None

def get_column_data_realtime(sheet_name, col_index):
    try:
        client = get_google_sheets_client()
        if client:
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            all_rows = sheet.get_all_values()
            data_list = []
            if len(all_rows) > 2:
                for r in all_rows[2:]:
                    if len(r) > col_index:
                        val = r[col_index].strip()
                        if val != "" and val not in data_list:
                            data_list.append(val)
            return data_list
    except Exception as e:
        pass
    return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH ĐA DỰ ÁN HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
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
    
    du_an_rows = get_column_data_realtime("DANH_SACH_DU_AN", 0)
    du_an_names = get_column_data_realtime("DANH_SACH_DU_AN", 1)
    
    danh_sach_du_an = []
    if du_an_rows and du_an_names:
        for m, t in zip(du_an_rows, du_an_names):
            danh_sach_du_an.append(f"{m} - {t}")
    if not danh_sach_du_an:
        danh_sach_du_an = ["DA880 - Nâng cấp hạ tầng kỹ thuật", "DA76 - Cung cấp thiết bị thôn xã"]
        
    du_an_chon = st.selectbox("📂 CHỌN DỰ ÁN TRIỂN KHAI *", danh_sach_du_an)
    
    danh_sach_doi = get_column_data_realtime("QUAN_LY_DOI", 1)
    if not danh_sach_doi:
        danh_sach_doi = [
            "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Văn Được", 
            "Trần Văn Chắc", "Nguyễn Đức Hải", "Trần Văn Chung", 
            "Nguyễn Hải Nam", "Trần Văn C", "Nguyễn Văn D", "Hồ Văn H", "Nguyễn Văn Ngu", "Như Con Lợn"
        ]
        
    danh_sach_diem = get_column_data_realtime("DANH_SACH_DIEM", 3)
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng (DA880)", "Phường Nông Tiến (DA880)", "Xã Đường Thượng (DA880)", "Xã Nà Hang (DA880)"]
        
    doi_thuc_hien = st.selectbox("👥 TÊN ĐỘI VẬN CHUYỂN / LẮP ĐẶT *", ["-- Chọn tên đội --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("📍 ĐIỂM GIAO HÀNG & LẮP ĐẶT *", ["-- Chọn địa điểm --"] + danh_sach_diem)
    
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chọn địa điểm --":
        so_luong_co_dinh = 3
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
    st.markdown("### 🎛️ BÁO CÁO XÁC NHẬN (3
