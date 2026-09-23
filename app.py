import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Kết nối trực tiếp với Google Sheets (chỉ cần link công khai hoặc chia sẻ quyền là đọc được)
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit") # Thay link sheet của anh vào đây

st.dataframe(data)
