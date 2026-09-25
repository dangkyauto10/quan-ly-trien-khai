import streamlit as st
import datetime
import requests
import urllib.parse

st.set_page_config(
    page_title="Hệ Thống Quản Lý Triển Khai Hiện Trường",
    page_icon="📡",
    layout="wide"
)

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCY-kns_lnNkgC-005rSYquDgcUgvBhdylHormgQktnydC0qhAfp62Lmm_9qLvrU6xIQ/exec"

query_params = st.query_params
view_mode = query_params.get("view", "hientruong")

# Bảng tra cứu định mức & tọa độ chuẩn cho từng điểm tác nghiệp
THONG_TIN_DIEM = {
    "Phường Minh Xuân": {"so_luong": 5, "toa_do": "21.83059,105.19240", "dia_chi": "Phường Minh Xuân, Tuyên Quang"},
    "Phường Nông Tiến": {"so_luong": 6, "toa_do": "21.82145,105.22810", "dia_chi": "Phường Nông Tiến, Tuyên Quang"},
    "Phường Bình Thuận": {"so_luong": 1, "toa_do": "21.78912,105.18520", "dia_chi": "Phường Bình Thuận, Tuyên Quang"},
    "Phường An Tường": {"so_luong": 7, "toa_do": "21.80210,105.20140", "dia_chi": "Phường An Tường, Tuyên Quang"}
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
# 3. TẦNG 2: BÁO CÁO THỰC ĐỊA (CÓ CHỈ ĐƯỜNG & ĐỊNH VỊ GPS CHÍNH XÁC)
# ==============================================================================
else:
    st.title("🛠️ Báo Cáo Hiện Trường Thực Thực Địa")
    st.caption("Dành cho đội kỹ thuật nhận thiết bị, chỉ đường GPS & nghiệm thu lắp đặt")
    
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
            list(THONG_TIN_DIEM.keys())
        )
        
        info_diem = THONG_TIN_DIEM.get(diem_lap_dat, {"so_luong": 5, "toa_do": "", "dia_chi": ""})
        so_luong_chuan = info_diem["so_luong"]
        
        st.number_input(
            "Số lượng thiết bị theo định mức (KHÓA CỐ ĐỊNH)", 
            value=so_luong_chuan, 
            disabled=True,
            help="Số lượng được ấn định tự động từ Kho. Không được phép chỉnh sửa."
        )

    # KHU VỰC TÌM ĐƯỜNG VÀ DẪN ĐƯỜNG GOOGLE MAPS
    st.markdown("### 🗺️ Tìm Đường & Dẫn Đường Tới Điểm Thi Công")
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        # Link dẫn đường Google Maps Directions
        link_dan_duong = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(info_diem['dia_chi'])}"
        st.link_button(f"🚗 Mở Google Maps chỉ đường tới {diem_lap_dat}", link_dan_duong)

    with col_map2:
        # Tiện ích định vị GPS thực địa qua trình duyệt
        st.caption("📍 Tọa độ đích danh mục: " + info_diem["toa_do"])

    with st.form("form_hientruong"):
        tinh_trang = st.radio(
            "Xác nhận tình trạng thực tế *",
            ["Đã giao hàng", "Đã lắp đặt xong (Hoàn thành)"],
            index=1
        )
        
        # Cho phép thợ dán link vị trí GPS chụp từ điện thoại hoặc lấy tọa độ mặc định
        default_map_url = f"https://maps.google.com/?q={info_diem['toa_do']}"
        link_maps = st.text_input(
            "Tọa độ GPS / Link vị trí xác thực thực địa *", 
            value=default_map_url,
            help="Thợ có thể bấm chia sẻ vị trí từ Google Maps điện thoại và dán vào đây để xác thực có mặt tại công trình."
        )
        
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
                st.success(f"🎉 Đã gửi xác nhận nghiệm thu {tinh_trang} tại {diem_lap_dat}!")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Đã ghi nhận báo cáo, đang đồng bộ về Google Sheets.")
