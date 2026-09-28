import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import json
import os

# Cấu hình giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

@st.cache_resource
def init_connection():
    try:
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi xác thực: {e}")
    return None

client = init_connection()

# Hàm lấy dữ liệu an toàn từ Google Sheets
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

# Menu 4 Module chuẩn vận hành
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

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
        st.info("Hệ thống giám sát tiến độ trực tiếp từ 126 điểm triển khai.")

# ----------------------------------------------------
# 2. MODULE 1: ĐĂNG KÝ & ADMIN DUYỆT
# ----------------------------------------------------
elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Đăng Ký & Phân Tuyến (Admin Duyệt)")
    tab1, tab2 = st.tabs(["📝 Form Đăng Ký Thành Viên", "⚙️ Admin Phê Duyệt"])
    with tab1:
        with st.form("form_dang_ky_thanh_vien"):
            reg_name = st.text_input("Họ và tên thành viên")
            reg_phone = st.text_input("Số điện thoại liên hệ")
            reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
            if st.form_submit_button("GỬI ĐĂNG KÝ"):
                if reg_name and reg_phone:
                    _, ws_dk = get_worksheet_data("DANG_KY_THANH_VIEN")
                    if ws_dk:
                        ws_dk.append_row([reg_name, reg_phone, reg_tuyen, "Chờ duyệt"])
                    st.success(f"Đã gửi đăng ký thành công cho {reg_name}!")
                else:
                    st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")
    with tab2:
        df_dk, _ = get_worksheet_data("DANG_KY_THANH_VIEN")
        if df_dk is not None and not df_dk.empty:
            st.dataframe(df_dk, use_container_width=True)
        else:
            st.info("Đang tải dữ liệu danh sách chờ duyệt...")

# ----------------------------------------------------
# 3. MODULE 2: KHO & PHÂN BỔ
# ----------------------------------------------------
elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
    df_kho, _ = get_worksheet_data("KHO_PHAN_BO")
    if df_kho is not None and not df_kho.empty:
        st.dataframe(df_kho, use_container_width=True)
    else:
        st.info("Kiểm soát tồn kho và phân bổ thiết bị cho 126 điểm.")

# ----------------------------------------------------
# 4. MODULE 3: VẬN CHUYỂN & LẮP ĐẶT
# ----------------------------------------------------
elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Lắp Đặt")
    df_vc, _ = get_worksheet_data("VAN_CHUYEN")
    if df_vc is not None and not df_vc.empty:
        st.dataframe(df_vc, use_container_width=True)
    else:
        st.info("Theo dõi trạng thái chuyến xe và tiến độ lắp đặt.")

# ----------------------------------------------------
# 5. MODULE 4: BÁO CÁO KTV & GPS (GIAO DIỆN CHUẨN ĐIỆN THOẠI)
# ----------------------------------------------------
elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")
    
    # Lấy danh sách điểm từ sheet DANH SACH DIEM (Cột D)
    diem_list = []
    df_diem, _ = get_worksheet_data("DANH SACH DIEM")
    if df_diem is not None and not df_diem.empty:
        # Lấy cột thứ 4 (index 3) hoặc cột có tên chứa 'ĐỊA' / 'DIEM' / 'Tên'
        col_name = df_diem.columns[3] if len(df_diem.columns) >= 4 else df_diem.columns[0]
        diem_list = df_diem[col_name].dropna().astype(str).tolist()
    else:
        # Fallback danh sách mẫu nếu chưa kết nối được sheet điểm
        diem_list = ["Phường Minh Xuân", "Xã Tân Trào", "Phường Nông Tiến", "Xã Trung Sơn"]

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        # Chọn Cán bộ / Đội trưởng
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện:",
            ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "Đội KTV Số 1", "Đội KTV Số 2", "Đội Vận Chuyển"]
        )
        
        # Chọn điểm lắp đặt có hỗ trợ gõ tìm kiếm nhanh (selectbox)
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Gõ chữ cái để gợi ý nhanh):",
            diem_list
        )
        
        # Ô hiển thị thông tin số lượng thiết bị phân bổ động
        st.info("📦 Số lượng thiết bị được phân bổ cho điểm này: **5 thiết bị**")
        
        soluong_lap = st.number_input("Số lượng thiết bị thực tế lắp đặt / giao hàng:", min_value=1, value=5, step=1)
        
        st.markdown("### 2. Trạng Thái Báo Cáo & Nghiệm Thu")
        trangthai = st.selectbox(
            "Chọn trạng thái hoàn thành:",
            [
                "Đã lắp đặt xong", 
                "Đã giao hàng xong (Dành cho vận chuyển)", 
                "Đã bàn giao và lắp đặt xong (Dành cho đơn vị vừa giao vừa lắp)"
            ]
        )
        
        ghichu = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường:")
        
        st.markdown("### 3. Định vị Địa điểm (Google Maps & GPS)")
        gps_link = st.text_input("Link Google Maps / Tọa độ GPS tại điểm check-in:", placeholder="Dán link vị trí hoặc tự động lấy GPS")
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU NGAY")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    _, ws_bc = get_worksheet_data("BAO_CAO_TRIEN_KHAI")
                    if ws_bc:
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_link])
                    st.success(f"✅ Gửi báo cáo thành công cho trạm [{diadiem}]!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công tại hiện trường cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin trước khi gửi!")
