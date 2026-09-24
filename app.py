import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Cấu hình giao diện ứng dụng
st.set_page_config(
    page_title="Báo Cáo Triển Khai Dự Án",
    page_icon="📱",
    layout="centered"
)

# -------------------------------------------------------------
# 1. KẾT NỐI GOOGLE SHEETS (HỖ TRỢ CẢ CLOUD SECRETS & LOCAL FILE)
# -------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def ket_noi_sheets():
    try:
        # Nếu chạy trên Streamlit Cloud (đọc cấu hình từ st.secrets)
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        else:
            # Nếu chạy trên máy tính cá nhân (đọc file credentials.json)
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        
        client = gspread.authorize(creds)
        # Mở bảng tính Google Sheets của dự án
        sh = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        return sh
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu Google Sheets: {e}")
        return None

sh = ket_noi_sheets()

# -------------------------------------------------------------
# 2. ĐỌC DỮ LIỆU DANH MỤC TỪ GOOGLE SHEETS
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

# Dữ liệu mặc định nếu chưa nạp được sheet
if not danh_sach_diem:
    danh_sach_diem = {
        "Phường Minh Xuân": 5,
        "Phường Phan Thiết": 4,
        "Xã Kim Phú": 6,
        "Xã Tràng Đà": 3
    }

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO HIỆN TRƯỜNG DỰ ÁN
# -------------------------------------------------------------
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động & ghi nhận hiện trường")

st.markdown("---")
st.subheader("1. Xác nhận thông tin thực hiện")

can_bo_chon = st.selectbox(
    "Cán bộ / Đội trưởng thực hiện:",
    options=danh_sach_ktv
)

diem_chon = st.selectbox(
    "Chọn Điểm lắp đặt thuộc phân công:",
    options=list(danh_sach_diem.keys())
)

sl_dinh_muc = danh_sach_diem.get(diem_chon, 0)
st.info(f"📦 **Số lượng thiết bị được phân bổ cho điểm này:** {sl_dinh_muc} thiết bị")

sl_thuc_te = st.number_input(
    "Số lượng thiết bị thực tế:",
    min_value=1,
    max_value=1000,
    value=int(sl_dinh_muc) if sl_dinh_muc else 1,
    step=1
)

# -------------------------------------------------------------
# 4. ĐỊNH VỊ VỊ TRÍ HIỆN TRƯỜNG (GPS) 1 CHẠM
# -------------------------------------------------------------
st.markdown("---")
st.subheader("2. Định vị Địa điểm (Google Maps)")

# Mã HTML/JavaScript kích hoạt cảm biến GPS của thiết bị di động
gps_component_html = """
<div style="text-align: center; margin-bottom: 12px;">
    <button onclick="layToaDoGPS()" style="
        background-color: #007bff;
        color: white;
        border: none;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    ">📍 BẤM ĐỂ LẤY VỊ TRÍ GPS HIỆN TẠI</button>
    <div id="gps-status" style="margin-top: 8px; font-size: 14px; font-weight: 500; color: #333;"></div>
</div>

<script>
function layToaDoGPS() {
    var status = document.getElementById("gps-status");
    if (!navigator.geolocation) {
        status.innerHTML = "❌ Thiết bị hoặc trình duyệt không hỗ trợ định vị GPS.";
        return;
    }
    status.innerHTML = "⏳ Đang quét tọa độ vệ tinh...";
    navigator.geolocation.getCurrentPosition(
        function(position) {
            var lat = position.coords.latitude;
            var lon = position.coords.longitude;
            var linkMaps = "https://www.google.com/maps?q=" + lat + "," + lon;
            
            // Sao chép trực tiếp vào bộ nhớ tạm
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(linkMaps).then(function() {
                    status.innerHTML = "✅ Đã sao chép link GPS! Dán (Paste) vào ô bên dưới.";
                }).catch(function() {
                    status.innerHTML = "✅ Tọa độ: " + lat + ", " + lon + " (Hãy copy link Maps)";
                });
            } else {
                status.innerHTML = "✅ Tọa độ: " + lat + ", " + lon;
            }
        },
        function(error) {
            if (error.code == error.PERMISSION_DENIED) {
                status.innerHTML = "⚠️ Vui lòng cấp quyền truy cập Vị trí (GPS) trên trình duyệt.";
            } else if (error.code == error.TIMEOUT) {
                status.innerHTML = "⚠️ Quá thời gian quét vị trí GPS.";
            } else {
                status.innerHTML = "⚠️ Không thể định vị được vị trí hiện tại.";
            }
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}
</script>
"""

st.components.v1.html(gps_component_html, height=105)

link_gps = st.text_input(
    "Dán Link GPS vừa lấy (hoặc nhập tọa độ):",
    placeholder="https://www.google.com/maps?q=..."
)

# -------------------------------------------------------------
# 5. GHI NHẬN TIẾN ĐỘ VỀ GOOGLE SHEETS
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
            thoi_gian_hien_tai = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            dong_moi = [
                thoi_gian_hien_tai,
                can_bo_chon,
                diem_chon,
                sl_thuc_te,
                loai_hinh,
                link_gps
            ]
            ws_bc.append_row(dong_moi)
            st.success(f"✅ Ghi nhận thành công: {loai_hinh} tại {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu lên Google Sheets: {e}")

with col1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        ghi_du_lieu_bao_cao("Đã giao hàng")

with col2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        ghi_du_lieu_bao_cao("Đã lắp đặt xong")
