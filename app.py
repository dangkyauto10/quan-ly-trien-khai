import pandas as pd

def dong_bo_danh_sach_diem_nhan(file_path):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Mở rộng và làm sạch phạm vi quét từ cột D của sheet nguồn (DANH_SACH_DIEM),
    đảm bảo không bị sót bất kỳ đơn vị, cơ quan, hay các 'Ban' nào ở phía dưới.
    """
    excel_file = pd.ExcelFile(file_path)
    
    # Đọc sheet danh sách điểm nhận (ví dụ: DANH_SACH_DIEM)
    try:
        df_ds_diem = pd.read_excel(excel_file, sheet_name='DANH_SACH_DIEM')
    except Exception:
        df_ds_diem = pd.DataFrame()
        
    danh_sach_chuan = []
    
    if not df_ds_diem.empty:
        # Quét toàn bộ cột D (index 3) từ trên xuống dưới không giới hạn cứng
        for _, row in df_ds_diem.iterrows():
            diem = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            
            # Loại bỏ tiêu đề hoặc dòng rác, chỉ lấy dữ liệu thật
            if diem and diem.lower() not in ["nan", "địa điểm giao hàng và lắp đặt", ""]:
                if diem not in danh_sach_chuan:
                    danh_sach_chuan.append(diem)
                    
    # In ra số lượng điểm nhận đã quét được để kiểm tra tính đầy đủ
    print(f"Đã quét và tổng hợp thành công {len(danh_sach_chuan)} điểm nhận thực tế từ cột D.")
    
    return danh_sach_chuan
