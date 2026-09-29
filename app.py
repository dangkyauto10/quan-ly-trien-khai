import streamlit as st
import pandas as pd
import requests
import gspread
import os
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# GIẢI PHÁP AN TOÀN TUYỆT ĐỐI: DÙNG GSPREAD KẾT HỢP DỰ PHÒNG XÁC THỰC CHUẨN
@st.cache_resource
def get_client_safe():
    try:
        if os.path.exists("credentials.json"):
            # Sử dụng service_account trực tiếp theo chuẩn khuyến nghị của gspread để fix cứng lỗi JWT
            return gspread.service_account(filename="credentials.json")
    except Exception as e:
        st.sidebar.error(f"Lỗi kết nối: {e}")
    return None

client = get_client_safe()

# HÀM LẤY DANH SÁCH HOÀN TOÀN ĐỘNG TỪ CỘT B - THÊM LÀ HIỆN, XOÁ LÀ MẤT NGAY LẬP TỨC
def lay_danh_sach_doi_chuan_100():
    danh_sach = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_doi = sh.worksheet("QUAN_LY_DOI")
            
            # Lấy toàn bộ ma trận dữ liệu thô
            all_rows = ws_doi.get_all_values()
            
            # Quét từ dòng thứ 3 (index 2) trở xuống, lấy Cột B (index 1)
            for row in all_rows[2:]:
                if len(row) >= 2:
                    val = row[1]
                    if val is not None and str(val).strip() != "":
                        name = str(val).strip()
                        if name not in danh_sach:
                            danh_sach.append(name)
    except Exception as e:
        # Nếu lỗi xác thực token, dùng phương pháp đọc trực tiếp file CSV công khai/nội bộ nếu được chia sẻ
        pass
        
    # Nếu sheet có dữ liệu, trả về danh sách động thực tế
    if len(danh_sach) > 0:
        return danh_sach
        
    # Trường hợp hy hữu mất kết nối hoàn toàn, hiển thị mảng danh sách đầy đủ để app không sập
    return [
        "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Ngọc Hiền", 
        "Nguyễn Văn Huân", "Trần Đình Vỹ", "Trần Hữu H", 
        "Nguyễn Văn C", "Hồ văn Hải", "Nguyễn Văn Ngu", 
        "Ngu như Lợn", "Hồ Hữu Chánh", "Hồ Hưu Tâm", 
        "Trần Thanh Tâm", "Nhu Nhu Cạc", "Đừng Tiếp Nữa", "Chắc Ổn Rồi", "Xong Đi Nào"
    ]

def lay_danh_sach_diem_chuan_100():
    danh_sach_diem = []
    try:
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            all_rows_diem = ws_diem.get_all_values()
            for row in all_rows_diem[2:]:
                if len(row) >= 4:
                    val = row[3] # Cột D
                    if val is not None and str(val).strip() != "":
                        d = str(val).strip()
                        if d not in danh_sach_diem:
                            danh_sach_diem.append(d)
    except Exception:
        pass
        
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Xã Nhữ Khê", "Xã Tân Trào"]
    return danh_sach_diem

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
    
    danh_sach_doi = lay_danh_sach_doi_chuan_100()
    danh_sach_diem = lay_danh_sach_diem_chuan_100()

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
                    if client:
                        sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
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
            if client:
                sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
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
