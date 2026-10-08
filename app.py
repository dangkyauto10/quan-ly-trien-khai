import pandas as pd
import streamlit as st

@st.cache_data(ttl=10)
def load_kho_phan_bo():
    """Đọc dữ liệu từ sheet KHO_PHAN_BO"""
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            # Tìm chính xác sheet KHO_PHAN_BO
            target_ws = None
            for ws in spreadsheet.worksheets():
                if "kho_phan_bo" in ws.title.lower() or "kho phân bổ" in ws.title.lower():
                    target_ws = ws
                    break
            if not target_ws:
                target_ws = spreadsheet.worksheets()[6] # Fallback nếu cần
            
            # Lấy toàn bộ records kèm theo số dòng (index) trên Google Sheet để ghi ngược lại chính xác
            rows = target_ws.get_all_records()
            return target_ws, pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
    return None, pd.DataFrame()

# --- GIAO DIỆN TRÊN WEBAPP ---
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
                # Lọc đúng các dòng dữ liệu của địa điểm đó
                df_filtered = df_doi[df_doi['Địa điểm nhận / lắp đặt'] == selected_diem]

                st.markdown("---")
                st.info(f"📍 **ĐỊA ĐIỂM:** {selected_diem}\n\n*Danh sách hàng hóa phân bổ cố định (Không được phép thay đổi số lượng):*")

                # Hiển thị danh sách thiết bị dạng cố định (Read-only) để kiểm đếm
                for idx, row in df_filtered.iterrows():
                    ten_tb = row.get('Tên thiết bị / Hạng mục', '')
                    so_luong = row.get('Số lượng', 0)
                    don_vi = row.get('Đơn vị tính', '')
                    current_status = row.get('Trạng thái Đón Nhận', 'Đang Vận Chuyển')

                    # Khung hiển thị thông tin từng mặt hàng (Khóa cứng số lượng)
                    st.text(f"• {ten_tb} | Số lượng: {so_luong} {don_vi} [ Trạng thái: {current_status} ]")

                st.markdown("---")
                st.subheader("Xác nhận hoàn thành nhiệm vụ hiện trường:")
                
                # Nút hành động tổng hoặc cập nhật trạng thái an toàn
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ ĐÃ GIAO XONG", use_container_width=True):
                        # Cập nhật an toàn chỉ vào cột Trạng thái Đón Nhận (Cột I) tương ứng các dòng đã lọc
                        try:
                            # row index trên pandas + 2 tương ứng với dòng trên Google Sheets (do có dòng tiêu đề header)
                            for original_index in df_filtered.index:
                                row_in_sheet = original_index + 2  # dòng tiêu đề là 1, data từ dòng 2
                                ws_kho.update_cell(row_in_sheet, 9, "Đã Giao hàng") # Cột I là cột số 9
                            st.success("Đã cập nhật trạng thái: ĐÃ GIAO XONG thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi cập nhật dữ liệu: {e}")

                with col2:
                    if st.button("🚀 ĐÃ LẮP XONG", use_container_width=True):
                        try:
                            for original_index in df_filtered.index:
                                row_in_sheet = original_index + 2
                                ws_kho.update_cell(row_in_sheet, 9, "Đã Giao Hàng tại Điểm") # Hoặc trạng thái lắp xong tùy ý anh
                            st.success("Đã cập nhật trạng thái: ĐÃ LẮP XONG thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi cập nhật dữ liệu: {e}")
