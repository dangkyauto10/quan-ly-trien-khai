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

st.header("🛠️ Đồng Bộ: Kho Phân Bổ ➔ Lắp Đặt")
if st.button("Thực thi đồng bộ sang Lắp Đặt"):
    try:
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        sheet_ld = spreadsheet.worksheet("LAP_DAT")
        
        kho_data = sheet_kho.get_all_values()
        if len(kho_data) < 3:
            st.warning("Sheet KHO_PHAN_BO chưa có dữ liệu hợp lệ (từ dòng 3 trở đi)!")
        else:
            rows_to_append = []
            # Bỏ qua 2 dòng tiêu đề đầu tiên, quét dữ liệu từ dòng 3 (index 2)
            for idx, row in enumerate(kho_data[2:], start=1):
                if not any(row): continue
                
                # Trích xuất dữ liệu chuẩn theo đúng Index mảng Python (bắt đầu từ 0)
                ma_du_an   = row[0] if len(row) > 0 else ""  # KPB Cột A
                ten_tb     = row[3] if len(row) > 3 else ""  # KPB Cột D
                so_luong   = row[4] if len(row) > 4 else ""  # KPB Cột E
                don_vi     = row[5] if len(row) > 5 else ""  # KPB Cột F
                doi_nhan   = row[6] if len(row) > 6 else ""  # KPB Cột G
                dia_diem   = row[7] if len(row) > 7 else ""  # KPB Cột H
                
                # Xếp đúng vị trí từng cột từ A đến J trên sheet LAP_DAT:
                row_data = [
                    f"CV_{idx}",    # Cột A: Mã công việc
                    ma_du_an,       # Cột B: Mã dự án (A KPB)
                    doi_nhan,       # Cột C: Đội nhận thiết bị (G KPB)
                    ten_tb,         # Cột D: Tên thiết bị / Hàng hóa (D KPB)
                    so_luong,       # Cột E: Số lượng thiết bị lắp (E KPB)
                    don_vi,         # Cột F: ĐVT (F KPB)
                    dia_diem,       # Cột G: Địa điểm lắp (H KPB)
                    "Đang lắp đặt", # Cột H: Tình trạng thực hiện
                    "",             # Cột I: Thời gian hoàn thành
                    ""              # Cột J: Link Google Maps
                ]
                rows_to_append.append(row_data)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success(f"✅ Đã đồng bộ thành công {len(rows_to_append)} dòng từ Kho phân bổ sang Lắp đặt!")
            else:
                st.warning("Không tìm thấy dòng dữ liệu nào để đồng bộ.")
    except Exception as e:
        st.error(f"Lỗi khi thực thi: {e}")
