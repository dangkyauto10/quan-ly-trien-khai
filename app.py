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
    # Đọc trực tiếp từ kho mật khẩu bảo mật của Streamlit Cloud
    secrets_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    sheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    st.success("Kết nối Google Sheet thành công tuyệt đối!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Chi tiết lỗi: {e}")
