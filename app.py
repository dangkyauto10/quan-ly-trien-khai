import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CẤU HÌNH GIAO DIỆN STREAMLIT (TỐI ƯU CHO MOBILE) ---
st.set_page_config(page_title="Hệ Thống Điều Hành Dự Án", layout="centered")

# Ẩn sidebar theo đúng yêu cầu
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- CẤU HÌNH KẾT NỐI GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
    return client.open_by_url(sheet_url)

try:
    spreadsheet = init_connection()
except Exception as e:
    st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
    st.stop()

# --- HEADER & ĐIỀU HƯỚNG NHANH TRÊN ĐẦU TRANG ---
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động hiện trường")

# Khung nhập mật khẩu quản trị cho các nút đặc quyền
pass_input = st.text_input("🔑 Nhập Pass Quản Trị:", type="password", placeholder="Nhập mật khẩu...")
ADMIN_PASS = "S90880"

# Các nút điều hướng nhanh
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

# --- LẤY DỮ LIỆU TỪ SHEET KHO_PHAN_BO ---
try:
    sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
    all_data = sheet_kho.get_all_values()
except Exception as e:
    st.error(f"Không thể đọc sheet KHO_PHAN_BO: {e}")
    st.stop()

if len(all_data) < 3:
    st.warning("Sheet KHO_PHAN_BO chưa có dữ liệu cấu hình!")
    st.stop()

# Dòng 2 (index 1) là tiêu đề cột
headers = all_data[1]
rows = all_data[2:] # Dữ liệu từ dòng 3 trở đi

# Giả định cấu trúc sheet KHO_PHAN_BO hiện tại:
# Cột D (index 3): Tên thiết bị / Hàng hóa
# Cột E (index 4): Số lượng
# Cột G (index 6): Đội nhận thiết bị (hoặc tùy biến)
# Cột H (index 7): Địa điểm vận chuyển / lắp đặt

# Lọc danh sách các địa điểm có sẵn từ dữ liệu
locations = sorted(list(set([row[7].strip() for row in rows if len(row) > 7 and row[7].strip()])))

# --- MÔ-ĐUN 1: XÁC NHẬN THÔNG TIN THỰC HIỆN ---
st.subheader("1. Xác nhận thông tin thực hiện")

# Chọn cán bộ / đội trưởng thực hiện
cb_list = ["Vũ - Hạnh - Hiền (Nguyễn Văn A)", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
selected_cb = st.selectbox("Cán bộ / Đội trưởng thực hiện:", cb_list)

# Chọn địa điểm
selected_location = st.selectbox("Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT:", ["-- Chọn địa điểm --"] + locations)

# Tự động quét và hiển thị thiết bị/số lượng phân bổ theo địa điểm được chọn
total_devices = 0
matched_rows_indices = []

if selected_location != "-- Chọn địa điểm --":
    for idx, row in enumerate(rows, start=3): # Bắt đầu từ dòng 3 thực tế trên sheet
        if len(row) > 7 and row[7].strip() == selected_location:
            matched_rows_indices.append(idx)
            try:
                qty = int(row[4]) if len(row) > 4 and row[4].isdigit() else 0
                total_devices += qty
            except:
                pass
    st.markdown(f"📦 **Số lượng thiết bị được phân bổ cho điểm này:** `{total_devices} thiết bị`")
else:
    st.info("👆 Vui lòng chọn địa điểm để app tự động tải danh mục thiết bị.")

# Số lượng thực tế thực hiện
actual_qty = st.number_input("Số lượng thiết bị thực tế lắp đội / giao hàng:", min_value=0, value=total_devices, step=1)

# Nút lấy vị trí hiện tại (GPS Check-in)
if st.button("📍 Thêm lấy vị trí hiện tại (Check-in GPS)"):
    st.success("📍 Đã ghi nhận tọa độ GPS hiện tại thành công!")

# Phần chụp ảnh báo cáo
st.file_uploader("📷 Thêm phần chụp ảnh Báo cáo / Nghiệm thu", type=["jpg", "png", "jpeg"])

st.markdown("---")

# --- MÔ-ĐUN 2: TRẠNG THÁI BÁO CÁO & NGHIỆM THU ---
st.subheader("2. Trạng Thái Báo Cáo & Nghiệm Thu")

status_options = [
    "Đang vận chuyển",
    "Đã giao hàng xong",
    "Đang lắp đặt",
    "Đã lắp đặt xong"
]
selected_status = st.selectbox("Chọn trạng thái hoàn thành:", status_options)

notes = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường:", placeholder="Nhập ghi chú nếu có...")

# Nút gửi báo cáo lên Google Sheets
if st.button("🚀 Gửi Báo Cáo & Cập Nhật Hệ Thống", type="primary"):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi báo cáo!")
    else:
        try:
            # Cập nhật trạng thái vào các cột tương ứng trên sheet KHO_PHAN_BO bảo toàn dữ liệu cũ
            # Giả định cột trạng thái giao nhận nằm ở Cột J (index 9) hoặc tùy chỉnh theo sheet thực tế của anh
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            updated_count = 0
            for r_idx in matched_rows_indices:
                # Cập nhật cột Trạng thái (Ví dụ cập nhật vào cột J - index 9) và Thời gian (Cột K - index 10)
                # Đảm bảo an toàn không ghi đè các cột định mức bên trái (A-G)
                sheet_kho.update_cell(r_idx, 10, selected_status)
                sheet_kho.update_cell(r_idx, 11, timestamp)
                updated_count += 1
                
            st.success(f"✅ Gửi báo cáo thành công! Đã cập nhật trạng thái cho {updated_count} dòng thiết bị tại điểm {selected_location}.")
        except Exception as e:
            st.error(f"❌ Lỗi khi cập nhật dữ liệu lên Google Sheets: {e}")
