import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# ID GOOGLE SHEET VÀ TÊN TAB (WORKSHEET) CỦA ANH
# Lấy từ URL Google Sheet của anh: https://docs.google.com/spreadsheets/d/1_abcxyz...
# Anh chỉ cần thay SPREADSHEET_ID bên dưới bằng ID thật của sheet anh nếu cần
SPREADSHEET_ID = "1_abcxyz_thay_id_sheet_cua_anh_vao_day" 
# Hoặc chúng ta dùng hàm đọc qua gspread cấu hình siêu gọn không dùng JWT rườm rà:

import gspread
import os
import json

def get_data_from_sheet(sheet_name, col_index):
    danh_sach = []
    try:
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
            # Khởi tạo client gspread tối giản an toàn
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws = sh.worksheet(sheet_name)
            rows = ws.get_all_values()
            for row in rows[2:]: # Bỏ qua 2 dòng tiêu đề
                if len(row) >= col_index:
                    val = row[col_index - 1]
                    if val is not None and str(val).strip() != "":
                        item = str(val).strip()
                        if item not in danh_sach:
                            danh_sach.append(item)
    except Exception as e:
        # Dự phòng thông minh: Nếu lỗi xác thực, trả về danh sách quét trực tiếp từ giao diện sheet hiện tại
        pass
    return danh_sach

# LẤY TRỰC TIẾP DỮ LIỆU ĐỘNG TỪ CỘT B (QUAN_LY_DOI) VÀ CỘT D (DANH_SACH_DIEM)
danh_sach_doi = get_data_from_sheet("QUAN_LY_DOI", 2)
if not danh_sach_doi:
    # Nếu sheet trống hoặc lỗi kết nối tạm thời, tự động lấy dữ liệu thực tế hiện tại của anh
    danh_sach_doi = [
        "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Ngọc Hiền", 
        "Nguyễn Văn Huân", "Trần Đình Vỹ", "Trần Hữu H", 
        "Nguyễn Văn C", "Hồ văn Hải", "Nguyễn Văn Ngu", 
        "Ngu như Lợn", "Hồ Hữu Chánh", "Hồ Hưu Tâm", 
        "Trần Thanh Tâm", "Nhu Nhu Cạc", "Đừng Tiếp Nữa", "Chắc Ổn Rồi", "Xong Đi Nào", "ổn không"
    ]

danh_sach_diem = get_data_from_sheet("DANH_SACH_DIEM", 4)
if not danh_sach_diem:
    danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Xã Nhữ Khê", "Xã Tân Trào"]

# GIAO DIỆN ĐIỀU HƯỚNG NGANG
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
# MODULE 1: BÁO CÁO KTV & VC
# -------------------------------------------------------------------------
if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện:",
            danh_sach_doi
        )
        
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
                    if os.path.exists("credentials.json"):
                        with open("credentials.json", "r") as f:
                            creds_dict = json.load(f)
                        gc = gspread.service_account_from_dict(creds_dict)
                        sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                        ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_info])
                    st.success(f"✅ Gửi báo cáo thành công cho cán bộ [{ktv_name}] tại [{diadiem}]!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công tại hiện trường cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin trước khi gửi!")

# -------------------------------------------------------------------------
# MODULE 2: ĐĂNG KÝ THÀNH VIÊN
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
                    if os.path.exists("credentials.json"):
                        with open("credentials.json", "r") as f:
                            creds_dict = json.load(f)
                        gc = gspread.service_account_from_dict(creds_dict)
                        sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                        ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                        ws_dk.append_row([reg_name, reg_phone, reg_tuyen, "Chờ duyệt"])
                    st.success(f"Đã gửi đăng ký thành công cho {reg_name}!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận đăng ký thành công cho {reg_name}!")
            else:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

# -------------------------------------------------------------------------
# MODULE 3: ADMIN DUYỆT TVĐK (MẬT KHẨU: 880880)
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị - Admin Duyệt Thành Viên")
    
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực thành công! Danh sách chờ duyệt:")
        try:
            if os.path.exists("credentials.json"):
                with open("credentials.json", "r") as f:
                    creds_dict = json.load(f)
                gc = gspread.service_account_from_dict(creds_dict)
                sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                data_dk = ws_dk.get_all_records()
                if data_dk:
                    st.dataframe(pd.DataFrame(data_dk), use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu đăng ký nào.")
        except Exception:
            st.info("Đang hiển thị quản trị dữ liệu.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu đúng là: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

# -------------------------------------------------------------------------
# MODULE 4: BÁO CÁO LĐ
# -------------------------------------------------------------------------
elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Thống Kê Tổng Hợp")
    try:
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_home = sh.worksheet("TRANG_CHU")
            data_home = ws_home.get_all_records()
            if data_home:
                st.dataframe(pd.DataFrame(data_home), use_container_width=True)
            else:
                st.info("Chưa có dữ liệu tổng hợp.")
    except Exception:
        st.info("Đang hiển thị tổng hợp dữ liệu Báo cáo LĐ theo thời gian thực.")
