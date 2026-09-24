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
# 2. ĐỌC DANH MỤC ĐA THIẾT BỊ THEO TỪNG ĐIỂM
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
phan_bo_diem = {}  # Cấu trúc: { 'Tên điểm': [{'thiet_bi': '...', 'dinh_muc': 5}, ...] }

if sh:
    try:
        ws_diem = sh.worksheet("DANH_SACH_DIEM")
        records = ws_diem.get_all_records()
        for row in records:
            ten_diem = str(row.get("TEN_DIEM", "")).strip()
            ten_tb = str(row.get("TEN_THIET_BI", "Thiết bị chung")).strip()
            sl_thau = row.get("SO_LUONG_THIET_BI", 1)
            
            try:
                sl_thau = int(sl_thau)
            except:
                sl_thau = 1
                
            if ten_diem:
                if ten_diem not in phan_bo_diem:
                    phan_bo_diem[ten_diem] = []
                phan_bo_diem[ten_diem].append({
                    "thiet_bi": ten_tb,
                    "dinh_muc": sl_thau
                })
    except Exception:
        pass

# Dữ liệu dự phòng mẫu
if not phan_bo_diem:
    phan_bo_diem = {
        "Phường Minh Xuân": [
            {"thiet_bi": "Camera ngoài trời IP 4MP", "dinh_muc": 3},
            {"thiet_bi": "Đầu ghi hình 8 kênh", "dinh_muc": 1},
            {"thiet_bi": "Switch PoE 8 cổng", "dinh_muc": 1}
        ],
        "Phường Phan Thiết": [
            {"thiet_bi": "Camera ngoài trời IP 4MP", "dinh_muc": 4},
            {"thiet_bi": "Switch PoE 8 cổng", "dinh_muc": 1}
        ]
    }

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO HIỆN TRƯỜNG
# -------------------------------------------------------------
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động & ghi nhận hiện trường")

st.markdown("---")
st.subheader("1. Xác nhận thông tin thực hiện")

can_bo_chon = st.selectbox("Cán bộ / Đội trưởng thực hiện:", options=danh_sach_ktv)
diem_chon = st.selectbox("Chọn Điểm lắp đặt:", options=list(phan_bo_diem.keys()))

st.markdown("#### Danh mục thiết bị phân bổ theo thầu:")
danh_sach_tb = phan_bo_diem.get(diem_chon, [])

# Tự động tạo ô nhập số lượng thực tế cho từng thiết bị
ket_qua_nhap = []
for idx, item in enumerate(danh_sach_tb):
    tb_name = item["thiet_bi"]
    tb_dinh_muc = item["dinh_muc"]
    
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown(f"📦 **{tb_name}** *(Định mức: {tb_dinh_muc})*")
    with col_b:
        sl_thuc_te = st.number_input(
            f"SL {tb_name}",
            min_value=0,
            max_value=1000,
            value=int(tb_dinh_muc),
            step=1,
            key=f"tb_{idx}",
            label_visibility="collapsed"
        )
    ket_qua_nhap.append({
        "thiet_bi": tb_name,
        "so_luong": sl_thuc_te
    })

# -------------------------------------------------------------
# 4. TỰ ĐỘNG BẮT TỌA ĐỘ GPS
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
    st.warning("⚠️ Nếu điện thoại hỏi quyền vị trí, hãy chọn 'Cho phép' (Allow).")

link_gps_cuoi = st.text_input(
    "Link Google Maps:",
    value=link_maps_tu_dong,
    placeholder="https://www.google.com/maps?q=..."
)

# -------------------------------------------------------------
# 5. GHI DỮ LIỆU ĐA THIẾT BỊ VÀO SHEETS
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3. Xác nhận hoàn thành công việc")

col1, col2 = st.columns(2)

def xu_ly_ghi_nhan(loai_hinh):
    if not sh:
        st.error("Không có kết nối với Google Sheets.")
        return
    
    with st.spinner("Đang lưu từng thiết bị về hệ thống..."):
        try:
            tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
            thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
            ma_da = "DA-TDV"
            
            # Mở sẵn các worksheet
            ws_bc = None
            ws_ld = None
            ws_vc = None
            try:
                ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
            except:
                pass

            if loai_hinh == "Đã lắp đặt xong":
                ws_ld = sh.worksheet("LAP_DAT")
            elif loai_hinh == "Đã giao hàng":
                try:
                    ws_vc = sh.worksheet("VAN_CHUYEN")
                except:
                    pass

            # Lặp qua từng thiết bị để ghi đúng từng dòng
            for idx_tb, item in enumerate(ket_qua_nhap):
                ten_tb = item["thiet_bi"]
                sl = item["so_luong"]
                if sl <= 0:
                    continue  # Bỏ qua nếu không lắp loại này
                
                ma_cv = f"CV-{datetime.now(tz_vn).strftime('%H%M%S')}-{idx_tb+1}"
                
                # 1. Ghi vào Sheet LAP_DAT
                if ws_ld:
                    # Thứ tự 9 cột: Mã CV, Mã DA, KTV, Tên TB, SL Lắp, Địa điểm, Tình trạng, Giờ hoàn thành, Link Maps
                    dong_ld = [
                        ma_cv,
                        ma_da,
                        can_bo_chon,
                        ten_tb,
                        sl,
                        diem_chon,
                        "Đã hoàn thành",
                        thoi_gian_vn,
                        link_gps_cuoi
                    ]
                    ws_ld.append_row(dong_ld)

                # 2. Ghi vào Sheet VAN_CHUYEN nếu là giao hàng
                if ws_vc:
                    dong_vc = [
                        thoi_gian_vn,
                        can_bo_chon,
                        ten_tb,
                        sl,
                        diem_chon,
                        link_gps_cuoi
                    ]
                    ws_vc.append_row(dong_vc)

                # 3. Ghi vào Sheet nhật ký chung
                if ws_bc:
                    ws_bc.append_row([
                        thoi_gian_vn,
                        can_bo_chon,
                        f"{diem_chon} ({ten_tb})",
                        sl,
                        link_gps_cuoi,
                        loai_hinh
                    ])
            
            st.success(f"✅ Đã ghi nhận toàn bộ thiết bị cho {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu lên Google Sheets: {e}")

with col1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        xu_ly_ghi_nhan("Đã giao hàng")

with col2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        xu_ly_ghi_nhan("Đã lắp đặt xong")
