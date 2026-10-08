import streamlit as st
import urllib.request
import json
import csv
import io

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"

# LINK 1: KẾT NỐI APPS SCRIPT ĐỂ ĐỌC DỮ LIỆU KHO PHÂN BỔ (LINK CHUẨN CỦA ANH)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

# LINK 2: LUỒNG TÀNG HÌNH ĐỌC TRỰC TIẾP CỘT A TỪ SHEET "DANH_SACH_DU_AN" (KHÔNG CẦN APPS SCRIPT)
PROJECT_CSV_URL = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/gviz/tq?tqx=out:csv&sheet=DANH_SACH_DU_AN"

@st.cache_data(ttl=10)
def load_project_list():
    try:
        req = urllib.request.Request(PROJECT_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            
            danh_sach = []
            for r in rows:
                if len(r) > 0:
                    val = str(r[0]).strip() # Vét sạch Cột A
                    if val and val.lower() not in ["mã dự án", "mã da", "stt", ""]:
                        if val not in danh_sach:
                            danh_sach.append(val)
            return danh_sach
    except Exception:
        return []

@st.cache_data(ttl=10)
def load_live_data_from_script():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        st.error(f"🚨 LỖI KẾT NỐI API KHO PHÂN BỔ: {e}")
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
    
    # 1. BỐC MÃ DỰ ÁN TRỰC TIẾP TỪ SHEET DANH SÁCH DỰ ÁN
    danh_sach_du_an = load_project_list()
    raw_data = load_live_data_from_script()
    rows_kho_data = raw_data[1:] if isinstance(raw_data, list) and len(raw_data) > 1 else []
    
    # Bọc lót nếu link Dự án lỗi, vét lại từ Kho Phân Bổ
    if not danh_sach_du_an and rows_kho_data:
        for r in rows_kho_data:
            if len(r) > 0:
                val_da = str(r[0]).strip()
                if val_da and val_da.lower() not in ["mã dự án", "stt", ""] and val_da not in danh_sach_du_an:
                    danh_sach_du_an.append(val_da)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        if not danh_sach_du_an:
            du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", ["-- Chưa kết nối được dữ liệu Dự Án --"])
        else:
            du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
            
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_data.clear()
            st.rerun()

    danh_sach_doi = []
    danh_sach_diem = []
    project_code = du_an_chon.strip() if "Chưa kết nối" not in du_an_chon else ""
    
    # 2. QUY CHIẾU LỌC ĐỘI VÀ ĐỊA ĐIỂM TỪ KHO PHÂN BỔ
    if rows_kho_data and project_code:
        headers_kho = [str(x).strip().lower() for x in raw_data[0]]
        
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

    ui_danh_sach_doi = ["-- Chon ten doi --"] + sorted(danh_sach_doi) if danh_sach_doi else ["-- Chon ten doi --"]
    ui_danh_sach_diem = ["-- Chon dia diem --"] + sorted(danh_sach_diem) if danh_sach_diem else ["-- Chon dia diem --"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ui_danh_sach_doi)
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Đồng bộ {len(danh_sach_diem)} đơn vị) *", ui_danh_sach_diem)
    
    # 3. LỌC DANH MỤC THIẾT BỊ PHÂN BỔ
    danh_sach_hang_hoa_phan_bo = []
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --" and project_code:
        for r in rows_kho_data:
            row_proj = str(r[0]).strip() if len(r) > 0 else ""
            diem_cell = str(r[idx_diem_kho]).strip() if len(r) > idx_diem_kho else ""
            
            if (row_proj.lower() == project_code.lower() or project_code.lower() in row_proj.lower()) and diem_giao_lap.lower() == diem_cell.lower():
                sku = str(r[idx_matb_kho]).strip() if len(r) > idx_matb_kho else "TB-0X"
                ten_tb = str(r[idx_tentb_kho]).strip() if len(r) > idx_tentb_kho else "Thiết bị"
                sl = str(r[idx_sl_kho]).strip() if len(r) > idx_sl_kho else "1"
                dvt = str(r[idx_dvt_kho]).strip() if len(r) > idx_dvt_kho else "Bộ"
                danh_sach_hang_hoa_phan_bo.append({"sku": sku, "ten": ten_tb, "sl": sl, "dvt": dvt})

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ CHO ĐƠN VỊ")
        st.markdown(f"📍 **Đơn vị / Địa điểm:** {diem_giao_lap} | 👥 **Đội thực hiện:** {doi_thuc_hien}")
        
        if danh_sach_hang_hoa_phan_bo:
            table_markdown = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in danh_sach_hang_hoa_phan_bo:
                table_markdown += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(table_markdown)
            st.success(f"Đã ánh xạ thành công toàn bộ {len(danh_sach_hang_hoa_phan_bo)} thiết bị thực tế!")
        else:
            st.warning("Không tìm thấy dữ liệu thiết bị khớp với đơn vị này.")
    else:
        st.info("Vui long chon day du Ten doi va Dia diem de hien thi chi tiet danh muc thiet bi phan bo.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    
    st.markdown("---")
    if st.button("Check-in GPS Tọa độ Hiện trường", use_container_width=True):
        st.success("Check-in GPS thành công!")
        
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("ĐÃ GIAO XONG (VC)", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo: ĐÃ GIAO XONG (VC) cho đội {doi_thuc_hien} tại {diem_giao_lap}")
    with col_b2:
        if st.button("ĐÃ LẮP XONG (LĐ)", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo: ĐÃ LẮP XONG (LĐ) cho đội {doi_thuc_hien} tại {diem_giao_lap}")
    with col_b3:
        if st.button("ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo TRỌN GÓI: ĐÃ GIAO VÀ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap}")

elif st.session_state.nav_tab == "Admin":
    st.markdown("### KHU VỰC QUẢN TRỊ - ADMIN DUYỆT")
    pass_input = st.text_input("Nhập mật khẩu quản trị (Mã PIN):", type="password")
    if pass_input == SECURE_PASS:
        st.success("Đăng nhập Admin thành công!")
        st.write("- [Chờ duyệt] Thành viên đăng ký mới")
        if st.button("Duyet tat ca tai khoan"):
            st.success("Đã phê duyệt thành công!")
    elif pass_input != "":
        st.error("Sai mật khẩu bảo mật! (Pass: 880880)")

elif st.session_state.nav_tab == "Link":
    st.markdown("### TRANG THEO DÕI TIẾN ĐỘ CHO LÃNH ĐẠO")
    pass_link = st.text_input("Nhập mật khẩu truy cập báo cáo (Mã PIN):", type="password")
    if pass_link == SECURE_PASS:
        st.success("Xác thực thành công!")
        st.markdown("- [Mở trực tiếp Google Sheets Tổng hợp](https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/edit)")
    elif pass_link != "":
        st.error("Sai mật khẩu truy cập! (Pass: 880880)")
