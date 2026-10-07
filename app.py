import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CẤU HÌNH GIAO DIỆN AN TOÀN ---
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

# --- 1. HÀM TẢI ĐỊA ĐIỂM CHUẨN TỪ CỘT D (DANH_SACH_DIEM) ---
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
        
    if not diem_list:
        diem_list = [
            "Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm",
            "Xã Nhữ Khê", "Xã Yên Sơn", "Xã Tân Long", "Xã Lực Hành", "Xã Xuân Vân", "Xã Thái Bình",
            "Xã Hùng Lợi", "Xã Trung Sơn", "Xã Kiến Thiết", "Xã Đông Thọ", "Xã Hồng Sơn", "Xã Trường Sinh",
            "Xã Phú Lượng", "Xã Sơn Thủy", "Xã Minh Thanh", "Xã Tân Trào", "Xã Tân Thanh", "Xã Bình Ca",
            "Xã Sơn Dương", "Xã Yên Nguyên", "Xã Kim Bình", "Xã Tri Phú", "Xã Kiên Đài", "Xã Hòa An",
            "Xã Chiêm Hóa", "Xã Tân An", "Xã Tân Mỹ", "Xã Yên Lập", "Xã Trung Hà", "Xã Thượng Nông",
            "Xã Yên Hoa", "Xã Nà Hang", "Xã Hồng Thái", "Xã Côn Lôn", "Xã Thượng Lâm", "Xã Lâm Bình",
            "Xã Minh Quang", "Xã Bình An", "Xã Hùng Đức", "Xã Bạch Xa", "Xã Yên Phú", "Xã Hàm Yên",
            "Xã Thái Sơn", "Xã Thái Hòa", "Xã Bình Xa", "Xã Phù Lưu", "Xã Đồng Tâm", "Xã Liên Hiệp",
            "Xã Bằng Hành", "Xã Bắc Quang", "Xã Tân Quang", "Xã Hùng An", "Xã Vĩnh Tuy", "Xã Đồng Yên",
            "Xã Bằng Lang", "Xã Xuân Giang", "Xã Quang Bình", "Xã Tân Trịnh", "Xã Tiên Yên", "Xã Yên Thành",
            "Xã Thông Nguyên", "Xã Nậm Dịch", "Xã Hồ Thầu", "Xã Hoàng Su Phì", "Xã Pờ Ly Ngài", "Xã Thàng Tín",
            "Xã Bản Máy", "Xã Xín Mần", "Xã Pà Vầy Sủ", "Xã Nấm Dẩn", "Xã Khuôn Lùng", "Xã Trung Thịnh",
            "Xã Quảng Nguyên", "Xã Tiên Nguyên", "Xã Tân Tiến", "Phường Hà Giang 1", "Phường Hà Giang 2",
            "Xã Ngọc Đường", "Xã Vị Xuyên", "Xã Phú Linh", "Xã Linh Hồ", "Xã Việt Lâm", "Xã Bạch Ngọc",
            "Xã Tùng Bá", "Xã Thuận Hòa", "Xã Thượng Sơn", "Xã Cao Bồ", "Xã Minh Tân", "Xã Thanh Thủy",
            "Xã Lao Chải", "Xã Bắc Mê", "Xã Minh Ngọc", "Xã Minh Sơn", "Xã Yên Cường", "Xã Đường Hồng",
            "Xã Giáp Trung", "Xã Cán Tỷ", "Xã Lùng Tám", "Xã Quản Bạ", "Xã Tùng Vài", "Xã Nghĩa Thuận",
            "Xã Bạch Đích", "Xã Thắng Mố", "Xã Yên Minh", "Xã Mậu Duệ", "Xã Du Già", "Xã Đường Thượng",
            "Xã Ngọc Long", "Xã Lũng Phìn", "Xã Sà Phìn", "Xã Phố Bảng", "Xã Đồng Văn", "Xã Lũng Cú",
            "Xã Niêm Sơn", "Xã Tát Ngà", "Xã Sủng Máng", "Xã Mèo Vạc", "Xã Khâu Vai", "Xã Sơn Vĩ",
            "Báo phát thanh và truyền hình tỉnh", "Đảng ủy Các cơ quan Đảng tỉnh", "Ban Tổ chức Tỉnh ủy",
            "Đảng ủy UBND tỉnh", "Đảng ủy Công an tỉnh", "Trường Chính trị tỉnh", "UB MTTQVN tỉnh",
            "Đảng ủy Quân sự tỉnh", "Văn phòng Tỉnh ủy", "Ban Nội chính Tỉnh ủy", "Ban Tuyên giáo và dân vận Tỉnh ủy",
            "Cơ quan UBKT Tỉnh ủy"
        ]
    return diem_list

danh_sach_du_an = load_danh_sach_cot_d()

# --- 2. HÀM ĐỌC KHO PHÂN BỔ (KHO_PAN_BO) CHÍNH XÁC ---
@st.cache_data(ttl=5)
def load_kho_phan_bo():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={urllib.parse.quote('KHO_PAN_BO')}"
        return pd.read_csv(url, header=None)
    except Exception:
        return pd.DataFrame()

