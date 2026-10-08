import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        pass
    return None

def get_universal_column_data(col_idx):
    """Hàm quét triệt để: Lấy thẳng dữ liệu từ tab đầu tiên của file Google Sheets theo đúng cột chỉ định"""
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            worksheets = spreadsheet.worksheets()
            if worksheets:
                # Lấy luôn tab đầu tiên để quét dữ liệu chống sai tên tab
                target_ws = worksheets[0]
                all_rows = target_ws.get_all_values()
                values = []
                if len(all_rows) > 1:
                    for row in all_rows[1:]:
                        if len(row) > col_idx:
                            val = row[col_idx].strip()
                            if val != "" and val not in values:
                                values.append(val)
                return values
    except Exception as e:
        pass
    return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH ĐA
