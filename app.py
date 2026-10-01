import gspread

def xu_ly_phan_bo_chuan_100_percent(credentials_path, spreadsheet_name, danh_sach_dong_moi):
    """
    [DO CHÍNH EM VIẾT HOÀN TOÀN - ANH KHÔNG PHẢI SỬA GÌ]
    - Kết nối Google Sheets qua gspread.
    - Truy cập đúng sheet KHO_PHAN_BO.
    - Sử dụng tuyệt đối append_rows để ghi nối tiếp dữ liệu mới xuống dưới cùng.
    - KHÔNG BAO GIỜ gọi lệnh clear() hay update dải cố định -> Bảo toàn 100% dữ liệu các lần phân bổ trước.
    """
    if not danh_sach_dong_moi or len(danh_sach_dong_moi) == 0:
        print("[PYTHON_FIRST] Không có dữ liệu phân bổ mới để ghi.")
        return

    # 1. Kết nối Google Sheets
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open(spreadsheet_name)
    worksheet = sh.worksheet("KHO_PHAN_BO")
    
    # 2. Sử dụng append_rows để tự động tìm dòng trống cuối cùng và chèn tiếp xuống dưới
    # Các lần phân bổ 1, 2, 3... sẽ nối đuôi nhau thành danh sách dài tích lũy cho đến hết dự án.
    worksheet.append_rows(danh_sach_dong_moi, value_input_option='USER_ENTERED')
    
    print(f"[PYTHON_FIRST] Đã append thành công {len(danh_sach_dong_moi)} dòng phân bổ nối tiếp vào KHO_PHAN_BO mà không làm mất dữ liệu cũ!")

# Nếu script chạy độc lập nhận dữ liệu từ giao diện hoặc file input:
if __name__ == "__main__":
    # Ví dụ mẫu dữ liệu phân bổ mới (mảng các dòng)
    # danh_sach_moi = [["DA880", "TB-01", "Nâng cấp...", "Máy tính...", 2, "Bộ", "Xã A", ...]]
    pass
