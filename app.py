import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from datetime import datetime
import pytz
import pandas as pd
from streamlit_js_eval import get_geolocation
import urllib.parse
import json

# -------------------------------------------------------------
# 1. PHÂN QUYỀN ĐƯỜNG DẪN (?view=dangky | ?view=lanhdao | mặc định)
# -------------------------------------------------------------
che_do_xem = st.query_params.get("view", "")

if che_do_xem == "lanhdao":
    st.set_page_config(page_title="Báo Cáo Tiến Độ - Lãnh Đạo", page_icon="📈", layout="wide")
elif che_do_xem == "dangky":
    st.set_page_config(page_title="Đăng Ký Thành Viên Đội Thi Công", page_icon="📝", layout="centered")
else:
    st.set_page_config(page_title="Điều Hành Dự Án Hiện Trường", page_icon="📱", layout="centered")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def ket_noi_dich_vu():
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        
        client_sheets = gspread.authorize(creds)
        file_sheet = client_sheets.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        return file_sheet, creds
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None, None

sh, creds_he_thong = ket_noi_dich_vu()

def tai_anh_len_drive(creds, file_obj, ten_file):
    if not creds or not file_obj:
        return ""
    try:
        session = AuthorizedSession(creds)
        metadata = {'name': ten_file, 'mimeType': 'image/jpeg'}
        files = {
            'data': ('metadata', json.dumps(metadata), 'application/json; charset=UTF-8'),
            'file': (ten_file, file_obj.getvalue(), 'image/jpeg')
        }
        res = session.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink', files=files)
        data = res.json()
        file_id = data.get('id')
        if file_id:
            session.post(f'https://www.googleapis.com/drive/v3/files/{file_id}/permissions', json={'role': 'reader', 'type': 'anyone'})
            return data.get('webViewLink', f'https://drive.google.com/file/d/{file_id}/view')
        return ""
    except Exception:
        return ""

# =============================================================
# TRƯỜNG HỢP 1: FORM ĐĂNG KÝ THÀNH VIÊN
# =============================================================
if che_do_xem == "dangky":
    st.title("📝 ĐĂNG KÝ THÀNH VIÊN ĐỘI THI CÔNG")
    st.caption("Dành cho các đội thợ / đối tác vận chuyển & lắp đặt dự án")
    st.markdown("---")

    ds_diem_dk = []
    if sh:
        try:
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            d_data = ws_diem.get_all_values()
            col_idx = 3
            for row in d_data[1:]:
                if len(row) > col_idx and row[col_idx].strip() and row[col_idx].strip() not in ds_diem_dk:
                    ds_diem_dk.append(row[col_idx].strip())
        except Exception:
            pass

    with st.form("form_dang_ky_thanh_vien"):
        ho_ten = st.text_input("1. Họ và tên đầy đủ *", placeholder="Ví dụ: Nguyễn Văn Bình")
        so_dien_thoai = st.text_input("2. Số điện thoại (dùng Zalo) *", placeholder="Ví dụ: 0912345678")
        
        dia_ban_chon = st.multiselect(
            "3. Địa bàn mong muốn nhận tuyến (chọn một hoặc nhiều điểm) *",
            options=ds_diem_dk if ds_diem_dk else ["Phường Minh Xuân", "Phường Nông Tiến", "Xã Thái Bình"]
        )
        
        chuyen_mon = st.selectbox(
            "4. Đăng ký hạng mục chuyên môn *", 
            options=["Lắp đặt thiết bị kỹ thuật", "Vận chuyển hàng hóa", "Cả vận chuyển & lắp đặt"]
        )
        phuong_tien = st.selectbox(
            "5. Phương tiện di chuyển *", 
            options=["Xe máy cá nhân", "Xe bán tải", "Xe tải chở hàng", "Không có xe vận chuyển"]
        )
        
        btn_gui_dk = st.form_submit_button("🚀 GỬI BẢN ĐĂNG KÝ THÀNH VIÊN", use_container_width=True)

    if btn_gui_dk:
        if not ho_ten.strip() or not so_dien_thoai.strip() or not dia_ban_chon:
            st.warning("⚠️ Vui lòng điền đầy đủ các thông tin có dấu sao (*).")
        else:
            with st.spinner("Đang lưu thông tin..."):
                try:
                    ws_dk = None
                    try:
                        ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                    except Exception:
                        ws_dk = sh.add_worksheet(title="DANG_KY_THANH_VIEN", rows="100", cols="10")
                        ws_dk.append_row([
                            "Thời gian", "Họ và tên", "Số điện thoại", 
                            "Địa bàn phụ trách", "Chuyên môn", "Phương tiện", 
                            "Trạng thái duyệt", "Đội gán"
                        ])

                    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
                    thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
                    dia_ban_str = ", ".join(dia_ban_chon)

                    ws_dk.append_row([
                        thoi_gian_vn, ho_ten.strip(), f"'{so_dien_thoai.strip()}",
                        dia_ban_str, chuyen_mon, phuong_tien, "Chờ duyệt", ""
                    ])
                    st.success("🎉 Đăng ký thành công! Hồ sơ đã được gửi tới Ban Quản Trị.")
                    
                    noi_dung_zalo = (
                        f"📢 [THÀNH VIÊN ĐĂNG KÝ TUYẾN]\n"
                        f"▪ Họ tên: {ho_ten}\n"
                        f"▪ SĐT: {so_dien_thoai}\n"
                        f"▪ Các điểm nhận: {dia_ban_str}\n"
                        f"▪ Chuyên môn: {chuyen_mon}\n"
                        f"👉 Vui lòng vào Google Sheets duyệt & gán đội."
                    )
                    st.link_button("📲 BÁO TIN CHO ADMIN QUA ZALO", f"https://zalo.me/share?text={urllib.parse.quote(noi_dung_zalo)}", use_container_width=True)
                except Exception as e:
                    st.error(f"Lỗi: {e}")

