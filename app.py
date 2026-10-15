import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
from streamlit_geolocation import streamlit_geolocation
from PIL import Image
import io

st.set_page_config(page_title="QUẢN LÝ DỰ ÁN", page_icon="🚀", layout="centered")

# ==========================================
# CSS GIAO DIỆN CHUẨN
# ==========================================
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 600px; }
    .stButton>button {
        border-radius: 12px; font-weight: 700 !important; font-size: 15px !important;
        height: 50px !important; color: white !important;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.2s ease-in-out;
    }
    .stButton>button:active { transform: scale(0.97); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    }
    div[data-baseweb="select"] > div, input {
        border-radius: 10px !important; border: 1px solid #CBD5E1 !important; padding: 2px !important;
    }
    h5 { color: #1E293B; font-weight: 700; margin-top: 20px; margin-bottom: 15px; font-size: 16px; }
    .pending-card {
        border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px;
        margin-bottom: 15px; background-color: #F8FAFC; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .map-btn {
        display: block; width: 100%; background-color: #10B981; color: white; text-align: center;
        padding: 12px 0; border-radius: 10px; font-weight: bold; text-decoration: none;
        margin-top: 5px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 15px;
    }
    .map-btn:active { background-color: #059669; }
    </style>
""", unsafe_allow_html=True)

SECURE_PASS = "880880"
APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwp2Pq3-PYNvHOWe4IQVm5PqeJd5TcIc_mPDtLm0BkDEGYUxq-C1cnV3rNS1X3xfI1p7w/exec"
)
IMGBB_API_KEY = "70e3f4a06020949c79c82ca5dea96b02"

# ==========================================
# HÀM NÉN ẢNH VÀ GỬI DỮ LIỆU ĐÁM MÂY (IMGBB)
# ==========================================
def compress_image(uploaded_file, max_size=(800, 800), quality=50):
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail(max_size)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality)
        return base64.b64encode(output.getvalue()).decode('utf-8')
    except Exception as e:
        return f"ERROR:{str(e)}"

def upload_to_imgbb(b64_str):
    try:
        url = "https://api.imgbb.com/1/upload"
        data = urllib.parse.urlencode({'key': IMGBB_API_KEY, 'image': b64_str}).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get("success"):
                return res["data"]["url"]
        return None
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_api_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            resp_text = response.read().decode('utf-8')
            try:
                return json.loads(resp_text), None
            except json.JSONDecodeError:
                return None, "❌ LỖI API KHÔNG TRẢ VỀ JSON: Vui lòng kiểm tra quyền Deploy Apps Script."
    except Exception as e:
        return None, f"❌ LỖI KẾT NỐI API: {str(e)}"

def submit_registration(ho_ten, sdt, dia_ban, chuyen_mon, phuong_tien):
    payload = {
        "action": "dang_ky",
        "ho_ten": ho_ten,
        "sdt": sdt,
        "dia_ban": dia_ban,
        "chuyen_mon": chuyen_mon,
        "phuong_tien": phuong_tien
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except Exception:
        return False

def submit_to_google(ma_da, ten_doi, diem_lap, diem_giao, ds_hang, gps, tinh_trang, image_files):
    img_urls = []
    if image_files:
        for f in image_files:
            b64 = compress_image(f)
            if b64 and not b64.startswith("ERROR:"):
                link = upload_to_imgbb(b64)
                if link:
                    img_urls.append(link)
            elif b64.startswith("ERROR:"):
                return False, f"Lỗi nén ảnh: {f.name}"

    payload = {
        "action": "bao_cao",
        "ma_du_an": ma_da,
        "ten_doi": ten_doi,
        "diem_lap_dat": diem_lap,
        "diem_giao_hang": diem_giao,
        "ds_hang_hoa": ds_hang,
        "link_maps": gps,
        "tinh_trang": tinh_trang,
        "image_urls": img_urls
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            resp = json.loads(response.read().decode('utf-8'))
            if resp.get("status") == "success":
                return True, "Thành công"
            else:
                return False, f"Lỗi từ Google: {resp.get('message', 'Unknown Error')}"
    except Exception as e:
        return False, f"Lỗi mạng/Code: {str(e)}"

def get_pending_members():
    payload = {"action": "get_pending"}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8')).get("data", [])
    except Exception:
        return []

def approve_member(row_index, doi_gan):
    payload = {"action": "duyet_thanh_vien", "row": row_index, "doi_gan": doi_gan}
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            APPS_SCRIPT_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8')).get("status") == "success"
    except Exception:
        return False

def quet_mat_than(data_sheet, p_code, d_doi, d_diem):
    ds_kq = []
    if not data_sheet:
        return ds_kq
    idx_proj = -1
    idx_matb = -1
    idx_doi = -1
    idx_tentb = -1
    idx_sl = -1
    idx_diem = -1
    idx_dvt = -1
    header_row_index = -1
    for r_idx, r in enumerate(data_sheet[:10]):
        row_str = " ".join([str(x).upper() for x in r])
        if "MÃ CÔNG VIỆC" in row_str or "MÃ DA" in row_str or "TÊN THIẾT BỊ" in row_str:
            header_row_index = r_idx
            for i, h in enumerate(r):
                h_str = str(h).replace('\xa0', ' ').strip().upper()
                if "MÃ DỰ ÁN" in h_str or "MÃ DA" in h_str:
                    idx_proj = i
                elif "ĐỊA ĐIỂM LẮP" in h_str or "ĐIỂM GIAO" in h_str or "ĐỊA ĐIỂM" in h_str or "ĐƠN VỊ" in h_str:
                    idx_diem = i
                elif "MÃ CÔNG VIỆC" in h_str or "SKU" in h_str:
                    idx_matb = i
                elif "TÊN THIẾT BỊ" in h_str or "HÀNG HÓA" in h_str:
                    idx_tentb = i
                elif "SỐ LƯỢNG" in h_str or "SL" in h_str:
                    idx_sl = i
                elif "ĐƠN VỊ TÍNH" in h_str or "ĐVT" in h_str:
                    idx_dvt = i
                elif "ĐỘI GIAO THIẾT BỊ" in h_str or "ĐỘI NHẬN THIẾT BỊ" in h_str or "ĐỘI" in h_str or "NHÂN SỰ" in h_str:
                    idx_doi = i
            break
    if idx_proj == -1 or idx_diem == -1 or idx_doi == -1 or header_row_index == -1:
        return ds_kq
    p_c = str(p_code).replace('\xa0', ' ').strip().upper()
    d_d = str(d_diem).replace('\xa0', ' ').strip().upper()
    d_o = str(d_doi).replace('\xa0', ' ').strip().upper()
    for r in data_sheet[header_row_index + 1:]:
        if len(r) > max(idx_proj, idx_diem, idx_doi):
            c_proj = str(r[idx_proj]).replace('\xa0', ' ').strip().upper()
            c_diem = str(r[idx_diem]).replace('\xa0', ' ').strip().upper()
            c_doi = str(r[idx_doi]).replace('\xa0', ' ').strip().upper()
            cond_diem = (d_d in c_diem) or (c_diem != "" and c_diem in d_d)
            cond_doi = (d_o in c_doi) or (c_doi != "" and c_doi in d_o)
            if (p_c in c_proj) and cond_diem and cond_doi:
                sku = str(r[idx_matb]).strip() if (idx_matb > -1 and len(r) > idx_matb) else "TB-0X"
                ten = str(r[idx_tentb]).strip() if (idx_tentb > -1 and len(r) > idx_tentb) else "Thiết bị"
                sl = str(r[idx_sl]).strip() if (idx_sl > -1 and len(r) > idx_sl) else "1"
                dvt = str(r[idx_dvt]).strip() if (idx_dvt > -1 and len(r) > idx_dvt) else "Bộ"
                if ten and str(ten).upper() not in ["TÊN THIẾT BỊ / HÀNG HÓA", "TÊN THIẾT BỊ", "NONE", ""]:
                    ds_kq.append({"sku": sku, "ten": ten, "sl": sl, "dvt": dvt})
    return ds_kq

# ==========================================
# KHU VỰC HIỂN THỊ CHÍNH
# ==========================================
title_placeholder = st.empty()
title_placeholder.markdown(
    "<h2 style='text-align: center; color: #1E3A8A; font-weight: 900;'>🚀 QUẢN LÝ DỰ ÁN</h2>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; color: #64748B; font-size: 14px; "
    "margin-top: -10px; margin-bottom: 20px;'>Hệ thống Điều hành Hiện trường</p>",
    unsafe_allow_html=True
)

menu_options = [
    "📊 Báo cáo nhiệm vụ",
    "📝 Đăng ký thành viên",
    "🔒 ADMIN DUYỆT ĐK THÀNH VIÊN",
    "🔗 Báo cáo tiến độ (để lãnh đạo xem)"
]
selected_menu = st.selectbox("CHỌN CHỨC NĂNG", options=menu_options, label_visibility="collapsed")

if "Báo cáo" in selected_menu and "tiến độ" not in selected_menu:
    nav_tab = "Bao_cao"
elif "Đăng ký" in selected_menu:
    nav_tab = "Dang_ky"
elif "ADMIN" in selected_menu:
    nav_tab = "Admin"
else:
    nav_tab = "Link"

st.divider()

BAD_WORDS = [
    "MÃ DỰ ÁN", "TÊN DỰ ÁN", "DỰ ÁN", "MÃ DA", "MÃ CÔNG VIỆC",
    "MÃ ĐỘI", "TÊN ĐỘI", "ĐỘI THỰC HIỆN", "ĐỘI",
    "MÃ ĐIỂM", "ĐỊA ĐIỂM", "TÊN ĐIỂM", "ĐIỂM", "ĐƠN VỊ", "NONE", "NAN"
]

if nav_tab == "Dang_ky":
    st.markdown("##### 📝 ĐĂNG KÝ THÀNH VIÊN ĐỘI")
    with st.spinner("Đang tải dữ liệu..."):
        raw_data, err_msg = fetch_api_data()

    if err_msg:
        st.error(err_msg)
    else:
        ds_diem_raw = raw_data.get("danh_sach_diem", []) if isinstance(raw_data, dict) else []
        ds_diem_sach = [
            str(x).strip() for x in ds_diem_raw
            if str(x).strip() != "" and str(x).strip().upper() not in BAD_WORDS
        ]

        with st.form("form_dang_ky_thanh_vien"):
            reg_hoten = st.text_input("Họ và tên *", placeholder="Nhập đầy đủ họ và tên...")
            reg_sdt = st.text_input("Số điện thoại liên hệ *", placeholder="Nhập số điện thoại (Zalo)...")
            reg_diaban_list = st.multiselect("Địa bàn phụ trách", options=ds_diem_sach)
            chuyen_mon_opts = [
                "1. Vận chuyển / Giao nhận",
                "2. KTV Lắp đặt thiết bị",
                "3. Giám sát / Điều phối chung",
                "4. Kho vận / Hậu cứ"
            ]
            reg_chuyenmon = st.selectbox("Chuyên môn / Nhiệm vụ", options=chuyen_mon_opts)
            reg_phuongtien = st.selectbox("Phương tiện di chuyển", options=["Xe máy", "Xe tải", "Xe bán tải", "Khác"])

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("GỬI ĐĂNG KÝ", use_container_width=True):
                if not reg_hoten.strip() or not reg_sdt.strip():
                    st.warning("Vui lòng nhập đầy đủ Họ tên và Số điện thoại!")
                else:
                    if submit_registration(reg_hoten, reg_sdt, ", ".join(reg_diaban_list), reg_chuyenmon, reg_phuongtien):
                        st.success(f"Đăng ký thành công {reg_hoten}!")
                    else:
                        st.error("Gửi đăng ký thất bại!")

elif nav_tab == "Bao_cao":
    with st.spinner("Đang đồng bộ dữ liệu hệ thống..."):
        raw_data, err_msg = fetch_api_data()

    if err_msg:
        st.error(err_msg)
    else:
        data_ld = raw_data.get("KHO_LAP_DAT", []) if isinstance(raw_data, dict) else []
        data_vc = raw_data.get("KHO_VAN_CHUYEN", []) if isinstance(raw_data, dict) else []
        st.info(f"✅ Đã kết nối Mắt Thần: {len(data_ld)} dòng LĐ | {len(data_vc)} dòng VC")

        st.markdown("##### 1️⃣ CHỌN THÔNG TIN NHIỆM VỤ")

        ds_du_an_raw = raw_data.get("du_an", []) if isinstance(raw_data, dict) else []
        ds_du_an_sach = [
            str(x).strip() for x in ds_du_an_raw
            if str(x).strip() != "" and str(x).strip().upper() not in BAD_WORDS
        ]

        ds_doi_raw = raw_data.get("doi", []) if isinstance(raw_data, dict) else []
        ds_doi_sach = [
            str(x).strip() for x in ds_doi_raw
            if str(x).strip() != "" and str(x).strip().upper() not in BAD_WORDS
        ]

        ds_diem_raw = raw_data.get("danh_sach_diem", []) if isinstance(raw_data, dict) else []
        ds_diem_sach = [
            str(x).strip() for x in ds_diem_raw
            if str(x).strip() != "" and str(x).strip().upper() not in BAD_WORDS
        ]

        du_an_chon = st.selectbox("DỰ ÁN TRIỂN KHAI *", options=ds_du_an_sach, index=None)
        if du_an_chon:
            html_title = (
                "<h2 style='text-align: center; color: #1E3A8A; font-weight: 900;'>"
                f"🚀 QUẢN LÝ DỰ ÁN <br><span style='color: #DC2626; font-size: 22px;'>[ {du_an_chon} ]</span>"
                "</h2>"
            )
            title_placeholder.markdown(html_title, unsafe_allow_html=True)

        doi_thuc_hien = st.selectbox("TÊN ĐỘI THỰC HIỆN *", options=ds_doi_sach, index=None)
        diem_giao_lap = st.selectbox(
            "📍 ĐỊA ĐIỂM GIAO & LẮP *",
            options=ds_diem_sach,
            index=None,
            placeholder="🔍 Chạm để gõ tìm tên địa điểm..."
        )

        if diem_giao_lap:
            diem_den_chuan = f"{diem_giao_lap}, Tuyên Quang"
            diem_den_encoded = urllib.parse.quote(diem_den_chuan)
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={diem_den_encoded}"
            html_map_btn = (
                f'<a href="{maps_url}" target="_blank" style="text-decoration: none;">'
                '<div style="background-color: #E8F0FE; color: #1A73E8; padding: 12px; '
                'border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #1A73E8; '
                'margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">'
                '🗺️ MỞ GOOGLE MAPS DẪN ĐƯỜNG TỚI ĐÂY'
                '</div></a>'
            )
            st.markdown(html_map_btn, unsafe_allow_html=True)

        ds_hang = []
        if du_an_chon and doi_thuc_hien and diem_giao_lap:
            ds_hang_raw = (
                quet_mat_than(data_ld, du_an_chon, doi_thuc_hien, diem_giao_lap) +
                quet_mat_than(data_vc, du_an_chon, doi_thuc_hien, diem_giao_lap)
            )
            seen = set()
            for item in ds_hang_raw:
                key = f"{item['sku']}_{item['ten']}_{item['sl']}"
                if key not in seen:
                    seen.add(key)
                    ds_hang.append(item)

            st.markdown("##### 2️⃣ THIẾT BỊ CẦN BÁO CÁO")
            if ds_hang:
                tb_md = "| SKU | Thiết bị | SL | ĐVT |\n| :--- | :--- | :---: | :---: |\n"
                for item in ds_hang:
                    tb_md += f"| {item['sku']} | {item['ten']} | **{item['sl']}** | {item['dvt']} |\n"
                st.markdown(tb_md)
            else:
                st.warning("Không tìm thấy hàng hóa phân bổ cho dự án, đội và địa điểm này.")
        else:
            st.warning("💡 Chọn đầy đủ thông tin để hiển thị Mắt Thần.")

        st.markdown("##### 3️⃣ CHỤP ẢNH HIỆN TRƯỜNG (Tối đa 10 ảnh)")
        img_captured_list = st.file_uploader(
            "📸 Chọn hoặc Chụp ảnh từ điện thoại",
            type=["jpg", "jpeg", "png", "heic"],
            accept_multiple_files=True
        )

        if img_captured_list:
            if len(img_captured_list) > 10:
                st.warning("⚠️ Chỉ được tải tối đa 10 ảnh. Các ảnh thừa sẽ bị bỏ qua!")
                img_captured_list = img_captured_list[:10]
            st.success(f"✅ Đã chọn {len(img_captured_list)} ảnh. Sẵn sàng báo cáo!")

        st.markdown("##### 4️⃣ CHỐT TỌA ĐỘ GPS (BẮT BUỘC)")
        html_gps_box = (
            '<div style="background-color: #F8FAFC; border: 2px dashed #3B82F6; '
            'border-radius: 15px; padding: 15px; text-align: center; margin-bottom: 10px;">'
            '<h4 style="color: #1E3A8A; margin: 0 0 5px 0; font-size: 16px;">'
            '📍 BẤM NÚT TÂM NGẮM BÊN DƯỚI ĐỂ CHECK-IN</h4>'
            '<p style="color: #64748B; font-size: 13px; margin: 0;">'
            '(Vui lòng cho phép trình duyệt truy cập vị trí)</p></div>'
        )
        st.markdown(html_gps_box, unsafe_allow_html=True)

        col_gps1, col_gps2, col_gps3 = st.columns([1, 1, 1])
        with col_gps2:
            loc = streamlit_geolocation()

        gps_link = ""
        if loc and loc.get('latitude'):
            lat = loc['latitude']
            lon = loc['longitude']
            gps_link = f"https://www.google.com/maps?q={lat},{lon}"
            st.success("✅ Đã chốt tọa độ GPS an toàn!")
        else:
            st.error("⚠️ Bạn chưa bấm định vị. Vui lòng bấm vào biểu tượng Tâm ngắm ở trên!")

        st.markdown("##### 5️⃣ GỬI BÁO CÁO NGHIỆM THU")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🚚 ĐÃ GIAO", type="primary", use_container_width=True):
                if not gps_link:
                    st.error("❌ Thiếu GPS!")
                elif not img_captured_list:
                    st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner(f"Đang xử lý tải siêu tốc {len(img_captured_list)} ảnh..."):
                        is_ok, msg = submit_to_google(
                            du_an_chon if du_an_chon else "",
                            doi_thuc_hien,
                            "",
                            diem_giao_lap,
                            ds_hang,
                            gps_link,
                            "Đã giao hàng",
                            img_captured_list
                        )
                        if is_ok:
                            st.success("🎉 XONG!")
                            st.balloons()
                        else:
                            st.error(f"❌ THẤT BẠI: {msg}")
        with col_b2:
            if st.button("🔧 ĐÃ LẮP", type="primary", use_container_width=True):
                if not gps_link:
                    st.error("❌ Thiếu GPS!")
                elif not img_captured_list:
                    st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner(f"Đang xử lý tải siêu tốc {len(img_captured_list)} ảnh..."):
                        is_ok, msg = submit_to_google(
                            du_an_chon if du_an_chon else "",
                            doi_thuc_hien,
                            diem_giao_lap,
                            "",
                            ds_hang,
                            gps_link,
                            "Đã lắp đặt",
                            img_captured_list
                        )
                        if is_ok:
                            st.success("🎉 XONG!")
                            st.balloons()
                        else:
                            st.error(f"❌ THẤT BẠI: {msg}")
        with col_b3:
            if st.button("✅ GIAO LẮP XONG", type="primary", use_container_width=True):
                if not gps_link:
                    st.error("❌ Thiếu GPS!")
                elif not img_captured_list:
                    st.error("❌ Thiếu Hình Ảnh!")
                else:
                    with st.spinner(f"Đang xử lý tải siêu tốc {len(img_captured_list)} ảnh..."):
                        is_ok, msg = submit_to_google(
                            du_an_chon if du_an_chon else "",
                            doi_thuc_hien,
                            diem_giao_lap,
                            diem_giao_lap,
                            ds_hang,
                            gps_link,
                            "Giao và Lắp xong",
                            img_captured_list
                        )
                        if is_ok:
                            st.success("🎉 XONG!")
                            st.balloons()
                        else:
                            st.error(f"❌ THẤT BẠI: {msg}")

elif nav_tab in ["Admin", "Link"]:
    if nav_tab == "Admin":
        st.markdown("##### 🔒 ADMIN DUYỆT ĐK THÀNH VIÊN")
    else:
        st.markdown("##### 🔒 DỮ LIỆU ĐIỀU HÀNH DÀNH CHO LÃNH ĐẠO")

    khung_nhap_pin = st.empty()
    pass_input = khung_nhap_pin.text_input("Nhập mã PIN:", type="password")

    if pass_input == SECURE_PASS:
        khung_nhap_pin.empty()
        st.success("Xác thực thành công!")

        if st.button("🔄 Đồng bộ dữ liệu mới nhất từ Google Sheets", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        if nav_tab == "Admin":
            with st.spinner("Đang tải dữ liệu..."):
                raw_data, err_msg = fetch_api_data()
            if err_msg:
                st.error(err_msg)
            else:
                st.info("💡 Danh sách thành viên đang chờ duyệt:")
                ds_doi_raw = raw_data.get("doi", []) if isinstance(raw_data, dict) else []
                ds_doi_sach = [
                    str(x).strip() for x in ds_doi_raw
                    if str(x).strip() != "" and str(x).strip().upper() not in BAD_WORDS
                ]

                with st.spinner("Đang quét thành viên mới..."):
                    pending = get_pending_members()

                if not pending:
                    st.success("🎉 Hiện không có thành viên nào cần duyệt!")
                else:
                    for tv in pending:
                        card_html = (
                            '<div class="pending-card">'
                            f'<h4 style="color:#1E3A8A; margin-top:0px; margin-bottom:5px;">👤 {tv["ho_ten"]}</h4>'
                            f'<b>📞 SĐT:</b> {tv["sdt"]} <br>'
                            f'<b>📍 Địa bàn:</b> {tv["dia_ban"]} <br>'
                            f'<b>🛠 Chuyên môn:</b> {tv["chuyen_mon"]} <br>'
                            f'<b>🛵 Phương tiện:</b> {tv["phuong_tien"]}'
                            '</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

                        doi_chon = st.selectbox(
                            f"Gán Đội cho {tv['ho_ten']}:",
                            options=["-- Chưa gán đội --"] + ds_doi_sach,
                            key=f"doi_{tv['row']}"
                        )

                        btn_label = f"✅ BẤM ĐỂ DUYỆT {tv['ho_ten'].upper()}"
                        if st.button(btn_label, type="primary", key=f"btn_{tv['row']}", use_container_width=True):
                            voi_doi = "" if doi_chon == "-- Chưa gán đội --" else doi_chon
                            with st.spinner("Đang truyền lệnh về Google Sheets..."):
                                if approve_member(tv['row'], voi_doi):
                                    st.cache_data.clear()
                                    st.success("Đã duyệt thành công! Dữ liệu đã được làm mới.")
                                else:
                                    st.error("Lỗi mạng, vui lòng thử lại.")
                        st.divider()

        elif nav_tab == "Link":
            with st.spinner("Đang đồng bộ số liệu từ Trung Tâm Điều Hành..."):
                raw_data, err_msg = fetch_api_data()
            if err_msg:
                st.error(err_msg)
            else:
                dash = raw_data.get("dashboard", {}) if isinstance(raw_data, dict) else {}
                try:
                    raw_giao = str(dash.get('giao_hang', '0')).replace(',', '').strip()
                    val_giao = int(float(raw_giao)) if raw_giao and raw_giao != 'None' else 0
                    if val_giao > 1000:
                        val_giao = 1
                except Exception:
                    val_giao = 0

                try:
                    raw_lap = str(dash.get('lap_dat', '0')).replace(',', '').strip()
                    val_lap = int(float(raw_lap)) if raw_lap and raw_lap != 'None' else 0
                    if val_lap > 1000:
                        val_lap = 1
                except Exception:
                    val_lap = 0

                try:
                    raw_nghiem = str(dash.get('nghiem_thu', '0')).replace(',', '').strip()
                    val_nghiem = int(float(raw_nghiem)) if raw_nghiem and raw_nghiem != 'None' else 0
                except Exception:
                    val_nghiem = 0

                try:
                    raw_tong = str(dash.get('tong_diem', '136')).replace(',', '').strip()
                    val_tong = int(float(raw_tong)) if raw_tong and raw_tong != 'None' else 136
                    if val_tong <= 0:
                        val_tong = 136
                except Exception:
                    val_tong = 136

                st.markdown("### 📈 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN")

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    box1 = (
                        '<div style="background-color: #FFF3CD; padding: 15px; border-radius: 10px; '
                        'text-align: center; border: 1px solid #FFEEBA; margin-bottom: 10px;">'
                        '<h5 style="color: #856404; margin: 0; font-size: 14px;">🚚 GIAO HÀNG</h5>'
                        f'<h2 style="color: #D35400; margin: 0; font-weight: 900; font-size: 30px;">{val_giao}</h2>'
                        '</div>'
                    )
                    box2 = (
                        '<div style="background-color: #D4EDDA; padding: 15px; border-radius: 10px; '
                        'text-align: center; border: 1px solid #C3E6CB; margin-bottom: 10px;">'
                        '<h5 style="color: #155724; margin: 0; font-size: 14px;">☑️ NGHIỆM THU</h5>'
                        f'<h2 style="color: #28A745; margin: 0; font-weight: 900; font-size: 30px;">{val_nghiem}</h2>'
                        '</div>'
                    )
                    st.markdown(box1, unsafe_allow_html=True)
                    st.markdown(box2, unsafe_allow_html=True)

                with col_d2:
                    box3 = (
                        '<div style="background-color: #D1ECF1; padding: 15px; border-radius: 10px; '
                        'text-align: center; border: 1px solid #BEE5EB; margin-bottom: 10px;">'
                        '<h5 style="color: #0C5460; margin: 0; font-size: 14px;">🔧 LẮP ĐẶT</h5>'
                        f'<h2 style="color: #007BFF; margin: 0; font-weight: 900; font-size: 30px;">{val_lap}</h2>'
                        '</div>'
                    )
                    box4 = (
                        '<div style="background-color: #F8D7DA; padding: 15px; border-radius: 10px; '
                        'text-align: center; border: 1px solid #F5C6CB; margin-bottom: 10px;">'
                        '<h5 style="color: #721C24; margin: 0; font-size: 14px;">📍 TỔNG ĐIỂM</h5>'
                        f'<h2 style="color: #DC3545; margin: 0; font-weight: 900; font-size: 30px;">{val_tong}</h2>'
                        '</div>'
                    )
                    st.markdown(box3, unsafe_allow_html=True)
                    st.markdown(box4, unsafe_allow_html=True)

                def tinh_ty_le(so_thuc_te, tong):
                    return min(so_thuc_te / tong, 1.0) if tong > 0 else 0.0

                def tinh_pct_str(so_thuc_te, tong):
                    return f"{(so_thuc_te / tong) * 100:.1f}%" if tong > 0 else "0%"

                html_chart = (
                    '<div style="background-color: white; padding: 20px; border-radius: 10px; '
                    'border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); '
                    'margin-top: 15px; margin-bottom: 20px;">'
                    '<h4 style="color: #1E293B; margin-top: 0; margin-bottom: 20px; '
                    'font-size: 16px; text-align: center;">📊 TỶ TRỌNG SO SÁNH TIẾN ĐỘ</h4>'

                    '<div style="margin-bottom: 15px;">'
                    '<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">'
                    f'<span style="font-weight: bold; color: #D35400; font-size: 14px;">📦 Giao hàng ({val_giao}/{val_tong})</span>'
                    f'<span style="font-weight: bold; color: #D35400; font-size: 14px;">{tinh_pct_str(val_giao, val_tong)}</span>'
                    '</div>'
                    '<div style="width: 100%; background-color: #F1F5F9; border-radius: 10px; height: 12px; overflow: hidden;">'
                    f'<div style="width: {tinh_ty_le(val_giao, val_tong) * 100}%; background-color: #D35400; height: 100%; border-radius: 10px;"></div>'
                    '</div></div>'

                    '<div style="margin-bottom: 15px;">'
                    '<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">'
                    f'<span style="font-weight: bold; color: #007BFF; font-size: 14px;">⚙️ Lắp đặt ({val_lap}/{val_tong})</span>'
                    f'<span style="font-weight: bold; color: #007BFF; font-size: 14px;">{tinh_pct_str(val_lap, val_tong)}</span>'
                    '</div>'
                    '<div style="width: 100%; background-color: #F1F5F9; border-radius: 10px; height: 12px; overflow: hidden;">'
                    f'<div style="width: {tinh_ty_le(val_lap, val_tong) * 100}%; background-color: #007BFF; height: 100%; border-radius: 10px;"></div>'
                    '</div></div>'

                    '<div style="margin-bottom: 5px;">'
                    '<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">'
                    f'<span style="font-weight: bold; color: #28A745; font-size: 14px;">✅ Hoàn thành ({val_nghiem}/{val_tong})</span>'
                    f'<span style="font-weight: bold; color: #28A745; font-size: 14px;">{tinh_pct_str(val_nghiem, val_tong)}</span>'
                    '</div>'
                    '<div style="width: 100%; background-color: #F1F5F9; border-radius: 10px; height: 12px; overflow: hidden;">'
                    f'<div style="width: {tinh_ty_le(val_nghiem, val_tong) * 100}%; background-color: #28A745; height: 100%; border-radius: 10px;"></div>'
                    '</div></div></div>'
                )
                st.markdown(html_chart, unsafe_allow_html=True)
