import pandas as pd

def xu_ly_phan_bo_va_dong_bo_ton_kho(file_path):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    1. Đọc dữ liệu từ các sheet: DM_CHUAN, DANH_SACH_DU_AN, KHO_PHAN_BO, NHAP_KHO.
    2. Nối tiếp (append dồn) dữ liệu phân bổ mới vào KHO_PHAN_BO (không làm mất dữ liệu đợt trước).
    3. Tính toán tồn kho bên NHAP_KHO:
       - Nếu KHO_PHAN_BO trống hoàn toàn -> Cột Tồn kho dự án = 100% Tổng nhập thầu.
       - Nếu có dữ liệu phân bổ -> Trừ đi tổng số lượng đã phân bổ cộng dồn theo (Mã Dự Án + SKU).
    """
    
    # Đọc dữ liệu từ file Excel hoặc Google Sheets qua Pandas
    excel_file = pd.ExcelFile(file_path)
    
    df_dm_chuan = pd.read_excel(excel_file, sheet_name='DM_CHUAN')
    df_nhap_kho = pd.read_excel(excel_file, sheet_name='NHAP_KHO')
    df_danh_sach_da = pd.read_excel(excel_file, sheet_name='DANH_SACH_DU_AN')
    
    # Đọc KHO_PHAN_BO hiện tại (nếu đã có)
    try:
        df_kho_phan_bo = pd.read_excel(excel_file, sheet_name='KHO_PHAN_BO')
    except Exception:
        df_kho_phan_bo = pd.DataFrame(columns=[
            'MaDuAn', 'MaSKU', 'TenDuAn', 'TenThietBi', 'SoLuong', 
            'DonViTinh', 'DoiNhan', 'DiaDiem', 'TrangThai'
        ])

    # 1. Tạo Map tên dự án từ DANH_SACH_DU_AN
    map_da = {}
    if not df_danh_sach_da.empty:
        for _, row in df_danh_sach_da.iterrows():
            m_da = str(row.iloc[0]).strip()
            t_da = str(row.iloc[1]).strip()
            if m_da and m_da not in ["Mã dự án", "Mã đội", "nan"]:
                map_da[m_da] = t_da

    # 2. Xử lý dữ liệu phân bổ mới từ DM_CHUAN (Bắt đầu từ dòng 3, tức index tương ứng)
    danh_sach_moi = []
    # Giả định cấu trúc DM_CHUAN: Col 0: Mã DA, Col 1: Mã SKU, Col 2: Tên thiết bị, Col 3: ĐVT, Col 4: Số lượng, Col 5: Đội nhận
    for _, row in df_dm_chuan.iloc[1:].iterrows(): # Bỏ qua dòng tiêu đề nếu cần
        ma_da = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "DA880"
        ma_sku = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        ten_tb = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        don_vi = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        so_luong = pd.to_numeric(row.iloc[4], errors='coerce')
        doi_nhan_str = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""

        if ma_sku and pd.notna(so_luong) and so_luong > 0:
            units = [u.strip() for u in doi_nhan_str.split(",") if u.strip() and u.strip().lower() != "nan"]
            if not units:
                units = [""]
            
            for unit in units:
                t_da = map_da.get(ma_da, ma_da)
                danh_sach_moi.append({
                    'MaDuAn': ma_da,
                    'MaSKU': ma_sku,
                    'TenDuAn': t_da,
                    'TenThietBi': ten_tb,
                    'SoLuong': so_luong,
                    'DonViTinh': don_vi,
                    'DoiNhan': unit,
                    'DiaDiem': "",
                    'TrangThai': ""
                })

    df_moi = pd.DataFrame(danh_sach_moi)

    # 3. NỐI TIẾP (APPEND DỒN) dữ liệu mới vào KHO_PHAN_BO cũ (Không làm mất dữ liệu lần trước)
    if not df_moi.empty:
        if not df_kho_phan_bo.empty and 'MaSKU' in df_kho_phan_bo.columns:
            # Lọc bỏ các dòng trống rác nếu có
            df_kho_phan_bo = df_kho_phan_bo[df_kho_phan_bo['MaSKU'].notna() & (df_kho_phan_bo['MaSKU'] != "")]
            df_kho_phan_bo_moi = pd.concat([df_kho_phan_bo, df_moi], ignore_index=True)
        else:
            df_kho_phan_bo_moi = df_moi
    else:
        df_kho_phan_bo_moi = df_kho_phan_bo

    # 4. TÍNH TOÁN TỒN KHO BÊN NHAP_KHO
    phan_bo_map = {}
    has_active_data = False

    if not df_kho_phan_bo_moi.empty:
        for _, row in df_kho_phan_bo_moi.iterrows():
            m_da = str(row.get('MaDuAn', '')).strip()
            m_sku = str(row.get('MaSKU', '')).strip()
            sl_pb = pd.to_numeric(row.get('SoLuong', 0), errors='coerce')
            
            if m_sku and m_sku != "nan" and pd.notna(sl_pb) and sl_pb > 0:
                has_active_data = True
                key = f"{m_da}_{m_sku}"
                phan_bo_map[key] = phan_bo_map.get(key, 0) + sl_pb

    # Cập nhật cột tồn kho (Cột F - Tồn kho dự án)
    ton_kho_ket_qua = []
    for _, row in df_nhap_kho.iterrows():
        m_da_nhap = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        m_sku_nhap = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        tong_nhap = pd.to_numeric(row.iloc[4], errors='coerce') # Cột E: Tổng nhập thầu (index 4)
        
        if m_sku_nhap and m_sku_nhap != "nan" and pd.notna(tong_nhap):
            lookup_key = f"{m_da_nhap}_{m_sku_nhap}"
            
            # NẾU KHO_PHAN_BO TRỐNG (has_active_data = False) -> Tồn kho = 100% Tổng nhập thầu
            da_phan_bo = phan_bo_map.get(lookup_key, 0) if has_active_data else 0
            ton_kho = tong_nhap - da_phan_bo
            
            if ton_kho < 0:
                ton_kho = 0
                
            ton_kho_ket_qua.append(ton_kho)
        else:
            ton_kho_ket_qua.append("")

    df_nhap_kho.iloc[:, 5] = ton_kho_ket_qua  # Ghi đè vào cột F (index 5)

    return df_kho_phan_bo_moi, df_nhap_kho
