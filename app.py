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
            for row in kho_data[2:]:
                if not any(row): continue
                
                # Lấy dữ liệu từ KHO_PHAN_BO (KPB) theo đúng index Python (bắt đầu từ 0)
                val_A = row[0] if len(row) > 0 else ""  # Mã dự án (A KPB)
                val_D = row[3] if len(row) > 3 else ""  # Tên thiết bị (D KPB)
                val_E = row[4] if len(row) > 4 else ""  # Số lượng (E KPB)
                val_F = row[5] if len(row) > 5 else ""  # ĐVT (F KPB)
                val_G = row[6] if len(row) > 6 else ""  # Đội nhận thiết bị (G KPB)
                val_H = row[7] if len(row) > 7 else ""  # Địa điểm lắp (H KPB)
                
                # Khởi tạo dòng 10 cột tương ứng từ A đến J trên sheet LAP_DAT
                new_row = [""] * 10
                new_row[1] = val_A  # Cột B: Mã dự án
                new_row[2] = val_G  # Cột C: Đội nhận thiết bị
                new_row[3] = val_D  # Cột D: Tên thiết bị / Hàng hóa
                new_row[4] = val_E  # Cột E: Số lượng thiết bị lắp
                new_row[5] = val_F  # Cột F: ĐVT
                new_row[6] = val_H  # Cột G: Địa điểm lắp
                new_row[7] = "Đang lắp đặt"  # Cột H: Tình trạng thực hiện
                
                rows_to_append.append(new_row)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ dữ liệu sang Lắp Đặt thành công với ánh xạ cột chuẩn xác!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
