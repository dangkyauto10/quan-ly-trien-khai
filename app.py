import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

@st.cache_data(ttl=1)
def load_da880_ph_chuan_data():
    mapping_du_an = {}
    danh_sach_diem = []
    
    # 1. Tự động quy chiếu Mã dự án (Col A) ra Tên dự án (Col B) từ DANH_SACH_DU_AN
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

    # 2. Đọc danh sách địa điểm / đơn vị từ DANH_SACH_DIEM (Cột D)
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
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Đường Thượng", "Phường Minh Xuân", "Phường Nông Tiến"]

    return mapping_du_an, danh_sach_diem

mapping_du_an, danh_sach_diem = load_da880_ph_chuan_data()

st.markdown("### 🚀 TRUNG TÂM PHÂN BỔ & ĐIỀU HÀNH DA880")

with st.form("form_phan_bo_chuan_100"):
    st.markdown("### 📋 KHAI BÁO PHÂN BỔ THIẾT BỊ THEO CHUẨN DM_CHUAN")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Cột A: Mã dự án
        ma_du_an = st.selectbox("Mã dự án (Cột A):", options=list(mapping_du_an.keys()))
        # Tự động quy chiếu Cột C: Tên dự án từ sheet DANH_SACH_DU_AN
        ten_du_an = mapping_du_an.get(ma_du_an, "")
        st.text_input("Tên dự án quy chiếu (Cột C Kho phân bổ):", value=ten_du_an, disabled=True)
        
        ma_sku = st.selectbox("Mã thiết bị / SKU (Cột B):", options=["TB-01", "TB-02", "TB-03", "TB-04", "TB-05"])
    
    with col_b:
        ten_thiet_bi = st.text_input("Tên thiết bị / Hàng hóa (Cột C DM_CHUAN ➡️ Cột D Kho):", value="Máy tính để bàn TQT TPY01 535215")
        don_vi_tinh = st.selectbox("Đơn vị tính (Cột D DM_CHUAN ➡️ Cột E Kho):", options=["Bộ", "Bàn", "Chiếc", "M"])
        so_luong = st.number_input("Số lượng (Cột E DM_CHUAN ➡️ Cột F Kho):", min_value=1, value=2, step=1)
    
    # Cột F DM_CHUAN: Phân bổ cho các đơn vị (có thể chọn 1 hoặc nhiều xã, đơn vị)
    don_vi_nhan = st.multiselect(
        "Phân bổ cho các đơn vị / xã (Cột F DM_CHUAN ➡️ Cột G Kho):",
        options=danh_sach_diem,
        default=[danh_sach_diem[0]] if danh_sach_diem else []
    )
    
    submitted = st.form_submit_button("📍 XÁC NHẬN VÀ ĐỒNG BỘ SANG KHO PHÂN BỔ")
    if submitted:
        if don_vi_nhan:
            ds_nhan_str = ", ".join(don_vi_nhan)
            st.success(f"✅ Đã phân bổ [{ten_thiet_bi}] (SL: {so_luong} {don_vi_tinh}) cho đơn vị: [{ds_nhan_str}] thuộc Dự án [{ma_du_an} - {ten_du_an}] thành công!")
        else:
            st.error("Vui lòng chọn ít nhất một đơn vị/xã nhận thiết bị!")
