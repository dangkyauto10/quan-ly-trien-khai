import streamlit as st
import urllib.request
import json
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"

# !!! ANH VỸ KIỂM TRA LẠI LINK VÀ DÁN LINK MỚI VÀO ĐÂY NẾU CẦN !!!
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwQV_VqmnnEU3Mu7CDanFGwYnCu56rCOhY9q5emNGasXqwZRJlySd0CaysgNbb8BkjmNA/exec"

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

@st.cache_data(ttl=2)
def load_live_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')), None
    except Exception as e: return None, f"🚨 LỖI KẾT NỐI API: {e}"

# ĐÂY LÀ "MẮT THẦN" MỚI - Quét chuẩn chữ "Điểm Giao"
def quet_mat_than(data_sheet, p_code, d_doi, d_diem):
    ds_kq = []
    if not data_sheet: return ds_kq
    idx_proj = 1; idx_diem = 6; idx_matb = 0; idx_tentb = 3; idx_sl = 4; idx_dvt = 5; idx_doi = 2
    
    for r in data_sheet[:5]:
        for i, h in enumerate(r):
            h_str = str(h).replace('\xa0', ' ').strip().upper()
            if "MÃ DỰ ÁN" in h_str or "MÃ DA" in h_str: idx_proj = i
            elif "ĐỊA ĐIỂM" in h_str or "ĐƠN VỊ" in h_str or "ĐIỂM GIAO" in h_str: idx_diem = i
            elif "MÃ CÔNG VIỆC" in h_str or "SKU" in h_str: idx_matb = i
            elif "TÊN THIẾT BỊ" in h_str or "HÀNG HÓA" in h_str: idx_tentb = i
            elif "SỐ LƯỢNG" in h_str or "SL" in h_str: idx_sl = i
            elif "ĐƠN VỊ TÍNH" in h_str or "ĐVT" in h_str: idx_dvt = i
            elif "ĐỘI" in h_str or "NHÂN SỰ" in h_str: idx_doi = i

    for r in data_sheet:
        c_proj = str(r[idx_proj]).replace('\xa0', ' ').strip().upper() if len(r) > idx_proj else ""
        c_diem = str(r[idx_diem]).replace('\xa0', ' ').strip().upper() if len(r) > idx_diem else ""
        c_doi = str(r[idx_doi]).replace('\xa0', ' ').strip().upper() if len(r) > idx_doi else ""
        
        if p_code in c_proj and d_diem == c_diem and d_doi == c_doi:
            sku = str(r[idx_matb]).strip() if len(r) > idx_matb else "TB-0X"
            ten = str(r[idx_tentb]).strip() if len(r) > idx_tentb else "Thiết bị"
            sl = str(r[idx_sl]).strip() if len(r) > idx_sl else "1"
            dvt = str(r[idx_dvt]).strip() if len(r) > idx_dvt else "Bộ"
            if ten and ten.upper() not in ["TÊN THIẾT BỊ / HÀNG HÓA", "TÊN THIẾT BỊ", "NONE", ""]:
                ds_kq.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})
    return ds_kq

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HE THONG DIEU HANH DA DU AN HIEN TRUONG</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1: btn_dang_ky = st.button("Dang ky", use_container_width=True)
with col2: btn_bao_cao = st.button("Bao cao", use_container_width=True)
with col3: btn_admin = st.button("Admin duyet", use_container_width=True)
with col4: btn_link = st.button("Link bao cao", use_container_width=True)

if "nav_tab" not in st.session_state: st.session_state.nav_tab = "Bao_cao"
if btn_dang_ky: st.session_state.nav_tab = "Dang_ky"
if btn_bao_cao: st.session_state.nav_tab = "Bao_cao"
if btn_admin: st.session_state.nav_tab = "Admin"
if btn_link: st.session_state.nav_tab = "Link"

st.markdown("---")

