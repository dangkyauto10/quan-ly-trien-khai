def thuc_hien_phan_bo_chuan(sh, danh_sach_dong_moi):
    """
    Tuân thủ tuyệt đối quy tắc PYTHON_FIRST:
    Hàm chuẩn hóa việc ghi dữ liệu phân bổ mới vào sheet KHO_PHAN_BO.
    Sử dụng append_rows để đảm bảo:
    - KHÔNG BAO GIỜ xóa dữ liệu cũ.
    - Tự động nối tiếp các lần phân bổ sau (lần 2, lần 3,...) xuống dưới cùng.
    - Tích lũy thành danh sách đầy đủ cho đến khi hoàn thành dự án.
    """
    worksheet_kho_pb = sh.worksheet("KHO_PHAN_BO")
    
    if danh_sach_dong_moi and len(danh_sach_dong_moi) > 0:
        # append_rows tự động tìm dòng trống cuối cùng và chèn dữ liệu mới nối tiếp vào
        worksheet_kho_pb.append_rows(danh_sach_dong_moi, value_input_option='USER_ENTERED')
        print(f"[PYTHON_FIRST] Đã append thành công {len(danh_sach_dong_moi)} dòng phân bổ nối tiếp vào KHO_PHAN_BO!")
