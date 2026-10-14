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
# CSS GIAO DIỆN CHUẨN (ĐÃ XÓA CÁC LỆNH GÂY LỖI NÚT)
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
    div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); }
    div[data-baseweb="select"] > div, input { border-radius: 10px !important; border: 1px solid #CBD5E1 !important; padding: 2px !important; }
    h5 { color: #1E293B; font-weight: 700; margin-top: 20px; margin-bottom: 15px; font-size: 16px; }
    .pending-card { border: 1px solid #E2E8F0; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #F8FAFC; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .map-btn {
        display: block; width: 100%; background-color: #10B981; color: white; text-align: center;
        padding: 12px 0; border-radius: 10px; font-weight: bold; text-decoration: none; margin-top: 5px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 15px;
    }
    .map-btn:active { background-color: #059669; }
    </style>
""", unsafe_allow_html=True)

SECURE_PASS = "880880"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwp2Pq3-PYNvHOWe4IQVm5PqeJd5TcIc_mPDtLm0BkDEGYUxq-C1cnV3rNS1X3xfI1p7w/exec"

# ==========================================
# HÀM NÉN ẢNH VÀ GỬI DỮ LIỆU
# ==========================================
def compress_image(uploaded_file, max_size=(1024, 1024), quality=60):
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        img.thumbnail(max_size)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality)
        return base64.b64encode(output.getvalue()).decode('utf-8')
    except Exception:
        return ""

def fetch_api_data():
    try:
        req = urllib.request.Request(APPS_SCRIPT_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_text = response.read().decode('utf-8')
            try:
                return json.loads(resp_text), None
            except json.JSONDecodeError:
                return None, "❌ LỖI API KHÔNG TRẢ VỀ JSON: Vui lòng kiểm tra quyền Deploy Apps Script."
    except Exception as e: 
        return None, f"❌ LỖI KẾT NỐI API: {str(e)}"

def submit_registration(ho_ten, s
