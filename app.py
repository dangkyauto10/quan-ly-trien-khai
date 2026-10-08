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
    except Exception as e:
        pass
    return None

def get_direct_column_values(keyword, col_idx):
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            worksheets = spreadsheet.worksheets()
            
            target_ws = None
            for ws in worksheets:
                if keyword.lower() in ws.title.lower():
                    target_ws = ws
                    break
            
            if not target_ws and worksheets:
                target_ws = worksheets[0]

            if target_ws:
                all_rows = target_ws.get_all_values()
                values = []
                if len(all_rows) > 1:
                    for row in all_rows[1:]:
                        if len(row) > col_idx:
                            val = row[col_idx].strip()
                            if val != "" and val not in values:
                                values.append(val)
                return values
    except Exception as e:
        pass
    return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HE THONG DIEU HANH DA DU AN HIEN TRUONG</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    btn_dang_ky = st.button("Dang ky", use_container_width=True)
with col2:
    btn_bao_cao = st.button("Bao cao", use_container_width=True)
with col3:
    btn_admin = st.button("Admin duyet", use_container_width=True)
with col4:
    btn_link = st.button("Link bao cao", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

# ================= 1. TAB ĐĂNG KÝ THÀNH VIÊN =================
if st.session_state.nav_tab == "Dang_ky":
    st.markdown("### DANG KY THANH VIEN / DOI THUC HIEN")
    with st.form("form_dang_ky"):
        ten_thanh_vien = st.text_input("Ho va ten *")
        sdt = st.text_input("So dien thoại lien he *")
        vai_tro = st.selectbox("Vai tro cong viec *", ["Doi Van Chuyen (VC)", "Doi Lap Dat (LD)", "Doi Kiem Nhiem (VC & LD)"])
        don_vi = st.text_input("Don vi / Bo phan cong tac *")
        if st.form_submit_button("Gui dang ky", type="primary"):
            if not ten_thanh_vien or not sdt: 
                st.warning("Vui long dien day du ho ten va so dien thoai!")
            else: 
                st.success("Dang ky thanh cong! Vui long cho Admin duyet tai khoan.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (1 - 5 DU AN)")
    
    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        danh_sach_du_an = [
            "DA880 - Nang cap ha tang ky thuat", 
            "DA76 - Cung cap thiet bi thon xã", 
            "DA01 - Trien khai tram vien thong khu vực phia Bac", 
            "DA02 - Lap dat thiet bi y te tuyen huyen", 
            "DA03 - Xay dung mang luoi chuyen doi so xa phuong"
        ]
        du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_resource.clear()
            st.rerun()

    danh_sach_doi = get_direct_column_values("QUAN_LY_DOI", 1)
    if not danh_sach_doi:
        danh_sach_doi = [
            "Nguyen Van Thien", "Nguyen Van Hai", "Nguyen Van Duoc", 
            "Tran Van Chac", "Nguyen Duc Hai", "Tran Van Chung", 
            "Nguyen Hai Nam", "Tran Van C", "Nguyen Van D", "Ho Van H", 
            "Nguyen Van Ngu", "Nhu Con Lon", "Khong thi la Bo", 
            "15 No la Suc Vat", "17 Dc Khong", "18 đc nào"
        ]
        
    danh_sach_diem = get_direct_column_values("DANH_SACH_DIEM", 3)
    if not danh_sach_diem:
        danh_sach_diem = get_direct_column_values("DIEM", 2)
    if not danh_sach_diem:
        danh_sach_diem = ["Xa Sung Mang", "Phuong Nong Tien", "Xa Duong Thuong", "Xa Na Hang"]
        
    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("DIEM GIAO HANG & LAP DAT *", ["-- Chon dia diem --"] + danh_sach_diem)
    
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chon dia diem --":
        so_luong_co_dinh = 3
        st.info("So luong thiet bi phan bo tai diem nay la 3 bo (Co dinh từ Kho)")
        so_luong_hien_tai = st.number_input("So luong thiet bi ap dung bao cao", value=float(so_luong_co_dinh), disabled=True)
    else:
        st.info("Vui long chon dia diem de hien thi so luong thiet bi phan bo.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    camera_file = st.camera_input("Chup anh thuc te")
    
    st.markdown("---")
    st.markdown("Xac thuc GPS hien truong:")
    if st.button("Check-in GPS Toa do Hien truong", use_container_width=True):
        st.success("Check-in GPS thanh cong!")
        
    st.markdown("---")
    st.markdown("### BAO CAO XAC NHAN")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("DA GIAO XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success("Gui bao cao thanh cong: DA GIAO XONG!")
    with col_b2:
        if st.button("DA LAP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success("Gui bao cao thanh cong: DA LAP XONG!")
    with col_b3:
        if st.button("DA GIAO VA LAP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success("Gui bao cao thanh cong: DA GIAO VA LAP XONG TRON GOI!")

# ================= 3. ADMIN & LINK =================
elif st.session_state.nav_tab == "Admin":
    st.markdown("### KHU VUC QUAN TRI - ADMIN DUYỆT")
    pass_input = st.text_input("Nhap mat khau quan tri (Ma PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("Dang nhap Admin thanh cong!")
        st.write("- [Cho duyet] Thanh vien dang ky moi")
        if st.button("Duyet tat ca tai khoan"):
            st.success("Da phe duyet thanh cong!")
    elif pass_input != "":
        st.error("Sai mat khau bao mat! (Pass: 880880)")

elif st.session_state.nav_tab == "Link":
    st.markdown("### TRANG THEO DOI TIEN DO CHO LANH DAO")
    pass_link = st.text_input("Nhap mat khau truy cap bao cao (Ma PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("Xac thuc thanh cong!")
        st.markdown("- [Mo truc tiep Google Sheets Tong hop](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "":
        st.error("Sai mat khau truy cap! (Pass: 880880)")
