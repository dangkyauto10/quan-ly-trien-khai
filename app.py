import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"

# CHỈ DÙNG 1 ĐƯỜNG DẪN APPS SCRIPT DUY NHẤT (ĐÃ CẮT BỎ ĐƯỜNG LINK CSV GÂY LỖI 404)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=10)
def load_live_data_from_script():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
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

if st.session_state.nav_tab == "Bao_cao":
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (ALLOCATION SYNC)")
    
    raw_data, err_msg = load_live_data_from_script()
    if err_msg:
        st.error(err_msg)
        
    data_kho = []
    data_du_an = []
    
    if raw_data:
        if isinstance(raw_data, list):
            data_kho = raw_data
        elif isinstance(raw_data, dict):
            data_kho = raw_data.get("KHO_PHAN_BO", [])
            data_du_an = raw_data.get("DANH_SACH_DU_AN", [])
            
    rows_kho_data = data_kho[1:] if len(data_kho) > 1 else []
    
    # 1. TÌM DANH SÁCH DỰ ÁN ĐỂ HIỂN THỊ CỘT A
    danh_sach_du_an = []
    
    # Ưu tiên lấy từ sheet DANH_SACH_DU_AN nếu Apps Script đã xuất
    if data_du_an and len(data_du_an) > 1:
        for r in data_du_an[1:]:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "mã da", "stt", ""] and val not in danh_sach_du_an:
                    danh_sach_du_an.append(val)
                    
    # Nếu chưa có, quét lấy Cột A từ KHO_PHAN_BO
    if not danh_sach_du_an and rows_kho_data:
        for r in rows_kho_data:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "stt", ""] and val not in danh_sach_du_an:
                    danh_sach_du_an.append(val)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        if not danh_sach_du_an:
            du_an_chon = st.selectbox(
                "CHON DU AN TRIEN KHAI *", 
                options=[],
                index=None,
                placeholder="-- Đang chờ kết nối dữ liệu Dự Án --"
            )
        else:
            du_an_chon = st.selectbox(
                "CHON DU AN TRIEN KHAI *", 
                options=danh_sach_du_an,
                index=0 
            )
            
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_data.clear()
            st.rerun()

    danh_sach_doi = []
    danh_sach_diem = []
    project_code = du_an_chon.strip() if du_an_chon else ""
    
    if rows_kho_data and project_code:
        headers_kho = [str(x).strip().lower() for x in data_kho[0]]
        
        def find_col_kho(kws, default_i):
            for i, h in enumerate(headers_kho):
                if any(kw in h for kw in kws): return i
            return default_i

        idx_doi_kho = find_col_kho(["đội"], 6)
        idx_diem_kho = find_col_kho(["địa điểm", "đơn vị"], 7)
        idx_matb_kho = find_col_kho(["mã tb", "sku"], 1)
        idx_tentb_kho = find_col_kho(["thiết bị", "hàng hóa", "tên tb"], 3)
        idx_sl_kho = find_col_kho(["số lượng", "sl"], 4)
        idx_dvt_kho = find_col_kho(["đvt", "đơn vị tính"], 5)

        for r in rows_kho_data:
            row_proj = str(r[0]).strip() if len(r) > 0 else ""
            if row_proj.lower() == project_code.lower() or project_code.lower() in row_proj.lower():
                if len(r) > idx_doi_kho and str(r[idx_doi_kho]).strip():
                    val_doi = str(r[idx_doi_kho]).strip()
                    if val_doi.lower() not in ["tên đội", "stt", ""] and val_doi not in danh_sach_doi:
                        danh_sach_doi.append(val_doi)
                        
                if len(r) > idx_diem_kho and str(r[idx_diem_kho]).strip():
                    val_diem = str(r[idx_diem_kho]).strip()
                    if val_diem.lower() not in ["địa điểm vận chuyển lắp đặt", "địa điểm", "stt", ""] and val_diem not in danh_sach_diem:
                        danh_sach_diem.append(val_diem)

    # 2. HIỂN THỊ Ô TÌM KIẾM THÔNG MINH (Không cần xóa chữ)
    ui_danh_sach_doi = sorted(danh_sach_doi)
    ui_danh_sach_diem = sorted(danh_sach_diem)

    doi_thuc_hien = st.selectbox(
        "TEN DOI VAN CHUYEN / LAP DAT *", 
        options=ui_danh_sach_doi,
        index=None,
        placeholder="-- Gõ để tìm hoặc chọn tên đội --"
    )
    
    diem_giao_lap = st.selectbox(
        f"DIEM GIAO HANG & LAP DAT (Đồng bộ {len(danh_sach_diem)} đơn vị) *", 
        options=ui_danh_sach_diem,
        index=None,
        placeholder="-- Gõ để tìm hoặc chọn địa điểm --"
    )
    
    # 3. LỌC DANH MỤC THIẾT BỊ
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap is not None and doi_thuc_hien is not None and project_code:
        for r in rows_kho_data:
            row_proj = str(r[0]).strip() if len(r) > 0 else ""
            diem_cell = str(r[idx_diem_kho]).strip() if len(r) > idx_diem_kho else ""
            
            if (row_proj.lower() == project_code.lower() or project_code.lower() in row_proj.lower()) and diem_giao_lap.lower() == diem_cell.lower():
                sku = str(r[idx_matb_kho]).strip() if len(r) > idx_matb_kho else "TB-0X"
                ten_tb = str(r[idx_tentb_kho]).strip() if len
