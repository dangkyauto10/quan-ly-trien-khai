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

def get_smart_column_data(target_sheet_name, col_indices):
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            worksheets = spreadsheet.worksheets()
            
            selected_sheet = None
            for ws in worksheets:
                if ws.title.strip().lower() == target_sheet_name.strip().lower():
                    selected_sheet = ws
                    break
            
            if not selected_sheet and worksheets:
                for ws in worksheets:
                    if target_sheet_name.strip().lower() in ws.title.strip().lower():
                        selected_sheet = ws
                        break
            if not selected_sheet:
                selected_sheet = worksheets[0]

            all_rows = selected_sheet.get_all_values()
            values = []
            if len(all_rows) > 1:
                for row in all_rows[1:]:
                    for idx in col_indices:
                        if len(row) > idx:
                            val = row[idx].strip()
                            if val != "" and not val.isdigit() and val not in values:
                                if "tên đội" not in val.lower() and "địa điểm" not in val.lower() and "khu vực" not in val.lower():
                                    values.append(val)
            return values
    except Exception as e:
        pass
    return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH ĐA DỰ ÁN HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    btn_dang_ky = st.button("📝 Đăng ký", use_container_width=True)
with col2:
    btn_bao_cao = st.button("📊 Báo cáo", use_container_width=True)
with col3:
    btn_admin = st.button("🔒 Admin duyệt", use_container_width=True)
with col4:
    btn_link = st.button("📈 Link báo cáo", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

# ================= 1. TAB ĐĂNG KÝ THÀNH VIÊN =================
if st.session_state.nav_tab == "Dang_ky":
    st.markdown("### 📝 Đ
