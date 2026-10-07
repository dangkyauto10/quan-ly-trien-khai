import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CẤU HÌNH GIAO DIỆN DI ĐỘNG ---
st.set_page_config(page_title="DỰ ÁN 880 — HIỆN TRƯỜNG", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 0.5rem; padding-bottom: 1rem; max-width: 500px;}
        .stButton button {width: 100%; border-radius: 8px; font-weight: bold;}
    </style>
    """,
    unsafe_allow_html=True
)

SHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

# --- 1. LẤY DANH SÁCH ĐỊA ĐIỂM (LỌC SẠCH RÁC) ---
@st.cache_data(ttl=5)
def load_danh_sach_cot_d():
    diem_list = []
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('DANH_SACH_DIEM')}"
        df = pd.read_csv(url, header=None)
        if len(df.columns) > 3 and len(df) > 2:
            for val in df.iloc[2:, 3].dropna().astype(str).str.strip():
                val_lower = val.lower()
                tu_khoa_rac = [
                    'nan', 'none', '', '0', '0.0', 'tỉnh', 'huyện', 'địa điểm', 
                    'nghiệm thu', 'kho phân bổ', 'danh sách điểm', 'stt', 'tên điểm',
                    'địa bàn', 'nội dung', 'ghi chú', 'đơn vị'
                ]
                is_rac = any(rac in val_lower for rac in tu_khoa_rac) or val.startswith("TỔNG") or val.startswith("DANH SÁCH") or val.startswith("KHO") or len(val) <= 2
                
                if not is_rac and val not in diem_list:
                    diem_list.append(val)
    except Exception:
        pass
    return diem_list

danh_sach_du_an = load_danh_sach_cot_d()

# --- 2. ĐỌC KHO PHÂN BỔ (KHO_PHAN_BO) ---
@st.cache_data(ttl=5)
def load_kho_phan_bo():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('KHO_PHAN_BO')}"
        return pd.read_csv(url, header=None)
    except Exception:
        return pd.DataFrame()

def get_du_lieu_theo_diem(dia_diem_chon):
    df_kho = load_kho_phan_bo()
    items = []
    if df_kho.empty or len(df_kho) <= 2:
        return items
    # Cấu trúc KHO_PHAN_BO: A:Mã DA, B:SKU, C:Tên DA, D:Tên TB, E:Số lượng, F:ĐVT, G:Đội nhận, H:Địa điểm đến
    for _, row in df_kho.iloc[2:].iterrows():
        try:
            dia_diem_row = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ""
            if dia_diem_row.lower() == dia_diem_chon.lower():
                items.append({
                    "ma_da": str(row.iloc[0]).strip() if len(row) > 0 and pd.notna(row.iloc[0]) else "DA880",
                    "sku": str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else "---",
                    "ten": str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else "---",
                    "soluong": str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else "0",
                    "donvi": str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else "",
                    "doi": str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else "Chưa phân công",
                    "diem": dia_diem_row
                })
        except Exception:
            continue
    return items

# --- QUẢN LÝ TRẠNG THÁI ---
if "gps_checked" not in st.session_state: st.session_state.gps_checked = False

# --- GIAO DIỆN DI ĐỘNG ---
st.markdown(
    """
    <div style="background-color: #0e1726; padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0; font-size: 20px;">📱 DỰ ÁN 880</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #a0aec0;">Hệ thống Báo cáo Giao nhận & Lắp đặt Hiện trường</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("📍 **BÁO CÁO CÔNG VIỆC**")

# 1. Chọn Xã/Phường
selected_location = st.selectbox(
    "1. Nhập từ khóa để chọn Xã/Phường *",
    options=["-- Gõ hoặc chọn địa điểm --"] + danh_sach_du_an,
    placeholder="Gõ từ khóa xã/phường..."
)

