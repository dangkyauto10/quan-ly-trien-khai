import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=2)
def load_live_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            data = json.loads(res_text)
            return data, None
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
    if err_msg:
        st.error(err_msg)
        
    data_kho = []
    data_du_an = []
    sheet_doi_raw = []
    
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
        
    rows_kho = data_kho[2:] if len(data_kho) > 2 else (data_kho[1:] if len(data_kho) > 1 else [])
    
    # 1. VÉT SẠCH CỘT A TỪ SHEET "DANH_SACH_DU_AN"
    danh_sach_du_an = []
    if data_du_an:
        for r in data_du_an:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "mã da", "stt", "none", "", "dự án"]:
                    if val not in danh_sach_du_an:
                        danh_sach_du_an.append(val)
                        
    if not danh_sach_du_an and rows_kho:
        for r in rows_kho:
            if len(r) > 0:
                val = str(r[0]).strip()
                if val and val.lower() not in ["mã dự án", "stt", "none", ""]:
                    if val not in danh_sach_du
