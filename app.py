import gspread

def tu_dong_cap_nhat_validation_python(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Toàn bộ logic mở rộng dải ô Data Validation dựa trên số dòng động của cột D (DANH_SACH_DIEM) 
    được xử lý hoàn toàn bằng Python qua gspread API. Không dùng Apps Script.
    """
    # 1. Kết nối Google Sheets qua Service Account Python
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 2. Lấy sheet nguồn và xác định chính xác dòng cuối cùng có dữ liệu của cột D
    sheet_diem = sh.worksheet("DANH_SACH_DIEM")
    col_d_values = sheet_diem.col_values(4) # Cột D (index 4)
    
    real_last_row = len(col_d_values)
    while real_last_row > 1 and not str(col_d_values[real_last_row - 1]).strip():
        real_last_row -= 1
        
    if real_last_row < 2:
        real_last_row = 2
        
    dynamic_range_string = f"DANH_SACH_DIEM!D2:D{real_last_row}"
    
    # 3. Tạo và áp dụng quy tắc Data Validation qua Python cho sheet DM_CHUAN (Cột F3:F500)
    sheet_dm = sh.worksheet("DM_CHUAN")
    
    rule = gspread.validation.DataValidationRule(
        gspread.validation.BooleanCriteria.CELL_RANGE,
        [dynamic_range_string],
        allow_invalid=False,
        help_text="Chọn đúng đơn vị từ danh sách nguồn động."
    )
    
    gspread.validation.set_data_validation_for_cell_range(sheet_dm, "F3:F500", rule)
    print(f"[PYTHON_FIRST] Đã đồng bộ thành công dải ô Data Validation đến dòng {real_last_row} qua Python!")

# Nếu chạy trực tiếp script:
if __name__ == "__main__":
    tu_dong_cap_nhat_validation_python("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
