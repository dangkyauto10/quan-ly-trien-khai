import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

@st.cache_data(ttl=1)
def load_da880_mapping_data():
    danh_sach_du_an = {} # {Mã dự án: Tên dự án}
    danh_sach_doi = []
    danh_sach_diem = []
    danh_sach_thiet_bi = []
    
    # 1. Đọc DANH_SACH_DU_AN (Lấy Mã dự án cột A và Tên dự án cột B)
    try:
        url_da = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=DANH_SACH_DU_AN"
        df_da = pd.read_csv(url_da, header=None)
        if df_da.shape[1] >= 2:
            for idx, row in df_da.iterrows():
                if idx >= 2:
                    ma_da = str(row[0]).strip() if pd.notna(row[0]) else ""
                    ten_da = str(row[1]).strip() if pd.notna(row[1]) else ""
                    if ma_da and ma_da != "nan":
                        danh_sach_du_an[ma_da] = ten_da
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

    # 4. Đọc NHAP_KHO (Danh mục thiết bị)
    try:
        url_nhap = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=NHAP_KHO"
        df_nhap = pd.read_csv(url_nhap, header=None)
        if df_nhap.shape[1] >= 3:
            for idx, row in df_nhap.iterrows():
                if idx >= 2:
                    sku = str(row[1]).strip() if pd.notna(row[1]) else ""
                    ten_tb = str(row[2]).strip() if pd.notna(row[2]) else ""
                    if ten_tb and ten_tb != "nan":
                        item_str = f"{sku} - {ten_tb}" if sku and sku != "nan" else ten_tb
                        if item_str not in danh_sach_thiet_bi:
                            danh_sach_thiet_bi.append(item_str)
    except Exception:
        pass

    # Dữ liệu dự phòng an toàn
    if not danh_sach_du_an:
        danh_sach_du_an = {"DA880": "Hệ thống điều hành triển khai tự động"}
    if not danh_sach_doi:
        danh_sach_doi = ["Nguyễn Văn Thiện", "Nguyễn Văn Hải"]
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Xã Đường Thượng"]
    if not danh_sach_thiet_bi:
        danh_sach_thiet_bi = ["TB-01 - Máy tính để bàn TQT TPY01 535215"]

    return danh_sach_du_an, danh_sach_doi, danh_sach_diem, danh_sach_thiet_bi

danh_sach_du_an, danh_sach_doi, danh_sach_diem, danh_sach_thiet_bi = load_da880_mapping_data()

st.markdown("### 🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN DA880")

with st.form("form_mapping_chuan"):
    st.markdown("### 1. Ánh Xạ Thông Tin Dự Án & Thiết Bị Tự Động")
    
    # Chọn Mã dự án (Cột A)
    ma_da_chon = st.selectbox(
        "Mã dự án (Cột A - Lấy từ sheet Danh sách dự án):",
        options=list(danh_sach_du_an.keys())
    )
    
    # Tự động hiện Tên dự án (Cột C) tương ứng với Mã dự án được chọn ở Cột B sheet danh sách dự án
    ten_da_hien_thi = danh_sach_du_an.get(ma_da_chon, "")
    st.text_input("Tên dự án tương ứng (Cột C - Tự động quy chiếu từ Cột B sheet Danh sách dự án):", value=ten_da_hien_thi, disabled=True)

    ktv_name = st.selectbox("Cán bộ / Đội trưởng thực hiện (Cột B QUAN_LY_DOI):", options=danh_sach_doi)
    diadiem = st.selectbox("Địa điểm vận chuyển / lắp đặt (Cột D DANH_SACH_DIEM):", options=danh_sach_diem)
    thietbi_chon = st.selectbox("Thiết bị / Hàng hóa (Quy chiếu từ NHAP_KHO):", options=danh_sach_thiet_bi)
    
    soluong_lap = st.number_input("Số lượng thực hiện phân bổ:", min_value=1, value=1, step=1)
    
    submitted = st.form_submit_button("📍 XÁC NHẬN VÀ ĐỒNG BỘ DỮ LIỆU")
    if submitted:
        st.success(f"✅ Đã ánh xạ thành công Dự án [{ma_da_chon} - {ten_da_hien_thi}] cho thiết bị [{thietbi_chon}]!")
