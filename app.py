import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Kết nối trực tiếp với file credentials.json vừa tải lên GitHub
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(creds)

# Mở file Google Sheet và hiển thị dữ liệu
sheet_name = "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH"
sh = gc.open(sheet_name)
worksheet = sh.get_worksheet(0)
data = worksheet.get_all_records()

st.title("Quản lý triển khai")
st.success(f"Đã kết nối thành công tới Google Sheet: {sheet_name}")
st.dataframe(data)
