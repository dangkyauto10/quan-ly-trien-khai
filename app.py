def ghi_phan_bo_chuan_xac_100(credentials_path, spreadsheet_name, danh_sach_dong_moi):
    """
    Do chính em viết và chịu trách nhiệm:
    - Tuyệt đối không dùng lệnh clear hay update đè dải cố định.
    - Tự động lấy toàn bộ dữ liệu hiện có, xác định đúng dòng trống tiếp theo để nối tiếp (append).
    - Giữ nguyên vẹn 100% dữ liệu các lần phân bổ trước, không bao giờ bị xóa.
    """
    import gspread
    
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    worksheet = sh.worksheet("KHO_PHAN_BO")
    
    if not danh_sach_dong_moi:
        return

    # Lấy toàn bộ dữ liệu hiện tại trên sheet
    all_values = worksheet.get_all_values()
    
    # Xác định dòng cuối cùng đang có dữ liệu thực tế
    last_row = len(all_values)
    while last_row > 2 and not any(str(cell).strip() for cell in all_values[last_row - 1]):
        last_row -= 1
        
    # Dòng tiếp theo cần ghi nối tiếp xuống dưới
    next_row = last_row + 1
    if next_row < 3:
        next_row = 3
        
    num_rows = len(danh_sach_dong_moi)
    num_cols = len(danh_sach_dong_moi[0])
    
    # Ép kiểu dải ô để cập nhật đúng từ dòng trống tiếp theo trở xuống
    end_col_letter = gspread.utils.rowcol_to_a1(1, num_cols).rstrip('1')
    range_to_update = f"A{next_row}:{end_col_letter}{next_row + num_rows - 1}"
    
    # Thực hiện ghi nối tiếp an toàn
    worksheet.update(range_to_update, danh_sach_dong_moi, value_input_option='USER_ENTERED')
    print(f"Đã ghi nối tiếp thành công {num_rows} dòng từ dòng {next_row}. Dữ liệu cũ được bảo toàn!")
