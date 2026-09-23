import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Lấy trực tiếp thông tin từ Secrets của Streamlit
creds_dict = dict(st.secrets["gcp_service_account"])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
data = sh.get_worksheet(0).get_all_records()

st.title("Quản lý triển khai")
st.success("Đã kết nối thành công tới Google Sheet!")
st.dataframe(data)
