from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Cấu hình kết nối Google Sheets (Hỗ trợ chuẩn Streamlit Secrets và file cục bộ)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def ket_noi_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        
        client = gspread.authorize(creds)
        return client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
    except Exception as e:
        st.error(f"Lỗi xác thực kết nối: {e}")
        return None

try:
    spreadsheet = ket_noi_sheets()

    if spreadsheet:
        # 1. Đọc sheet QUAN_LY_DOI (Quét động theo tiêu đề cột, chống lệch cột)
        doi_sheet = spreadsheet.worksheet("QUAN_LY_DOI")
        doi_data = doi_sheet.get_all_values()

        doi_to_khu_vuc = {}
        danh_sach_nguoi_phu_trach = []

        if len(doi_data) > 2:
            header_doi = doi_data[1]  # Dòng 2 chứa tiêu đề
            try:
                idx_ma_doi = header_doi.index("Mã Đội") if "Mã Đội" in header_doi else 1
                idx_ten = header_doi.index("Họ và Tên") if "Họ và Tên" in header_doi else 2
                idx_khu_vuc = header_doi.index("Khu Vực Phụ Trách") if "Khu Vực Phụ Trách" in header_doi else 4
            except:
                idx_ma_doi, idx_ten, idx_khu_vuc = 1, 2, 4

            for row in doi_data[2:]:
                if len(row) > idx_ten and row[idx_ten].strip():
                    ten_doi_truong = row[idx_ten].strip()
                    ma_doi = row[idx_ma_doi].strip() if len(row) > idx_ma_doi and row[idx_ma_doi].strip() else ""
                    hien_thi = f"{ten_doi_truong} ({ma_doi})" if ma_doi else ten_doi_truong

                    danh_sach_nguoi_phu_trach.append(hien_thi)
                    khu_vuc = row[idx_khu_vuc].strip() if len(row) > idx_khu_vuc else ""
                    doi_to_khu_vuc[hien_thi] = khu_vuc

        # 2. Đọc sheet DANH_SACH_DIEM (Quét động theo tiêu đề cột)
        diem_sheet = spreadsheet.worksheet("DANH_SACH_DIEM")
        diem_data = diem_sheet.get_all_values()

        diem_info = {}
        if len(diem_data) > 2:
            header_diem = diem_data[1]
            try:
                idx_ten_diem = header_diem.index("Tên Điểm") if "Tên Điểm" in header_diem else 3
                idx_so_luong = header_diem.index("Số Lượng Thiết Bị") if "Số Lượng Thiết Bị" in header_diem else 7
            except:
                idx_ten_diem, idx_so_luong = 3, 7

            for row in diem_data[2:]:
                if len(row) > idx_ten_diem and row[idx_ten_diem].strip():
                    ten_diem = row[idx_ten_diem].strip()
                    so_luong = row[idx_so_luong].strip() if len(row) > idx_so_luong and row[idx_so_luong].strip() else "0"
                    diem_info[ten_diem] = so_luong

        tat_ca_diem = list(diem_info.keys())
    else:
        danh_sach_nguoi_phu_trach, doi_to_khu_vuc, tat_ca_diem, diem_info = [], {}, [], {}

except Exception as e:
    st.error(f"Lỗi đọc dữ liệu Google Sheets: {e}")
    danh_sach_nguoi_phu_trach = []
    doi_to_khu_vuc = {}
    tat_ca_diem = []
    diem_info = {}

# --- GIAO DIỆN APP DI ĐỘNG ---
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.write("Hệ thống điều hành phân bổ tự động")

with st.form("form_bao_cao"):
    st.subheader("1. Xác nhận thông tin thực hiện")

    if danh_sach_nguoi_phu_trach:
        selected_nguoi = st.selectbox("Cán bộ / Đội trưởng thực hiện:", danh_sach_nguoi_phu_trach)
    else:
        selected_nguoi = ""
        st.warning("Chưa tải được danh sách nhân sự từ Google Sheets.")

    khu_vuc_duoc_giao = doi_to_khu_vuc.get(selected_nguoi, "")

    danh_sach_diem_hien_thi = [
        d for d in tat_ca_diem
        if khu_vuc_duoc_giao
        and (khu_vuc_duoc_giao.lower() in d.lower() or d.lower() in khu_vuc_duoc_giao.lower())
    ]
    if not danh_sach_diem_hien_thi:
        danh_sach_diem_hien_thi = tat_ca_diem

    if danh_sach_diem_hien_thi:
        selected_diem = st.selectbox("Chọn Điểm lắp đặt thuộc phân công:", danh_sach_diem_hien_thi)
    else:
        selected_diem = ""
        st.warning("Không tìm thấy điểm lắp đặt phù hợp.")

    sl_phan_bo = diem_info.get(selected_diem, "0") if selected_diem else "0"
    st.info(f"📦 **Số lượng thiết bị được phân bổ cho điểm này:** {sl_phan_bo} thiết bị")

    so_luong_thuc_te = st.number_input(
        "Số lượng thiết bị thực tế lắp đặt:",
        min_value=0,
        value=int(sl_phan_bo) if sl_phan_bo.isdigit() else 0,
    )

    st.subheader("2. Định vị Địa điểm (Google Maps)")
    maps_link = st.text_input(
        "Link Google Maps / Tọa độ GPS:",
        placeholder="Dán link Google Maps hoặc bấm lấy tọa độ thực tế",
    )

    submitted = st.form_submit_button("🚀 GỬI BÁO CÁO HOÀN THÀNH")

    if submitted:
        try:
            bao_cao_sheet = spreadsheet.worksheet("BAO_CAO_TRIEN_KHAI")
            thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            row_data = [
                thoi_gian,
                selected_nguoi,
                selected_diem,
                str(so_luong_thuc_te),
                maps_link,
            ]
            bao_cao_sheet.append_row(row_data)

            st.success("🎉 Gửi báo cáo thành công! Dữ liệu đã tự động cập nhật về hệ thống.")
        except Exception as e:
            st.error(f"Lỗi khi gửi báo cáo: {e}")
