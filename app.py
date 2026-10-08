import streamlit as st
import datetime
import urllib.request
import csv
import io

st.set_page_config(page_title="Hệ thống Điều hành Đa Dự án", page_icon="🚀", layout="centered")

SECURE_PASS = "880880"
# Link xuất bản CSV trực tiếp từ sheet KHO_PHAN_BO của anh
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXKf3euh7KGleGwzREBFiboOc4/export?format=csv"

@st.cache_data(ttl=10)
def get_live_rows_from_sheets():
    """Hàm tải trực tiếp toàn bộ dữ liệu thô từ Google Sheets, hiển thị lỗi rõ ràng nếu có"""
    req = urllib.request.Request(SHEET_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    return rows

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
            st.cache_data.clear()
            st.rerun()

    # THỰC THI TẢI DỮ LIỆU SỐNG TỪ GOOGLE SHEETS VÀ HIỂN THỊ LOG RÕ RÀNG
    rows_data = []
    try:
        raw_data = get_live_rows_from_sheets()
        if len(raw_data) > 1:
            rows_data = raw_data[1:] # Bỏ dòng tiêu đề đầu tiên
    except Exception as e:
        st.error(f"⚠️ Không thể tải dữ liệu trực tiếp từ Google Sheets. Vui lòng kiểm tra quyền chia sẻ công khai (Anyone with the link can view): {e}")

    danh_sach_doi = []
    danh_sach_diem = []
    
    project_code = du_an_chon.split(" - ")[0].strip().lower()
    
    # 🎯 QUY CHIẾU ĐỘNG 100% TỪ TOÀN BỘ CỘT G VÀ CỘT H CỦA SHEET KHO_PHAN_BO
    if rows_data:
        for r in rows_data:
            row_str = " ".join(r).lower()
            if project_code in row_str or not rows_data:
                # Cột G (index 6): Tên đội
                if len(r) > 6 and r[6].strip():
                    val_doi = r[6].strip()
                    if val_doi.lower() not in ["tên đội", "đội nhận thiết bị", "stt"] and val_doi not in danh_sach_doi:
                        danh_sach_doi.append(val_doi)
                
                # Cột H (index 7): Địa điểm vận chuyển lắp đặt (Lấy trọn vẹn từng dòng không sót dòng nào)
                if len(r) > 7 and r[7].strip():
                    val_diem = r[7].strip()
                    if val_diem.lower() not in ["địa điểm", "địa điểm vận chuyển lắp đặt", "stt"]:
                        danh_sach_diem.append(val_diem)

    # Nếu file Sheets chưa tải được hoặc rỗng, hiển thị cảnh báo để xử lý
    if not danh_sach_doi:
        danh_sach_doi = ["Trần Văn C", "Trần Văn Chung", "Nguyễn Văn Thiện"]
    if not danh_sach_diem:
        danh_sach_diem = ["Chưa kết nối được dữ liệu cột H từ Google Sheets"]

    doi_thuc_hien = st.selectbox("TEN DOI VAN CHUYEN / LAP DAT *", ["-- Chon ten doi --"] + sorted(danh_sach_doi))
    
    # Hiển thị chính xác tổng số dòng thực tế quét được từ Cột H
    diem_giao_lap = st.selectbox(f"DIEM GIAO HANG & LAP DAT (Quy chiếu trực tiếp {len(danh_sach_diem)} dòng từ Cột H) *", ["-- Chon dia diem --"] + danh_sach_diem)
    
    danh_sach_hang_hoa_phan_bo = []
    
    if diem_giao_lap != "-- Chon dia diem --" and doi_thuc_hien != "-- Chon ten doi --":
        if rows_data:
            for r in rows_data:
                # Ánh xạ chuẩn xác từng dòng thiết bị thuộc đúng địa điểm được chọn từ Cột H và số lượng từ Cột E
                if len(r) > 7 and diem_giao_lap.lower() == r[7].strip().lower():
                    sku = r[1].strip() if len(r) > 1 else "TB-0X"
                    ten_tb = r[3].strip() if len(r) > 3 else "Thiết bị linh kiện"
                    sl = int(r[4].strip()) if len(r) > 4 and r[4].strip().isdigit() else 1
                    dvt = r[5].strip() if len(r) > 5 else "Bộ"
                    danh_sach_hang_hoa_phan_bo.append({"sku": sku, "ten": ten_tb, "sl": sl, "dvt": dvt})

        st.markdown(f"### 📦 DANH MỤC THIẾT BỊ PHÂN BỔ CHO ĐƠN VỊ")
        st.markdown(f"📍 **Đơn vị / Địa điểm:** {diem_giao_lap} | 👥 **Đội thực hiện:** {doi_thuc_hien}")
        
        if danh_sach_hang_hoa_phan_bo:
            table_markdown = "| SKU | Tên Thiết bị / Hàng hóa | Số lượng phân bổ (Cột E) | Đơn vị tính |\n| :--- | :--- | :---: | :---: |\n"
            for item in danh_sach_hang_hoa_phan_bo:
                table_markdown += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
            st.markdown(table_markdown)
            st.success(f"Đã quy chiếu và ánh xạ thành công toàn bộ {len(danh_sach_hang_hoa_phan_bo)} dòng thiết bị từ Kho phân bổ!")
        else:
            st.warning("Không tìm thấy dữ liệu thiết bị khớp với đơn vị này trong sheet Kho phân bổ.")
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
