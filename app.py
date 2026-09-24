import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

# Cấu hình giao diện ứng dụng
st.set_page_config(
    page_title="Báo Cáo Triển Khai Dự Án",
    page_icon="📱",
    layout="centered"
)

# -------------------------------------------------------------
# 1. KẾT NỐI GOOGLE SHEETS
# -------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def ket_noi_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        
        client = gspread.authorize(creds)
        return client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return None

sh = ket_noi_sheets()

# -------------------------------------------------------------
# 2. ĐỌC DANH MỤC ĐIỂM
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_diem = {}

if sh:
    try:
        ws_diem = sh.worksheet("DANH_SACH_DIEM")
        records = ws_diem.get_all_records()
        for row in records:
            ten_diem = str(row.get("TEN_DIEM", "")).strip()
            sl_thau = row.get("SO_LUONG_THIET_BI", 0)
            if ten_diem:
                danh_sach_diem[ten_diem] = sl_thau
    except Exception:
        pass

if not danh_sach_diem:
    danh_sach_diem = {
        "Phường Minh Xuân": 5,
        "Phường Phan Thiết": 4,
        "Xã Kim Phú": 6,
        "Xã Tràng Đà": 3
    }

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO
# -------------------------------------------------------------
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động & ghi nhận hiện trường")

st.markdown("---")
st.subheader("1. Xác nhận thông tin thực hiện")

can_bo_chon = st.selectbox("Cán bộ / Đội trưởng thực hiện:", options=danh_sach_ktv)
diem_chon = st.selectbox("Chọn Điểm lắp đặt thuộc phân công:", options=list(danh_sach_diem.keys()))

sl_dinh_muc = danh_sach_diem.get(diem_chon, 0)
st.info(f"📦 **Số lượng thiết bị phân bổ theo thầu:** {sl_dinh_muc} thiết bị")

sl_thuc_te = st.number_input(
    "Số lượng thiết bị thực tế:",
    min_value=1,
    max_value=1000,
    value=int(sl_dinh_muc) if sl_dinh_muc else 1,
    step=1
)

# -------------------------------------------------------------
# 4. TỰ ĐỘNG BẮT TỌA ĐỘ GPS (KHÔNG CẦN DÁN THỦ CÔNG)
# -------------------------------------------------------------
st.markdown("---")
st.subheader("2. Định vị Hiện trường (GPS)")

location = get_geolocation()

link_maps_tu_dong = ""
if location and "coords" in location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    link_maps_tu_dong = f"https://www.google.com/maps?q={lat},{lon}"
    st.success(f"📍 Đã nhận diện vị trí vệ tinh: {lat:.5f}, {lon:.5f}")
else:
    st.warning("⚠️ Nếu điện thoại hỏi quyền truy cập vị trí, hãy chọn 'Cho phép' (Allow).")

link_gps_cuoi = st.text_input(
    "Link Google Maps (Tự động điền khi nhận GPS):",
    value=link_maps_tu_dong,
    placeholder="https://www.google.com/maps?q=..."
)

# -------------------------------------------------------------
# 5. GHI DỮ LIỆU CHUẨN GIỜ VIỆT NAM (GMT+7)
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3. Xác nhận hoàn thành công việc")

col1, col2 = st.columns(2)

def ghi_du_lieu_bao_cao(loai_hinh):
    if not sh:
        st.error("Không có kết nối với Google Sheets.")
        return
    
    with st.spinner("Đang lưu dữ liệu về hệ thống..."):
        try:
            ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
            # Chuẩn hóa giờ Việt Nam (GMT+7)
            tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
            thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
            
            dong_moi = [
                thoi_gian_vn,        # Cột A: Dấu thời gian chuẩn giờ VN
                can_bo_chon,         # Cột B: Tên đội thực hiện
                diem_chon,           # Cột C: Điểm lắp đặt
                sl_thuc_te,          # Cột D: Số lượng thiết bị thực tế
                link_gps_cuoi,       # Cột E: Link Google Maps
                loai_hinh            # Cột F: Trạng thái thực hiện
            ]
            ws_bc.append_row(dong_moi)
            st.success(f"✅ Ghi nhận thành công: {loai_hinh} tại {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu: {e}")

with col1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        ghi_du_lieu_bao_cao("Đã giao hàng")

with col2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        ghi_du_lieu_bao_cao("Đã lắp đặt xong")