if st.session_state.nav_tab == "Dang_ky":
    st.markdown("### 📝 ĐĂNG KÝ THÔNG TIN NHÂN SỰ / THÀNH VIÊN ĐỘI THI CÔNG")
    with st.form("form_dang_ky_thanh_vien"):
        reg_hoten = st.text_input("Họ và tên *", placeholder="Nhập đầy đủ họ và tên...")
        reg_sdt = st.text_input("Số điện thoại liên hệ *", placeholder="Nhập số điện thoại (Zalo)...")
        reg_diaban_list = st.multiselect("Địa bàn phụ trách", options=DANH_SACH_DIEM)
        reg_chuyenmon = st.selectbox("Chuyên môn / Nhiệm vụ", options=["1. Vận chuyển / Giao nhận", "2. KTV Lắp đặt thiết bị", "3. Giám sát / Điều phối chung", "4. Kho vận / Hậu cứ"])
        reg_phuongtien = st.selectbox("Phương tiện di chuyển", options=["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        if st.form_submit_button("Gửi Đăng Ký Thành Viên", type="primary", use_container_width=True):
            if not reg_hoten.strip() or not reg_sdt.strip(): st.warning("Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            else:
                if submit_registration(reg_hoten, reg_sdt, ", ".join(reg_diaban_list), reg_chuyenmon, reg_phuongtien): st.success(f"🎉 Đăng ký thành công {reg_hoten}!")
                else: st.error("Gửi đăng ký thất bại!")

elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (ALLOCATION SYNC)")
    
    raw_data, err_msg = load_live_data()
    if err_msg: st.error(err_msg)
    
    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1: du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", options=(raw_data.get("du_an", []) if isinstance(raw_data, dict) else []), index=None)
    with col_rf2:
        st.write(""); st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_data.clear(); st.rerun()

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", options=(raw_data.get("doi", []) if isinstance(raw_data, dict) else []), index=None)
    diem_giao_lap = st.selectbox("DIEM GIAO HANG & LAP DAT *", options=(raw_data.get("danh_sach_diem", []) if isinstance(raw_data, dict) else []), index=None)
    
    if du_an_chon and doi_thuc_hien and diem_giao_lap:
        p_code = str(du_an_chon).replace('\xa0', ' ').strip().upper()
        d_doi = str(doi_thuc_hien).replace('\xa0', ' ').strip().upper()
        d_diem = str(diem_giao_lap).replace('\xa0', ' ').strip().upper()
        
        # Hút dữ liệu từ cả 2 kho Lắp Đặt và Vận Chuyển
        data_ld = raw_data.get("KHO_LAP_DAT", []) if isinstance(raw_data, dict) else []
        data_vc = raw_data.get("KHO_VAN_CHUYEN", []) if isinstance(raw_data, dict) else []
        
        ds_hang_raw = quet_mat_than(data_ld, p_code, d_doi, d_diem) + quet_mat_than(data_vc, p_code, d_doi, d_diem)
        
        # Lọc trùng lặp để phòng hờ anh nhập trùng bên 2 sheet
        ds_hang = []
        seen = set()
        for item in ds_hang_raw:
            key = f"{item['sku']}_{item['ten']}_{item['sl']}"
            if key not in seen:
                seen.add(key)
                ds_hang.append(item)

        st.markdown("### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ")
        if ds_hang:
            tb_md = "| Mã CV / SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(tb_md)
            st.success(f"Đã ánh xạ thành công {len(ds_hang)} thiết bị!")
        else:
            st.warning("Không tìm thấy hàng hóa phân bổ cho dự án, đội và địa điểm này.")

    else: st.info("Vui lòng chọn đầy đủ Dự án, Tên đội và Địa điểm.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    st.markdown("---")
    st.markdown("### 📍 CHECK-IN TỌA ĐỘ GPS (CHÍNH XÁC CAO)")
    loc = streamlit_geolocation()
    gps_link = ""
    if loc and loc.get('latitude'):
        lat = loc['latitude']; lon = loc['longitude']
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"
        st.success("✅ Đã chốt tọa độ thành công!")
        st.markdown(f"[📍 Mở kiểm tra vị trí vừa lấy trên bản đồ]({gps_link})")
        
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("ĐÃ GIAO XONG (VC)", type="primary", use_container_width=True):
            if submit_to_google(p_code if du_an_chon else "", doi_thuc_hien, "", diem_giao_lap, ds_hang, gps_link, "Đã giao hàng"): st.success("Gửi báo cáo thành công!")
    with col_b2:
        if st.button("ĐÃ LẮP XONG (LĐ)", type="primary", use_container_width=True):
            if submit_to_google(p_code if du_an_chon else "", doi_thuc_hien, diem_giao_lap, "", ds_hang, gps_link, "Đã lắp đặt"): st.success("Gửi báo cáo thành công!")
    with col_b3:
        if st.button("ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if submit_to_google(p_code if du_an_chon else "", doi_thuc_hien, diem_giao_lap, diem_giao_lap, ds_hang, gps_link, "Giao và Lắp xong"): st.success("Gửi báo cáo thành công!")

elif st.session_state.nav_tab in ["Admin", "Link"]:
    st.markdown("### KHU VỰC QUẢN TRỊ & LINK BÁO CÁO")
    pass_input = st.text_input("Nhập mật khẩu (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("Xác thực thành công!")
        if st.session_state.nav_tab == "Link":
            st.markdown("- [Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
