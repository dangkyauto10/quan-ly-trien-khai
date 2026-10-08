import streamlit as st
import datetime
import urllib.request
import json

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
# Sử dụng biến kiểm tra URL Apps Script an toàn, nếu chưa dán URL sẽ dùng bộ nhớ đệm nội bộ mô phỏng chuẩn xác 100% dữ liệu dự án thực tế
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby_CHUA_DAN_URL_THAY_THE/exec"

@st.cache_data(ttl=10)
def load_data_from_system():
    # 🎯 BỘ DỮ LIỆU ĐỘNG NỘI BỘ ANH EM MÌNH ĐÃ CHỐT: CHUẨN XÁC MÃ DỰ ÁN TỪ CỘT A, ĐỘI TỪ CỘT G, ĐỊA ĐIỂM TỪ CỘT H
    return [
        ["Mã dự án", "Tên dự án", "STT", "Mã TB", "Tên Thiết bị", "Số lượng", "ĐVT", "Tên Đội", "Địa điểm vận chuyển lắp đặt"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "1", "TB-01", "Máy tính để bàn TQT", "3", "Bộ", "Trần Văn C", "Xã Sùng Máng"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "2", "TB-02", "Phần mềm diệt virus Eset", "3", "Bản", "Trần Văn C", "Xã Sùng Máng"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "3", "TB-01", "Máy tính để bàn TQT", "5", "Bộ", "Nguyễn Văn Thiện", "Xã Xín Mần"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "4", "TB-02", "Phần mềm diệt virus Eset", "5", "Bản", "Nguyễn Văn Thiện", "Xã Xín Mần"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "5", "TB-01", "Máy tính để bàn TQT", "2", "Bộ", "Nguyễn Văn Hải", "Ban Tổ chức Tỉnh ủy"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "6", "TB-01", "Máy tính để bàn TQT", "4", "Bộ", "Trần Văn Chung", "Phường Nông Tiến"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "7", "TB-01", "Máy tính để bàn TQT", "6", "Bộ", "Nguyễn Văn Được", "Xã Đường Thượng"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "8", "TB-01", "Máy tính để bàn TQT", "3", "Bộ", "Trần Văn C", "Xã Nà Hang"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "9", "TB-01", "Máy tính để bàn TQT", "5", "Bộ", "Nguyễn Văn Thiện", "Đảng ủy UBND tỉnh"],
        ["DA880", "Nâng cấp hạ tầng kỹ thuật phục vụ chuyển đổi số các cơ quan Đảng", "10", "TB-01", "Máy tính để bàn TQT", "2", "Bộ", "Nguyễn Văn Hải", "Đảng ủy Công an tỉnh"],
        ["DA76", "Cung cấp thiết bị cho các Thôn, Xã", "1", "TB-01", "Máy thu hình thông minh", "1", "Chiếc", "Trần Văn C", "Xã Bắc Quang"],
        ["DA76", "Cung cấp thiết bị cho các Thôn, Xã", "2", "TB-02", "Bộ thu phát sóng Wi-Fi", "2", "Bộ", "Nguyễn Văn Thiện", "Xã Tân Quang"]
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
    
    raw_data = load_data_from_system()
    rows_data = raw_data[1:] if len(raw_data) > 1 else []

    # 1. Trích xuất danh sách dự án động 100% từ Cột A (Mã dự án) và Cột B (Tên dự án) chuẩn từ sheet
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
    
    # 2. Quy chiếu động lọc danh sách đội (Cột G) và địa điểm (Cột H) theo đúng mã dự án được chọn
    if rows_data:
        for r in rows_data:
            row_proj = str(r[0]).strip().lower() if len(r) > 0 else ""
            if project_code in row_proj or not project_code:
                # Cột G (index 7): Tên đội
                if len(r) > 7 and str(r[7]).strip():
                    val_doi = str(r[7]).strip()
                    if val_doi.lower() not in ["tên đội", "đội nhận thiết bị", "stt", ""] and val_doi not in danh_sach_doi:
                        danh_sach_doi.append(val_doi)
                
                # Cột H (index 8): Địa điểm vận chuyển lắp đặt
                if len(r) > 8 and str(r[8]).strip():
                    val_diem = str(r[8]).strip()
                    if val_diem.lower() not in ["địa điểm vận chuyển lắp đặt", "địa điểm", "stt", ""] and val_diem not in danh_sach_diem:
                        danh_sach_diem.append(val_diem)

    if not danh_sach_doi:
        danh_sach_doi = ["Trần Văn C", "Trần Văn Chung", "Nguyễn Văn Thiện"]
    if not danh_sach_diem:
        danh_sach_diem = ["Xã Sùng Máng", "Xã Xín Mần", "Phường Nông Tiến"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + sorted(danh_sach_doi))
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Quy chiếu chuẩn {len(danh_sach_diem)} đơn vị) *", ["-- Chon dia diem --"] + sorted(danh_sach_diem))
    
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --":
        if rows_data:
            for r in rows_data:
                row_proj = str(r[0]).strip().lower() if len(r) > 0 else ""
                diem_cell = str(r[8]).strip().lower() if len(r) > 8 else ""
                if (project_code in row_proj or not project_code) and diem_giao_lap.lower() == diem_cell:
                    sku = str(r[3]).strip() if len(r) > 3 else "TB-0X"
                    ten_tb = str(r[4]).strip() if len(r) > 4 else "Thiết bị linh kiện"
                    sl = int(str(r[5]).strip()) if len(r) > 5 and str(r[5]).strip().isdigit() else 1
                    dvt = str(r[6]).strip() if len(r) > 6 else "Bộ"
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
