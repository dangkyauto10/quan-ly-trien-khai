from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Cấu hình kết nối Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = "credentials.json"


@st.cache_resource
def ket_noi_sheets():
  creds = Credentials.from_service_account_file(
      SERVICE_ACCOUNT_FILE, scopes=SCOPES
  )
  client = gspread.authorize(creds)
  return client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")


try:
  spreadsheet = ket_noi_sheets()

  # 1. Đọc danh sách từ sheet QUAN_LY_DOI
  doi_sheet = spreadsheet.worksheet("QUAN_LY_DOI")
  doi_data = doi_sheet.get_all_values()

  danh_sach_doi = []
  for row in doi_data[2:]:  # Bỏ qua dòng tiêu đề
    if len(row) > 2 and row[2].strip():
      # Cấu trúc giả định: [STT, Mã Đội, Tên Đội Trưởng, Số Điện thoại, Khu vực]
      # Bạn có thể điều chỉnh vị trí cột (index) cho khớp với sheet thực tế của bạn
      thong_tin_doi = {
          "ma_doi": row[1].strip() if len(row) > 1 else "",
          "ten": row[2].strip(),
          "sdt": row[3].strip() if len(row) > 3 else "",
          "khu_vuc": row[4].strip() if len(row) > 4 else "",
      }
      danh_sach_doi.append(thong_tin_doi)

  # 2. Đọc danh sách điểm từ sheet DANH_SACH_DIEM
  diem_sheet = spreadsheet.worksheet("DANH_SACH_DIEM")
  danh_sach_diem_raw = diem_sheet.get_all_values()

  diem_info = {}
  for row in danh_sach_diem_raw[2:]:
    if len(row) > 3 and row[3].strip():
      ten_diem = row[3].strip()
      so_luong = row[7].strip() if len(row) > 7 and row[7].strip() else "0"
      diem_info[ten_diem] = so_luong

  tat_ca_diem = list(diem_info.keys())

except Exception as e:
  st.error(f"Lỗi kết nối dữ liệu Google Sheets: {e}")
  danh_sach_doi = []
  tat_ca_diem = []
  diem_info = {}

# --- GIAO DIỆN APP DI ĐỘNG ---
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.write("Hệ thống điều hành phân bổ tự động")

# Bước nhận diện thành viên qua Số Điện Thoại
st.subheader("1. Xác thực thành viên")
sdt_nhap = st.text_input(
    "Nhập Số Điện Thoại của bạn để tiếp tục:",
    placeholder="Ví dụ: 0912345678",
)

nguoi_dung_hien_tai = None
if sdt_nhap:
  # Tìm kiếm trong danh sách đội đã được duyệt
  for doi in danh_sach_doi:
    if doi["sdt"] == sdt_nhap.strip():
      nguoi_dung_hien_tai = doi
      break

  if nguoi_dung_hien_tai:
    st.success(
        f"✅ Chào mừng **{nguoi_dung_hien_tai['ten']}** (Đội:"
        f" {nguoi_dung_hien_tai['ma_doi']})!"
    )
  else:
    st.warning(
        "⚠️ Số điện thoại này chưa được cấp quyền hoặc chưa được quản lý duyệt."
        " Vui lòng kiểm tra lại hoặc liên hệ Admin."
    )

# Chỉ hiển thị form báo cáo nếu đã nhận diện được thành viên
if nguoi_dung_hien_tai:
  with st.form("form_bao_cao"):
    st.subheader("2. Thông tin lắp đặt")

    # Lọc điểm lắp đặt tương ứng khu vực của đội
    khu_vuc_duoc_giao = nguoi_dung_hien_tai["khu_vuc"]
    danh_sach_diem_hien_thi = [
        d
        for d in tat_ca_diem
        if khu_vuc_duoc_giao
        and (
            khu_vuc_duoc_giao.lower() in d.lower()
            or d.lower() in khu_vuc_duoc_giao.lower()
        )
    ]
    if not danh_sach_diem_hien_thi:
      danh_sach_diem_hien_thi = tat_ca_diem

    selected_diem = st.selectbox(
        "Chọn Điểm lắp đặt thuộc phân công:", danh_sach_diem_hien_thi
    )

    sl_phan_bo = (
        diem_info.get(selected_diem, "0") if selected_diem else "0"
    )
    st.info(
        f"📦 **Số lượng thiết bị được phân bổ cho điểm này:** {sl_phan_bo} thiết"
        " bị"
    )

    so_luong_thuc_te = st.number_input(
        "Số lượng thiết bị thực tế lắp đặt:",
        min_value=0,
        value=int(sl_phan_bo) if sl_phan_bo.isdigit() else 0,
    )

    st.subheader("3. Định vị Địa điểm (Google Maps)")
    maps_link = st.text_input(
        "Link Google Maps / Tọa độ GPS:",
        placeholder="Dán link Google Maps hoặc bấm lấy tọa độ thực tế",
    )

    submitted = st.form_submit_button("🚀 GỬI BÁO CÁO HOÀN THÀNH")

    if submitted:
      try:
        bao_cao_sheet = spreadsheet.worksheet("BAO_CAO_TRIEN_KHAI")
        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        hien_thi_ten = (
            f"{nguoi_dung_hien_tai['ten']} ({nguoi_dung_hien_tai['ma_doi']})"
        )
        row_data = [
            thoi_gian,
            hien_thi_ten,
            selected_diem,
            str(so_luong_thuc_te),
            maps_link,
        ]
        bao_cao_sheet.append_row(row_data)

        st.success(
            "🎉 Gửi báo cáo thành công! Dữ liệu đã tự động cập nhật về hệ thống."
        )
      except Exception as e:
        st.error(f"Lỗi khi gửi báo cáo: {e}")