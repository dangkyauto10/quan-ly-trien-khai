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
# 2. ĐỌC DANH MỤC ĐIỂM & ĐỌC PHÂN BỔ THIẾT BỊ TỪ KHO_PHAN_BO
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_diem = []
phan_bo_kho = {}  # { 'Điểm lắp': [{'thiet_bi': '...', 'so_luong': 2, 'dvt': 'Bộ'}, ...] }

if sh:
    # 2.1 Đọc danh sách điểm từ DANH_SACH_DIEM
    try:
        ws_diem = sh.worksheet("DANH_SACH_DIEM")
        data_diem = ws_diem.get_all_values()
        # Tìm cột "Địa điểm giao hàng và lắp đặt" (thường ở cột D / index 3)
        if len(data_diem) >= 2:
            headers = [h.strip() for h in data_diem[1]]
            col_idx = 3
            for idx, h in enumerate(headers):
                if "Địa điểm" in h:
                    col_idx = idx
                    break
            for row in data_diem[2:]:
                if len(row) > col_idx:
                    val = row[col_idx].strip()
                    if val and val not in danh_sach_diem:
                        danh_sach_diem.append(val)
    except Exception:
        pass

    # 2.2 Đọc danh mục thiết bị từ sheet KHO_PHAN_BO
    try:
        ws_kho = sh.worksheet("KHO_PHAN_BO")
        data_kho = ws_kho.get_all_values()
        if len(data_kho) >= 2:
            # Dòng tiêu đề là dòng 1 hoặc 2
            header_row_idx = 0
            for r_idx in range(min(3, len(data_kho))):
                if any("Tên thiết bị" in str(x) for x in data_kho[r_idx]):
                    header_row_idx = r_idx
                    break
            
            headers_kho = [str(x).strip() for x in data_kho[header_row_idx]]
            
            # Xác định các cột tương ứng theo ảnh KHO_PHAN_BO
            col_tb = 3    # Cột D: Tên thiết bị / Hàng hóa
            col_sl = 4    # Cột E: Số lượng
            col_dvt = 5   # Cột F: Đơn vị tính
            col_diem = 7  # Cột H: Địa điểm vận chuyển lắp đặt

            for i, h in enumerate(headers_kho):
                if "Tên thiết bị" in h: col_tb = i
                elif "Số lượng" in h and "tồn" not in h.lower(): col_sl = i
                elif "Đơn vị" in h: col_dvt = i
                elif "Địa điểm" in h: col_diem = i

            for row in data_kho[header_row_idx + 1:]:
                if len(row) > max(col_tb, col_diem):
                    diem = row[col_diem].strip()
                    tb = row[col_tb].strip()
                    if not diem or not tb:
                        continue
                    
                    sl = 1
                    if len(row) > col_sl:
                        try:
                            sl = int(float(str(row[col_sl]).strip()))
                        except:
                            sl = 1
                    
                    dvt = row[col_dvt].strip() if len(row) > col_dvt else "Thiết bị"
                    
                    if diem not in phan_bo_kho:
                        phan_bo_kho[diem] = []
                    phan_bo_kho[diem].append({
                        "thiet_bi": tb,
                        "so_luong": sl,
                        "dvt": dvt
                    })
    except Exception:
        pass

# Danh sách điểm dự phòng nếu chưa đọc được
if not danh_sach_diem:
    danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm"]

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO TRÊN ĐIỆN THOẠI
# -------------------------------------------------------------
st.title("📱 BÁO CÁO TRIỂN KHAI DỰ ÁN")
st.caption("Hệ thống điều hành phân bổ tự động & ghi nhận hiện trường")

st.markdown("---")
st.subheader("1. Xác nhận thông tin thực hiện")

can_bo_chon = st.selectbox("Cán bộ / Đội trưởng thực hiện:", options=danh_sach_ktv)
diem_chon = st.selectbox("Chọn Địa điểm lắp đặt:", options=danh_sach_diem)

# Lấy danh sách thiết bị phân bổ từ KHO_PHAN_BO cho điểm đã chọn
danh_sach_tb = phan_bo_kho.get(diem_chon, [])

