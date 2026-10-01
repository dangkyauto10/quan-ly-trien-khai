# 1. Lấy toàn bộ dữ liệu hiện tại của sheet KHO_PHAN_BO để xác định dòng trống tiếp theo
existing_data = worksheet_kho_phan_bo.get_all_values()
next_row = len(existing_data) + 1

# Nếu bảng trống hoặc chỉ có tiêu đề (ví dụ dòng 1, 2 là tiêu đề)
if next_row < 3:
    next_row = 3

# 2. Ghi danh sách phân bổ mới nối tiếp vào dưới cùng (không làm mất dữ liệu cũ của lần 1)
# Ví dụ dữ liệu đợt 2 nằm trong biến `new_allocation_rows`
worksheet_kho_phan_bo.update(f"A{next_row}:H{next_row + len(new_allocation_rows) - 1}", new_allocation_rows)
