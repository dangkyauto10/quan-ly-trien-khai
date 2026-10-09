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

    doi_label = "TEN DOI VAN CHUYEN / LAP DAT (Đồng bộ " + str(len(ds_doi)) + " nhân sự) *"
    doi_thuc_hien = st.selectbox(doi_label, options=ds_doi, index=None, placeholder="-- Gõ để tìm hoặc chọn tên đội --")

    idx_diem, idx_matb, idx_tentb, idx_sl, idx_dvt = 7, 1, 3, 4, 5
    ds_diem = []
    
    if data_kho:
        for r in data_kho:
            if len(r) > idx_diem:
                v_diem = str(r[idx_diem]).strip()
                if v_diem and v_diem.upper() not in ["ĐỊA ĐIỂM VẬN CHUYỂN LẮP ĐẶT", "ĐỊA ĐIỂM", "ĐƠN VỊ", "STT", "NONE", ""]:
                    r_proj = str(r[0]).strip().upper()
                    if not p_code or p_code in r_proj:
                        if v_diem not in ds_diem: ds_diem.append(v_diem)

    diem_label = "DIEM GIAO HANG & LAP DAT (Đồng bộ " + str(len(ds_diem)) + " đơn vị) *"
    diem_giao_lap = st.selectbox(diem_label, options=sorted(ds_diem), index=None, placeholder="-- Gõ để tìm hoặc chọn địa điểm --")
    
    ds_hang = []
    if diem_giao_lap and doi_thuc_hien and p_code:
        for r in data_kho:
            r_proj = str(r[0]).strip().upper() if len(r) > 0 else ""
            c_diem = str(r[idx_diem]).strip().upper() if len(r) > idx_diem else ""
            
            if p_code in r_proj and diem_giao_lap.upper() == c_diem:
                sku = str(r[idx_matb]).strip() if len(r) > idx_matb else "TB-0X"
                ten = str(r[idx_tentb]).strip() if len(r) > idx_tentb else "Thiết bị"
                sl = str(r[idx_sl]).strip() if len(r) > idx_sl else "1"
                dvt = str(r[idx_dvt]).strip() if len(r) > idx_dvt else "Bộ"
                if ten and ten.upper() not in ["TÊN THIẾT BỊ / HÀNG HÓA", "TÊN TB", "THIẾT BỊ", "NONE", ""]:
                    ds_hang.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})

        st.markdown("### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ CHO ĐƠN VỊ")
        st.markdown(f"📍 **Đơn vị:** {diem_giao_lap} | 👥 **Đội:** {doi_thuc_hien}")
        
        if ds_hang:
            tb_md = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(tb_md)
            st.success(f"Đã ánh xạ thành công {len(ds_hang)} thiết bị thực tế!")
        else:
            st.warning("Không tìm thấy thiết bị khớp. Hãy thử bấm nút 'Làm mới dữ liệu'.")
    else:
        st.info("Vui lòng chọn Dự án, Tên đội và Địa điểm để xem thiết bị.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    
    st.markdown("---")
    st.markdown("### 📍 CHECK-IN TỌA ĐỘ GPS (CHÍNH XÁC CAO)")
    loc = streamlit_geolocation()
    gps_link = ""
    if loc and loc.get('latitude'):
        lat, lon = loc['latitude'], loc['longitude']
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"
        st.success(f"✅ Đã chốt tọa độ thành công! (Lat: {lat}, Lon: {lon})")
        
    st.markdown("---")
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("ĐÃ GIAO XONG (VC)", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Chọn đủ thông tin!")
            elif not gps_link: st.warning("Check-in GPS trước!")
            else:
                if submit_to_google(p_code, doi_thuc_hien, "", diem_giao_lap, ds_hang, gps_link, "Đã giao hàng"): st.success("Gửi báo cáo VC thành công!")
                else: st.error("Gửi thất bại!")
    with col_b2:
        if st.button("ĐÃ LẮP XONG (LĐ)", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Chọn đủ thông tin!")
            elif not gps_link: st.warning("Check-in GPS trước!")
            else:
                if submit_to_google(p_code, doi_thuc_hien, diem_giao_lap, "", ds_hang, gps_link, "Đã lắp đặt"): st.success("Gửi báo cáo LĐ thành công!")
                else: st.error("Gửi thất bại!")
    with col_b3:
        if st.button("ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Chọn đủ thông tin!")
            elif not gps_link: st.warning("Check-in GPS trước!")
            else:
                if submit_to_google(p_code, doi_thuc_hien, diem_giao_lap, diem_giao_lap, ds_hang, gps_link, "Giao và Lắp xong"): st.success("Gửi báo cáo trọn gói thành công!")
                else: st.error("Gửi thất bại!")

elif st.session_state.nav_tab == "Admin":
    st.markdown("### KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu (Mã PIN):", type="password")
    if pass_input == SECURE_PASS: st.success("Thành công!")
    elif pass_input != "": st.error("Sai mật khẩu!")

elif st.session_state.nav_tab == "Link":
    st.markdown("### TRANG THEO DÕI TIẾN ĐỘ")
    pass_link = st.text_input("Nhập mật khẩu (Mã PIN):", type="password")
    if pass_link == SECURE_PASS: st.success("Xác thực thành công!")
    elif pass_link != "": st.error("Sai mật khẩu!")