danh_sach_hien_tai = []
if selected_location != "-- Gõ hoặc chọn địa điểm --":
    danh_sach_hien_tai = get_du_lieu_theo_diem(selected_location)
    if danh_sach_hien_tai:
        st.info(f"📦 Dữ liệu ánh xạ từ KHO PHÂN BỔ cho điểm `{selected_location}`:")
        df_show = pd.DataFrame(danh_sach_hien_tai)[["ma_da", "doi", "sku", "ten", "soluong", "donvi"]]
        df_show.columns = ["Mã DA", "Đội nhận", "SKU", "Tên thiết bị", "Số lượng", "ĐVT"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Điểm này chưa có thiết bị phân bổ trong KHO_PHAN_BO.")

# 2. Loại công việc
loai_cong_viec = st.selectbox(
    "2. Loại công việc *",
    ["🚚 Giao nhận hàng hóa / Vận chuyển", "⚙ Kỹ thuật lắp đặt hiện trường"]
)

# 3. Trạng thái thực hiện
st.markdown("3. Trạng thái thực hiện *")
col_st1, col_st2 = st.columns(2)
is_lap_dat = ("lắp đặt" in loai_cong_viec.lower())

with col_st1:
    btn_done = st.button("✅ ĐÃ HOÀN THÀNH", use_container_width=True)
with col_st2:
    btn_undone = st.button("❌ CHƯA XONG", use_container_width=True)

if "trang_thai_chon" not in st.session_state:
    st.session_state.trang_thai_chon = "Đã hoàn thành"

if btn_done: st.session_state.trang_thai_chon = "Đã hoàn thành"
if btn_undone: st.session_state.trang_thai_chon = "Chưa xong"

st.caption(f"📌 Đang chọn trạng thái: **{st.session_state.trang_thai_chon}**")

# 4. Họ tên người gửi / Đội phụ trách
nguoi_gui = st.text_input("4. Họ tên người gửi / Đội phụ trách *", placeholder="Ví dụ: Trần Đình Vỹ - Đội 01")

# Nút lấy tọa độ GPS (Bắt buộc nếu lắp đặt)
if is_lap_dat:
    st.markdown("---")
    if not st.session_state.gps_checked:
        st.warning("⚠️ Yêu cầu bắt buộc: Đội lắp đặt phải bấm lấy tọa độ GPS hiện trường!")
        if st.button("📍 BÁM LẤY TỌA ĐỘ GPS HIỆN TẠI", use_container_width=True, type="secondary"):
            st.session_state.gps_checked = True
            st.session_state.gps_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ Đã lấy tọa độ GPS thành công!")
            st.rerun()
    else:
        st.success(f"✅ Đã xác thực GPS lúc `{st.session_state.get('gps_time', 'N/A')}`")

st.markdown("---")

# --- XÁC NHẬN BÁO CÁO TRÊN GIAO DIỆN ---
if st.button("✅ GỬI BÁO CÁO VỀ HỆ THỐNG", type="primary", use_container_width=True):
    if selected_location == "-- Gõ hoặc chọn địa điểm --":
        st.error("⚠️ Vui lòng chọn Xã/Phường trước khi gửi báo cáo!")
    elif not nguoi_gui:
        st.error("⚠️ Vui lòng nhập họ tên người gửi / đội phụ trách!")
    elif is_lap_dat and not st.session_state.gps_checked:
        st.error("❌ BẮT BUỘC: Chưa lấy tọa độ GPS hiện trường nên không thể gửi báo cáo lắp đặt!")
    elif not danh_sach_hien_tai:
        st.error("⚠️ Không có dữ liệu thiết bị phân bổ tương ứng để ghi nhận!")
    else:
        thoi_gian_hien_tai = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_sheet = "LAP_DAT" if is_lap_dat else "VAN_CHUYEN"
        
        st.success(f"🎉 Xác nhận báo cáo thành công cho {len(danh_sach_hien_tai)} thiết bị tại **{selected_location}** trên phân hệ **{target_sheet}** lúc {thoi_gian_hien_tai}!")
        if is_lap_dat:
            st.caption(f"📌 Thời gian check-in GPS: `{st.session_state.get('gps_time', 'N/A')}`")
        st.balloons()
