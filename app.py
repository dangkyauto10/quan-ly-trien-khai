import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_google_sheets_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client
    except Exception as e:
        st.error(f"Lỗi xác thực Google Sheets: {e}")
    return None

client = init_google_sheets_connection()
SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

st.markdown("### 🚀 TRUNG TÂM PHÂN BỔ & ĐIỀU HÀNH DỰ ÁN DA880")

if client:
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        
        # 1. Đọc sheet DANH_SACH_DU_AN: Col A = Mã dự án, Col B = Tên dự án
        sheet_da = spreadsheet.worksheet("DANH_SACH_DU_AN")
        data_da = sheet_da.get_all_values()
        map_da = {}
        for row in data_da[2:]: # Bỏ qua 2 dòng tiêu đề
            if len(row) >= 2 and row[0].strip():
                m_da = row[0].strip()
                t_da = row[1].strip() # Cột B: Tên dự án
                map_da[m_da] = t_da

        # 2. Đọc sheet DM_CHUAN
        sheet_dm = spreadsheet.worksheet("DM_CHUAN")
        data_dm = sheet_dm.get_all_values()
        
        st.markdown("#### 📋 Kiểm tra dữ liệu DM_CHUAN")
        items_list = []
        
        for row in data_dm[2:]: # Bỏ qua 2 dòng tiêu đề
            ma_da = row[0].strip() if len(row) > 0 else ""
            ma_tb = row[1].strip() if len(row) > 1 else ""
            ten_tb = row[2].strip() if len(row) > 2 else ""
            don_vi = row[3].strip() if len(row) > 3 else ""
            so_luong = row[4].strip() if len(row) > 4 else ""
            
            # Thu thập thiết bị chuẩn từ DM_CHUAN (từ TB-01 đến TB-05)
            if ma_tb and so_luong != "":
                items_list.append({
                    "ma_da": ma_da if ma_da else "DA880",
                    "ma_tb": ma_tb,
                    "ten_tb": ten_tb,
                    "don_vi": don_vi,
                    "so_luong": so_luong
                })

        if items_list:
            st.write(f"Tìm thấy **{len(items_list)}** mặt hàng thiết bị chuẩn trong DM_CHUAN.")
            
            if st.button("🚀 XÁC NHẬN VÀ ĐẨY DỮ LIỆU SANG KHO_PHAN_BO"):
                sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
                
                # Xóa sạch và tạo lại tiêu đề chuẩn cho KHO_PHAN_BO
                sheet_kho.clear()
                sheet_kho.append_row(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""])
                sheet_kho.append_row([
                    "Mã dự án",                   # Col A
                    "Mã thiết bị / SKU",         # Col B
                    "Tên dự án",                  # Col C (Quy chiếu chuẩn từ Col B DANH_SACH_DU_AN)
                    "Tên thiết bị / Hàng hóa",    # Col D (Lấy từ Col C DM_CHUAN)
                    "Số lượng",                   # Col E (Lấy từ Col E DM_CHUAN)
                    "Đơn vị tính",                # Col F (Lấy từ Col D DM_CHUAN)
                    "Đội nhận thiết bị",          # Col G (Để trống cho Admin tự phân bổ)
                    "Địa điểm vận chuyển lắp đặt",# Col H (Để trống)
                    "Trạng thái Giao Nhận"        # Col I (Để trống cho Admin xác nhận)
                ])
                
                rows_to_append = []
                for item in items_list:
                    m_da = item["ma_da"]
                    t_da = map_da.get(m_da, m_da) # Quy chiếu Tên dự án từ Col B DANH_SACH_DU_AN
                    
                    row_row = [
                        m_da,             # Col A: Mã dự án
                        item["ma_tb"],    # Col B: Mã thiết bị / SKU
                        t_da,             # Col C: Tên dự án (Quy chiếu chuẩn từ Col B DANH_SACH_DU_AN)
                        item["ten_tb"],   # Col D: Tên thiết bị / Hàng hóa
                        item["so_luong"], # Col E: Số lượng
                        item["don_vi"],   # Col F: Đơn vị tính
                        "",               # Col G: Đội nhận thiết bị (Để trống cho Admin tự phân bổ)
                        "",               # Col H: Địa điểm vận chuyển lắp đặt (Để trống)
                        ""                # Col I: Trạng thái Giao Nhận (Để trống)
                    ]
                    rows_to_append.append(row_row)
                
                if rows_to_append:
                    sheet_kho.append_rows(rows_to_append)
                    st.success(f"✅ Đã đẩy thành công {len(rows_to_append)} dòng sang KHO_PHAN_BO! Cột đội nhận, địa điểm và trạng thái để trống để Admin tự chủ động phân bổ.")
                else:
                    st.warning("⚠️ Không có dữ liệu để phân bổ.")
        else:
            st.warning("⚠️️ Chưa có danh mục thiết bị ở sheet DM_CHUAN.")
            
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
else:
    st.warning("⚠️ Chưa kết nối được Google Sheets.")
