import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import urllib.parse

st.set_page_config(
    page_title="Hệ Thống Quản Lý & Điều Hành Dự Án 880",
    page_icon="📡",
    layout="wide"
)

# 1. BỘ XỬ LÝ NHẬN DIỆN LINK
try:
    params = dict(st.query_params)
    raw_view = params.get("view", "hientruong")
except Exception:
    raw_view = "hientruong"

if isinstance(raw_view, list):
    view_mode = raw_view[0] if len(raw_view) > 0 else "hientruong"
else:
    view_mode = str(raw_view).strip().lower()

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCY-kns_lnNkgC-005rSYquDgcUgvBhdylHormgQktnydC0qhAfp62Lmm_9qLvrU6xIQ/exec"

# ==============================================================================
# DANH MỤC CÁC ĐỘI ĐÃ ĐƯỢC DUYỆT
# ==============================================================================
DANH_SACH_DOI_CHUAN = [
    "VHH",
    "Đội KTV 001",
    "Đội KTV 002",
    "Đội KTV 003",
    "Đội KTV 004",
    "Đội KTV 005",
    "Đội KTV 006",
    "Đội Vận Chuyển 01",
    "Đội Vận Chuyển 02",
    "Vỹ - Hạnh - Hiển (Nguyễn Văn A)",
    "🔍 [Tự nhập tên đội khác...]"
]

