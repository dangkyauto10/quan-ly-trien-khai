import gspread

def cap_nhat_validation_cot_f_chuan(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Tự động quét trọn vẹn toàn bộ dữ liệu thực tế ở cột D của sheet DANH_SACH_DIEM 
    (bao gồm toàn bộ các xã, huyện và các Ban ở cuối bảng) 
    và đồng bộ thẳng vào dải ô Data Validation của cột F (sheet DM_CHUAN).
    """
    # 1. Kết nối Google Sheets qua Service Account
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 2. Lấy sheet nguồn DANH_SACH_DIEM và tìm dòng cuối cùng thực tế của cột D
    sheet_diem = sh.worksheet("DANH_SACH_DIEM")
    col_d_values = sheet_diem.col_values(4) # Cột D là cột số 4
    
    last_row = len(col_d_values)
    while last_row > 1 and not str(col_d_values[last_row - 1]).strip():
        last_row -= 1
        
    if last_row < 2:
        last_row = 2
        
    dynamic_range = f"DANH_SACH_DIEM!D2:D{last_row}"
    
    # 3. Áp dụng dải ô động này vào Data Validation của cột F (từ dòng 3 đến 500) ở sheet DM_CHUAN
    sheet_dm = sh.worksheet("DM_CHUAN")
    
    rule = gspread.validation.DataValidationRule(
        gspread.validation.BooleanCriteria.CELL_RANGE,
        [dynamic_range],
        allow_invalid=False,
        help_text="Chọn đúng đơn vị từ danh sách nguồn."
    )
    
    # Áp dụng cho dải F3:F500 (hoặc mở rộng tùy ý)
    gspread.validation.set_data_validation_for_cell_range(sheet_dm, "F3:F500", rule)
    print(f"[PYTHON_FIRST] Đã đồng bộ Data Validation thành công từ dải {dynamic_range}!")

if __name__ == "__main__":
    cap_nhat_validation_cot_f_chuan("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
