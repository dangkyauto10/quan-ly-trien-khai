import gspread

def run_python_first_allocation(credentials_path, spreadsheet_name):
    """
    [PYTHON_FIRST: ALLOCATION_SYNC - ĐỘC LẬP TRÊN PYTHON]
    - Đọc dữ liệu chuẩn từ DM_CHUAN (Cột A đến F).
    - Append nối tiếp vào KHO_PHAN_BO (Tích lũy dồn lịch sử, bảo toàn 100% dữ liệu cũ).
    - Đồng bộ tồn kho trừ lùi tự động vào Cột F của NHAP_KHO.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 1. Đọc dữ liệu từ DM_CHUAN
    sheet_dm = sh.worksheet("DM_CHUAN")
    dm_values = sheet_dm.get_all_values()
    if len(dm_values) < 3:
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

    # 2. Xử lý bóc tách thiết bị và điểm nhận
    items = []
    units = []
    for i in range(2, len(dm_values)):
        row = dm_values[i]
        if len(row) < 6:
            continue
        ma_du_an = str(row[0]).strip()
        ma_tb    = str(row[1]).strip()
        ten_tb   = str(row[2]).strip()
        don_vi   = str(row[3]).strip()
        sl_raw   = str(row[4]).strip()
        doi_nhan = str(row[5]).strip()
        
        if ma_tb and sl_raw != "":
            try:
                so_luong = float(sl_raw)
            except ValueError:
                continue
            items.append({
                "maDuAn": ma_du_an if ma_du_an else "DA880",
                "maTB": ma_tb, "tenTB": ten_tb, "donVi": don_vi, "soLuong": so_luong
            })
            
        if doi_nhan and doi_nhan.lower() != "nan":
            for p in doi_nhan.split(","):
                u_clean = p.strip()
                if u_clean and u_clean not in units:
                    units.append(u_clean)

    if not items:
        return
    if not units:
        units = [""]

    # Xây dựng danh sách dòng mới cần append
    rows_to_append = []
    for u in units:
        for item in items:
            m_da = item["maDuAn"]
            t_da = map_da.get(m_da, m_da)
            rows_to_append.append([
                m_da, item["maTB"], t_da, item["tenTB"], item["soLuong"], item["donVi"], "", u, ""
            ])

    # 3. APPEND NỐI TIẾP VÀO KHO_PHAN_BO (Tích lũy trọn vẹn, không xóa dữ liệu cũ)
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    if rows_to_append:
        sheet_kho.append_rows(rows_to_append, value_input_option='USER_ENTERED')

    # 4. ALLOCATION_SYNC: Đồng bộ tồn kho trừ lùi vào Cột F của NHAP_KHO
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
        print("[SUCCESS] Phân bổ tích lũy và đồng bộ tồn kho hoàn tất!")

if __name__ == "__main__":
    run_python_first_allocation("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
