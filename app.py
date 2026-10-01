import gspread

def tong_hop_va_ghi_ra_sheet(credentials_path, spreadsheet_name):
    """
    [TỔNG HỢP SỐ LIỆU KHO_PHAN_BO]
    - Quét toàn bộ lịch sử phân bổ từ sheet KHO_PHAN_BO.
    - Gom nhóm tổng số lượng theo từng Mã thiết bị (SKU) / Tên thiết bị / Đơn vị tính.
    - Tự động ghi trực tiếp kết quả ra sheet 'TONG_HOP' trên file Google Sheets để xem ngay lập tức.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 1. Đọc dữ liệu từ KHO_PHAN_BO
    try:
        sheet_kho = sh.worksheet("KHO_PHAN_BO")
    except gspread.exceptions.WorksheetNotFound:
        print("[LỖI] Không tìm thấy sheet KHO_PHAN_BO!")
        return
        
    kho_data = sheet_kho.get_all_values()
    if len(kho_data) < 3:
        print("[THÔNG BÁO] Sheet KHO_PHAN_BO chưa có dữ liệu tích lũy.")
        return

    # Tổng hợp số lượng theo SKU
    tong_hop_dict = {}
    
    for r in range(2, len(kho_data)):
        row = kho_data[r]
        if len(row) < 8:
            continue
            
        ma_sku  = str(row[1]).strip() # Cột B: Mã thiết bị / SKU
        ten_tb  = str(row[3]).strip() # Cột D: Tên thiết bị / Hàng hóa
        don_vi  = str(row[5]).strip() # Cột F: Đơn vị tính
        sl_raw  = str(row[4]).strip() # Cột E: Số lượng
        
        try:
            so_luong = float(sl_raw)
        except ValueError:
            so_luong = 0
            
        if ma_sku:
            key = ma_sku
            if key not in tong_hop_dict:
                tong_hop_dict[key] = {
                    "ma_sku": ma_sku,
                    "ten_tb": ten_tb,
                    "don_vi": don_vi,
                    "tong_sl": 0
                }
            tong_hop_dict[key]["tong_sl"] += so_luong

    # Chuẩn bị dữ liệu để ghi ra sheet TONG_HOP
    output_rows = [
        ["Mã thiết bị / SKU", "Tên thiết bị / Hàng hóa", "Đơn vị tính", "Tổng số lượng đã phân bổ"]
    ]
    
    for key, data in tong_hop_dict.items():
        output_rows.append([
            data["ma_sku"],
            data["ten_tb"],
            data["don_vi"],
            data["tong_sl"]
        ])

    # 2. Tạo hoặc cập nhật sheet TONG_HOP trên Google Sheets
    try:
        sheet_tong_hop = sh.worksheet("TONG_HOP")
        sheet_tong_hop.clear() # Xóa dữ liệu cũ để ghi mới hoàn toàn sạch sẽ
    except gspread.exceptions.WorksheetNotFound:
        sheet_tong_hop = sh.add_worksheet(title="TONG_HOP", rows=100, cols=10)
        
    # Ghi dữ liệu tổng hợp lên sheet TONG_HOP
    sheet_tong_hop.update("A1", output_rows, value_input_option='USER_ENTERED')
    print("[SUCCESS] Đã tổng hợp và cập nhật thành công dữ liệu ra sheet 'TONG_HOP' trên Google Sheets!")

if __name__ == "__main__":
    tong_hop_va_ghi_ra_sheet("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
