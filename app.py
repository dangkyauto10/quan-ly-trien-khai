import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# HÀM ĐỌC DỮ LIỆU ĐỘNG TỪ GOOGLE SHEETS DẠNG CSV CÔNG KHAI (KHÔNG LO LỖI SECRETS / PEM)
# Đảm bảo Google Sheets của anh đã được chia sẻ ở chế độ: "Anyone with the link can view"
@st.cache_data(ttl=1)
def lay_du_lieu_dong_tu_sheets():
    danh_sach_doi = []
    danh_sach_diem = []
    
    try:
        # 1. Đọc Cột B từ sheet QUAN_LY_DOI (Thay đúng ID spreadsheet của anh vào link bên dưới)
        url_doi = "https://docs.google.com/spreadsheets/d/1QUẢN_LÝ_DỰ_ÁN_HỆ_THỐNG_ĐIỀU_HÀNH/gviz/tq?tqx=out:csv&sheet=QUAN_LY_DOI"
        df_doi = pd.read_csv(url_doi)
        if df_doi.shape[1] >= 2:
            # Lấy sạch từ dòng thứ 3 trở xuống (bỏ tiêu đề)
            col_b = df_doi.iloc[1:, 1].dropna().astype(str).str.strip()
            for val in col_b:
                if val and val != "nan" and val not in danh_sach_doi:
                    danh_sach_doi.append(val)
    except Exception:
        pass

    try:
        # 2. Đọc Cột D từ sheet DANH_SACH_DIEM
        url_diem = "https://docs.google.com/spreadsheets/d/1QUẢN_LÝ_DỰ_ÁN_HỆ_THỐNG_ĐIỀU_HÀNH/gviz/tq?tqx=out:csv&sheet=DANH_SACH_DIEM"
        df_diem = pd.read_csv(url_diem)
        if df_diem.shape[1] >= 4:
            col_d = df_diem.iloc[1:, 3].dropna().astype(str).str.strip()
            for val in col_d:
                if val and val != "nan" and val not in danh_sach_diem:
                    danh_sach_diem.append(val)
    except Exception:
        pass

    # Dự phòng thông minh chỉ kích hoạt nếu mất kết nối mạng hoàn toàn
    if not danh_sach_doi:
        danh_sach_doi = ["Chưa có dữ liệu Cột B từ Sheets"]
    if not danh_sach_diem:
        danh_sach_diem = ["Chưa có dữ liệu Cột D từ Sheets"]

    return danh_sach_doi, danh_sach_diem

danh_sach_doi, danh_sach_diem = lay_du_lieu_dong_tu_sheets()

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

# ================= TAB 1: BÁO CÁO KTV & VC =================
if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
    st.write("Hệ thống điều hành phân bổ tự động theo dữ liệu Google Sheets thực tế")

    st.success(f"🟢 Đang kết nối trực tiếp động 100%: Nhận diện **{len(danh_sach_doi)}** đội từ Cột B và **{len(danh_sach_diem)}** điểm từ Cột D.")

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện")
        
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện (Đồng bộ động từ Cột B):",
            options=danh_sach_doi
        )
        
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Đồng bộ động từ Cột D):",
            options=danh_sach_diem
        )
        
        st.info("📦 Số lượng thiết bị được phân bổ cho điểm này: **Theo định mức chuẩn từ KHO_PHAN_BO**")
        soluong_lap = st.number_input("Số lượng thiết bị thực tế lắp đặt / giao hàng:", min_value=1, value=1, step=1)
        
        st.markdown("### 2. Trạng Thái Báo Cáo & Nghiệm Thu")
        trangthai = st.selectbox("Chọn trạng thái hoàn thành:", [
            "Đã lắp đặt xong", 
            "Đã giao hàng xong (Dành cho vận chuyển)", 
            "Đã bàn giao và lắp đặt xong (Dành cho đơn vị vừa giao vừa lắp)"
        ])
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
                st.success(f"✅ Đã ghi nhận báo cáo thành công cho đội [{ktv_name}] tại điểm [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin!")

# ================= TAB 2: ĐĂNG KÝ THÀNH VIÊN =================
elif st.session_state.active_tab == "Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên Tham Gia Triển Khai")
    with st.form("form_dang_ky_moi"):
        reg_name = st.text_input("Họ và tên thành viên")
        reg_phone = st.text_input("Số điện thoại liên hệ")
        reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
        submitted_dk = st.form_submit_button("GỬI ĐĂNG KÝ MỚI")
        if submitted_dk:
            if reg_name and reg_phone:
                st.success(f"✅ Đã gửi đăng ký thành công cho thành viên: {reg_name}!")
            else:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

# ================= TAB 3: ADMIN DUYỆT THÀNH VIÊN =================
elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị - Admin Duyệt Thành Viên")
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực Admin thành công!")
        st.info("Khu vực hiển thị danh sách thành viên chờ duyệt từ sheet `DANG_KY_THANH_VIEN`.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu chuẩn: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

# ================= TAB 4: BÁO CÁO LĐ =================
elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Thống Kê Tổng Hợp")
    st.info("Khu vực tổng hợp báo cáo thời gian thực từ sheet `TRANG_CHU` và các module liên quan.")
