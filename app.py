import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Hệ thống Điều hành Đa Dự Án Hiện Trường", page_icon="📊", layout="centered")

SPREADSHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

# --- HÀM KẾT NỐI GOOGLE SHEETS AN TOÀN (KHẮC PHỤC LỖI TRÊN) ---
@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi xác thực Google Service Account: {e}")
    return None

# --- HÀM ĐỌC SHEET KHO_PHAN_BO ---
@st.cache_data(ttl=10)
def load_kho_phan_bo():
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "kho_phan_bo" in ws.title.lower() or "kho phân bổ" in ws.title.lower():
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[6] # Fallback lấy sheet Kho phân bổ
            
            rows = target_ws.get_all_records()
            return target_ws, pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu Google Sheets: {e}")
    return None, pd.DataFrame()

# --- GIAO DIỆN ỨNG DỤNG CHÍNH ---
st.markdown("<h2 style='text-align: center; color: #003366;'>HỆ THỐNG ĐIỀU HÀNH ĐA DỰ ÁN HIỆN TRƯỜNG</h2>", unsafe_allow_html=True)
st.markdown("---")

ws_kho, df_kho = load_kho_phan_bo()

if not df_kho.empty:
    # 1. Chọn Dự án
    projects = df_kho['Tên dự án'].unique().tolist() if 'Tên dự án' in df_kho.columns else []
    selected_project = st.selectbox("CHỌN DỰ ÁN TRIỂN KHAI *", options=["-- Chọn dự án --"] + projects)

    if selected_project != "-- Chọn dự án --":
        df_proj = df_kho[df_kho['Tên dự án'] == selected_project]

        # 2. Chọn Đội vận chuyển (Cột G)
        doi_list = df_proj['Đội vận chuyển thiết bị'].unique().tolist() if 'Đội vận chuyển thiết bị' in df_proj.columns else []
        selected_doi = st.selectbox("TÊN ĐỘI VẬN CHUYỂN / LẮP ĐẶT *", options=["-- Chọn tên đội --"] + doi_list)

        if selected_doi != "-- Chọn tên đội --":
            df_doi = df_proj[df_proj['Đội vận chuyển thiết bị'] == selected_doi]

            # 3. Chọn Địa điểm nhận (Cột H)
            diem_list = df_doi['Địa điểm nhận / lắp đặt'].unique().tolist() if 'Địa điểm nhận / lắp đặt' in df_doi.columns else []
            selected_diem = st.selectbox("ĐIỂM GIAO HÀNG & LẮP ĐẶT *", options=["-- Chọn địa điểm --"] + diem_list)

            if selected_diem != "-- Chọn địa điểm --":
                df_filtered = df_doi[df_doi['Địa điểm nhận / lắp đặt'] == selected_diem]

                st.markdown("---")
                st.info(f"📍 **ĐỊA ĐIỂM ĐÃ CHỌN:** {selected_diem}\n\n*Danh mục thiết bị phân bổ cố định (Không được phép thay đổi số lượng):*")

                # Hiển thị danh sách thiết bị cố định (Read-only) để anh em kiểm đếm
                for idx, row in df_filtered.iterrows():
                    ten_tb = row.get('Tên thiết bị / Hạng mục', '')
                    so_luong = row.get('Số lượng', 0)
                    don_vi = row.get('Đơn vị tính', '')
                    current_status = row.get('Trạng thái Đón Nhận', 'Đang Vận Chuyển')

                    st.text(f"• {ten_tb} | Số lượng: {so_luong} {don_vi} [Trạng thái: {current_status}]")

                st.markdown("---")
                
                # Nút hành động cập nhật trạng thái an toàn
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ ĐÃ GIAO XONG", use_container_width=True):
                        try:
                            for original_index in df_filtered.index:
                                row_in_sheet = original_index + 2  # Dòng header là 1, data bắt đầu từ dòng 2
                                ws_kho.update_cell(row_in_sheet, 9, "Đã Giao hàng") # Cột I là cột số 9
                            st.success("Đã cập nhật trạng thái: ĐÃ GIAO XONG thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi cập nhật: {e}")

                with col2:
                    if st.button("🚀 ĐÃ LẮP XONG", use_container_width=True):
                        try:
                            for original_index in df_filtered.index:
                                row_in_sheet = original_index + 2
                                ws_kho.update_cell(row_in_sheet, 9, "Đã Giao Hàng tại Điểm")
                            st.success("Đã cập nhật trạng thái: ĐÃ LẮP XONG thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi cập nhật: {e}")
else:
    st.warning("Đang tải dữ liệu hoặc chưa kết nối được với Google Sheets. Vui lòng kiểm tra lại cấu hình kho phân bổ.")
