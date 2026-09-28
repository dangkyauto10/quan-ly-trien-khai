import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=10) # Tự động cập nhật dữ liệu mới từ Google Sheets mỗi khi reload trang
def lay_danh_sach_doi_tu_sheet():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Xác thực thông qua Service Account đã cấu hình trên Streamlit Cloud (hoặc credentials.json)
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
            
        client = gspread.authorize(creds)
        
        # Mở Google Sheet chính của hệ thống và trỏ đến sheet QUAN_LY_DOI
        spreadsheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        sheet = spreadsheet.worksheet("QUAN_LY_DOI")
        
        # Lấy toàn bộ dữ liệu Cột B (Tên đội), từ hàng 3 trở xuống
        col_b_values = sheet.col_values(2) 
        
        danh_sach = []
        for val in col_b_values[2:]: # Bỏ qua dòng tiêu đề 1 và 2
            v = str(val).strip()
            if v and v.upper() != "TÊN ĐỘI":
                danh_sach.append(v)
                
        return danh_sach if danh_sach else ["VHH", "NTH"]
    except Exception as e:
        # Fallback an toàn tuyệt đối giúp app không bị crash nếu mất mạng tạm thời
        return ["VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A"]

# Đưa vào ô chọn trên giao diện Streamlit (Ví dụ cho Đội thực hiện / Đội nhận TB):
# danh_sach_doi_hien_tai = lay_danh_sach_doi_tu_sheet()
# doi_thuc_hien = st.selectbox("Đội thực hiện *", danh_sach_doi_hien_tai)
