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
        
        # 1. Đọc sheet DANH_SACH_DU_AN để quy chiếu Tên dự án
        sheet_da = spreadsheet.worksheet("DANH_SACH_DU_AN")
        data_da = sheet_da.get_all_values()
        map_da = {}
        for row in data_da[2:]: # Bỏ qua tiêu đề
            if len(row) >= 2 and row[0].strip():
                map_da[row[0].strip()] = row[1].strip()

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
                ten_tb = row[2].strip()      # Col C: Tên thiết bị
                don_vi_tinh = row[3].strip() # Col D: Đơn vị tính
                so_luong = row[4].strip()    # Col E: Số lượng
                don_vi_nhan_str = row[5].strip() # Col F: Đội nhận / Xã
                
                # Thu thập danh mục hàng hóa hợp lệ
                if ma_tb and so_luong != "":
                    items_list.append({
                        "ma_da": ma_da,
                        "ma_tb": ma_tb,
                        "ten_tb": ten_tb,
                        "don_vi_tinh": don_vi_tinh,
                        "so_luong": so_luong
                    })
                
                # Thu thập toàn bộ các xã / đơn vị nhận ở cột F (hỗ trợ phân tách dấu phẩy)
                if don_vi_nhan_str and don_vi_nhan_str.lower() != "nan":
                    for dv in don_vi_nhan_str.split(","):
                        dv_clean = dv.strip()
                        if dv_clean:
                            units_set.add(dv_clean)

        if items_list and units_set:
            df_preview = pd.DataFrame(items_list)
            st.dataframe(df_preview, use_container_width=True)
            st.info(f"Đã nhận diện các đơn vị nhận: {list(units_set)}")
            
            if st.button("📍 THỰC HIỆN PHÂN BỔ VÀ ĐẨY DỮ LIỆU SANG KHO PHÂN BỔ"):
                sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
                
                rows_to_append = []
                # Phân bổ: Từng xã/đơn vị nhận được ĐẦY ĐỦ trọn bộ tất cả các mặt hàng với số lượng y hệt nhau
                for dv_nhan in sorted(list(units_set)):
                    for item in items_list:
                        m_da = item["ma_da"]
                        t_da = map_da.get(m_da, m_da) # Tra cứu tên dự án
                        
                        # Ánh xạ chuẩn xác từng cột theo đúng phom kho yêu cầu:
                        # Col A: Mã dự án
                        # Col B: Mã thiết bị / SKU
                        # Col C: Tên dự án (quy chiếu từ DANH_SACH_DU_AN)
                        # Col D: Tên thiết bị / Hàng hóa
                        # Col E: Số lượng
                        # Col F: Đơn vị tính
                        # Col G: Đội nhận thiết bị
                        # Col H: Địa điểm vận chuyển lắp đặt (lấy theo danh mục đơn vị phân bổ)
                        # Col I: Trạng thái Giao Nhận (để trống cho AD xác nhận)
                        row_row = [
                            m_da,                   # Col A
                            item["ma_tb"],          # Col B
                            t_da,                   # Col C
                            item["ten_tb"],         # Col D
                            item["so_luong"],       # Col E
                            item["don_vi_tinh"],    # Col F
                            dv_nhan,                # Col G
                            dv_nhan,                # Col H (Địa điểm theo đúng danh mục)
                            ""                      # Col I (Trạng thái để trống)
                        ]
                        rows_to_append.append(row_row)
                
                if rows_to_append:
                    # Ghi đè hoặc append vào KHO_PHAN_BO
                    sheet_kho.append_rows(rows_to_append)
                    st.success(f"✅ Đã phân bổ thành công {len(rows_to_append)} dòng sang sheet KHO_PHAN_BO! Mỗi đơn vị nhận trọn bộ đầy đủ mặt hàng với số lượng chuẩn xác.")
                else:
                    st.warning("⚠️ Không có dữ liệu hợp lệ để phân bổ.")
        else:
            st.info("Chưa có đủ danh mục thiết bị hoặc chưa khai báo đơn vị nhận ở cột F.")
            
    except Exception as e:
        st.error(f"❌ Lỗi xử lý dữ liệu hệ thống: {e}")
else:
    st.warning("⚠️ Vui lòng cấu hình kết nối Google Sheets trong Secret.")
