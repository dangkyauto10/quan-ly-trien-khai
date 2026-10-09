# ĐÂY LÀ "MẮT THẦN" ĐÃ ĐƯỢC BỔ SUNG TỪ KHÓA "ĐỊA ĐIỂM LẮP"
def quet_mat_than(data_sheet, p_code, d_doi, d_diem):
    ds_kq = []
    if not data_sheet: return ds_kq
    # Mặc định chuẩn theo cấu trúc file của anh
    idx_proj = 1; idx_diem = 6; idx_matb = 0; idx_tentb = 3; idx_sl = 4; idx_dvt = 5; idx_doi = 2
    
    for r in data_sheet[:5]:
        for i, h in enumerate(r):
            h_str = str(h).replace('\xa0', ' ').strip().upper()
            if "MÃ DỰ ÁN" in h_str or "MÃ DA" in h_str: idx_proj = i
            elif "ĐỊA ĐIỂM" in h_str or "ĐƠN VỊ" in h_str or "ĐIỂM GIAO" in h_str or "ĐỊA ĐIỂM LẮP" in h_str: idx_diem = i
            elif "MÃ CÔNG VIỆC" in h_str or "SKU" in h_str: idx_matb = i
            elif "TÊN THIẾT BỊ" in h_str or "HÀNG HÓA" in h_str: idx_tentb = i
            elif "SỐ LƯỢNG" in h_str or "SL" in h_str: idx_sl = i
            elif "ĐƠN VỊ TÍNH" in h_str or "ĐVT" in h_str: idx_dvt = i
            elif "ĐỘI" in h_str or "NHÂN SỰ" in h_str: idx_doi = i

    for r in data_sheet:
        c_proj = str(r[idx_proj]).replace('\xa0', ' ').strip().upper() if len(r) > idx_proj else ""
        c_diem = str(r[idx_diem]).replace('\xa0', ' ').strip().upper() if len(r) > idx_diem else ""
        c_doi = str(r[idx_doi]).replace('\xa0', ' ').strip().upper() if len(r) > idx_doi else ""
        
        # So khớp lỏng hơn một chút để chống trượt ký tự ẩn
        if p_code in c_proj and (d_diem in c_diem or c_diem in d_diem) and (d_doi in c_doi or c_doi in d_doi):
            sku = str(r[idx_matb]).strip() if len(r) > idx_matb else "TB-0X"
            ten = str(r[idx_tentb]).strip() if len(r) > idx_tentb else "Thiết bị"
            sl = str(r[idx_sl]).strip() if len(r) > idx_sl else "1"
            dvt = str(r[idx_dvt]).strip() if len(r) > idx_dvt else "Bộ"
            if ten and ten.upper() not in ["TÊN THIẾT BỊ / HÀNG HÓA", "TÊN THIẾT BỊ", "NONE", ""]:
                ds_kq.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})
    return ds_kq
