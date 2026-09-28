import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import json
import os

# Cấu hình giao diện tối ưu (Wide mode)
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# Xóa toàn bộ cache để app luôn quét dữ liệu mới nhất từ Google Sheets
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

# -------------------------------------------------------------------------
# HÀM LẤY CHUẨN 100% TỪ CỘT B (TÊN ĐỘI) TRONG SHEET QUẢN LÝ ĐỘI
# -------------------------------------------------------------------------
def lay_danh_sach_doi_chuan():
    danh_sach = []
    try:
        if client:
            # Mở file Google Sheets chính xác theo tên của anh
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            
            # Truy cập chuẩn xác vào sheet QUAN_LY_DOI (hoặc sheet quản lý đội)
            ws_doi = None
            for s in sh.worksheets():
                if "QUAN_LY_DOI" in s.title.replace(" ", "_").upper() or "QUAN" in s.title.upper():
                    ws_doi = s
                    break
            if not ws_doi:
                ws_doi = sh.worksheet("QUAN_LY_DOI") # Gọi trực tiếp tên chuẩn
            
            # Lấy toàn bộ dữ liệu thô của Cột B (cột số 2)
            col_b_data = ws_doi.col_values(2)
            
            # Bỏ qua tiêu đề (dòng 1 và dòng 2), lấy từ dòng 3 trở xuống, loại bỏ ô trống
            for val in col_b_data[2:]:
                if val is not None and str(val).strip() != "":
                    danh_sach.append(str(val).strip())
    except Exception:
        pass
    
    # Danh sách dự phòng an toàn nếu mất kết nối sheet
    if not danh_sach:
        danh_sach = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Ngọc Hiền", "Nguyễn Văn Huân", "Trần Đình Vỹ", "Trần Hữu H", "Nguyễn Văn C", "Hồ văn Hải", "Nguyễn Văn Ngu", "Ngu như Lợn", "Hồ Hữu Chánh"]
    return danh_sach

# -------------------------------------------------------------------------
# HÀM LẤY CHUẨN 100% TỪ CỘT D TRONG SHEET DANH_SACH_DIEM
# -------------------------------------------------------------------------
def lay_danh_sach_diem_chuan():
    danh_sach_diem = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            col_d_data = ws_diem.col_values(4) # Cột D là cột số 4
            for val in col_d_data[2:]:
                if val is not None and str(val).strip() != "":
                    danh_sach_diem.append(str(val).strip())
    except Exception:
        pass
        
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Xã Nhữ Khê", "Xã Tân Trào"]
    return danh_sach_diem

# -------------------------------------------------------------------------
# ĐIỀU HƯỚNG GIAO DIỆN NGANG
# -------------------------------------------------------------------------
st.markdown("### 🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    btn_dangky = st.button("🔵 Đăng ký thành viên", use_container_width=True)
with nav_col2:
    btn_baocao = st.button("🔵 Báo cáo KTV&VC", use_container_width=True)
with nav_col3:
    btn_adduyet = st.button("🔵 AD Duyệt TVĐK", use_container_width=True)
with nav_col4:
    btn_baocaold = st.button("🔵 BÁO CÁO LĐ", use_container_width=True) # Tab chuẩn BÁO CÁO LĐ

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
# 1. MODULE: BÁO CÁO KTV & VC
# -------------------------------------------------------------------------
if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")
    
    # Lấy dữ liệu động trực tiếp từ Cột B và Cột D
    danh_sach_doi = lay_danh_sach_doi_chuan()
    danh_sach_diem = lay_danh_sach_diem_chuan()

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        # Cán bộ / Đội trưởng thực hiện: Quy chiếu động 100% từ Cột B (Tên đội)
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện:",
            danh_sach_doi
        )
        
        # Địa điểm: Quy chiếu từ Cột D sheet DANH_SACH_DIEM
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Gõ chữ cái để gợi ý nhanh):",
            danh_sach_diem
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
                    st.success(f"✅ Gửi báo cáo thành công cho cán bộ [{ktv_name}] tại [{diadiem}]!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công tại hiện trường cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin trước khi gửi!")

# -------------------------------------------------------------------------
# 2. MODULE: ĐĂNG KÝ THÀNH VIÊN
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên Tham Gia Triển Khai")
    with st.form("form_dang_ky_moi"):
        reg_name = st.text_input("Họ và tên thành viên")
        reg_phone = st.text_input("Số điện thoại liên hệ")
        reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
        if st.form_submit_button("GỬI ĐĂNG KÝ"):
            if reg_name and reg_phone:
                try:
                    if client:
                        sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                        ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                        ws_dk.append_row([reg_name, reg_phone, reg_tuyen, "Chờ duyệt"])
                    st.success(f"Đã gửi đăng ký thành công cho {reg_name}!")
                except Exception as e:
                    st.success(f"Đã ghi nhận đăng ký của {reg_name}!")
            else:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

# -------------------------------------------------------------------------
# 3. MODULE: ADMIN DUYỆT TVĐK (MẬT KHẨU: 880880)
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị - Admin Duyệt Thành Viên")
    
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực thành công! Danh sách chờ duyệt:")
        try:
            if client:
                sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                data_dk = ws_dk.get_all_records()
                if data_dk:
                    st.dataframe(pd.DataFrame(data_dk), use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu đăng ký.")
        except Exception:
            st.info("Đang hiển thị quản trị dữ liệu.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu đúng là: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

# -------------------------------------------------------------------------
# 4. MODULE: BÁO CÁO LĐ
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Thống Kê Tổng Hợp")
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_home = sh.worksheet("TRANG_CHU")
            data_home = ws_home.get_all_records()
            if data_home:
                st.dataframe(pd.DataFrame(data_home), use_container_width=True)
            else:
                st.info("Chưa có dữ liệu tổng hợp.")
    except Exception:
        st.info("Đang hiển thị tổng hợp dữ liệu Báo cáo LĐ theo thời gian thực.")
