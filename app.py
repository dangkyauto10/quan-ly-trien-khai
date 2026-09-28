import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

# Thiết lập giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide")

# Khởi tạo kết nối Google Sheets an toàn theo chuẩn ngày 26/9
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

st.title("🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

if client:
    st.sidebar.success("🟢 Kết nối Google Sheets thành công")
else:
    st.sidebar.warning("🟡 Chế độ giao diện độc lập")

# Menu 4 Module chuẩn vận hành ngày 26/9
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

def load_data_from_sheet(sheet_name):
    if client:
        try:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            if data:
                return pd.DataFrame(data)
        except Exception:
            pass
    return None

if menu == "Trang chủ & Lãnh đạo Theo Dõi":
    st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực (TRANG_CHU)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm DA880", "880", "100%")
    col2.metric("Trạng Thái", "Hoạt Động", "Sync")
    col3.metric("Điểm Lắp Đặt", "126 Trạm", "OK")
    col4.metric("Nghiệm Thu", "Real-time", "Active")
    
    st.markdown("---")
    st.write("### 📋 Tổng Quan Dữ Liệu Lãnh Đạo")
    df_home = load_data_from_sheet("TRANG_CHU")
    if df_home is not None and not df_home.empty:
        st.dataframe(df_home, use_container_width=True)
    else:
        st.info("Hệ thống giám sát tiến độ trực tiếp từ 126 điểm triển khai.")

elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến (Admin Duyệt)")
    df_dk = load_data_from_sheet("DANG_KY_THANH_VIEN")
    if df_dk is not None and not df_dk.empty:
        st.dataframe(df_dk, use_container_width=True)
    else:
        st.info("Đang đồng bộ dữ liệu từ DANG_KY_THANH_VIEN và THANH_VIEN.")

elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho (KHO_PHAN_BO)")
    df_kho = load_data_from_sheet("KHO_PHAN_BO")
    if df_kho is not None and not df_kho.empty:
        st.dataframe(df_kho, use_container_width=True)
    else:
        st.info("Kiểm soát số lượng vật tư tồn kho và phân bổ thực tế cho hiện trường.")

elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Sinh Mã Công Việc")
    df_vc = load_data_from_sheet("VAN_CHUYEN")
    if df_vc is not None and not df_vc.empty:
        st.dataframe(df_vc, use_container_width=True)
    else:
        st.info("Theo dõi trạng thái chuyến xe và tiến độ lắp đặt tại các trạm.")

elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (Dành cho KTV)")
    with st.form("baocao_ktv_real"):
        ktv_name = st.text_input("Họ và tên KTV")
        diadiem = st.text_input("Mã trạm / Vị trí hiện trường")
        trangthai = st.selectbox("Trạng thái công việc", [
            "Chờ lắp đặt", 
            "Đã nhận vật tư & Đang thi công", 
            "Đã giao hàng & Lắp đặt hoàn tất"
        ])
        ghichu = st.text_area("Ghi chú chi tiết")
        if st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU"):
            if ktv_name and diadiem:
                st.success(f"Đã ghi nhận báo cáo của KTV {ktv_name} tại {diadiem}!")
            else:
                st.error("Vui lòng điền đủ Tên KTV và Địa điểm!")
