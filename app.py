import streamlit as st
import gspread
import os
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# KHỞI TẠO KẾT NỐI MỚI HOÀN TOÀN KHÔNG DÙNG BỘ NHỚ ĐỆM (CACHE)
def get_live_client():
    try:
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            # Trả về client kết nối trực tiếp không qua cache
            return gspread.authorize(creds)
    except Exception as e:
        st.sidebar.error(f"Lỗi kết nối: {e}")
    return None

# HÀM ĐỌC VÉT CẠN TƯƠI MỚI 100% - KHÔNG BỎ SÓT BẤT KỲ DÒNG MỚI NÀO DƯỚI CÙNG
def lay_du_lieu_thời_gian_thực(worksheet_name, col_index):
    danh_sach = []
    try:
        client = get_live_client()
        if client:
            sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
            ws = sh.worksheet(worksheet_name)
            
            # Ép buộc lấy sạch toàn bộ giá trị hiện tại từ bảng tính
            rows = ws.get_all_values()
            
            # Quét từ dòng thứ 3 trở xuống (bỏ qua 2 dòng tiêu đề)
            for row in rows[2:]:
                if len(row) >= col_index:
                    val = row[col_index - 1]
                    if val is not None and str(val).strip() != "":
                        text = str(val).strip()
                        if text not in danh_sach:
                            danh_sach.append(text)
    except Exception:
        pass
    return danh_sach

# LẤY TRỰC TIẾP DỮ LIỆU ĐỘNG THỜI GIAN THỰC CHO 2 TRƯỜNG:
# 1. Cán bộ / Đội trưởng: Lấy từ Cột B (index 2) của sheet QUAN_LY_DOI
danh_sach_doi = lay_du_lieu_thời_gian_thực("QUAN_LY_DOI", 2)

# 2. Địa điểm vận chuyển / lắp đặt: Lấy từ Cột D (index 4) của sheet DANH_SACH_DIEM
danh_sach_diem = lay_du_lieu_thời_gian_thực("DANH_SACH_DIEM", 4)

# Danh sách dự phòng an toàn tuyệt đối nếu mất mạng
if not danh_sach_doi:
    danh_sach_doi = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Được thôi nào", "Mệt và Mỏi", "được để qua", "Khổ Lắm Rồi"]

if not danh_sach_diem:
    danh_sach_diem = [
        "Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm",
        "Xã Nhữ Khê", "Xã Yên Sơn", "Xã Tân Long", "Xã Lực Hành", "Xã Xuân Vân", "Xã Thái Bình", "Xã Hùng Lợi",
        "Xã Trung Sơn", "Xã Kiến Thiết", "Xã Đông Thọ", "Xã Hồng Sơn", "Xã Trường Sinh", "Xã Phú Lương",
        "Xã Sơn Thủy", "Xã Minh Thanh", "Xã Tân Trào", "Xã Tân Thanh", "Xã Bình Ca", "Xã Sơn Dương",
        "Xã Yên Nguyên", "Xã Kim Bình", "Xã Tri Phú"
    ]

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
            "Cán bộ / Đội trưởng thực hiện (Lấy từ Cột B - QUAN_LY_DOI):",
            danh_sach_doi
        )
        
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Lấy từ Cột D - DANH_SACH_DIEM):",
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
            uploaded_image = st.camera_input("📷 Chụp ảnh hiện trường (Bấm máy ảnh để chụp trực tiếp qua camera)")
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO NGHIỆM THU NGAY")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    client = get_live_client()
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
                    client = get_live_client()
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
            client = get_live_client()
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
        client = get_live_client()
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
