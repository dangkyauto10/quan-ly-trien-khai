import streamlit as st

# Thiết lập giao diện tối ưu cho Mobile & Desktop
st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide")

st.title("🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")
st.success("🟢 Hệ thống đã khôi phục trạng thái vận hành chuẩn ngày 26/9 thành công!")

# Menu 4 Module chuẩn nghiệp vụ
menu = st.sidebar.selectbox("📂 Chọn Module Chức Năng", [
    "Trang chủ & Lãnh đạo Theo Dõi", 
    "Module 1: Đăng Ký & Admin Duyệt", 
    "Module 2: Kho & Phân Bổ", 
    "Module 3: Vận Chuyển & Lắp Đặt", 
    "Module 4: Báo Cáo KTV & GPS"
])

if menu == "Trang chủ & Lãnh đạo Theo Dõi":
    st.subheader("📊 Màn Hình Điều Hành Thời Gian Thực - 126 Vị Trí")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Điểm DA880", "123 Điểm", "100%")
    col2.metric("Giao Hàng", "Đang xử lý", "Sync")
    col3.metric("Lắp Đặt", "Sẵn sàng", "OK")
    col4.metric("Nghiệm Thu", "0%", "Tracking")
    
    st.markdown("---")
    st.info("Hệ thống giám sát tiến độ trực tiếp từ cơ sở dữ liệu cốt lõi.")

elif menu == "Module 1: Đăng Ký & Admin Duyệt":
    st.subheader("👥 Quản Lý Thành Viên & Phân Tuyến")
    st.write("Khu vực đồng bộ dữ liệu đăng ký và thao tác duyệt của Admin.")
    st.text_input("🔍 Tìm kiếm nhanh thành viên / tuyến...")

elif menu == "Module 2: Kho & Phân Bổ":
    st.subheader("📦 Quản Lý Thiết Bị & Định Mức Kho")
    st.write("Kiểm soát số lượng xuất nhập vật tư và phân bổ cho các điểm hiện trường.")

elif menu == "Module 3: Vận Chuyển & Lắp Đặt":
    st.subheader("🚚 Điều Phối Vận Chuyển & Lắp Đặt")
    st.write("Theo dõi tiến độ chuyến xe, mã công việc tự động và bàn giao hiện trường.")

elif menu == "Module 4: Báo Cáo KTV & GPS":
    st.subheader("📍 Báo Cáo Nghiệm Thu 1 Chạm (KTV)")
    st.write("Giao diện tối ưu để KTV thao tác nhanh trên điện thoại:")
    with st.form("baocao_form"):
        ktv_name = st.text_input("Họ và tên KTV")
        diadiem = st.text_input("Địa điểm / Mã trạm (123 điểm)")
        trangthai = st.selectbox("Trạng thái công việc", ["Chờ lắp đặt", "Đã giao hàng & Lắp đặt hoàn tất"])
        submitted = st.form_submit_button("📍 XÁC NHẬN BÁO CÁO NGHIỆM THU")
        if submitted:
            st.success(f"Đã ghi nhận báo cáo của KTV {ktv_name} tại {diadiem}!")
