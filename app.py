import gspread

def phan_bo_va_tich_luy_an_toan_tuyet_doi(credentials_path, spreadsheet_name, rows_to_append):
    """
    [CAM KẾT AN TOÀN 100% - CHUẨN GITHUB & PYTHON_FIRST]
    - Tuyệt đối không có lệnh clear(), không xóa dữ liệu cũ.
    - Sử dụng chuẩn append_rows() của gspread để tự động nối tiếp các lần phân bổ mới xuống dưới cùng.
    - Bảo toàn nguyên vẹn 100% dữ liệu các lần trước, không làm lệch cột hay ảnh hưởng NHAP_KHO.
    """
    if not rows_to_append or len(rows_to_append) == 0:
        print("[PYTHON_FIRST] Không có dữ liệu phân bổ mới.")
        return

    # 1. Kết nối Google Sheets
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    sheet_kho = sh.worksheet("KHO_PHAN_BO")
    
    # 2. Sử dụng append_rows để tự động tìm dòng trống cuối cùng và chèn tiếp nối đuôi xuống dưới
    # Giữ nguyên toàn bộ lịch sử các lần phân bổ trước, không một dòng nào bị xóa.
    sheet_kho.append_rows(rows_to_append, value_input_option='USER_ENTERED')
    
    print("[PYTHON_FIRST] Đã append thành công, dữ liệu tích lũy đầy đủ và an toàn tuyệt đối!")
