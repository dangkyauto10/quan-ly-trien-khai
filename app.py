import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Kết nối trực tiếp bằng đường link gốc chuẩn của Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/edit")

st.dataframe(data)
