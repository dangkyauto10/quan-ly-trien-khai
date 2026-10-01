import gspread

def tong_hop_kho_phan_bo(credentials_path, spreadsheet_name):
    """
    [TỔNG HỢP SỐ LIỆU KHO_PHAN_BO]
    - Đọc toàn bộ lịch sử phân bổ hiện tại từ sheet KHO_PHAN_BO.
    - Tổng hợp tổng số lượng hàng hóa đã phân bổ theo từng Mã thiết bị (SKU) và từng Đơn vị/Địa điểm nhận.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    kho_data = sheet_kho.get_all_values()
    
    if len(kho_data) < 3:
        print("[THÔNG BÁO] Sheet KHO_PHAN_BO chưa có dữ liệu phân bổ tích lũy.")
        return

    # Bảng tổng hợp theo SKU và theo đơn vị nhận
    tong_hop_sku = {}
    tong_hop_diem = {}
    
    # Duyệt từ dòng 3 (bỏ qua tiêu đề hàng 1 và 2)
    for r in range(2, len(kho_data)):
        row = kho_data[r]
        if len(row) < 8:
            continue
            
        ma_da   = str(row[0]).strip()
        ma_sku  = str(row[1]).strip()
        ten_tb  = str(row[3]).strip()
        don_vi  = str(row[5]).strip()
        sl_raw  = str(row[4]).strip()
        doi_nhan = str(row[7]).strip() # Cột H: Địa điểm/Đơn vị nhận
        
        try:
            so_luong = float(sl_raw)
        except ValueError:
            so_luong = 0
            
        if ma_sku:
            # 1. Tổng hợp theo SKU thiết bị
            if ma_sku not in tong_hop_sku:
                tong_hop_sku[ma_sku] = {
                    "ten_tb": ten_tb,
                    "don_vi": don_vi,
                    "tong_sl": 0
                }
            tong_hop_sku[ma_sku]["tong_sl"] += so_luong
            
        if doi_nhan:
            # 2. Tổng hợp theo điểm/đơn vị nhận
            tong_hop_diem[doi_nhan] = tong_hop_diem.get(doi_nhan, 0) + so_luong

    # In kết quả tổng hợp ra màn hình console để theo dõi nhanh
    print("=== TỔNG HỢP KHỐI LƯỢNG PHÂN BỔ THEO THIẾT BỊ (SKU) ===")
    for sku, info in tong_hop_sku.items():
        print(f"- [{sku}] {info['ten_tb']} ({info['don_vi']}): Tổng phân bổ = {info['tong_sl']}")
        
    print("\n=== TỔNG HỢP KHỐI LƯỢNG THEO CÁC ĐƠN VỊ / ĐIỂM NHẬN ===")
    for diem, sl in tong_hop_diem.items():
        print(f"- {diem}: {sl} đơn vị thiết bị")

if __name__ == "__main__":
    tong_hop_kho_phan_bo("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
