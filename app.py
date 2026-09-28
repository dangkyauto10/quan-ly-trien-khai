# HÀM AN TOÀN ĐỌC DANH SÁCH ĐỘI TỪ CỘT B SHEET QUAN_LY_DOI (GIỮ NGUYÊN GIAO DIỆN GỐC)
@st.cache_data(ttl=10)
def lay_danh_sach_doi_tu_sheet_goc():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
            
        client = gspread.authorize(creds)
        spreadsheet = client.open("QUẢN LÝ DỰ ÁN - HỆ THỐNG ĐIỀU HÀNH")
        sheet = spreadsheet.worksheet("QUAN_LY_DOI")
        
        col_b_values = sheet.col_values(2)
        danh_sach = []
        for val in col_b_values[2:]:
            v = str(val).strip()
            if v and v.upper() != "TÊN ĐỘI":
                danh_sach.append(v)
                
        return danh_sach if danh_sach else ["VHH", "NTH"]
    except Exception as e:
        return ["VHH", "NTH", "Vinh Bắc Mê", "Nguyễn Văn A"]
