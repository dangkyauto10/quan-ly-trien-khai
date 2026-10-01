import gspread

def run_python_first_allocation_sync(credentials_path, spreadsheet_name):
    """
    [PYTHON_FIRST: ALLOCATION_SYNC - GIẢI PHÁP CHUẨN XÁC ĐỘC LẬP]
    - Đọc dữ liệu từ DM_CHUAN (Cột A đến F).
    - Append dữ liệu nối tiếp vào KHO_PHAN_BO (Bảo toàn 100% lịch sử cũ).
    - Đồng bộ tồn kho trừ lùi vào Cột F của NHAP_KHO.
    """
    # 1. Khởi tạo kết nối gspread
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 2. Lấy dữ liệu từ DM_CHUAN
    sheet_dm = sh.worksheet("DM_CHUAN")
    dm_values = sheet_dm.get_all_values()
    if len(dm_values) < 3:
        print("[PYTHON_FIRST] Sheet DM_CHUAN chưa có dữ liệu hợp lệ từ dòng 3.")
        return

    # Lấy map tên dự án từ DANH_SACH_DU_AN
    sheet_da = sh.worksheet("DANH_SACH_DU_AN")
    da_values = sheet_da.get_all_values()
    map_da = {}
    for row in da_values:
        m_da = str(row[0]).strip() if len(row) > 0 else ""
        t_da = str(row[1]).strip() if len(row) > 1 else ""
        if m_da and m_da != "Mã dự án" and m_da != "Mã đội":
            map_da[m_da] = t_da

    # 3. Quét và phân tách các dòng phân bổ từ DM_CHUAN
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
        print("[PYTHON_FIRST] Không tìm thấy hàng hóa nào để phân bổ.")
        return
        
    if not units:
        units = [""]

    # 4. Xây dựng danh sách dòng mới cần append
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
                "",      # Cột G: Đội nhận thiết bị (để trống hoặc điền tùy ý)
                u,       # Cột H: Địa điểm / Đơn vị nhận
                ""       # Cột I: Trạng thái Giao Nhận
            ])

    # 5. Thực hiện APPEND vào KHO_PHAN_BO (Tích lũy trọn vẹn, không bao giờ xóa dữ liệu cũ)
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    if rows_to_append:
        sheet_kho.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"[PYTHON_FIRST] Đã append thành công {len(rows_to_append)} dòng mới vào KHO_PHAN_BO.")

    # 6. ALLOCATION_SYNC: Đồng bộ tính toán tồn kho sang sheet NHAP_KHO (Cột F)
    sheet_nhap = sh.worksheet("NHAP_KHO")
    nhap_values = sheet_nhap.get_all_values()
    if len(nhap_values) < 3:
        return

    # Lấy toàn bộ dữ liệu lịch sử hiện tại của KHO_PHAN_BO để tính tổng đã phân bổ
    kho_all = sheet_kho.get_all_values()
    phan_bo_map = {}
    if len(kho_all) >= 3:
        for r in range(2, len(kho_all)):
            r_data = kho_all[r]
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

    # Cập nhật giá trị tồn kho tĩnh vào Cột F của NHAP_KHO
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
        print("[ALLOCATION_SYNC] Đã đồng bộ tồn kho thành công vào NHAP_KHO qua Python.")

if __name__ == "__main__":
    # Thay đường dẫn service_account và tên spreadsheet thực tế của anh khi chạy
    run_python_first_allocation_sync("path/to/credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
