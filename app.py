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

st.title("🚀 Hệ Thống Quản Lý Lắp Đặt Dự Án")

st.header("🛠️ Quản Lý Lắp Đặt")
if st.button("Đồng bộ dữ liệu từ Kho phân bổ sang Lắp Đặt"):
    try:
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        sheet_ld = spreadsheet.worksheet("LAP_DAT")
        
        kho_data = sheet_kho.get_all_values()
        if len(kho_data) < 3:
            st.warning("Sheet KHO_PHAN_BO chưa có dữ liệu!")
        else:
            rows_to_append = []
            for idx, row in enumerate(kho_data[2:], start=1):
                if not any(row): continue
                
                # Lấy đúng dữ liệu từ KHO_PHAN_BO (index mảng Python từ 0):
                # row[0] = Cột A (Mã dự án)
                # row[3] = Cột D (Tên thiết bị)
                # row[4] = Cột E (Số lượng)
                # row[5] = Cột F (ĐVT)
                # row[6] = Cột G (Đội nhận thiết bị)
                # row[7] = Cột H (Địa điểm lắp)
                
                ma_du_an   = row[0] if len(row) > 0 else ""
                ten_tb     = row[3] if len(row) > 3 else ""
                so_luong   = row[4] if len(row) > 4 else ""
                don_vi     = row[5] if len(row) > 5 else ""
                doi_nhan   = row[6] if len(row) > 6 else ""
                dia_diem   = row[7] if len(row) > 7 else ""
                
                # Ánh xạ chuẩn 10 cột khớp 100% giao diện sheet LAP_DAT (từ A đến J):
                # [0] Cột A: Mã công việc (Tự sinh CV_1, CV_2,...)
                # [1] Cột B: Mã dự án <- Cột A KPB
                # [2] Cột C: Đội nhận thiết bị <- Cột G KPB
                # [3] Cột D: Tên thiết bị / Hàng hóa <- Cột D KPB
                # [4] Cột E: Số lượng thiết bị lắp <- Cột E KPB
                # [5] Cột F: ĐVT <- Cột F KPB
                # [6] Cột G: Địa điểm lắp <- Cột H KPB
                # [7] Cột H: Tình trạng thực hiện ("Đang lắp đặt")
                # [8] Cột I: Thời gian hoàn thành (để trống)
                # [9] Cột J: Link Google Maps (để trống)
                
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
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ dữ liệu sang Lắp Đặt thành công tuyệt đối!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
