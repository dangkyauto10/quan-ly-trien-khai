import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

# 1. Kết nối Google Sheets qua Service Account
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
        
        # Đọc sheet DANH_SACH_DU_AN để quy chiếu Tên dự án
        sheet_da = spreadsheet.worksheet("DANH_SACH_DU_AN")
        data_da = sheet_da.get_all_values()
        map_da = {}
        for row in data_da[2:]: # Bỏ qua tiêu đề
            if len(row) >= 2 and row[0].strip():
                map_da[row[0].strip()] = row[1].strip()

        # Đọc sheet DM_CHUAN để lấy danh mục thiết bị mẫu
        sheet_dm = spreadsheet.worksheet("DM_CHUAN")
        data_dm = sheet_dm.get_all_values()
        
        st.markdown("#### 📋 Kiểm tra danh mục chuẩn thiết bị (DM_CHUAN)")
        items_list = []
        danh_sach_don_vi = []
        
        for row in data_dm[2:]: # Bỏ qua dòng tiêu đề
            if len(row) >= 6:
                ma_da = row[0].strip()
                ma_tb = row[1].strip()
                ten_tb = row[2].strip()
                don_vi_tinh = row[3].strip()
                so_luong = row[4].strip()
                don_vi_nhan_str = row[5].strip()
                
                if ma_tb and so_luong:
                    items_list.append({
                        "ma_da": ma_da,
                        "ma_tb": ma_tb,
                        "ten_tb": ten_tb,
                        "don_vi_tinh": don_vi_tinh,
                        "so_luong": so_luong
                    })
                
                if don_vi_nhan_str:
                    for dv in don_vi_nhan_str.split(","):
                        dv_clean = dv.strip()
                        if dv_clean and dv_clean not in danh_sach_don_vi:
                            danh_sach_don_vi.append(dv_clean)

        if items_list:
            df_preview = pd.DataFrame(items_list)
            st.dataframe(df_preview, use_container_width=True)
            
            if st.button("📍 XÁC NHẬN PHÂN BỔ VÀ ĐẨY DỮ LIỆU SANG KHO PHÂN BỔ"):
                sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
                
                rows_to_append = []
                for dv_nhan in danh_sach_don_vi:
                    for item in items_list:
                        m_da = item["ma_da"]
                        t_da = map_da.get(m_da, m_da)
                        
                        # Cấu trúc chuẩn xác từng cột của KHO_PHAN_BO:
                        # Col A: Mã dự án
                        # Col B: Mã SKU
                        # Col C: Tên dự án (quy chiếu)
                        # Col D: Tên thiết bị / Hàng hóa
                        # Col E: Số lượng
                        # Col F: Đơn vị tính
                        # Col G: Đội nhận thiết bị
                        # Col H: Địa điểm vận chuyển lắp đặt (Lấy chính xác theo danh mục đơn vị phân bổ)
                        # Col I: Trạng thái Giao Nhận (để trống cho AD xác nhận)
                        row_row = [
                            m_da,
                            item["ma_tb"],
                            t_da,
                            item["ten_tb"],
                            item["so_luong"],
                            item["don_vi_tinh"],
                            dv_nhan,
                            dv_nhan, # Địa điểm lấy theo danh mục đơn vị phân bổ
                            ""       # Trạng thái để trống
                        ]
                        rows_to_append.append(row_row)
                
                if rows_to_append:
                    sheet_kho.append_rows(rows_to_append)
                    st.success(f"✅ Đã phân bổ thành công {len(rows_to_append)} dòng sang sheet KHO_PHAN_BO với đầy đủ địa điểm theo danh mục!")
                else:
                    st.warning("⚠️ Không có dữ liệu hợp lệ để phân bổ.")
        else:
            st.info("Chưa có dữ liệu thiết bị trong sheet DM_CHUAN.")
            
    except Exception as e:
        st.error(f"❌ Lỗi xử lý dữ liệu hệ thống: {e}")
else:
    st.warning("⚠️ Vui lòng cấu hình kết nối Google Sheets trong Secret.")
