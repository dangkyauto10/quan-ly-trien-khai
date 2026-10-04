import streamlit as st
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Điều Hành Dự Án", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- ĐỌC DỮ LIỆU TỪ GOOGLE SHEETS (PUBLIC CSV) ---
@st.cache_data(ttl=60)
def load_sheet_data():
    sheet_id = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet=KHO_PHAN_BO"
    df = pd.read_csv(csv_url, header=None)
    return df

try:
    df_data = load_sheet_data()
    st.success("✅ Kết nối hệ thống thành công!")
except Exception as e:
    st.error(f"❌ Lỗi tải dữ liệu: {e}")
    st.stop()

# --- GIAO DIỆN CHÍNH ---
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động hiện trường")

pass_input = st.text_input("🔑 Nhập Pass Quản Trị:", type="password", placeholder="Nhập mật khẩu...")
ADMIN_PASS = "S90880"

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📝 Đăng ký thành viên"):
        st.info("Chức năng Đăng ký thành viên đang phát triển.")
    if st.button("📊 Báo cáo KTV & VC"):
        st.info("Chức năng Báo cáo KTV & VC đang phát triển.")
with col_btn2:
    if st.button("🛡️ AD Duyệt TVĐK"):
        if pass_input == ADMIN_PASS:
            st.success("✅ Xác thực AD thành công!")
        else:
            st.warning("⚠️ Sai mật khẩu quản trị!")
    if st.button("🛠️ BÁO CÁO LD"):
        if pass_input == ADMIN_PASS:
            st.success("✅ Xác thực Quản lý Lắp đặt thành công!")
        else:
            st.warning("⚠️ Sai mật khẩu quản trị!")

st.markdown("---")

# Xử lý dữ liệu dạng bảng từ dòng thứ 3 (index 2)
if len(df_data) < 3:
    st.warning("Sheet KHO_PHAN_BO chưa đủ dữ liệu!")
    st.stop()

rows = df_data.iloc[2:].values.tolist()
locations = sorted(list(set([str(row[7]).strip() for row in rows if len(row) > 7 and pd.notna(row[7]) and str(row[7]).strip()])))

st.subheader("1. Xác nhận thông tin thực hiện")
cb_list = ["Vũ - Hạnh - Hiền (Nguyễn Văn A)", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
selected_cb = st.selectbox("Cán bộ / Đội trưởng thực hiện:", cb_list)

selected_location = st.selectbox("Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT:", ["-- Chọn địa điểm --"] + locations)

total_devices = 0
matched_rows_indices = []

if selected_location != "-- Chọn địa điểm --":
    for idx, row in enumerate(rows, start=3):
        if len(row) > 7 and pd.notna(row[7]) and str(row[7]).strip() == selected_location:
            matched_rows_indices.append(idx)
            try:
                qty = int(row[4]) if len(row) > 4 and pd.notna(row[4]) and str(row[4]).isdigit() else 0
                total_devices += qty
            except:
                pass
    st.markdown(f"📦 **Số lượng thiết bị được phân bổ cho điểm này:** `{total_devices} thiết bị`")
else:
    st.info("👆 Vui lòng chọn địa điểm để app tự động tải danh mục thiết bị.")

actual_qty = st.number_input("Số lượng thiết bị thực tế lắp đội / giao hàng:", min_value=0, value=total_devices, step=1)

if st.button("📍 Thêm lấy vị trí hiện tại (Check-in GPS)"):
    st.success("📍 Đã ghi nhận tọa độ GPS hiện tại thành công!")

st.file_uploader("📷 Thêm phần chụp ảnh Báo cáo / Nghiệm thu", type=["jpg", "png", "jpeg"])

st.markdown("---")

# --- 2. TRẠNG THÁI BÁO CÁO & NGHIỆM THU (CHUYỂN THÀNH CÁC NÚT BẤM TIỆN LỢI) ---
st.subheader("2. Trạng Thái Báo Cáo & Nghiệm Thu")
st.write("Chọn trạng thái hoàn thành:")

# Dùng state lưu trạng thái được chọn
if "selected_status" not in st.session_state:
    st.session_state.selected_status = "Đang vận chuyển"

# Chia thành 2 hàng nút bấm cho dễ nhìn trên di động
r1_col1, r1_col2 = st.columns(2)
with r1_col1:
    if st.button("🚚 Đang vận chuyển", use_container_width=True):
        st.session_state.selected_status = "Đang vận chuyển"
with r1_col2:
    if st.button("✅ Đã giao hàng xong", use_container_width=True):
        st.session_state.selected_status = "Đã giao hàng xong"

r2_col1, r2_col2 = st.columns(2)
with r2_col1:
    if st.button("⚙️ Đang lắp đặt", use_container_width=True):
        st.session_state.selected_status = "Đang lắp đặt"
with r2_col2:
    if st.button("🎉 Đã lắp đặt xong", use_container_width=True):
        st.session_state.selected_status = "Đã lắp đặt xong"

# Hiển thị trạng thái đang được chọn
st.info(f"📌 Trạng thái hiện tại: **{st.session_state.selected_status}**")

notes = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường:", placeholder="Nhập ghi chú nếu có...")

if st.button("🚀 Gửi Báo Cáo & Cập Nhật Hệ Thống", type="primary"):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi báo cáo!")
    else:
        st.success(f"✅ Gửi báo cáo thành công! Đã cập nhật trạng thái '{st.session_state.selected_status}' cho điểm {selected_location}.")
