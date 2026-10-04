import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- KIỂM TRA KẾT NỐI AN TOÀN (CHỈ ĐỌC) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else "credentials.json"

st.header("🔍 Kiểm tra trạng thái hệ thống và kết nối Google Sheets")

if st.button("Chạy kiểm tra kết nối (An toàn tuyệt đối)"):
    try:
        if isinstance(creds_dict, dict):
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
        spreadsheet = client.open_by_url(sheet_url)
        
        # Đọc thử sheet KHO_PHAN_BO
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        headers = sheet_kho.row_values(2) # Đọc dòng tiêu đề ở dòng 2
        
        st.success("✅ Kết nối Google Sheets thành công và an toàn!")
        st.write(f"📂 Đang mở file: **{spreadsheet.title}**")
        st.write(f"📊 Đã đọc tiêu đề sheet `KHO_PHAN_BO` (Dòng 2):")
        st.write(headers)
        
    except Exception as e:
        st.error(f"❌ Lỗi kết nối hoặc phân quyền: {e}")
        st.info("💡 Hướng dẫn khắc phục: Hãy đảm bảo email Service Account đã được cấp quyền Editor cho file Google Sheets.")
