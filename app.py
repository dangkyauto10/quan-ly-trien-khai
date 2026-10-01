import gspread

def tu_dong_co_gian_validation(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Tự động xác định số dòng thực tế có dữ liệu ở cột D của sheet DANH_SACH_DIEM,
    sau đó tự động co giãn phạm vi Data Validation cho cột F của sheet DM_CHUAN 
    đúng khớp với số lượng thực tế đó (không fix cứng, tự động theo dữ liệu động).
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    # 1. Lấy dữ liệu động từ sheet DANH_SACH_DIEM cột D
    worksheet_diem = sh.worksheet("DANH_SACH_DIEM")
    col_d_values = worksheet_diem.col_values(4) # Cột D là cột số 4
    
    # Tìm dòng cuối cùng thực sự có dữ liệu (bỏ qua các ô trống cuối bảng)
    last_row = len(col_d_values)
    while last_row > 1 and not str(col_d_values[last_row - 1]).strip():
        last_row -= 1
        
    # Đảm bảo dải ô tối thiểu từ dòng 2 đến last_row thực tế
    if last_row < 2:
        last_row = 2
        
    dynamic_range_string = f"DANH_SACH_DIEM!D2:D{last_row}"
    
    # 2. Áp dụng dải ô động này vào Data Validation của cột F (từ dòng 3 đến 500) ở sheet DM_CHUAN
    worksheet_dm = sh.worksheet("DM_CHUAN")
    
    rule = gspread.validation.DataValidationRule(
        gspread.validation.BooleanCriteria.CELL_RANGE,
        [dynamic_range_string],
        allow_invalid=False,
        help_text="Chọn đúng đơn vị từ danh sách nguồn động."
    )
    
    gspread.validation.set_data_validation_for_cell_range(worksheet_dm, "F3:F500", rule)
    print(f"Đã tự động co giãn dải ô Data Validation theo dữ liệu thực tế ({dynamic_range_string}) thành công!")