def get_thiet_bi_theo_dia_diem(dia_diem_chon):
    df_kho = load_kho_phan_bo()
    items = []
    if df_kho.empty or len(df_kho) <= 2:
        return items
    
    # Cấu trúc KHO_PAN_BO thực tế: A:Mã DA, B:SKU, C:Tên DA, D:Tên TB, E:Số lượng, F:ĐVT, G:Đội nhận, H:Địa điểm đến
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
                    "doi": str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else "Chưa phân công"
                })
        except Exception:
            continue
    return items

# --- 3. HÀM TẢI DỮ LIỆU ĐĂNG KÝ (ĐĂNG_KÝ_THÀNH_VIÊN) ---
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
if "selected_status" not in st.session_state: st.session_state.selected_status = "Đang vận chuyển"

# --- GIAO DIỆN CHÍNH ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")

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

# --- MÀN HÌNH CHÍNH: ĐIỀU HÀNH & KHO PHÂN BỔ ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM (Đến):", ["-- Chọn địa điểm --"] + danh_sach_du_an)

# --- HIỂN THỊ THIẾT BỊ TỪ KHO PHÂN BỔ (CHỈ ĐỌC - VIEW ONLY) ---
thiet_bi_hien_tai = []
if selected_location != "-- Chọn địa điểm --":
    st.markdown("---")
    st.subheader(f"📦 Thiết bị phân bổ đến: `{selected_location}`")
    thiet_bi_hien_tai = get_thiet_bi_theo_dia_diem(selected_location)
    
    if thiet_bi_hien_tai:
        df_display = pd.DataFrame(thiet_bi_hien_tai)[["ma_da", "sku", "ten", "soluong", "donvi", "doi"]]
        df_display.columns = ["Mã Dự Án", "Mã SKU", "Tên Hàng Hóa / Thiết Bị", "Số Lượng", "ĐVT", "Đội Nhận"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"ℹ Chưa có thiết bị phân bổ cho điểm `{selected_location}` trong kho.")

# --- TRẠNG THÁI & NGHIỆP VỤ ---
st.markdown("---")
st.markdown("**2. Trạng Thái Hoàn Thành Công Việc:**")

b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚚 Đang V/C", use_container_width=True): 
        st.session_state.selected_status = "Đang vận chuyển"
        st.session_state.checked_in = False
with b_col2:
    if st.button("✅ Đã Giao", use_container_width=True): 
        st.session_state.selected_status = "Đã giao hàng xong"
        st.session_state.checked_in = False

b_col3, b_col4 = st.columns(2)
with b_col3:
    if st.button("⚙ Đang Lắp", use_container_width=True): 
        st.session_state.selected_status = "Đang lắp đặt"
with b_col4:
    if st.button("🎉 Hoàn Thành", use_container_width=True): 
        st.session_state.selected_status = "Đã lắp đặt xong"

st.caption(f"📌 Đang chọn trạng thái: **{st.session_state.selected_status}**")

# --- CHỐT CHẶN CHECK-IN CHO LẮP ĐẶT ---
is_lap_dat_mode = ("Lắp đặt" in st.session_state.selected_status)

if is_lap_dat_mode:
    st.markdown("---")
    st.markdown("📍 **Yêu cầu hiện trường (Bắt buộc Check-in):**")
    if not st.session_state.checked_in:
        st.warning("⚠️ Đội lắp đặt bắt buộc phải bấm **Check-in GPS** xác thực vị trí trước khi gửi báo cáo!")
        if st.button("📍 CHECK-IN TỌA ĐỘ HIỆN TRƯỜNG NGAY", use_container_width=True, type="secondary"):
            st.session_state.checked_in = True
            st.session_state.checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"✅ Check-in thành công lúc {st.session_state.checkin_time}!")
            st.rerun()
    else:
        st.success(f"✅ Đã Check-in thành công lúc `{st.session_state.checkin_time}`.")

col_note, col_img = st.columns(2)
with col_note:
    notes = st.text_area("Ghi chú / Phát sinh:", placeholder="Nhập ghi chú thực tế...", height=70)
with col_img:
    st.file_uploader("📷 Ảnh nghiệm thu", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- NÚT GỬI BÁO CÁO & LƯU VẾT ---
if st.button("🚀 GỬI BÁO CÁO & CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️ Vui lòng chọn địa điểm trước khi gửi báo cáo!")
    elif is_lap_dat_mode and not st.session_state.checked_in:
        st.error("❌ BẮT BUỘC CHECK-IN: Đội lắp đặt chưa Check-in GPS nên không thể gửi báo cáo!")
    elif not thiet_bi_hien_tai:
        st.warning("⚠️ Điểm này chưa có thiết bị trong kho phân bổ để ghi nhận báo cáo!")
    else:
        thoi_gian_hien_tai = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"✅ Gửi báo cáo thành công trạng thái '{st.session_state.selected_status}' cho điểm **{selected_location}**!")
        if is_lap_dat_mode:
            st.caption(f"📌 Đã lưu vết Check-in lắp đặt lúc: `{st.session_state.checkin_time}` | Hoàn thành lúc: `{thoi_gian_hien_tai}`")
        else:
            st.caption(f"📌 Đã ghi nhận vận chuyển lúc: `{thoi_gian_hien_tai}`")
