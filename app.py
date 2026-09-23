import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Kết nối đúng chuẩn với GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

# Đọc dữ liệu từ đúng link Google Sheet của anh
data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/edit")
st.dataframe(data)
