# Đoạn code Python cập nhật Data Validation tự động qua Google Sheets API (nếu dùng gspread)
import gspread

def cap_nhat_validation_cot_f(sheet_tu_xa):
    worksheet_dm = sheet_tu_xa.worksheet("DM_CHUAN")
    
    # Định nghĩa quy tắc Data Validation lấy nguồn từ toàn bộ cột D của sheet DANH_SACH_DIEM (từ dòng 2 đến 500)
    rule = gspread.validation.DataValidationRule(
        gspread.validation.BooleanCriteria.CELL_RANGE,
        ["DANH_SACH_DIEM!D2:D500"],
        allow_invalid=False,
        help_text="Vui lòng chọn hoặc nhập đúng danh sách điểm nhận."
    )
    
    # Áp dụng cho toàn bộ cột F từ dòng 3 đến 200 của sheet DM_CHUAN
    gspread.validation.set_data_validation_for_cell_range(worksheet_dm, "F3:F200", rule)
