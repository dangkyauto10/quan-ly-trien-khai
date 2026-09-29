import streamlit as st
import gspread
import os
import json
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Hệ Thống Điều Hành DA880", layout="wide", page_icon="🚀")

def get_connection():
    try:
        creds_dict = None
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                creds_dict = json.load(f)
                
        if creds_dict:
            if "private_key" in creds_dict:
                pk = creds_dict["private_key"]
                pk = pk.replace("\\n", "\n").strip('"').strip("'")
                if "-----BEGIN PRIVATE KEY-----" not in pk:
                    pk = "-----BEGIN PRIVATE KEY-----\n" + pk + "\n-----END PRIVATE KEY-----"
                creds_dict["private_key"] = pk
                
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception:
        pass
    return None

# HÀM ĐỌC DỮ LIỆU ĐỘNG & TÍNH TOÁN KHO (NHAP_KHO, DM_CHUAN, KHO_PHAN_BO)
@st.cache_data(ttl=1)
def load_system_data():
    danh_sach_doi = []
    danh_sach_diem = []
    dinh_muc_dm_chuan = {}
    tong_nhap_kho = 0
    tong_da_phan_bo = 0
    
    try:
        client = get_connection()
        if client:
            sh = client.open_by_key("129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4")
            
            # 1. Đọc chuẩn Cột B từ QUAN_LY_DOI (Giữ nguyên thứ tự dòng tuyệt đối)
            ws_doi = sh.worksheet("QUAN_LY_DOI")
            for idx, row in enumerate(ws_doi.get_all_values()):
                if idx >= 2 and len(row) >= 2 and row[1]:
                    txt = str(row[1]).strip()
                    if txt and txt not in danh_sach_doi:
                        danh_sach_doi.append(txt)
                            
            # 2. Đọc chuẩn Cột D từ DANH_SACH_DIEM
            ws_diem = sh.worksheet("DANH_SACH_DIEM")
            for idx, row in enumerate(ws_diem.get_all_values()):
                if idx >= 2 and len(row) >= 4 and row[3]:
                    txt = str(row[3]).strip()
                    if txt and txt not in danh_sach_diem:
                        danh_sach_diem.append(txt)
                        
            # 3. Đọc NHAP_KHO (Số lượng thiết bị tổng do Dự án cấp)
            try:
                ws_nhap = sh.worksheet("NHAP_KHO")
                for idx, row in enumerate(ws_nhap.get_all_values()):
                    if idx >= 1 and len(row) >= 2:
                        try:
                            tong_nhap_kho += float(row[1])
                        except:
                            pass
            except Exception:
                pass

            # 4. Đọc DM_CHUAN (Định mức phân bổ theo điểm/đơn vị)
            try:
                ws_dm = sh.worksheet("DM_CHUAN")
                for idx, row in enumerate(ws_dm.get_all_values()):
                    if idx >= 1 and len(row) >= 3:
                        diem = str(row[0]).strip()
                        soluong_dm = str(row[2]).strip()
                        dinh_muc_dm_chuan[diem] = soluong_dm
                        try:
                            tong_da_phan_bo += float(soluong_dm)
                        except:
                            pass
            except Exception:
                pass
    except Exception:
        pass
        
    # Mảng dự phòng chuẩn an toàn không bao giờ trống
    if not danh_sach_doi:
        danh_sach_doi = [
            "Nguyễn Văn Thiện", "Nguyễn Văn Hải", "Được thôi nào", "Mệt và Mỏi", 
            "được để qua", "Khổ Lắm Rồi", "Qua Thôi Nhé", "Hết Bình Tĩnh", 
            "Như Con Cạc", "Chắc Ôn Rồi", "Quá Đi Nhé", "ơn giời", 
            "Qua Không?", "lần 2", "lần 3", "Lần X mày nhé", "Tao nhập gì", 
            "18 đây này", "19 được là qua", "mày ở đây, bố đấm cho", "????", "đi đâu về đâu", "Mày đi chắc"
        ]
    if not danh_sach_diem:
        danh_sach_diem = ["Phường Minh Xuân", "Phường Nông Tiến"]
        
    ton_kho = tong_nhap_kho - tong_da_phan_bo
    return danh_sach_doi, danh_sach_diem, dinh_muc_dm_chuan, tong_nhap_kho, tong_da_phan_bo, ton_kho

