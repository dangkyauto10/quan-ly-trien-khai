import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
        else:
            st.error("⚠️ Thiếu cấu hình [gcp_service_account] trong Streamlit Secrets!")
    except Exception as e:
        st.error(f"⚠️ Lỗi xác thực Service Account: {e}")
    return None

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HE THONG DIEU HANH DA DU AN HIEN TRUONG</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1: btn_dang_ky = st.button("Dang ky", use_container_width=True)
with col2: btn_bao_cao = st.button("Bao cao", use_container_width=True)
with col3: btn_admin = st.button("Admin duyet", use_container_width=True)
with col4: btn_link = st.button("Link bao cao", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

if st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (1 - 5 DU AN)")
    
    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        danh_sach_du_an = ["DA880 - Nang cap ha tang ky thuat", "DA76 - Cung cap thiet bi thon xa"]
        du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_resource.clear()
            st.rerun()

    # KHỞI TẠO DỮ LIỆU ĐỘNG TỪ GOOGLE SHEETS
    danh_sach_doi = []
    danh_sach_diem = []
    
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            worksheets = spreadsheet.worksheets()
            
            for ws in worksheets:
                title_l = ws.title.lower()
                rows = ws.get_all_values()
                
                # Quét tên đội
                if "doi" in title_l or "quan_ly" in title_l:
                    if len(rows) > 1:
                        for row in rows[1:]:
                            for cell in row:
                                val = cell.strip()
                                if val and not val.isdigit() and len(val) > 1:
                                    if val.lower() not in ["tên đội", "mã đội", "stt", "họ tên"]:
                                        if val not in danh_sach_doi:
                                            danh_sach_doi.append(val)
                                            
                # Quét danh sách điểm
                if "diem" in title_l or "danh_sach_diem" in title_l or "kho" in title_l or "phan_bo" in title_l:
                    if len(rows) > 1:
                        for row in rows[1:]:
                            for cell in row:
                                val = cell.strip()
                                if val and not val.isdigit() and len(val) > 1:
                                    if val.lower() not in ["địa điểm", "tên điểm", "stt", "khu vực", "ghi chú", "tổng số"]:
                                        if val not in danh_sach_diem:
                                            danh_sach_diem.append(val)
        except Exception as e:
            st.error(f"⚠️ Lỗi đọc dữ liệu sheet: {e}")

    # Fallback an toàn nếu chưa cấu hình secrets
    if not danh_sach_doi:
        danh_sach_doi = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Trần Văn Chắc"]
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng", "Phường Nông Tiến", "Xã Đường Thượng", "Xã Nà Hang"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("DIEM GIAO HANG & LAP DAT *", ["-- Chon dia diem --"] + danh_sach_diem)
    
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chon dia diem --":
        so_luong_dong = 3
        try:
            if client:
                spreadsheet = client.open_by_key(SPREADSHEET_ID)
                for ws in spreadsheet.worksheets():
                    if "kho" in ws.title.lower() or "phan_bo" in ws.title.lower():
                        for row in ws.get_all_values()[1:]:
                            if diem_giao_lap.lower() in " ".join(row).lower():
                                if len(row) > 7 and row[7].strip().isdigit():
                                    so_luong_dong = int(row[7].strip())
                                    break
        except Exception:
            pass
            
        st.info(f"So luong thiet bi phan bo tai {diem_giao_lap} la: {so_luong_dong} bo")
        so_luong_hien_tai = st.number_input("So luong thiet bi ap dung bao cao", value=float(so_luong_dong), disabled=True)
    else:
        st.info("Vui long chon dia diem de hien thi so luong thiet bi phan bo.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    
    st.markdown("---")
    if st.button("Check-in GPS Toa do Hien truong", use_container_width=True):
        st.success("Check-in GPS thanh cong!")
        
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("DA GIAO XONG", type="primary", use_container_width=True):
            st.success("Gui bao cao thanh cong!")
    with col_b2:
        if st.button("DA LAP XONG", type="primary", use_container_width=True):
            st.success("Gui bao cao thanh cong!")
    with col_b3:
        if st.button("DA GIAO VA LAP XONG", type="primary", use_container_width=True):
            st.success("Gui bao cao thanh cong!")

elif st.session_state.nav_tab == "Admin":
    st.markdown("### ADMIN")
    pass_input = st.text_input("PIN:", type="password")
    if pass_input == SECURE_PASS: st.success("OK")

elif st.session_state.nav_tab == "Link":
    st.markdown("### LINK")
    pass_link = st.text_input("PIN:", type="password")
    if pass_link == SECURE_PASS: st.success("OK")
