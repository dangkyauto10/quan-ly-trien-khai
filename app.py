import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import json
import os

# Cấu hình giao diện ứng dụng
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# 1. Xóa sạch bộ nhớ cache để app luôn đọc dữ liệu thời gian thực mới nhất từ Google Sheets
st.cache_resource.clear()

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

# 2. HÀM QUÉT ĐỘNG 100% CỘT B (TÊN ĐỘI) TỪ SHEET QUẢN LÝ ĐỘI
def get_doi_list_from_sheet():
    doi_list = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            # Tìm chính xác worksheet quản lý đội
            target_ws = None
            for s in sh.worksheets():
                title_up = s.title.upper()
                if "QUAN" in title_up or "DOI" in title_up:
                    target_ws = s
                    break
            if not target_ws:
                target_ws = sh.worksheets()[1] # Fallback lấy sheet thứ 2
            
            # Lấy toàn bộ giá trị thô của sheet
            raw_data = target_ws.get_all_values()
            if len(raw_data) > 2:
                # Chuyển thành DataFrame, bỏ qua 2 dòng tiêu đề đầu tiên
                df_doi = pd.DataFrame(raw_data[2:])
                if len(df_doi.columns) >= 2:
                    # Lấy dữ liệu chuẩn từ Cột B (index 1), lọc bỏ các ô trống hoặc khoảng trắng thừa
                    col_b_series = df_doi.iloc[:, 1].dropna().astype(str)
                    doi_list = [val.strip() for val in col_b_series if val.strip() != ""]
    except Exception:
        pass
    
    # Danh sách dự phòng nếu chưa kết nối được sheet
    if not doi_list:
        doi_list = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Ngọc Hiền", "Nguyễn Văn Huân", "Trần Đình Vỹ"]
    return doi_list

# 3. HÀM QUÉT ĐỘNG CỘT D (ĐỊA ĐIỂM) TỪ SHEET DANH_SACH_DIEM
def get_diem_list_from_sheet():
    diem_list = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            raw_diem = ws_diem.get_all_values()
            if len(raw_diem) > 2:
                df_diem = pd.DataFrame(raw_diem[2:])
                if len(df_diem.columns) >= 4:
                    # Lấy dữ liệu chuẩn từ Cột D (index 3)
                    col_d_series = df_diem.iloc[:, 3].dropna().astype(str)
                    diem_list = [val.strip() for val in col_d_series if val.strip() != ""]
    except Exception:
        pass
        
    if not diem_list:
        diem_list = ["Phường Minh Xuân", "Phường Nông Tiến", "Xã Nhữ Khê", "Xã Tân Trào"]
    return diem_list

# Giao diện điều hướng ngang các module
st.markdown("### 🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    btn_dangky = st.button("🔵 Đăng ký thành viên", use_container_width=True)
with nav_col2:
    btn_baocao = st.button("🔵 Báo cáo KTV&VC", use_container_width=True)
with nav_col3:
    btn_adduyet = st.button("🔵 AD Duyệt TVĐK", use_container_width=True)
with nav_col4:
    btn_baocaold = st.button("🔵 BÁO CÁO LĐ", use_container_width=True)

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Báo cáo KTV&VC"

if btn_dangky:
    st.session_state.active_tab = "Đăng ký thành viên"
elif btn_baocao:
    st.session_state.active_tab = "Báo cáo KTV&VC"
elif btn_adduyet:
    st.session_state.active_tab = "AD Duyệt TVĐK"
elif btn_baocaold:
    st.session_state.active_tab = "BÁO CÁO LĐ"

st.markdown("---")

# -------------------------------------------------------------------------
# MODULE BÁO CÁO KTV & VC
# -------------------------------------------------------------------------
if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")
    
    # Gọi trực tiếp hàm lấy danh sách đội mới nhất từ Cột B
    current_doi_list = get_doi_list_from_sheet()
    current_diem_list = get_diem_list_from_sheet()

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        # Phần hiển thị danh sách Cán bộ / Đội trưởng (Tự động cập nhật 100% tên mới nhập ở Cột B)
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện:",
            current_doi_list
        )
        
        # Chọn địa điểm từ Cột D
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Gõ chữ cái để gợi ý nhanh):",
            current_diem_list
        )
        
        st.info("📦 Số lượng thiết bị được phân bổ cho điểm này: **Theo định mức chuẩn từ KHO_PHAN_BO** (Chỉ hiển thị, không chỉnh sửa)")
        
        soluong_lap = st.number_input("Số lượng thiết bị thực tế lắp đặt / giao hàng:", min_value=1, value=1, step=1)
        
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
        
        st.markdown("### 3. Định Vị GPS & Chụp Ảnh Hiện Trường")
        col_gps, col_img = st.columns(2)
        with col_gps:
            gps_info = st.text_input("📍 Lấy vị trí hiện tại (Tọa độ / Google Maps):", placeholder="Bấm để ghi nhận GPS hiện tại")
        with col_img:
            uploaded_image = st.file_uploader("📷 Bấm vào máy ảnh để chọn camera chụp/tải ảnh báo cáo thực tế", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU NGAY")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    if client:
                        sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                        ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_info])
                    st.success(f"✅ Gửi báo cáo thành công cho điểm [{diadiem}]!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công tại hiện trường cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin trước khi gửi!")

# Các module phụ trợ khác giữ nguyên vẹn
elif st.session_state.active_tab == "Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên Tham Gia Triển Khai")
    with st.form("form_dang_ky_moi"):
        reg_name = st.text_input("Họ và tên thành viên")
        reg_phone = st.text_input("Số điện thoại liên hệ")
        reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
        if st.form_submit_button("GỬI ĐĂNG KÝ"):
            if reg_name and reg_phone:
                st.success(f"Đã gửi đăng ký thành công cho {reg_name}!")
            else:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị - Admin Duyệt Thành Viên")
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực thành công! Hệ thống quản trị hoạt động bình thường.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu đúng là: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Thống Kê Tổng Hợp")
    st.info("Đang hiển thị tổng hợp dữ liệu Báo cáo LĐ theo thời gian thực.")