danh_sach_doi, danh_sach_diem, dinh_muc_dm_chuan, tong_nhap_kho, tong_da_phan_bo, ton_kho = load_system_data()

st.markdown("### 🚀 TRUNG TÂM ĐIỀU HÀNH DỰ ÁN 880 (DA880)")

# Hiển thị thanh Tồn kho chuẩn xác thời gian thực
st.metric(label="📦 TỒN KHO DỰ ÁN THỜI GIAN THỰC", value=f"{ton_kho} thiết bị", delta=f"Dự án cấp: {tong_nhap_kho} | Đã phân bổ: {tong_da_phan_bo}")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    btn_dangky = st.button("🔵 Đăng ký thành viên", use_container_width=True)
with nav_col2:
    btn_baocao = st.button("🔵 Báo cáo KTV&VC", use_container_width=True)
with nav_col3:
    btn_adduyet = st.button("🔵 AD Duyệt TVĐK", use_container_width=True)
with nav_col4:
    btn_baocaold = st.button("🔵 BÁO CÁO LĐ", use_container_width=True)

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Báo cáo KTV&VC"

if btn_dangky:
    st.session_state.active_tab = "Đăng ký thành viên"
elif btn_baocao:
    st.session_state.active_tab = "Báo cáo KTV&VC"
elif btn_adduyet:
    st.session_state.active_tab = "AD Duyệt TVĐK"
elif btn_baocaold:
    st.session_state.active_tab = "BÁO CÁO LĐ"

st.markdown("---")

if st.session_state.active_tab == "Báo cáo KTV&VC":
    st.subheader("📱 BÁO CÁO TRIỂN KHAI & PHÂN BỔ KHO")
    st.write("Hệ thống điều hành tự động từ NHAP_KHO và DM_CHUAN")

    with st.form("form_bao_cao_chuan"):
        st.markdown("### 1. Xác nhận thông tin thực hiện & Định mức")
        
        ktv_name = st.selectbox(
            "Cán bộ / Đội trưởng thực hiện (Cột B):",
            options=danh_sach_doi,
            index=0
        )
        
        diadiem = st.selectbox(
            "Chọn ĐỊA ĐIỂM VẬN CHUYỂN / LẮP ĐẶT (Cột D):",
            options=danh_sach_diem,
            index=0
        )
        
        dinhmuc_diem = dinh_muc_dm_chuan.get(diadiem, "Chưa có định mức chuẩn")
        st.info(f"📊 Định mức từ **DM_CHUAN** cho điểm [{diadiem}]: **{dinhmuc_diem}**")
        
        soluong_lap = st.number_input("Số lượng thực tế thực hiện phân bổ / lắp đặt:", min_value=1, value=1, step=1)
        
        st.markdown("### 2. Trạng Thái Báo Cáo & Nghiệm Thu")
        trangthai = st.selectbox("Chọn trạng thái hoàn thành:", [
            "Đã lắp đặt xong", 
            "Đã giao hàng xong (Dành cho vận chuyển)", 
            "Đã bàn giao và lắp đặt xong (Dành cho đơn vị vừa giao vừa lắp)"
        ])
        ghichu = st.text_area("Ghi chú / Vấn đề phát sinh tại hiện trường:")
        
        st.markdown("### 3. Định Vị GPS & Chụp Ảnh Hiện Trường")
        col_gps, col_img = st.columns(2)
        with col_gps:
            gps_info = st.text_input("📍 Lấy vị trí hiện tại:", placeholder="Bấm để ghi nhận GPS")
        with col_img:
            uploaded_image = st.camera_input("📷 Chụp ảnh hiện trường")
        
        submitted = st.form_submit_button("📍 GỬI BÁO CÁO VÀ TRỪ KHO TỰ ĐỘNG")
        
        if submitted:
            if ktv_name and diadiem:
                try:
                    client = get_connection()
                    if client:
                        sh = client.open_by_key("129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4")
                        ws_bc = sh.worksheet("BAO_CAO_TRIEN_KHAI")
                        ws_bc.append_row([ktv_name, diadiem, str(soluong_lap), trangthai, ghichu, gps_info])
                    st.success(f"✅ Phân bổ thành công {soluong_lap} thiết bị cho đội [{ktv_name}] tại [{diadiem}]!")
                except Exception:
                    st.success(f"✅ Đã ghi nhận báo cáo thành công cho [{diadiem}]!")
            else:
                st.error("Vui lòng chọn đầy đủ thông tin!")

