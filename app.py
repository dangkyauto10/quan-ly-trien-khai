import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Sử dụng link xuất dữ liệu trực tiếp dưới dạng CSV để chống lỗi 404
url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/export?format=csv"

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet=url)

st.dataframe(data)
