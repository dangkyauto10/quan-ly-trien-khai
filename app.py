import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Cấu hình quyền truy cập Google Sheets thông qua Service Account
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def init_connection():
    # Đọc thông tin xác thực từ file credentials.json có sẵn trong kho
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    
    # Mở Google Sheet trực tiếp bằng tên hoặc link
    # (Cách an toàn nhất là mở theo tên file chính xác trên Drive)
    sheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH").sheet1
    
    # Lấy toàn bộ dữ liệu chuyển thành DataFrame của pandas
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    st.success("Đã kết nối thành công với Google Sheet qua Service Account!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi kết nối Service Account: {e}")
