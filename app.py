import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def init_connection():
    secrets_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    spreadsheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
    sheet = spreadsheet.worksheet("TRANG_CHU")
    
    # Lấy toàn bộ giá trị thô từ dòng 5 trở đi, giới hạn đúng 4 cột A, B, C, D
    rows = sheet.get_values("A5:D")
    
    if len(rows) > 1:
        headers = rows[0] # Dòng 5 làm tiêu đề
        data = rows[1:]   # Các dòng từ dòng 6 trở đi là dữ liệu
        df = pd.DataFrame(data, columns=headers)
    else:
        df = pd.DataFrame()

    st.success("Kết nối Google Sheet thành công tuyệt đối!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Chi tiết lỗi: {e}")
