import gspread

def fix_validation_quet_toan_bo_sheet(credentials_path, spreadsheet_name):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Quét toàn bộ mọi ô trong sheet DANH_SACH_DIEM (không bỏ sót bất kỳ dòng nào, 
    bất chấp dòng trống hay cách quãng), gom trọn vẹn toàn bộ tên đơn vị, xã, phường và các Ban, 
    sau đó ép thẳng danh sách vào Data Validation của cột F (DM_CHUAN) qua Google Sheets API.
    """
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    
    sheet_diem = sh.worksheet("DANH_SACH_DIEM")
    sheet_dm = sh.worksheet("DM_CHUAN")
    
    # 1. Đọc toàn bộ ma trận dữ liệu của sheet DANH_SACH_DIEM
    all_rows = sheet_diem.get_all_values()
    
    clean_values = []
    # Các từ khóa tiêu đề hoặc rác cần loại bỏ
    ignored_keywords = [
        "nan", "địa điểm giao hàng và lắp đặt", "thuộc huyện", "số thứ tự", 
        "stt", "huyện", "thành phố", ""
    ]
    
    for row in all_rows:
        for cell in row:
            val_str = str(cell).strip()
            # Lọc lấy các giá trị chữ hợp lệ, bỏ qua số thứ tự thuần túy hoặc từ khóa tiêu đề
            if val_str and not val_str.isdigit():
                if val_str.lower() not in ignored_keywords:
                    if val_str not in clean_values:
                        clean_values.append(val_str)
                        
    print(f"[PYTHON_FIRST] Đã quét toàn bộ sheet và gom được {len(clean_values)} đơn vị/địa điểm duy nhất.")
    
    # 2. Xây dựng API Request ép danh sách đầy đủ (LIST_OF_VALUES) vào Data Validation của cột F (DM_CHUAN)
    sheet_dm_id = sheet_dm.id
    request_body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_dm_id,
                        "startRowIndex": 2,      # Dòng 3 trở đi
                        "endRowIndex": 1000,
                        "startColumnIndex": 5,   # Cột F
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
    
    sh.batch_update(request_body)
    print("[PYTHON_FIRST] Đã cập nhật thành công toàn bộ danh sách đầy đủ vào Data Validation!")

if __name__ == "__main__":
    fix_validation_quet_toan_bo_sheet("credentials.json", "QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
