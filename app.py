import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
# ĐÃ RÁP CHUẨN XÁC LINK APPS SCRIPT WEB APP CỦA DỰ ÁN
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=10)
def load_live_data_from_script():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        st.error(f"🚨 LỖI KẾT NỐI TỚI GOOGLE SHEETS: {e}. Vui lòng kiểm tra lại quyền truy cập hoặc file Sheet.")
        return []

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
    
    raw_data = load_live_data_from_script()
    rows_data = raw_data[1:] if len(raw_data) > 1 else []

    danh_sach_du_an = []
    if rows_data:
        for r in rows_data:
            if len(r) > 0 and str(r[0]).strip():
                ma_da = str(r[0]).strip()
                ten_da = str(r[1]).strip() if len(r) > 1 else ""
                if ma_da.lower() not in ["mã dự án", "stt", ""]:
                    item_str = f"{ma_da} - {ten_da}" if ten_da else ma_da
                    if item_str not in danh_sach_du_an:
                        danh_sach_du_an.append(item_str)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        if not danh_sach_du_an:
            du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", ["-- Chưa có dữ liệu dự án --"])
        else:
            du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
            
    with col_rf2:
        st.write("")
        st.write("")
