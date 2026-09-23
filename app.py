import streamlit as st
import pandas as pd

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Đường dẫn xuất file CSV đã được mở khóa hoàn toàn sau khi Publish to web
sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/export?format=csv"

try:
    data = pd.read_csv(sheet_url)
    st.success("Đã kết nối thành công tới Google Sheet!")
    st.dataframe(data)
except Exception as e:
    st.error(f"Không thể đọc dữ liệu. Chi tiết lỗi: {e}")
