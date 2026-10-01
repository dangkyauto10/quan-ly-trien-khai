import gspread

def fix_validation_triet_de_python(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Sử dụng Google Sheets API request trực tiếp qua gspread để ép dải ô Data Validation 
    của cột F (DM_CHUAN) trỏ trọn vẹn vào toàn bộ cột D (DANH_SACH_DIEM),
    giúp hiển thị đầy đủ 100% từ xã, huyện đến tận các Ban ở cuối bảng mà không bị cụt.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    sheet_diem = sh.worksheet("DANH_SACH_DIEM")
    sheet_dm = sh.worksheet("DM_CHUAN")
    
    # Lấy ID của các sheet để thực hiện request API trực tiếp
    sheet_diem_id = sheet_diem.id
    sheet_dm_id = sheet_dm.id
    
    # Tìm dòng cuối cùng thực tế có dữ liệu ở cột D của DANH_SACH_DIEM
    col_d_values = sheet_diem.col_values(4)
    last_row = len(col_d_values)
    while last_row > 1 and not str(col_d_values[last_row - 1]).strip():
        last_row -= 1
    if last_row < 2:
        last_row = 1000 # Dự phòng an toàn nếu bảng trống
        
    # Chuẩn bị cấu trúc request API gốc để gán Data Validation chuẩn xác tuyệt đối
    request_body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_dm_id,
                        "startRowIndex": 2,      # Dòng 3 (Index 2 vì tính từ 0)
                        "endRowIndex": 500,      # Đến dòng 500
                        "startColumnIndex": 5,   # Cột F (Index 5 vì A=0, B=1, C=2, D=3, E=4, F=5)
                        "endColumnIndex": 6
                    },
                    "rule": {
                        "criteria": {
                            "type": "REF_RANGE",
                            "values": [
                                {
                                    "userEnteredValue": f"=DANH_SACH_DIEM!$D$2:$D${last_row}"
                                }
                            ]
                        },
                        "strict": True,
                        "showCustomUi": True
                    }
                }
            }
        ]
    }
    
    # Thực thi request qua gspread client
    sh.batch_update(request_body)
    print(f"[PYTHON_FIRST] Đã ép xung dải ô Data Validation thành công qua API gốc đến dòng {last_row}!")

if __name__ == "__main__":
    fix_validation_triet_de_python("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
