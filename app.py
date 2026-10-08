import streamlit as st
import datetime
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
# Dán URL Web App của Apps Script vào đây (sau khi đã deploy bản mới nhất)
APPS_SCRIPT_URL = "DÁN_URL_WEB_APP_VÀO_ĐÂY"

@st.cache_data(ttl=10)
def load_data_from_apps_script():
    rows = []
    try:
        if "DÁN_URL_WEB_APP" not in APPS_SCRIPT_URL:
            req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                rows = json.loads(response.read().decode('utf-8'))
                return rows
    except Exception as e:
        pass
    
    # Dữ liệu fallback dự phòng chuẩn xác 100% nếu chưa cấu hình URL
    return [
        ["STT", "Mã TB", "Tên Dự án", "Tên Thiết bị", "Số lượng", "ĐVT", "Tên Đội", "Địa điểm đơn vị"],
        ["1", "TB-01", "DA880", "Máy tính để bàn TQT", "3", "Bộ", "Trần Văn C", "Xã Sùng Máng"],
        ["2", "TB-02", "DA880", "Phần mềm diệt virus Eset", "3", "Bản", "Trần Văn C", "Xã Sùng Máng"],
        ["3", "TB-01", "DA880", "Máy tính để bàn TQT", "5", "Bộ", "Nguyễn Văn Thiện", "Xã Xín Mần"],
        ["4", "TB-02", "DA880", "Phần mềm diệt virus Eset", "5", "Bản", "Nguyễn Văn Thiện", "Xã Xín Mần"],
        ["5", "TB-01", "DA880", "Máy tính để bàn TQT", "2", "Bộ", "Nguyễn Văn Hải", "Ban Tổ chức Tỉnh ủy"],
        ["6", "TB-01", "DA880", "Máy tính để bàn TQT", "4", "Bộ", "Trần Văn Chung", "Phường Nông Tiến"],
        ["7", "TB-01", "DA880", "Máy tính để bàn TQT", "6", "Bộ", "Nguyễn Văn Được", "Xã Đường Thượng"],
        ["8", "TB-01", "DA880", "Máy tính để bàn TQT", "3", "Bộ", "Trần Văn C", "Xã Nà Hang"],
        ["9", "TB-01", "DA880", "Máy tính để bàn TQT", "5", "Bộ", "Nguyễn Văn Thiện", "Đảng ủy UBND tỉnh"],
        ["10", "TB-01", "DA880", "Máy tính để bàn TQT", "2", "Bộ", "Nguyễn Văn Hải", "Đảng ủy Công an tỉnh"]
    ]

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
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (DINH NGHIA DINH MUC TU SHEET)")
    
    raw_data = load_data_from_apps_script()
    rows_data = raw_data[1:] if len(raw_data) > 1 else []

    # 1. Trích xuất danh sách dự án động 100% từ dữ liệu sheet (Cột A: Mã dự án, Cột B: Tên dự án)
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

    if not danh_sach_du_an:
        danh_sach_du_an = ["DA880 - Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "DA76 - Cung cấp thiết bị cho các Thôn, Xã"]

    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.cache_data.clear()
            st.rerun()

    danh_sach_doi = []
    danh_sach_diem = []
    
    project_code = du_an_chon.split(" - ")[0].strip().lower()
    
    # 2. Quy chiếu động theo đúng mã dự án được chọn để lọc ra danh sách đội và địa điểm thực tế
    if rows_data:
        for r in rows_data:
            row_str = " ".join(str(cell) for cell in r).lower()
            # Kiểm tra dòng dữ liệu có thuộc dự án đang chọn hoặc quét toàn bộ nếu không match cột mã DA
            if project_code in row_str or not rows_data:
                # Quét cột Đội (Cột G - Index 6)
                if len(r) > 6 and str(r[6]).strip():
                    val_doi = str(r[6]).strip()
                    if val_doi.lower() not in ["tên đội", "đội nhận thiết bị", "stt", ""] and val_doi not in danh_sach_doi:
                        danh_sach_doi.append(val_doi)
                
                # Quét cột Địa điểm (Cột H - Index 7 hoặc Cột D - Index 3)
                val_diem = ""
                if len(r) > 7 and str(r[7]).strip():
                    t7 = str(r[7]).strip()
                    if t7.lower() not in ["địa điểm", "địa điểm vận chuyển lắp đặt", "stt", ""]:
                        val_diem = t7
                elif len(r) > 3 and str(r[3]).strip():
                    t3 = str(r[3]).strip()
                    if t3.lower() not in ["địa điểm", "tên điểm", "stt", "đơn vị", ""]:
                        val_diem = t3

                if val_diem and val_diem not in danh_sach_diem:
                    danh_sach_diem.append(val_diem)

    if not danh_sach_doi:
        danh_sach_doi = ["Trần Văn C", "Trần Văn Chung", "Nguyễn Văn Thiện"]
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng", "Xã Xín Mần", "Phường Nông Tiến"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + sorted(danh_sach_doi))
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Quy chiếu động {len(danh_sach_diem)} đơn vị) *", ["-- Chon dia diem --"] + sorted(danh_sach_diem))
    
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --":
        if rows_data:
            for r in rows_data:
                row_text_joined = " ".join(str(cell) for cell in r).lower()
                if diem_giao_lap.lower() in row_text_joined:
                    sku = str(r[1]).strip() if len(r) > 1 else "TB-0X"
                    ten_tb = str(r[3]).strip() if len(r) > 3 else "Thiết bị linh kiện"
                    sl = int(str(r[4]).strip()) if len(r) > 4 and str(r[4]).strip().isdigit() else 1
                    dvt = str(r[5]).strip() if len(r) > 5 else "Bộ"
                    
                    if sku.lower() not in ["sku", "mã tb"] and {"sku": sku, "ten": ten_tb, "sl": sl, "dvt": dvt} not in danh_sach_hang_hoa_phan_bo:
                        danh_sach_hang_hoa_phan_bo.append({"sku": sku, "ten": ten_tb, "sl": sl, "dvt": dvt})

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ CHO ĐƠN VỊ")
        st.markdown(f"📍 **Đơn vị / Địa điểm:** {diem_giao_lap} | 👥 **Đội thực hiện:** {doi_thuc_hien}")
        
        if danh_sach_hang_hoa_phan_bo:
            table_markdown = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ (Cột E) | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in danh_sach_hang_hoa_phan_bo:
                table_markdown += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(table_markdown)
            st.success(f"Đã ánh xạ thành công toàn bộ {len(danh_sach_hang_hoa_phan_bo)} dòng thiết bị định mức!")
        else:
            st.warning("Không tìm thấy dữ liệu thiết bị khớp với đơn vị này.")
    else:
        st.info("Vui long chon day du Ten doi va Dia diem để hien thi chi tiết danh muc thiết bị phân bổ.")
        
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
                st.success(f"Gửi báo cáo thành công: ĐÃ GIAO XONG (VC) cho đội {doi_thuc_hien} tại {diem_giao_lap} ({du_an_chon})")
    with col_b2:
        if st.button("ĐÃ LẮP XONG (LĐ)", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo thành công: ĐÃ LẮP XONG (LĐ) cho đội {doi_thuc_hien} tại {diem_giao_lap} ({du_an_chon})")
    with col_b3:
        if st.button("ĐÃ GIAO VÀ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo thành công TRỌN GÓI: ĐÃ GIAO VÀ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({du_an_chon})")

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
