import streamlit as st
import datetime

st.set_page_config(
    page_title="Hệ Thống Quản Lý Triển Khai Hiện Trường",
    page_icon="📡",
    layout="wide"
)

# Lấy tham số chế độ xem (view)
query_params = st.query_params
view_mode = query_params.get("view", "hientruong")

# ==============================================================================
# 1. TẦNG 1: ĐĂNG KÝ THÀNH VIÊN / ĐỘI THỢ (?view=dangky)
# ==============================================================================
if view_mode == "dangky":
    st.title("📝 Đăng Ký Thành Viên Đội Thi Công")
    st.caption("Dành cho KTV và đối tác đăng ký gia nhập đội triển khai")
    
    with st.form("form_dangky"):
        ho_ten = st.text_input("Họ và tên KTV / Trưởng nhóm *")
        so_dien_thoai = st.text_input("Số điện thoại (Zalo) *")
        chuyen_mon = st.selectbox("Chuyên môn chính", ["Kéo cáp viễn thông", "Lắp đặt Camera / Thiết bị", "Cấu hình mạng", "Tổng hợp"])
        phuong_tien = st.selectbox("Phương tiện di chuyển", ["Xe máy", "Xe bán tải / Ô tô", "Xe tải"])
        dia_ban = st.multiselect("Địa bàn / Tuyến có thể nhận", ["TP Tuyên Quang", "Sơn Dương", "Yên Sơn", "Hàm Yên", "Chiêm Hóa", "Na Hang", "Lâm Bình"])
        
        submitted = st.form_submit_button("Gửi Đăng Ký")
        if submitted:
            if not ho_ten or not so_dien_thoai:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")
            else:
                st.success("✅ Đã gửi đăng ký thành công! Quản trị viên sẽ phê duyệt trên Google Sheets.")

# ==============================================================================
# 2. TẦNG 3: GIÁM SÁT DÀNH CHO LÃNH ĐẠO (?view=lanhdao)
# ==============================================================================
elif view_mode == "lanhdao":
    st.title("📊 Trung Tâm Giám Sát Tiến Độ - Ban Lãnh Đạo")
    st.caption("Báo cáo tiến độ và nghiệm thu hiện trường thời gian thực")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Điểm Triển Khai", "1 điểm")
    with col2:
        st.metric("Vận Chuyển", "5 thiết bị")
    with col3:
        st.metric("Lắp Đặt Xong", "5 thiết bị")
    with col4:
        st.metric("Tỷ Lệ Nghiệm Thu", "100.0%")
        
    st.info("💡 Toàn bộ dữ liệu được quản trị tập trung tại Google Sheets của Ban Quản lý.")

# ==============================================================================
# 3. TẦNG 2: HIỆN TRƯỜNG TÁC NGHIỆP (Mặc định cho đội VHH)
# ==============================================================================
else:
    st.title("🛠️ Báo Cáo Hiện Trường Thực Địa")
    st.caption("Đội kỹ thuật VHH cập nhật tiến độ giao hàng & lắp đặt")
    
    with st.form("form_hientruong"):
        ma_da = st.selectbox("Mã dự án *", ["DA880", "Dự án khác"])
        doi_thuc_hien = st.selectbox("Đội thực hiện *", ["[DA880] Vỹ - Hạnh - Hiển (Nguyễn Văn A)", "Đội KTV-02", "Đội khác"])
        diem_lap_dat = st.selectbox("Điểm tác nghiệp *", ["Phường Minh Xuân", "Phường Nông Tiến", "Điểm khác"])
        so_luong = st.number_input("Số lượng thiết bị thực tế", min_value=1, value=5, step=1)
        
        tinh_trang = st.radio(
            "Tình trạng thực hiện *",
            ["Đã giao hàng", "Đã lắp đặt xong (Hoàn thành)"],
            index=1
        )
        
        link_maps = st.text_input("Tọa độ GPS / Link Google Maps", value="https://maps.google.com/?q=21.83059,105.19240")
        
        btn_gui = st.form_submit_button("BÁO CÁO NGAY")
        if btn_gui:
            st.success(f"🎉 Đã gửi báo cáo thành công cho điểm {diem_lap_dat}! Trạng thái: {tinh_trang}.")
            st.balloons()
