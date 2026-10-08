@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                # Tự động thay thế và khôi phục đúng định dạng xuống dòng PEM cho khóa bảo mật
                pk = creds_dict["private_key"]
                if "\\n" in pk:
                    pk = pk.replace("\\n", "\n")
                creds_dict["private_key"] = pk
                
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi xác thực Google Service Account: {e}")
    return None