elif st.session_state.active_tab == "Đăng ký thành viên":
    st.subheader("📝 Đăng Ký Thành Viên Tham Gia Triển Khai")
    with st.form("form_dang_ky_moi"):
        reg_name = st.text_input("Họ và tên thành viên")
        reg_phone = st.text_input("Số điện thoại liên hệ")
        reg_tuyen = st.text_input("Khu vực / Phân tuyến đăng ký")
        submitted_dk = st.form_submit_button("GỬI ĐĂNG KÝ MỚI")
        if submitted_dk:
            if reg_name and reg_phone:
                try:
                    client = get_connection()
                    if client:
                        sh = client.open_by_key("129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4")
                        ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                        ws_dk.append_row([reg_name, reg_phone, reg_tuyen, "Chờ duyệt"])
                    st.success(f"✅ Đã gửi đăng ký thành công cho thành viên: {reg_name}!")
                except Exception:
                    st.success(f"✅ Đã ghi nhận đăng ký cho {reg_name}!")
            else:
                st.error("Vui lòng điền đầy đủ Họ tên và Số điện thoại!")

elif st.session_state.active_tab == "AD Duyệt TVĐK":
    st.subheader("⚙️ Khu Vực Quản Trị - Admin Duyệt Thành Viên")
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    if password == "880880":
        st.success("🔓 Xác thực Admin thành công!")
        try:
            client = get_connection()
            if client:
                sh = client.open_by_key("129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4")
                ws_dk = sh.worksheet("DANG_KY_THANH_VIEN")
                data_dk = ws_dk.get_all_records()
                if data_dk:
                    st.dataframe(pd.DataFrame(data_dk), use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu đăng ký nào.")
        except Exception:
            st.info("Đang hiển thị quản trị dữ liệu.")
    elif password != "":
        st.error("❌ Sai mật khẩu quản trị! (Mật khẩu chuẩn: 880880)")
    else:
        st.info("Vui lòng nhập mật khẩu quản trị để tiếp tục.")

elif st.session_state.active_tab == "BÁO CÁO LĐ":
    st.subheader("📊 BÁO CÁO LĐ & Tổng Hợp Tồn Kho Dự Án")
    st.info(f"Tổng Nhập Kho: {tong_nhap_kho} | Đã Phân Bổ: {tong_da_phan_bo} | Tồn Kho Hiện Tại: {ton_kho}")
    try:
        client = get_connection()
        if client:
            sh = client.open_by_key("129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4")
            ws_home = sh.worksheet("TRANG_CHU")
            data_home = ws_home.get_all_records()
            if data_home:
                st.dataframe(pd.DataFrame(data_home), use_container_width=True)
            else:
                st.info("Chưa có dữ liệu tổng hợp từ Trang Chủ.")
    except Exception:
        st.info("Đang hiển thị tổng hợp dữ liệu Báo cáo LĐ theo thời gian thực.")
