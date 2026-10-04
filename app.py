# --- MODULE: ĐỒNG BỘ TỪ KHO PHÂN BỔ SANG LẮP ĐẶT (LAP_DAT) ---
st.header("🛠️ Quản Lý Lắp Đặt")
if st.button("Đồng bộ dữ liệu sang Lắp Đặt"):
    try:
        sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
        sheet_ld = spreadsheet.worksheet("LAP_DAT")
        
        kho_data = sheet_kho.get_all_values()
        if len(kho_data) < 3:
            st.warning("Sheet KHO_PHAN_BO chưa có dữ liệu!")
        else:
            rows_to_append = []
            for row in kho_data[2:]:
                if not any(row): continue
                
                # Lấy dữ liệu từ KHO_PHAN_BO (Index trong Python bắt đầu từ 0)
                val_A = row[0] if len(row) > 0 else ""  # A KPB: Mã dự án
                val_D = row[3] if len(row) > 3 else ""  # D KPB: Tên thiết bị
                val_E = row[4] if len(row) > 4 else ""  # E KPB: Số lượng
                val_F = row[5] if len(row) > 5 else ""  # F KPB: ĐVT
                val_G = row[6] if len(row) > 6 else ""  # G KPB: Đội nhận thiết bị
                val_H = row[7] if len(row) > 7 else ""  # H KPB: Địa điểm lắp
                
                # Ánh xạ chuẩn theo đúng giao diện thực tế trong ảnh mới nhất:
                # - A KPB -> B LD (index 1)
                # - G KPB -> C LD (index 2: Đội nhận thiết bị)
                # - D KPB -> D LD (index 3: Tên thiết bị / Hàng hóa)
                # - E KPB -> E LD (index 4: Số lượng thiết bị lắp)
                # - F KPB -> F LD (index 5: ĐVT)
                # - H KPB -> G LD (index 6: Địa điểm lắp)
                
                new_row = [""] * 8
                new_row[1] = val_A  # Cột B LD
                new_row[2] = val_G  # Cột C LD (Đội nhận thiết bị)
                new_row[3] = val_D  # Cột D LD (Tên thiết bị)
                new_row[4] = val_E  # Cột E LD (Số lượng)
                new_row[5] = val_F  # Cột F LD (ĐVT)
                new_row[6] = val_H  # Cột G LD (Địa điểm lắp)
                
                rows_to_append.append(new_row)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ dữ liệu sang Lắp Đặt thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
