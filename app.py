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

st.title("⚙️ CẤU HÌNH TỰ ĐỘNG HỆ THỐNG")
st.write("Bấm nút bên dưới để hệ thống tự động thiết lập danh sách Dropdown và sửa toàn bộ lỗi trên Google Sheets.")

if st.button("🚀 BẮT ĐẦU CẤU HÌNH TRỰC TIẾP", type="primary"):
    if not sh:
        st.error("Chưa kết nối được với Google Sheets.")
    else:
        with st.spinner("Đang cấu hình trực tiếp vào Google Sheets..."):
            try:
                spreadsheet_id = sh.id
                
                # 1. Lấy sheetId của các trang tính
                ws_kpb = sh.worksheet("KHO_PHAN_BO")
                ws_da = sh.worksheet("DANH_SACH_DU_AN")
                ws_nk = sh.worksheet("NHAP_KHO")
                ws_doi = sh.worksheet("QUAN_LY_DOI")
                ws_diem = sh.worksheet("DANH_SACH_DIEM")
                
                id_kpb = ws_kpb.id
                id_da = ws_da.id
                id_nk = ws_nk.id
                id_doi = ws_doi.id
                id_diem = ws_diem.id

                # 2. Tạo yêu cầu Data Validation (Dropdown) qua Google Sheets API
                requests = [
                    # Dropdown Cột A: Mã dự án (lấy từ DANH_SACH_DU_AN!A2:A20)
                    {
                        "setDataValidation": {
                            "range": {"sheetId": id_kpb, "startRowIndex": 2, "endRowIndex": 100, "startColumnIndex": 0, "endColumnIndex": 1},
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_RANGE",
                                    "values": [{"userEnteredValue": f"='DANH_SACH_DU_AN'!$A$2:$A$20"}]
                                },
                                "showCustomUi": True,
                                "strict": False
                            }
                        }
                    },
                    # Dropdown Cột D: Tên thiết bị (lấy từ NHAP_KHO!C3:C50)
                    {
                        "setDataValidation": {
                            "range": {"sheetId": id_kpb, "startRowIndex": 2, "endRowIndex": 100, "startColumnIndex": 3, "endColumnIndex": 4},
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_RANGE",
                                    "values": [{"userEnteredValue": f"='NHAP_KHO'!$C$3:$C$50"}]
                                },
                                "showCustomUi": True,
                                "strict": False
                            }
                        }
                    },
                    # Dropdown Cột G: Đội nhận thiết bị (lấy từ QUAN_LY_DOI!A2:A30)
                    {
                        "setDataValidation": {
                            "range": {"sheetId": id_kpb, "startRowIndex": 2, "endRowIndex": 100, "startColumnIndex": 6, "endColumnIndex": 7},
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_RANGE",
                                    "values": [{"userEnteredValue": f"='QUAN_LY_DOI'!$A$2:$A$30"}]
                                },
                                "showCustomUi": True,
                                "strict": False
                            }
                        }
                    },
                    # Dropdown Cột H: Địa điểm vận chuyển (lấy từ DANH_SACH_DIEM!D3:D130)
                    {
                        "setDataValidation": {
                            "range": {"sheetId": id_kpb, "startRowIndex": 2, "endRowIndex": 100, "startColumnIndex": 7, "endColumnIndex": 8},
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_RANGE",
                                    "values": [{"userEnteredValue": f"='DANH_SACH_DIEM'!$D$3:$D$130"}]
                                },
                                "showCustomUi": True,
                                "strict": False
                            }
                        }
                    }
                ]
                
                # Gửi cấu hình trực tiếp vào bảng tính
                sh.batch_update({"requests": requests})
                
                st.success("✅ Đã thiết lập thành công 100% Dropdown cho các cột A, D, G, H trên Sheet KHO_PHAN_BO!")
            except Exception as e:
                st.error(f"Chi tiết lỗi: {e}")
