import streamlit as st
import pandas as pd

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Link xuất trực tiếp CSV chuẩn xác từ Google Sheet công khai
sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/export?format=csv"

data = pd.read_csv(sheet_url)
st.dataframe(data)
