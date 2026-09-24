import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="Hệ Thống Điều Hành Dự Án",
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
# 2. ĐỌC DỮ LIỆU ĐA DỰ ÁN & PHÂN BỔ THIẾT BỊ
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_du_an = []
danh_sach_diem = []
kho_phan_bo_map = {}

if sh:
    # Đọc danh sách Dự án từ sheet DANH_SACH_DU_AN
    try:
        ws_da = sh.worksheet("DANH_SACH_DU_AN")
        records_da = ws_da.get_all_records()
        for r in records_da:
            ma = str(r.get("Mã dự án", "")).strip()
            ten = str(r.get("Tên dự án", "")).strip()
            if ma and ma != "nan":
                nhan = f"{ma} - {ten}" if ten and ten != "nan" else ma
                danh_sach_du_an.append({"ma": ma, "hien_thi": nhan})
    except Exception:
        pass

    # Đọc danh sách Địa điểm từ sheet DANH_SACH_DIEM
    try:
        ws_diem = sh.worksheet("DANH_SACH_DIEM")
        data_diem = ws_diem.get_all_values()
        if len(data_diem) >= 2:
            headers = [h.strip() for h in data_diem[1]]
            col_diem_idx = 3
            for idx, h in enumerate(headers):
                if "Địa điểm" in h:
                    col_diem_idx = idx
                    break
            for row in data_diem[2:]:
                if len(row) > col_diem_idx:
                    val = row[col_diem_idx].strip()
                    if val and val not in danh_sach_diem:
                        danh_sach_diem.append(val)
    except Exception:
        pass

    # Đọc thiết bị phân bổ từ KHO_PHAN_BO
    try:
        ws_kho = sh.worksheet("KHO_PHAN_BO")
        data_kho = ws_kho.get_all_values()
        if len(data_kho) >= 2:
            headers_k = [str(x).strip() for x in data_kho[0]]
            col_da, col_tb, col_sl, col_dvt, col_diem = 0, 3, 4, 5, 7
            for i, h in enumerate(headers_k):
                if "Mã dự án" in h: col_da = i
                elif "Tên thiết bị" in h: col_tb = i
                elif "Số lượng" in h and "tồn" not in h.lower(): col_sl = i
                elif "Đơn vị" in h: col_dvt = i
                elif "Địa điểm" in h: col_diem = i

            for row in data_kho[1:]:
                if len(row) > max(col_da, col_tb, col_diem):
                    m_da = row[col_da].strip()
                    d_diem = row[col_diem].strip()
                    t_tb = row[col_tb].strip()
                    if not m_da or not d_diem or not t_tb or "#" in t_tb:
                        continue
                    sl = 1
                    if len(row) > col_sl:
                        try: sl = int(float(str(row[col_sl]).strip()))
                        except: sl = 1
                    dvt = row[col_dvt].strip() if len(row) > col_dvt else "Chiếc"
                    
                    key = (m_da, d_diem)
                    if key not in kho_phan_bo_map:
                        kho_phan_bo_map[key] = []
                    kho_phan_bo_map[key].append({"thiet_bi": t_tb, "so_luong": sl, "dvt": dvt})
    except Exception:
        pass

if not danh_sach_du_an:
    danh_sach_du_an = [{"ma": "DA880", "hien_thi": "DA880 - Viettel Tuyên Quang"}, {"ma": "Dự án 76", "hien_thi": "Dự án 76"}]
if not danh_sach_diem:
    danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường"]

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO HIỆN TRƯỜNG ĐA DỰ ÁN
# -------------------------------------------------------------
st.title("📱 HỆ THỐNG ĐIỀU HÀNH DỰ ÁN")
st.caption("Quản trị đa dự án song song & cập nhật hiện trường tự động")

st.markdown("---")
st.subheader("1. Thông tin Dự án & Hiện trường")

lua_chon_da = st.selectbox(
    "Đang thực hiện cho Dự án:",
    options=[item["hien_thi"] for item in danh_sach_du_an]
)
ma_da_chon = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == lua_chon_da)

