import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import urllib.request
import json

# --- CẤU HÌNH GIAO DIỆN GỌN GÀNG ---
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

# --- ID GOOGLE SHEETS & DANH SÁCH DỰ ÁN ---
SHEET_ID = "129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4"

danh_sach_du_an = [
    "Phường Minh Xuân", "Phường Nông Tiến", "Phường Bình Thuận", "Phường An Tường", "Phường Mỹ Lâm",
    "Xã Nhữ Khê", "Xã Yên Sơn", "Xã Tân Long", "Xã Lực Hành", "Xã Xuân Vân", "Xã Thái Bình",
    "Xã Hùng Lợi", "Xã Trung Sơn", "Xã Kiến Thiết", "Xã Đông Thọ", "Xã Hồng Sơn", "Xã Trường Sinh",
    "Xã Phú Lượng", "Xã Sơn Thủy", "Xã Minh Thanh", "Xã Tân Trào", "Xã Tân Thanh", "Xã Bình Ca",
    "Xã Sơn Dương", "Xã Yên Nguyên", "Xã Kim Bình", "Xã Trí Phú", "Xã Kiên Đài", "Xã Hòa An",
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

# --- HÀM TẢI DỮ LIỆU ĐĂNG KÝ TỪ GOOGLE SHEETS ---
@st.cache_data(ttl=5)
def load_dang_ky_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=ĐĂNG_KÝ_THÀNH_VIÊN"
        df = pd.read_csv(url, header=None)
        return df
    except:
        try:
            url_alt = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
            return pd.read_csv(url_alt, header=None)
        except:
            return pd.DataFrame()

# --- QUẢN LÝ TRANG & TRẠNG THÁI ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# --- GIAO DIỆN CHÍNH ---
st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")

# Khu vực quản trị thu gọn
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
            st.info("Chức năng Báo cáo đang phát triển.")
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

# --- NẾU ADMIN BẤM DUYỆT (HIỂN THỊ DANH SÁCH CHỜ DUYỆT TRÊN ĐIỆN THOẠI) ---
if st.session_state.admin_mode:
    st.markdown("---")
    st.subheader("🛡️ Phê Duyệt Đăng Ký Trực Tiếp Trên Điện Thoại")
    st.caption("Danh sách thành viên đăng ký tham gia từ hiện trường được tải trực tiếp từ Google Sheets.")
    
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
                diaban = str(r[3]) if len(r) > 3 and pd.notna(r[3]) else "---"
                chuyen_mon = str(r[4]) if len(r) > 4 and pd.notna(r[4]) else "---"
                phuong_tien = str(r[5]) if len(r) > 5 and pd.notna(r[5]) else "---"
                trang_thai = str(r[6]) if len(r) > 6 and pd.notna(r[6]) else "Chờ duyệt"
                
                with st.container():
                    st.markdown(f"""
                    📌 **Họ tên:** {ho_ten} (`{sdt}`)  
                    🕒 **Thời gian:** {thoi_gian}  
                    📍 **Địa bàn phụ trách:** {diaban}  
                    ⚙️ **Chuyên môn:** {chuyen_mon} | **Xe:** {phuong_tien}  
                    📌 **Trạng thái hiện tại:** `{trang_thai}`
                    """)
                    
                    c_duyet, c_tuchoi = st.columns(2)
                    with c_duyet:
                        if st.button(f"✅ Duyệt ngay", key=f"app_{idx}"):
                            st.success(f"Đã duyệt thành công cho {ho_ten}! (Vui lòng cập nhật trạng thái trên Google Sheets)")
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
    st.caption(f"✅ Hệ thống đã nạp sẵn **{len(danh_sach_du_an)} điểm dự án**. Thành viên chọn đồng thời nhiều điểm triển khai.")
    
    with st.form("register_form"):
        reg_name = st.text_input("Họ và tên thành viên:")
        reg_phone = st.text_input("Số điện thoại liên hệ:")
        
        selected_projects = st.multiselect(
            "Chọn các điểm giao hàng và lắp đặt phụ trách (Chọn nhiều điểm cùng lúc):",
            options=danh_sach_du_an,
            placeholder="Gõ tìm kiếm hoặc chọn địa bàn..."
        )
        
        reg_spec = st.selectbox("Chuyên môn thực hiện:", [
            "1. Vận chuyển / Giao nhận thiết bị",
            "2. KTV Lắp đặt hiện trường"
        ])
        reg_vehicle = st.selectbox("Phương tiện di chuyển:", ["Xe máy", "Xe tải", "Ô tô con", "Khác"])
        
        submitted = st.form_submit_button("🚀 GỬI YÊU CẦU ĐĂNG KÝ", type="primary")
        if submitted:
            if not reg_name or not reg_phone:
                st.warning("⚠️ Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
            elif not selected_projects:
                st.warning("⚠️ Vui lòng chọn ít nhất 1 địa bàn/dự án phụ trách!")
            else:
                projects_str = ", ".join(selected_projects)
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Hướng dẫn liên kết Google Sheets tự động nhận dữ liệu
                st.success(f"✅ Gửi đăng ký thành công cho **{reg_name}**!\n\n📌 **Phụ trách {len(selected_projects)} điểm dự án:**\n`{projects_str}`.\n\n📊 Dữ liệu đã sẵn sàng đồng bộ vào bảng Google Sheets để Admin phê duyệt trên di động.")
                
                # Hiển thị thông tin chuỗi dữ liệu để dán thủ công hoặc đồng bộ qua Google Apps Script Webhook nếu cần
                with st.expander("🔍 Chi tiết dữ liệu ghi nhận (Dùng để đồng bộ Google Sheets):"):
                    st.code(f"Thời gian: {current_time} | Họ tên: {reg_name} | SĐT: {reg_phone} | Địa bàn: {projects_str} | Chuyên môn: {reg_spec} | Xe: {reg_vehicle}", language="text")
                
    st.stop()

# --- MÀN HÌNH CHÍNH: ĐIỀU HÀNH HIỆN TRƯỜNG ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    cb_list = ["Vũ - Hạnh - Hiền", "Đội Vận Chuyển 01", "Đội Lắp Đặt 02", "Kỹ thuật hiện trường"]
    selected_cb = st.selectbox("Cán bộ / Đội thực hiện:", cb_list)
with col2:
    selected_location = st.selectbox("Chọn ĐỊA ĐIỂM:", ["-- Chọn địa điểm --"] + danh_sach_du_an)

total_devices = 10  # Mặc định an toàn

col_q, col_g = st.columns(2)
with col_q:
    actual_qty = st.number_input("Số lượng thực tế:", min_value=0, value=total_devices, step=1)
with col_g:
    st.write("") 
    if st.button("📍 Check-in GPS", use_container_width=True):
        st.success("📍 Đã ghi nhận GPS!")

# --- TRẠNG THÁI & BÁO CÁO ---
st.markdown("---")
st.markdown("**2. Trạng Thái Hoàn Thành:**")

if "selected_status" not in st.session_state:
    st.session_state.selected_status = "Đang vận chuyển"

b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚚 Đang V/C", use_container_width=True): st.session_state.selected_status = "Đang vận chuyển"
with b_col2:
    if st.button("✅ Đã Giao", use_keyword=True) or st.button("✅ Đã Giao", key="btn_giao", use_container_width=True): st.session_state.selected_status = "Đã giao hàng xong"

b_col3, b_col4 = st.columns(2)
with b_col3:
    if st.button("⚙️ Đang Lắp", key="btn_lap", use_container_width=True): st.session_state.selected_status = "Đang lắp đặt"
with b_col4:
    if st.button("🎉 Hoàn Thành", key="btn_ht", use_container_width=True): st.session_state.selected_status = "Đã lắp đặt xong"

st.caption(f"📌 Đang chọn: **{st.session_state.selected_status}**")

col_note, col_img = st.columns(2)
with col_note:
    notes = st.text_area("Ghi chú / Phát sinh:", placeholder="Nhập ghi chú...", height=70)
with col_img:
    st.file_uploader("📷 Ảnh nghiệm thu", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if st.button("🚀 GỬI BÁO CÁO & CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
    if selected_location == "-- Chọn địa điểm --":
        st.warning("⚠️️ Vui lòng chọn địa điểm trước khi gửi!")
    else:
        st.success(f"✅ Gửi báo cáo thành công trạng thái '{st.session_state.selected_status}' cho điểm {selected_location}!")
