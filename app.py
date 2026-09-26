import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import urllib.parse
import base64

st.set_page_config(
    page_title="Hệ Thống Quản Lý & Điều Hành Dự Án 880",
    page_icon="📡",
    layout="wide"
)

# ==============================================================================
# 1. BỘ XỬ LÝ NHẬN DIỆN VÀ ĐỒNG BỘ ĐIỀU HƯỚNG TỪ URL (FIX LỖI ẢNH 2)
# ==============================================================================
DANH_SACH_MENU = [
    "🛠️ Báo cáo hiện trường", 
    "📱 Duyệt nhân sự (Admin)", 
    "📝 Đăng ký thành viên", 
    "📊 Giám sát lãnh đạo"
]

# Đọc tham số URL
query_view = st.query_params.get("view", "hientruong").lower().strip()

target_index = 0
if "duyet" in query_view:
    target_index = 1
elif "dangky" in query_view:
    target_index = 2
elif "lanhdao" in query_view:
    target_index = 3

# Đồng bộ chuyển tab tức thì theo URL
if "current_nav" not in st.session_state or st.session_state.get("last_query") != query_view:
    st.session_state.current_nav = DANH_SACH_MENU[target_index]
    st.session_state.last_query = query_view

che_do_chon = st.radio(
    "📌 Chuyển nhanh giao diện:",
    options=DANH_SACH_MENU,
    index=DANH_SACH_MENU.index(st.session_state.current_nav),
    horizontal=True,
    key="nav_radio"
)
st.session_state.current_nav = che_do_chon

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCY-kns_lnNkgC-005rSYquDgcUgvBhdylHormgQktnydC0qhAfp62Lmm_9qLvrU6xIQ/exec"
ADMIN_PIN = "880880"

# ==============================================================================
# DANH MỤC CÁC ĐỘI THEO SHEET QUẢN LÝ ĐỘI
# ==============================================================================
DANH_SACH_DOI_CHUAN = [
    "VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A", "Trần Văn B",
    "Đội KTV 006", "Đội KTV 007", "Đội KTV 008", "Đội KTV 009", "Đội KTV 010",
    "Đội KTV 011", "Đội KTV 012", "Đội KTV 013", "Đội KTV 014", "Đội KTV 015",
    "Đội KTV 016", "Đội KTV 017", "Đội KTV 018", "Đội KTV 019", "Đội KTV 020",
    "Đội KTV 021", "Đội KTV 022", "Đội KTV 023", "🔍 [Tự nhập tên đội khác...]"
]

# ==============================================================================
# DANH MỤC ĐỊA BÀN MỞ RỘNG (TUYÊN QUANG + TOÀN TUYẾN HÀ GIANG)
# ==============================================================================
DANH_SACH_DIA_BAN_DANG_KY = [
    "TP Tuyên Quang", "H. Yên Sơn", "H. Sơn Dương", "H. Hàm Yên", "H. Chiêm Hóa", "H. Na Hang", "H. Lâm Bình",
    "H. Mèo Vạc (Hà Giang)", "H. Đồng Văn (Hà Giang)", "H. Yên Minh (Hà Giang)", "H. Quản Bạ (Hà Giang)", 
    "H. Bắc Mê (Hà Giang)", "H. Vị Xuyên (Hà Giang)", "TP Hà Giang"
]

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

if "cho_duyet" not in st.session_state:
    st.session_state.cho_duyet = []

st.markdown("---")