# =============================================================
# TRƯỜNG HỢP 2 & 3: LÃNH ĐẠO & HIỆN TRƯỜNG
# =============================================================
else:
    danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)"]
    ktv_diem_map = {}
    danh_sach_du_an = []
    toan_bo_diem_goc = []
    kho_phan_bo_map = {}
    trang_thai_diem = {}

    if sh:
        try:
            ws_tv = sh.worksheet("DANG_KY_THANH_VIEN")
            data_tv = ws_tv.get_all_values()
            if len(data_tv) >= 2:
                for row in data_tv[1:]:
                    if len(row) >= 7:
                        ten_tv = row[1].strip()
                        diem_giao = row[3].strip()
                        tt_duyet = row[6].strip().lower()
                        doi_gan = row[7].strip() if len(row) >= 8 else ""
                        
                        if ("duyệt" in tt_duyet or "đã duyệt" in tt_duyet) and "chờ" not in tt_duyet:
                            nhan_tv = f"{doi_gan} - {ten_tv}" if doi_gan else ten_tv
                            if nhan_tv not in danh_sach_ktv:
                                danh_sach_ktv.append(nhan_tv)
                            if diem_giao:
                                cac_diem = [d.strip() for d in diem_giao.split(",") if d.strip()]
                                ktv_diem_map[nhan_tv] = cac_diem
        except Exception:
            pass

        try:
            ws_da = sh.worksheet("DANH_SACH_DU_AN")
            d_da = ws_da.get_all_values()
            for r in d_da[1:]:
                if len(r) >= 2 and r[0].strip() and r[0].strip() != "Mã dự án":
                    nhan = f"{r[0].strip()} - {r[1].strip()}" if r[1].strip() else r[0].strip()
                    danh_sach_du_an.append({"ma": r[0].strip(), "hien_thi": nhan})
        except Exception:
            pass

        try:
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            data_diem = ws_diem.get_all_values()
            col_diem_idx = 3
            for r in data_diem[1:]:
                if len(r) > col_diem_idx and r[col_diem_idx].strip():
                    val = r[col_diem_idx].strip()
                    if val not in toan_bo_diem_goc and "Địa điểm" not in val:
                        toan_bo_diem_goc.append(val)
        except Exception:
            pass

        try:
            ws_td = sh.worksheet("TIEN_DO")
            d_td = ws_td.get_all_values()
            for r in d_td[2:]:
                if len(r) >= 4 and r[3].strip():
                    trang_thai_diem[r[3].strip()] = r[2].strip()
        except Exception:
            pass

    if not danh_sach_du_an:
        danh_sach_du_an = [{"ma": "DA880", "hien_thi": "DA880 - Viettel Tuyên Quang"}]

    # ---------------------------------------------------------
    # GIAO DIỆN LÃNH ĐẠO
    # ---------------------------------------------------------
    if che_do_xem == "lanhdao":
        st.title("📈 BÁO CÁO TIẾN ĐỘ THỜI GIAN THỰC")
        st.caption("Ban Lãnh đạo & Quản lý điều hành dự án")

        df_bc = pd.DataFrame()
        if sh:
            try:
                ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                raw_vals = ws_bc.get_all_values()
                if len(raw_vals) >= 2:
                    h_idx = 0
                    for idx, r in enumerate(raw_vals[:3]):
                        if any("thời gian" in str(c).lower() for c in r):
                            h_idx = idx
                            break
                    headers = [str(c).strip() if str(c).strip() else f"Cột_{i+1}" for i, c in enumerate(raw_vals[h_idx])]
                    clean_rows = [r + [""] * (len(headers) - len(r)) for r in raw_vals[h_idx+1:] if any(str(x).strip() for x in r)]
                    df_bc = pd.DataFrame([r[:len(headers)] for r in clean_rows], columns=headers)
            except Exception:
                pass

        if not df_bc.empty:
            ds_loc = ["Tất cả dự án"] + [item["hien_thi"] for item in danh_sach_du_an]
            da_chon = st.selectbox("🔍 Lọc theo Dự án:", options=ds_loc)
            
            c_doi = next((c for c in df_bc.columns if "đội" in c.lower()), "Tên đội thực hiện")
            c_tt = next((c for c in df_bc.columns if "tình trạng" in c.lower() or "trạng thái" in c.lower()), "Tình trạng thực hiện")
            c_sl = next((c for c in df_bc.columns if "số lượng" in c.lower()), "Số lượng thiết bị thực tế")
            c_gps = next((c for c in df_bc.columns if "maps" in c.lower() or "gps" in c.lower()), "Link Google Maps")

            df_view = df_bc.copy()
            if da_chon != "Tất cả dự án":
                ma_loc = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == da_chon)
                if c_doi in df_view.columns:
                    df_view = df_view[df_view[c_doi].astype(str).str.contains(ma_loc, na=False)]

            so_gh = len(df_view[df_view[c_tt].astype(str).str.contains("giao", case=False, na=False)]) if c_tt in df_view.columns else 0
            so_ld = len(df_view[df_view[c_tt].astype(str).str.contains("lắp", case=False, na=False)]) if c_tt in df_view.columns else 0
            tong_tb = int(pd.to_numeric(df_view[c_sl], errors="coerce").fillna(0).sum()) if c_sl in df_view.columns else 0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📦 Đã Giao Hàng", f"{so_gh} lượt")
            k2.metric("🔧 Đã Lắp Đặt Xong", f"{so_ld} lượt")
            k3.metric("🎯 Tổng Thiết Bị", f"{tong_tb} chiếc")
            k4.metric("📝 Tổng Nhật Ký", f"{len(df_view)} lượt")

            st.markdown("---")
            st.subheader("📋 Nhật Ký Thực Địa Chi Tiết")
            cfg = {c_gps: st.column_config.LinkColumn("Vị trí GPS", display_text="📍 Xem bản đồ")} if c_gps in df_view.columns else {}
            st.dataframe(df_view.tail(25).iloc[::-1], use_container_width=True, column_config=cfg, hide_index=True)
        else:
            st.info("Chưa có dữ liệu báo cáo.")

    # ---------------------------------------------------------
    # GIAO DIỆN HIỆN TRƯỜNG CHO THỢ
    # ---------------------------------------------------------
    else:
        st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")
        st.caption("Dẫn đường theo tuyến & Báo cáo thi công")

        lua_chon_da = st.selectbox("Dự án đang thực hiện:", options=[item["hien_thi"] for item in danh_sach_du_an], key="sb_da_tech")
        ma_da_chon = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == lua_chon_da)

        col_kb1, col_kb2 = st.columns(2)
        with col_kb1:
            can_bo_chon = st.selectbox("Cán bộ / Đội trưởng:", options=danh_sach_ktv, key="sb_ktv_tech")

        ds_tuyen_cua_doi = ktv_diem_map.get(can_bo_chon, [])
        if not ds_tuyen_cua_doi:
            ds_tuyen_cua_doi = toan_bo_diem_goc if toan_bo_diem_goc else ["Phường Minh Xuân", "Phường Nông Tiến"]

        with col_kb2:
            st.info(f"📍 Tuyến nhận: **{len(ds_tuyen_cua_doi)} điểm**")

        st.markdown("---")
        st.markdown("### 🧭 Tra cứu tuyến & Chỉ đường Maps")
        diem_tim_kiem = st.selectbox("🔍 Chọn điểm trong tuyến cần đến:", options=ds_tuyen_cua_doi, key="sb_tim_diem")

        tt_hien_tai = trang_thai_diem.get(diem_tim_kiem, "Chưa thực hiện")
        if "100%" in tt_hien_tai or "xong" in tt_hien_tai.lower():
            st.success(f"📌 **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Đã xong)")
        elif "giao" in tt_hien_tai.lower():
            st.warning(f"📌 **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Cần lắp đặt)")
        else:
            st.info(f"📌 **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Chưa làm)")

        link_dan_duong = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(diem_tim_kiem + ', Tuyên Quang')}"
        st.link_button(f"🚗 MỞ GOOGLE MAPS DẪN ĐƯỜNG TỚI: {diem_tim_kiem.upper()}", link_dan_duong, type="primary", use_container_width=True)

        st.markdown("---")
        st.subheader("1. Thông tin Báo cáo Hiện trường")
        diem_chon = st.selectbox(
            "Địa điểm báo cáo:", 
            options=ds_tuyen_cua_doi, 
            index=ds_tuyen_cua_doi.index(diem_tim_kiem) if diem_tim_kiem in ds_tuyen_cua_doi else 0, 
            key="sb_diem_tech"
        )

        sl_mac_dinh = st.number_input("Số lượng thiết bị thực tế bàn giao / lắp đặt:", min_value=1, max_value=500, value=5, step=1, key="sl_def_tech")

        st.markdown("---")
        st.subheader("2. Chụp ảnh nghiệm thu / Biên bản")
        file_anh = st.file_uploader("Chụp hoặc tải ảnh hiện trường (Camera sau):", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if file_anh:
            st.image(file_anh, caption="Ảnh xem trước", width=250)

        st.markdown("---")
        st.subheader("3. Định vị Hiện trường (GPS)")
        location = get_geolocation()
        link_maps_tu_dong = f"https://www.google.com/maps?q={location['coords']['latitude']},{location['coords']['longitude']}" if location and "coords" in location else ""
        link_gps_cuoi = st.text_input("Link Google Maps vị trí hiện tại:", value=link_maps_tu_dong, placeholder="https://www.google.com/maps?q=...", key="inp_gps_tech")

        st.markdown("---")
        st.subheader("4. Xác nhận hoàn thành công việc")

        if "zalo_share_url" not in st.session_state:
            st.session_state["zalo_share_url"] = None

        col_b1, col_b2 = st.columns(2)

        def xu_ly_ghi_nhan(loai_hinh):
            if not sh:
                return
            with st.spinner("Đang ghi nhận..."):
                try:
                    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
                    thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
                    link_anh_drive = tai_anh_len_drive(creds_he_thong, file_anh, f"{ma_da_chon}_{diem_chon}_{datetime.now(tz_vn).strftime('%Y%m%d_%H%M%S')}.jpg") if file_anh else ""

                    ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                    if loai_hinh == "Đã lắp đặt xong":
                        sh.worksheet("LAP_DAT").append_row([f"CV-{datetime.now(tz_vn).strftime('%H%M%S')}", ma_da_chon, can_bo_chon, "Bộ thiết bị chuẩn", sl_mac_dinh, diem_chon, "Đã hoàn thành", thoi_gian_vn, link_gps_cuoi])
                    elif loai_hinh == "Đã giao hàng":
                        sh.worksheet("VAN_CHUYEN").append_row([ma_da_chon, "Đội nhận", "Bộ thiết bị chuẩn", sl_mac_dinh, "Xe nội bộ", can_bo_chon, diem_chon, "Đã giao hàng", thoi_gian_vn])

                    ws_bc.append_row([thoi_gian_vn, f"[{ma_da_chon}] {can_bo_chon}", f"{diem_chon} (Bộ thiết bị)", sl_mac_dinh, link_gps_cuoi, f"{loai_hinh} - [Xem ảnh]({link_anh_drive})" if link_anh_drive else loai_hinh])

                    dong_anh = f"\n📸 Ảnh: {link_anh_drive}" if link_anh_drive else ""
                    noi_dung_zalo = (
                        f"📢 [BÁO CÁO TIẾN ĐỘ]\n"
                        f"▪ Dự án: {lua_chon_da}\n"
                        f"▪ Cán bộ: {can_bo_chon}\n"
                        f"▪ Điểm: {diem_chon}\n"
                        f"▪ Hạng mục: {loai_hinh} (SL: {sl_mac_dinh})\n"
                        f"▪ Thời gian: {thoi_gian_vn}\n"
                        f"📍 GPS: {link_gps_cuoi if link_gps_cuoi else 'Chưa có'}"
                        f"{dong_anh}"
                    )
                    st.session_state["zalo_share_url"] = f"https://zalo.me/share?text={urllib.parse.quote(noi_dung_zalo)}"
                    st.success(f"✅ Đã ghi nhận thành công cho {diem_chon}!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

        with col_b1:
            if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, key="btn_gh_tech"):
                xu_ly_ghi_nhan("Đã giao hàng")

        with col_b2:
            if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True, type="primary", key="btn_ld_tech"):
                xu_ly_ghi_nhan("Đã lắp đặt xong")

        if st.session_state.get("zalo_share_url"):
            st.markdown("---")
            st.link_button("📲 GỬI BÁO CÁO NÀY QUA ZALO NGAY", st.session_state["zalo_share_url"], type="primary", use_container_width=True)
