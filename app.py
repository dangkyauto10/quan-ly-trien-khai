import gspread

def giai_phap_phan_bo_tich_luy_kha_thi(credentials_path, spreadsheet_name):
    """
    [PHƯƠNG ÁN KHẢ THI TỐI ƯU - PYTHON_FIRST: ALLOCATION_SYNC]
    - Quét trực tiếp toàn bộ dữ liệu hiện tại của KHO_PHAN_BO để xác định chính xác dòng cuối cùng thực tế.
    - Tuyệt đối KHÔNG BAO GIỜ xóa dữ liệu cũ.
    - Tự động tính toán dải ô từ dòng tiếp theo (next_row) để ghi nối tiếp (Append) dữ liệu mới.
    - Đồng bộ tồn kho chính xác vào Cột F của NHAP_KHO.
    """
    # 1. Kết nối Google Sheets
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 2. Đọc dữ liệu nguồn từ DM_CHUAN
    sheet_dm = sh.worksheet("DM_CHUAN")
    dm_values = sheet_dm.get_all_values()
    if len(dm_values) < 3:
        print("[PYTHON_FIRST] Sheet DM_CHUAN chưa có dữ liệu phân bổ.")
        return

    # Lấy bản đồ tên dự án từ DANH_SACH_DU_AN
    sheet_da = sh.worksheet("DANH_SACH_DU_AN")
    da_values = sheet_da.get_all_values()
    map_da = {}
    for row in da_values:
        m_da = str(row[0]).strip() if len(row) > 0 else ""
        t_da = str(row[1]).strip() if len(row) > 1 else ""
        if m_da and m_da != "Mã dự án" and m_da != "Mã đội":
            map_da[m_da] = t_da

    # 3. Phân tách danh sách thiết bị và điểm nhận từ DM_CHUAN (Đúng chuẩn cột A->F)
    items = []
    units = []
    
    for i in range(2, len(dm_values)):
        row = dm_values[i]
        if len(row) < 6:
            continue
            
        ma_du_an = str(row[0]).strip()
        ma_tb    = str(row[1]).strip() # SKU / Mã thiết bị
        ten_tb   = str(row[2]).strip()
        don_vi   = str(row[3]).strip()
        sl_raw   = str(row[4]).strip() # Số lượng
        doi_nhan = str(row[5]).strip() # Phân bổ cho các đơn vị
        
        if ma_tb and sl_raw != "":
            try:
                so_luong = float(sl_raw)
            except ValueError:
                continue
                
            items.append({
                "maDuAn": ma_du_an if ma_du_an else "DA880",
                "maTB": ma_tb,
                "tenTB": ten_tb,
                "donVi": don_vi,
                "soLuong": so_luong
            })
            
        if doi_nhan and doi_nhan.lower() != "nan":
            parts = doi_nhan.split(",")
            for p in parts:
                u_clean = p.strip()
                if u_clean and u_clean not in units:
                    units.append(u_clean)

    if not items:
        print("[PYTHON_FIRST] Không có item hợp lệ để phân bổ.")
        return
        
    if not units:
        units = [""]

    # Xây dựng mảng dữ liệu chuẩn bị ghi
    rows_to_append = []
    for u in units:
        for item in items:
            m_da = item["maDuAn"]
            t_da = map_da.get(m_da, m_da)
            rows_to_append.append([
                m_da, 
                item["maTB"], 
                t_da, 
                item["tenTB"], 
                item["soLuong"], 
                item["donVi"], 
                "",      # Cột G
                u,       # Cột H: Đơn vị / Địa điểm nhận
                ""       # Cột I
            ])

    if not rows_to_append:
        return

    # 4. THỰC HIỆN TÍCH LŨY NỐI TIẾP AN TOÀN TUYỆT ĐỐI (KHÔNG BAO GIỜ XÓA DỮ LIỆU CŨ)
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    
    # Lấy toàn bộ giá trị hiện có trên sheet KHO_PHAN_BO để đếm chính xác số dòng đang có
    existing_kho_data = sheet_kho.get_all_values()
    current_total_rows = len(existing_kho_data)
    
    # Xác định dòng bắt đầu ghi mới (Nếu bảng trống hoặc chỉ có tiêu đề hàng 1, 2 thì bắt đầu từ dòng 3)
    next_row = current_total_rows + 1
    if next_row < 3:
        next_row = 3
        
    num_rows = len(rows_to_append)
    num_cols = len(rows_to_append[0])
    
    # Tính toán dải ô A1 chính xác (Ví dụ: từ A8 đến I15)
    end_col_letter = gspread.utils.rowcol_to_a1(1, num_cols).rstrip('1')
    range_string = f"A{next_row}:{end_col_letter}{next_row + num_rows - 1}"
    
    # Ghi dữ liệu nối tiếp vào đúng vùng trống phía dưới cùng của bảng
    sheet_kho.update(range_string, rows_to_append, value_input_option='USER_ENTERED')
    print(f"[PYTHON_FIRST] Đã ghi nối tiếp thành công {num_rows} dòng từ dòng {next_row} vào KHO_PHAN_BO. Bảo toàn 100% dữ liệu cũ!")

    # 5. ALLOCATION_SYNC: Đồng bộ tồn kho trừ lùi vào Cột F của sheet NHAP_KHO
    sheet_nhap = sh.worksheet("NHAP_KHO")
    nhap_values = sheet_nhap.get_all_values()
    if len(nhap_values) < 3:
        return

    # Quét lại toàn bộ KHO_PHAN_BO sau khi đã nối tiếp để tính tổng đã phân bổ
    updated_kho_all = sheet_kho.get_all_values()
    phan_bo_map = {}
    if len(updated_kho_all) >= 3:
        for r in range(2, len(updated_kho_all)):
            r_data = updated_kho_all[r]
            if len(r_data) >= 5:
                m_da = str(r_data[0]).strip()
                m_sku = str(r_data[1]).strip()
                try:
                    sl_pb = float(r_data[4])
                except ValueError:
                    sl_pb = 0
                if m_sku:
                    key = f"{m_da}_{m_sku}"
                    phan_bo_map[key] = phan_bo_map.get(key, 0) + sl_pb

    # Cập nhật tồn kho vào Cột F của NHAP_KHO
    ton_kho_values = []
    for r in range(2, len(nhap_values)):
        row = nhap_values[r]
        m_da_nhap = str(row[0]).strip() if len(row) > 0 else ""
        m_sku_nhap = str(row[1]).strip() if len(row) > 1 else ""
        tong_nhap_raw = str(row[4]).strip() if len(row) > 4 else "0"
        
        try:
            tong_nhap = float(tong_nhap_raw)
        except ValueError:
            tong_nhap = 0

        if m_sku_nhap:
            lookup_key = f"{m_da_nhap}_{m_sku_nhap}"
            da_phan_bo = phan_bo_map.get(lookup_key, 0)
            ton_kho = tong_nhap - da_phan_bo
            ton_kho_values.append([ton_kho])
        else:
            ton_kho_values.append([""])

    if ton_kho_values:
        sheet_nhap.update(f"F3:F{2 + len(ton_kho_values)}", ton_kho_values, value_input_option='USER_ENTERED')
        print(f"[ALLOCATION_SYNC] Đã đồng bộ tồn kho thành công vào NHAP_KHO.")

if __name__ == "__main__":
    giai_phap_phan_bo_tich_luy_kha_thi("path/to/credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
