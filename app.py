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
    
    # Lấy tiêu đề ở hàng 5 và đúng một dòng số liệu ở hàng 6
    headers = sheet.row_values(5)[:4]
    values = sheet.row_values(6)[:4]
    
    df = pd.DataFrame([values], columns=headers)

    st.success("Kết nối Google Sheet thành công tuyệt đối!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Chi tiết lỗi: {e}")
