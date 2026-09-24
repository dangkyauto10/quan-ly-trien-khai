import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import pandas as pd
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="Hệ Thống Quản Trị & Báo Cáo Tiến Độ",
    page_icon="📊",
    layout="wide"
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
# 2. ĐỌC DỮ LIỆU TỔNG QUAN
# -------------------------------------------------------------
danh_sach_ktv = ["Vỹ - Hạnh - Hiền (Nguyễn Văn A)", "KTV-01", "KTV-02", "KTV-03"]
danh_sach_du_an = []
toan_bo_diem_goc = []
kho_phan_bo_map = {}
diem_theo_du_an = {}

if sh:
    try:
        ws_da = sh.worksheet("DANH_SACH_DU_AN")
        for r in ws_da.get_all_records():
            ma = str(r.get("Mã dự án", "")).strip()
            ten = str(r.get("Tên dự án", "")).strip()
            if ma and ma != "nan":
                nhan = f"{ma} - {ten}" if ten and ten != "nan" else ma
                danh_sach_du_an.append({"ma": ma, "hien_thi": nhan})
    except Exception:
        pass

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

# -------------------------------------------------------------
# PHÂN CHIA GIAO DIỆN BẰNG 2 TAB
# -------------------------------------------------------------
tab_dashboard, tab_baocao = st.tabs(["📊 BÁO CÁO TIẾN ĐỘ (DÀNH CHO LÃNH ĐẠO)", "📱 BÁO CÁO HIỆN TRƯỜNG"])

# =============================================================
# TAB 1: BÁO CÁO DÀNH CHO LÃNH ĐẠO
# =============================================================
with tab_dashboard:
    st.header("📈 Báo Cáo Tiến Độ Dự Án Thời Gian Thực")
    st.caption("Cập nhật tự động từ kết quả triển khai thực địa")

    # Đọc dữ liệu từ BAO_CAO_TRIEN_KHAI
    df_bc = pd.DataFrame()
    if sh:
        try:
            ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
            data_all = ws_bc.get_all_records()
            df_bc = pd.DataFrame(data_all)
        except Exception as e:
            st.error(f"Chưa lấy được dữ liệu báo cáo: {e}")

    if not df_bc.empty:
        # Bộ lọc dự án cho Lãnh đạo
        ds_loc_da = ["Tất cả dự án"] + [item["hien_thi"] for item in danh_sach_du_an]
        da_duoc_chon = st.selectbox("🔍 Xem tiến độ theo Dự án:", options=ds_loc_da, key="filter_da_boss")
        
        df_hien_thi = df_bc.copy()
        if da_duoc_chon != "Tất cả dự án":
            ma_da_loc = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == da_duoc_chon)
            # Lọc theo tiền tố [Mã dự án]
            df_hien_thi = df_hien_thi[df_hien_thi["Tên đội thực hiện"].astype(str).str.contains(ma_da_loc, na=False)]

        # Tính toán các chỉ số KPI
        tong_luot = len(df_hien_thi)
        so_giao_hang = len(df_hien_thi[df_hien_thi["Tình trạng thực hiện"] == "Đã giao hàng"])
        so_lap_dat = len(df_hien_thi[df_hien_thi["Tình trạng thực hiện"] == "Đã lắp đặt xong"])
        tong_tb = 0
        if "Số lượng thiết bị thực tế" in df_hien_thi.columns:
            try:
                tong_tb = int(pd.to_numeric(df_hien_thi["Số lượng thiết bị thực tế"], errors="coerce").fillna(0).sum())
            except:
                pass

        # 4 Thẻ KPI nổi bật trên điện thoại
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("📦 Đã Giao Hàng", f"{so_giao_hang} lượt")
        kpi2.metric("🔧 Đã Lắp Đặt", f"{so_lap_dat} lượt")
        kpi3.metric("🎯 Tổng Thiết Bị", f"{tong_tb} chiếc")
        kpi4.metric("📝 Tổng Lần Ghi Nhận", f"{tong_luot} lượt")

        st.markdown("---")
        
        # Biểu đồ cột tổng hợp
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.subheader("📊 Tỷ Lệ Hoàn Thành Công Việc")
            df_chart = pd.DataFrame({
                "Hạng mục": ["Giao hàng", "Lắp đặt xong"],
                "Số lượng": [so_giao_hang, so_lap_dat]
            }).set_index("Hạng mục")
            st.bar_chart(df_chart)

        with col_c2:
            st.subheader("📌 Tóm Tắt Tình Hình")
            st.success(f"✔️ Tiến độ lắp đặt hiện trường: **{so_lap_dat}** điểm đã hoàn thành.")
            st.info(f"✔️ Tổng thiết bị đã triển khai đến các điểm: **{tong_tb}** thiết bị.")
            if so_giao_hang > 0:
                tl = round((so_lap_dat / so_giao_hang) * 100, 1) if so_giao_hang else 0
                st.warning(f"⚡ Tỷ lệ lắp đặt / giao hàng: **{tl}%**")

        st.markdown("---")
        st.subheader("📋 Danh Sách Nhật Ký Hiện Trường Mới Nhất")
        
        # Hiển thị bảng chi tiết, cho phép xem link Maps trực tiếp
        df_view = df_hien_thi.tail(15).iloc[::-1]  # Lấy 15 dòng mới nhất lên đầu
        st.dataframe(
            df_view,
            use_container_width=True,
            column_config={
                "Link Google Maps": st.column_config.LinkColumn("Vị trí GPS", display_text="📍 Xem bản đồ")
            },
            hide_index=True
        )
    else:
        st.info("Chưa có dữ liệu báo cáo nào được gửi từ hiện trường.")