st.markdown("#### 📦 Danh mục thiết bị được phân bổ:")
ket_qua_nhap = []

if danh_sach_tb:
    for idx, item in enumerate(danh_sach_tb):
        tb_name = item["thiet_bi"]
        sl_dm = item["so_luong"]
        dvt = item["dvt"]
        
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"**{tb_name}**  \n*(Phân bổ: {sl_dm} {dvt})*")
        with c2:
            sl_tt = st.number_input(
                f"SL {tb_name}",
                min_value=0,
                max_value=1000,
                value=int(sl_dm),
                step=1,
                key=f"tb_input_{idx}",
                label_visibility="collapsed"
            )
        ket_qua_nhap.append({
            "thiet_bi": tb_name,
            "so_luong": sl_tt,
            "dvt": dvt
        })
else:
    # Nếu ADMIN chưa phân bổ thiết bị cho điểm này ở KHO_PHAN_BO
    st.info("Điểm này chưa có danh mục thiết bị cụ thể trong 'KHO_PHAN_BO'. Mặc định ghi nhận 1 thiết bị:")
    sl_mac_dinh = st.number_input("Số lượng thiết bị thực tế:", min_value=1, max_value=500, value=1, step=1)
    ket_qua_nhap.append({
        "thiet_bi": "Thiết bị tổng hợp",
        "so_luong": sl_mac_dinh,
        "dvt": "Bộ"
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
# 5. GHI DỮ LIỆU TỰ ĐỘNG VÀO CÁC SHEET CHUYÊN TRÁCH
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3. Xác nhận hoàn thành công việc")

col1, col2 = st.columns(2)

def xu_ly_ghi_nhan(loai_hinh):
    if not sh:
        st.error("Không có kết nối với Google Sheets.")
        return
    
    with st.spinner("Đang lưu dữ liệu từng thiết bị về hệ thống..."):
        try:
            tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
            thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
            ma_da = "DA-TDV"
            
            ws_bc = None
            ws_ld = None
            ws_vc = None
            try: ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
            except: pass

            if loai_hinh == "Đã lắp đặt xong":
                ws_ld = sh.worksheet("LAP_DAT")
            elif loai_hinh == "Đã giao hàng":
                try: ws_vc = sh.worksheet("VAN_CHUYEN")
                except: pass

            for idx_tb, item in enumerate(ket_qua_nhap):
                ten_tb = item["thiet_bi"]
                sl = item["so_luong"]
                if sl <= 0:
                    continue
                
                ma_cv = f"CV-{datetime.now(tz_vn).strftime('%H%M%S')}-{idx_tb+1}"
                
                # Ghi vào sheet LAP_DAT
                if ws_ld:
                    ws_ld.append_row([
                        ma_cv,              # Cột A: Mã công việc
                        ma_da,              # Cột B: Mã dự án
                        can_bo_chon,        # Cột C: Đội trưởng KTV
                        ten_tb,             # Cột D: Tên thiết bị
                        sl,                 # Cột E: Số lượng thiết bị lắp
                        diem_chon,          # Cột F: Địa điểm lắp
                        "Đã hoàn thành",    # Cột G: Tình trạng thực hiện
                        thoi_gian_vn,       # Cột H: Thời gian hoàn thành
                        link_gps_cuoi       # Cột I: Link Google Maps
                    ])

                # Ghi vào sheet VAN_CHUYEN nếu là giao hàng
                if ws_vc:
                    ws_vc.append_row([
                        thoi_gian_vn,
                        can_bo_chon,
                        ten_tb,
                        sl,
                        diem_chon,
                        link_gps_cuoi
                    ])

                # Ghi nhật ký chung BAO_CAO_TRIEN_KHAI
                if ws_bc:
                    ws_bc.append_row([
                        thoi_gian_vn,
                        can_bo_chon,
                        f"{diem_chon} ({ten_tb})",
                        sl,
                        link_gps_cuoi,
                        loai_hinh
                    ])
            
            st.success(f"✅ Đã ghi nhận thành công cho {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu lên Google Sheets: {e}")

with col1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        xu_ly_ghi_nhan("Đã giao hàng")

with col2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        xu_ly_ghi_nhan("Đã lắp đặt xong")
