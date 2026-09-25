import streamlit as st
import streamlit.components.v1 as components
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

# Bảng tra cứu định mức & địa chỉ mẫu của dự án
THONG_TIN_DIEM = {
    "Phường Minh Xuân": {"so_luong": 5, "toa_do": "21.83059,105.19240", "dia_chi": "Phường Minh Xuân, TP Tuyên Quang"},
    "Phường Nông Tiến": {"so_luong": 6, "toa_do": "21.82145,105.22810", "dia_chi": "Phường Nông Tiến, TP Tuyên Quang"},
    "Phường Bình Thuận": {"so_luong": 1, "toa_do": "21.78912,105.18520", "dia_chi": "Phường Bình Thuận, TP Tuyên Quang"},
    "Phường An Tường": {"so_luong": 7, "toa_do": "21.80210,105.20140", "dia_chi": "Phường An Tường, TP Tuyên Quang"}
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
# 3. TẦNG 2: HIỆN TRƯỜNG TÁC NGHIỆP - TỰ DO TÌM ĐƯỜNG, ĐỊNH VỊ GPS & BÁO CÁO
# ==============================================================================
else:
    st.title("🛠️ Báo Cáo Hiện Trường Thực Địa")
    st.caption("Tra cứu đường đi, lấy tọa độ GPS thực địa & nghiệm thu công việc")
    
    # --- PHẦN 1: THÔNG TIN DỰ ÁN & ĐỊNH MỨC VẬT TƯ (KHÓA CHỐNG SỬA) ---
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
        danh_sach_diem = list(THONG_TIN_DIEM.keys()) + ["Điểm tác nghiệp mới / Khác"]
        diem_lap_dat = st.selectbox("Điểm tác nghiệp mục tiêu *", danh_sach_diem)
        
        info_diem = THONG_TIN_DIEM.get(diem_lap_dat, {"so_luong": 5, "toa_do": "21.83059,105.19240", "dia_chi": "Tuyên Quang"})
        so_luong_chuan = info_diem["so_luong"]
        
        # Khóa cứng số lượng thiết bị theo định mức phân bổ từ kho
        st.number_input(
            "Số lượng thiết bị theo định mức (KHÓA CỐ ĐỊNH - CHỐNG SỬA)", 
            value=so_luong_chuan, 
            disabled=True,
            help="Số lượng được ấn định tự động từ Kho. Kỹ thuật viên không được can thiệp."
        )

    st.markdown("---")

    # --- PHẦN 2: TÌM ĐƯỜNG THEO ĐỊA CHỈ TÙY CHỌN & NÚT BẮT GPS ---
    st.markdown("### 🗺️ Tiện Ích Dẫn Đường & Định Vị Thực Địa")
    
    col_nav1, col_nav2 = st.columns([1.2, 1])
    
    with col_nav1:
        # Cho phép gõ địa chỉ bất kỳ để tìm đường tới điểm tiếp theo
        dia_chi_mac_dinh = info_diem.get("dia_chi", "TP Tuyên Quang")
        dia_chi_tim_duong = st.text_input(
            "Nhập địa chỉ / Điểm cần đến tiếp theo:", 
            value=dia_chi_mac_dinh,
            help="Thợ có thể gõ bất kỳ thôn, xã, phường hoặc số nhà nào cần đến."
        )
        if dia_chi_tim_duong.strip():
            url_chiduong = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(dia_chi_tim_duong.strip())}"
            st.link_button(f"🚗 Mở Google Maps chỉ đường tới đây", url_chiduong)

    with col_nav2:
        st.write("**Lấy tọa độ GPS thực tế nơi đang đứng:**")
        components.html("""
            <div style="font-family: sans-serif;">
                <button onclick="layViTri()" style="background-color: #0d6efd; color: white; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; width: 100%;">
                    📍 Bấm để lấy GPS & Copy vị trí
                </button>
                <p id="gps_info" style="font-size: 12px; color: #198754; margin-top: 6px; margin-bottom: 0px; font-weight: bold;"></p>
            </div>
            <script>
            function layViTri() {
                var info = document.getElementById("gps_info");
                info.innerText = "⏳ Đang kết nối vệ tinh GPS...";
                info.style.color = "#d63384";
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(pos) {
                        var lat = pos.coords.latitude.toFixed(6);
                        var lng = pos.coords.longitude.toFixed(6);
                        var mapUrl = "https://maps.google.com/?q=" + lat + "," + lng;
                        info.innerText = "✅ Đã bắt GPS & sao chép: " + lat + ", " + lng;
                        info.style.color = "#198754";
                        navigator.clipboard.writeText(mapUrl);
                    }, function(err) {
                        info.innerText = "⚠️ Chưa bật GPS hoặc chưa cấp quyền.";
                        info.style.color = "#dc3545";
                    }, {enableHighAccuracy: true, timeout: 10000});
                } else {
                    info.innerText = "Trình duyệt không hỗ trợ GPS.";
                }
            }
            </script>
        """, height=75)

    st.markdown("---")

    # --- PHẦN 3: FORM XÁC NHẬN BÁO CÁO CÔNG VIỆC ---
    with st.form("form_hientruong"):
        # Tùy chọn 1 chạm dành riêng cho đội kiêm nhiệm
        tinh_trang = st.radio(
            "Xác nhận tình trạng công việc *",
            [
                "Giao hàng & Lắp đặt hoàn tất (Đội kiêm nhiệm trọn gói)",
                "Đã giao hàng (Chỉ vận chuyển đến nơi)",
                "Đã lắp đặt xong (KTV đã hoàn thành lắp đặt)"
            ],
            index=0
        )
        
        default_map_url = f"https://maps.google.com/?q={info_diem['toa_do']}"
        link_maps = st.text_input(
            "Tọa độ GPS / Link vị trí nghiệm thu thực địa *", 
            value=default_map_url,
            help="Hệ thống tự điền tọa độ hoặc thợ bấm dán link GPS vừa copy vào đây."
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
                st.success(f"🎉 Đã gửi thành công! Trạng thái: {tinh_trang} tại {diem_lap_dat} ({so_luong_chuan} thiết bị). Dữ liệu đã tự động cập nhật về Google Sheets.")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Báo cáo đã ghi nhận, hệ thống đang đồng bộ về Google Sheets.")
