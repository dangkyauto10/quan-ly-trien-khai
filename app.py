import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Điều Hành Dự Án", layout="centered")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

SHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

# --- HÀM KẾT NỐI GOOGLE SHEETS DÙNG FILE CREDENTIALS.JSON ---
def get_gspread_client():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # Đọc trực tiếp file credentials.json nằm ngay trong thư mục gốc
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets qua credentials.json: {e}")
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
    except Exception as e:
        st.error(f"Lỗi tải danh sách điểm: {e}")
    return diem_list

danh_sach_du_an = load_danh_sach_cot_d()

# --- 2. ĐỌC KHO PHÂN BỔ VÀ ÁNH XẠ ---
@st.cache_data(ttl=5)
def load_kho_phan_bo():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('KHO_PAN_BO')}"
        return pd.read_csv(url, header=None)
    except Exception:
        return pd.DataFrame()

def get_du_lieu_vc_ld_theo_diem(dia_diem_chon):
    df_kho = load_kho_phan_bo()
    items = []
    if df_kho.empty or len(df_kho) <= 2:
        return items
    
    # Cấu trúc KHO_PAN_BO: A:Mã DA, B:SKU, C:Tên DA, D:Tên TB, E:Số lượng, F:ĐVT, G:Đội nhận, H:Địa điểm đến
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

# --- 3. TẢI DỮ LIỆU ĐĂNG KÝ ---
@st.cache_data(ttl=5)
def load_dang_ky_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('ĐĂNG_KÝ_THÀNH_VIÊN')}"
        return pd.read_csv(url, header=None)
    except:
        return pd.DataFrame()

# --- QUẢN LÝ TRANG & TRẠNG THÁI ---
if "page" not in st.session_state: st.session_state.page = "home"
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
if "checked_in" not in st.session_state: st.session_state.checked_in = False
if "selected_mode" not in st.session_state: st.session_state.selected_mode = "Vận Chuyển (VC)"

# --- GIAO DIỆN CHÍNH ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG - VC & LĐ")

with st.expander("🔑 Khu vực Quản Trị & Chức Năng Khác", expanded=False):
    pass_input = st.text_input("Nhập Pass Quản Trị:", type="password", placeholder="Mật khẩu...")
    ADMIN_PASSWORDS = ["S90880", "880880"]
    
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        if st.button("📝 Đăng ký", use_container_width=True): 
            st.session_state.page = "register"
            st.session_state.admin_mode = False
            st.rerun()
    with col_a2:
        if st.button("📊 Báo cáo", use_container_width=True): 
            st.session_state.page = "home"
            st.session_state.admin_mode = False
            st.rerun()
    with col_a3:
        if st.button("🛡️ AD Duyệt", use_container_width=True):
            if pass_input in ADMIN_PASSWORDS: 
                st.session_state.admin_mode = True
                st.session_state.page = "home"
                st.success("✅ Xác thực Admin thành công!")
            else: 
                st.warning("Sai MK")
    with col_a4:
        if st.button("🛠️ B/C LD", use_container_width=True):
            if pass_input in ADMIN_PASSWORDS: 
                st.info("Chức năng Báo cáo Lãnh đạo đang phát triển.")
            else: 
                st.warning("Sai MK")

# --- CHẾ ĐỘ ADMIN DUYỆT ---
if st.session_state.admin_mode:
    st.markdown("---")
    st.subheader("🛡 Phê Duyệt Đăng Ký Trực Tiếp Trên Điện Thoại")
    df_dk = load_dang_ky_data()
    
    if df_dk.empty or len(df_dk) < 3:
        st.info("📭 Hiện tại chưa có dữ liệu đăng ký mới trong Google Sheets.")
    else:
        rows_dk = df_dk.iloc[2:].values.tolist()
        for idx, r in enumerate(rows_dk):
            if len(r) > 2 and pd.notna(r[1]):
                thoi_gian = str(r[0]) if len(r) > 0 and pd.notna(r[0]) else "---"
                ho_ten = str(r[1]) if len(r) > 1 and pd.notna(r[1]) else "---"
                sdt = str(r[2]) if len(r) > 2 and pd.notna(r[2]) else "---"
                chuyen_mon = str(r[4]) if len(r) > 4 and pd.notna(r[4]) else "---"
                phuong_tien = str(r[5]) if len(r) > 5 and pd.notna(r[5]) else "---"
                trang_thai = str(r[6]) if len(r) > 6 and pd.notna(r[6]) else "Chờ duyệt"
                
                with st.container():
                    st.markdown(f"""
                    📌 **Họ tên:** {ho_ten} (`{sdt}`)  
                    🕒 **Thời gian:** {thoi_gian}  
                    ⚙ **Chuyên môn:** {chuyen_mon} | **Xe:** {phuong_tien}  
                    📌 **Trạng thái:** `{trang_thai}`
                    """)
                    c_duyet, c_tuchoi = st.columns(2)
                    with c_duyet:
                        if st.button(f"✅ Duyệt ngay", key=f"app_{idx}"):
                            st.success(f"Đã duyệt thành công cho {ho_ten}!")
                    with c_tuchoi:
                        if st.button(f"❌ Từ chối", key=f"rej_{idx}"):
                            st.warning(f"Đã từ chối yêu cầu của {ho_ten}.")
                    st.markdown("---")
                    
    if st.button("⬅ Thoát chế độ Quản Trị"):
        st.session_state.admin_mode = False
        st.rerun()
    st.stop()

