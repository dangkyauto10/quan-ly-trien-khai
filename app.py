import streamlit as st
import urllib.request
import json
import time
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwQV_VqmnnEU3Mu7CDanFGwYnCu56rCOhY9q5emNGasXqwZRJlySd0CaysgNbb8BkjmNA/exec"

def submit_registration(ho_ten, sdt, dia_ban, chuyen_mon, phuong_tien):
    payload = {"action": "dang_ky", "ho_ten": ho_ten, "sdt": sdt, "dia_ban": dia_ban, "chuyen_mon": chuyen_mon, "phuong_tien": phuong_tien}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except:
        return False

def submit_to_google(ma_da, ten_doi, diem_lap, diem_giao, ds_hang, gps, tinh_trang):
    payload = {"action": "bao_cao", "ma_du_an": ma_da, "ten_doi": ten_doi, "diem_lap_dat": diem_lap, "diem_giao_hang": diem_giao, "ds_hang_hoa": ds_hang, "link_maps": gps, "tinh_trang": tinh_trang}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except:
        return False

# HỦY BỎ HOÀN TOÀN CACHE ĐỂ ÉP STREAMLIT LẤY DỮ LIỆU LIVE 100% TỪ GOOGLE SHEETS
def load_live_data():
    try:
        url = f"{APPS_SCRIPT_URL}?t={int(time.time())}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8')), None
    except Exception as e:
        return None, f"🚨 LỖI KẾT NỐI API: {e}"

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
    st.info("Vui lòng điền đầy đủ thông tin bên dưới để gửi yêu cầu tham gia triển khai dự án về hệ thống.")
    with st.form("form_dang_ky_thanh_vien"):
        reg_hoten = st.text_input("Họ và tên *", placeholder="Nhập đầy đủ họ và tên...")
        reg_sdt = st.text_input("Số điện thoại liên hệ *", placeholder="Nhập số điện thoại (Zalo)...")
        reg_diaban = st.text_input("Địa bàn phụ trách", placeholder="Ví dụ: Toàn tuyến dự án")
        reg_chuyenmon = st.selectbox("Chuyên môn / Nhiệm vụ", ["1. Vận chuyển / Giao nhận", "2. KTV Lắp đặt thiết bị", "3. Giám sát / Điều phối chung", "4. Kho vận / Hậu cứ"])
        reg_phuongtien = st.selectbox("Phương tiện di chuyển", ["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        if st.form_submit_button("Gửi Đăng Ký Thành Viên", type="primary", use_container_width=True):
            if not reg_hoten.strip() or not reg_sdt.strip(): st.warning("Vui lòng nhập đủ Họ tên và SĐT!")
            else:
                if submit_registration(reg_hoten, reg_sdt, reg_diaban, reg_chuyenmon, reg_phuongtien): st.success(f"🎉 Đăng ký thành công! Chào mừng {reg_hoten}.")
                else: st.error("Lỗi kết nối!")

elif st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (ALLOCATION SYNC)")
    
    raw_data, err_msg = load_live_data()
    if err_msg: st.error(err_msg)
        
    data_kho = raw_data.get("KHO_PHAN_BO", []) if isinstance(raw_data, dict) else []
    data_du_an = raw_data.get("DANH_SACH_DU_AN", []) if isinstance(raw_data, dict) else []
    sheet_doi_raw = raw_data.get("QUAN_LY_DOI", []) if isinstance(raw_data, dict) else []

    danh_sach_du_an = []
    for r in data_du_an + data_kho:
        if len(r) > 0:
            val = str(r[0]).strip()
            if val and val.upper() not in ["MÃ DỰ ÁN", "MÃ DA", "STT", "NONE", "", "DỰ ÁN", "TÊN DỰ ÁN"]:
                if val not in danh_sach_du_an: danh_sach_du_an.append(val)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1: du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", options=danh_sach_du_an, index=None, placeholder="-- Gõ để tìm hoặc chọn mã dự án --")
    with col_rf2:
        st.write(""); st.write("")
        if st.button("Lam moi du lieu"): st.rerun()

    ds_doi = []
    p_code = du_an_chon.strip().upper() if du_an_chon else ""
    
    for r in sheet_doi_raw + data_kho:
        idx = 1 if r in sheet_doi_raw else 6
        if len(r) > idx:
            val = str(r[idx]).strip()
            if val and val.upper() not in ["TÊN ĐỘI", "TEN DOI", "ĐỘI NHẬN THIẾT BỊ", "STT", "NONE", "", "MÃ ĐỘI"] and val not in ds_doi:
                ds_doi.append(val)

    doi_thuc_hien = st.selectbox(f"TEN DOI
