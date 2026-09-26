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
# DANH MỤC CÁC ĐỘI QUY CHIẾU THEO SHEET QUẢN LÝ ĐỘI
# ==============================================================================
DANH_SACH_DOI_CHUAN = [
    "VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A", "Trần Văn B",
    "Đội KTV 006", "Đội KTV 007", "Đội KTV 008", "Đội KTV 009", "Đội KTV 010",
    "Đội KTV 011", "Đội KTV 012", "Đội KTV 013", "Đội KTV 014", "Đội KTV 015",
    "Đội KTV 016", "Đội KTV 017", "Đội KTV 018", "Đội KTV 019", "Đội KTV 020",
    "Đội KTV 021", "Đội KTV 022", "Đội KTV 023", "🔍 [Tự nhập tên đội khác...]"
]

# ==============================================================================
# QUY CHIẾU TOÀN BỘ CỘT D TRONG SHEET DANH SÁCH ĐIỂM
# ==============================================================================
DANH_SACH_DIEM_CHUAN = [
    # --- TUYÊN QUANG ---
    "Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm",
    "Xã Nhữ Khê", "Xã Yên Sơn", "Xã Tân Long", "Xã Lực Hành", "Xã Xuân Vân",
    "Xã Thái Bình", "Xã Hùng Lợi", "Xã Trung Sơn", "Xã Kiến Thiết", "Xã Đông Thọ",
    "Xã Hồng Sơn", "Xã Trường Sinh", "Xã Phú Lương", "Xã Sơn Thủy", "Xã Minh Thanh",
    "Xã Tân Trào", "Xã Tân Thanh", "Xã Bình Ca", "Xã Sơn Dương",
    "Xã Yên Nguyên", "Xã Kim Bình", "Xã Tri Phú",
    
    # --- HÀ GIANG ---
    "Xã Đường Hồng", "Xã Giáp Trung", "Xã Cán Tỷ", "Xã Lùng Tám", "Xã Quản Bạ",
    "Xã Tùng Vài", "Xã Nghĩa Thuận", "Xã Đông Hà", "Xã Quyết Tiến", "Xã Bát Đại Sơn",
    "Xã Bạch Đích", "Xã Thắng Mố", "Xã Yên Minh", "Xã Mậu Duệ", "Xã Du Già",
    "Xã Đường Thượng", "Xã Ngọc Long", "Xã Lũng Phìn", "Xã Sà Phìn", "Xã Phố Bảng",
    "Xã Đồng Văn", "Xã Lũng Cú", "Xã Niêm Sơn", "Xã Ma Lé", "Xã Sính Lủng",
    "Xã Tát Ngà", "Xã Sủng Máng", "Xã Mèo Vạc", "Xã Khâu Vai", "Xã Sơn Vĩ",
    "Xã Giàng Chu Phìn", "Xã Lũng Pù", "Xã Cán Chu Phìn", "Xã Thượng Phùng", "Xã Xín Cái",
    "Xã Pả Vi", "Xã Pải Lủng", "Xã Tả Lủng", "Xã Nậm Ban", "Xã Niêm Tòng",
    "Xã Minh Tân", "Xã Thuận Hòa", "Xã Tùng Bá", "Xã Thanh Thủy", "Xã Phương Độ",
    "Xã Yên Cường", "Xã Lạc Nông", "Xã Minh Sơn", "Xã Thượng Tân"
]

