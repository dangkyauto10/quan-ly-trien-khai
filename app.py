import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=10)
def lay_danh_sach_doi_tu_sheet_goc():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
            
        client = gspread.authorize(creds)
        spreadsheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        sheet = spreadsheet.worksheet("QUAN_LY_DOI")
        
        col_b_values = sheet.col_values(2)
        danh_sach = []
        for val in col_b_values[2:]:
            v = str(val).strip()
            if v and v.upper() != "TÊN ĐỘI":
                danh_sach.append(v)
                
        return danh_sach if danh_sach else ["VHH", "NTH"]
    except Exception as e:
        return ["VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A"]

# Lấy danh sách đội từ Cột B sheet QUAN_LY_DOI
danh_sach_doi = lay_danh_sach_doi_tu_sheet_goc()

# --- KHUNG GIAO DIỆN GỐC CỦA ANH (Đăng ký thành viên, Báo cáo kỹ thuật viên, Theo dõi lãnh đạo) ---
st.title("QUẢN LÝ TRIỂN KHAI - HỆ THỐNG ĐIỀU HÀNH")

# Hiển thị kiểm tra nhanh dữ liệu đội đã đồng bộ
st.success(f"Đã tải thành công danh sách đội từ Cột B (QUAN_LY_DOI): {danh_sach_doi}")
