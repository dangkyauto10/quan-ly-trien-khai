import streamlit as st
import pandas as pd
import requests
import base64

st.set_page_config(
    page_title="Hệ Thống Quản Lý & Điều Hành Dự Án",
    page_icon="📡",
    layout="wide"
)

st.title("📡 HỆ THỐNG QUẢN LÝ & ĐIỀU HÀNH HIỆN TRƯỜNG")

MENU_OPTIONS = [
    "1. Đăng ký thành viên",
    "2. Báo cáo thực hiện của KTV",
    "3. Admin duyệt đăng ký thành viên",
    "4. Lãnh đạo theo dõi"
]

che_do_chon = st.radio("📌 Chọn chức năng hệ thống:", options=MENU_OPTIONS, horizontal=True)
st.markdown("---")

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCY-kns_lnNkgC-005rSYquDgcUgvBhdylHormgQktnydC0qhAfp62Lmm_9qLvrU6xIQ/exec"
ADMIN_PASS = "880880"

# Danh sách nguồn dữ liệu động theo đúng yêu cầu
DANH_SACH_DU_AN = [
    "Dự án 880 - Lắp đặt thiết bị viễn thông",
    "Dự án Mở rộng hạ tầng tuyến Tuyên Quang",
    "Dự án Triển khai trạm phát sóng Hà Giang",
    "🔍 [Tự nhập tên dự án khác...]"
]

DANH_SACH_THANH_VIEN = [
    "Nguyễn Văn Thiện",
    "Nguyễn Văn Hải",
    "Vỹ - Hạnh - Hiền",
    "Trần Văn B",
    "Đội KTV 006",
    "🔍 [Tự nhập tên thành viên khác...]"
]

if "danh_sach_cho_duyet" not in st.session_state:
    st.session_state.danh_sach_cho_duyet = []

# ================= MODULE 1 =================
if che_do_chon == "1. Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên Đội Thi Công")
    with st.form("form_dang_ky"):
        ho_ten = st.text_input("Họ và tên thành viên *")
        sdt = st.text_input("Số điện thoại / Zalo *")
        chuyen_mon = st.selectbox("Vai trò chuyên môn:", ["KTV Lắp đặt", "Vận chuyển thiết bị", "Kiêm nhiệm"])
        dia_ban = st.text_input("Địa bàn phụ trách *")
        if st.form_submit_button("GỬI YÊU CẦU ĐĂNG KÝ"):
            if not ho_ten or not sdt or not dia_ban:
                st.error("Vui lòng điền đầy đủ thông tin!")
            else:
                data = {"ho_ten": ho_ten, "sdt": sdt, "chuyen_mon": chuyên_mon, "dia_ban": dia_ban}
                st.session_state.danh_sach_cho_duyet.append(data)
                st.success(f"🎉 Đã gửi đăng ký cho {ho_ten} thành công!")

# ================= MODULE 2 =================
elif che_do_chon == "2. Báo cáo thực hiện của KTV":
    st.subheader("🛠️ Báo Cáo Hiện Trường Kỹ Thuật Viên")
    with st.form("form_bao_cao"):
        chon_da = st.selectbox("Chọn Tên Dự Án (Cột A - Sheet Danh sach du an):", options=DANH_SACH_DU_AN)
        ten_du_an = st.text_input("Nhập tên dự án cụ thể:") if "Tự nhập" in chon_da else chon_da
        
        chon_tv = st.selectbox("Tên Thành Viên (Cột B - Sheet quan ly doi):", options=DANH_SACH_THANH_VIEN)
        ten_thanh_vien = st.text_input("Nhập tên thành viên cụ thể:") if "Tự nhập" in chon_tv else chon_tv
        
        st.markdown("### 📍 Địa điểm & Vị trí (Làm giàu dữ liệu)")
        dia_diem = st.text_input("Địa điểm tác nghiệp cụ thể (Xã/Phường, Huyện/Tỉnh) *")
        link_gps = st.text_input("Link Google Maps / Tọa độ GPS:", value="https://maps.google.com/?q=21.83057,105.19236")
        
        st.markdown("### 📦 Công việc thực hiện")
        hang_muc = st.multiselect("Chọn hạng mục hoàn thành:", ["🚚 Giao hàng thiết bị", "🔧 Lắp đặt thiết bị", "✅ Bàn giao xong"])
        so_luong = st.number_input("Số lượng thiết bị:", value=5, step=1)
        ghi_chu = st.text_area("Ghi chú hiện trường:")
        file_anh = st.file_uploader("Tải ảnh hiện trường:", type=["jpg", "jpeg", "png"])
        
        if st.form_submit_button("🚀 GỬI BÁO CÁO"):
            if not dia_diem or not hang_muc:
                st.error("Vui lòng nhập địa điểm và chọn hạng mục!")
            else:
                st.success(f"🎉 Gửi báo cáo thành công cho dự án {ten_du_an}!")
                st.balloons()

# ================= MODULE 3 =================
elif che_do_chon == "3. Admin duyệt đăng ký thành viên":
    st.subheader("🔐 Quản Trị Viên: Duyệt Thành Viên Mới")
    pass_admin = st.text_input("🔑 Nhập mật khẩu Admin:", type="password")
    if pass_admin == ADMIN_PASS:
        st.success("🔓 Đã mở khóa quyền Admin.")
        danh_sach = st.session_state.danh_sach_cho_duyet
        if not danh_sach:
            st.info("Không có yêu cầu chờ duyệt.")
        else:
            for idx, tv in enumerate(danh_sach):
                with st.expander(f"👤 {tv['ho_ten']} - {tv['sdt']}"):
                    st.write(f"Chuyên môn: {tv['chuyen_mon']} | Địa bàn: {tv['dia_ban']}")
                    if st.button("✅ Phê duyệt", key=f"duyet_{idx}"):
                        st.session_state.danh_sach_cho_duyet.pop(idx)
                        st.rerun()
    elif pass_admin != "":
        st.error("❌ Sai mật khẩu! (Mã đúng: 880880)")

# ================= MODULE 4 =================
else:
    st.subheader("📊 Trung Tâm Giám Sát & Điều Hành (Lãnh Đạo)")
    pass_ld = st.text_input("🔑 Nhập mật khẩu Lãnh đạo:", type="password")
    if pass_ld == ADMIN_PASS:
        st.success("🔓 Đã mở khóa báo cáo lãnh đạo.")
        col1, col2 = st.columns(2)
        col1.metric("Tổng Dự Án", len(DANH_SACH_DU_AN))
        col2.metric("Tổng Thành Viên", len(DANH_SACH_THANH_VIEN))
    elif pass_ld != "":
        st.error("❌ Sai mật khẩu! (Mã đúng: 880880)")
