import pandas as pd

def xu_ly_phan_bo_va_ton_kho(df_dm_chuan, df_nhap_kho, df_kho_phan_bo_hien_tai, df_danh_sach_du_an):
    """
    1. Nối tiếp (append) dữ liệu phân bổ mới từ DM_CHUAN vào KHO_PHAN_BO.
    2. Tính toán tồn kho / chờ phân bổ bên NHAP_KHO:
       - Nếu KHO_PHAN_BO trống -> Tồn kho NHAP_KHO = 100% Tổng nhập thầu.
       - Nếu có phân bổ -> Trừ đi tổng số lượng đã phân bổ cộng dồn theo (Mã Dự Án + SKU).
       - Khi phân bổ hết sạch số lượng -> Tồn kho về 0.
    """
    
    # Bước 1: Xử lý dữ liệu phân bổ mới từ DM_CHUAN
    # (Map mã dự án, tách đội nhận, sinh các dòng phân bổ mới...)
    danh_sach_phan_bo_moi = []
    
    # Giả lập gom dữ liệu phân bổ mới nối tiếp vào kho phân bổ hiện tại
    if df_kho_phan_bo_hien_tai is not None and not df_kho_phan_bo_hien_tai.empty:
        df_kho_phan_bo_moi = pd.concat([df_kho_phan_bo_hien_tai, pd.DataFrame(danh_sach_phan_bo_moi)], ignore_index=True)
    else:
        df_kho_phan_bo_moi = pd.DataFrame(danh_sach_phan_bo_moi)
        
    # Bước 2: Tính toán tồn kho bên NHAP_KHO
    # Tạo từ điển cộng dồn số lượng đã phân bổ theo khóa: "MãDA_SKU"
    phan_bo_map = {}
    has_active_data = False
    
    if not df_kho_phan_bo_moi.empty:
        for _, row in df_kho_phan_bo_moi.iterrows():
            ma_da = str(row.get('MaDuAn', '')).strip()
            ma_sku = str(row.get('MaSKU', '')).strip()
            so_luong_pb = float(row.get('SoLuong', 0) or 0)
            
            if ma_sku and so_luong_pb != 0:
                has_active_data = True
                key = f"{ma_da}_{ma_sku}"
                phan_bo_map[key] = phan_bo_map.get(key, 0) + so_luong_pb
                
    # Bước 3: Cập nhật cột "Tồn kho / chờ phân bổ" bên NHAP_KHO
    danh_sach_ton_kho = []
    for _, row in df_nhap_kho.iterrows():
        ma_da_nhap = str(row.get('MaDuAn', '')).strip()
        ma_sku_nhap = str(row.get('MaSKU', '')).strip()
        tong_nhap_thau = float(row.get('TongNhapThau', 0) or 0)
        
        if ma_sku_nhap:
            lookup_key = f"{ma_da_nhap}_{ma_sku_nhap}"
            
            # Nếu KHO_PHAN_BO trống (hoặc đã xóa hết) -> Tồn kho = 100% Tổng nhập thầu
            # Nếu có phân bổ -> Trừ đi tổng số lượng đã phân bổ cộng dồn
            da_phan_bo = phan_bo_map.get(lookup_key, 0) if has_active_data else 0
            ton_kho = tong_nhap_thau - da_phan_bo
            
            # Đảm bảo không bị âm nếu phân bổ vượt quá (tùy nghiệp vụ, có thể chặn ở 0)
            ton_kho = max(0, ton_kho)
            
            danh_sach_ton_kho.append(ton_kho)
        else:
            danh_sach_ton_kho.append("")
            
    df_nhap_kho['TonKhoDuAn'] = danh_sach_ton_kho
    
    return df_kho_phan_bo_moi, df_nhap_kho
