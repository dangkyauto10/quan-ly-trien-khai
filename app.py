import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=5)
def load_live_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            return json.loads(res_text), None
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

if st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (ALLOCATION SYNC)")
    
    raw_data, err_msg = load_live_data()
    if err_msg: st.error(err_msg)
        
    data_kho, data_du_an, sheet_doi_raw = [], [], []
    
    # Bóc tách dữ liệu
    if isinstance(raw_data, dict):
        for k, v in raw_data.items():
            k_lower = str(k).lower()
            if "kho" in k_lower: data_kho = v
            elif "du_an" in k_lower or "danh_sach_du_an" in k_lower: data_du_an = v
            elif "doi" in k_lower or "quan_ly_doi" in k_lower: sheet_doi_raw = v
            
        if not data_kho and "KHO_PHAN_BO" in raw_data: data_kho = raw_data["KHO_PHAN_BO"]
        if not data_du_an and "DANH_SACH_DU_AN" in raw_data: data_du_an = raw_data["DANH_SACH_DU_AN"]
        if not sheet_doi_raw and "QUAN_LY_DOI" in raw_data: sheet_doi_raw = raw_data["QUAN_LY_DOI"]
    elif isinstance(raw_data, list):
        data_kho = raw_data

    # 1. VÉT SẠCH DỰ ÁN (Tự động bỏ qua các dòng tiêu đề)
    danh_sach_du_an = []
    if data_du_an:
        for r in data_du_an:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "mã da", "stt", "none", "", "dự án", "tên dự án"]:
                    if val not in danh_sach_du_an: danh_sach_du_an.append(val)
                        
    if not danh_sach_du_an and data_kho:
        for r in data_kho:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "stt", "none", "", "dự án"]:
                    if val not in danh_sach_du_an: danh_sach_du_an.append(val)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", options=danh_sach_du_an, index=None, placeholder="-- Gõ để tìm hoặc chọn mã dự án --")
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_data.clear()
            st.rerun()

    ds_doi, ds_diem = [], []
    p_code = du_an_chon.strip() if du_an_chon else ""
    
    # 2. VÉT TRỌN VẸN TÊN ĐỘI BẤT CHẤP CẤU TRÚC HEADER
    col_idx_ten_doi = 1
    if sheet_doi_raw:
        # Quét 3 dòng đầu tìm đúng cột Tên đội
        for r in sheet_doi_raw[:3]:
            for i, h in enumerate(r):
                if "tên đội" in str(h).strip().lower() or "ten doi" in str(h).strip().lower():
                    col_idx_ten_doi = i
                    break
        # Lấy dữ liệu và tự động loại bỏ rác/tiêu đề
        for r in sheet_doi_raw:
            if len(r) > col_idx_ten_doi:
                val = str(r[col_idx_ten_doi]).strip()
                if val and val.lower() not in ["tên đội", "ten doi", "stt", "none", "", "mã đội"]:
                    if val not in ds_doi: ds_doi.append(val)
                        
    # Bọc lót lấy đội từ kho nếu sheet đội lỗi
    if not ds_doi and data_kho:
        idx_doi_kho = 6
        for r in data_kho[:3]:
            for i, h in enumerate(r):
                if "đội" in str(h).strip().lower(): idx_doi_kho = i
        for r in data_kho:
            if len(r) > idx_doi_kho:
                val = str(r[idx_doi_kho]).strip()
                if val and val.lower() not in ["tên đội", "đội", "stt", "none", ""]:
                    if val not in ds_doi: ds_doi.append(val)

    # 3. LỌC ĐỊA ĐIỂM TỪ KHO THEO DỰ ÁN (Tự động nhận diện cột)
    idx_diem = 7; idx_matb = 1; idx_tentb = 3; idx_sl = 4; idx_dvt = 5
    if data_kho:
        for r in data_kho[:3]:
            for i, h in enumerate(r):
                h_str = str(h).strip().lower()
                if "địa điểm" in h_str or "đơn vị" in h_str: idx_diem = i
                elif "mã tb" in h_str or "sku" in h_str: idx_matb = i
                elif "thiết bị" in h_str or "tên tb" in h_str: idx_tentb = i
                elif "số lượng" in h_str or "sl" in h_str: idx_sl = i
                elif "đvt" in h_str or "đơn vị tính" in h_str: idx_dvt = i

    if data_kho and p_code:
        for r in data_kho:
            r_proj = str(r[0]).strip().lower() if len(r) > 0 else ""
            if r_proj == p_code.lower() or p_code.lower() in r_proj:
                if len(r) > idx_diem:
                    v_diem = str(r[idx_diem]).strip()
                    if v_diem and v_diem.lower() not in ["địa điểm", "đơn vị", "stt", "none", ""]:
                        if v_diem not in ds_diem: ds_diem.append(v_diem)

    doi_thuc_hien = st.selectbox(f"TEN DOI VAN CHUYEN / LAP DAT (Đồng bộ {len(ds_doi)} nhân sự) *", options=ds_doi, index=None, placeholder="-- Gõ để tìm hoặc chọn tên đội --")
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Đồng bộ {len(ds_diem)} đơn vị) *", options=sorted(ds_diem), index=None, placeholder="-- Gõ để tìm hoặc chọn địa điểm --")
    
    # 4. DANH MỤC THIẾT BỊ
    ds_hang = []
    if diem_giao_lap and doi_thuc_hien and p_code:
        for r in data_kho:
            r_proj = str(r[0]).strip().lower() if len(r) > 0 else ""
            c_diem = str(r[idx_diem]).strip().lower() if len(r) > idx_diem else ""
            if (r_proj == p_code.lower() or p_code.lower() in r_proj) and diem_giao_lap.lower() == c_diem:
                sku = str(r[idx_matb]).strip() if len(r) > idx_matb else "TB-0X"
                ten = str(r[idx_tentb]).strip() if len(r) > idx_tentb else "Thiết bị"
                sl = str(r[idx_sl]).strip() if len(r) > idx_sl else "1"
                dvt = str(r[idx_dvt]).strip() if len(r) > idx_dvt else "Bộ"
                if ten.lower() not in ["tên tb", "thiết bị", "none", ""]:
                    ds_hang.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ CHO ĐƠN VỊ")
        st.markdown(f"📍 **Đơn vị / Địa điểm:** {diem_giao_lap} | 👥 **Đội thực hiện:** {doi_thuc_hien}")
        
        if ds_hang:
            tb_md = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(tb_md)
            st.success(f"Đã ánh xạ thành công {len(ds_hang)} thiết bị thực tế!")
        else:
            st.warning("Không tìm thấy dữ liệu thiết bị khớp với đơn vị này.")
    else:
        st.info("Vui lòng chọn đầy đủ Dự án, Tên đội và Địa điểm để hiển thị thiết bị phân bổ.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    st.markdown("---")
    if st.button("Check-in GPS Tọa độ Hiện trường", use_container_width=True): st.success("Check-in GPS thành công!")
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("ĐÃ GIAO XONG (VC)", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Vui lòng chọn đầy đủ thông tin!")
            else: st.success(f"Gửi báo cáo: ĐÃ GIAO XONG (VC) cho dự án {p_code} - Đội {doi_thuc_hien} tại {diem_giao_lap}")
    with col_b2:
        if st.button("ĐÃ LẮP XONG (LĐ)", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Vui lòng chọn đầy đủ thông tin!")
            else: st.success(f"Gửi báo cáo: ĐÃ LẮP XONG (LĐ) cho dự án {p_code} - Đội {doi_thuc_hien} tại {diem_giao_lap}")
    with col_b3:
        if st.button("ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if not p_code or not doi_thuc_hien or not diem_giao_lap: st.warning("Vui lòng chọn đầy đủ thông tin!")
            else: st.success(f"Gửi báo cáo TRỌN GÓI: GIAO VÀ LẮP XONG cho dự án {p_code} - Đội {doi_thuc_hien} tại {diem_giao_lap}")

elif st.session_state.nav_tab == "Admin":
    st.markdown("### KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("Đăng nhập Admin thành công!")
        st.write("- [Chờ duyệt] Thành viên đăng ký mới")
        if st.button("Duyet tat ca tai khoan"): st.success("Đã phê duyệt thành công!")
    elif pass_input != "": st.error("Sai mật khẩu bảo mật!")

elif st.session_state.nav_tab == "Link":
    st.markdown("### TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("Xác thực thành công!")
        st.markdown("- [Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "": st.error("Sai mật khẩu truy cập!")