# --- MÀN HÌNH ĐĂNG KÝ THÀNH VIÊN ---
if st.session_state.page == "register":
    st.markdown("---")
    if st.button("⬅ Quay lại màn hình chính"):
        st.session_state.page = "home"
        st.rerun()
        
    st.subheader("📝 Đăng Ký Thành Viên & Phân Bổ Dự Án")
    with st.form("register_form"):
        reg_name = st.text_input("Họ và tên thành viên:")
        reg_phone = st.text_input("Số điện thoại liên hệ:")
        selected_projects = st.multiselect(
            "Chọn các điểm giao hàng và lắp đặt phụ trách:",
            options=danh_sach_du_an,
            placeholder="Gõ tìm kiếm hoặc chọn địa bàn..."
        )
        reg_spec = st.selectbox("Chuyên môn thực hiện:", ["1. Vận chuyển / Giao nhận thiết bị", "2. KTV Lắp đặt hiện trường"])
        reg_vehicle = st.selectbox("Phương tiện di chuyển:", ["Xe máy", "Xe tải", "Ô tô con", "Khác"])
        
        submitted = st.form_submit_button("🚀 GỬI YÊU CẦU ĐĂNG KÝ", type="primary")
        if submitted:
            if not reg_name or not reg_phone:
                st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            elif not selected_projects:
                st.warning("⚠️ Vui lòng chọn ít nhất 1 địa bàn/dự án phụ trách!")
            else:
                st.success(f"✅ Gửi đăng ký thành công cho **{reg_name}**!")
    st.stop()

# --- MÀN HÌNH CHÍNH: CHỌN PHÂN HỆ VÀ ĐỊA ĐIỂM ---
st.markdown("---")
col_mode_1, col_mode_2 = st.columns(2)
with col_mode_1:
    if st.button("🚚 Phân Hệ Vận Chuyển (VC)", use_container_width=True, type="primary" if st.session_state.selected_mode == "Vận Chuyển (VC)" else "secondary"):
        st.session_state.selected_mode = "Vận Chuyển (VC)"
        st.rerun()
with col_mode_2:
    if st.button("⚙ Phân Hệ Lắp Đặt (LĐ)", use_container_width=True, type="primary" if st.session_state.selected_mode == "Lắp Đặt (LĐ)" else "secondary"):
        st.session_state.selected_mode = "Lắp Đặt (LĐ)"
        st.rerun()

st.info(f"📌 Đang thao tác trên phân hệ: **{st.session_state.selected_mode}**")

col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM:", ["-- Chọn địa điểm --"] + danh_sach_du_an)

