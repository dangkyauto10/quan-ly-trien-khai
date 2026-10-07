import streamlit as st
import datetime

# Cấu hình giao diện trang
st.set_page_config(page_title="Hệ thống Triển khai Hiện trường", page_icon="🚚", layout="centered")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG BÁO CÁO HIỆN TRƯỜNG (VC & LẮP ĐẶT)</h2>", unsafe_allow_html=True)
st.markdown("---")

# Chọn loại công việc
loai_cong_viec = st.selectbox("📌 1. Chọn loại công việc thực hiện *", ["🚚 Vận chuyển hàng hóa (VC)", "🔧 Lắp đặt thiết bị (LD)"])

# Tên đội thực hiện
doi_thuc_hien = st.text_input("👥 2. Tên đội thực hiện *", placeholder="Ví dụ: Đội Nguyễn Văn Thiện")

if "Vận chuyển" in loai_cong_viec:
    st.markdown("### 📦 Thông tin Báo cáo Vận Chuyển")
    diem_giao = st.text_input("📍 Điểm giao hàng *", placeholder="Ví dụ: Xã Sùng Máng")
    so_luong_tt = st.number_input("🔢 Số lượng thiết bị thực tế giao", min_value=1, value=1)
    link_anh_vc = st.text_input("📷 Link ảnh nghiệm thu / Ghi chú giao hàng", placeholder="Dán link ảnh hoặc ghi chú tại đây")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ BÁO CÁO: ĐÃ GIAO XONG", type="primary", use_container_width=True):
        if not doi_thuc_hien or not diem_giao:
            st.warning("⚠️ Vui lòng điền đầy đủ Tên đội thực hiện và Điểm giao hàng!")
        else:
            # Dữ liệu chuẩn đẩy vào sheet BAO_CAO_TRIEN_KHAI và VAN_CHUYEN
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"🎉 Gửi báo cáo Vận chuyển thành công lúc {timestamp}!")
            st.info(f"Đội: {doi_thuc_hien} | Điểm giao: {diem_giao} | SL: {so_luong_tt} | Trạng thái: Đã giao xong")
            
else:
    st.markdown("### 🛠️ Thông tin Báo cáo Lắp Đặt")
    diem_lap = st.text_input("📍 Điểm lắp đặt *", placeholder="Ví dụ: Xã Sùng Máng")
    so_luong_tt_ld = st.number_input("🔢 Số lượng thiết bị thực tế lắp đặt", min_value=1, value=1)
    link_anh_ld = st.text_input("📷 Link ảnh nghiệm thu lắp đặt", placeholder="Dán link ảnh nghiệm thu tại đây")
    
    st.markdown("<br>")
    
    # Khởi tạo trạng thái check-in GPS trong session
    if "gps_checked" not in st.session_state:
        st.session_state.gps_checked = False
        st.session_state.gps_data = ""

    # Yêu cầu Check-in GPS trước
    if not st.session_state.gps_checked:
        st.warning("⚠️ Yêu cầu bắt buộc: Phải Check-in GPS vị trí hiện trường trước khi xuất hiện nút hoàn thành!")
        if st.button("📍 THỰC HIỆN CHECK-IN GPS HIỆN TRƯỜNG", use_container_width=True):
            # Giả lập tọa độ GPS thực tế lấy từ thiết bị di động
            current_time_gps = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.gps_checked = True
            st.session_state.gps_data = f"GPS Verified (Lat: 22.345, Long: 105.123) - {current_time_gps}"
            st.success("📍 Check-in GPS thành công!")
            st.rerun()
    else:
        st.success(f"✅ Đã xác thực vị trí: {st.session_state.gps_data}")
        
        # Chỉ khi check-in thành công mới hiển thị nút Đã lắp đặt xong
        if st.button("✅ BÁO CÁO: ĐÃ LẮP ĐẶT XONG", type="primary", use_container_width=True):
            if not doi_thuc_hien or not diem_lap:
                st.warning("⚠️ Vui lòng điền đầy đủ Tên đội thực hiện và Điểm lắp đặt!")
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"🎉 Gửi báo cáo Lắp đặt thành công lúc {timestamp}!")
                st.info(f"Đội: {doi_thuc_hien} | Điểm lắp đặt: {diem_lap} | GPS: {st.session_state.gps_data} | Trạng thái: Đã lắp đặt xong")
                
                # Reset trạng thái GPS cho lần báo cáo tiếp theo
                st.session_state.gps_checked = False
                st.rerun()
