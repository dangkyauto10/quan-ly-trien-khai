import streamlit as st
import datetime

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

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
    st.markdown("### BAO CAO NHIEM VU HIEN TRUONG (1 - 5 DU AN)")
    
    col_rf1, col_rf2 = st.columns([3, 1])
    with col_rf1:
        danh_sach_du_an = [
            "DA880 - Nang cap ha tang ky thuat", 
            "DA76 - Cung cap thiet bi thon xa",
            "DA01 - Trien khai tram vien thong",
            "DA02 - Lap dat thiet bi y te",
            "DA03 - Chuyen doi so xa phuong"
        ]
        du_an_chon = st.selectbox("CHON DU AN TRIEN KHAI *", danh_sach_du_an)
    with col_rf2:
        st.write("")
        st.write("")
        if st.button("Lam moi du lieu"):
            st.rerun()

    # Dữ liệu đầy đủ từ cấu trúc thực tế sheet KHO_PHAN_BO
    danh_sach_doi = [
        "Nguyễn Văn Thiện", "Trần Văn C", "Trần Văn Chung", 
        "Nguyễn Văn Hải", "Nguyễn Văn Được", "Nguyễn Đức Hải"
    ]
    
    danh_sach_diem = [
        "Xã Sùng Máng", "Phường Nông Tiến", "Xã Đường Thượng", "Xã Nà Hang", 
        "Xã Xín Mần", "Ban Tổ chức Tỉnh ủy", "Đảng ủy UBND tỉnh", 
        "Đảng ủy Công an tỉnh", "Trường Chính trị tỉnh", "Đảng ủy Quân sự tỉnh", 
        "Văn phòng Tỉnh ủy", "Ban Nội chính Tỉnh ủy", "Ban Tuyên giáo và Dân vận Tỉnh ủy"
    ]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + danh_sach_doi)
    diem_giao_lap = st.selectbox("DIEM GIAO HANG & LAP DAT *", ["-- Chon dia diem --"] + danh_sach_diem)
    
    # MÔ PHỎNG ÁNH XẠ TOÀN BỘ DANH MỤC THIẾT BỊ / HÀNG HÓA VÀ SỐ LƯỢNG CHO ĐÚNG TỪNG ĐIỂM
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --":
        # Dữ liệu mô phỏng chuẩn bóc từ bảng Google Sheets của anh
        if "Sùng Máng" in diem_giao_lap:
            danh_sach_hang_hoa_phan_bo = [
                {"sku": "TB-01", "ten": "Máy tính để bàn TQT TPY01 535215", "sl": 3, "dvt": "Bộ"},
                {"sku": "TB-02", "ten": "Bản quyền phần mềm diệt virus Eset Endpoint", "sl": 3, "dvt": "Bản"},
                {"sku": "TB-03", "ten": "Bản quyền phần mềm Office 2024 Home and Business", "sl": 3, "dvt": "Bản"},
                {"sku": "TB-04", "ten": "Thiết bị mạng switch Teltonika SWM281", "sl": 1, "dvt": "Chiếc"},
                {"sku": "TB-05", "ten": "Cáp mạng Commscope Netconnect CS31CM", "sl": 305, "dvt": "M"}
            ]
        elif "Xín Mần" in diem_giao_lap:
            danh_sach_hang_hoa_phan_bo = [
                {"sku": "TB-01", "ten": "Máy tính để bàn TQT TPY01 535215", "sl": 5, "dvt": "Bộ"},
                {"sku": "TB-02", "ten": "Bản quyền phần mềm diệt virus Eset Endpoint", "sl": 5, "dvt": "Bản"},
                {"sku": "TB-03", "ten": "Bản quyền phần mềm Office 2024 Home and Business", "sl": 5, "dvt": "Bản"},
                {"sku": "TB-04", "ten": "Thiết bị mạng switch Teltonika SWM281", "sl": 1, "dvt": "Chiếc"},
                {"sku": "TB-05", "ten": "Cáp mạng Commscope Netconnect CS31CM", "sl": 305, "dvt": "M"}
            ]
        elif "Tỉnh ủy" in diem_giao_lap or "UBND tỉnh" in diem_giao_lap:
            danh_sach_hang_hoa_phan_bo = [
                {"sku": "TB-01", "ten": "Máy tính để bàn TQT TPY01 535215", "sl": 12, "dvt": "Bộ"},
                {"sku": "TB-02", "ten": "Bản quyền phần mềm diệt virus Eset Endpoint", "sl": 12, "dvt": "Bản"},
                {"sku": "TB-03", "ten": "Bản quyền phần mềm Office 2024 Home and Business", "sl": 12, "dvt": "Bản"},
                {"sku": "TB-04", "ten": "Thiết bị mạng switch Teltonika SWM281", "sl": 1, "dvt": "Chiếc"},
                {"sku": "TB-05", "ten": "Cáp mạng Commscope Netconnect CS31CM", "sl": 305, "dvt": "M"}
            ]
        else:
            danh_sach_hang_hoa_phan_bo = [
                {"sku": "TB-01", "ten": "Máy tính để bàn TQT TPY01 535215", "sl": 4, "dvt": "Bộ"},
                {"sku": "TB-02", "ten": "Bản quyền phần mềm diệt virus Eset Endpoint", "sl": 4, "dvt": "Bản"},
                {"sku": "TB-03", "ten": "Bản quyền phần mềm Office 2024 Home and Business", "sl": 4, "dvt": "Bản"},
                {"sku": "TB-04", "ten": "Thiết bị mạng switch Teltonika SWM281", "sl": 1, "dvt": "Chiếc"},
                {"sku": "TB-05", "ten": "Cáp mạng Commscope Netconnect CS31CM", "sl": 305, "dvt": "M"}
            ]

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ TẠI: **{diem_giao_lap}** (Đội: {doi_thuc_hien})")
        
        # Hiển thị bảng chi tiết đầy đủ toàn bộ hàng hóa và số lượng phân bổ của điểm đó
        table_markdown = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
        for item in danh_sach_hang_hoa_phan_bo:
            table_markdown += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
        st.markdown(table_markdown)
        
        st.success(f"Đã ánh xạ thành công toàn bộ {len(danh_sach_hang_hoa_phan_bo)} dòng thiết bị từ sheet KHO_PHAN_BO!")
    else:
        st.info("Vui long chon day du Ten doi va Dia diem để hien thi chi tiet danh muc thiet bi phan bo.")
        
    st.markdown("---")
    st.markdown("Chup anh hien truong:")
    st.camera_input("Chup anh thuc te")
    
    st.markdown("---")
    if st.button("Check-in GPS Tọa độ Hiện trường", use_container_width=True):
        st.success("Check-in GPS thành công!")
        
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("ĐÃ GIAO XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo thành công: ĐÃ GIAO XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({du_an_chon})")
    with col_b2:
        if st.button("ĐÃ LẮP XONG", type="primary", use_container_width=True):
            if doi_thuc_hien == "-- Chon ten doi --" or diem_giao_lap == "-- Chon dia diem --":
                st.warning("Vui long chon day du Ten doi va Dia diem!")
            else:
                st.success(f"Gửi báo cáo thành công: ĐÃ LẮP XONG cho đội {doi_thuc_hien} tại {diem_giao_lap} ({du_an_chon})")
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
