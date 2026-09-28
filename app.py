import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="Quản Lý Triển Khai - DA880", layout="wide")

@st.cache_resource
def init_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Tự động làm sạch định dạng private_key để chống lỗi Invalid padding
            if "private_key" in creds_dict:
                pk = creds_dict["private_key"]
                pk = pk.replace("\\n", "\n")
                creds_dict["private_key"] = pk
                
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
    return None

client = init_connection()

st.title("🚀 Hệ Thống Quản Lý Triển Khai & Điều Hành")

if client:
    st.sidebar.success("🟢 Kết nối Google Sheets thành công")
    try:
        sheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        
        menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
            "Trang chủ & Lãnh đạo Theo Dõi", 
            "Module 1: Đăng Ký & Admin Duyệt", 
            "Module 2: Kho & Phân Bổ", 
            "Module 3: Vận Chuyển & Lắp Đặt", 
            "Module 4: Báo Cáo KTV & GPS"
        ])

        if menu == "Trang chủ & Lãnh đạo Theo Dõi":
            st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tổng Điểm DA880", "880", "100%")
            col2.metric("Giao Hàng", "Sẵn sàng", "OK")
            col3.metric("Lắp Đặt", "Ổn định", "OK")
            col4.metric("Nghiệm Thu", "Tracking", "Active")
            st.info("Hệ thống đã kết nối trực tiếp cơ sở dữ liệu Google Sheets.")

        elif menu == "Module 1: Đăng Ký & Admin Duyệt":
            st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến")
            ws = sheet.worksheet("DANG_KY_THANH_VIEN")
            st.dataframe(ws.get_all_records(), use_container_width=True)

        elif menu == "Module 2: Kho & Phân Bổ":
            st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
            st.write("Đồng bộ số liệu kho và phân bổ vật tư hiện trường.")

        elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
            st.subheader("🚚 Điều Phối Vận Chuyển & Lắp Đặt")
            st.write("Theo dõi tiến độ giao hàng và mã công việc tự động.")

        elif menu == "Module 4: Báo Cáo KTV & GPS":
            st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (KTV)")
            with st.form("baocao_form"):
                ktv_name = st.text_input("Họ và tên KTV")
                diadiem = st.text_input("Địa điểm / Mã trạm")
                trangthai = st.selectbox("Trạng thái", ["Đã hoàn tất", "Đang xử lý"])
                if st.form_submit_button("XÁC NHẬN BÁO CÁO"):
                    st.success(f"Đã ghi nhận báo cáo của {ktv_name}!")

    except Exception as e:
        st.error(f"Lỗi đọc Sheet: {e}")
else:
    st.warning("🟡 Đang chạy ở chế độ giao diện độc lập.")
    menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
        "Trang chủ & Lãnh đạo Theo Dõi", 
        "Module 1: Đăng Ký & Admin Duyệt", 
        "Module 2: Kho & Phân Bổ", 
        "Module 3: Vận Chuyển & Lắp Đặt", 
        "Module 4: Báo Cáo KTV & GPS"
    ])
    st.info("Giao diện đã sẵn sàng thao tác trên điện thoại.")
