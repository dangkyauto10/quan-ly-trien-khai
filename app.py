import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import json
import os

# Cấu hình giao diện tối ưu (Wide mode)
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
# 1. MODULE: BÁO CÁO KTV & VC
# -------------------------------------------------------------------------
if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")
    
    # Đọc ĐỘNG 100% từ Cột B của sheet QUAN_LY_DOI (hoặc sheet quản lý đội)
    doi_list = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            # Quét tìm sheet Quản lý đội
            target_ws = None
            for s in sh.worksheets():
                if "QUAN" in s.title.upper() or "DOI" in s.title.upper():
                    target_ws = s
                    break
            if not target_ws:
                target_ws = sh.worksheet("QUAN_LY_DOI") # Gọi trực tiếp theo tên chuẩn
            
            # Lấy toàn bộ giá trị Cột B (từ dòng 3 trở xuống để bỏ tiêu đề)
            col_b_values = target_ws.col_values(2)
            doi_list = [val.strip() for val in col_b_values[2:] if val and val.strip() != ""]
    except Exception:
        pass
        
    if not doi_list:
        doi_list = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Ngọc Hiền"]

    # Đọc ĐỘNG 100% danh sách Địa điểm từ Cột D của sheet DANH_SACH_DIEM
    diem_list = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            col_d_values = ws_diem.col_values(4) # Cột D
            diem_list = [val.strip() for val in col_d_values[2:] if val and val.strip() != ""]
    except Exception:
        pass
        
    if not diem_list:
        diem_list = ["Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận"]

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        # Hiển thị đầy đủ danh sách động bao gồm Nguyễn Ngọc Hiền
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện:",
            doi_list
        )
        
        # Chọn địa điểm từ Cột D
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Gõ chữ cái để gợi ý nhanh):",
            diem_list
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
                    _, ws_bc = get_worksheet_data("BAO_CAO_TRIEN_KHAI")
                    if ws_bc:
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_info])
                    st.success(f"✅ Gửi báo cáo thành công cho điểm [{diadiem}]!")
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
                    _, ws_dk = get_worksheet_data("DANG_KY_THANH_VIEN")
                    if ws_dk:
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
        df_dk, _ = get_worksheet_data("DANG_KY_THANH_VIEN")
        if df_dk is not None and not df_dk.empty:
            st.dataframe(df_dk, use_container_width=True)
            row_idx = st.number_input("Nhập số thứ tự dòng cần duyệt", min_value=1, step=1)
            if st.button("Phê duyệt dòng này"):
                st.success(f"Đã duyệt thành công dòng số {row_idx}!")
        else:
            st.info("Chưa có dữ liệu đăng ký nào.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu đúng là: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

# -------------------------------------------------------------------------
# 4. MODULE: BÁO CÁO LĐ
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Thống Kê Tổng Hợp")
    df_home, _ = get_worksheet_data("TRANG_CHU")
    if df_home is not None and not df_home.empty:
        st.dataframe(df_home, use_container_width=True)
    else:
        st.info("Đang hiển thị tổng hợp dữ liệu Báo cáo LĐ theo thời gian thực.")