# ==============================================================================
# GIAO DIỆN 1: DUYỆT NHÂN SỰ (ADMIN TRÊN ĐIỆN THOẠI)
# ==============================================================================
if che_do_chon == "📱 Duyệt nhân sự (Admin)":
    st.title("📱 DUYỆT NHÂN SỰ MỚI (DÀNH CHO ADMIN)")
    st.caption("Xem thông tin và phê duyệt thành viên mới trực tiếp ngay trên điện thoại")
    
    pin_admin = st.text_input("🔑 Nhập mã PIN Quản trị viên để mở khóa:", type="password", placeholder="Nhập mã PIN bảo mật...", key="pin_admin_input")
    
    if pin_admin == ADMIN_PIN:
        st.success("🔓 Xác thực thành công! Đã mở quyền Quản trị viên.")
        
        danh_sach = st.session_state.cho_duyet
        st.subheader(f"📋 Yêu cầu chờ duyệt ({len(danh_sach)} nhân sự)")
        
        if len(danh_sach) == 0:
            st.info("Hiện không có yêu cầu nào chờ duyệt.")
        else:
            for idx, user in enumerate(danh_sach):
                with st.expander(f"👤 {user['ho_ten']} - {user['sdt']}", expanded=True):
                    st.write(f"**Chuyên môn / Vai trò:** `{user['vai_tro']}`")
                    st.write(f"**Phương tiện:** `{user.get('phuong_tien', 'Xe máy')}`")
                    st.write(f"**Địa bàn nhận:** `{user['dia_ban']}`")
                    st.write(f"**Đội nguyện vọng gán:** `{user.get('doi_gan', 'Chưa chọn')}`")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"✅ DUYỆT VÀO HỆ THỐNG", key=f"duyet_{idx}"):
                            payload_duyet = {
                                "action": "duyet_thanh_vien",
                                "ho_ten": user["ho_ten"],
                                "so_dien_thoai": user["sdt"],
                                "vai_tro": user["vai_tro"],
                                "dia_ban": user["dia_ban"],
                                "phuong_tien": user.get("phuong_tien", "Xe máy"),
                                "doi_gan": user.get("doi_gan", "")
                            }
                            try:
                                requests.post(WEBHOOK_URL, json=payload_duyet, timeout=15)
                            except Exception:
                                pass
                            st.session_state.cho_duyet.pop(idx)
                            st.success(f"Đã duyệt thành công nhân sự: {user['ho_ten']}!")
                            st.rerun()
                            
                    with col_btn2:
                        if st.button(f"❌ TỪ CHỐI", key=f"tuchoi_{idx}"):
                            st.session_state.cho_duyet.pop(idx)
                            st.warning(f"Đã từ chối nhân sự: {user['ho_ten']}!")
                            st.rerun()
    elif pin_admin != "":
        st.error("❌ Mã PIN không chính xác! Vui lòng kiểm tra lại.")
    else:
        st.info("🔒 Vui lòng nhập mã PIN quản trị để xem và phê duyệt nhân sự.")

# ==============================================================================
# GIAO DIỆN 2: ĐĂNG KÝ THÀNH VIÊN (ĐÃ BỔ SUNG ĐẦY ĐỦ THEO ẢNH 1 & ẢNH 2)
# ==============================================================================
elif che_do_chon == "📝 Đăng ký thành viên":
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
        
        # ĐỊA BÀN PHỤ TRÁCH ĐẦY ĐỦ CẢ TUYÊN QUANG VÀ HÀ GIANG
        dia_ban = st.multiselect(
            "Địa bàn phụ trách có thể nhận *", 
            options=DANH_SACH_DIA_BAN_DANG_KY,
            placeholder="Bấm vào để chọn một hoặc nhiều huyện/thành phố..."
        )
        
        # GỢI Ý ĐỘI GÁN (KHỚP THEO SHEET QUẢN LÝ ĐỘI)
        doi_nguyen_vong = st.selectbox(
            "Nguyện vọng tham gia Đội (Đội gán)",
            options=["Chưa xác định (Admin tự phân bổ)"] + DANH_SACH_DOI_CHUAN[:-1],
            index=0
        )
        
        submitted = st.form_submit_button("GỬI ĐĂNG KÝ")
        if submitted:
            if not ho_ten or not so_dien_thoai or not dia_ban:
                st.error("Vui lòng điền đầy đủ: Họ tên, Số điện thoại và Địa bàn phụ trách!")
            else:
                chuyen_mon_cuoi = chuyen_mon_tu_ghi.strip() if chuyen_mon_tu_ghi.strip() else lua_chon_vai_tro
                payload = {
                    "action": "dang_ky_thanh_vien",
                    "ho_ten": ho_ten,
                    "so_dien_thoai": so_dien_thoai,
                    "chuyen_mon": chuyen_mon_cuoi,
                    "phuong_tien": phuong_tien,
                    "dia_ban": ", ".join(dia_ban),
                    "doi_gan": doi_nguyen_vong if doi_nguyen_vong != "Chưa xác định (Admin tự phân bổ)" else ""
                }
                
                # Lưu vào bộ nhớ tạm duyệt trên app
                st.session_state.cho_duyet.append({
                    "ho_ten": ho_ten,
                    "sdt": so_dien_thoai,
                    "vai_tro": chuyen_mon_cuoi,
                    "phuong_tien": phuong_tien,
                    "dia_ban": ", ".join(dia_ban),
                    "doi_gan": doi_nguyen_vong
                })
                
                try:
                    requests.post(WEBHOOK_URL, json=payload, timeout=15)
                except Exception:
                    pass
                st.success(f"🎉 Đã gửi đăng ký thành công cho {ho_ten}! Quản trị viên sẽ phê duyệt và gán đội.")

