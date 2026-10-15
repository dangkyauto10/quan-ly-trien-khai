import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
from streamlit_geolocation import streamlit_geolocation
from PIL import Image
import io

st.set_page_config(page_title="QUẢN LÝ DỰ ÁN", page_icon="🚀", layout="centered")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 600px; }
    .stButton>button { border-radius: 12px; font-weight: 700 !important; font-size: 15px !important; height: 50px !important; color: white !important; background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); border: none; }
    div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); }
    </style>
""", unsafe_allow_html=True)

SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwp2Pq3-PYNvHOWe4IQVm5PqeJd5TcIc_mPDtLm0BkDEGYUxq-C1cnV3rNS1X3xfI1p7w/exec"
IMGBB_API_KEY = "70e3f4a06020949c79c82ca5dea96b02"

def compress_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB': img = img.convert('RGB')
        img.thumbnail((800, 800))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=50)
        return base64.b64encode(output.getvalue()).decode('utf-8')
    except: return None

def upload_to_imgbb(b64_str):
    try:
        url = "https://api.imgbb.com/1/upload"
        data = urllib.parse.urlencode({'key': IMGBB_API_KEY, 'image': b64_str}).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get("success"): return res["data"]["url"]
        return None
    except: return None

def fetch_api_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response: return json.loads(response.read().decode('utf-8')), None
    except Exception as e: return None, str(e)

def submit_to_google(ma_da, ten_doi, diem_lap, diem_giao, ds_hang, gps, tinh_trang, image_files):
    img_urls = []
    if image_files:
        for f in image_files:
            b64 = compress_image(f)
            if b64:
                link = upload_to_imgbb(b64)
                if link: img_urls.append(link)
                
    payload = {
        "action": "bao_cao", "ma_du_an": ma_da, "ten_doi": ten_doi, 
        "diem_lap_dat": diem_lap, "diem_giao_hang": diem_giao, 
        "ds_hang_hoa": ds_hang, "link_maps": gps, "tinh_trang": tinh_trang, 
        "image_urls": img_urls
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response: return json.loads(response.read().decode('utf-8')).get("status") == "success", ""
    except Exception as e: return False, str(e)

def quet_mat_than(data_sheet, p_code, d_doi, d_diem):
    ds_kq = []
    if not data_sheet: return ds_kq
    idx_proj = -1; idx_matb = -1; idx_doi = -1; idx_tentb = -1; idx_sl = -1; idx_diem = -1; idx_dvt = -1
    header_row_index = -1
    for r_idx, r in enumerate(data_sheet[:10]):
        row_str = " ".join([str(x).upper() for x in r])
        if "MÃ CÔNG VIỆC" in row_str or "MÃ DA" in row_str or "TÊN THIẾT BỊ" in row_str:
            header_row_index = r_idx
            for i, h in enumerate(r):
                h_str = str(h).replace('\xa0', ' ').strip().upper() 
                if "MÃ DỰ ÁN" in h_str or "MÃ DA" in h_str: idx_proj = i
                elif "ĐỊA ĐIỂM" in h_str or "ĐIỂM GIAO" in h_str or "ĐƠN VỊ" in h_str: idx_diem = i
                elif "SKU" in h_str or "MÃ CÔNG VIỆC" in h_str: idx_matb = i
                elif "TÊN THIẾT BỊ" in h_str or "HÀNG HÓA" in h_str: idx_tentb = i
                elif "SỐ LƯỢNG" in h_str or "SL" in h_str: idx_sl = i
                elif "ĐƠN VỊ TÍNH" in h_str or "ĐVT" in h_str: idx_dvt = i
                elif "ĐỘI" in h_str or "NHÂN SỰ" in h_str: idx_doi = i
            break 
    if idx_proj == -1 or idx_diem == -1 or idx_doi == -1 or header_row_index == -1: return ds_kq
    p_c = str(p_code).replace('\xa0', ' ').strip().upper(); d_d = str(d_diem).replace('\xa0', ' ').strip().upper(); d_o = str(d_doi).replace('\xa0', ' ').strip().upper()
    for r in data_sheet[header_row_index + 1:]:
        if len(r) > max(idx_proj, idx_diem, idx_doi):
            c_proj = str(r[idx_proj]).replace('\xa0', ' ').strip().upper(); c_diem = str(r[idx_diem]).replace('\xa0', ' ').strip().upper(); c_doi = str(r[idx_doi]).replace('\xa0', ' ').strip().upper()
            if p_c in c_proj and (d_d in c_diem or (c_diem != "" and c_diem in d_d)) and (d_o in c_doi or (c_doi != "" and c_doi in d_o)):
                sku = str(r[idx_matb]).strip() if (idx_matb > -1 and len(r) > idx_matb) else "TB"
                ten = str(r[idx_tentb]).strip() if (idx_tentb > -1 and len(r) > idx_tentb) else "Thiết bị"
                if ten and str(ten).upper() not in ["NONE", ""]: ds_kq.append({"sku": sku, "ten": ten, "sl": str(r[idx_sl]).strip() if idx_sl > -1 else "1", "dvt": str(r[idx_dvt]).strip() if idx_dvt > -1 else "Bộ"})
    return ds_kq

title_placeholder = st.empty()
title_placeholder.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 900;'>🚀 QUẢN LÝ DỰ ÁN</h2>", unsafe_allow_html=True)

with st.spinner("Đang tải dữ liệu..."):
    raw_data, err_msg = fetch_api_data()

if err_msg:
    st.error("Lỗi dữ liệu: " + err_msg)
else:
    data_ld = raw_data.get("KHO_LAP_DAT", []) if isinstance(raw_data, dict) else []
    data_vc = raw_data.get("KHO_VAN_CHUYEN", []) if isinstance(raw_data, dict) else []
    
    ds_du_an_sach = [str(x).strip() for x in raw_data.get("du_an", []) if str(x).strip() != "" and str(x).strip().upper() not in ["MÃ DỰ ÁN", "TÊN DỰ ÁN", "DỰ ÁN", "NONE"]]
    ds_doi_sach = [str(x).strip() for x in raw_data.get("doi", []) if str(x).strip() != "" and str(x).strip().upper() not in ["MÃ ĐỘI", "TÊN ĐỘI", "ĐỘI", "NONE"]]
    ds_diem_sach = [str(x).strip() for x in raw_data.get("danh_sach_diem", []) if str(x).strip() != "" and str(x).strip().upper() not in ["MÃ ĐIỂM", "ĐỊA ĐIỂM", "ĐIỂM", "NONE"]]

    du_an_chon = st.selectbox("DỰ ÁN TRIỂN KHAI *", options=ds_du_an_sach, index=None)
    doi_thuc_hien = st.selectbox("TÊN ĐỘI THỰC HIỆN *", options=ds_doi_sach, index=None)
    diem_giao_lap = st.selectbox("📍 ĐỊA ĐIỂM GIAO LẮP *", options=ds_diem_sach, index=None)
    
    if du_an_chon and doi_thuc_hien and diem_giao_lap:
        ds_hang = []
        seen = set()
        for item in quet_mat_than(data_ld, du_an_chon, doi_thuc_hien, diem_giao_lap) + quet_mat_than(data_vc, du_an_chon, doi_thuc_hien, diem_giao_lap):
            key = f"{item['sku']}_{item['ten']}_{item['sl']}"
            if key not in seen:
                seen.add(key)
                ds_hang.append(item)

        st.markdown("##### THIẾT BỊ CẦN BÁO CÁO")
        if ds_hang:
            tb_md = "| SKU | Thiết bị | SL | ĐVT |\n| :--- | :--- | :---: | :---: |\n"
            for item in ds_hang: tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(tb_md)

        st.markdown("##### CHỤP ẢNH HIỆN TRƯỜNG")
        img_captured_list = st.file_uploader("📸 Chọn ảnh", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True)
        
        st.markdown("##### CHỐT TỌA ĐỘ GPS")
        loc = streamlit_geolocation()
        gps_link = f"https://www.google.com/maps?q={loc['latitude']},{loc['longitude']}" if loc and loc.get('latitude') else ""

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✅ BÁO CÁO NHANH", type="primary", use_container_width=True):
                if not gps_link: st.error("❌ Bấm GPS trước!")
                elif not img_captured_list: st.error("❌ Chọn Ảnh trước!")
                else:
                    with st.spinner("Đang bắn dữ liệu siêu tốc..."):
                        is_ok, msg = submit_to_google(du_an_chon, doi_thuc_hien, diem_giao_lap, diem_giao_lap, ds_hang, gps_link, "Hoàn thành", img_captured_list)
                        if is_ok: st.success("🎉 XONG! (Tốc độ bàn thờ)")
                        else: st.error(msg)
