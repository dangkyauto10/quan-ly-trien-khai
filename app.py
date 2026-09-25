import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import pytz
import pandas as pd
from streamlit_js_eval import get_geolocation
import urllib.parse
import io

# -------------------------------------------------------------
# 1. PHÂN QUYỀN ĐƯỜNG DẪN
# -------------------------------------------------------------
che_do_xem = st.query_params.get("view", "")

if che_do_xem == "lanhdao":
    st.set_page_config(
        page_title="Báo Cáo Tiến Độ - Lãnh Đạo",
        page_icon="📈",
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="Điều Hành Dự Án Hiện Trường",
        page_icon="📱",
        layout="centered"
    )

# -------------------------------------------------------------
# 2. KẾT NỐI SHEETS & DRIVE
# -------------------------------------------------------------
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
        drive_service = build("drive", "v3", credentials=creds)
        return file_sheet, drive_service
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return None, None

sh, drive_service = ket_noi_dich_vu()

def tai_anh_len_drive(file_obj, ten_file):
    if not drive_service or not file_obj:
        return ""
    try:
        file_metadata = {
            "name": ten_file,
            "mimeType": "image/jpeg"
        }
        media = MediaIoBaseUpload(io.BytesIO(file_obj.read()), mimetype="image/jpeg", resumable=True)
        uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
        
        file_id = uploaded.get("id")
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"}
        ).execute()
        return uploaded.get("webViewLink", "")
    except Exception as e:
        return f"Lỗi tải ảnh: {e}"

# -------------------------------------------------------------
# 3. ĐỌC DỮ LIỆU ĐA DỰ ÁN & PHÂN BỔ
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_du_an = []
toan_bo_diem_goc = []
kho_phan_bo_map = {}
diem_theo_du_an = {}
trang_thai_diem = {}

if sh:
    # 1. Danh sách Dự án
    try:
        ws_da = sh.worksheet("DANH_SACH_DU_AN")
        data_da = ws_da.get_all_values()
        if len(data_da) >= 2:
            for row in data_da[1:]:
                if len(row) >= 2:
                    ma = row[0].strip()
                    ten = row[1].strip()
                    if ma and ma.lower() != "nan" and ma != "Mã dự án":
                        nhan = f"{ma} - {ten}" if ten and ten.lower() != "nan" else ma
                        danh_sach_du_an.append({"ma": ma, "hien_thi": nhan})
    except Exception:
        pass

    # 2. Danh sách Điểm gốc
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
                    if val and val not in toan_bo_diem_goc:
                        toan_bo_diem_goc.append(val)
    except Exception:
        pass

    # 3. Trạng thái từ TIEN_DO
    try:
        ws_td = sh.worksheet("TIEN_DO")
        data_td = ws_td.get_all_values()
        if len(data_td) >= 3:
            for row in data_td[2:]:
                if len(row) >= 4:
                    d_name = row[3].strip()
                    d_status = row[2].strip()
                    if d_name:
                        trang_thai_diem[d_name] = d_status
    except Exception:
        pass

    # 4. Kho phân bổ
    try:
        ws_kho = sh.worksheet("KHO_PHAN_BO")
        data_kho = ws_kho.get_all_values()
        if len(data_kho) >= 2:
            headers_k = [str(x).strip() for x in data_kho[1]] if len(data_kho) > 1 and "Mã dự án" in data_kho[1] else [str(x).strip() for x in data_kho[0]]
            col_da, col_tb, col_sl, col_dvt, col_doi, col_diem = 0, 3, 4, 5, 6, 7
            for i, h in enumerate(headers_k):
                if "Mã dự án" in h: col_da = i
                elif "Tên thiết bị" in h: col_tb = i
                elif "Số lượng" in h and "tồn" not in h.lower(): col_sl = i
                elif "Đơn vị" in h: col_dvt = i
                elif "Đội nhận" in h: col_doi = i
                elif "Địa điểm" in h: col_diem = i

            start_idx = 2 if "Mã dự án" in data_kho[1] else 1
            for row in data_kho[start_idx:]:
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
                    doi_nhan = row[col_doi].strip() if len(row) > col_doi else "VHH"
                    
                    key = (m_da, d_diem)
                    if key not in kho_phan_bo_map:
                        kho_phan_bo_map[key] = []
                    kho_phan_bo_map[key].append({
                        "thiet_bi": t_tb,
                        "so_luong": sl,
                        "dvt": dvt,
                        "doi_nhan": doi_nhan
                    })
                    
                    if m_da not in diem_theo_du_an:
                        diem_theo_du_an[m_da] = []
                    if d_diem not in diem_theo_du_an[m_da]:
                        diem_theo_du_an[m_da].append(d_diem)
    except Exception:
        pass

