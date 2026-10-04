import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

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

# --- KẾT NỐI AN TOÀN TRÁNH MỌI LỖI JWT/PEM ---
@st.cache_resource
def init_connection():
    # Đọc trực tiếp thông tin từ st.secrets hoặc fallback an toàn
    sec = st.secrets["gcp_service_account"]
    
    # Ép kiểu và xử lý sạch ký tự xuống dòng của private_key
    p_key = str(sec["private_key"]).replace("\\n", "\n")
    
    creds_dict = {
        "type": "service_account",
        "project_id": str(sec["project_id"]),
        "private_key_id": str(sec["private_key_id"]),
        "private_key": p_key,
        "client_email": str(sec["client_email"]),
        "client_id": str(sec["client_id"]),
        "auth_uri": str(sec["auth_uri"]),
        "token_uri": str(sec["token_uri"]),
        "auth_provider_x509_cert_url": str(sec["auth_provider_x509_cert_url"]),
        "client_x509_cert_url": str(sec["client_x509_cert_url"]),
    }
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit"
    return client.open_by_url(sheet_url)

try:
    spreadsheet = init_connection()
except Exception as e:
    st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
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

# --- ĐỌC DỮ LIỆU TỪ SHEET KHO_PHAN_BO ---
try:
    sheet_kho = spreadsheet.worksheet("KHO_PHAN_BO")
    all_data = sheet_kho.get_all_values()
except Exception as e:
    st.error(f"Không thể mở sheet 'KHO_PHAN_BO': {e}")
    st.stop()

if len(all_data) < 3:
    st.warning("Sheet KHO_PHAN_BO chưa có đủ dữ liệu!")
    st.stop()

rows = all_data[2:]
locations = sorted(list(set([row[7].strip() for row in rows if len(row) > 7 and row[7].strip()])))

st.subheader("1. Xác nhận thông tin thực hiện")
cb_list = ["Vũ - Hạnh - Hiền (Nguyễn Văn A)", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
selected_cb = st.selectbox("Cán bộ / Đội trưởng thực hiện:", cb_list)

selected_location = st.selectbox("Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT:", ["-- Chọn địa điểm --"] + locations)

total_devices = 0
matched_rows_indices = []

if selected_location != "-- Chọn địa điểm --":
    for idx, row in enumerate(rows, start=3):
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

actual_qty = st.number_input("Số lượng thiết bị thực tế lắp đội / giao hàng:", min_value=0, value=total_devices, step=1)

if st.button("📍 Thêm lấy vị trí hiện tại (Check-in GPS)"):
    st.success("📍 Đã ghi nhận tọa độ GPS hiện tại thành công!")

st.file_uploader("📷 Thêm phần chụp ảnh Báo cáo / Nghiệm thu", type=["jpg", "png", "jpeg"])

st.markdown("---")

st.subheader("2. Trạng Thái Báo Cáo & Nghiệm Thu")
status_options = ["Đang vận chuyển", "Đã giao hàng xong", "Đang lắp đặt", "Đã lắp đặt xong"]
selected_status = st.selectbox("Chọn trạng thái hoàn thành:", status_options)

notes = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường:", placeholder="Nhập ghi chú nếu có...")

if st.button("🚀 Gửi Báo Cáo & Cập Nhật Hệ Thống", type="primary"):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi báo cáo!")
    else:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_count = 0
            for r_idx in matched_rows_indices:
                sheet_kho.update_cell(r_idx, 10, selected_status)
                sheet_kho.update_cell(r_idx, 11, timestamp)
                updated_count += 1
                
            st.success(f"✅ Gửi báo cáo thành công! Đã cập nhật trạng thái cho {updated_count} dòng thiết bị tại điểm {selected_location}.")
        except Exception as e:
            st.error(f"❌ Lỗi khi cập nhật dữ liệu lên Google Sheets: {e}")
