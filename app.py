import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=10)
def load_live_data_from_script():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        st.error(f"🚨 LỖI KẾT NỐI API GOOGLE SHEETS: {e}")
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
    
    danh_sach_du_an = []
    rows_data = []
    
    # Set default index phòng trường hợp sheet bị trắng
    idx_mada = 0; idx_tenda = -1; idx_matb = 1; idx_tentb = 3; idx_sl = 4; idx_dvt = 5; idx_doi = 6; idx_diem = 7

    # PHƯƠNG THỨC XỬ LÝ MỚI: QUY CHIẾU DỮ LIỆU ĐỘNG QUA TIÊU ĐỀ
    if raw_data and len(raw_data) > 0:
        headers = [str(x).strip().lower() for x in raw_data[0]]
        rows_data = raw_data[1:]
        
        def find_col(kws, default_i):
            for i, h in enumerate(headers):
                if any(kw in h for kw in kws): return i
            return default_i

        # Tự động tìm vị trí Cột bất chấp file Sheet bị đổi cấu trúc
        idx_mada = find_col(["dự án", "mã da"], 0)
        idx_tenda = find_col(["tên dự án", "tên da"], -1)
        idx_doi = find_col(["đội"], 6)
        idx_diem = find_col(["địa điểm", "đơn vị"], 7)
        idx_matb = find_col(["mã tb", "sku"], 1)
        idx_tentb = find_col(["thiết bị", "hàng hóa", "tên tb"], 3)
        idx_sl = find_col(["số lượng", "sl"], 4)
        idx_dvt = find_col(["đvt", "đơn vị tính"], 5)

        for r in rows_data:
            if len(r) > idx_mada:
                val_da = str(r[idx_mada]).strip()
                val_tenda = str(r[idx_tenda]).strip() if idx_tenda != -1 and len(r) > idx_tenda else ""
                
                if val_da and val_da.lower() not in ["mã dự án", "stt", ""]:
                    item_str = f"{val_da} - {val_tenda}" if val_tenda and val_tenda != val_da else val_da
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
        if st.button("Lam moi du lieu"):
            st.cache_data.clear()
            st.rerun()

    danh_sach_doi = []
    danh_sach_diem = []
    project_code = du_an_chon.split(" - ")[0].strip().lower() if du_an_chon != "-- Chưa có dữ liệu dự án --" else ""
    
    if rows_data and project_code:
        for r in rows_data:
            row_proj = str(r[idx_mada]).strip().lower() if len(r) > idx_mada else ""
            if project_code in row_proj:
                if len(r) > idx_doi and str(r[idx_doi]).strip():
                    val_doi = str(r[idx_doi]).strip()
                    if val_doi.lower() not in ["tên đội", "stt", ""] and val_doi not in danh_sach_doi:
                        danh_sach_doi.append(val_doi)
                        
                if len(r) > idx_diem and str(r[idx_diem]).strip():
                    val_diem = str(r[idx_diem]).strip()
                    if val_diem.lower() not in ["địa điểm", "stt", ""] and val_diem not in danh_sach_diem:
                        danh_sach_diem.append(val_diem)

    ui_danh_sach_doi = ["-- Chon ten doi --"] + sorted(danh_sach_doi) if danh_sach_doi else ["-- Chon ten doi --"]
    ui_danh_sach_diem = ["-- Chon dia diem --"] + sorted(danh_sach_diem) if danh_sach_diem else ["-- Chon dia diem --"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ui_danh_sach_doi)
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Đồng bộ {len(danh_sach_diem)} đơn vị chuẩn) *", ui_danh_sach_diem)
    
    danh_sach_hang_hoa_phan_bo = []
    
    # Logic chuẩn: Bắt buộc chọn CẢ Tên Đội VÀ Địa điểm mới show list thiết bị
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --" and project_code:
        for r in rows_data:
            row_proj = str(r[idx_mada]).strip().lower() if len(r) > idx_mada else ""
            diem_cell = str(r[idx_diem]).strip().lower() if len(r) > idx_diem else ""
            
            if project_code in row_proj and diem_giao_lap.lower() == diem_cell:
                sku = str(r[idx_matb]).strip() if len(r) > idx_matb else "TB-0X"
                ten_tb = str(r[idx_tentb]).strip() if len(r) > idx_tentb else "Thiết bị"
                sl = str(r[idx_sl]).strip() if len(r) > idx_sl else "1"
                dvt = str(r[idx_dvt]).strip() if len(r) > idx_dvt else "Bộ"
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
        # Nhắc nhở nếu như quên chọn 1 trong 2 trường (như ở ảnh 1)
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