if not danh_sach_du_an:
    danh_sach_du_an = [{"ma": "DA880", "hien_thi": "DA880 - Viettel Tuyên Quang"}, {"ma": "Dự án 76", "hien_thi": "Dự án 76"}]

# =============================================================
# TRƯỜNG HỢP 1: BÁO CÁO CHO LÃNH ĐẠO (?view=lanhdao)
# =============================================================
if che_do_xem == "lanhdao":
    st.title("📈 BÁO CÁO TIẾN ĐỘ THỜI GIAN THỰC")
    st.caption("Dành riêng cho Ban Lãnh đạo & Quản lý điều hành")

    df_bc = pd.DataFrame()
    if sh:
        try:
            ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
            raw_vals = ws_bc.get_all_values()
            if len(raw_vals) >= 2:
                header_idx = 0
                for r_idx, r in enumerate(raw_vals[:3]):
                    if any("thời gian" in str(c).lower() for c in r):
                        header_idx = r_idx
                        break
                
                headers = [str(c).strip() for c in raw_vals[header_idx]]
                headers = [h if h else f"Cột_{i+1}" for i, h in enumerate(headers)]
                
                rows_data = raw_vals[header_idx + 1:]
                clean_rows = []
                for r in rows_data:
                    if any(str(x).strip() for x in r):
                        padded = r + [""] * (len(headers) - len(r))
                        clean_rows.append(padded[:len(headers)])
                
                df_bc = pd.DataFrame(clean_rows, columns=headers)
        except Exception as e:
            st.error(f"Lỗi nạp báo cáo: {e}")

    if not df_bc.empty:
        ds_loc_da = ["Tất cả dự án"] + [item["hien_thi"] for item in danh_sach_du_an]
        da_duoc_chon = st.selectbox("🔍 Lọc xem theo Dự án:", options=ds_loc_da)
        
        col_doi_ten = next((c for c in df_bc.columns if "đội" in c.lower() or "cán bộ" in c.lower()), "Tên đội thực hiện")
        col_tt_ten = next((c for c in df_bc.columns if "tình trạng" in c.lower() or "trạng thái" in c.lower()), "Tình trạng thực hiện")
        col_sl_ten = next((c for c in df_bc.columns if "số lượng" in c.lower()), "Số lượng thiết bị thực tế")
        col_gps_ten = next((c for c in df_bc.columns if "maps" in c.lower() or "link" in c.lower() or "gps" in c.lower()), "Link Google Maps")

        df_hien_thi = df_bc.copy()
        if da_duoc_chon != "Tất cả dự án":
            ma_da_loc = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == da_duoc_chon)
            if col_doi_ten in df_hien_thi.columns:
                df_hien_thi = df_hien_thi[df_hien_thi[col_doi_ten].astype(str).str.contains(ma_da_loc, na=False)]

        tong_luot = len(df_hien_thi)
        so_giao_hang = len(df_hien_thi[df_hien_thi[col_tt_ten].astype(str).str.contains("giao", case=False, na=False)]) if col_tt_ten in df_hien_thi.columns else 0
        so_lap_dat = len(df_hien_thi[df_hien_thi[col_tt_ten].astype(str).str.contains("lắp", case=False, na=False)]) if col_tt_ten in df_hien_thi.columns else 0
        tong_tb = 0
        if col_sl_ten in df_hien_thi.columns:
            try:
                tong_tb = int(pd.to_numeric(df_hien_thi[col_sl_ten], errors="coerce").fillna(0).sum())
            except:
                pass

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("📦 Đã Giao Hàng", f"{so_giao_hang} lượt")
        kpi2.metric("🔧 Đã Lắp Đặt Xong", f"{so_lap_dat} lượt")
        kpi3.metric("🎯 Tổng Thiết Bị", f"{tong_tb} chiếc")
        kpi4.metric("📝 Tổng Nhật Ký", f"{tong_luot} lượt")

        st.markdown("---")
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.subheader("📊 Tỷ Lệ Thực Hiện")
            df_chart = pd.DataFrame({
                "Hạng mục": ["Giao hàng", "Lắp đặt xong"],
                "Số lượng": [so_giao_hang, so_lap_dat]
            }).set_index("Hạng mục")
            st.bar_chart(df_chart)

        with col_c2:
            st.subheader("📌 Tóm Tắt Tình Hình")
            st.success(f"✔️ Điểm lắp đặt hoàn thành: **{so_lap_dat}** điểm.")
            st.info(f"✔️ Tổng thiết bị cấp phát thực địa: **{tong_tb}** chiếc.")
            if so_giao_hang > 0:
                tl = round((so_lap_dat / so_giao_hang) * 100, 1)
                st.warning(f"⚡ Tỷ lệ hoàn thiện lắp đặt / giao nhận: **{tl}%**")

        st.markdown("---")
        st.subheader("📋 Nhật Ký Hiện Trường (Kèm GPS & Ảnh)")
        df_view = df_hien_thi.tail(25).iloc[::-1]
        cfg = {}
        if col_gps_ten in df_view.columns:
            cfg[col_gps_ten] = st.column_config.LinkColumn("Vị trí GPS", display_text="📍 Xem bản đồ")
            
        st.dataframe(
            df_view,
            use_container_width=True,
            column_config=cfg,
            hide_index=True
        )
    else:
        st.info("Chưa có dữ liệu báo cáo nào được ghi nhận.")

