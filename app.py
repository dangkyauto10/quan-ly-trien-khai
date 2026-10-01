def ghi_nhan_phan_bo_vao_kho(sh, danh_sach_phan_bo_moi):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Đoạn code chuẩn hóa logic ghi dữ liệu vào sheet KHO_PHAN_BO.
    Luôn tự động tìm dòng trống tiếp theo để append dữ liệu mới, 
    giữ nguyên vẹn toàn bộ dữ liệu phân bổ từ các lần trước.
    """
    worksheet_kho_pb = sh.worksheet("KHO_PHAN_BO")
    
    # 1. Lấy toàn bộ dữ liệu hiện tại của sheet để xác định chính xác dòng trống tiếp theo
    existing_data = worksheet_kho_pb.get_all_values()
    next_row = len(existing_data) + 1
    
    # Đảm bảo không ghi đè lên phần tiêu đề (giả sử tiêu đề nằm ở dòng 1 và 2)
    if next_row < 3:
        next_row = 3
        
    # 2. Nếu có danh sách phân bổ mới, tiến hành ghi nối tiếp vào các dòng phía dưới
    if danh_sach_phan_bo_moi:
        # Xác định dải ô bắt đầu từ dòng trống tiếp theo, trải dài đủ số lượng dòng và cột cần ghi
        num_rows = len(danh_sach_phan_bo_moi)
        num_cols = len(danh_sach_phan_bo_moi[0]) if num_rows > 0 else 1
        
        # Chuyển đổi chỉ số cột sang dạng chữ cái Excel (A, B, C...)
        end_col_letter = gspread.utils.rowcol_to_a1(1, num_cols).rstrip('1')
        range_string = f"A{next_row}:{end_col_letter}{next_row + num_rows - 1}"
        
        # Ghi nối tiếp dữ liệu mới (giữ lại 100% dữ liệu các lần phân bổ cũ ở phía trên)
        worksheet_kho_pb.update(range_string, danh_sach_phan_bo_moi)
        print(f"[PYTHON_FIRST] Đã ghi nối tiếp thành công {num_rows} dòng phân bổ mới từ dòng {next_row}!")