# =============================================================
# TAB 2: GIAO DIỆN BÁO CÁO CHO ANH EM HIỆN TRƯỜNG
# =============================================================
with tab_baocao:
    st.header("📱 Ghi Nhận Kết Quả Hiện Trường")
    st.caption("Dành cho cán bộ kỹ thuật và đội trưởng thi công")

    lua_chon_da = st.selectbox(
        "Đang thực hiện cho Dự án:",
        options=[item["hien_thi"] for item in danh_sach_du_an],
        key="sb_da_tech"
    )
    ma_da_chon = next(item["ma"] for item in danh_sach_du_an if item["hien_thi"] == lua_chon_da)

    ds_diem_kha_dung = diem_theo_du_an.get(ma_da_chon, [])
    if not ds_diem_kha_dung:
        ds_diem_kha_dung = toan_bo_diem_goc if toan_bo_diem_goc else ["Phường Minh Xuân", "Phường Nông Tiến"]

    col_kb1, col_kb2 = st.columns(2)
    with col_kb1:
        can_bo_chon = st.selectbox("Cán bộ / Đội trưởng:", options=danh_sach_ktv, key="sb_ktv_tech")
    with col_kb2:
        diem_chon = st.selectbox("Địa điểm lắp đặt:", options=ds_diem_kha_dung, key="sb_diem_tech")

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
        placeholder="https://www.google.com/maps?q=...",
        key="inp_gps_tech"
    )

    st.markdown("---")
    st.subheader("3. Xác nhận hoàn thành công việc")

    col_b1, col_b2 = st.columns(2)

    def xu_ly_ghi_nhan(loai_hinh):
        if not sh:
            st.error("Không có kết nối với Google Sheets.")
            return
        
        with st.spinner("Đang ghi nhận dữ liệu..."):
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
                    doi_nhan = item.get("doi_nhan", "VHH")
                    if sl <= 0:
                        continue
                    
                    ma_cv = f"CV-{datetime.now(tz_vn).strftime('%H%M%S')}-{idx_tb+1}"
                    
                    # Ghi LAP_DAT
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

                    # Ghi VAN_CHUYEN
                    if ws_vc:
                        ws_vc.append_row([
                            ma_da_chon,
                            doi_nhan,
                            ten_tb,
                            sl,
                            "Xe nội bộ",
                            can_bo_chon,
                            diem_chon,
                            "Đã giao hàng",
                            thoi_gian_vn
                        ])

                    # Ghi BAO_CAO_TRIEN_KHAI
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
        if st.button("📦 ĐÃ GIAO HÀNG", use_container_width=True, type="primary", key="btn_gh_tech"):
            xu_ly_ghi_nhan("Đã giao hàng")

    with col_b2:
        if st.button("🔧 ĐÃ LẮP ĐẶT XONG", use_container_width=True, key="btn_ld_tech"):
            xu_ly_ghi_nhan("Đã lắp đặt xong")