# =============================================================
# TRƯỜNG HỢP 2: BÁO CÁO HIỆN TRƯỜNG & TÌM ĐƯỜNG GOOGLE MAPS
# =============================================================
else:
    st.title("📱 ĐIỀU HÀNH HIỆN TRƯỜNG")
    st.caption("Dẫn đường vệ tinh & Báo cáo tiến độ")

    # 1. CHỌN DỰ ÁN
    lua_chon_da = st.selectbox(
        "Dự án đang thực hiện:",
        options=[item["hien_thi"] for item in danh_sach_du_an],
        key="sb_da_tech"
    )
    ma_da_chon = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == lua_chon_da)

    ds_diem_kha_dung = diem_theo_du_an.get(ma_da_chon, [])
    if not ds_diem_kha_dung:
        ds_diem_kha_dung = toan_bo_diem_goc if toan_bo_diem_goc else ["Phường Minh Xuân", "Phường Nông Tiến"]

    # ---------------------------------------------------------
    # TÍNH NĂNG MỚI: TÌM ĐỊA ĐIỂM & CHỈ ĐƯỜNG TRỰC TIẾP (HIỂN THỊ CỐ ĐỊNH)
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧭 Tra cứu điểm & Chỉ đường Maps")
    diem_tim_kiem = st.selectbox(
        "🔍 Chọn hoặc gõ tìm điểm cần tới:",
        options=ds_diem_kha_dung,
        key="sb_tim_diem"
    )

    tt_hien_tai = trang_thai_diem.get(diem_tim_kiem, "Chưa thực hiện")
    if "100%" in tt_hien_tai or "xong" in tt_hien_tai.lower():
        st.success(f"📌 Điểm: **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Đã xong)")
    elif "giao" in tt_hien_tai.lower():
        st.warning(f"📌 Điểm: **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Cần lắp đặt)")
    else:
        st.info(f"📌 Điểm: **{diem_tim_kiem}** — Trạng thái: **{tt_hien_tai}** (Chưa làm)")

    # Nút bấm mở Google Maps chuẩn native Streamlit
    link_dan_duong = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(diem_tim_kiem + ', Tuyên Quang')}"
    st.link_button(
        f"🚗 MỞ GOOGLE MAPS DẪN ĐƯỜNG TỚI: {diem_tim_kiem.upper()}",
        link_dan_duong,
        type="primary",
        use_container_width=True
    )

    # ---------------------------------------------------------
    # 2. KHU VỰC BÁO CÁO THI CÔNG
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("1. Thông tin Báo cáo Hiện trường")

    col_kb1, col_kb2 = st.columns(2)
    with col_kb1:
        can_bo_chon = st.selectbox("Cán bộ / Đội trưởng:", options=danh_sach_ktv, key="sb_ktv_tech")
    with col_kb2:
        # Tự động gợi ý điểm vừa tìm ở trên làm mặc định
        idx_mac_dinh = 0
        if diem_tim_kiem in ds_diem_kha_dung:
            idx_mac_dinh = ds_diem_kha_dung.index(diem_tim_kiem)
        diem_chon = st.selectbox("Địa điểm báo cáo:", options=ds_diem_kha_dung, index=idx_mac_dinh, key="sb_diem_tech")

    key_tra_cuu = (ma_da_chon, diem_chon)
    danh_sach_tb = kho_phan_bo_map.get(key_tra_cuu, [])

    st.markdown("#### 📦 Danh mục thiết bị thực hiện:")
    ket_qua_nhap = []

    if danh_sach_tb:
        for idx, item in enumerate(danh_sach_tb):
            tb_name = item["thiet_bi"]
            sl_dm = item["so_luong"]
            dvt = item.get("dvt", "Chiếc")
            doi_nhan = item.get("doi_nhan", "VHH")
            
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
            ket_qua_nhap.append({
                "thiet_bi": tb_name,
                "so_luong": sl_tt,
                "dvt": dvt,
                "doi_nhan": doi_nhan
            })
    else:
        st.info(f"Điểm '{diem_chon}' chưa cấu hình chi tiết ở KHO_PHAN_BO. Mặc định nhận 5 thiết bị chuẩn:")
        sl_mac_dinh = st.number_input("Số lượng thiết bị thực tế:", min_value=1, max_value=500, value=5, step=1, key="sl_def_tech")
        ket_qua_nhap.append({
            "thiet_bi": "Thiết bị chuẩn theo gói",
            "so_luong": sl_mac_dinh,
            "dvt": "Thiết bị",
            "doi_nhan": "VHH"
        })

    # CHỤP ẢNH / TẢI ẢNH
    st.markdown("---")
    st.subheader("2. Chụp ảnh nghiệm thu / Biên bản")
    st.caption("Chạm vào bên dưới để chụp ảnh bằng Camera sau hoặc tải ảnh:")
    file_anh = st.file_uploader("Chụp hoặc tải ảnh hiện trường:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if file_anh:
        st.image(file_anh, caption="Ảnh xem trước", width=250)

    # GPS VỊ TRÍ HIỆN TẠI
    st.markdown("---")
    st.subheader("3. Định vị Hiện trường (GPS)")
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
        "Link Google Maps hiện tại:",
        value=link_maps_tu_dong,
        placeholder="https://www.google.com/maps?q=...",
        key="inp_gps_tech"
    )

    # ---------------------------------------------------------
    # 4. XÁC NHẬN BÁO CÁO & NÚT ZALO
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("4. Xác nhận hoàn thành công việc")

    # Lưu thông tin sau khi ghi thành công vào session_state để hiện nút Zalo chuẩn
    if "zalo_share_url" not in st.session_state:
        st.session_state["zalo_share_url"] = None

    col_b1, col_b2 = st.columns(2)

    def xu_ly_ghi_nhan(loai_hinh):
        if not sh:
            st.error("Không có kết nối với Google Sheets.")
            return
        
        with st.spinner("Đang lưu trữ dữ liệu và tải ảnh lên hệ thống..."):
            try:
                tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
                thoi_gian_vn = datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M:%S")
                
                link_anh_drive = ""
                if file_anh:
                    ten_file_drive = f"{ma_da_chon}_{diem_chon}_{datetime.now(tz_vn).strftime('%Y%m%d_%H%M%S')}.jpg"
                    link_anh_drive = tai_anh_len_drive(file_anh, ten_file_drive)

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

                ds_tb_text = []
                for idx_tb, item in enumerate(ket_qua_nhap):
                    ten_tb = item["thiet_bi"]
                    sl = item["so_luong"]
                    doi_nhan = item.get("doi_nhan", "VHH")
                    if sl <= 0:
                        continue
                    
                    ds_tb_text.append(f"{ten_tb} (SL: {sl})")
                    ma_cv = f"CV-{datetime.now(tz_vn).strftime('%H%M%S')}-{idx_tb+1}"
                    
                    if ws_ld:
                        ws_ld.append_row([
                            ma_cv, ma_da_chon, can_bo_chon, ten_tb, sl,
                            diem_chon, "Đã hoàn thành", thoi_gian_vn, link_gps_cuoi
                        ])

                    if ws_vc:
                        ws_vc.append_row([
                            ma_da_chon, doi_nhan, ten_tb, sl, "Xe nội bộ",
                            can_bo_chon, diem_chon, "Đã giao hàng", thoi_gian_vn
                        ])

                    if ws_bc:
                        noi_dung_tt = loai_hinh
                        if link_anh_drive and "http" in link_anh_drive:
                            noi_dung_tt = f"{loai_hinh} - [Xem ảnh]({link_anh_drive})"
                        
                        ws_bc.append_row([
                            thoi_gian_vn,
                            f"[{ma_da_chon}] {can_bo_chon}",
                            f"{diem_chon} ({ten_tb})",
                            sl,
                            link_gps_cuoi,
                            noi_dung_tt
                        ])

                text_tb_str = ", ".join(ds_tb_text)
                link_anh_kem = f"\n📸 Link ảnh: {link_anh_drive}" if (link_anh_drive and "http" in link_anh_drive) else ""
                
                noi_dung_zalo = (
                    f"📢 [BÁO CÁO TIẾN ĐỘ]\n"
                    f"▪ Dự án: {lua_chon_da}\n"
                    f"▪ Cán bộ: {can_bo_chon}\n"
                    f"▪ Điểm: {diem_chon}\n"
                    f"▪ Hạng mục: {loai_hinh}\n"
                    f"▪ Thiết bị: {text_tb_str}\n"
                    f"▪ Thời gian: {thoi_gian_vn}\n"
                    f"📍 Vị trí GPS: {link_gps_cuoi if link_gps_cuoi else 'Chưa có'}"
                    f"{link_anh_kem}"
                )
                
                st.session_state["zalo_share_url"] = f"https://zalo.me/share?text={urllib.parse.quote(noi_dung_zalo)}"
                st.success(f"✅ Đã ghi nhận thành công cho [{ma_da_chon}] tại {diem_chon}!")
                
            except Exception as e:
                st.error(f"Lỗi khi gửi dữ liệu: {e}")

    with col_b1:
        if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="secondary", key="btn_gh_tech"):
            xu_ly_ghi_nhan("Đã giao hàng")

    with col_b2:
        if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True, type="primary", key="btn_ld_tech"):
            xu_ly_ghi_nhan("Đã lắp đặt xong")

    # Nút Zalo chính thức dùng st.link_button không bao giờ bị chặn popup
    if st.session_state.get("zalo_share_url"):
        st.markdown("---")
        st.link_button(
            "📲 GỬI BÁO CÁO NÀY QUA ZALO NGAY",
            st.session_state["zalo_share_url"],
            type="primary",
            use_container_width=True
        )
