import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN STREAMLIT (TỐI ƯU CHO MOBILE) ---
st.set_page_config(page_title="Hệ Thống Điều Hành Dự Án", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- KẾT NỐI GOOGLE SHEETS BẰNG TỪ ĐIỂN TỐC ĐỘ CAO (DỨT ĐIỂM MỌI LỖI JWT) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    # Lấy thông tin từ st.secrets['gcp_service_account'] và sửa trực tiếp chuỗi private_key
    secrets_dict = dict(st.secrets["gcp_service_account"])
    
    # Xử lý dứt điểm dấu xuống dòng bị lỗi khi đọc từ chuỗi TOML/Secret
    private_key = secrets_dict["private_key"]
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")
    
    creds_dict = {
        "type": secrets_dict["type"],
        "project_id": secrets_dict["project_id"],
        "private_key_id": secrets_dict["private_key_id"],
        "private_key": private_key,
        "client_email": secrets_dict["client_email"],
        "client_id": secrets_dict["client_id"],
        "auth_uri": secrets_dict["auth_uri"],
        "token_uri": secrets_dict["token_uri"],
        "auth_provider_x509_cert_url": secrets_dict["auth_provider_x509_cert_url"],
        "client_x509_cert_url": secrets_dict["client_x509_cert_url"],
        "universe_domain": secrets_dict.get("universe_domain", "googleapis.com")
    }

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
    return client.open_by_url(sheet_url)

try:
    spreadsheet = init_connection()
    st.success("✅ Kết nối Google Sheets thành công tuyệt đối!")
except Exception as e:
    st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
    st.stop()
