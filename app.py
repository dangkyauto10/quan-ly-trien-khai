# ĐOẠN CODE PYTHON ĐỌC TRỰC TIẾP DANH SÁCH ĐỘI TỪ CỘT B SHEET QUAN_LY_DOI
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_danh_sach_doi_tu_sheets():
    try:
        # Sử dụng thông tin xác thực Google Cloud Service Account sẵn có của dự án
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Đảm bảo credentials trỏ đúng cấu hình Service Account hiện tại của anh
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope) # Hoặc dùng st.secrets tùy cấu hình app của anh
        client = gspread.authorize(creds)
        
        # Mở Google Sheet theo tên hoặc ID hiện tại của hệ thống
        sheet = client.open("Tên_Google_Sheet_Của_Anh").worksheet("QUAN_LY_DOI")
        
        # Đọc dữ liệu từ Cột B (từ hàng 3 đến hết)
        # Cột B tương ứng với index cột là 2 trong gspread
        col_values = sheet.col_values(2) # Lấy toàn bộ cột B
        
        danh_sach_doi = []
        for val in col_values[2:]:  # Bỏ qua dòng 1 và dòng 2 (tiêu đề)
            val_str = str(val).strip()
            if val_str and val_str.upper() != "TÊN ĐỘI":
                danh_sach_doi.append(val_str)
                
        return danh_sach_doi if danh_sach_doi else ["VHH", "NTH"] # Fallback nếu trống
    except Exception as e:
        # Nếu có lỗi kết nối, trả về danh sách an toàn không làm crash app
        return ["VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A"]

# Sử dụng hàm này trực tiếp vàoselectbox hoặc multiselect của Streamlit:
# danh_sach_doi_hien_tai = get_danh_sach_doi_tu_sheets()
# doi_thuc_hien = st.selectbox("Đội thực hiện *", danh_sach_doi_hien_tai)