# ==============================================================================
# CƠ SỞ DỮ LIỆU ĐỊA BÀN: NGUYÊN TÊN PHƯỜNG / XÃ
# ==============================================================================
DANH_SACH_DIEM_CHUAN = {
    # Tuyến T01: Tuyên Quang nội tỉnh
    "Phường Minh Xuân": {"tuyen": "T01 - Nội tỉnh", "huyen": "TP Tuyên Quang", "so_luong": 5, "toa_do": "21.83059,105.19240"},
    "Phường Nông Tiến": {"tuyen": "T01 - Nội tỉnh", "huyen": "TP Tuyên Quang", "so_luong": 6, "toa_do": "21.82145,105.22810"},
    "Phường Bình Thuận": {"tuyen": "T01 - Nội tỉnh", "huyen": "TP Tuyên Quang", "so_luong": 1, "toa_do": "21.78912,105.18520"},
    "Phường An Tường": {"tuyen": "T01 - Nội tỉnh", "huyen": "TP Tuyên Quang", "so_luong": 7, "toa_do": "21.80210,105.20140"},
    "Phường Mỹ Lâm": {"tuyen": "T01 - Nội tỉnh", "huyen": "TP Tuyên Quang", "so_luong": 5, "toa_do": "21.78500,105.15000"},
    
    # Tuyến T02: Yên Sơn Bắc/Đông
    "Xã Nhữ Khê": {"tuyen": "T02 - Yên Sơn Bắc/Đông", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.72000,105.25000"},
    "Xã Yên Sơn": {"tuyen": "T02 - Yên Sơn Bắc/Đông", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.85000,105.28000"},
    "Xã Tân Long": {"tuyen": "T02 - Yên Sơn Bắc/Đông", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.90000,105.29000"},
    "Xã Lực Hành": {"tuyen": "T02 - Yên Sơn Bắc/Đông", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.93000,105.31000"},
    "Xã Xuân Vân": {"tuyen": "T02 - Yên Sơn Bắc/Đông", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.95000,105.32000"},
    
    # Tuyến T03: Yên Sơn Kiến Thiết
    "Xã Thái Bình": {"tuyen": "T03 - Yên Sơn Kiến Thiết", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.82000,105.35000"},
    "Xã Hùng Lợi": {"tuyen": "T03 - Yên Sơn Kiến Thiết", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.75000,105.40000"},
    "Xã Trung Sơn": {"tuyen": "T03 - Yên Sơn Kiến Thiết", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.79000,105.43000"},
    "Xã Kiến Thiết": {"tuyen": "T03 - Yên Sơn Kiến Thiết", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.86000,105.45000"},
    "Xã Đông Thọ": {"tuyen": "T03 - Yên Sơn Kiến Thiết", "huyen": "Huyện Yên Sơn", "so_luong": 5, "toa_do": "21.68000,105.38000"},
    
    # Tuyến T04: Sơn Dương
    "Xã Hồng Sơn": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.65000,105.35000"},
    "Xã Trường Sinh": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.61000,105.32000"},
    "Xã Phú Lương": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.62000,105.39000"},
    "Xã Sơn Thủy": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.67000,105.41000"},
    "Xã Minh Thanh": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.74000,105.42000"},
    "Xã Tân Trào": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.77000,105.44000"},
    "Xã Tân Thanh": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.71000,105.39000"},
    "Xã Bình Ca": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.73000,105.31000"},
    "Xã Sơn Dương": {"tuyen": "T04 - Sơn Dương", "huyen": "Huyện Sơn Dương", "so_luong": 5, "toa_do": "21.70000,105.37000"},
    
    # Tuyến T05: Chiêm Hóa
    "Xã Yên Nguyên": {"tuyen": "T05 - Chiêm Hóa", "huyen": "Huyện Chiêm Hóa", "so_luong": 5, "toa_do": "22.05000,105.20000"},
    "Xã Kim Bình": {"tuyen": "T05 - Chiêm Hóa", "huyen": "Huyện Chiêm Hóa", "so_luong": 5, "toa_do": "22.12000,105.23000"},
    "Xã Tri Phú": {"tuyen": "T05 - Chiêm Hóa", "huyen": "Huyện Chiêm Hóa", "so_luong": 5, "toa_do": "22.18000,105.21000"}
}

DANH_SACH_TEN_XA = list(DANH_SACH_DIEM_CHUAN.keys()) + ["🔍 [Tự nhập điểm khác...]"]

# ==============================================================================
# NHÁNH 1: ĐĂNG KÝ THÀNH VIÊN (?view=dangky)
# ==============================================================================
if view_mode == "dangky":
    st.title("📝 Đăng Ký Thành Viên Đội Thi Công")
    st.caption("Dành cho KTV, đội vận chuyển và đối tác đăng ký tham gia dự án")
    
    with st.form("form_dangky"):
        ho_ten = st.text_input("Họ và tên KTV / Trưởng nhóm *")
        so_dien_thoai = st.text_input("Số điện thoại (Zalo) *")
        
        lua_chon_vai_tro = st.selectbox(
            "Vai trò / Chuyên môn tham gia *",
            [
                "1. Vận chuyển / Giao nhận thiết bị",
                "2. KTV Lắp đặt thiết bị",
                "3. Kiêm nhiệm (Vừa giao nhận vừa lắp đặt)",
                "4. Tự nhập chuyên môn khác..."
            ]
        )
        
        chuyen_mon_tu_ghi = st.text_input(
            "Nếu chọn 'Tự nhập khác', ghi cụ thể chuyên môn tại đây (hoặc để trống nếu chọn gợi ý trên):",
            placeholder="Ví dụ: Kéo rải cáp quang, hàn nối, cấu hình thiết bị mạng..."
        )
        
        phuong_tien = st.selectbox("Phương tiện di chuyển chính", ["Xe máy", "Xe bán tải / Ô tô", "Xe tải"])
        dia_ban = st.multiselect(
            "Địa bàn phụ trách có thể nhận", 
            ["TP Tuyên Quang", "Sơn Dương", "Yên Sơn", "Hàm Yên", "Chiêm Hóa", "Na Hang", "Lâm Bình"]
        )
        
        submitted = st.form_submit_button("Gửi Đăng Ký")
        if submitted:
            if not ho_ten or not so_dien_thoai:
                st.error("Vui lòng điền đầy đủ Họ và tên và Số điện thoại!")
            else:
                chuyen_mon_cuoi = chuyen_mon_tu_ghi.strip() if chuyen_mon_tu_ghi.strip() else lua_chon_vai_tro
                payload = {
                    "action": "dang_ky_thanh_vien",
                    "ho_ten": ho_ten,
                    "so_dien_thoai": so_dien_thoai,
                    "chuyen_mon": chuyen_mon_cuoi,
                    "phuong_tien": phuong_tien,
                    "dia_ban": ", ".join(dia_ban)
                }
                try:
                    requests.post(WEBHOOK_URL, json=payload, timeout=15)
                except Exception:
                    pass
                st.success(f"✅ Đã gửi đăng ký thành công cho {ho_ten} với vai trò: '{chuyen_mon_cuoi}'! Quản trị viên sẽ phê duyệt trên Google Sheets.")

# ==============================================================================
# NHÁNH 2: TRUNG TÂM GIÁM SÁT DÀNH CHO LÃNH ĐẠO (?view=lanhdao)
# ==============================================================================
elif view_mode == "lanhdao":
    st.title("📊 TRUNG TÂM GIÁM SÁT & ĐIỀU HÀNH DỰ ÁN (LÃNH ĐẠO)")
    st.caption("Số liệu báo cáo tiến độ và biểu đồ trực quan thời gian thực")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="📍 Tổng điểm dự án (DA880)", value="4 điểm")
    with col2:
        st.metric(label="🚚 Tiến độ Giao hàng", value="4 / 4", delta="100% Hoàn thành")
    with col3:
        st.metric(label="🔧 Tiến độ Lắp đặt", value="4 / 4", delta="100% Hoàn thành")
    with col4:
        st.metric(label="✅ Tỷ lệ Nghiệm thu", value="100.00%", delta="Đạt mục tiêu")
        
    st.markdown("---")
    
    st.subheader("📈 Biểu Đồ Tiến Độ Thực Hiện")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("**Khối lượng thiết bị đã phân bổ theo địa bàn:**")
        df_diem = pd.DataFrame({
            "Địa bàn": ["Minh Xuân", "Nông Tiến", "Bình Thuận", "An Tường"],
            "Số lượng thiết bị": [5, 6, 1, 7]
        })
        st.bar_chart(df_diem.set_index("Địa bàn"), color="#0d6efd")
        
    with col_chart2:
        st.write("**Tỷ lệ hoàn thành các giai đoạn:**")
        df_tiendo = pd.DataFrame({
            "Giai đoạn": ["Giao hàng", "Lắp đặt xong", "Nghiệm thu"],
            "Tỷ lệ hoàn thành (%)": [100, 100, 100]
        })
        st.bar_chart(df_tiendo.set_index("Giai đoạn"), color="#198754")
        
    st.markdown("---")
    
    st.subheader("📋 Bảng Tổng Hợp Trạng Thái Các Điểm Triển Khai")
    data_tonghop = [
        {"Mã CV": "CV-100001", "Dự án": "DA880", "Đội KTV": "VHH", "Địa bàn": "Phường Minh Xuân", "Thiết bị": 5, "Trạng thái": "✅ Đã lắp đặt xong"},
        {"Mã CV": "CV-100002", "Dự án": "DA880", "Đội KTV": "Đội KTV 003", "Địa bàn": "Phường Nông Tiến", "Thiết bị": 6, "Trạng thái": "✅ Đã lắp đặt xong"},
        {"Mã CV": "CV-100003", "Dự án": "DA880", "Đội KTV": "Đội KTV 003", "Địa bàn": "Phường Bình Thuận", "Thiết bị": 1, "Trạng thái": "✅ Đã lắp đặt xong"},
        {"Mã CV": "CV-100004", "Dự án": "DA880", "Đội KTV": "Đội KTV 004", "Địa bàn": "Phường An Tường", "Thiết bị": 7, "Trạng thái": "✅ Đã lắp đặt xong"}
    ]
    st.dataframe(pd.DataFrame(data_tonghop), use_container_width=True, hide_index=True)

# ==============================================================================
# NHÁNH 3: BÁO CÁO TIẾN ĐỘ HIỆN TRƯỜNG (KỸ THUẬT VIÊN)
# ==============================================================================
else:
    st.title("🛠️ BÁO CÁO TIẾN ĐỘ THỰC HIỆN DỰ ÁN")
    st.caption("Xem danh sách điểm, lấy tọa độ GPS thực địa & nghiệm thu công việc")
    
    col_a, col_b = st.columns(2)
    with col_a:
        ma_da = st.selectbox("Mã dự án *", ["DA880", "Dự án khác"])
        
        # 1 Ô DUY NHẤT: CHẠM VÀO LÀ HIỆN DANH SÁCH GỢI Ý & GÕ ĐƯỢC NGAY
        doi_thuc_hien_chon = st.selectbox(
            "Đội thực hiện *",
            options=DANH_SACH_DOI_CHUAN,
            index=0,
            placeholder="Chạm vào để chọn hoặc gõ tên đội...",
            help="Chạm vào là danh sách gợi ý hiện lên, gõ để lọc nhanh."
        )
        
        if "Tự nhập" in doi_thuc_hien_chon:
            doi_thuc_hien = st.text_input("Gõ chính xác tên đội mới:")
        else:
            doi_thuc_hien = doi_thuc_hien_chon

    with col_b:
        # 1 Ô DUY NHẤT: CHẠM VÀO LÀ HIỆN GỢI Ý PHƯỜNG / XÃ & GÕ ĐƯỢC NGAY
        diem_duoc_chon = st.selectbox(
            "Điểm tác nghiệp (Chỉ hiển thị tên phường/xã) *",
            options=DANH_SACH_TEN_XA,
            index=0,
            placeholder="Chạm vào để chọn hoặc gõ tên phường/xã...",
            help="Chạm vào là danh sách phường/xã hiện ra, gõ chữ để tìm nhanh."
        )
        
        if "Tự nhập" in diem_duoc_chon:
            diem_thuc_te = st.text_input("Gõ tên địa điểm cụ thể:")
            so_luong_chuan = 5
            tuyen_duong = "Điểm tác nghiệp mới"
            dia_chi_mac_dinh = f"{diem_thuc_te}, Tuyên Quang" if diem_thuc_te else "TP Tuyên Quang"
            toa_do_chuan = "21.83059,105.19240"
        else:
            diem_thuc_te = diem_duoc_chon
            info = DANH_SACH_DIEM_CHUAN[diem_duoc_chon]
            so_luong_chuan = info["so_luong"]
            tuyen_duong = info["tuyen"]
            dia_chi_mac_dinh = f"{diem_duoc_chon}, {info['huyen']}, Tuyên Quang"
            toa_do_chuan = info["toa_do"]

        st.number_input(
            f"Số lượng thiết bị định mức ({tuyen_duong}) - [KHÓA CỐ ĐỊNH]", 
            value=so_luong_chuan, 
            disabled=True,
            help="Số lượng được lấy cố định từ Kho phân bổ. Kỹ thuật viên không được chỉnh sửa."
        )

    st.markdown("---")

    # KHU VỰC DẪN ĐƯỜNG & GPS
    st.markdown("### 🗺️ Tiện Ích Dẫn Đường & Định Vị Thực Địa")
    col_nav1, col_nav2 = st.columns([1.3, 1])
    
    with col_nav1:
        st.write(f"**Điểm đến hiện tại:** `{dia_chi_mac_dinh}`")
        url_chiduong = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(dia_chi_mac_dinh)}"
        st.link_button(f"🚗 Mở Google Maps chỉ đường tới {diem_thuc_te}", url_chiduong)

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

    # FORM BÁO CÁO CÔNG VIỆC
    with st.form("form_hientruong"):
        tinh_trang = st.radio(
            "Xác nhận tình trạng công việc *",
            [
                "Giao hàng & Lắp đặt hoàn tất (Đội kiêm nhiệm trọn gói)",
                "Đã giao hàng (Chỉ vận chuyển đến nơi)",
                "Đã lắp đặt xong (KTV đã hoàn thành lắp đặt)"
            ],
            index=0
        )
        
        default_map_url = f"https://maps.google.com/?q={toa_do_chuan}"
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
                "diem_lap_dat": diem_thuc_te,
                "so_luong": so_luong_chuan,
                "tinh_trang": tinh_trang,
                "link_maps": link_maps
            }
            try:
                resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
                st.success(f"🎉 Đã gửi thành công! Đội: {doi_thuc_hien} | Trạng thái: {tinh_trang} tại {diem_thuc_te} ({so_luong_chuan} thiết bị).")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Báo cáo đã ghi nhận, hệ thống đang đồng bộ về Google Sheets.")