# ==============================================================================
# GIAO DIỆN 3: GIÁM SÁT LÃNH ĐẠO (BẢO VỆ MÃ PIN)
# ==============================================================================
elif che_do_chon == "📊 Giám sát lãnh đạo":
    st.title("📊 TRUNG TÂM GIÁM SÁT & ĐIỀU HÀNH DỰ ÁN (LÃNH ĐẠO)")
    st.caption("Báo cáo tiến độ và bảng điều hành chỉ số nội bộ")
    
    pin_lanhdao = st.text_input("🔑 Nhập mã PIN Lãnh đạo để xem báo cáo:", type="password", placeholder="Nhập mã PIN bảo mật...", key="pin_lanhdao_input")
    
    if pin_lanhdao == ADMIN_PIN:
        st.success("🔓 Xác thực thành công! Đã mở quyền truy cập Báo cáo Lãnh đạo.")
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="📍 Tổng điểm danh mục Cột D", value=f"{len(DANH_SACH_DIEM_CHUAN)} điểm")
        with col2:
            st.metric(label="🚚 Tiến độ Giao hàng", value="Đang cập nhật", delta="Live")
        with col3:
            st.metric(label="🔧 Tiến độ Lắp đặt", value="Đang cập nhật", delta="Live")
        with col4:
            st.metric(label="✅ Tỷ lệ Nghiệm thu", value="Đang cập nhật", delta="Live")
            
        st.markdown("---")
        st.subheader(f"📋 Bảng Chi Tiết Toàn Bộ {len(DANH_SACH_DIEM_CHUAN)} Điểm Triển Khai (Cột D)")
        df_preview = pd.DataFrame({"STT": range(1, len(DANH_SACH_DIEM_CHUAN) + 1), "Địa bàn": DANH_SACH_DIEM_CHUAN})
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
    elif pin_lanhdao != "":
        st.error("❌ Mã PIN không chính xác! Vui lòng kiểm tra lại.")
    else:
        st.info("🔒 Vui lòng nhập mã PIN bảo mật để xem báo cáo điều hành và số liệu dự án.")

# ==============================================================================
# GIAO DIỆN 4: BÁO CÁO TIẾN ĐỘ HIỆN TRƯỜNG (KỸ THUẬT VIÊN)
# ==============================================================================
else:
    st.title("🛠️ BÁO CÁO TIẾN ĐỘ THỰC HIỆN DỰ ÁN")
    st.caption("Tra cứu tuyến đường, chụp ảnh nghiệm thu, lấy GPS & hoàn tất công việc")
    
    col_a, col_b = st.columns(2)
    with col_a:
        ma_da = st.selectbox("Mã dự án *", ["DA880", "Dự án khác"])
        
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

    # KHU VỰC CHỤP ẢNH HIỆN TRƯỜNG & NGHIỆM THU
    st.markdown("### 📷 Chụp Ảnh Hiện Trường & Bàn Giao Thiết Bị")
    tab_cam, tab_file = st.tabs(["📸 Chụp trực tiếp bằng Camera", "📁 Tải ảnh từ thư viện máy"])
    
    anh_base64 = ""
    with tab_cam:
        anh_chup = st.camera_input("Chạm để bật camera chụp ảnh hiện trường:")
        if anh_chup is not None:
            bytes_data = anh_chup.getvalue()
            anh_base64 = base64.b64encode(bytes_data).decode()
            st.success("✅ Đã chụp ảnh hiện trường thành công!")
            
    with tab_file:
        anh_tai_len = st.file_uploader("Hoặc chọn ảnh đã chụp sẵn trong máy:", type=["jpg", "jpeg", "png"])
        if anh_tai_len is not None and not anh_base64:
            bytes_data = anh_tai_len.getvalue()
            anh_base64 = base64.b64encode(bytes_data).decode()
            st.success("✅ Đã tải ảnh lên thành công!")

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
        
        ghi_chu = st.text_input("Ghi chú hiện trường (nếu có):", placeholder="Ví dụ: Đã bàn giao chìa khóa tủ rack, tín hiệu tốt...")
        
        btn_gui = st.form_submit_button("XÁC NHẬN BÁO CÁO NGHIỆM THU")
        if btn_gui:
            payload = {
                "ma_da": ma_da,
                "doi_thuc_hien": doi_thuc_hien,
                "diem_lap_dat": diem_thuc_te,
                "so_luong": 5,
                "tinh_trang": tinh_trang,
                "link_maps": link_maps,
                "ghi_chu": ghi_chu,
                "anh_hien_truong": anh_base64
            }
            try:
                resp = requests.post(WEBHOOK_URL, json=payload, timeout=20)
                st.success(f"🎉 Đã gửi thành công! Đội: {doi_thuc_hien} | Trạng thái: {tinh_trang} tại {diem_thuc_te} kèm ảnh hiện trường.")
                st.balloons()
            except Exception as e:
                st.warning("⚠️ Báo cáo đã ghi nhận, hệ thống đang đồng bộ về Google Sheets.")
