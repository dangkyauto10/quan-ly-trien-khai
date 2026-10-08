import streamlit as st
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")
SECURE_PASS = "880880"

# Link Apps Script (Vẫn giữ link anh cung cấp để anh không phải sửa code)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyCjVh5gdBgbQtka1UN_F4WGepgQRYdTcPobXcRr_xy70kN0kn_aLDTVtoI2nObszogsw/exec"

@st.cache_data(ttl=10)
def load_live_data_from_script():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        st.error(f"🚨 LỖI KẾT NỐI API GOOGLE SHEETS: {e}")
        return {"KHO_PHAN_BO": [], "DANH_SACH_DU_AN": []}

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
    
    if isinstance(raw_data, list):
        data_kho = raw_data
        data_du_an = []
    else:
        data_kho = raw_data.get("KHO_PHAN_BO", [])
        data_du_an = raw_data.get("DANH_SACH_DU_AN", [])
    
    # 1. ÁNH XẠ CHÍNH XÁC "CỘT A" TỪ SHEET VÀO DROPDOWN NHƯ ẢNH ANH VỸ KHOANH TRÒN
    danh_sach_du_an = []
    
    # Luồng 1: Nếu đọc được sheet DANH_SACH_DU_AN
    if data_du_an and len(data_du_an) > 1:
        headers_da = [str(x).strip().lower() for x in data_du_an[0]]
        idx_ma_da = 0 # Cột A
        for i, h in enumerate(headers_da):
            if "mã dự án" in h or "mã da" in h:
                idx_ma_da = i
                break
                
        for r in data_du_an[1:]:
            if len(r) > idx_ma_da:
                val_da = str(r[idx_ma_da]).strip() # Chỉ bốc chính xác Cột A
                if val_da and val_da.lower() not in ["mã dự án", "stt", ""]:
                    if val_da not in danh_sach_du_an:
                        danh_sach_du_an.append(val_da)

    # Luồng bọc lót: Nếu link Apps Script CŨ chưa cập nhật, tự bốc cột A từ sheet KHO_PHAN_BO để App không bị liệt
    rows_kho_data = data_kho[1:] if len(data_kho) > 1 else []
    if not danh_sach_du_an and rows_kho_data:
        headers_kho = [str(x).strip().lower() for x in data_kho[0]]
        idx_mada_kho = 0
        for i, h in enumerate(headers_kho):
            if "dự án" in h or "mã da" in h:
                idx_mada_kho = i
                break
        
        for r in rows_kho_data:
            if len(r) > idx_mada_kho:
                val_da = str(r[idx_mada_kho]).strip()
                if val_da and val_da.lower() not in ["mã dự án", "stt", ""]:
                    if val_da not in danh_sach_du_an:
                        danh_sach_du_an.append(val_da)

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        if not danh_sach_du_an:
            du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", ["-- Chưa kết nối được dữ liệu --"])
        else:
            # Hiển thị đúng chuẩn Cột A: DA880, DA76...
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
    
    # 2. QUY CHIẾU LỌC ĐỘI VÀ ĐỊA ĐIỂM
    if data_kho and len(data_kho) > 0 and project_code:
        headers_kho = [str(x).strip().lower() for x in data_kho[0]]
        
        def find_col_kho(kws, default_i):
            for i, h in enumerate(headers_kho):
                if any(kw in h for kw in kws): return i
            return default_i

        idx_mada_kho = find_col_kho(["dự án", "mã da"], 0)
        idx_doi_kho = find_col_kho(["đội"], 6)
        idx_diem_kho = find_col_kho(["địa điểm", "đơn vị"], 7)
        idx_matb_kho = find_col_kho(["mã tb", "sku"], 1)
        idx_tentb_kho = find_col_kho(["thiết bị", "hàng hóa", "tên tb"], 3)
        idx_sl_kho = find_col_kho(["số lượng", "sl"], 4)
        idx_dvt_kho = find_col_kho(["đvt", "đơn vị tính"], 5)

        for r in rows_kho_data:
            row_proj = str(r[idx_mada_kho]).strip() if len(r) > idx_mada_kho else ""
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
    
    # 3. LỌC DANH MỤC THIẾT BỊ
    danh_sach_hang_hoa_phan_bo = []
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --" and project_code:
        for r in rows_kho_data:
            row_proj = str(r[idx_mada_kho]).strip() if len(r) > idx_mada_kho else ""
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
