import gspread

def fix_validation_list_values_triet_de(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Python tự động bóc tách toàn bộ giá trị thực tế từ cột D của DANH_SACH_DIEM,
    lọc bỏ ô trống và ép thẳng toàn bộ danh sách chuẩn (bao gồm tất cả các Ban) 
    vào quy tắc Data Validation (kiểu LIST_OF_VALUES) của cột F (DM_CHUAN) qua API gốc.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    sheet_diem = sh.worksheet("DANH_SACH_DIEM")
    sheet_dm = sh.worksheet("DM_CHUAN")
    
    sheet_dm_id = sheet_dm.id
    
    # 1. Đọc toàn bộ cột D của sheet DANH_SACH_DIEM và lọc sạch các ô trống, tiêu đề rác
    col_d_values = sheet_diem.col_values(4)
    clean_values = []
    
    for val in col_d_values[1:]:  # Bỏ qua tiêu đề dòng đầu tiên
        val_str = str(val).strip()
        if val_str and val_str.lower() not in ["nan", "địa điểm giao hàng và lắp đặt", ""]:
            if val_str not in clean_values:
                clean_values.append(val_str)
                
    print(f"[PYTHON_FIRST] Đã quét được {len(clean_values)} đơn vị thực tế (đảm bảo gom đủ toàn bộ các Ban).")
    
    # 2. Xây dựng API Request ép trực tiếp danh sách giá trị (LIST_OF_VALUES) qua batch_update
    request_body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_dm_id,
                        "startRowIndex": 2,      # Dòng 3 (Index 2)
                        "endRowIndex": 500,      # Đến dòng 500
                        "startColumnIndex": 5,   # Cột F (Index 5)
                        "endColumnIndex": 6
                    },
                    "rule": {
                        "criteria": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": item} for item in clean_values]
                        },
                        "strict": True,
                        "showCustomUi": True
                    }
                }
            }
        ]
    }
    
    # 3. Thực thi cập nhật trực tiếp qua Google Sheets API
    sh.batch_update(request_body)
    print("[PYTHON_FIRST] Đã ép xung thành công toàn bộ danh sách vào Data Validation qua API Python!")

if __name__ == "__main__":
    fix_validation_list_values_triet_de("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
