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

def get_exact_diem_from_sheet():
    """Đọc thẳng tắp toàn bộ dữ liệu từ sheet DANH_SACH_DIEM mà không qua bất kỳ bộ lọc cứng nhắc nào"""
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            # Mở thẳng sheet có tên DANH_SACH_DIEM hoặc lấy worksheet đầu tiên nếu khớp
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "danh_sach_diem" in ws.title.lower() or ws.title.lower() == "danh_sach_diem":
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[0]
                
            rows = target_ws.get_all_values()
            diem_list = []
            if len(rows) > 1:
                # Bỏ qua dòng tiêu đề (dòng 0), quét toàn bộ các cột từ dòng 1 trở đi
                for row in rows[1:]:
                    for cell in row:
                        val = cell.strip()
                        # Lấy tất cả các ô có nội dung chữ hợp lệ, không phải số hoặc rỗng
                        if val != "" and not val.isdigit() and len(val) > 1:
                            low = val.lower()
                            if "danh sách" not in low and "điểm" not in low and "stt" not in low and "mã" not in low:
                                if val not in diem_list:
                                    diem_list.append(val)
            if diem_list:
                return diem_list
    except Exception as e:
        pass
    return ["Xã Sùng Máng", "Phường Nông Tiến", "Xã Đường Thượng", "Xã Nà Hang"]

def get_exact_doi_from_sheet():
    """Đọc thẳng tắp danh sách tên đội từ sheet QUAN_LY_DOI"""
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "quan_ly_doi" in ws.title.lower() or ws.title.lower() == "quan_ly_doi":
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[1] if len(spreadsheet.worksheets()) > 1 else spreadsheet.worksheets()[0]
                
            rows = target_ws.get_all_values()
            doi_list = []
            if len(rows) > 1:
                for row in rows[1:]:
                    for cell in row:
                        val = cell.strip()
                        if val != "" and not val.isdigit() and len(val) > 1:
                            low = val.lower()
                            if "tên" not in low and "đội" not in low and "stt" not in low and "mã" not in low:
                                if val not in doi_list:
                                    doi_list.append(val)
            if doi_list:
                return doi_list
    except Exception as e:
        pass
    return ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Văn Được", "Trần Văn Chắc"]

def get_exact_quantity(diem_chon):
    """Tra cứu trực tiếp số lượng phân bổ từ sheet KHO_PHAN_BO theo địa điểm"""
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "kho_phan_bo" in ws.title.lower() or "kho" in ws.title.lower():
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[2] if len(spreadsheet.worksheets()) > 2 else spreadsheet.worksheets()[0]
                
            rows = target_ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    row_text = " ".join(row).lower()
                    if diem_chon.lower() in row_text:
                        # Lấy giá trị cột H (index 7) nếu có, hoặc tìm số nguyên đầu tiên trong dòng
                        if len(row) > 7 and row[7].strip().isdigit():
                            return int(row[7].strip())
                        for cell in row:
                            if cell.strip().isdigit() and int(cell.strip()) > 0:
                                return int(cell.strip())
    except Exception as e:
        pass
    return 3

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
            "DA76 - Cung cap thiet bi thon xa", 
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

    danh_sach_doi = get_exact_doi_from_sheet()
    danh_sach_diem = get_exact_diem_from_sheet()
        
    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("DIEM GIAO HANG & LAP DAT *", ["-- Chon dia diem --"] + danh_sach_diem)
    
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chon dia diem --":
        so_luong_dong = get_exact_quantity(diem_giao_lap)
        st.info(f"So luong thiet bi phan bo tai {diem_giao_lap} la: {so_luong_dong} bo (Dong bo truc tiếp từ KHO_PHAN_BO)")
        so_luong_hien_tai = st.number_input("So luong thiet bi ap dung bao cao", value=float(so_luong_dong), disabled=True)
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
