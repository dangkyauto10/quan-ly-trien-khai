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
        
        # 1. Đọc sheet DANH_SACH_DU_AN: Cột A là Mã dự án, Cột B là Tên dự án (dùng để quy chiếu vào Cột C KHO_PHAN_BO)
        sheet_da = spreadsheet.worksheet("DANH_SACH_DU_AN")
        data_da = sheet_da.get_all_values()
        map_da = {}
        for row in data_da[2:]: # Bỏ qua 2 dòng tiêu đề
            if len(row) >= 2 and row[0].strip():
                ma_du_an_key = row[0].strip()
                ten_du_an_val = row[1].strip() # Lấy chuẩn cột B của DANH_SACH_DU_AN
                map_da[ma_du_an_key] = ten_du_an_val

        # 2. Đọc sheet DM_CHUAN
        sheet_dm = spreadsheet.worksheet("DM_CHUAN")
        data_dm = sheet_dm.get_all_values()
        
        st.markdown("#### 📋 Kiểm tra danh mục chuẩn thiết bị (DM_CHUAN)")
        items_list = []
        units_set = set()
        
        for row in data_dm[2:]: # Bỏ qua 2 dòng tiêu đề
            if len(row) >= 6:
                ma_da = row[0].strip()       # Col A: Mã dự án
                ma_tb = row[1].strip()       # Col B: Mã SKU
                ten_tb = row[2].strip()      # Col C: Tên thiết bị / Hàng hóa
                don_vi_tinh = row[3].strip() # Col D: Đơn vị tính
                so_luong = row[4].strip()    # Col E: Số lượng
                don_vi_nhan_str = row[5].strip() # Col F: Đội nhận / Xã
                
                if ma_tb and so_luong != "":
                    items_list.append({
                        "ma_da": ma_da,
                        "ma_tb": ma_tb,
                        "ten_tb": ten_tb,
                        "don_vi_tinh": don_vi_tinh,
                        "so_luong": so_luong
                    })
                
                if don_vi_nhan_str and don_vi_nhan_str.lower() != "nan":
                    for dv in don_vi_nhan_str.split(","):
                        dv_clean = dv.strip()
                        if dv_clean:
                            units_set.add(dv_clean)

        if items_list and units_set:
            df_preview = pd.DataFrame(items_list)
            st.dataframe(df_preview, use_container_width=True)
            st.info(f"📍 Các đơn vị nhận phân bổ: {list(units_set)}")
            
            if st.button("🚀 THỰC HIỆN PHÂN BỔ VÀ ĐẨY DỮ LIỆU SANG KHO PHÂN BỔ"):
                sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
                
                # Làm sạch sheet KHO_PHAN_BO trước khi ghi mới
                sheet_kho.clear()
                sheet_kho.append_row(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""])
                sheet_kho.append_row([
                    "Mã dự án",                   # Col A
                    "Mã thiết bị / SKU",         # Col B
                    "Tên dự án",                  # Col C (Quy chiếu chuẩn từ Cột B DANH_SACH_DU_AN)
                    "Tên thiết bị / Hàng hóa",    # Col D (Lấy từ Col C DM_CHUAN)
                    "Số lượng",                   # Col E (Lấy từ Col E DM_CHUAN)
                    "Đơn vị tính",                # Col F (Lấy từ Col D DM_CHUAN)
                    "Đội nhận thiết bị",          # Col G (Lấy từ Col F DM_CHUAN)
                    "Địa điểm vận chuyển lắp đặt",# Col H (Lấy theo đơn vị nhận)
                    "Trạng thái Giao Nhận"        # Col I (Để trống cho Admin xác nhận)
                ])
                
                rows_to_append = []
                # Phân bổ chuẩn: Mỗi xã/đơn vị nhận ĐẦY ĐỦ trọn bộ tất cả các mặt hàng với số lượng y hệt nhau
                for dv_nhan in sorted(list(units_set)):
                    for item in items_list:
                        m_da = item["ma_da"]
                        # Bắt buộc quy chiếu Tên dự án từ cột B của DANH_SACH_DU_AN qua map_da
                        t_da = map_da.get(m_da, m_da) 
                        
                        row_row = [
                            m_da,                   # Col A: Mã dự án
                            item["ma_tb"],          # Col B: Mã SKU
                            t_da,                   # Col C: Tên dự án (Lấy chuẩn từ Cột B DANH_SACH_DU_AN)
                            item["ten_tb"],         # Col D: Tên thiết bị / Hàng hóa
                            item["so_luong"],       # Col E: Số lượng
                            item["don_vi_tinh"],    # Col F: Đơn vị tính
                            dv_nhan,                # Col G: Đội nhận thiết bị / xã
                            dv_nhan,                # Col H: Địa điểm vận chuyển lắp đặt (theo danh mục đơn vị)
                            ""                      # Col I: Trạng thái Giao Nhận (để trống)
                        ]
                        rows_to_append.append(row_row)
                
                if rows_to_append:
                    sheet_kho.append_rows(rows_to_append)
                    st.success(f"✅ Đã phân bổ thành công {len(rows_to_append)} dòng sang sheet KHO_PHAN_BO! Cột C đã quy chiếu chuẩn từ Cột B DANH_SACH_DU_AN.")
                else:
                    st.warning("⚠️ Không có dữ liệu hợp lệ để phân bổ.")
        else:
            st.info("Chưa có đủ danh mục thiết bị hoặc chưa khai báo đơn vị nhận ở cột F.")
            
    except Exception as e:
        st.error(f"❌ Lỗi xử lý dữ liệu hệ thống: {e}")
else:
    st.warning("⚠️ Vui lòng cấu hình kết nối Google Sheets trong Secret.")
