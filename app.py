import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Thiết Lập Hệ Thống Tự Động", page_icon="⚙️")

# 1. KẾT NỐI GOOGLE SHEETS
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
        st.error(f"Lỗi kết nối: {e}")
        return None

sh = ket_noi_sheets()

st.title("⚙️ CẬP NHẬT CẤU HÌNH DANH SÁCH ĐỘI")
st.write("Bấm nút bên dưới để chuyển danh sách Đội nhận thiết bị sang **Cột B (Tên đội)** của sheet `QUAN_LY_DOI`.")

if st.button("🚀 CẬP NHẬT LẠI DANH SÁCH ĐỘI (CỘT B)", type="primary"):
    if not sh:
        st.error("Chưa kết nối được với Google Sheets.")
    else:
        with st.spinner("Đang cập nhật trực tiếp vào Google Sheets..."):
            try:
                ws_kpb = sh.worksheet("KHO_PHAN_BO")
                id_kpb = ws_kpb.id

                # Cấu hình Cột G nhận dữ liệu từ QUAN_LY_DOI!B2:B30 (bỏ dòng 1 tiêu đề)
                requests = [
                    {
                        "setDataValidation": {
                            "range": {
                                "sheetId": id_kpb,
                                "startRowIndex": 2,
                                "endRowIndex": 100,
                                "startColumnIndex": 6,
                                "endColumnIndex": 7
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_RANGE",
                                    "values": [{"userEnteredValue": "='QUAN_LY_DOI'!$B$2:$B$30"}]
                                },
                                "showCustomUi": True,
                                "strict": False
                            }
                        }
                    }
                ]
                
                sh.batch_update({"requests": requests})
                st.success("✅ Đã đổi thành công! Cột G giờ sẽ hiển thị đúng Tên đội (VHH, Nguyễn văn B, Đội KTV 003...)!")
            except Exception as e:
                st.error(f"Chi tiết lỗi: {e}")
