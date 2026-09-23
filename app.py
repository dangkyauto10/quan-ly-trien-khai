import streamlit as st
import pandas as pd

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Đọc trực tiếp dữ liệu chuẩn từ Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9jvUXKf3euh7KGieGwzREBFibOoC4/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(sheet_url)

df = load_data()
st.dataframe(df)
