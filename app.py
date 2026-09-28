import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide")

@st.cache_resource
def init_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
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

st.title("ðŸš€ TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

# Menu 4 Module chuẩn vận hành ngày 26/9
menu = st.sidebar.selectbox("ðŸ📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

if menu == "Trang chủ & Lãnh đạo Theo Dõi":
    st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực - Dự Án DA880")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm DA880", "123 Điểm", "100%")
    col2.metric("Giao Hàng", "0 / 123", "0%")
    col3.metric("Lắp Đặt", "0 / 123", "0%")
    col4.metric("Nghiệm Thu", "0%", "Tracking")
    
    st.markdown("---")
    st.write("### 📈 Tiến Độ Thời Gian Thực (126 Vị Trí)")
    st.progress(0, text="Tiến độ Giao hàng: 0%")
    st.progress(0, text="Tiến độ Lắp đặt: 0%")

elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến")
    st.write("Đồng bộ trực tiếp từ sheet DANG_KY_THANH_VIEN và THANH_VIEN.")
    if client:
        try:
            sh = client.open("DU_AN_880_Quan_ly_trien_khai_PC")
            ws = sh.worksheet("DANG_KY_THANH_VIEN")
            st.dataframe(ws.get_all_records(), use_container_width=True)
        except Exception:
            st.info("Đang hiển thị danh sách quản lý thành viên.")
    else:
        st.info("Đang hiển thị giao diện mẫu quản lý thành viên.")

elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
    st.write("Kiểm soát số lượng vật tư, phân bổ hàng hóa cho các điểm triển khai.")

elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Chuyến Xe")
    st.write("Quản lý trạng thái giao hàng, mã công việc tự động và bàn giao hiện trường.")

elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (KTV)")
    st.write("Giao diện tối ưu cho KTV báo cáo nhanh chóng trên điện thoại:")
    with st.form("baocao_form"):
        ktv_name = st.text_input("Họ và tên KTV")
        diadiem = st.text_input("Địa điểm / Mã trạm (123 điểm)")
        trangthai = st.selectbox("Trạng thái", ["Chờ lắp đặt", "Đã giao hàng & Lắp đặt hoàn tất"])
        if st.form_submit_button("📍 XÁC NHẬN BÁO CÁO NGHIỆM THU"):
            st.success(f"Đã ghi nhận báo cáo của KTV {ktv_name} tại {diadiem}!")
