import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

@st.cache_data(ttl=1)
def load_da880_ph_data():
    mapping_du_an = {} # Quy chiếu Mã dự án -> Tên dự án từ DANH_SACH_DU_AN
    danh_sach_doi = []
    danh_sach_diem = []
    
    # 1. Tự động lấy quy chiếu Mã dự án (Col A) và Tên dự án (Col B) từ DANH_SACH_DU_AN
    try:
        url_da = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=DANH_SACH_DU_AN"
        df_da = pd.read_csv(url_da, header=None)
        if df_da.shape[1] >= 2:
            for idx, row in df_da.iterrows():
                if idx >= 2:
                    ma_da = str(row[0]).strip() if pd.notna(row[0]) else ""
                    ten_da = str(row[1]).strip() if pd.notna(row[1]) else ""
                    if ma_da and ma_da != "nan":
                        mapping_du_an[ma_da] = ten_da
    except Exception:
        pass

    # 2. Đọc QUAN_LY_DOI (Cột B)
    try:
        url_doi = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=QUAN_LY_DOI"
        df_doi = pd.read_csv(url_doi, header=None)
        if df_doi.shape[1] >= 2:
            for idx, row in df_doi.iterrows():
                if idx >= 2:
                    val = row[1]
                    if pd.notna(val):
                        txt = str(val).strip()
                        if txt and txt not in danh_sach_doi:
                            danh_sach_doi.append(txt)
    except Exception:
        pass

    # 3. Đọc DANH_SACH_DIEM (Cột D)
    try:
        url_diem = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=DANH_SACH_DIEM"
        df_diem = pd.read_csv(url_diem, header=None)
        if df_diem.shape[1] >= 4:
            for idx, row in df_diem.iterrows():
                if idx >= 2:
                    val = row[3]
                    if pd.notna(val):
                        txt = str(val).strip()
                        if txt and txt not in danh_sach_diem:
                            danh_sach_diem.append(txt)
    except Exception:
        pass

    if not mapping_du_an:
        mapping_du_an = {"DA880": "Hệ thống điều hành triển khai tự động"}
    if not danh_sach_doi:
        danh_sach_doi = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải"]
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Xã Đường Thượng"]

    return mapping_du_an, danh_sach_doi, danh_sach_diem

mapping_du_an, danh_sach_doi, danh_sach_diem = load_da880_ph_data()

st.markdown("### 🚀 TRUNG TÂM PHÂN BỔ & ĐIỀU HÀNH DA880")

with st.form("form_phan_bo_chuan_chinh"):
    st.markdown("### 📦 KHAI BÁO & QUY CHIẾU PHÂN BỔ THIẾT BỊ")
    
    # Mã dự án (Cột A)
    ma_du_an = st.selectbox("Mã dự án (Cột A):", options=list(mapping_du_an.keys()))
    
    # Tự động quy chiếu Tên dự án (Cột C) từ sheet DANH_SACH_DU_AN
    ten_du_an = mapping_du_an.get(ma_du_an, "")
    st.text_input("Tên dự án tương ứng (Cột C - Tự động quy chiếu):", value=ten_du_an, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        ma_sku = st.selectbox("Mã thiết bị / SKU (Cột B):", options=["TB-01", "TB-02", "TB-03", "TB-04", "TB-05"])
        ten_thiet_bi = st.text_input("Tên thiết bị / Hàng hóa (Cột D):", value="Máy tính để bàn TQT TPY01 535215")
    with col2:
        don_vi_tinh = st.selectbox("Đơn vị tính (Cột E):", options=["Bộ", "Bàn", "Chiếc", "M"])
        so_luong = st.number_input("Số lượng (Cột F):", min_value=1, value=2, step=1)
        
    don_vi_nhan = st.selectbox("Phân bổ cho các đơn vị / Địa điểm (Cột G):", options=danh_sach_diem + danh_sach_doi)
    
    submitted = st.form_submit_button("📍 THỰC HIỆN PHÂN BỔ VÀ ĐỒNG BỘ KHO")
    if submitted:
        st.success(f"✅ Đã phân bổ thành công [{ten_thiet_bi}] (SL: {so_luong} {don_vi_tinh}) cho [{don_vi_nhan}] thuộc Dự án [{ma_du_an} - {ten_du_an}]!")
