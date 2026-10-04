import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CẤU HÌNH KẾT NỐI GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"] if "gcp_service_account" in st.secrets else "credentials.json"

try:
    if isinstance(creds_dict, dict):
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
    spreadsheet = client.open_by_url(sheet_url)
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")

st.title("🚀 Hệ Thống Quản Lý Lắp Đặt Dự Án (Debug Mode)")

st.header("🛠️ Đồng Bộ: Kho Phân Bổ ➔ Lắp Đặt")

if st.button("Thực thi đồng bộ sang Lắp Đặt"):
    try:
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        sheet_ld = spreadsheet.worksheet("LAP_DAT")
        
        kho_data = sheet_kho.get_all_values()
        
        # IN RA MÀN HÌNH ĐỂ KIỂM TRA DỮ LIỆU THỰC TẾ ĐỌC ĐƯỢC TỪ KHO PHÂN BỔ
        st.write(f"📊 Tổng số dòng đọc được từ KHO_PHAN_BO: {len(kho_data)}")
        if len(kho_data) > 0:
            st.write("Dòng đầu tiên (Tiêu đề):", kho_data[0])
        if len(kho_data) > 2:
            st.write("Dữ liệu từ dòng 3 trở đi:", kho_data[2:])
        
        if len(kho_data) < 3:
            st.warning("⚠️ Sheet KHO_PHAN_BO có ít hơn 3 dòng, không đủ dữ liệu để đồng bộ!")
        else:
            rows_to_append = []
            for idx, row in enumerate(kho_data[2:], start=1):
                if not any(row): continue
                
                ma_du_an   = row[0] if len(row) > 0 else ""
                ten_tb     = row[3] if len(row) > 3 else ""
                so_luong   = row[4] if len(row) > 4 else ""
                don_vi     = row[5] if len(row) > 5 else ""
                doi_nhan   = row[6] if len(row) > 6 else ""
                dia_diem   = row[7] if len(row) > 7 else ""
                
                row_data = [
                    f"CV_{idx}",    # A
                    ma_du_an,       # B
                    doi_nhan,       # C
                    ten_tb,         # D
                    so_luong,       # E
                    don_vi,         # F
                    dia_diem,       # G
                    "Đang lắp đặt", # H
                    "",             # I
                    ""              # J
                ]
                rows_to_append.append(row_data)
            
            st.write(f"🔍 Số dòng hợp lệ chuẩn bị đẩy sang LAP_DAT: {len(rows_to_append)}")
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success(f"✅ Đã ghi thành công {len(rows_to_append)} dòng vào sheet LAP_DAT!")
            else:
                st.warning("⚠️ Không có dòng dữ liệu nào thỏa mãn điều kiện để đưa sang LAP_DAT.")
                
    except Exception as e:
        st.error(f"❌ Lỗi ngoại lệ chi tiết: {e}")
