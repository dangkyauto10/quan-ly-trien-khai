import pandas as pd

def cap_nhat_doi_nhan_dm_chuan(file_path):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Quy chiếu động toàn bộ dữ liệu cột D từ sheet DANH_SACH_DIEM 
    để cập nhật chính xác cho cột F của sheet DM_CHUAN theo từng dự án.
    """
    excel_file = pd.ExcelFile(file_path)
    
    df_dm_chuan = pd.read_excel(excel_file, sheet_name='DM_CHUAN')
    df_ds_diem = pd.read_excel(excel_file, sheet_name='DANH_SACH_DIEM')
    
    # 1. Xây dựng bộ lọc/bản đồ ánh xạ từ DANH_SACH_DIEM
    # Giả định cột A là Mã dự án, cột D là Danh sách điểm nhận / đội nhận
    map_diem_nhan = {}
    
    if not df_ds_diem.empty:
        for _, row in df_ds_diem.iterrows():
            ma_da = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            diem_nhan = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "" # Cột D là index 3
            
            if ma_da and ma_da not in ["Mã dự án", "nan"]:
                if ma_da not in map_diem_nhan:
                    map_diem_nhan[ma_da] = []
                if diem_nhan and diem_nhan.lower() != "nan":
                    map_diem_nhan[ma_da].append(diem_nhan)

    # 2. Cập nhật tự động vào cột F (index 5) của sheet DM_CHUAN dựa theo Mã dự án (Cột A - index 0)
    danh_sach_cap_nhat = []
    for _, row in df_dm_chuan.iterrows():
        ma_da = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        
        if ma_da in map_diem_nhan:
            # Nối các điểm nhận lại thành chuỗi phân tách bằng dấu phẩy để phân bổ động
            row_diem_moi = ", ".join(map_diem_nhan[ma_da])
            danh_sach_cap_nhat.append(row_diem_moi)
        else:
            danh_sach_cap_nhat.append(str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else "")

    # Ghi đè lại cột F của DM_CHUAN
    df_dm_chuan.iloc[:, 5] = danh_sach_cap_nhat
    
    return df_dm_chuan
