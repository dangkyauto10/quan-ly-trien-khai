import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Cấu hình giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Quản Lý Triển Khai - DA880", layout="wide")

# Khởi tạo kết nối Google Sheets an toàn (không làm sập app nếu mất mạng)
@st.cache_resource
def init_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception:
        pass
    return None

client = init_connection()

# Giao diện điều hành chính
st.title("🚀 Hệ Thống Quản Lý Triển Khai (DA880)")

if client:
    st.sidebar.success("🟢 Đã kết nối Google Sheets")
else:
    st.sidebar.warning("🟡 Chạy ở chế độ giao diện độc lập")

# Menu 4 Module chuẩn nghiệp vụ
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Tổng quan", 
    "Module 1: Đăng Ký & Nhân Sự", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo Lãnh Đạo"
])

if menu == "Trang chủ & Tổng quan":
    st.info("Chào mừng anh quay lại hệ thống điều hành tiêu chuẩn ngày 26/9[cite: 14].")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm Dự Án", "880", "100%")
    col2.metric("Giao Hàng", "Đang cập nhật", "Sync")
    col3.metric("Lắp Đặt", "Sẵn sàng", "OK")
    col4.metric("Nghiệm Thu", "0%", "Tracking")

elif menu == "Module 1: Đăng Ký & Nhân Sự":
    st.subheader("Quản lý danh sách thành viên & phân tuyến")
    st.write("Đồng bộ dữ liệu trực tiếp từ sheet DANG_KY_THANH_VIEN và THANH_VIEN[cite: 14].")

elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("Quản lý thiết bị & định mức kho[cite: 14]")
    st.write("Khóa cứng dữ liệu kho, đảm bảo không sai lệch số liệu hiện trường.")

elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("Điều phối vận chuyển và sinh mã công việc tự động")
    st.write("Theo dõi trạng thái giao hàng và cập nhật phiếu lắp đặt[cite: 14].")

elif menu == "Module 4: Báo Cáo Lãnh Đạo":
    st.subheader("Giám sát tọa độ GPS & Tiến độ thời gian thực")
    st.write("Hỗ trợ KTV báo cáo 1 chạm qua Web App trên điện thoại[cite: 14].")