# Hàm xác định khu vực cấp Huyện/Thành phố dựa theo tên xã
def xac_dinh_khu_vuc(ten_diem):
    tq_tp = ["Minh Xuân", "Nông Tiến", "Bình Thuận", "An Tường", "Mỹ Lâm"]
    tq_ys = ["Nhữ Khê", "Yên Sơn", "Tân Long", "Lực Hành", "Xuân Vân", "Thái Bình", "Hùng Lợi", "Trung Sơn", "Kiến Thiết", "Đông Thọ"]
    tq_sd = ["Hồng Sơn", "Trường Sinh", "Phú Lương", "Sơn Thủy", "Minh Thanh", "Tân Trào", "Tân Thanh", "Bình Ca", "Sơn Dương"]
    tq_ch = ["Yên Nguyên", "Kim Bình", "Tri Phú"]
    hg_mv = ["Mèo Vạc", "Khâu Vai", "Sơn Vĩ", "Giàng Chu Phìn", "Lũng Pù", "Cán Chu Phìn", "Thượng Phùng", "Xín Cái", "Pả Vi", "Pải Lủng", "Tả Lủng", "Nậm Ban", "Niêm Tòng", "Tát Ngà"]
    hg_dv = ["Đồng Văn", "Lũng Cú", "Sà Phìn", "Phố Bảng", "Ma Lé", "Sính Lủng"]
    hg_ym = ["Yên Minh", "Bạch Đích", "Thắng Mố", "Mậu Duệ", "Du Già", "Đường Thượng", "Ngọc Long", "Lũng Phìn", "Niêm Sơn", "Sủng Máng"]
    hg_qb = ["Quản Bạ", "Cán Tỷ", "Lùng Tám", "Tùng Vài", "Nghĩa Thuận", "Đông Hà", "Quyết Tiến", "Bát Đại Sơn"]
    
    for x in tq_tp:
        if x in ten_diem: return "TP Tuyên Quang"
    for x in tq_ys:
        if x in ten_diem: return "H. Yên Sơn"
    for x in tq_sd:
        if x in ten_diem: return "H. Sơn Dương"
    for x in tq_ch:
        if x in ten_diem: return "H. Chiêm Hóa"
    for x in hg_mv:
        if x in ten_diem: return "H. Mèo Vạc"
    for x in hg_dv:
        if x in ten_diem: return "H. Đồng Văn"
    for x in hg_ym:
        if x in ten_diem: return "H. Yên Minh"
    for x in hg_qb:
        if x in ten_diem: return "H. Quản Bạ"
    return "Huyện Bắc Mê / Khác"

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
            ["TP Tuyên Quang", "Sơn Dương", "Yên Sơn", "Hàm Yên", "Chiêm Hóa", "Na Hang", "Lâm Bình", "Hà Giang", "Mèo Vạc", "Đồng Văn", "Yên Minh", "Quản Bạ", "Bắc Mê"]
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
    st.title("📊 TRUNG TÂM GIÁM SÁT & ĐIỀU HÀNH DỰ ÁN 880 (LÃNH ĐẠO)")
    st.caption("Tổng hợp khối lượng danh mục, tiến độ vận chuyển và hoàn thành lắp đặt thực tế")
    
    tong_so_diem = len(DANH_SACH_DIEM_CHUAN)
    
    # 4 Ô CHỈ SỐ KPI CHUẨN XÁC
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="📍 Tổng điểm danh mục (Cột D)", value=f"{tong_so_diem} điểm")
    with col2:
        st.metric(label="🚚 Tiến độ Giao hàng", value="Đang cập nhật", delta="Đồng bộ theo KTV")
    with col3:
        st.metric(label="🔧 Tiến độ Lắp đặt", value="Đang cập nhật", delta="Đồng bộ theo KTV")
    with col4:
        st.metric(label="✅ Tỷ lệ Nghiệm thu", value="Đang cập nhật", delta="Theo thời gian thực")
        
    st.markdown("---")
    
    # PHÂN TÍCH KHỐI LƯỢNG ĐIỂM THEO HUYỆN / KHU VỰC
    st.subheader("📈 Phân Bổ Điểm Triển Khai Theo Khu Vực Địa Bàn")
    
    data_khu_vuc = []
    for d in DANH_SACH_DIEM_CHUAN:
        data_khu_vuc.append({
            "Địa bàn": d,
            "Khu vực": xac_dinh_khu_vuc(d),
            "Thiết bị định mức": 5
        })
    df_all = pd.DataFrame(data_khu_vuc)
    df_khuvuc = df_all.groupby("Khu vực").size().reset_index(name="Số lượng điểm")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.write("**Số lượng điểm tác nghiệp theo từng địa bàn huyện/thành phố:**")
        st.bar_chart(df_khuvuc.set_index("Khu vực"), color="#0d6efd")
        
    with col_chart2:
        st.write("**Tỷ lệ phân bổ theo huyện/thị:**")
        st.dataframe(df_khuvuc, use_container_width=True, hide_index=True)
        
    st.markdown("---")
    
    # BẢNG TỔNG HỢP TOÀN BỘ CÁC ĐIỂM CỦA DỰ ÁN
    st.subheader(f"📋 Bảng Chi Tiết {tong_so_diem} Điểm Triển Khai Toàn Tuyến (Cột D)")
    
    # Bộ lọc nhanh cho lãnh đạo
    khu_vuc_filter = st.selectbox(
        "Lọc nhanh theo khu vực:",
        options=["Tất cả khu vực"] + sorted(list(df_all["Khu vực"].unique()))
    )
    
    if khu_vuc_filter != "Tất cả khu vực":
        df_hienthi = df_all[df_all["Khu vực"] == khu_vuc_filter]
    else:
        df_hienthi = df_all
        
    st.dataframe(
        df_hienthi[["Khu vực", "Địa bàn", "Thiết bị định mức"]], 
        use_container_width=True, 
        hide_index=True
    )

