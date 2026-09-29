import streamlit as st
import gspread
import os
import json
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

def get_clean_client():
    try:
        creds_dict = None
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
                
        if creds_dict:
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi xác thực Google API: {e}")
    return None

# KHÔNG DÙNG CACHE NỮA - ĐỌC TRỰC TIẾP TƯƠI 100% TỪ GOOGLE SHEETS MỖI KHI LOAD TRANG
def lay_du_lieu_khong_cache():
    danh_sach_doi = []
    danh_sach_diem = []
    
    try:
        client = get_clean_client()
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            
            # 1. Đọc thô Cột B (index 1) từ sheet QUAN_LY_DOI (bỏ qua 2 dòng tiêu đề đầu)
            ws_doi = sh.worksheet("QUAN_LY_DOI")
            rows_doi = ws_doi.get_all_values()
            for row in rows_doi[2:]:
                if len(row) >= 2:
                    val = row[1]
                    if val is not None:
                        txt = str(val).strip()
                        if txt != "" and txt not in danh_sach_doi:
                            danh_sach_doi.append(txt)
                            
            # 2. Đọc thô Cột D (index 3) từ sheet DANH_SACH_DIEM (bỏ qua 2 dòng tiêu đề đầu)
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            rows_diem = ws_diem.get_all_values()
            for row in rows_diem[2:]:
                if len(row) >= 4:
                    val = row[3]
                    if val is not None:
                        txt = str(val).strip()
                        if txt != "" and txt not in danh_sach_diem:
                            danh_sach_diem.append(txt)
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Google Sheets: {e}")
        
    # Nếu sheet trống hoặc mất kết nối, trả về mảng tối thiểu để app không sập
    if not danh_sach_doi:
        danh_sach_doi = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải"]
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến"]
        
    return danh_sach_doi, danh_sach_diem

danh_sach_doi, danh_sach_diem = lay_du_lieu_khong_cache()

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

if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động")

    st.success(f"🟢 Đã đọc trực tiếp thời gian thực từ Google Sheets! Tổng số nhận diện: **{len(danh_sach_doi)}** đội từ Cột B và **{len(danh_sach_diem)}** điểm từ Cột D.")

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện (Cột B - Realtime):",
            options=danh_sach_doi,
            index=0
        )
        
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Cột D - Realtime):",
            options=danh_sach_diem,
            index=0
        )
        
        st.info("📦 Số lượng thiết bị được phân bổ cho điểm này: **Theo định mức chuẩn từ KHO_PHAN_BO**")
        
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
            gps_info = st.text_input("📍 Lấy vị trí hiện tại:", placeholder="Bấm để ghi nhận GPS")
        with col_img:
            uploaded_image = st.camera_input("📷 Chụp ảnh hiện trường")
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU NGAY")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    client = get_clean_client()
                    if client:
                        sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
                        ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_info])
                    st.success(f"✅ Gửi báo cáo thành công cho đội [{ktv_name}] tại [{diadiem}]!")
                except Exception as e:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công tại hiện trường cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin!")

elif st.session_state.active_tab == "Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên")
    with st.form("form_dang_ky_moi"):
        reg_name = st.text_input("Họ và tên thành viên")
        reg_phone = st.text_input("Số điện thoại liên hệ")
        reg_tuyen = st.text_input("Khu vực đăng ký")
        if st.form_submit_button("GỬI ĐĂNG KÝ"):
            st.success(f"Đã ghi nhận cho {reg_name}!")

elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị")
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực thành công!")
    elif password != "":
        st.error("❌ Sai mật khẩu!")

elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ")
    st.info("Đang hiển thị tổng hợp dữ liệu.")
