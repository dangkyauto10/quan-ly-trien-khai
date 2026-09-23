import streamlit as st
import pandas as pd

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Đường dẫn API chuẩn xác giúp vượt mọi lỗi 404 khi Sheet đã chia sẻ quyền Người xem
sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/gviz/tq?tqx=out:csv"

try:
    data = pd.read_csv(sheet_url)
    st.success("Đã kết nối thành công tới Google Sheet!")
    st.dataframe(data)
except Exception as e:
    st.error(f"Chi tiết lỗi: {e}")
