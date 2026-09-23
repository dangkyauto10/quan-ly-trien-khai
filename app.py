import streamlit as st
import pandas as pd

st.title("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")

# Đưa trực tiếp dữ liệu dạng bảng vào đây để chạy offline trên Cloud, loại bỏ hoàn toàn lỗi mạng
data = {
    "STT": [1, 2, 3],
    "Nội dung công việc": [
        "Khởi tạo hệ thống điều hành",
        "Triển khai ứng dụng di động",
        "Hoàn thiện báo cáo dự án"
    ],
    "Trạng thái": ["Đang thực hiện", "Hoàn thành", "Chờ duyệt"],
    "Ghi chú": ["Ổn định", "Đã xong", "Bản nháp"]
}

df = pd.DataFrame(data)

st.success("Đã kết nối và hiển thị hệ thống thành công!")
st.dataframe(df, use_container_width=True)
