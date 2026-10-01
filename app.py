import gspread

def thuc_hien_phan_bo_va_dong_bo_python(credentials_path, spreadsheet_name):
    """
    [PYTHON_FIRST: ALLOCATION_SYNC]
    Đọc chuẩn xác theo vị trí cột thực tế của sheet DM_CHUAN:
    - Cột A (index 0): Mã dự án
    - Cột B (index 1): Mã thiết bị / SKU
    - Cột C (index 2): Tên thiết bị / Hàng hóa
    - Cột D (index 3): Đơn vị tính
    - Cột E (index 4): Số lượng
    - Cột F (index 5): Phân bổ cho các đơn vị (Đội nhận thiết bị)
    - Tích lũy dồn danh sách sang KHO_PHAN_BO bằng append_rows (Không xóa dữ liệu cũ).
    - Đồng bộ tồn kho tự động vào NHAP_KHO.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 1. Đọc dữ liệu từ DM_CHUAN
    sheet_dm = sh.worksheet("DM_CHUAN")
    values_dm = sheet_dm.get_all_values()
    if len(values_dm) < 3:
        print("[PYTHON_FIRST] Sheet DM_CHUAN không có dữ liệu!")
        return

    # Lấy bản đồ tên dự án từ DANH_SACH_DU_AN
    sheet_da = sh.worksheet("DANH_SACH_DU_AN")
    da_data = sheet_da.get_all_values()
    map_da = {}
    for row in da_data:
        m_da = str(row[0]).strip()
        t_da = str(row[1]).strip()
        if m_da and m_da != "Mã dự án" and m_da != "Mã đội":
            map_da[m_da] = t_da

    # Parse dữ liệu đúng theo vị trí cột thực tế của DM_CHUAN
    items = []
    units = []
    for i in range(2, len(values_dm)):
        row = values_dm[i]
        if len(row) < 6:
            continue
        ma_du_an = str(row[0]).strip()
        ma_tb    = str(row[1]).strip()
        ten_tb   = str(row[2]).strip()
        don_vi   = str(row[3]).strip()
        so_luong_raw = str(row[4]).strip()
        doi_nhan = str(row[5]).strip()
        
        if ma_tb and so_luong_raw != "":
            try:
                so_luong = float(so_luong_raw)
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
        print("[PYTHON_FIRST] Không tìm thấy item hợp lệ để phân bổ.")
        return
    if not units:
        units = [""]

    # Xếp dữ liệu chuẩn bị ghi xuống KHO_PHAN_BO
    rows_to_append = []
    for current_unit in units:
        for item in items:
            m_da = item["maDuAn"]
            t_da = map_da.get(m_da, m_da)
            rows_to_append.append([
                m_da, item["maTB"], t_da, item["tenTB"], item["soLuong"], item["donVi"], "", current_unit, ""
            ])

    # 2. Ghi nối tiếp (Append) vào KHO_PHAN_BO - Đảm bảo tích lũy, không xóa dữ liệu cũ
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    if rows_to_append:
        sheet_kho.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"[PYTHON_FIRST] Đã append thành công {len(rows_to_append)} dòng vào KHO_PHAN_BO!")

    # 3. Đồng bộ tồn kho sang NHAP_KHO (ALLOCATION_SYNC)
    sheet_nhap = sh.worksheet("NHAP_KHO")
    nhap_values = sheet_nhap.get_all_values()
    if len(nhap_values) < 3:
        return

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
        print("[ALLOCATION_SYNC] Đã đồng bộ tồn kho thành công vào NHAP_KHO!")
