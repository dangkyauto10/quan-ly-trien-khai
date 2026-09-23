import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Lấy thông tin xác thực từ Streamlit Secrets
creds_dict = dict(st.secrets["gcp_service_account"])

# Tự động chuẩn hóa định dạng khóa bảo mật
if "private_key" in creds_dict:
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

# 2. Định nghĩa quyền truy cập (Scope) cho Google Sheets và Google Drive
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 3. Xác thực kết nối
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

# 4. Mở file Google Sheet và hiển thị dữ liệu
sheet_name = "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH"
try:
    sh = gc.open(sheet_name)
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_records()

    st.title("Quản lý triển khai")
    st.success(f"Đã kết nối thành công tới Google Sheet: {sheet_name}")
    st.dataframe(data)

except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.info("Hãy chắc chắn bạn đã chia sẻ quyền Editor của Google Sheet cho email trong file credentials.json!")
