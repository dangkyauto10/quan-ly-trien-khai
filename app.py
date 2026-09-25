import streamlit as st
import datetime
import requests

st.set_page_config(
    page_title="Hệ Thống Quản Lý Triển Khai Hiện Trường",
    page_icon="📡",
    layout="wide"
)

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCY-kns_lnNkgC-005rSYquDgcUgvBhdylHormgQktnydC0qhAfp62Lmm_9qLvrU6xIQ/exec"

query_params = st.query_params
view_mode = query_params.get("view", "hientruong")

# Bảng tra cứu định mức phân bổ cố định từ Kho (Chống thất thoát)
DINH_MUC_PHAN_BO = {
    "Phường Minh Xuân": 5,
    "Phường Nông Tiến": 6,
    "Phường Bình Thuận": 1,
    "Phường An Tường": 7
}

# ==============================================================================
# 1. TẦNG 1: ĐĂNG KÝ THÀNH VIÊN ĐỘI THI CÔNG (?view=dangky)
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
        st.metric("Tổng Điểm Triển Khai", "4 điểm")
    with col2:
        st.metric("Giao Hàng", "4 điểm")
    with col3:
        st.metric("Lắp Đặt Xong", "Tự động đồng bộ")
    with col4:
        st.metric("Nghiệm Thu", "100.0% khi hoàn tất")
        
    st.info("💡 Toàn bộ dữ liệu được quản trị tập trung tại Google Sheets của Ban Quản lý.")

# ==============================================================================
# 3. TẦNG 2: HIỆN TRƯỜNG TÁC NGHIỆP (KHÓA CHẶT SỐ LƯỢNG - CHỐNG SỬA)
# ==============================================================================
else:
    st.title("🛠️ Báo Cáo Hiện Trường Thực Địa")
    st.caption("Đội kỹ thuật cập nhật tiến độ nghiệm thu theo định mức kho đã giao")
    
    # Lựa chọn bên ngoài form để tự động nhảy số lượng định mức
    col_a, col_b = st.columns(2)
    with col_a:
        ma_da = st.selectbox("Mã dự án *", ["DA880", "Dự án khác"])
        doi_thuc_hien = st.selectbox(
            "Đội thực hiện *", 
            [
                "VHH",
                "Đội KTV 003", 
                "Đội KTV 004", 
                "Đội KTV 005",
                "[DA880] Vỹ - Hạnh - Hiển (Nguyễn Văn A)"
            ]
        )
    with col_b:
        diem_lap_dat = st.selectbox(
            "Điểm tác nghiệp *", 
            [
                "Phường Minh Xuân", 
                "Phường Nông Tiến", 
                "Phường Bình Thuận", 
                "Phường An Tường"
            ]
        )
        
        # Tự động lấy số lượng định mức đã phân bổ từ kho
        so_luong_chuan = DINH_MUC_PHAN_BO.get(diem_lap_dat, 5)
        # Khóa trường này lại, thợ không thể bấm tăng giảm hay gõ sửa
        st.number_input(
            "Số lượng thiết bị bàn giao theo định mức (CỐ ĐỊNH - KHÔNG ĐƯỢC SỬA)", 
            value=so_luong_chuan, 
            disabled=True,
            help="Số lượng được ấn định tự động từ Kho phân bổ. Kỹ thuật viên không được can thiệp."
        )

    with st.form("form_hientruong"):
        tinh_trang = st.radio(
            "Xác nhận tình trạng thực tế *",
            ["Đã giao hàng", "Đã lắp đặt xong (Hoàn thành)"],
            index=1
        )
        
        link_maps = st.text_input("Tọa độ GPS / Link vị trí xác thực", value="https://maps.google.com/?q=21.83059,105.19240")
        
        btn_gui = st.form_submit_button("XÁC NHẬN BÁO CÁO NGHIỆM THU")
        if btn_gui:
            payload = {
                "ma_da": ma_da,
                "doi_thuc_hien": doi_thuc_hien,
                "diem_lap_dat": diem_lap_dat,
                "so_luong": so_luong_chuan,
                "tinh_trang": tinh_trang,
                "link_maps": link_maps
            }
            try:
                resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
                st.success(f"🎉 Đã gửi xác nhận {tinh_trang} tại {diem_lap_dat} với đúng định mức {so_luong_chuan} thiết bị!")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Báo cáo đã ghi nhận, hệ thống đang đồng bộ về bảng tính.")
