import streamlit as st

# Thiết lập giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Quản Lý Triển Khai - DA880", layout="wide")

st.title("🚀 Hệ Thống Quản Lý Triển Khai & Điều Hành (DA880)")
st.success("🟢 Ứng dụng đã khởi động thành công và sẵn sàng thao tác!")

# Menu 4 Module chuẩn vận hành
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

if menu == "Trang chủ & Lãnh đạo Theo Dõi":
    st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm DA880", "880", "100%")
    col2.metric("Giao Hàng", "Sẵn sàng", "OK")
    col3.metric("Lắp Đặt", "Ổn định", "OK")
    col4.metric("Nghiệm Thu", "Active", "OK")
    st.info("Hệ thống quản lý tự động đã sẵn sàng kết nối dữ liệu.")

elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến")
    st.write("Khu vực hiển thị danh sách đăng ký và thao tác duyệt của Admin.")
    st.text_input("Tìm kiếm thành viên hoặc tuyến...")

elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
    st.write("Kiểm soát số lượng xuất nhập vật tư và phân bổ cho các điểm triển khai.")

elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Lắp Đặt")
    st.write("Theo dõi tiến độ chuyến xe, mã công việc và bàn giao hiện trường.")

elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (KTV)")
    st.write("Giao diện tối ưu cho KTV thao tác nhanh chóng trên điện thoại:")
    with st.form("baocao_form"):
        ktv_name = st.text_input("Họ và tên KTV")
        diadiem = st.text_input("Địa điểm / Mã trạm")
        trangthai = st.selectbox("Trạng thái công việc", ["Chờ lắp đặt", "Đã giao hàng & Lắp đặt hoàn tất"])
        if st.form_submit_button("📍 XÁC NHẬN BÁO CÁO NGHIỆM THU"):
            st.success(f"Đã ghi nhận báo cáo của KTV {ktv_name} tại {diadiem}!")
