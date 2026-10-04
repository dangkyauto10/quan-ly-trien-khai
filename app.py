import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

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

st.title("🚀 Hệ Thống Quản Lý Vận Chuyển & Lắp Đặt Dự Án")

# --- MODULE 1: QUẢN LÝ VẬN CHUYỂN (VAN_CHUYEN) ---
st.header("📦 Quản Lý Vận Chuyển")
if st.button("Đồng bộ dữ liệu từ Kho phân bổ sang Vận chuyển"):
    try:
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        sheet_vc = spreadsheet.worksheet("VAN_CHUYEN")
        
        kho_data = sheet_kho.get_all_values()
        if len(kho_data) < 3:
            st.warning("Sheet KHO_PHAN_BO chưa có dữ liệu!")
        else:
            rows_to_append = []
            for row in kho_data[2:]:
                if not any(row): continue
                ma_du_an = row[0]
                doi_nhan = row[7]
                ten_tb = row[3]
                so_luong = row[4]
                
                rows_to_append.append([
                    ma_du_an,
                    doi_nhan,
                    ten_tb,
                    so_luong,
                    "Đang vận chuyển",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
            
            if rows_to_append:
                sheet_vc.append_rows(rows_to_append)
                st.success("✅ Đồng bộ vận chuyển thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")

# --- MODULE 2: QUẢN LÝ LẮP ĐẶT (LAP_DAT) ---
st.header("🛠️ Quản Lý Lắp Đặt")
if st.button("Đồng bộ dữ liệu sang Lắp Đặt"):
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
                
                # Trích xuất dữ liệu từ KHO_PHAN_BO (KPB)
                ma_du_an = row[0] if len(row) > 0 else ""       # Cột A KPB (Mã dự án)
                ten_tb = row[3] if len(row) > 3 else ""         # Cột D KPB (Tên thiết bị)
                so_luong = row[4] if len(row) > 4 else ""       # Cột E KPB (Số lượng)
                don_vi_tinh = row[5] if len(row) > 5 else ""    # Cột F KPB (ĐVT)
                doi_nhan = row[7] if len(row) > 7 else ""       # Cột H KPB (Đội nhận thiết bị)
                dia_diem = row[7] if len(row) > 7 else ""       # Cột H KPB (Địa điểm lắp)
                
                # Khởi tạo đúng 10 cột khớp 100% với tiêu đề từ A đến J trên sheet LAP_DAT:
                row_data = [
                    f"CV_{idx}",    # A: Mã công việc
                    ma_du_an,       # B: Mã dự án
                    doi_nhan,       # C: Đội nhận thiết bị
                    ten_tb,         # D: Tên thiết bị / Hàng hóa
                    so_luong,       # E: Số lượng thiết bị lắp
                    don_vi_tinh,    # F: ĐVT
                    dia_diem,       # G: Địa điểm lắp
                    "Đang lắp đặt", # H: Tình trạng thực hiện
                    "",             # I: Thời gian hoàn thành
                    ""              # J: Link Google Maps
                ]
                rows_to_append.append(row_data)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ sang Lắp Đặt chuẩn xác 100% từng cột!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
