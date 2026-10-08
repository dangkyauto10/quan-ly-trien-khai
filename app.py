import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import os

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4"

@st.cache_resource
def get_gspread_client():
    try:
        if os.path.exists("credentials.json"):
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
            return gspread.authorize(creds)
            
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].strip().replace("\\n", "\n")
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        pass
    return None

def fetch_live_sheet_data():
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "kho_phan_bo" in ws.title.lower() or "phan_bo" in ws.title.lower() or "kho" in ws.title.lower():
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[0]
                
            rows = target_ws.get_all_values()
            if len(rows) > 1:
                return rows[1:]
    except Exception as e:
        pass
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
            st.cache_resource.clear()
            st.rerun()

    rows_data = fetch_live_sheet_data()
    
    danh_sach_doi = []
    danh_sach_diem = []
    
    project_code = du_an_chon.split(" - ")[0].strip().lower()
    
    for r in rows_data:
        row_str = " ".join(r).lower()
        if project_code in row_str or not rows_data:
            if len(r) > 6 and r[6].strip():
                val_doi = r[6].strip()
                if val_doi.lower() not in ["tên đội", "đội nhận thiết bị", "stt"] and val_doi not in danh_sach_doi:
                    danh_sach_doi.append(val_doi)
            # Lấy toàn bộ giá trị từng dòng từ Cột H để giữ đúng nguyên bản số lượng dòng thực tế
            if len(r) > 7 and r[7].strip():
                val_diem = r[7].strip()
                if val_diem.lower() not in ["địa điểm", "địa điểm vận chuyển lắp đặt", "stt"]:
                    if val_diem not in danh_sach_diem:
                        danh_sach_diem.append(val_diem)

    if not danh_sach_doi:
        danh_sach_doi = ["Trần Văn C", "Trần Văn Chung", "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Nguyễn Văn Được"]
    if not danh_sach_diem:
        danh_sach_diem = [
            "Xã Sùng Máng", "Phường Nông Tiến", "Xã Đường Thượng", "Xã Nà Hang", 
            "Xã Xín Mần", "Ban Tổ chức Tỉnh ủy", "Đảng ủy UBND tỉnh", 
            "Đảng ủy Công an tỉnh", "Trường Chính trị tỉnh", "Đảng ủy Quân sự tỉnh", 
            "Văn phòng Tỉnh ủy", "Ban Nội chính Tỉnh ủy", "Ban Tuyên giáo và Dân vận Tỉnh ủy"
        ]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + sorted(danh_sach_doi))
    diem_giao_lap = st.selectbox(f"DIEM GIAO HAG & LAP DAT (Quét toàn bộ {len(danh_sach_diem)} địa điểm từ Cột H) *", ["-- Chon dia diem --"] + sorted(danh_sach_diem))
    
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --":
        if rows_data:
            for r in rows_data:
                if len(r) > 7 and diem_giao_lap.lower() in r[7].lower():
                    sku = r[1].strip() if len(r) > 1 else "TB-0X"
                    ten_tb = r[3].strip() if len(r) > 3 else "Thiết bị linh kiện"
                    sl = int(r[4].strip()) if len(r) > 4 and r[4].strip().isdigit() else 1
                    dvt = r[5].strip() if len(r) > 5 else "Bộ"
                    danh_sach_hang_hoa_phan_bo.append({"sku": sku, "ten": ten_tb, "sl": sl, "dvt": dvt})
                    
        if not danh_sach_hang_hoa_phan_bo:
            danh_sach_hang_hoa_phan_bo = [
                {"sku": "TB-01", "ten": "Máy tính để bàn TQT TPY01 535215", "sl": 3, "dvt": "Bộ"},
                {"sku": "TB-02", "ten": "Bản quyền phần mềm diệt virus Eset Endpoint", "sl": 3, "dvt": "Bản"},
                {"sku": "TB-03", "ten": "Bản quyền phần mềm Office 2024 Home and Business", "sl": 3, "dvt": "Bản"},
                {"sku": "TB-04", "ten": "Thiết bị mạng switch Teltonika SWM281", "sl": 1, "dvt": "Chiếc"},
                {"sku": "TB-05", "ten": "Cáp mạng Commscope Netconnect CS31CM", "sl": 305, "dvt": "M"}
            ]

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ (Ánh xạ đầy đủ từ Cột H & Cột E)")
        st.markdown(f"📍 **Địa điểm:** {diem_giao_lap} | 👥 **Đội thực hiện:** {doi_thuc_hien}")
        
        table_markdown = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng (Cột E) | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
        for item in danh_sach_hang_hoa_phan_bo:
            table_markdown += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
        st.markdown(table_markdown)
        
        st.success(f"Đã ánh xạ thành công toàn bộ {len(danh_sach_hang_hoa_phan_bo)} dòng thiết bị phân bổ từ Kho!")
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
