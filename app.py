import gspread

def ghi_nhan_phan_bo_python_chuan(credentials_path, spreadsheet_name, rows_to_append):
    """
    [PYTHON_FIRST - CAM KẾT AN TOÀN TUYỆT ĐỐI CHO CÁC MODULE ĐÃ HOÀN THÀNH]
    - Không gọi bất kỳ lệnh clear() hay xóa dữ liệu cũ nào.
    - Tự động quét lấy toàn bộ dữ liệu hiện tại của sheet KHO_PHAN_BO để xác định đúng dòng trống tiếp theo (next_row).
    - Ghi nối tiếp (append) dữ liệu mới xuống dưới cùng, bảo toàn nguyên vẹn 100% dữ liệu các lần phân bổ trước.
    - Giữ nguyên chuẩn xác số lượng cột, không làm lệch cấu trúc bảng.
    """
    if not rows_to_append or len(rows_to_append) == 0:
        print("[PYTHON_FIRST] Không có dữ liệu phân bổ mới để ghi.")
        return

    # 1. Kết nối Google Sheets qua service account
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    
    # 2. Lấy toàn bộ dữ liệu hiện tại để xác định vị trí ghi nối tiếp chính xác
    existing_data = sheet_kho.get_all_values()
    last_row = len(existing_data)
    
    # Xác định dòng trống tiếp theo (bắt đầu từ dòng 3 trở xuống nếu bảng trống)
    next_row = last_row + 1
    if next_row < 3:
        next_row = 3
        
    num_rows = len(rows_to_append)
    num_cols = len(rows_to_append[0])
    
    # 3. Tính toán dải ô an toàn dựa trên số cột thực tế của dữ liệu
    end_col_letter = gspread.utils.rowcol_to_a1(1, num_cols).rstrip('1')
    range_string = f"A{next_row}:{end_col_letter}{next_row + num_rows - 1}"
    
    # 4. Thực hiện ghi đè an toàn vào vùng trống mới (Không chạm vào dữ liệu cũ ở trên)
    sheet_kho.update(range_string, rows_to_append, value_input_option='USER_ENTERED')
    print(f"[PYTHON_FIRST] Đã ghi nối tiếp thành công {num_rows} dòng phân bổ từ dòng {next_row} vào KHO_PHAN_BO. Dữ liệu cũ được bảo toàn tuyệt đối!")
