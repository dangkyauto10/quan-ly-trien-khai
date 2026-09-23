import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Lấy thông tin xác thực từ Streamlit Secrets (đã cấu hình [gcp_service_account])
creds_dict = dict(st.secrets["gcp_service_account"])

# 2. Định nghĩa quyền truy cập (Scope) cho Google Sheets và Google Drive
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 3. Xác thực kết nối
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

# 4. Mở file Google Sheet (Bạn hãy thay "quan-ly-trien-khai" bằng tên chính xác file Google Sheet của bạn)
sheet_name = "quan-ly-trien-khai" 
try:
    sh = gc.open(sheet_name)
    worksheet = sh.get_worksheet(0) # Lấy sheet đầu tiên
    data = worksheet.get_all_records()
    
    st.title("Quản lý triển khai")
    st.success(f"Đã kết nối thành công tới Google Sheet: {sheet_name}")
    
    # Hiển thị dữ liệu dạng bảng trên web/điện thoại
    st.dataframe(data)
    
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.info("Hãy chắc chắn bạn đã chia sẻ quyền Editor của Google Sheet cho email trong file credentials.json!")
