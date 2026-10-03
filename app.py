import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
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
    # Mở Google Sheets theo Key dự án
    sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
    spreadsheet = client.open_by_url(sheet_url)
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")

st.title("🚀 Hệ Thống Quản Lý Vận Chuyển & Lắp Đặt Dự Án")

# --- MODULE 1: ĐỒNG BỘ VẬN CHUYỂN (VAN_CHUYEN) ---
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

# --- MODULE 2: XỬ LÝ LẮP ĐẶT (LAP_DAT) ---
st.header("🛠️ Quản Lý Lắp Đặt")
if st.button("Khởi tạo danh sách Lắp đặt từ Vận chuyển"):
    try:
        sheet_vc = spreadsheet.worksheet("VAN_CHUYEN")
        sheet_ld = spreadsheet.worksheet("LAP_DAT")
        
        vc_data = sheet_vc.get_all_values()
        if len(vc_data) < 3:
            st.warning("Sheet VAN_CHUYEN chưa có dữ liệu!")
        else:
            rows_to_append = []
            for row in vc_data[2:]:
                if not any(row): continue
                ma_du_an = row[0]
                doi_nhan = row[1]
                ten_tb = row[2]
                so_luong = row[3]
                
                rows_to_append.append([
                    ma_du_an,
                    doi_nhan,
                    ten_tb,
                    so_luong,
                    doi_nhan,
                    "Đang lắp đặt",
                    ""
                ])
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Khởi tạo danh sách lắp đặt thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
