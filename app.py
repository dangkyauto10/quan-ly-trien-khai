thoi_gian_hien_tai = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not is_lap_dat:
            # --- ÁNH XẠ CHO SHEET VAN_CHUYEN ---
            target_sheet_name = "VAN_CHUYEN"
            # Cấu trúc cột VAN_CHUYEN tương ứng
            # Sẽ map từ KHO_PHAN_BO: Mã DA, Đội nhận, Tên thiết bị, Số lượng, ĐVT, Người gửi, Địa điểm, Trạng thái, Thời gian...
        else:
            # --- ÁNH XẠ CHO SHEET LAP_DAT ĐÚNG CHUẨN CÁC CỘT YÊU CẦU ---
            target_sheet_name = "LAP_DAT"
            for idx, item in enumerate(danh_sach_hien_tai, start=1):
                ma_cv = f"LD-{datetime.now().strftime('%m%d%H%M')}-{idx}"
                # Ánh xạ chính xác các cột từ KHO_PHAN_BO sang LAP_DAT:
                # [Mã công việc, Mã dự án, Đội nhận, Tên thiết bị, Số lượng, ĐVT, Địa điểm lắp, Trạng thái, Thời gian, Link Maps]
                row_mapped = [
                    ma_cv,                     # Cột A: Mã công việc
                    item["ma_da"],             # Cột B: Mã dự án (ánh xạ từ KHO_PHAN_BO)
                    item["doi"],               # Cột C: Đội nhận thiết bị (ánh xạ từ KHO_PHAN_BO)
                    item["ten"],               # Cột D: Tên thiết bị / Hàng hóa (ánh xạ từ KHO_PHAN_BO)
                    item["soluong"],           # Cột E: Số lượng thiết bị lắp (ánh xạ từ KHO_PHAN_BO)
                    item["donvi"],             # Cột F: ĐVT (ánh xạ từ KHO_PHAN_BO)
                    selected_location,         # Cột G: Địa điểm lắp (ánh xạ từ KHO_PHAN_BO cột địa điểm đến)
                    st.session_state.trang_thai_chon, # Cột H: Tình trạng thực hiện
                    thoi_gian_hien_tai,        # Cột I: Thời gian hoàn thành
                    f"GPS Verified ({st.session_state.get('gps_time', '')})" # Cột J: Link Google Maps
                ]
