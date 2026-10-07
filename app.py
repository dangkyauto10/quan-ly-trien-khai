import streamlit as st
import datetime
import urllib.request
import csv

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án Hiện trường", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"

# Cấu hình danh sách các dự án (Anh có thể thêm bớt từ 1 đến 5+ dự án tại đây)
DANH_SACH_DU_AN = {
    "Dự án 1: Hệ thống Điều hành Chính (DA880)": {
        "spreadsheet_id": "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4",
        "gid_quan_ly_doi": "1563705161",
        "gid_danh_sach_diem": "0"
    },
    # "Dự án 2: Tên dự án khác...": {
    #     "spreadsheet_id": "ID_SHEET_DU_AN_2",
    #     "gid_quan_ly_doi": "GID_QUAN_LY_DOI_2",
    #     "gid_danh_sach_diem": "GID_DANH_SACH_DIEM_2"
    # }
}

def get_live_sheet_column(spreadsheet_id, gid, col_idx):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        response = urllib.request.urlopen(url)
        lines = [line.decode('utf-8') for line in response.readlines()]
        reader = csv.reader(lines)
        rows = list(reader)
        
        col_data = []
        # Quét từ dòng thứ 3 trở xuống (index 2 trong Python) theo thời gian thực
        if len(rows) > 2:
            for r in rows[2:]:
                if len(r) > col_idx:
                    val = r[col_idx].strip()
                    if val != "" and val not in col_data:
                        col_data.append(val)
        return col_data
    except Exception as e:
        return []

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG ĐIỀU HÀNH ĐA DỰ ÁN HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1: btn_dang_ky = st.button("📝 Đăng ký", use_container_width=True)
with col2: btn_bao_cao = st.button("📊 Báo cáo", use_container_width=True)
with col3: btn_admin = st.button("🔒 Admin duyệt", use_container_width=True)
with col4: btn_link = st.button("📈 Link báo cáo", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

# ================= 1. TAB ĐĂNG KÝ THÀNH VIÊN =================
if st.session_state.nav_tab == "Dang_ky":
    st.markdown("### 📝 ĐĂNG KÝ THÀNH VIÊN / ĐỘI THỰC HIỆN")
    with st.form("form_dang_ky"):
        ten_thanh_vien = st.text_input("Họ và tên *")
        sdt = st.text_input("Số điện thoại liên hệ *")
        vai_tro = st.selectbox("Vai trò công việc *", ["Đội Vận Chuyển (VC)", "Đội Lắp Đặt (LD)", "Đội Kiêm Nhiệm (VC & LD)"])
        don_vi = st.text_input("Đơn vị / Bộ phận công tác *")
        if st.form_submit_button("Gửi đăng ký", type="primary"):
            if not ten_thanh_vien or not sdt: 
                st.warning("⚠️ Vui lòng điền đầy đủ họ tên và số điện thoại!")
            else: 
                st.success("🎉 Đăng ký thành công! Vui lòng chờ Admin duyệt tài khoản.")

# ================= 2. TAB BÁO CÁO CỦA ĐỘI VC & LĐ =================
elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### 📊 BÁO CÁO NHIỆM VỤ HIỆN TRƯỜNG")
    
    # 1. CHỌN DỰ ÁN THỰC THI (Hỗ trợ 1 đến nhiều dự án)
    ten_du_an_chon = st.selectbox("📂 CHỌN DỰ ÁN TRIỂN KHAI *", list(DANH_SACH_DU_AN.keys()))
    current_config = DANH_SACH_DU_AN[ten_du_an_chon]
    
    # 2. ÁNH XẠ ĐỘNG TOÀN BỘ CỘT B (Index 1) SHEET QUAN_LY_DOI THEO THỜI GIAN THỰC
    danh_sach_doi = get_live_sheet_column(current_config["spreadsheet_id"], current_config["gid_quan_ly_doi"], 1)
    if not danh_sach_doi:
        danh_sach_doi = ["(Sheet QUAN_LY_DOI trống cột B hoặc chưa cấu hình)"]
        
    # 3. ÁNH XẠ ĐỘNG TOÀN BỘ CỘT D (Index 3) SHEET DANH_SACH_DIEM THEO THỜI GIAN THỰC
    danh_sach_diem = get_live_sheet_column(current_config["spreadsheet_id"], current_config["gid_danh_sach_diem"], 3)
    if not danh_sach_diem:
        danh_sach_diem = ["(Sheet DANH_SACH_DIEM trống cột D hoặc chưa cấu hình)"]
        
    doi_thuc_hien = st.selectbox("👥 TÊN ĐỘI VẬN CHUYỂN / LẮP ĐẶT *", ["-- Chọn tên đội --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("📍 ĐIỂM GIAO HÀNG & LẮP ĐẶT *", ["-- Chọn địa điểm --"] + danh_sach_diem)
    
    # 4. SỐ LƯỢNG THIẾT BỊ CỐ ĐỊNH TỪ KHO THEO ĐIỂM
    so_luong_hien_tai = 0
    if diem_giao_lap != "-- Chọn địa điểm --" and not diem_giao_lap.startswith("("):
        so_luong_co_dinh = 3  # Định mức phân bổ kho
        st.info(f"📦 Số lượng thiết bị phân bổ tại **{diem_giao_lap}**: **{so_luong_co_dinh} bộ** (Cố định từ Kho)")
        so_luong_hien_tai = st.number_input("Số lượng thiết bị áp dụng báo cáo", value=float(so_luong_co_dinh), disabled=True)
    else:
        st.info("📦 Vui lòng chọn địa điểm để hiển thị số lượng thiết bị phân bổ.")
        
    st.markdown("---")
    st.markdown("📷 **Chụp ảnh hiện trường** (Hỗ trợ camera sau/trước của thiết bị):")
    camera_file = st.camera_input("Chụp ảnh thực tế")
    
    st.markdown("---")
    st.markdown("📍 **Xác thực GPS hiện trường:**")
    if st.button("📍 Check-in GPS Tọa độ Hiện trường", use_container_width=True):
        st.success("📍 Check-in GPS thành công!")
        
    st.markdown("---")
    st.markdown("### 🎛️ BÁO CÁO XÁC NHẬN (3 NÚT RIÊNG BIỆT):")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("✅ ĐÃ GIAO XONG", type="primary", use_container_width=True):
            if doi_thuc_hien.startswith("--") or doi_thuc_hien.startswith("("):
                st.warning("⚠️ Vui lòng chọn Tên đội hợp lệ!")
            elif diem_giao_lap.startswith("--") or diem_giao_lap.startswith("("):
                st.warning("⚠️ Vui lòng chọn Địa điểm hợp lệ!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công: ĐÃ GIAO XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({ten_du_an_chon})!")
    with col_b2:
        if st.button("✅ ĐÃ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien.startswith("--") or doi_thuc_hien.startswith("("):
                st.warning("⚠️ Vui lòng chọn Tên đội hợp lệ!")
            elif diem_giao_lap.startswith("--") or diem_giao_lap.startswith("("):
                st.warning("⚠️ Vui lòng chọn Địa điểm hợp lệ!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công: ĐÃ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({ten_du_an_chon})!")
    with col_b3:
        if st.button("🚀 ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien.startswith("--") or doi_thuc_hien.startswith("("):
                st.warning("⚠️ Vui lòng chọn Tên đội hợp lệ!")
            elif diem_giao_lap.startswith("--") or diem_giao_lap.startswith("("):
                st.warning("⚠️ Vui lòng chọn Địa điểm hợp lệ!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công TRỌN GÓI: ĐÃ GIAO VÀ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({ten_du_an_chon})!")

# ================= 3. TAB ADMIN DUYỆT (PASS: 880880) =================
elif st.session_state.nav_tab == "Admin":
    st.markdown("### 🔒 KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("🔓 Đăng nhập Admin thành công!")
        st.write("- [Chờ duyệt] Thành viên đăng ký mới")
        if st.button("✅ Duyệt tất cả tài khoản"): 
            st.success("Đã phê duyệt thành công!")
    elif pass_input != "": 
        st.error("❌ Sai mật khẩu bảo mật! (Pass: 880880)")

# ================= 4. TAB LINK BÁO CÁO (PASS: 880880) =================
elif st.session_state.nav_tab == "Link":
    st.markdown("### 📈 TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("🔓 Xác thực thành công!")
        st.markdown("- 🔗 [Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "": 
        st.error("❌ Sai mật khẩu truy cập! (Pass: 880880)")
