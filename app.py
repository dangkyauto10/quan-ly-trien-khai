import streamlit as st
import urllib.request
import json
import base64
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="QUẢN LÝ DỰ ÁN", page_icon="🚀", layout="centered")

# ==========================================
# CSS GIAO DIỆN ĐIỆN THOẠI HIỆN ĐẠI (NATIVE APP UI)
# ==========================================
st.markdown("""
    <style>
    /* Căn chỉnh lại lề cho gọn gàng */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 600px;
    }
    /* Bo góc và làm bóng các nút bấm (Hiệu ứng 3D như app thật) */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700 !important;
        font-size: 15px !important;
        height: 50px !important;
        color: white !important;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:active {
        transform: scale(0.97);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Riêng nút báo cáo Lắp đặt / Giao hàng sẽ dùng màu nổi bật */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    }
    /* Khung nhập liệu bo góc hiện đại */
    div[data-baseweb="select"] > div, input {
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 2px !important;
    }
    /* Tiêu đề các mục con chuyên nghiệp */
    h5 {
        color: #1E293B;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwp2Pq3-PYNvHOWe4IQVm5PqeJd5TcIc_mPDtLm0BkDEGYUxq-C1cnV3rNS1X3xfI1p7w/exec"

# ==========================================
# HÀM TẢI DỮ LIỆU TỐI ƯU SIÊU TỐC (CHỈ GỌI KHI CẦN)
# ==========================================
@st.cache_data(ttl=300)
def fetch_api_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')), None
    except Exception as e: 
        return None, f"LỖI KẾT NỐI API: {e}"

def submit_registration(ho_ten, sdt, dia_ban, chuyen_mon, phuong_tien):
    payload = {"action": "dang_ky", "ho_ten": ho_ten, "sdt": sdt, "dia_ban": dia_ban, "chuyen_mon": chuyen_mon, "phuong_tien": phuong_tien}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except: return False

def submit_to_google(ma_da, ten_doi, diem_lap, diem_giao, ds_hang, gps, tinh_trang, image_file):
    img_base64 = ""
    if image_file is not None:
        try:
            img_bytes = image_file.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        except: pass

    payload = {
        "action": "bao_cao", 
        "ma_du_an": ma_da, 
        "ten_doi": ten_doi, 
        "diem_lap_dat": diem_lap, 
        "diem_giao_hang": diem_giao, 
        "ds_hang_hoa": ds_hang, 
        "link_maps": gps, 
        "tinh_trang": tinh_trang,
        "image_base64": img_base64
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except: return False

def quet_mat_than(data_sheet, p_code, d_doi, d_diem):
    ds_kq = []
    if not data_sheet: return ds_kq
    
    idx_proj = -1; idx_matb = -1; idx_doi = -1; idx_tentb = -1; idx_sl = -1; idx_diem = -1; idx_dvt = -1
    header_row_index = -1
    
    for r_idx, r in enumerate(data_sheet[:10]):
        row_str = " ".join([str(x).upper() for x in r])
        if "MÃ CÔNG VIỆC" in row_str or "MÃ DA" in row_str or "TÊN THIẾT BỊ" in row_str:
            header_row_index = r_idx
            for i, h in enumerate(r):
                h_str = str(h).replace('\xa0', ' ').strip().upper() 
                if "MÃ DỰ ÁN" in h_str or "MÃ DA" in h_str: idx_proj = i
                elif "ĐỊA ĐIỂM LẮP" in h_str or "ĐIỂM GIAO" in h_str or "ĐỊA ĐIỂM" in h_str or "ĐƠN VỊ" in h_str: idx_diem = i
                elif "MÃ CÔNG VIỆC" in h_str or "SKU" in h_str: idx_matb = i
                elif "TÊN THIẾT BỊ" in h_str or "HÀNG HÓA" in h_str: idx_tentb = i
                elif "SỐ LƯỢNG" in h_str or "SL" in h_str: idx_sl = i
                elif "ĐƠN VỊ TÍNH" in h_str or "ĐVT" in h_str: idx_dvt = i
                elif "ĐỘI GIAO THIẾT BỊ" in h_str or "ĐỘI NHẬN THIẾT BỊ" in h_str or "ĐỘI" in h_str or "NHÂN SỰ" in h_str: idx_doi = i
            break 

    if idx_proj == -1 or idx_diem == -1 or idx_doi == -1 or header_row_index == -1: return ds_kq

    p_c = str(p_code).replace('\xa0', ' ').strip().upper()
    d_d = str(d_diem).replace('\xa0', ' ').strip().upper()
    d_o = str(d_doi).replace('\xa0', ' ').strip().upper()

    for r in data_sheet[header_row_index + 1:]:
        if len(r) > max(idx_proj, idx_diem, idx_doi):
            c_proj = str(r[idx_proj]).replace('\xa0', ' ').strip().upper()
            c_diem = str(r[idx_diem]).replace('\xa0', ' ').strip().upper()
            c_doi = str(r[idx_doi]).replace('\xa0', ' ').strip().upper()
            
            if p_c in c_proj and (d_d in c_diem or (c_diem != "" and c_diem in d_d)) and (d_o in c_doi or (c_doi != "" and c_doi in d_o)):
                sku = str(r[idx_matb]).strip() if (idx_matb > -1 and len(r) > idx_matb) else "TB-0X"
                ten = str(r[idx_tentb]).strip() if (idx_tentb > -1 and len(r) > idx_tentb) else "Thiết bị"
                sl = str(r[idx_sl]).strip() if (idx_sl > -1 and len(r) > idx_sl) else "1"
                dvt = str(r[idx_dvt]).strip() if (idx_dvt > -1 and len(r) > idx_dvt) else "Bộ"
                if ten and str(ten).upper() not in ["TÊN THIẾT BỊ / HÀNG HÓA", "TÊN THIẾT BỊ", "NONE", ""]:
                    ds_kq.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})
    return ds_kq

# ==========================================
# KHU VỰC HIỂN THỊ CHÍNH
# ==========================================
# ==========================================
# KHU VỰC HIỂN THỊ CHÍNH
# ==========================================
st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 900;'>🚀 QUẢN LÝ DỰ ÁN</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>Hệ thống Điều hành Hiện trường</p>", unsafe_allow_html=True)

menu_options = ["📊 Báo cáo nhiệm vụ", "📝 Đăng ký thành viên", "🔒 ADMIN DUYỆT ĐK THÀNH VIÊN", "🔗 Báo cáo tiến độ (để lãnh đạo xem)"]
selected_menu = st.selectbox("CHỌN CHỨC NĂNG", options=menu_options, label_visibility="collapsed")

if "Báo cáo" in selected_menu and "tiến độ" not in selected_menu: nav_tab = "Bao_cao"
elif "Đăng ký" in selected_menu: nav_tab = "Dang_ky"
elif "ADMIN" in selected_menu: nav_tab = "Admin"
else: nav_tab = "Link"

st.divider()

if nav_tab == "Dang_ky":
    st.markdown("##### 📝 ĐĂNG KÝ THÀNH VIÊN ĐỘI")
    
    with st.spinner("Đang tải dữ liệu..."):
        raw_data, err_msg = fetch_api_data()
        ds_diem = raw_data.get("danh_sach_diem", []) if isinstance(raw_data, dict) else []

    with st.form("form_dang_ky_thanh_vien"):
        reg_hoten = st.text_input("Họ và tên *", placeholder="Nhập đầy đủ họ và tên...")
        reg_sdt = st.text_input("Số điện thoại liên hệ *", placeholder="Nhập số điện thoại (Zalo)...")
        reg_diaban_list = st.multiselect("Địa bàn phụ trách", options=ds_diem)
        reg_chuyenmon = st.selectbox("Chuyên môn / Nhiệm vụ", options=["1. Vận chuyển / Giao nhận", "2. KTV Lắp đặt thiết bị", "3. Giám sát / Điều phối chung", "4. Kho vận / Hậu cứ"])
        reg_phuongtien = st.selectbox("Phương tiện di chuyển", options=["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("GỬI ĐĂNG KÝ", use_container_width=True):
            if not reg_hoten.strip() or not reg_sdt.strip(): st.warning("Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            else:
                if submit_registration(reg_hoten, reg_sdt, ", ".join(reg_diaban_list), reg_chuyenmon, reg_phuongtien): st.success(f"Đăng ký thành công {reg_hoten}!")
                else: st.error("Gửi đăng ký thất bại!")

elif nav_tab == "Bao_cao":
    with st.spinner("Đang đồng bộ dữ liệu hệ thống..."):
        raw_data, err_msg = fetch_api_data()
        
    if err_msg: st.error(err_msg)
    else:
        data_ld = raw_data.get("KHO_LAP_DAT", []) if isinstance(raw_data, dict) else []
        data_vc = raw_data.get("KHO_VAN_CHUYEN", []) if isinstance(raw_data, dict) else []
        
        st.info(f"✅ Đã kết nối Mắt Thần: {len(data_ld)} dòng LĐ | {len(data_vc)} dòng VC")
        
        st.markdown("##### 1️⃣ CHỌN THÔNG TIN NHIỆM VỤ")
        du_an_chon = st.selectbox("DỰ ÁN TRIỂN KHAI *", options=(raw_data.get("du_an", []) if isinstance(raw_data, dict) else []), index=None)
        doi_thuc_hiện = st.selectbox("TÊN ĐỘI THỰC HIỆN *", options=(raw_data.get("doi", []) if isinstance(raw_data, dict) else []), index=None)
        diem_giao_lap = st.selectbox("ĐỊA ĐIỂM GIAO & LẮP *", options=(raw_data.get("danh_sach_diem", []) if isinstance(raw_data, dict) else []), index=None)
        
        if du_an_chon and doi_thuc_hiện and diem_giao_lap:
            p_code = du_an_chon
            d_doi = doi_thuc_hiện
            d_diem = diem_giao_lap
            
            ds_hang_raw = quet_mat_than(data_ld, p_code, d_doi, d_diem) + quet_mat_than(data_vc, p_code, d_doi, d_diem)
            
            ds_hang = []
            seen = set()
            for item in ds_hang_raw:
                key = f"{item['sku']}_{item['ten']}_{item['sl']}"
                if key not in seen:
                    seen.add(key)
                    ds_hang.append(item)

            st.markdown("##### 2️⃣ THIẾT BỊ CẦN BÁO CÁO")
            if ds_hang:
                tb_md = "| SKU | Thiết bị | SL | ĐVT |\n| :--- | :--- | :---: | :---: |\n"
                for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
                st.markdown(tb_md)
            else:
                st.warning("Không tìm thấy hàng hóa phân bổ cho dự án, đội và địa điểm này.")
        else: 
            st.warning("💡 Chọn đầy đủ thông tin để hiển thị Mắt Thần.")
            
        st.markdown("##### 3️⃣ CHỤP ẢNH HIỆN TRƯỜNG")
        img_captured = st.camera_input("Chụp ảnh thực tế công việc")
        
        loc = streamlit_geolocation()
        gps_link = ""
        
        if loc and loc.get('latitude'):
            lat = loc['latitude']
            lon = loc['longitude']
            gps_link = f"https://www.google.com/maps?q={lat},{lon}"
            st.success("✅ Đã chốt tọa độ GPS an toàn!")
        else:
            st.error("⚠️ Bấm Định Vị (Location) để quét tọa độ GPS.")

        st.markdown("##### 4️⃣ CHỐT BÁO CÁO NGHIỆM THU")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🚚 ĐÃ GIAO", type="primary", use_container_width=True):
                if not gps_link: st.error("❌ Thiếu GPS!")
                elif not img_captured: st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner("Đang tải ảnh lên Drive..."):
                        if submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, "", diem_giao_lap, ds_hang, gps_link, "Đã giao hàng", img_captured): st.success("🎉 Xong!")
        with col_b2:
            if st.button("🔧 ĐÃ LẮP", type="primary", use_container_width=True):
                if not gps_link: st.error("❌ Thiếu GPS!")
                elif not img_captured: st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner("Đang tải ảnh lên Drive..."):
                        if submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, diem_giao_lap, "", ds_hang, gps_link, "Đã lắp đặt", img_captured): st.success("🎉 Xong!")
        with col_b3:
            if st.button("✅ GIAO & LẮP ĐẶT XONG", type="primary", use_container_width=True):
                if not gps_link: st.error("❌ Thiếu GPS!")
                elif not img_captured: st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner("Đang tải ảnh lên Drive..."):
                        if submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, diem_giao_lap, diem_giao_lap, ds_hang, gps_link, "Giao và Lắp xong", img_captured): st.success("🎉 Xong!")

elif nav_tab in ["Admin", "Link"]:
    if nav_tab == "Admin": st.markdown("##### 🔒 ADMIN DUYỆT ĐK THÀNH VIÊN")
    else: st.markdown("##### 🔒 TRUY CẬP DỮ LIỆU")
        
    khung_nhap_pin = st.empty()
    pass_input = khung_nhap_pin.text_input("Nhập mã PIN:", type="password")
    
    if pass_input == SECURE_PASS:
        khung_nhap_pin.empty() # Xóa sổ ô nhập PIN
        st.success("Xác thực thành công!")
        
        if nav_tab == "Admin":
            st.info("💡 Danh sách thành viên đang chờ duyệt:")
            raw_data, _ = fetch_api_data()
            ds_doi = raw_data.get("doi", []) if isinstance(raw_data, dict) else []
            
            with st.spinner("Đang quét thành viên mới..."):
                pending = get_pending_members()
                
            if not pending:
                st.success("🎉 Hiện không có thành viên nào cần duyệt!")
            else:
                for tv in pending:
                    st.markdown(f"""
                    <div class="pending-card">
                        <h4 style="color:#1E3A8A; margin-top:0px; margin-bottom:5px;">👤 {tv['ho_ten']}</h4>
                        <b>📞 SĐT:</b> {tv['sdt']} <br>
                        <b>📍 Địa bàn:</b> {tv['dia_ban']} <br>
                        <b>🛠 Chuyên môn:</b> {tv['chuyen_mon']} <br>
                        <b>🛵 Phương tiện:</b> {tv['phuong_tien']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    doi_chon = st.selectbox(f"Gán Đội cho {tv['ho_ten']}:", options=["-- Chưa gán đội --"] + ds_doi, key=f"doi_{tv['row']}")
                    
                    if st.button(f"✅ BẤM ĐỂ DUYỆT {tv['ho_ten'].upper()}", type="primary", key=f"btn_{tv['row']}", use_container_width=True):
                        voi_doi = "" if doi_chon == "-- Chưa gán đội --" else doi_chon
                        with st.spinner("Đang truyền lệnh về Google Sheets..."):
                            if approve_member(tv['row'], voi_doi):
                                st.success("Đã duyệt thành công! Vui lòng làm mới (F5) ứng dụng.")
                            else:
                                st.error("Lỗi mạng, vui lòng thử lại.")
                    st.divider()
                    
        elif nav_tab == "Link":
            st.info("💡 Dữ liệu báo cáo tổng hợp dành cho Lãnh đạo.")
            st.markdown("- [🔗 Mở Data Google Sheets (Báo cáo tiến độ)](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
