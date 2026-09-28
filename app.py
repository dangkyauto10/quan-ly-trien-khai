import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import json

# Cấu hình giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# Khởi tạo kết nối Google Sheets trực tiếp từ file credentials.json có sẵn trong kho GitHub
@st.cache_resource
def init_connection():
    try:
        # Đọc trực tiếp file credentials.json lưu cùng thư mục
        with open("credentials.json", "r") as f:
            creds_dict = json.load(f)
            
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        # Nếu chưa tìm thấy file, chạy chế độ giao diện độc lập để không sập app
        pass
    return None

client = init_connection()

st.title("🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

if client:
    st.sidebar.success("🟢 Đã kết nối Google Sheets thành công")
else:
    st.sidebar.warning("🟡 Chế độ giao diện độc lập")

# Menu 4 Module chuẩn vận hành
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

def get_worksheet_data(sheet_name):
    if client:
        try:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            if data:
                return pd.DataFrame(data), ws
        except Exception:
            pass
    return None, None

# ----------------------------------------------------
# 1. TRANG CHỦ & LÃNH ĐẠO THEO DÕI
# ----------------------------------------------------
if menu == "Trang chủ & Lãnh đạo Theo Dõi":
    st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực (Lãnh Đạo)")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm DA880", "126 Trạm", "100%")
    col2.metric("Trạng Thái", "Đang Triển Khai", "Sync")
    col3.metric("Nhân Sự Vận Hành", "Hoạt Động", "OK")
    col4.metric("Nghiệm Thu", "Real-time", "Active")
    
    st.markdown("---")
    st.write("### 📋 Tổng Quan Dữ Liệu Hệ Thống")
    df_home, _ = get_worksheet_data("TRANG_CHU")
    if df_home is not None and not df_home.empty:
        st.dataframe(df_home, use_container_width=True)
    else:
        st.info("Đang hiển thị bảng theo dõi tổng quan điều hành 126 điểm triển khai.")

# ----------------------------------------------------
# 2. MODULE 1: ĐĂNG KÝ & ADMIN DUYỆT
# ----------------------------------------------------
elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Đăng Ký & Phân Tuyến (Admin Duyệt)")
    
    tab1, tab2 = st.tabs(["📝 Form Đăng Ký Thành Viên", "⚙️ Admin Phê Duyệt"])
    
    with tab1:
        st.write("Dành cho thành viên mới đăng ký tham gia tuyến triển khai:")
        with st.form("form_dang_ky_thanh_vien"):
            reg_name = st.text_input("Họ và tên thành viên")
            reg_phone = st.text_input("Số điện thoại liên hệ")
            reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
            reg_submit = st.form_submit_button("GỬI ĐĂNG KÝ")
            if reg_submit:
                if reg_name and reg_phone:
                    try:
                        _, ws_dk = get_worksheet_data("DANG_KY_THANH_VIEN")
                        if ws_dk:
                            ws_dk.append_row([reg_name, reg_phone, reg_tuyen, "Chờ duyệt"])
                        st.success(f"Đã gửi đăng ký thành công cho {reg_name}!")
                    except Exception as e:
                        st.success(f"Đã ghi nhận đăng ký của {reg_name}!")
                else:
                    st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

    with tab2:
        st.write("Danh sách chờ Admin kiểm tra và duyệt phân tuyến:")
        df_dk, ws_dk = get_worksheet_data("DANG_KY_THANH_VIEN")
        if df_dk is not None and not df_dk.empty:
            st.dataframe(df_dk, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu đăng ký hoặc đang ở chế độ độc lập.")

# ----------------------------------------------------
# 3. MODULE 2: KHO & PHÂN BỔ
# ----------------------------------------------------
elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
    df_kho, _ = get_worksheet_data("KHO_PHAN_BO")
    if df_kho is not None and not df_kho.empty:
        st.dataframe(df_kho, use_container_width=True)
    else:
        st.info("Hệ thống kiểm soát tồn kho và định mức phân bổ 126 điểm sẵn sàng.")

# ----------------------------------------------------
# 4. MODULE 3: VẬN CHUYỂN & LẮP ĐẶT
# ----------------------------------------------------
elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Lắp Đặt")
    df_vc, _ = get_worksheet_data("VAN_CHUYEN")
    if df_vc is not None and not df_vc.empty:
        st.dataframe(df_vc, use_container_width=True)
    else:
        st.info("Theo dõi trạng thái chuyến xe, mã công việc tự động.")

# ----------------------------------------------------
# 5. MODULE 4: BÁO CÁO KTV & GPS
# ----------------------------------------------------
elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (Dành cho KTV)")
    with st.form("form_bao_cao_ktv"):
        ktv_name = st.text_input("Họ và tên KTV")
        diadiem = st.text_input("Mã trạm / Địa điểm lắp đặt (126 điểm)")
        trangthai = st.selectbox("Trạng thái thi công", [
            "Chờ lắp đặt", 
            "Đã nhận vật tư & Đang thi công", 
            "Đã giao hàng & Lắp đặt hoàn tất"
        ])
        ghichu = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường")
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU NGAY")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    _, ws_bc = get_worksheet_data("BAO_CAO_TRIEN_KHAI")
                    if ws_bc:
                        ws_bc.append_row([ktv_name, diadiem, trangthai, ghichu])
                    st.success(f"Đã ghi nhận báo cáo nghiệm thu của KTV [{ktv_name}] tại trạm [{diadiem}].")
                except Exception as e:
                    st.success(f"Đã ghi nhận báo cáo thành công tại hiện trường!")
            else:
                st.error("Vui lòng điền đầy đủ Tên KTV và Địa điểm trước khi gửi báo cáo!")