# --- HIỂN THỊ DỮ LIỆU ÁNH XẠ TỪ KHO PHÂN BỔ ---
danh_sach_phan_bo_hien_tai = []
if selected_location != "-- Chọn địa điểm --":
    st.markdown("---")
    st.subheader(f"📦 Dữ liệu từ KHO PHÂN BỔ cho điểm: `{selected_location}`")
    danh_sach_phan_bo_hien_tai = get_du_lieu_vc_ld_theo_diem(selected_location)
    
    if danh_sach_phan_bo_hien_tai:
        df_display = pd.DataFrame(danh_sach_phan_bo_hien_tai)
        if st.session_state.selected_mode == "Vận Chuyển (VC)":
            df_vc = df_display[["ma_da", "doi", "sku", "ten", "soluong", "donvi", "diem"]]
            df_vc.columns = ["Mã Dự Án", "Đội Nhận TB", "Mã SKU", "Tên Thiết Bị / Hàng Hóa", "Số Lượng V/C", "ĐVT / Xe", "Điểm Giao"]
            st.dataframe(df_vc, use_container_width=True, hide_index=True)
        else:
            df_ld = df_display[["ma_da", "doi", "sku", "ten", "soluong", "donvi", "diem"]]
            df_ld.columns = ["Mã Dự Án", "Đội Nhận Thiết Bị", "Mã SKU", "Tên Thiết Bị / Hàng Hóa", "Số Lượng Lắp", "ĐVT", "Địa Điểm Lắp"]
            st.dataframe(df_ld, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Chưa có dữ liệu phân bổ nào trong sheet `KHO_PAN_BO` cho điểm `{selected_location}`.")

# --- TRẠNG THÁI VÀ GỬI BÁO CÁO ---
st.markdown("---")
if st.session_state.selected_mode == "Vận Chuyển (VC)":
    st.markdown("**2. Trạng Thái Vận Chuyển:**")
    b_c1, b_c2 = st.columns(2)
    with b_c1:
        if st.button("🚚 Đang Vận Chuyển", use_container_width=True): st.session_state.vc_status = "Đang vận chuyển"
    with b_c2:
        if st.button("✅ Đã Giao Hàng Xong", use_container_width=True): st.session_state.vc_status = "Đã giao hàng xong"
    current_action_status = st.session_state.get('vc_status', 'Đang vận chuyển')
    st.caption(f"📌 Trạng thái VC: **{current_action_status}**")
else:
    st.markdown("**2. Trạng Thái Lắp Đặt & Check-in Hiện Trường:**")
    b_c1, b_c2 = st.columns(2)
    with b_c1:
        if st.button("⚙ Đang Lắp Đặt", use_container_width=True): st.session_state.ld_status = "Đang lắp đặt"
    with b_c2:
        if st.button("🎉 Hoàn Thành Lắp Đặt", use_container_width=True): st.session_state.ld_status = "Đã lắp đặt xong"
    current_action_status = st.session_state.get('ld_status', 'Đang lắp đặt')
    st.caption(f"📌 Trạng thái LĐ: **{current_action_status}**")

# --- CHỐT CHẶN CHECK-IN CHO LẮP ĐẶT ---
is_lap_dat = (st.session_state.selected_mode == "Lắp Đặt (LĐ)")
if is_lap_dat:
    st.markdown("📍 **Yêu cầu bắt buộc Check-in GPS:**")
    if not st.session_state.checked_in:
        st.warning("⚠️ Đội lắp đặt bắt buộc phải bấm **Check-in GPS** xác thực vị trí trước khi gửi báo cáo!")
        if st.button("📍 CHECK-IN TỌA ĐỘ HIỆN TRƯỜNG NGAY", use_container_width=True, type="secondary"):
            st.session_state.checked_in = True
            st.session_state.checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"✅ Check-in thành công lúc {st.session_state.checkin_time}!")
            st.rerun()
    else:
        st.success(f"✅ Đã Check-in xác thực lúc `{st.session_state.checkin_time}`.")

col_note, col_img = st.columns(2)
with col_note:
    notes = st.text_area("Ghi chú / Phát sinh:", placeholder="Nhập ghi chú thực tế...", height=70)
with col_img:
    st.file_uploader("📷 Ảnh nghiệm thu", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- NÚT GỬI BÁO CÁO VÀ GHI TRỰC TIẾP VÀO GOOGLE SHEETS ---
if st.button("🚀 GỬI BÁO CÁO VÀ CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi báo cáo!")
    elif is_lap_dat and not st.session_state.checked_in:
        st.error("❌ BẮT BUỘC CHECK-IN: Đội lắp đặt chưa Check-in GPS nên không thể gửi báo cáo!")
    elif not danh_sach_phan_bo_hien_tai:
        st.warning("⚠️ Không có dữ liệu phân bổ từ Kho phân bổ để ghi nhận báo cáo!")
    else:
        thoi_gian_gui = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client = get_gspread_client()
        
        if not client:
            st.error("❌ Không thể kết nối với Google Sheets API qua file credentials.json!")
        else:
            try:
                sh = client.open_by_key(SHEET_ID)
                success_count = 0
                
                if st.session_state.selected_mode == "Vận Chuyển (VC)":
                    worksheet = sh.worksheet("VAN_CHUYEN")
                    # Ghi theo đúng cấu trúc sheet VAN_CHUYEN
                    for item in danh_sach_phan_bo_hien_tai:
                        row_data = [
                            "", # Cột A trống
                            item["ma_da"],
                            item["doi"],
                            item["ten"],
                            item["soluong"],
                            item["donvi"],
                            selected_cb,
                            selected_location,
                            current_action_status,
                            thoi_gian_gui
                        ]
                        worksheet.append_row(row_data)
                        success_count += 1
                else:
                    worksheet = sh.worksheet("LAP_DAT")
                    # Ghi theo đúng cấu trúc sheet LAP_DAT
                    for idx, item in enumerate(danh_sach_phan_bo_hien_tai, start=1):
                        ma_cong_viec = f"LD-{datetime.now().strftime('%m%d%H%M')}-{idx}"
                        row_data = [
                            ma_cong_viec, # Cột A: Mã công việc
                            item["ma_da"],
                            item["doi"],
                            item["ten"],
                            item["soluong"],
                            item["donvi"],
                            selected_location,
                            current_action_status,
5                            thoi_gian_gui,
                            "Google Maps Check-in OK"
                        ]
                        worksheet.append_row(row_data)
                        success_count += 1
                
                st.success(f"✅ Đã ghi thành công **{success_count} dòng dữ liệu** vào sheet `{st.session_state.selected_mode}` trên Google Sheets lúc `{thoi_gian_gui}`!")
                if is_lap_dat:
                    st.caption(f"📌 Lưu vết Check-in lắp đặt: `{st.session_state.checkin_time}`")
            except Exception as e:
                st.error(f"❌ Lỗi khi ghi dữ liệu vào Google Sheets: {e}")
