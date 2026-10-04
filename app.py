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
                val_A = row[0] if len(row) > 0 else ""  # Mã dự án
                val_D = row[3] if len(row) > 3 else ""  # Tên thiết bị / Hàng hóa
                val_E = row[4] if len(row) > 4 else ""  # Số lượng
                val_F = row[5] if len(row) > 5 else ""  # Đơn vị tính
                val_G = row[6] if len(row) > 6 else ""  # Cột G KPB
                val_H = row[7] if len(row) > 7 else ""  # Cột H KPB
                
                # Ánh xạ chuẩn theo đúng yêu cầu:
                # - A KPB -> B LD (Index 1)
                # - D KPB -> D LD (Index 3)
                # - E KPB -> E LD (Index 4)
                # - F KPB -> F LD (Index 5)
                # - G KPB -> Cột C LD (Index 2 - Đội nhận thiết bị)
                # - H KPB -> G LD (Index 6)
                
                new_row = [""] * 7
                new_row[1] = val_A  # B của LD
                new_row[3] = val_D  # D của LD
                new_row[4] = val_E  # E của LD
                new_row[5] = val_F  # F của LD
                new_row[2] = val_G  # C của LD (Đội nhận thiết bị)
                new_row[6] = val_H  # G của LD
                
                rows_to_append.append(new_row)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ dữ liệu sang Lắp Đặt thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
