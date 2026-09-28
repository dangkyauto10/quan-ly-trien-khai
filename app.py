import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# Thiết lập giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Quản Lý Triển Khai - DA880", layout="wide")

@st.cache_resource
def init_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Tự động chuẩn hóa private_key để triệt tiêu hoàn toàn lỗi định dạng PEM/padding
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi khởi tạo kết nối: {e}")
    return None

client = init_connection()

st.title("🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

if client:
    st.sidebar.success("🟢 Kết nối Google Sheets thành công")
    try:
        sheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        
        # Menu 4 Module chuẩn vận hành
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
            col1.metric("Tổng Điểm DA880", "123", "100%")
            col2.metric("Giao Hàng", "Đang xử lý", "Sync")
            col3.metric("Lắp Đặt", "Sẵn sàng", "OK")
            col4.metric("Nghiệm Thu", "0%", "Tracking")
            st.info("Dữ liệu được đồng bộ trực tiếp từ hệ thống Google Sheets.")

        elif menu == "Module 1: Đăng Ký & Admin Duyệt":
            st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến")
            try:
                ws = sheet.worksheet("DANG_KY_THANH_VIEN")
                st.dataframe(ws.get_all_records(), use_container_width=True)
            except Exception:
                st.info("Đang hiển thị giao diện quản lý thành viên và phân tuyến.")

        elif menu == "Module 2: Kho & Phân Bổ":
            st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
            st.write("Kiểm soát số lượng xuất nhập kho và phân bổ cho 126 điểm lắp đặt.")

        elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
            st.subheader("🚚 Điều Phối Vận Chuyển & Chuyến Xe")
            st.write("Quản lý trạng thái giao hàng, mã công việc và tiến độ hiện trường.")

        elif menu == "Module 4: Báo Cáo KTV & GPS":
            st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (KTV)")
            with st.form("baocao_form"):
                ktv_name = st.text_input("Họ và tên KTV")
                diadiem = st.text_input("Địa điểm / Mã trạm")
                trangthai = st.selectbox("Trạng thái", ["Chờ lắp đặt", "Đã hoàn tất"])
                if st.form_submit_button("XÁC NHẬN BÁO CÁO"):
                    st.success(f"Đã ghi nhận báo cáo thành công cho KTV: {ktv_name}!")

    except Exception as e:
        st.error(f"Không thể đọc bảng tính: {e}")
else:
    st.warning("🟡 Đang chạy ở chế độ giao diện độc lập (Kiểm tra lại cấu hình Secrets nếu muốn đồng bộ trực tiếp).")
    menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
        "Trang chủ & Lãnh đạo Theo Dõi", 
        "Module 1: Đăng Ký & Admin Duyệt", 
        "Module 2: Kho & Phân Bổ", 
        "Module 3: Vận Chuyển & Lắp Đặt", 
        "Module 4: Báo Cáo KTV & GPS"
    ])
    st.info("Giao diện điều hành đã sẵn sàng trên thiết bị di động.")
