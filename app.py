import pandas as pd

def xu_ly_phan_bo_chuan_python(file_path):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    - Lọc điểm nhận từ sheet nguồn theo từ khóa ở cột F (DM_CHUAN).
    - Chỉ phân bổ các dòng có dữ liệu thực tế (bỏ qua dòng trống).
    - Nối tiếp dữ liệu sang KHO_PHAN_BO và đồng bộ tồn kho 100% sang NHAP_KHO.
    """
    excel_file = pd.ExcelFile(file_path)
    
    df_dm_chuan = pd.read_excel(excel_file, sheet_name='DM_CHUAN')
    df_nhap_kho = pd.read_excel(excel_file, sheet_name='NHAP_KHO')
    df_danh_sach_da = pd.read_excel(excel_file, sheet_name='DANH_SACH_DU_AN')
    
    # Giả định sheet chứa danh sách điểm nhận gốc là DANH_SACH_DIEM (hoặc chỉnh lại tên sheet cho khớp thực tế)
    try:
        df_ds_diem = pd.read_excel(excel_file, sheet_name='DANH_SACH_DIEM')
    except Exception:
        df_ds_diem = pd.DataFrame()

    # Đọc KHO_PHAN_BO hiện tại (nếu có)
    try:
        df_kho_phan_bo = pd.read_excel(excel_file, sheet_name='KHO_PHAN_BO')
    except Exception:
        df_kho_phan_bo = pd.DataFrame(columns=[
            'MaDuAn', 'MaSKU', 'TenDuAn', 'TenThietBi', 'SoLuong', 
            'DonViTinh', 'DoiNhan', 'DiaDiem', 'TrangThai'
        ])

    # 1. Map tên dự án từ DANH_SACH_DU_AN
    map_da = {}
    if not df_danh_sach_da.empty:
        for _, row in df_danh_sach_da.iterrows():
            m_da = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            t_da = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if m_da and m_da not in ["Mã dự án", "Mã đội", "nan"]:
                map_da[m_da] = t_da

    # 2. Xây dựng danh sách toàn bộ các điểm nhận gốc từ sheet danh sách điểm (Cột D - index 3)
    danh_sach_diem_goc = []
    if not df_ds_diem.empty:
        for _, row in df_ds_diem.iterrows():
            diem = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            if diem and diem.lower() not in ["nan", "địa điểm giao hàng và lắp đặt", ""]:
                danh_sach_diem_goc.append(diem)

    # 3. Duyệt DM_CHUAN để lọc từ khóa và chỉ lấy các dòng có đơn vị phân bổ thực tế
    danh_sach_phan_bo_moi = []
    
    # Bắt đầu từ dòng dữ liệu thực tế (bỏ qua tiêu đề, ví dụ từ dòng index 1 trở đi)
    for _, row in df_dm_chuan.iloc[1:].iterrows():
        ma_da = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "DA880"
        ma_sku = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        ten_tb = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        don_vi = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        so_luong = pd.to_numeric(row.iloc[4], errors='coerce')
        tu_khoa_nhap = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else ""

        # QUY TẮC: Chỉ xử lý khi dòng có SKU và số lượng hợp lệ (> 0)
        if ma_sku and ma_sku != "nan" and pd.notna(so_luong) and so_luong > 0:
            
            # Lọc đơn vị dựa trên từ khóa nhập ở cột F (nếu có từ khóa, lọc các điểm chứa từ khóa đó)
            units_to_allocate = []
            if tu_khoa_nhap and tu_khoa_nhap.lower() != "nan":
                # Kiểm tra xem từ khóa có trùng khớp trực tiếp với danh sách đơn vị không, 
                # hoặc lọc các điểm chứa từ khóa
                matched_units = [d for d in danh_sach_diem_goc if tu_khoa_nhap.lower() in d.lower()]
                if matched_units:
                    units_to_allocate = matched_units
                else:
                    # Nếu từ khóa nhập thẳng tên đơn vị không qua danh sách lọc
                    units_to_allocate = [u.strip() for u in tu_khoa_nhap.split(",") if u.strip()]
            
            # QUY TẮC: Nếu dòng trống hoàn toàn cột đơn vị/từ khóa -> BỎ QUA, KHÔNG PHÂN BỔ
            if not units_to_allocate:
                continue

            # Sinh các dòng phân bổ tương ứng cho từng đơn vị hợp lệ
            for unit in units_to_allocate:
                t_da = map_da.get(ma_da, ma_da)
                danh_sach_phan_bo_moi.append({
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

    df_moi = pd.DataFrame(danh_sach_phan_bo_moi)

    # 4. NỐI TIẾP (APPEND DỒN) vào KHO_PHAN_BO hiện tại
    if not df_moi.empty:
        if not df_kho_phan_bo.empty and 'MaSKU' in df_kho_phan_bo.columns:
            df_kho_phan_bo = df_kho_phan_bo[df_kho_phan_bo['MaSKU'].notna() & (df_kho_phan_bo['MaSKU'] != "")]
            df_kho_phan_bo_moi = pd.concat([df_kho_phan_bo, df_moi], ignore_index=True)
        else:
            df_kho_phan_bo_moi = df_moi
    else:
        df_kho_phan_bo_moi = df_kho_phan_bo

    # 5. TÍNH TOÁN VÀ ĐỒNG BỘ TỒN KHO NHAP_KHO (100% khi trống, trừ lùi khi có phân bổ)
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

    ton_kho_ket_qua = []
    for _, row in df_nhap_kho.iterrows():
        m_da_nhap = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        m_sku_nhap = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        tong_nhap = pd.to_numeric(row.iloc[4], errors='coerce') # Cột E: Tổng nhập thầu
        
        if m_sku_nhap and m_sku_nhap != "nan" and pd.notna(tong_nhap):
            lookup_key = f"{m_da_nhap}_{m_sku_nhap}"
            
            # KHO_PHAN_BO TRỐNG -> 100% Tổng nhập thầu. CÓ DỮ LIỆU -> TRỪ LÙI CỘNG DỒN
            da_phan_bo = phan_bo_map.get(lookup_key, 0) if has_active_data else 0
            ton_kho = tong_nhap - da_phan_bo
            
            if ton_kho < 0:
                ton_kho = 0
                
            ton_kho_ket_qua.append(ton_kho)
        else:
            ton_kho_ket_qua.append("")

    df_nhap_kho.iloc[:, 5] = ton_kho_ket_qua  # Ghi đè vào cột F (Tồn kho dự án)

    return df_kho_phan_bo_moi, df_nhap_kho
