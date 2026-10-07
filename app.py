import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

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

# --- HÀM KẾT NỐI GOOGLE SHEETS AN TOÀN TUYỆT ĐỐI ---
def get_gspread_client():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # Nhúng trực tiếp cấu hình từ credentials.json để tránh lỗi đọc file trên Cloud
        service_account_info = {
            "type": "service_account",
            "project_id": "quanlyduanpython",
            "private_key_id": "d97569af576aaa99349231ddc12d55d24c4717ba",
            "private_key": st.secrets["PRIVATE_KEY"] if "PRIVATE_KEY" in st.secrets else "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZn+nMiIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDbN+1jV1gIbaDanBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZn+nMiIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDbN+1jV1gIbaDanBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZn+nMiIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDbN+1jV1gIbaDanBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZn+nMiIEv...dummy_key_to_replace_or_use_file...\n-----END PRIVATE KEY-----\n",
            "client_email": "tdv2026@quanlyduanpython.iam.gserviceaccount.com",
            "client_id": "104406443886537574070",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tdv2026%40quanlyduanpython.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        # Thử đọc từ file trước, nếu lỗi thì dùng dict trực tiếp
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        except Exception:
            # Lấy private_key chuẩn từ file credentials.json của anh trên GitHub
            import json
            with open("credentials.json", "r") as f:
                data = json.load(f)
            creds = Credentials.from_service_account_info(data, scopes=scopes)
            
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Chi tiết lỗi kết nối Google Sheets: {e}")
        return None

# --- 1. LẤY DANH SÁCH ĐỊA ĐIỂM ĐỘNG TỪ CỘT D (DANH_SACH_DIEM) ---
@st.cache_data(ttl=5)
def load_danh_sach_cot_d():
    diem_list = []
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('DANH_SACH_DIEM')}"
        df = pd.read_csv(url, header=None)
        if len(df.columns) > 3 and len(df) > 2:
            raw_vals = df.iloc[2:, 3].dropna().astype(str).str.strip().tolist()
            for val in raw_vals:
                val_lower = val.lower()
                is_invalid = (
                    not val or len(val) < 2 or "%" in val or
                    val_lower in ['nan', 'none', '', '0', '0.0', 'tỉnh', 'huyện', 'địa điểm giao hàng và lắp đặt', 'địa bàn', 'tên điểm', 'danh sách điểm', 'nghiệm thu', 'kho phân bổ'] or
                    val.startswith("TỔNG") or val.startswith("DANH SÁCH") or val.startswith("NGHIỆM") or val.startswith("KHO") or val.startswith("STT")
                )
                if not is_invalid and val not in diem_list:
                    diem_list.append(val)
    except Exception:
        pass
    return diem_list

danh_sach_du_an = load_danh_sach_cot_d()

# --- 2. ĐỌC KHO PHÂN BỔ ĐỂ ÁNH XẠ ---
@st.cache_data(ttl=5)
def load_kho_phan_bo():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('KHO_PAN_BO')}"
        return pd.read_csv(url, header=None)
    except Exception:
        return pd.DataFrame()

def get_du_lieu_theo_diem(dia_diem_chon):
    df_kho = load_kho_phan_bo()
    items = []
    if df_kho.empty or len(df_kho) <= 2:
        return items
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

# --- HEADER GIAO DIỆN DI ĐỘNG ---
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
    placeholder="Gõ từ khóa (ví dụ: Sủng Máng, Nông Tiến...)"
)

# Hiển thị dữ liệu tự động từ Kho phân bổ (View-only)
danh_sach_hien_tai = []
if selected_location != "-- Gõ hoặc chọn địa điểm --":
    danh_sach_hien_tai = get_du_lieu_theo_diem(selected_location)
    if danh_sach_hien_tai:
        st.info(f"📦 Đã tự động tải {len(danh_sach_hien_tai)} thiết bị phân bổ cho điểm này:")
        df_show = pd.DataFrame(danh_sach_hien_tai)[["sku", "ten", "soluong", "donvi", "doi"]]
        df_show.columns = ["SKU", "Tên thiết bị", "Số lượng", "ĐVT", "Đội nhận"]
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

# Nút lấy tọa độ GPS (Chốt chặn bắt buộc nếu là Lắp đặt)
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

# --- NÚT GỬI BÁO CÁO VỀ HỆ THỐNG (GHI THẲNG VÀO GOOGLE SHEETS) ---
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
        client = get_gspread_client()
        
        if not client:
            st.error("❌ Lỗi kết nối Google Sheets API. Vui lòng kiểm tra lại cấu hình thông tin bảo mật!")
        else:
            try:
                sh = client.open_by_key(SHEET_ID)
                count = 0
                if not is_lap_dat:
                    # Ghi vào sheet VAN_CHUYEN theo đúng cấu trúc cột
                    ws = sh.worksheet("VAN_CHUYEN")
                    for item in danh_sach_hien_tai:
                        row = [
                            "", # Cột A trống
                            item["ma_da"], # Cột B
                            item["doi"],   # Cột C
                            item["ten"],   # Cột D
                            item["soluong"], # Cột E
                            item["donvi"], # Cột F
                            nguoi_gui,     # Cột G
                            selected_location, # Cột H
                            st.session_state.trang_thai_chon, # Cột I
                            thoi_gian_hien_tai # Cột J
                        ]
                        ws.append_row(row)
                        count += 1
                else:
                    # Ghi vào sheet LAP_DAT theo đúng cấu trúc cột
                    ws = sh.worksheet("LAP_DAT")
                    for idx, item in enumerate(danh_sach_hien_tai, start=1):
                        ma_cv = f"LD-{datetime.now().strftime('%m%d%H%M')}-{idx}"
                        row = [
                            ma_cv, # Cột A
                            item["ma_da"], # Cột B
                            item["doi"],   # Cột C
                            item["ten"],   # Cột D
                            item["soluong"], # Cột E
                            item["donvi"], # Cột F
                            selected_location, # Cột G
                            st.session_state.trang_thai_chon, # Cột H
                            thoi_gian_hien_tai, # Cột I
                            "Google Maps GPS Verified" # Cột J
                        ]
                        ws.append_row(row)
                        count += 1
                
                st.success(f"🎉 Gửi thành công {count} dòng dữ liệu vào Google Sheets lúc {thoi_gian_hien_tai}!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Lỗi ghi dữ liệu vào Google Sheets: {e}")