col_kb1, col_kb2 = st.columns(2)
with col_kb1:
    can_bo_chon = st.selectbox("Cán bộ / Đội trưởng:", options=danh_sach_ktv)
with col_kb2:
    diem_chon = st.selectbox("Địa điểm lắp đặt:", options=danh_sach_diem)

# Lấy danh mục thiết bị từ KHO_PHAN_BO theo Dự án và Địa điểm
key_tra_cuu = (ma_da_chon, diem_chon)
danh_sach_tb = kho_phan_bo_map.get(key_tra_cuu, [])

st.markdown("#### 📦 Danh mục thiết bị thực hiện:")
ket_qua_nhap = []

if danh_sach_tb:
    for idx, item in enumerate(danh_sach_tb):
        tb_name = item["thiet_bi"]
        sl_dm = item["so_luong"]
        dvt = item.get("dvt", "Chiếc")
        
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
                key=f"in_tb_{idx}",
                label_visibility="collapsed"
            )
        ket_qua_nhap.append({"thiet_bi": tb_name, "so_luong": sl_tt, "dvt": dvt})
else:
    st.info(f"Điểm '{diem_chon}' chưa cấu hình chi tiết ở KHO_PHAN_BO. Mặc định nhận 5 thiết bị chuẩn:")
    sl_mac_dinh = st.number_input("Số lượng thiết bị thực tế:", min_value=1, max_value=500, value=5, step=1)
    ket_qua_nhap.append({"thiet_bi": "Thiết bị chuẩn theo gói", "so_luong": sl_mac_dinh, "dvt": "Thiết bị"})

# -------------------------------------------------------------
# 4. GPS VỆ TINH
# -------------------------------------------------------------
st.markdown("---")
st.subheader("2. Định vị Hiện trường (GPS)")

location = get_geolocation()
link_maps_tu_dong = ""
if location and "coords" in location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    link_maps_tu_dong = f"https://www.google.com/maps?q={lat},{lon}"
    st.success(f"📍 Tọa độ vệ tinh: {lat:.5f}, {lon:.5f}")
else:
    st.warning("⚠️ Nếu thiết bị hỏi quyền vị trí, hãy chọn 'Cho phép' (Allow).")

link_gps_cuoi = st.text_input(
    "Link Google Maps:",
    value=link_maps_tu_dong,
    placeholder="https://www.google.com/maps?q=..."
)

# -------------------------------------------------------------
# 5. PHÂN LUỒNG DỮ LIỆU TỰ ĐỘNG
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3. Xác nhận hoàn thành công việc")

col_b1, col_b2 = st.columns(2)

def xu_ly_ghi_nhan(loai_hinh):
    if not sh:
        st.error("Không có kết nối với Google Sheets.")
        return
    
    with st.spinner("Đang tự động phân luồng dữ liệu..."):
        try:
            tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
            thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
            
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
                
                # Ghi vào LAP_DAT
                if ws_ld:
                    ws_ld.append_row([
                        ma_cv,
                        ma_da_chon,
                        can_bo_chon,
                        ten_tb,
                        sl,
                        diem_chon,
                        "Đã hoàn thành",
                        thoi_gian_vn,
                        link_gps_cuoi
                    ])

                # Ghi vào VAN_CHUYEN
                if ws_vc:
                    ws_vc.append_row([
                        thoi_gian_vn,
                        ma_da_chon,
                        can_bo_chon,
                        ten_tb,
                        sl,
                        diem_chon,
                        link_gps_cuoi
                    ])

                # Ghi nhật ký BAO_CAO_TRIEN_KHAI
                if ws_bc:
                    ws_bc.append_row([
                        thoi_gian_vn,
                        f"[{ma_da_chon}] {can_bo_chon}",
                        f"{diem_chon} ({ten_tb})",
                        sl,
                        link_gps_cuoi,
                        loai_hinh
                    ])

            st.success(f"✅ Ghi nhận thành công cho [{ma_da_chon}] tại {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu: {e}")

with col_b1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        xu_ly_ghi_nhan("Đã giao hàng")

with col_b2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        xu_ly_ghi_nhan("Đã lắp đặt xong")
