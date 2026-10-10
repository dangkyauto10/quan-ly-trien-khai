import streamlit as st
import urllib.request
import json
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

# CSS TÙY CHỈNH GIÚP CHỮ TRÊN NÚT TO, RÕ RÀNG VÀ DỄ BẤM HƠN TRÊN MOBILE
st.markdown("""
    <style>
    /* Định dạng lại tất cả các nút bấm cho to, rõ, đậm nét */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold !important;
        font-size: 15px !important;
        height: 50px !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwp2Pq3-PYNvHOWe4IQVm5PqeJd5TcIc_mPDtLm0BkDEGYUxq-C1cnV3rNS1X3xfI1p7w/exec"

@st.cache_data(ttl=300)
def tai_danh_sach_diem():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            ket_qua = json.loads(response.read().decode('utf-8'))
            if ket_qua.get("status") == "success": return ket_qua.get("danh_sach_diem", [])
    except: pass
    return ["-- Lỗi mạng: Không tải được danh sách --"]

DANH_SACH_DIEM = tai_danh_sach_diem()

def submit_registration(ho_ten, sdt, dia_ban, chuyen_mon, phuong_tien):
    payload = {"action": "dang_ky", "ho_ten": ho_ten, "sdt": sdt, "dia_ban": dia_ban, "chuyen_mon": chuyen_mon, "phuong_tien": phuong_tien}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except: return False

def submit_to_google(ma_da, ten_doi, diem_lap, diem_giao, ds_hang, gps, tinh_trang):
    payload = {"action": "bao_cao", "ma_du_an": ma_da, "ten_doi": ten_doi, "diem_lap_dat": diem_lap, "diem_giao_hang": diem_giao, "ds_hang_hoa": ds_hang, "link_maps": gps, "tinh_trang": tinh_trang}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except: return False

def load_live_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')), None
    except Exception as e: return None, f"LỖI KẾT NỐI API: {e}"

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

st.markdown("<h3 style='text-align: center; color: #1E3A8A; margin-bottom: 0px;'>🚀 ĐIỀU HÀNH HIỆN TRƯỜNG</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-top: 5px;'>Hệ thống quản lý phân bổ & báo cáo tự động</p>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: btn_dang_ky = st.button("📝 Đăng ký", use_container_width=True)
with c2: btn_bao_cao = st.button("📊 Báo cáo", use_container_width=True)
with c3: btn_admin = st.button("🔒 Admin", use_container_width=True)
with c4: btn_link = st.button("🔗 Link", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

if st.session_state.nav_tab == "Dang_ky":
    st.markdown("#### 📝 ĐĂNG KÝ THÀNH VIÊN ĐỘI")
    with st.form("form_dang_ky_thanh_vien"):
        reg_hoten = st.text_input("Họ và tên *", placeholder="Nhập đầy đủ họ và tên...")
        reg_sdt = st.text_input("Số điện thoại liên hệ *", placeholder="Nhập số điện thoại (Zalo)...")
        reg_diaban_list = st.multiselect("Địa bàn phụ trách", options=DANH_SACH_DIEM)
        reg_chuyenmon = st.selectbox("Chuyên môn / Nhiệm vụ", options=["1. Vận chuyển / Giao nhận", "2. KTV Lắp đặt thiết bị", "3. Giám sát / Điều phối chung", "4. Kho vận / Hậu cứ"])
        reg_phuongtien = st.selectbox("Phương tiện di chuyển", options=["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        if st.form_submit_button("Gửi Đăng Ký", type="primary", use_container_width=True):
            if not reg_hoten.strip() or not reg_sdt.strip(): st.warning("Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            else:
                if submit_registration(reg_hoten, reg_sdt, ", ".join(reg_diaban_list), reg_chuyenmon, reg_phuongtien): st.success(f"Đăng ký thành công {reg_hoten}!")
                else: st.error("Gửi đăng ký thất bại!")

elif st.session_state.nav_tab == "Bao_cao":
    raw_data, err_msg = load_live_data()
    if err_msg: st.error(err_msg)
    
    data_ld = raw_data.get("KHO_LAP_DAT", []) if isinstance(raw_data, dict) else []
    data_vc = raw_data.get("KHO_VAN_CHUYEN", []) if isinstance(raw_data, dict) else []
    
    st.success(f"✅ Đã kết nối API: **{len(data_ld)}** dòng LĐ | **{len(data_vc)}** dòng VC")
    
    st.markdown("##### 1️⃣ Chọn thông tin nhiệm vụ")
    du_an_chon = st.selectbox("CHỌN DỰ ÁN TRIỂN KHAI *", options=(raw_data.get("du_an", []) if isinstance(raw_data, dict) else []), index=None)
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

        st.markdown("##### 2️⃣ Danh mục thiết bị phân bổ")
        if ds_hang:
            tb_md = "| SKU | Thiết bị | SL | ĐVT |\n| :--- | :--- | :---: | :---: |\n"
            for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(tb_md)
        else:
            st.warning("Không tìm thấy hàng hóa phân bổ cho dự án, đội và địa điểm này.")
    else: 
        st.info("💡 Vui lòng chọn đầy đủ Dự án, Đội và Địa điểm để hiển thị danh mục thiết bị.")
        
    st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
    st.markdown("##### 3️⃣ Xác thực hiện trường (Ảnh & GPS)")
    st.camera_input("Chụp ảnh thực tế hiện trường")
    
    loc = streamlit_geolocation()
    gps_link = ""
    
    if loc and loc.get('latitude'):
        lat = loc['latitude']
        lon = loc['longitude']
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"
        st.success("✅ Đã chốt tọa độ GPS thành công!")
        st.markdown(f"[📍 Kiểm tra vị trí trên bản đồ Google Maps]({gps_link})")
    else:
        st.warning("⚠️ Vui lòng bấm định vị (Location) để lấy tọa độ trước khi nộp báo cáo.")

    st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
    st.markdown("##### 4️⃣ Nút Báo cáo kết quả")
    
    # Rút gọn câu chữ trên nút cho to, rõ ràng và dễ đọc trên di động
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("🚚 ĐÃ GIAO", type="primary", use_container_width=True):
            if not gps_link: st.error("❌ Thiếu GPS!")
            elif submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, "", diem_giao_lap, ds_hang, gps_link, "Đã giao hàng"): st.success("🎉 Giao hàng thành công!")
    with col_b2:
        if st.button("🔧 ĐÃ LẮP", type="primary", use_container_width=True):
            if not gps_link: st.error("❌ Thiếu GPS!")
            elif submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, diem_giao_lap, "", ds_hang, gps_link, "Đã lắp đặt"): st.success("🎉 Lắp đặt thành công!")
    with col_b3:
        if st.button("✅ HOÀN TẤT", type="primary", use_container_width=True):
            if not gps_link: st.error("❌ Thiếu GPS!")
            elif submit_to_google(du_an_chon if du_an_chon else "", doi_thuc_hiện, diem_giao_lap, diem_giao_lap, ds_hang, gps_link, "Giao và Lắp xong"): st.success("🎉 Hoàn tất thành công!")

elif st.session_state.nav_tab in ["Admin", "Link"]:
    st.markdown("#### 🔒 QUẢN TRỊ HỆ THỐNG")
    pass_input = st.text_input("Nhập mật khẩu (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("Xác thực thành công!")
        if st.session_state.nav_tab == "Link":
            st.markdown("- [🔗 Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