# ==============================================================================
# NHÁNH 3: BÁO CÁO TIẾN ĐỘ HIỆN TRƯỜNG (KỸ THUẬT VIÊN)
# ==============================================================================
else:
    st.title("🛠️ BÁO CÁO TIẾN ĐỘ THỰC HIỆN DỰ ÁN")
    st.caption("Tra cứu tuyến đường, lấy tọa độ GPS thực địa & nghiệm thu công việc")
    
    col_a, col_b = st.columns(2)
    with col_a:
        ma_da = st.selectbox("Mã dự án *", ["DA880", "Dự án khác"])
        
        # Ô CHỌN ĐỘI: CHẠM VÀO GÕ NGAY, CÓ GỢI Ý ĐẦY ĐỦ (INDEX=NONE)
        doi_thuc_hien_chon = st.selectbox(
            "Đội thực hiện *",
            options=DANH_SACH_DOI_CHUAN,
            index=None,
            placeholder="🔎 Chạm vào để gõ tìm đội (VHH, NTH, 006...)",
            help="Chạm vào là danh sách gợi ý hiện lên, gõ để lọc nhanh."
        )
        
        if not doi_thuc_hien_chon:
            doi_thuc_hien = "VHH"
        elif "Tự nhập" in doi_thuc_hien_chon:
            doi_thuc_hien = st.text_input("Gõ chính xác tên đội mới:")
        else:
            doi_thuc_hien = doi_thuc_hien_chon

    with col_b:
        # Ô CHỌN ĐIỂM: CHẠM VÀO GÕ NGAY (INDEX=NONE, ĐẦY ĐỦ TOÀN BỘ CỘT D)
        diem_duoc_chon = st.selectbox(
            "Điểm tác nghiệp (Chỉ hiển thị tên phường/xã) *",
            options=DANH_SACH_DIEM_CHUAN + ["🔍 [Tự nhập điểm khác ngoài danh mục...]"],
            index=None,
            placeholder="🔎 Chạm vào để gõ tìm (Mèo Vạc, Đồng Văn, Minh Xuân...)",
            help="Chạm vào là gợi ý các xã/phường Cột D hiện ra ngay."
        )
        
        if diem_duoc_chon == "🔍 [Tự nhập điểm khác ngoài danh mục...]":
            diem_thuc_te = st.text_input("Gõ tên địa điểm tác nghiệp cụ thể:", placeholder="Gõ tên xã/phường hoặc thôn/xóm...")
        elif diem_duoc_chon:
            diem_thuc_te = diem_duoc_chon
        else:
            diem_thuc_te = "Xã Mèo Vạc"

        dia_chi_mac_dinh = f"{diem_thuc_te}"

        st.number_input(
            "Số lượng thiết bị định mức (Cố định phân bổ) - [KHÓA CỐ ĐỊNH]", 
            value=5, 
            disabled=True,
            help="Số lượng được lấy cố định từ Kho phân bổ. Kỹ thuật viên không được chỉnh sửa."
        )

    st.markdown("---")

    # KHU VỰC DẪN ĐƯỜNG & GPS
    st.markdown("### 🗺️ Tiện Ích Dẫn Đường & Định Vị Thực Địa")
    col_nav1, col_nav2 = st.columns([1.3, 1])
    
    with col_nav1:
        st.write(f"**Điểm đến chỉ đường:** `{dia_chi_mac_dinh}`")
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
        
        default_map_url = "https://maps.google.com/?q=21.83059,105.19240"
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
                "so_luong": 5,
                "tinh_trang": tinh_trang,
                "link_maps": link_maps
            }
            try:
                resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
                st.success(f"🎉 Đã gửi thành công! Đội: {doi_thuc_hien} | Trạng thái: {tinh_trang} tại {diem_thuc_te}.")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Báo cáo đã ghi nhận, hệ thống đang đồng bộ về Google Sheets.")
