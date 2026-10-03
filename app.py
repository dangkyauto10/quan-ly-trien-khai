# --- MODULE 2: ĐỒNG BỘ TỪ KHO PHÂN BỔ SANG LẮP ĐẶT (LAP_DAT) ---
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
            # Duyệt qua dữ liệu từ dòng 3 của KHO_PHAN_BO (index từ 2)
            for row in kho_data[2:]:
                if not any(row): continue
                
                # Lấy dữ liệu từ các cột nguồn KPB (Lưu ý: Index mảng bắt đầu từ 0)
                # Cột A (index 0), Cột D (index 3), Cột E (index 4), Cột F (index 5), Cột G (index 6), Cột H (index 7)
                val_A_kpb = row[0] if len(row) > 0 else ""  # Mã dự án
                val_D_kpb = row[3] if len(row) > 3 else ""  # Tên thiết bị / Hàng hóa
                val_E_kpb = row[4] if len(row) > 4 else ""  # Số lượng
                val_F_kpb = row[5] if len(row) > 5 else ""  # Đơn vị tính
                val_G_kpb = row[6] if len(row) > 6 else ""  # (Cột G KPB)
                val_H_kpb = row[7] if len(row) > 7 else ""  # (Cột H KPB - Đội nhận / Điểm giao)
                
                # Mapping chuẩn theo đúng yêu cầu:
                # - A KPB -> B LD (Index 1)
                # - D KPB -> D LD (Index 3)
                # - E KPB -> E LD (Index 4)
                # - F KPB -> F LD (Index 5)
                # - G KPB -> Cột C LD (Index 2 - Đội nhận thiết bị)
                # - H KPB -> G LD (Index 6)
                
                # Tạo một dòng đủ rộng cho LAP_DAT (giả sử tối thiểu 7 cột từ A đến G)
                new_row = [""] * 7
                new_row[1] = val_A_kpb  # Cột B của LD
                new_row[3] = val_D_kpb  # Cột D của LD
                new_row[4] = val_E_kpb  # Cột E của LD
                new_row[5] = val_F_kpb  # Cột F của LD
                new_row[2] = val_G_kpb  # Cột C của LD (Đội nhận thiết bị)
                new_row[6] = val_H_kpb  # Cột G của LD
                
                rows_to_append.append(new_row)
            
            if rows_to_append:
                sheet_ld.append_rows(rows_to_append)
                st.success("✅ Đồng bộ dữ liệu sang Lắp Đặt thành công!")
    except Exception as e:
        st.error(f"Lỗi: {e}")
