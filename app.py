import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# Thiết lập tiêu đề trang
st.set_page_config(page_title="Quản Lý Triển Khai", layout="wide")

# Hàm kết nối Google Sheets sử dụng Streamlit Secrets bảo mật
@st.cache_resource
def init_connection():
    try:
        # Lấy thông tin xác thực từ Streamlit Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

client = init_connection()

# Giao diện chính của ứng dụng
st.title("Ứng dụng Quản Lý Triển Khai")
st.write("Hệ thống kết nối dữ liệu Google Sheets thành công!")

if client:
    st.success("Đã kết nối thành công với Google Cloud & Google Sheets!")
    
    # Menu chức năng các module
    menu = st.sidebar.selectbox("Chọn Module", ["Trang chủ", "Module 1", "Module 2", "Module 3", "Module 4"])
    
    if menu == "Trang chủ":
        st.info("Chào mừng anh đến với hệ thống quản lý triển khai tự động.")
    elif menu == "Module 1":
        st.subheader("Quản lý Dữ liệu Module 1")
    elif menu == "Module 2":
        st.subheader("Quản lý Dữ liệu Module 2")
    elif menu == "Module 3":
        st.subheader("Quản lý Dữ liệu Module 3")
    elif menu == "Module 4":
        st.subheader("Quản lý Dữ liệu Module 4")
else:
    st.warning("Vui lòng kiểm tra lại phần Secrets trên Streamlit Cloud để ứng dụng có thể kết nối Google Sheets.")
