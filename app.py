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
# 2. ĐỌC DỮ LIỆU ĐA DỰ ÁN & TÍNH TOÁN TỒN KHO TỰ ĐỘNG
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_du_an = []
danh_sach_diem = []
kho_phan_bo_map = {}  # {(ma_da, dia_diem): [{'thiet_bi': '...', 'so_luong': 2, 'dvt': 'Chiếc'}]}
nhap_kho_map = {}     # {ma_da: [{'tb': '...', 'tong_nhap': 50, 'dvt': 'Chiếc'}]}

if sh:
    # 2.1 Đọc danh sách dự án
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

    # 2.2 Đọc danh sách điểm
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

    # 2.3 Đọc cấu hình phân bổ KHO_PHAN_BO
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
                    if not m_da or not d_diem or not t_tb:
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

    # 2.4 Đọc và tự động tính tồn kho từ sheet NHAP_KHO
    try:
        ws_nk = sh.worksheet("NHAP_KHO")
        data_nk = ws_nk.get_all_values()
        if len(data_nk) >= 3:
            # Tiêu đề ở dòng 2 (index 1)
            headers_nk = [str(x).strip() for x in data_nk[1]]
            col_da_nk, col_tb_nk, col_nhap_nk = 0, 2, 4
            for i, h in enumerate(headers_nk):
                if "Mã dự án" in h: col_da_nk = i
                elif "Tên thiết bị" in h: col_tb_nk = i
                elif "Tổng nhập" in h: col_nhap_nk = i
            
            for row in data_nk[2:]:
                if len(row) > max(col_da_nk, col_tb_nk, col_nhap_nk):
                    m_da = row[col_da_nk].strip()
                    t_tb = row[col_tb_nk].strip()
                    if not m_da or not t_tb:
                        continue
                    try: sl_nhap = int(float(str(row[col_nhap_nk]).strip()))
                    except: sl_nhap = 0
                    
                    if m_da not in nhap_kho_map:
                        nhap_kho_map[m_da] = []
                    nhap_kho_map[m_da].append({"thiet_bi": t_tb, "tong_nhap": sl_nhap})
    except Exception:
        pass

# Giá trị dự phòng
if not danh_sach_du_an:
    danh_sach_du_an = [{"ma": "DA880", "hien_thi": "DA880 - Viettel Tuyên Quang"}, {"ma": "Dự án 76", "hien_thi": "Dự án 76"}]
if not danh_sach_diem:
    danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường"]

# -------------------------------------------------------------
# 3. GIAO DIỆN BÁO CÁO HIỆN TRƯỜNG ĐA DỰ ÁN
# -------------------------------------------------------------
st.title("📱 HỆ THỐNG ĐIỀU HÀNH DỰ ÁN")
st.caption("Quản trị đa dự án song song & ghi nhận hiện trường thời gian thực")

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

# Lấy danh sách thiết bị theo (Dự án + Điểm)
key_tra_cuu = (ma_da_chon, diem_chon)
danh_sach_tb = kho_phan_bo_map.get(key_tra_cuu, [])

# Nếu chưa có trong KHO_PHAN_BO nhưng đã nhập ở NHAP_KHO của dự án này
if not danh_sach_tb and ma_da_chon in nhap_kho_map:
    danh_sach_tb = [{"thiet_bi": x["thiet_bi"], "so_luong": 1, "dvt": "Chiếc"} for x in nhap_kho_map[ma_da_chon]]

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
                key=f"input_tb_{idx}",
                label_visibility="collapsed"
            )
        ket_qua_nhap.append({"thiet_bi": tb_name, "so_luong": sl_tt, "dvt": dvt})
else:
    st.info(f"Điểm '{diem_chon}' đang dùng gói chuẩn thầu (5 thiết bị):")
    sl_mac_dinh = st.number_input("Số lượng thiết bị thực tế:", min_value=1, max_value=500, value=5, step=1)
    ket_qua_nhap.append({"thiet_bi": "Thiết bị chuẩn theo gói", "so_luong": sl_mac_dinh, "dvt": "Thiết bị"})

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
    st.success(f"📍 Tọa độ vệ tinh: {lat:.5f}, {lon:.5f}")
else:
    st.warning("⚠️ Nếu điện thoại hỏi quyền vị trí, hãy chọn 'Cho phép' (Allow).")

link_gps_cuoi = st.text_input(
    "Link Google Maps:",
    value=link_maps_tu_dong,
    placeholder="https://www.google.com/maps?q=..."
)

# -------------------------------------------------------------
# 5. TỰ ĐỘNG PHÂN LUỒNG VÀ CẬP NHẬT TỒN KHO TỰ ĐỘNG
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3. Xác nhận hoàn thành công việc")

col_b1, col_b2 = st.columns(2)

def xu_ly_ghi_nhan(loai_hinh):
    if not sh:
        st.error("Không có kết nối với Google Sheets.")
        return
    
    with st.spinner("Đang tự động xử lý và phân luồng dữ liệu..."):
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
            
            # Cập nhật tự động cột Tồn kho dự án trên sheet NHAP_KHO
            try:
                ws_nk = sh.worksheet("NHAP_KHO")
                data_nk = ws_nk.get_all_values()
                if len(data_nk) >= 3:
                    # Tính tổng đã giao/lắp của từng thiết bị theo dự án
                    for r_idx in range(2, len(data_nk)):
                        row_vals = data_nk[r_idx]
                        if len(row_vals) >= 5:
                            r_ma_da = row_vals[0].strip()
                            r_tb = row_vals[2].strip()
                            try: tong_nhap = int(float(str(row_vals[4]).strip()))
                            except: tong_nhap = 0
                            
                            # Tính tổng số lượng đã hoàn thành từ LAP_DAT
                            da_lap = 0
                            if ws_ld:
                                ld_data = ws_ld.get_all_values()
                                for ld_row in ld_data[2:]:
                                    if len(ld_row) >= 5 and ld_row[1].strip() == r_ma_da and ld_row[3].strip() == r_tb:
                                        try: da_lap += int(float(str(ld_row[4]).strip()))
                                        except: pass
                            
                            ton_kho = max(0, tong_nhap - da_lap)
                            # Cột F là cột 6 (Tồn kho dự án)
                            ws_nk.update_cell(r_idx + 1, 6, ton_kho)
            except Exception:
                pass

            st.success(f"✅ Ghi nhận thành công cho [{ma_da_chon}] tại {diem_chon}!")
        except Exception as e:
            st.error(f"Lỗi khi gửi dữ liệu lên Google Sheets: {e}")

with col_b1:
    if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary"):
        xu_ly_ghi_nhan("Đã giao hàng")

with col_b2:
    if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True):
        xu_ly_ghi_nhan("Đã lắp đặt xong")
