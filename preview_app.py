# QUAN LY DU AN — PREVIEW 2026-10-22
# Staged only: never deploy to production without user approval.
import io
import json
import base64
from pathlib import Path
import uuid
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlparse

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
from streamlit_geolocation import streamlit_geolocation
# The cookie component runs once on each page execution. Its browser-side
# cookie cache is populated asynchronously after the component has mounted.
from streamlit_cookies_controller import CookieController
from preview_remember import (
    COOKIE_NAME, VALID_SECONDS, issue_remember_token, verify_remember_token
)

from preview_registration import role_for_specialty, team_id_from_registration, matching_teams
from preview_approval_ui import render_pending_approvals
from preview_assignment import (
    assignment_rows, assignment_batch_requests, allowed_modes,
    eligible_site_tasks, project_site_catalog, site_assignment_plan, compact_site_assignment_requests
)
from preview_bulk_allocation import (
    inventory_by_sku, allocation_waiting_summary,
    build_plan, verify_plan, atomic_requests
)
from preview_bulk_excel import parse_exception_excel
from preview_allocation_groups import (
    match_contract_locations, read_contract_locations_excel, preview_basket
)
from preview_leadership import build_progress, display_amount
from preview_leader_access import leadership_username
from preview_team_access import resolve_login_username, friendly_account_name
from preview_team_access import normalized_name
from preview_credential_accounts import (
    team_accounts, visible_credential_state, next_account_id,
    new_password, create_hash, validate_custom_password
)
from preview_signup_credentials import registration_requests, pending_row
from preview_team_detach import (
    lost_registrations, revoked_team_ids, plan_detach,
    detach_requests, ACTIVE as LINK_ACTIVE
)
from preview_remember import account_fingerprint
from preview_handover import installer_handover, site_may_complete_installation
from preview_hub import hub_plan, received_by_site, signed_receipt_lines, qty_label, verify_vc_assignment
from preview_user_guide import GUIDE_URL, render_guide
from io import BytesIO
from openpyxl import Workbook as ExcelWorkbook
from preview_import_locations import (read_location_file, candidate_names,
    column_choice, is_header, normalize_name, blank_excel_template)

APP_ICON = Path(__file__).resolve().parent / "assets" / "tdv_icon_144.png"
# Use the approved TDV square logo for the tab favicon and app masthead.
st.set_page_config(
    page_title="QUẢN LÝ DỰ ÁN • PREVIEW",
    page_icon=str(APP_ICON),
    layout="centered"
)
APP_ICON_DATA = base64.b64encode(APP_ICON.read_bytes()).decode("ascii")

cookie_controller = CookieController(key="tdv_cookie_controller_v1")


def remember_signing_key():
    raw = st.secrets.get("remember_login_secret", "")
    return raw if isinstance(raw, str) and len(raw) >= 32 else None


def sync_remembered_login():
    """Handle a pending browser-cookie change before trying auto login."""
    action = st.session_state.pop("_remember_action", None)
    if action == "set":
        token = st.session_state.pop("_remember_token", "")
        if token:
            cookie_controller.set(
                COOKIE_NAME, token,
                max_age=VALID_SECONDS, expires=datetime.now() + timedelta(days=30),
                secure=True, same_site="strict")
    elif action == "remove":
        st.session_state.pop("_remember_token", None)
        if cookie_controller.get(COOKIE_NAME) is not None:
            cookie_controller.remove(COOKIE_NAME)

    if not st.session_state.get("auth") and action != "remove":
        key = remember_signing_key()
        cookie = cookie_controller.get(COOKIE_NAME)
        if key and cookie:
            accounts=effective_accounts()
            account = verify_remember_token(cookie, accounts, key)
            if account:
                account["_fp"]=account_fingerprint(accounts[account["username"]])
                st.session_state["auth"] = account



st.markdown("""
<style>
.block-container {
  max-width: 720px;
  padding: 2.1rem 1rem 3rem !important;
}
.tdv-hero {
  box-sizing: border-box;
  width: 100%;
  text-align: center;
  /* Reserve vertical room for Vietnamese accents on all devices.
     Streamlit may otherwise clip the top of a short HTML line. */
  padding: 1.05rem 0.25rem 1rem;
  margin: 0 auto 0.55rem;
  height: auto !important;
  min-height: 8.3rem;
  overflow: visible !important;
}
.tdv-hero-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #173A73;
  font-weight: 800;
  font-size: clamp(1.55rem, 4.5vw, 2rem);
  line-height: 1.5 !important;
  letter-spacing: -0.02em;
  white-space: normal;
  flex-wrap: wrap;
  min-height: 3.5rem;
  padding: 0.25rem 0;
  overflow: visible !important;
}
.tdv-hero-name {
  display: inline-block;
  line-height: 1.5 !important;
  padding: 0.12rem 0;
  overflow: visible !important;
}
.tdv-hero-icon {
  display: block;
  width: 3.15rem;
  height: 3.15rem;
  object-fit: contain;
  flex-shrink: 0;
  border-radius: 0.68rem;
}
.tdv-hero-subtitle {
  margin-top: 0.18rem;
  color: #64748b;
  font-size: 0.84rem;
  line-height: 1.6;
}
.tdv-preview-tag {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.22rem 0.7rem;
  border: 1px solid #dbe5f2;
  background: #f5f8fc;
  border-radius: 999px;
  color: #526581;
  font-size: 0.66rem;
  line-height: 1.5;
  letter-spacing: 0.02em;
}
@media (max-width: 600px) {
  .block-container {
    padding-top: 1.8rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
  }
  .tdv-hero {
    padding-top: 1rem;
    min-height: 8.3rem;
  }
  .tdv-hero-title {
    font-size: clamp(1.28rem, 5.8vw, 1.55rem);
    gap: 0.35rem;
    line-height: 1.55 !important;
    min-height: 3.35rem;
  }
  .tdv-hero-name {line-height: 1.55 !important;}
  .tdv-hero-icon {width: 2.65rem; height: 2.65rem;}
}
h2, h3 {color: #173A73;}
div[data-testid="stMetric"] {
  border: 1px solid #DFEAF5;
  background: #F2F7FC;
  border-radius: 14px;
  padding: 12px 14px;
}
div[data-testid="stForm"] {
  border: 1px solid #D9E5F2;
  border-radius: 16px;
  background: #F8FBFE;
  padding: 16px;
}
div.stButton > button, div.stLinkButton > a {
  border-radius: 11px;
  min-height: 43px;
  font-weight: 700;
}
div.stButton > button[kind="primary"] {
  background: #155EEF;
  color: white;
}
div[data-baseweb="select"] > div {border-radius: 10px;}
input {border-radius: 10px !important;}
/* TDV PREVIEW - TANG CO CHU DE DOC */
.tdv-hero-subtitle {
  font-size: 1.04rem !important;
}
.tdv-preview-tag {
  font-size: 0.95rem !important;
}
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp label {
  font-size: 1.1rem !important;
  line-height: 1.6 !important;
}
.stApp [data-testid="stCaptionContainer"] p {
  font-size: 1rem !important;
}
.stApp input,
.stApp textarea,
.stApp div[data-baseweb="select"] > div,
.stApp div.stButton > button {
  font-size: 1.1rem !important;
}
.stApp div.stButton > button {
  min-height: 48px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="tdv-hero">
  <div class="tdv-hero-title">
    <img class="tdv-hero-icon" src="data:image/png;base64,{APP_ICON_DATA}" alt="TDV" />
    <span class="tdv-hero-name">QUẢN LÝ DỰ ÁN</span>
  </div>
  <div class="tdv-hero-subtitle">Hệ thống điều hành hiện trường</div>
  <div class="tdv-preview-tag">BẢN THỬ NGHIỆM · CHƯA VẬN HÀNH</div>
</div>
""", unsafe_allow_html=True)


SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"]
READY = "Đã đồng bộ"

def now():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(timespec="seconds")

def sheet_datetime_serial():
    """Store a real Sheets date-time (Vietnam local time) for formatted columns."""
    local = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None, microsecond=0)
    return (local - datetime(1899, 12, 30)).total_seconds() / 86400

def fail(message):
    st.error(message)
    st.stop()

@st.cache_resource
def client():
    if "spreadsheet_id" not in st.secrets:
        raise RuntimeError("Thiếu spreadsheet_id trong Streamlit Secrets.")
    # Support the original JSON file pasted as a literal TOML multiline value.
    if "gcp_service_account_json" in st.secrets:
        info = json.loads(st.secrets["gcp_service_account_json"])
    elif "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
    else:
        raise RuntimeError("Thiếu gcp_service_account_json trong Streamlit Secrets.")
    cred = Credentials.from_service_account_info(info, scopes=SHEETS_SCOPE)
    sh = gspread.authorize(cred).open_by_key(st.secrets["spreadsheet_id"])
    return sh, cred

@st.cache_data(ttl=15, show_spinner=False)
def read_sheet(name):
    sh, _ = client()
    values = sh.worksheet(name).get_all_values()
    if not values:
        return []
    headers = values[0]
    return [
        dict(zip(headers, row + [""] * (len(headers) - len(row))), _row=i)
        for i, row in enumerate(values[1:], 2) if any(str(x).strip() for x in row)
    ]

def sheet(name):
    return client()[0].worksheet(name)

def append(name, values):
    sheet(name).append_row([str(v) if v is not None else "" for v in values],
                           value_input_option="RAW")
    read_sheet.clear()

def audit(actor, action, target, target_id, result, detail=""):
    try:
        append("NHAT_KY_HE_THONG",
               [now(), actor, st.session_state.get("auth", {}).get("role", "VISITOR"),
                action, target, target_id, result, detail])
    except Exception:
        pass

def lookup(rows, key_field, key):
    return next((r for r in rows if r.get(key_field, "") == key), None)

def pbkdf(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"),
                              bytes.fromhex(salt), 390000).hex()

@st.cache_resource
def login_blocks():
    return {}


def effective_accounts():
    """Privileged credentials from Secrets only; team credentials from Sheet.

    Invalid/missing sheet fails CLOSED for sheet-backed team users,
    while existing ADMIN Secrets login remains available for recovery.
    """
    secrets_accounts = st.secrets.get("accounts", {})
    try:
        rows=read_sheet("QUAN_LY_DOI")
        accounts=team_accounts(secrets_accounts,
                               read_sheet("TAI_KHOAN_DOI"),rows)
        # Fail closed immediately for an externally deleted registration,
        # even before ADMIN reconciles site and account references.
        denied=revoked_team_ids(
            read_sheet("DANG_KY_THANH_VIEN"),
            read_sheet("LIEN_KET_DANG_KY_DOI"))
        return {name:info for name,info in accounts.items() if not (
            str(info.get("role","")).upper()=="DOI_TRUONG"
            and str(info.get("team_id","")) in denied)}
    except Exception:
        # Credential/source outage must never expose a deleted captain.
        # Keep privileged accounts in Secrets available for recovery.
        return {name:info for name,info in secrets_accounts.items()
                if str(info.get("role","")).upper() in ("ADMIN","LANH_DAO")}


def valid_login(username, pin):
    accounts = effective_accounts()
    info = accounts.get(username)
    if not info:
        return None
    locks = login_blocks()
    record = locks.get(username, {"count": 0, "until": 0})
    if record["until"] > time.time():
        return None
    try:
        valid = hmac.compare_digest(pbkdf(pin, info["salt"]), info["hash"])
    except (KeyError, ValueError):
        return None
    if valid:
        locks.pop(username, None)
        return {"username": username, "role": str(info["role"]).upper(),
                "team_id": str(info.get("team_id", "")),
                "_fp": account_fingerprint(info)}
    count = record["count"] + 1
    locks[username] = {"count": count, "until": time.time() + 900 if count >= 5 else 0}
    return None

def leadership_login():
    """One-button entry for a dedicated read-only leadership identity."""
    st.subheader("📊 LÃNH ĐẠO – XEM BÁO CÁO")
    st.caption("Chỉ cần nhập mật khẩu để xem tiến độ. "
               "Không cần mã tài khoản hoặc chọn chức năng.")
    if st.button("← Trở về trang chính",key="leader_login_back"):
        st.session_state["leader_login_open"] = False
        st.rerun()
    username = leadership_username(
        st.secrets.get("accounts", {}),
        st.secrets.get("leader_login_username", "")
    )
    if not username:
        st.warning("Chưa cấu hình tài khoản riêng cho LÃNH ĐẠO. "
                   "ADMIN cần tạo tài khoản vai trò LANH_DAO trong Secrets. "
                   "Không dùng chung tài khoản ADMIN.")
        return
    key = remember_signing_key()
    with st.form("leader_password_only",clear_on_submit=True):
        password = st.text_input("Mật khẩu Lãnh đạo",
                                  type="password")
        remember = st.checkbox(
            "Ghi nhớ đăng nhập trên thiết bị này (30 ngày)",
            value=False,disabled=not bool(key),
            help="Chỉ tích trên điện thoại hoặc máy tính cá nhân, không "
                 "sử dụng ở thiết bị công cộng hoặc dùng chung."
        )
        if not key:
            st.caption("Cần ADMIN cấu hình remember_login_secret "
                       "để sử dụng ghi nhớ đăng nhập.")
        submitted=st.form_submit_button("🔓 XEM BÁO CÁO",
                                        use_container_width=True)
    if not submitted:
        return
    account=valid_login(username,password)
    if not account or account.get("role")!="LANH_DAO":
        st.error("Mật khẩu không đúng hoặc tài khoản đang tạm khóa.")
        return
    # No password or PIN is written into browser cookies or session state.
    st.session_state["auth"]=account
    st.session_state["leader_login_open"]=False
    if remember and key:
        info=st.secrets["accounts"][username]
        st.session_state["_remember_token"]=issue_remember_token(
            username,info,key)
        st.session_state["_remember_action"]="set"
    else:
        st.session_state["_remember_action"]="remove"
    st.rerun()


# Stable PREVIEW URL for staff home-screen shortcuts (no production changes).
PREVIEW_HOME_URL = (
    "https://quan-ly-trien-khai-qfzumkrq7escxbxpv9v9tr.streamlit.app"
)


def home_screen_guide(expanded=False):
    """One-time device-owner shortcut setup; no silent install is possible."""
    with st.expander("📲 ĐƯA APP RA MÀN HÌNH ĐIỆN THOẠI",expanded=expanded):
        st.write("**Lưu biểu tượng QUẢN LÝ DỰ ÁN để mở app chỉ bằng một lần chạm.** "
                 "Không cần quay lại Zalo tìm link. Việc tạo biểu tượng do "
                 "chính chủ điện thoại xác nhận một lần.")
        st.caption("Nếu đang xem link trong Zalo hoặc Facebook, hãy chọn "
                   "Mở bằng trình duyệt / Mở trong Safari hoặc Chrome trước.")
        ios,android=st.tabs(["🍎 iPhone","🤖 Android"])
        with ios:
            st.markdown(
                "**①** Nếu mở trong Zalo, chọn **Mở bằng trình duyệt → Safari**.\n\n"
                "**②** Trong Safari: **Chia sẻ ⬆️ → Thêm vào Màn hình chính "
                "→ Thêm**. Bật *Mở dưới dạng ứng dụng web* nếu có."
            )
        with android:
            st.markdown(
                "**①** Nếu mở trong Zalo, chọn **Mở bằng trình duyệt → Chrome**.\n\n"
                "**②** Trong Chrome: **⋮ → Cài đặt và tạo lối tắt** "
                "(hoặc **Thêm vào màn hình chính**) **→ Thêm**."
            )
        st.info("Biểu tượng giúp mở app ngay từ màn hình điện thoại. "
                "Mật khẩu tự đặt khi đăng ký chỉ dùng được **sau khi "
                "ADMIN duyệt**; có thể chọn ghi nhớ đăng nhập 30 ngày "
                "trên thiết bị cá nhân.")
        st.caption("B đã cập nhật logo TV vàng cam làm favicon của PREVIEW. "
                   "Biểu tượng khi ghim lên iPhone/Android vẫn phụ thuộc "
                   "trình duyệt và Streamlit Cloud; nếu đã ghim icon cũ, "
                   "cần xóa lối tắt cũ và tạo lại để kiểm tra.")


def login(team_only=False):
    """Name-first team login or regular ADMIN login. PIN is always required."""
    if team_only:
        st.subheader("👷 ĐỘI TRƯỞNG – BÁO CÁO")
        st.caption("Nhập họ tên đã đăng ký và mật khẩu riêng. "
                   "Không cần biết mã đội hay mã tài khoản.")
        if st.button("← Trở về trang chính",key="team_login_back"):
            st.session_state["team_login_open"]=False
            st.rerun()
    with st.form("team_login_form" if team_only else "login_form_preview"):
        typed=st.text_input(
            "Họ và tên đội trưởng" if team_only else
            "Họ tên đội trưởng hoặc mã tài khoản ADMIN",
            placeholder="Ví dụ: Nguyễn Văn A" if team_only else "")
        pin=st.text_input("Mật khẩu riêng",type="password")
        remember_key=remember_signing_key()
        remember=st.checkbox(
            "Ghi nhớ đăng nhập trên thiết bị này (30 ngày)",
            value=False,disabled=not bool(remember_key),
            help="Chỉ chọn trên điện thoại hoặc máy tính cá nhân; "
                 "không chọn trên thiết bị dùng chung.")
        if remember_key is None:
            st.caption("Ghi nhớ đăng nhập chỉ có khi ADMIN đã cấu hình khóa "
                       "ký phiên remember_login_secret trong Secrets.")
        submitted=st.form_submit_button(
            "✅ VÀO BÁO CÁO" if team_only else "ĐĂNG NHẬP",
            use_container_width=True)
    if not submitted:
        return
    accounts=effective_accounts()
    username,reason=resolve_login_username(
        typed,accounts,read_sheet("QUAN_LY_DOI"))
    if reason=="ambiguous":
        st.error("Có nhiều hồ sơ trùng tên hoặc thông tin không nhất quán. "
                 "Nhờ ADMIN kiểm tra, không đăng nhập nhầm tài khoản.")
        return
    if not username:
        st.error("Họ tên hoặc tài khoản chưa được cấp quyền, hoặc thông tin "
                 "đăng nhập không hợp lệ. Vui lòng liên hệ ADMIN.")
        return
    if team_only and str(accounts[username].get("role","")).upper()!="DOI_TRUONG":
        st.error("Chỉ tài khoản đội trưởng được dùng nút này.")
        return
    user=valid_login(username,pin)
    if not user or (team_only and user["role"]!="DOI_TRUONG"):
        st.error("Mật khẩu không đúng hoặc tài khoản tạm khóa.")
        return
    st.session_state["auth"]=user
    st.session_state["team_login_open"]=False
    if remember and remember_key:
        account=accounts[user["username"]]
        st.session_state["_remember_token"]=issue_remember_token(
            user["username"],account,remember_key)
        st.session_state["_remember_action"]="set"
    else:
        st.session_state["_remember_action"]="remove"
    st.rerun()


def auth():
    a = st.session_state.get("auth")
    if not a:
        return None
    cur = effective_accounts().get(a.get("username"))
    if (not cur or str(cur.get("role","")).upper() != a.get("role")
            or str(cur.get("team_id","")) != a.get("team_id")
            or a.get("_fp") != account_fingerprint(cur)):
        st.session_state.pop("auth",None)
        return None
    if a["role"]=="DOI_TRUONG":
        match=[t for t in read_sheet("QUAN_LY_DOI")
               if t.get("Mã đội")==a.get("team_id") and
               t.get("Trạng thái")=="Hoạt động"]
        if len(match)!=1:
            st.session_state.pop("auth",None)
            return None
    return a

def require_role(*roles):
    a = auth()
    if not a or a["role"] not in roles:
        fail("Tài khoản không có quyền sử dụng chức năng này.")
    return a

def menu():
    sync_remembered_login()
    a = auth()
    if a and a.get("role")=="ADMIN":
        # ADMIN opens/refreshes the app: detect new registrations deleted
        # directly in Sheets, then revoke associated team and pending tasks.
        reconcile_deleted_captains()
    if not a:
        if st.session_state.get("leader_login_open"):
            return "__LEADERSHIP_LOGIN__"
        if st.session_state.get("team_login_open"):
            return "__TEAM_LOGIN__"
        if st.button("📊 LÃNH ĐẠO – XEM BÁO CÁO",
                     type="primary",use_container_width=True,
                     key="leader_entry_button"):
            st.session_state["leader_login_open"]=True
            st.rerun()
        if st.button("👷 ĐỘI TRƯỞNG – BÁO CÁO",
                     use_container_width=True,key="team_entry_button"):
            st.session_state["team_login_open"]=True
            st.rerun()
        if not st.session_state.get("registered_notice"):
            home_screen_guide(expanded=False)
        opts = ["🔐 Đăng nhập ADMIN / tài khoản khác",
                "📝 Đăng ký tham gia"]
    elif a["role"] == "ADMIN":
        opts = ["📊 Báo cáo tiến độ", "📁 Dự án/Điểm/Nhập kho", "📦 Phân bổ",
                "👥 Đăng ký & quản lý đội", "📦 Bàn giao tập kết",
                "📝 Đăng ký hộ đội trưởng", "📋 Báo cáo nhiệm vụ",
                "🗺️ Tìm đường"]
    elif a["role"] == "LANH_DAO":
        # Executive landing is always the read-only progress view.
        st.caption("📊 LÃNH ĐẠO • Chế độ chỉ xem")
        if st.button("🚪 ĐĂNG XUẤT",use_container_width=True,
                     key="leader_logout"):
            st.session_state.pop("auth",None)
            st.session_state["leader_login_open"]=False
            st.session_state["_remember_action"]="remove"
            st.rerun()
        return "📊 Báo cáo tiến độ"
    elif a["role"] == "DOI_TRUONG":
        opts = ["📋 Báo cáo nhiệm vụ", "🗺️ Tìm đường"]
    else:
        opts = ["🗺️ Tìm đường"]
    if a:
        name=friendly_account_name(a,read_sheet("QUAN_LY_DOI")) if a["role"]=="DOI_TRUONG" else a["username"]
        st.caption(f"Đã đăng nhập: {name} • {a['role']}")
        if st.button("Đăng xuất"):
            st.session_state.pop("auth", None)
            st.session_state["_remember_action"] = "remove"
            st.rerun()
    if a and a["role"] == "ADMIN":
        pending_count=sum(x.get("Trạng thái duyệt")=="Chờ duyệt"
                          for x in read_sheet("DANG_KY_THANH_VIEN"))
        if pending_count:
            st.info(f"📩 Có {pending_count} hồ sơ đội trưởng CHỜ DUYỆT.")
            if st.button("📩 MỞ DANH SÁCH CHỜ DUYỆT", use_container_width=True):
                st.session_state["preview_menu"] = "👥 Đăng ký & quản lý đội"
                st.rerun()
    # Navigation requests are applied before widget construction on the
    # next run; writing to a rendered selectbox's key is not permitted.
    destination=st.session_state.pop("_next_menu",None)
    if destination in opts:
        st.session_state["preview_menu"]=destination
    project_to_assign=st.session_state.pop("_next_assignment_project",None)
    if project_to_assign and destination=="👥 Đăng ký & quản lý đội":
        st.session_state["site_assign_project"]=project_to_assign
    return st.selectbox("CHỌN CHỨC NĂNG", opts, key="preview_menu")

def register(on_behalf=False):
    """Public registration and Admin-assisted registration use the same pending queue."""
    acting_admin = require_role("ADMIN") if on_behalf else None
    st.subheader("📝 " + ("ADMIN đăng ký hộ đội trưởng" if on_behalf else "Đội trưởng đăng ký tham gia dự án"))
    st.caption("Khai khu vực đã hợp đồng với công ty. Đây là thông tin đăng ký, "
               "không tự cấp quyền báo cáo; ADMIN sẽ xét duyệt và giao nhiệm vụ.")
    saved_notice = st.session_state.pop("registered_notice", None)
    if saved_notice:
        st.success(saved_notice)
        if not on_behalf:
            st.link_button("📖 XEM HƯỚNG DẪN & THỰC HÀNH THỬ",
                           GUIDE_URL,use_container_width=True)
            home_screen_guide(expanded=True)
    projects = [p for p in read_sheet("DANH_SACH_DU_AN")
                if p.get("Mã dự án") and p.get("Tên dự án")]
    if not projects:
        st.info("Chưa có dự án mở đăng ký. Vui lòng liên hệ ADMIN.")
        return
    options = [p["Mã dự án"] for p in projects]
    project_names = {p["Mã dự án"]: p["Tên dự án"] for p in projects}
    points = read_sheet("DANH_SACH_DIEM")
    revision = st.session_state.get("registration_form_revision", 0)
    # Project selector stays OUTSIDE the form: changing project must immediately
    # refresh the valid list of locations, never silently retain another project.
    project = st.selectbox("Dự án đăng ký *", options,
        format_func=lambda key: f"{key} — {project_names[key]}",
        key=f"register_project_{'admin' if on_behalf else 'public'}")
    with st.form(f"registration_{'admin' if on_behalf else 'public'}_{revision}"):
        full_name = st.text_input("Họ và tên *", max_chars=120)
        phone = st.text_input("Điện thoại liên hệ (Zalo) *", max_chars=20)
        area_options = sorted({
            p["Tên xã/phường/đơn vị"] for p in points
            if p.get("Mã dự án") == project and p.get("Tên xã/phường/đơn vị")
        })
        area = st.multiselect("Khu vực đã hợp đồng (chọn nhiều nếu cần)",
                              area_options, key=f"register_areas_{project}_{revision}")
        area_other = st.text_area("Khu vực theo hợp đồng cần ghi bổ sung",
            placeholder="Gõ địa bàn, xã/phường hoặc đơn vị chưa có trong danh sách...",
            max_chars=1200, height=84)
        specialty = st.selectbox("Chuyên môn / Nhiệm vụ *",
            ["Vận chuyển / Giao nhận", "KTV lắp đặt",
             "Vận chuyển & Lắp đặt", "Điều phối / Giám sát", "Kho vận / Hậu cứ"])
        vehicle = st.selectbox("Phương tiện", ["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        if not on_behalf:
            st.markdown("#### 🔐 Tự đặt mật khẩu đăng nhập")
            st.caption("V tự chọn mật khẩu dễ nhớ, **từ 10 ký tự có chữ và số**, "
                       "ví dụ một cụm từ riêng có số (không dùng ví dụ chung). "
                       "Không dùng họ tên, số điện thoại, ngày sinh hay "
                       "mật khẩu Zalo. Chỉ lưu mã băm; "
                       "ADMIN duyệt xong mới đăng nhập được.")
            desired_password=st.text_input(
                "Mật khẩu tự chọn *",type="password",max_chars=128)
            confirm_password=st.text_input(
                "Nhập lại mật khẩu *",type="password",max_chars=128)
        st.caption("Khu vực tự khai chỉ để ADMIN tham khảo khi phân công. "
                   "Chỉ điểm được giao chính thức mới có thể báo cáo.")
        if st.form_submit_button("GỬI ĐĂNG KÝ" if not on_behalf else
                                 "GỬI HỒ SƠ ĐĂNG KÝ HỘ", use_container_width=True):
            normalized_phone = "".join(c for c in phone if c.isdigit())
            described_areas = ", ".join(area + ([area_other.strip()] if area_other.strip() else []))
            if len(full_name.strip()) < 3 or len(normalized_phone) not in (9,10,11):
                st.error("Vui lòng kiểm tra họ tên và số điện thoại (9–11 chữ số).")
            elif not on_behalf and desired_password!=confirm_password:
                st.error("Hai lần nhập mật khẩu chưa giống nhau.")
            elif not on_behalf and validate_custom_password(
                    desired_password,full_name,normalized_phone):
                st.error(validate_custom_password(
                    desired_password,full_name,normalized_phone))
            elif not described_areas:
                st.error("Hãy chọn hoặc ghi ít nhất một khu vực đã hợp đồng.")
            elif project not in [p["Mã dự án"] for p in read_sheet("DANH_SACH_DU_AN")]:
                st.error("Dự án không còn tồn tại, vui lòng kiểm tra lại.")
            else:
                existing = read_sheet("DANG_KY_THANH_VIEN")
                same = [row for row in existing
                    if row.get("Mã dự án đăng ký") == project
                    and "".join(c for c in row.get("Số điện thoại","") if c.isdigit()) == normalized_phone
                    and " ".join(row.get("Họ tên","").casefold().split()) ==
                        " ".join(full_name.casefold().split())
                    and row.get("Trạng thái duyệt") in ("Chờ duyệt", "Đã duyệt")]
                if same:
                    st.warning("Hồ sơ này đã đăng ký trước đó. "
                               "Không được đăng ký lại để đổi mật khẩu. "
                               "Nếu muốn đổi mật khẩu tự chọn hoặc hồ sơ cũ "
                               "chưa có mật khẩu, hãy nhờ ADMIN vào mục "
                               "CẤP / ĐẶT LẠI MẬT KHẨU ĐỘI TRƯỞNG "
                               "và nhập mật khẩu theo đề nghị.")
                else:
                    rid = "DK-" + uuid.uuid4().hex[:12].upper()
                    submitter = ("ADMIN:" + acting_admin["username"]) if acting_admin else "Tự đăng ký"
                    try:
                        date_serial = sheet_datetime_serial()
                        registration=[rid, date_serial, full_name.strip(),
                                      normalized_phone,described_areas,
                                      specialty,vehicle,"Chờ duyệt",
                                      "","","",project,submitter]
                        if on_behalf:
                            sheet("DANG_KY_THANH_VIEN").append_row(
                                registration,value_input_option="RAW")
                            notice="ADMIN cần cấp mật khẩu riêng sau khi duyệt."
                        else:
                            pending=pending_row(rid,project,desired_password,now())
                            # One atomic Sheets request: no registration without
                            # its corresponding salted password hash.
                            batch=registration_requests(
                                sheet("DANG_KY_THANH_VIEN").id,
                                sheet("MAT_KHAU_DANG_KY").id,
                                registration,pending)
                            client()[0].batch_update({"requests":batch})
                            notice=("Mật khẩu đã được lưu an toàn dưới dạng mã "
                                    "băm. Chỉ đăng nhập được sau khi ADMIN duyệt.")
                        read_sheet.clear()
                        st.session_state["registered_notice"] = (
                            f"Đã nhận hồ sơ {rid} — đang chờ ADMIN duyệt. "+notice)
                        st.session_state["registration_form_revision"] = revision + 1
                        st.rerun()
                    except Exception as e:
                        st.error("Chưa xác nhận gửi hồ sơ thành công (" +
                                 type(e).__name__ +
                                 "). Hãy nhờ ADMIN kiểm tra danh sách trước khi gửi lại.")

def directions():
    st.subheader("🗺️ Tìm địa điểm – Dẫn đường")
    points = [r for r in read_sheet("DANH_SACH_DIEM") if r.get("Mã điểm") and r.get("Tên xã/phường/đơn vị")]
    if not points:
        st.info("Admin chưa tạo danh sách địa điểm.")
        return
    options = {f"{p['Tên xã/phường/đơn vị']} • {p['Mã điểm']}": p for p in points}
    selected = st.selectbox("Gõ tên xã, phường hoặc đơn vị cần đến", list(options))
    p = options[selected]
    st.caption(p.get("Địa chỉ chi tiết") or p.get("Tỉnh/Thành") or "")
    st.info("Có thể cho phép GPS để dùng vị trí đang đứng, hoặc để Google Maps tự xác định điểm xuất phát.")
    loc = streamlit_geolocation()
    lat = loc.get("latitude") if isinstance(loc, dict) else None
    lon = loc.get("longitude") if isinstance(loc, dict) else None
    destination = ((p.get("Vĩ độ") + "," + p.get("Kinh độ"))
                   if p.get("Vĩ độ") and p.get("Kinh độ")
                   else ", ".join(filter(None, [p["Tên xã/phường/đơn vị"],
                                                 p.get("Địa chỉ chi tiết"), p.get("Tỉnh/Thành")])))
    url = "https://www.google.com/maps/dir/?api=1&destination=" + quote(destination)
    if lat is not None and lon is not None:
        url += "&origin=" + quote(f"{lat},{lon}")
    if not (p.get("Vĩ độ") and p.get("Kinh độ")):
        st.warning("Điểm này chưa có GPS đã xác minh. Google Maps sẽ tìm "
                   "theo tên/địa chỉ; hãy chọn đúng vị trí đích trên bản đồ "
                   "trước khi bắt đầu chỉ đường.")
    st.link_button("🧭 MỞ GOOGLE MAPS CHỈ ĐƯỜNG", url, use_container_width=True)
    st.caption("Tìm đường không cấp quyền báo cáo nhiệm vụ.")


def bulk_import_locations():
    """Admin-only, review-before-write import of a project location list."""
    require_role("ADMIN")
    st.markdown("#### 📥 Nạp danh sách xã, đơn vị, địa điểm")
    st.caption("Dữ liệu chỉ nhập vào dự án đã chọn. Không xóa hoặc ghi đè các điểm đã có.")
    projects = [r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN") if r.get("Mã dự án")]
    if not projects:
        st.info("Admin cần tạo dự án trước khi nhập danh sách.")
        return
    project = st.selectbox("Dự án cần nhập danh sách *", projects, key="bulk_location_project")
    st.download_button("⬇️ Tải mẫu Excel (1 cột tên địa điểm)",
        data=blank_excel_template(),
        file_name="MAU_DANH_SACH_DIEM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_location_template")
    upload = st.file_uploader("Tải Word (.docx) hoặc Excel (.xlsx), tối đa 5 MB",
        type=["docx", "xlsx"], key="upload_bulk_locations")
    if upload is None:
        return
    try:
        sources = read_location_file(upload.name, upload.getvalue())
    except Exception as exc:
        st.error("Không đọc được danh sách: " + str(exc))
        return
    if not sources:
        st.warning("Tệp không có dòng dữ liệu hợp lệ.")
        return
    chosen_sheet = st.selectbox("Trang chứa danh sách", list(sources),
                                key="bulk_location_source_sheet")
    rows = sources[chosen_sheet]
    number_of_cols = min(24, max((len(row) for row in rows), default=1))
    preferred_col = min(column_choice(rows), number_of_cols - 1)
    cols = list(range(number_of_cols))
    selected_col = st.selectbox("Cột chứa tên xã/phường/đơn vị", cols,
        index=preferred_col, key="bulk_location_column",
        format_func=lambda idx: f"Cột {idx+1} • " +
        ", ".join(str(r[idx])[:48] for r in rows[:4] if len(r)>idx and r[idx])[:125])
    first_is_header = bool(rows and len(rows[0]) > selected_col and is_header(rows[0][selected_col]))
    skip_header = st.checkbox("Bỏ qua dòng đầu (dòng tiêu đề)",
                              value=first_is_header, key="bulk_location_skip_header")
    names = candidate_names(rows, selected_col, skip_header)
    seen, unique = set(), []
    duplicate_inside = 0
    for name in names:
        norm = normalize_name(name)
        if norm in seen:
            duplicate_inside += 1
        else:
            seen.add(norm)
            unique.append(name)
    prior = [r for r in read_sheet("DANH_SACH_DIEM") if r.get("Mã dự án") == project]
    oldnames = {normalize_name(r.get("Tên xã/phường/đơn vị")) for r in prior}
    to_add = [name for name in unique if normalize_name(name) not in oldnames]
    st.write(f"**Đọc được:** {len(names)} dòng  •  **Trùng trong tệp:** {duplicate_inside}"
             f"  •  **Đã có trong dự án:** {len(unique)-len(to_add)}"
             f"  •  **Dự kiến thêm:** {len(to_add)}")
    if to_add:
        st.dataframe([{"STT":i, "Tên xã/phường/đơn vị":name}
                      for i,name in enumerate(to_add[:100],1)],
                     hide_index=True, use_container_width=True)
        if len(to_add)>100:
            st.caption("Đang hiển thị 100 tên đầu tiên; khi xác nhận sẽ nhập cả danh sách.")
    else:
        st.info("Không có địa điểm mới để thêm.")
        return
    st.warning("Vui lòng kiểm tra cột, tên địa điểm và dự án trước khi nạp.")
    if st.button(f"✅ XÁC NHẬN NẠP {len(to_add)} ĐỊA ĐIỂM",
                 type="primary", use_container_width=True,
                 key="confirm_bulk_locations", disabled=len(to_add)>1000):
        # Recheck project and duplicates immediately before committing.
        if project not in {r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")}:
            st.error("Dự án không còn tồn tại; không ghi dữ liệu.")
            return
        latest = [r for r in read_sheet("DANH_SACH_DIEM") if r.get("Mã dự án") == project]
        already = {normalize_name(r.get("Tên xã/phường/đơn vị")) for r in latest}
        final = [name for name in to_add if normalize_name(name) not in already]
        if not final:
            st.info("Danh sách này đã được nạp trước đó, không tạo bản ghi trùng.")
            return
        payload = []
        for name in final:
            point_id = "DD-" + uuid.uuid4().hex[:12].upper()
            # Coordinates must be verified by Admin before relying on navigation.
            payload.append([point_id, project, name, "", "", "", "", "", "",
                            "Hoạt động", "Nhập từ " + upload.name[:80]])
        try:
            sheet("DANH_SACH_DIEM").append_rows(payload, value_input_option="RAW")
            read_sheet.clear()
            audit(auth()["username"], "NHẬP ĐỊA ĐIỂM", "DANH_SACH_DIEM", project,
                  "OK", f"{len(final)} điểm từ tệp {upload.name[:80]}")
            st.success(f"Đã thêm {len(final)} địa điểm vào dự án {project}. "
                       "Điểm trùng được giữ nguyên, không ghi đè.")
            st.info("✅ Danh sách đã nạp thành công. Chưa có tọa độ GPS "
                    "không ảnh hưởng đến nhập kho, PHÂN BỔ hay GÁN ĐỘI. "
                    "Khi cần dẫn đường, Google Maps có thể tìm theo tên điểm "
                    "nhưng ADMIN/đội trưởng phải kiểm tra đúng vị trí trước "
                    "khi đi; không tự coi kết quả tìm tên là tọa độ xác nhận.")
        except Exception as exc:
            read_sheet.clear()
            st.error("Chưa thể xác nhận nhập danh sách thành công (" +
                     type(exc).__name__ + "). Hãy kiểm tra Google Sheets trước khi thử lại.")

def projects_and_inventory():
    require_role("ADMIN")
    st.subheader("📁 Danh mục do Admin quản lý")
    choice = st.radio("Thao tác quản lý", ["Dự án", "Địa điểm", "Hàng nhập kho", "Nạp danh sách địa điểm"], horizontal=False)
    if choice == "Nạp danh sách địa điểm":
        bulk_import_locations()
        return
    projects = read_sheet("DANH_SACH_DU_AN")
    ids = [x.get("Mã dự án") for x in projects if x.get("Mã dự án")]
    # This selector MUST remain OUTSIDE clear_on_submit form.
    # Otherwise after every receipt it silently reverts to first project.
    project = None
    if choice in ("Địa điểm", "Hàng nhập kho"):
        if not ids:
            st.warning("Chưa có dự án. Hãy tạo dự án trước.")
            return
        project = st.selectbox(
            "📁 Dự án đang nhập (giữ nguyên sau mỗi lần lưu)",
            ids, key="master_sticky_project")
        st.caption(f"Đang ghi dữ liệu vào dự án: {project}. "
                   "Khi nhập phiếu mới, kiểm tra mã dự án trước khi bấm LƯU.")
    with st.form("new_master", clear_on_submit=True):
        if choice == "Dự án":
            code = st.text_input("Mã dự án")
            name = st.text_input("Tên dự án")
            deadline = st.date_input("Hạn hoàn thành")
        elif choice == "Địa điểm":
            code = st.text_input("Mã điểm duy nhất")
            name = st.text_input("Tên xã/phường/đơn vị")
            address = st.text_input("Địa chỉ chi tiết")
            province = st.text_input("Tỉnh/Thành")
            route = st.text_input("Tuyến/Khu vực")
            latitude = st.text_input("Vĩ độ (nếu có)")
            longitude = st.text_input("Kinh độ (nếu có)")
        else:
            sku = st.text_input("SKU")
            name = st.text_input("Tên hàng hóa")
            unit = st.text_input("ĐVT")
            quantity = st.number_input("Số lượng THỰC NHẬN", min_value=0.0, step=1.0)
        if st.form_submit_button("LƯU", use_container_width=True):
            try:
                if choice == "Dự án":
                    if not code or not name or code in ids:
                        fail("Trùng hoặc thiếu mã dự án/tên dự án.")
                    append("DANH_SACH_DU_AN",[code,name,now()[:10],deadline.isoformat(),"Đang triển khai",auth()["username"],""])
                elif choice == "Địa điểm":
                    if not code or not name or lookup(read_sheet("DANH_SACH_DIEM"),"Mã điểm",code):
                        fail("Trùng hoặc thiếu mã điểm/tên điểm.")
                    url="https://www.google.com/maps/search/?api=1&query="+quote(", ".join(filter(None,[name,address,province])))
                    append("DANH_SACH_DIEM",[code,project,name,address,province,route,latitude,longitude,url,"Hoạt động",""])
                else:
                    if not sku or not name or not unit or quantity <= 0:
                        fail("Thiếu thông tin hoặc SLHH không hợp lệ.")
                    append("NHAP_KHO",["NK-"+uuid.uuid4().hex[:12].upper(),project,now(),sku,name,unit,quantity,"",auth()["username"],""])
                audit(auth()["username"],"THÊM DANH MỤC",choice,code if choice != "Hàng nhập kho" else sku,"OK")
                read_sheet.clear()
                st.success("Đã lưu vào Google Sheets Preview.")
            except Exception as e:
                st.error(f"Lưu thất bại: {type(e).__name__}")
    if choice == "Hàng nhập kho":
        st.markdown("#### 📦 Hàng còn chờ phân bổ theo SKU")
        st.caption("Tổng thực nhập qua nhiều đợt trừ tổng đã phân bổ cho "
                   "địa điểm. Đây KHÔNG phải tồn vật lý sau xuất kho.")
        records,problems = allocation_waiting_summary(
            project,read_sheet("NHAP_KHO"),read_sheet("KHO_PHAN_BO"))
        if problems:
            for problem in problems[:8]:
                st.error(problem)
            st.warning("Dữ liệu kho có lỗi; cần đối soát trước khi phân bổ.")
        elif records:
            st.dataframe(records,hide_index=True,use_container_width=True)
            if all(row["Hàng còn chờ phân bổ"] == 0 for row in records):
                st.success("Toàn bộ hàng đã nhập của dự án đã được phân bổ hết "
                           "(còn chờ phân bổ = 0 cho mọi SKU).")
        else:
            st.info("Dự án chưa nhập hàng. Khi có phiếu nhập, "
                    "tổng hàng và số còn chờ phân bổ sẽ hiển thị tại đây.")

def read_sheet_live(name):
    """Bypass Streamlit's short cache for the final stock/duplicate check."""
    values = sheet(name).get_all_values()
    if not values:
        return []
    headers = values[0]
    return [dict(zip(headers, row + [""] * (len(headers)-len(row))), _row=i)
            for i, row in enumerate(values[1:], 2) if any(str(x).strip() for x in row)]


def reconcile_deleted_captains():
    """ADMIN-triggered automatic cleanup of externally deleted profiles.

    No background Google Sheets trigger exists: runs when logged-in ADMIN
    opens or refreshes the PREVIEW app, without a separate deletion button.
    Legacy/manual teams not linked in LIEN_KET_DANG_KY_DOI are untouched.
    """
    who=st.session_state.get("auth",{})
    if who.get("role")!="ADMIN":
        return
    try:
        # No external reads/writes until at least one new tracked link exists.
        links=read_sheet("LIEN_KET_DANG_KY_DOI")
        if not any(r.get("Trạng thái liên kết")==LINK_ACTIVE for r in links):
            return
        fresh_links=read_sheet_live("LIEN_KET_DANG_KY_DOI")
        fresh_regs=read_sheet_live("DANG_KY_THANH_VIEN")
        orphaned=lost_registrations(fresh_regs,fresh_links)
        if not orphaned:
            return
        total_tasks=0
        reviewed=0
        processed=0
        for link in orphaned:
            # Each linked team is reconciled against fresh data before
            # applying a single atomic batch across the related worksheets.
            teams=read_sheet_live("QUAN_LY_DOI")
            creds=read_sheet_live("TAI_KHOAN_DOI")
            tasks_vc=read_sheet_live("VAN_CHUYEN")
            tasks_ld=read_sheet_live("LAP_DAT")
            reports=read_sheet_live("BAO_CAO_TRIEN_KHAI")
            hub=read_sheet_live("BAN_GIAO_TAP_KET")
            plan=plan_detach(link,teams,creds,tasks_vc,tasks_ld,reports,hub)
            keys=("QUAN_LY_DOI","TAI_KHOAN_DOI","VAN_CHUYEN",
                  "LAP_DAT","LIEN_KET_DANG_KY_DOI")
            ids={n:sheet(n).id for n in keys}
            changes=detach_requests(plan,ids,now())
            client()[0].batch_update({"requests":changes})
            read_sheet.clear()
            processed+=1
            total_tasks+=len(plan["pending_tasks"])
            reviewed+=int(plan["review"])
            audit(who["username"],"TỰ GỠ ĐỘI SAU XÓA ĐĂNG KÝ",
                  "LIEN_KET_DANG_KY_DOI",
                  str(link.get("Mã đăng ký","")),"OK",
                  f"Đội: {plan['team_id']} • Nhiệm vụ trả về: "
                  f"{len(plan['pending_tasks'])} • Cần đối soát: {plan['review']}")
        if processed:
            st.success(f"Đã đối chiếu hồ sơ bị xóa: gỡ {processed} đội "
                       f"và trả {total_tasks} nhiệm vụ/SKU chưa thực hiện "
                       "về chờ phân công lại.")
            if reviewed:
                st.warning(f"{reviewed} đội có báo cáo, chứng từ tập kết "
                           "hoặc nhiệm vụ đã thực hiện: đã khóa quyền, "
                           "giữ chứng từ cũ để ADMIN đối soát.")
    except Exception as exc:
        read_sheet.clear()
        st.warning("Không hoàn tất được đồng bộ xóa đăng ký ("+
                   type(exc).__name__+"). Không xóa thủ công nhiệm vụ, "
                   "hãy vào Quản lý đội để đối soát. "
                   "Các tài khoản thuộc hồ sơ đã mất vẫn bị khóa "
                   "khi xác thực lại.")


def bulk_matrix_xlsx(plan, sku_list):
    wb = ExcelWorkbook()
    ws = wb.active
    ws.title = "PHAN_BO_XEM_TRUOC"
    ws.append(["Mã điểm", "Tên địa điểm"] + sku_list)
    for r in plan:
        ws.append([r["Mã điểm"], r["Tên địa điểm"]] +
                  [float(r["quantities"][sku]) for sku in sku_list])
    ws.freeze_panes = "C2"
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 44
    for n in range(len(sku_list)):
        from openpyxl.utils import get_column_letter
        ws.column_dimensions[get_column_letter(n+3)].width = 16
    for cell in ws[1]:
        from openpyxl.styles import Font, PatternFill
        cell.fill = PatternFill("solid", fgColor="183A72")
        cell.font = Font(color="FFFFFF", bold=True)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def allocate_bulk():
    require_role("ADMIN")
    st.subheader("📦 Phân bổ theo nhóm địa điểm – bộ định mức hồ sơ thầu")
    st.caption("Khai một bộ SKU và số lượng cấp cho MỖI ĐIỂM, sau đó chọn "
               "nhiều xã/đơn vị cùng nhận bộ hàng đó. Nhóm có định mức khác "
               "thực hiện ở đợt riêng hoặc chỉnh ngoại lệ. "
               "PHÂN BỔ không phải XUẤT KHO.")
    prows=read_sheet("DANH_SACH_DU_AN")
    projects=[r["Mã dự án"] for r in prows if r.get("Mã dự án")]
    if not projects:
        st.warning("Cần tạo dự án trước.")
        return
    project=st.selectbox("Dự án",projects,key="bulk_project")
    points=[r for r in read_sheet("DANH_SACH_DIEM")
            if r.get("Mã dự án")==project and r.get("Mã điểm")
            and r.get("Trạng thái")=="Hoạt động"]
    if len(points)!=len({r["Mã điểm"] for r in points}):
        st.error("Danh sách địa điểm có mã trùng. Cần ADMIN đối soát trước.")
        return
    imports=read_sheet("NHAP_KHO")
    allocations=read_sheet("KHO_PHAN_BO")
    inventory,inventory_issues=inventory_by_sku(project,imports,allocations)
    if inventory_issues:
        for issue in inventory_issues:
            st.error(issue)
        st.warning("Phải đối soát kho trước khi phân bổ.")
        return
    if not points or not inventory:
        st.warning("Dự án cần có danh sách địa điểm và ít nhất một SKU trong NHAP_KHO.")
        return
    point_by_id={r["Mã điểm"]:r for r in points}
    point_ids=list(point_by_id)
    names={pid:point_by_id[pid]["Tên xã/phường/đơn vị"] for pid in point_ids}
    skus=list(inventory)
    st.write(f"**{len(point_ids)} địa điểm** · **{len(skus)} SKU nhập kho** "
             "· Có thể chia thành nhiều nhóm định mức theo hồ sơ thầu.")

    st.markdown("#### 1. Bộ mặt hàng và định mức cho mỗi điểm")
    st.caption("Nhập số lượng **mỗi địa điểm được cấp**, KHÔNG phải tổng "
               "của cả nhóm. Ví dụ 12 bộ/điểm × 20 điểm = 240 bộ. "
               "SKU nào không cấp trong nhóm này thì để 0.")
    defaults={}
    for sku in skus:
        item=inventory[sku]
        st.caption(f"**{sku}** — {item['name']} ({item['unit']}) · "
                   f"Kho còn khả dụng để phân bổ: {item['remaining']:g}")
        defaults[sku]=st.number_input(
            f"Số lượng {sku} / mỗi điểm ({item['unit']})",
            min_value=0.0,value=0.0,step=1.0,format="%.3f",
            key=f"bulk_default_{project}_{sku}")

    st.markdown("#### 2. Chọn nhóm xã/đơn vị có cùng định mức")
    method=st.radio("Cách chọn danh sách điểm theo hồ sơ thầu",
        ["🔎 Gõ tìm tên / mã điểm", "📋 Dán danh sách từ hợp đồng",
         "📄 Nạp danh sách Excel", "☑️ Chọn tất cả điểm chưa phân bổ"],
        key=f"bulk_method_{project}")
    issues=[]
    if method.startswith("🔎"):
        chosen_ids=st.multiselect(
            "Địa điểm nhận bộ hàng hóa trên",
            point_ids, default=[],
            format_func=lambda pid:f"{names[pid]} • {pid}",
            placeholder="Gõ tên xã, đơn vị hoặc mã điểm để tìm...",
            key=f"bulk_points_{project}")
        st.caption("Chọn liên tiếp các điểm trong cùng một nhóm. "
                   "Không phải kéo qua cả 136 hay 500 điểm.")
    elif method.startswith("📋"):
        text_list=st.text_area(
            "Dán danh sách địa điểm đã ký hợp đồng",
            placeholder="Mỗi dòng một tên xã/đơn vị hoặc một Mã điểm. "
                        "Ví dụ:\nPhường Minh Xuân\nDD-TEST-127",
            key=f"bulk_contract_text_{project}",height=170)
        chosen_ids,issues=match_contract_locations(
            project,points,text_list.splitlines())
    elif method.startswith("📄"):
        upload=st.file_uploader(
            "Nạp Excel danh sách điểm cùng định mức "
            "(cột Mã điểm hoặc Tên xã/phường/đơn vị)",
            type=["xlsx"],key=f"bulk_group_excel_{project}")
        chosen_ids=[]
        if upload:
            try:
                raw_names=read_contract_locations_excel(
                    upload.name,upload.getvalue())
                chosen_ids,issues=match_contract_locations(
                    project,points,raw_names)
            except ValueError as exc:
                issues=[str(exc)]
    else:
        has_any={r.get("Mã điểm") for r in allocations
                 if r.get("Mã dự án")==project and r.get("SKU")}
        chosen_ids=[pid for pid in point_ids if pid not in has_any]
        st.caption("Chỉ chọn điểm chưa có SKU nào được phân bổ. "
                   "Điểm đã phân bổ một phần phải kiểm tra riêng.")

    for issue in issues[:10]:
        st.error(issue)
    if len(issues)>10:
        st.error(f"Còn {len(issues)-10} địa điểm không khớp. "
                 "Hãy sửa danh sách, không thể ghi.")
    st.write(f"**Nhóm hiện chọn: {len(chosen_ids)} địa điểm** "
             f"trong tổng số {len(point_ids)} điểm của dự án.")
    if chosen_ids:
        with st.expander("Xem tên và mã điểm đã chọn"):
            st.dataframe([{"Mã điểm":pid,"Xã/phường/đơn vị":names[pid]}
                          for pid in chosen_ids],
                         hide_index=True,use_container_width=True)
    if issues:
        return
    if not chosen_ids:
        st.info("Vui lòng chọn ít nhất một địa điểm để lập phương án phân bổ.")
        return

    # Basket totals here are a preview, not a record of a warehouse issue.
    basket_totals=preview_basket(skus,defaults,len(chosen_ids))
    st.markdown("#### Đối chiếu nhanh bộ định mức × số điểm")
    st.dataframe([{
        "SKU":sku,"Hàng hóa":inventory[sku]["name"],
        "ĐVT":inventory[sku]["unit"],
        "SL/điểm":float(defaults[sku]),
        "Số điểm":len(chosen_ids),
        "Tổng dự kiến":float(basket_totals[sku]),
        "Tồn có thể phân bổ":float(inventory[sku]["remaining"])
    } for sku in skus if basket_totals[sku]>0],
        hide_index=True,use_container_width=True)
    st.caption("Đây là bảng rà soát theo định mức ADMIN vừa nhập; "
               "chưa có dữ liệu định mức thầu độc lập để tự so sánh với "
               "hồ sơ gốc. ADMIN cần kiểm tra định mức trước khi xác nhận.")

    st.markdown("#### 3. Điều chỉnh những đơn vị có định mức khác")
    uploaded = st.file_uploader(
        "Tùy chọn: nạp Excel các điểm ngoại lệ (cột Mã điểm và các cột SKU)",
        type=["xlsx"], key=f"bulk_exc_upload_{project}")
    imported, imported_points = {}, []
    upload_fingerprint = "noexcel"
    if uploaded is not None:
        try:
            import_data = uploaded.getvalue()
            imported, imported_points = parse_exception_excel(
                uploaded.name, import_data, chosen_ids, skus)
            upload_fingerprint = hashlib.sha256(import_data).hexdigest()[:10]
            st.success(f"Đã đọc {len(imported_points)} điểm ngoại lệ trong Excel. "
                       "Chưa ghi vào Google Sheets.")
        except Exception as exc:
            st.error("Excel ngoại lệ không hợp lệ: " + str(exc))
            return
    exceptions = st.multiselect("Chọn các điểm ngoại lệ (có thể nhiều hoặc ít hơn 15)",
        chosen_ids,default=imported_points,
        format_func=lambda pid:f"{names[pid]} • {pid}",
        key=f"bulk_exception_{project}_{upload_fingerprint}")
    overrides = {}
    if exceptions:
        source_rows = []
        for pid in exceptions:
            row = {"Mã điểm":pid,"Tên địa điểm":names[pid]}
            row.update({sku:float(imported.get((pid,sku), defaults[sku])) for sku in skus})
            source_rows.append(row)
        ui_key = hashlib.sha256(
            repr((project, upload_fingerprint, sorted(exceptions),
                  tuple((k,defaults[k]) for k in skus))).encode()
        ).hexdigest()[:16]
        edited = st.data_editor(
            source_rows, key=f"bulk_exceptions_{ui_key}", hide_index=True,
            use_container_width=True, num_rows="fixed",
            disabled=["Mã điểm", "Tên địa điểm"],
            column_config={
                "Mã điểm":st.column_config.TextColumn("Mã điểm"),
                "Tên địa điểm":st.column_config.TextColumn("Địa điểm"),
                **{sku:st.column_config.NumberColumn(
                    sku, min_value=0.0, step=1.0, format="%.3f")
                   for sku in skus}
            })
        exception_rows = edited.to_dict("records") if hasattr(edited,"to_dict") else edited
        for row in exception_rows:
            pid = row["Mã điểm"]
            for sku in skus:
                overrides[(pid,sku)] = row.get(sku,defaults[sku])
    plan = build_plan([point_by_id[pid] for pid in chosen_ids],
                      skus, defaults, overrides)
    errors, candidates, totals = verify_plan(
        project, plan, inventory, allocations, points)
    st.markdown("#### 4. Đối soát trước khi xác nhận")
    preview_summary = []
    for sku,itm in inventory.items():
        preview_summary.append({
            "SKU":sku,"Tên hàng":itm["name"],"ĐVT":itm["unit"],
            "Tồn khả dụng":float(itm["remaining"]),
            "Dự kiến phân bổ":float(totals.get(sku, 0)),
            "Còn sau phân bổ":float(itm["remaining"]-totals.get(sku,0))
        })
    st.dataframe(preview_summary, hide_index=True, use_container_width=True)
    st.caption(f"Dự kiến ghi {len(candidates)} dòng vào KHO_PHAN_BO; "
               f"phát sinh tương ứng nhiệm vụ VC và KTV. "
               f"Địa điểm được chọn: {len(chosen_ids)}; ngoại lệ: {len(exceptions)}.")
    with st.expander("Xem toàn bộ ma trận địa điểm × SKU",expanded=False):
        st.dataframe([{"Mã điểm":r["Mã điểm"],"Địa điểm":r["Tên địa điểm"],
                       **{sku:float(r["quantities"][sku]) for sku in skus}}
                      for r in plan],hide_index=True,use_container_width=True)
    st.download_button("⬇️ Tải ma trận xem trước (.xlsx)",
        data=bulk_matrix_xlsx(plan, skus),
        file_name=f"PHAN_BO_NHAP_{project}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"bulk_preview_download_{project}")
    if errors:
        for error in errors[:12]:
            st.error(error)
        if len(errors)>12:
            st.error(f"Còn {len(errors)-12} lỗi khác; phải xử lý trước khi ghi.")
        return
    st.warning("Chỉ xác nhận khi bộ SKU, định mức của mỗi điểm và DANH SÁCH "
               "địa điểm đã khớp hồ sơ thầu. Không cho phân bổ trùng SKU/điểm "
               "hoặc vượt hàng thực nhập.")
    if len(candidates)>1600:
        st.info("Đợt lớn có thể tải lâu khi ghi nhiều dòng. "
                "Chỉ bấm xác nhận một lần và đối soát mã đợt.")
    basket_signature=hashlib.sha256(repr((
        project,tuple(sorted(chosen_ids)),
        tuple((r["Mã điểm"],tuple(sorted(r["quantities"].items()))) for r in plan)
    )).encode("utf-8")).hexdigest()[:16]
    accepted=st.checkbox(
        f"Tôi đã kiểm tra {len(chosen_ids)} điểm, định mức SKU, tồn khả dụng "
        "và xác nhận đúng hồ sơ thầu.",
        key=f"bulk_approved_{basket_signature}")
    if not st.button("✅ XÁC NHẬN PHÂN BỔ HÀNG LOẠT",
                     key=f"bulk_confirm_{project}",type="primary",
                     use_container_width=True,disabled=not accepted):
        return
    # A single atomic Google Sheets batch contains the data for all tables.
    # Re-read live without cached data immediately before commit.
    try:
        live_imports = read_sheet_live("NHAP_KHO")
        live_allocations = read_sheet_live("KHO_PHAN_BO")
        live_points = read_sheet_live("DANH_SACH_DIEM")
        live_projects = read_sheet_live("DANH_SACH_DU_AN")
        if project not in {p.get("Mã dự án") for p in live_projects}:
            st.error("Dự án đã thay đổi, không ghi phân bổ.")
            return
        live_inventory, live_errors = inventory_by_sku(
            project,live_imports,live_allocations)
        changed = any(sku not in live_inventory or
            (live_inventory[sku]["name"],live_inventory[sku]["unit"]) !=
            (inventory[sku]["name"],inventory[sku]["unit"])
            for sku in skus)
        if live_errors or changed:
            st.error("Danh mục kho đã thay đổi; vui lòng kiểm tra và lập lại.")
            return
        live_errors, live_candidates, live_totals = verify_plan(
            project,plan,live_inventory,live_allocations,live_points)
        if live_errors:
            for issue in live_errors[:8]:
                st.error(issue)
            st.error("Không ghi dữ liệu. Hãy kiểm tra lại phương án.")
            return
        batch_id="PB-"+uuid.uuid4().hex[:12].upper()
        sheet_names=["DM_CHUAN","KHO_PHAN_BO","VAN_CHUYEN","LAP_DAT",
                     "TIEN_DO","NHAT_KY_HE_THONG"]
        spreadsheet=client()[0]
        ids={name:spreadsheet.worksheet(name).id for name in sheet_names}
        existing_tasks={
            "VAN_CHUYEN":read_sheet_live("VAN_CHUYEN"),
            "LAP_DAT":read_sheet_live("LAP_DAT")
        }
        progress=read_sheet_live("TIEN_DO")
        requests = atomic_requests(
            ids,live_candidates,batch_id,project,live_inventory,
            names,auth()["username"],now(),existing_tasks,progress)
        spreadsheet.batch_update({"requests":requests})
        read_sheet.clear()
        st.success(f"Đã phân bổ {len(live_candidates)} dòng tại "
                   f"{len({p for p,s,q in live_candidates})} điểm. "
                   f"Mã đợt: {batch_id}. "
                   "Đã tạo đồng thời nhiệm vụ VC/KTV, chờ ADMIN gán đội.")
    except Exception as exc:
        read_sheet.clear()
        st.error("CHƯA XÁC NHẬN ĐƯỢC KẾT QUẢ GHI ("+type(exc).__name__+
                 "). KHÔNG bấm lại. Kiểm tra KHO_PHAN_BO, VAN_CHUYEN, "
                 "LAP_DAT và NHAT_KY_HE_THONG trước khi thử tiếp.")


def allocate():
    require_role("ADMIN")
    mode=st.radio("Cách phân bổ",[
        "Hàng loạt – định mức chung + ngoại lệ",
        "Theo từng địa điểm (cách cũ)"
    ],key="allocation_mode")
    if mode.startswith("Hàng loạt"):
        allocate_bulk()
    else:
        allocate_single()


def allocate_single():
    require_role("ADMIN")
    st.subheader("📦 Phân bổ SLHH theo từng điểm")
    prows=read_sheet("DANH_SACH_DU_AN")
    projects=[r["Mã dự án"] for r in prows if r.get("Mã dự án")]
    if not projects:
        st.info("Cần tạo dự án trước.")
        return
    project=st.selectbox("Dự án",projects)
    points=[x for x in read_sheet("DANH_SACH_DIEM") if x.get("Mã dự án")==project and x.get("Mã điểm")]
    if not points:
        st.info("Cần có điểm thuộc dự án này.")
        return
    pmap={f"{x['Tên xã/phường/đơn vị']} • {x['Mã điểm']}":x for x in points}
    point=pmap[st.selectbox("Điểm cần phân bổ",list(pmap))]
    imports=[r for r in read_sheet("NHAP_KHO") if r.get("Mã dự án")==project and r.get("SKU")]
    allocations=[r for r in read_sheet("KHO_PHAN_BO") if r.get("Mã dự án")==project]
    items={}
    for r in imports:
        sku=r["SKU"]
        if sku not in items:
            items[sku]={"name":r["Tên hàng hóa"],"unit":r["Đơn vị tính"],"in":0}
        items[sku]["in"]+=float(r.get("SL thực nhận") or 0)
    for r in allocations:
        if r.get("SKU") in items:
            items[r["SKU"]]["in"]-=float(r.get("SL phân bổ") or 0)
    with st.form("allocate_batch"):
        quantities={}
        for sku,item in items.items():
            remain=max(0,item["in"])
            st.caption(f"{sku} • {item['name']} • Tồn khả dụng: {remain:g} {item['unit']}")
            quantities[sku]=st.number_input(f"SL phân bổ {sku}",min_value=0.0,max_value=float(remain),step=1.0,key=f"alloc_{sku}")
        if st.form_submit_button("PHÂN BỔ",use_container_width=True):
            chosen={sku:v for sku,v in quantities.items() if v>0}
            if not chosen:
                st.warning("Chưa nhập SLHH.")
                return
            bid="PB-"+uuid.uuid4().hex[:12].upper()
            try:
                # Re-check stock just before writing. One Admin should allocate at a time.
                freshin=read_sheet("NHAP_KHO")
                freshpb=read_sheet("KHO_PHAN_BO")
                for sku,qty in chosen.items():
                    available=(sum(float(r.get("SL thực nhận") or 0) for r in freshin if r.get("Mã dự án")==project and r.get("SKU")==sku)
                               -sum(float(r.get("SL phân bổ") or 0) for r in freshpb if r.get("Mã dự án")==project and r.get("SKU")==sku))
                    if qty>available: fail(f"SKU {sku}: vượt số lượng còn lại.")
                for sku,qty in chosen.items():
                    pid="PB-"+uuid.uuid4().hex[:12].upper()
                    item=items[sku]
                    append("DM_CHUAN",[bid,project,sku,item["name"],item["unit"],qty,point["Mã điểm"],point["Tên xã/phường/đơn vị"],"Đã phân bổ",auth()["username"],now(),""])
                    append("KHO_PHAN_BO",[pid,bid,project,point["Mã điểm"],sku,item["name"],item["unit"],qty,now(),"Đã phân bổ",""])
                    append("VAN_CHUYEN",["VC-"+uuid.uuid4().hex[:12].upper(),pid,project,point["Mã điểm"],sku,qty,"","Chưa giao","","","","","",""])
                    append("LAP_DAT",["LD-"+uuid.uuid4().hex[:12].upper(),pid,project,point["Mã điểm"],sku,qty,"","Chưa lắp","","","","","",""])
                sync_progress(project, point["Mã điểm"])
                audit(auth()["username"],"PHÂN BỔ","KHO_PHAN_BO",bid,"OK")
                st.success(f"Đã phân bổ {len(chosen)} SKU. Tiếp theo Admin gán đội VC/KTV.")
            except Exception as e:
                audit(auth()["username"],"PHÂN BỔ","KHO_PHAN_BO",bid,"CẦN ĐỐI SOÁT",str(e))
                st.error("Có lỗi giữa quá trình phân bổ. Cần đối soát trước khi thử lại.")

def provision_team_password():
    """ADMIN-only provisioning. Password is shown ONCE and never stored clear.

    Existing signed remembered logins become invalid after a password reset.
    The sheet is an ADMIN/SA-only credential vault; do not share edit access.
    """
    a=require_role("ADMIN")
    with st.expander("🔐 CẤP / ĐẶT LẠI MẬT KHẨU – ĐỘI ĐÃ TẠO",
                     expanded=False):
        st.caption("Danh sách này đọc từ QUAN_LY_DOI (đội đã có trong hệ thống), "
                   "KHÔNG đọc từ DANG_KY_THANH_VIEN. "
                   "Xóa hồ sơ đăng ký không xóa các đội này. "
                   "Hồ sơ mới có mật khẩu tự chọn sẽ kích hoạt khi ADMIN duyệt; "
                   "đội cũ hoặc quên mật khẩu có thể cấp/đặt lại tại đây.")
        teams=[t for t in read_sheet("QUAN_LY_DOI")
               if t.get("Trạng thái")=="Hoạt động"
               and t.get("Loại nhiệm vụ") in ("VC","KTV","VC+KTV")
               and t.get("Mã dự án") and t.get("Mã đội")]
        if not teams:
            st.info("Chưa có đội trưởng VC/KTV đã duyệt. "
                    "Cần duyệt hồ sơ trước khi cấp mật khẩu.")
            return
        team=st.selectbox(
            "Chọn đội trưởng đang có trong QUAN_LY_DOI", teams,
            format_func=lambda t:(t.get("Tên đội/đội trưởng","")+
                                  " • "+t.get("Mã dự án","")+
                                  " • "+t.get("Loại nhiệm vụ","")),
            key="credential_team_selection")
        if sum(normalized_name(t.get("Tên đội/đội trưởng"))==
               normalized_name(team.get("Tên đội/đội trưởng"))
               for t in teams)>1:
            st.error("Có nhiều đội trưởng trùng họ tên. "
                     "Hiện đăng nhập bằng tên không phân biệt được họ; "
                     "ADMIN cần làm rõ định danh trước khi cấp.")
            return
        records=read_sheet("TAI_KHOAN_DOI")
        current,existing=visible_credential_state(
            team,records,st.secrets.get("accounts",{}))
        if current=="conflict":
            st.error("Có nhiều tài khoản trùng mã đội. "
                     "Cần xử lý hồ sơ tài khoản trước khi cấp.")
            return
        if current=="legacy":
            st.info("Đội này đã có tài khoản trong Streamlit Secrets. "
                    "Để tránh hai tài khoản cùng quyền, B chưa cho cấp thêm "
                    "ở đây; ADMIN cần đối soát tài khoản cũ trước.")
            return
        if current=="active":
            st.info("Đội trưởng đã được cấp tài khoản. "
                    "Nếu quên mật khẩu, có thể ĐẶT LẠI; "
                    "mật khẩu cũ sẽ mất hiệu lực.")
        else:
            st.info("Đội trưởng chưa có tài khoản. Có thể cấp mới.")
        action="ĐẶT LẠI MẬT KHẨU" if current=="active" else "CẤP MẬT KHẨU"
        method=st.radio(
            "Cách chọn mật khẩu",
            ["Đội trưởng đề nghị / ADMIN nhập hộ","Hệ thống tự tạo mật khẩu"],
            horizontal=False,key="credential_password_method")
        if method.startswith("Đội trưởng"):
            st.caption("Nhập mật khẩu theo mong muốn của người nhận: "
                       "ít nhất **10 ký tự**, có chữ và số, không dùng "
                       "tên/số điện thoại hoặc mã dễ đoán. "
                       "Không gửi mật khẩu trong nhóm Zalo.")
            custom_password=st.text_input(
                "Mật khẩu theo đề nghị *",type="password",
                max_chars=128,key="credential_custom_password")
            confirm_custom=st.text_input(
                "Nhập lại mật khẩu *",type="password",
                max_chars=128,key="credential_custom_confirm")
        approve=st.checkbox(
            "Tôi xác nhận đúng người nhận và sẽ chỉ gửi mật khẩu "
            "qua tin nhắn riêng, không đăng vào nhóm.",
            key="credential_confirm_private")
        if not st.button("🔐 "+action,type="primary",
                         use_container_width=True,
                         disabled=not approve,key="credential_provision"):
            return
        if method.startswith("Đội trưởng"):
            if custom_password!=confirm_custom:
                st.error("Hai lần nhập mật khẩu chưa giống nhau. "
                         "Chưa cấp/đặt lại mật khẩu.")
                return
            message=validate_custom_password(
                custom_password,team.get("Tên đội/đội trưởng",""),
                team.get("SĐT đội trưởng",""))
            if message:
                st.error(message)
                return
        try:
            # Strict live recheck before writing: sheet and team can change
            # while the ADMIN form is open.
            read_sheet.clear()
            teams_live=read_sheet("QUAN_LY_DOI")
            live=[t for t in teams_live
                  if t.get("Mã đội")==team["Mã đội"]
                  and t.get("Mã dự án")==team["Mã dự án"]
                  and t.get("Trạng thái")=="Hoạt động"
                  and t.get("Loại nhiệm vụ") in ("VC","KTV","VC+KTV")]
            if len(live)!=1 or live[0].get("Tên đội/đội trưởng")!=team.get("Tên đội/đội trưởng"):
                fail("Thông tin đội trưởng đã thay đổi. Hãy tải lại.")
            if sum(normalized_name(t.get("Tên đội/đội trưởng"))==
                   normalized_name(team.get("Tên đội/đội trưởng"))
                   for t in teams_live if t.get("Trạng thái")=="Hoạt động")>1:
                fail("Tên đội trưởng trùng; phải đối soát trước khi cấp.")
            fresh=read_sheet("TAI_KHOAN_DOI")
            kind,row=visible_credential_state(
                live[0],fresh,st.secrets.get("accounts",{}))
            if kind!=current or kind in ("conflict","legacy"):
                fail("Tình trạng tài khoản thay đổi; hãy mở lại.")
            password=(custom_password if method.startswith("Đội trưởng")
                      else new_password())
            salt,digest=create_hash(password)
            admin=str(a["username"])
            when=now()
            if current=="active":
                # Replace only salted secret, status, time and audit owner.
                # Never duplicate active accounts for a team.
                idx=row.get("_row")
                if not isinstance(idx,int) or idx<2:
                    fail("Không tìm thấy dòng tài khoản để đặt lại.")
                sheet("TAI_KHOAN_DOI").update(
                    range_name=f"E{idx}:J{idx}",
                    values=[[salt,digest,"Hoạt động",when,admin,
                             "ADMIN đặt lại mật khẩu trên PREVIEW"]],
                    value_input_option="RAW")
                username=row["Mã tài khoản"]
            else:
                usernames={r.get("Mã tài khoản") for r in fresh}
                usernames.update(st.secrets.get("accounts",{}).keys())
                username=next_account_id(usernames)
                append("TAI_KHOAN_DOI", [
                    username,team["Mã đội"],team["Mã dự án"],
                    "DOI_TRUONG",salt,digest,"Hoạt động",when,
                    admin,"ADMIN cấp mật khẩu trên PREVIEW"])
            read_sheet.clear()
            verified=effective_accounts().get(username)
            if not verified or verified.get("hash")!=digest or (
                    verified.get("team_id")!=team["Mã đội"]):
                fail("Đã ghi nhưng chưa xác nhận tài khoản hợp lệ. "
                     "Không cấp mật khẩu; hãy đối soát trước khi thử lại.")
            # No raw password in Sheets, GitHub, audit logs, or cookies.
            audit(admin,"CẤP MẬT KHẨU ĐỘI TRƯỞNG","TAI_KHOAN_DOI",
                  username,"OK",team["Mã dự án"]+
                  " / "+("Đặt lại" if current=="active" else "Cấp mới"))
            st.success("Đã "+("đặt lại" if current=="active" else "cấp")+
                       " mật khẩu cho **"+team["Tên đội/đội trưởng"]+"**.")
            st.warning("Mật khẩu chỉ được hiển thị cho ADMIN tại lần cấp này. "
                       "Hãy gửi riêng cho đội trưởng; không đăng nhóm.")
            st.code(password,language=None)
            st.caption("Đội trưởng mở app → ĐỘI TRƯỞNG – BÁO CÁO "
                       "→ nhập HỌ TÊN đã đăng ký + mật khẩu này. "
                       "Có thể tích Ghi nhớ đăng nhập 30 ngày trên máy cá nhân.")
        except Exception as exc:
            read_sheet.clear()
            st.error("Chưa xác nhận được việc cấp mật khẩu ("+
                     type(exc).__name__+"). Không gửi bất kỳ mật khẩu "
                     "nào nếu chưa thấy thông báo cấp thành công. "
                     "Cần kiểm tra bảng tài khoản trước khi làm lại.")


def teams_and_approval():
    require_role("ADMIN")
    st.subheader("👥 Quản lý đội / Duyệt đăng ký")
    if st.button("🔄 LÀM MỚI DỮ LIỆU TỪ GOOGLE SHEETS",
                 key="admin_team_refresh",use_container_width=True):
        read_sheet.clear()
        st.rerun()
    registrations=read_sheet("DANG_KY_THANH_VIEN")
    active_teams=[t for t in read_sheet("QUAN_LY_DOI")
                  if t.get("Mã đội") and t.get("Trạng thái")=="Hoạt động"]
    account_count=sum(bool(r.get("Mã tài khoản"))
                      for r in read_sheet("TAI_KHOAN_DOI")
                      if r.get("Trạng thái")=="Hoạt động")
    st.caption(f"Google Sheets PREVIEW: **{len(registrations)} hồ sơ đăng ký**"
               f" • **{len(active_teams)} đội trưởng đang hoạt động**"
               f" • **{account_count} tài khoản cấp qua app**.")
    if not registrations and active_teams:
        st.info("📋 Bảng DANG_KY_THANH_VIEN đã trống. "
                "Các tên trong mục CẤP / ĐẶT LẠI MẬT KHẨU là đội trưởng "
                "đang còn ở bảng QUAN_LY_DOI, KHÔNG phải hồ sơ chờ duyệt. "
                "Các đội cũ/tạo thủ công chưa có liên kết hồ sơ "
                "sẽ được giữ nguyên để tránh xóa nhầm. "
                "Với đội mới có liên kết, khi xóa hồ sơ app sẽ tự ngừng "
                "tài khoản và gỡ các nhiệm vụ CHƯA thực hiện lúc ADMIN "
                "mở/làm mới app. Phân bổ kho cho xã vẫn giữ nguyên.")
    render_pending_approvals(
        read_sheet=read_sheet, sheet=sheet, client=client, auth=auth,
        audit=audit, lookup=lookup, sheet_datetime_serial=sheet_datetime_serial,
        secret_accounts=st.secrets.get("accounts",{}),current_time=now)
    # Read-only impact preview: assess consequence BEFORE deleting an
    # approved registration in Sheets; no task/stock/account writes.
    links=[x for x in read_sheet("LIEN_KET_DANG_KY_DOI")
           if x.get("Trạng thái liên kết")==LINK_ACTIVE]
    with st.expander("🔎 XEM ẢNH HƯỞNG KHI XÓA ĐỘI TRƯỞNG",
                     expanded=False):
        st.caption("Chỉ mô phỏng bằng dữ liệu hiện tại, KHÔNG xóa. "
                   "ADMIN thấy nhiệm vụ nào có thể giao lại ngay, "
                   "nhiệm vụ nào phải bàn giao thực tế/đối soát trước. "
                   "Hàng phân bổ cho xã luôn giữ nguyên.")
        if not links:
            st.info("Chưa có đội nào gắn được với hồ sơ đăng ký. "
                    "Các đội nhập thủ công/cũ phải đối chiếu riêng.")
        else:
            all_teams=read_sheet("QUAN_LY_DOI")
            by_code={(t.get("Mã dự án"),t.get("Mã đội")):t for t in all_teams}
            selected=st.selectbox(
                "Chọn đội trưởng để xem tác động",
                links,
                format_func=lambda link:(
                    by_code.get((link.get("Mã dự án"),link.get("Mã đội")),{})
                    .get("Tên đội/đội trưởng","Đội trưởng")+
                    " • "+str(link.get("Mã dự án",""))),
                key="admin_detach_impact_team")
            try:
                impact=plan_detach(
                    selected,all_teams,read_sheet("TAI_KHOAN_DOI"),
                    read_sheet("VAN_CHUYEN"),read_sheet("LAP_DAT"),
                    read_sheet("BAO_CAO_TRIEN_KHAI"),
                    read_sheet("BAN_GIAO_TAP_KET"))
                c1,c2=st.columns(2)
                c1.metric("SKU-nhiệm vụ trả chờ giao",
                          len(impact["pending_tasks"]))
                c2.metric("Nhiệm vụ/chứng từ giữ đối soát",
                          len(impact["protected_tasks"]))
                st.caption(f"Địa điểm có việc trả về: "
                           f"{impact['released_sites']} • "
                           f"KTV còn giữ hàng tập kết: "
                           f"{impact['custody_sites']} • "
                           f"VC đã bàn giao ở tập kết: "
                           f"{impact['vc_hub_sites']} • "
                           f"Biên bản cũ thiếu mã VC: "
                           f"{impact['unknown_hub_sites']}")
                if impact["protected_details"]:
                    st.warning("Có hàng đã nhận, báo cáo hoặc chứng từ "
                               "cần xử lý bàn giao. Không tự giải phóng "
                               "trách nhiệm KTV đang giữ hàng.")
                display=impact["pending_details"]+impact["protected_details"]
                if display:
                    st.dataframe([{
                        "Công đoạn":r["table"],"Mã điểm":r["point_id"],
                        "SKU":r["sku"],"SL nhiệm vụ":r["quantity"],
                        "Xử lý":r["state"],
                        "Lý do":r.get("reason","")
                    } for r in display],
                        hide_index=True,use_container_width=True,height=230)
                else:
                    st.info("Đội chưa có nhiệm vụ VC/LĐ cần xử lý.")
                st.caption("Nếu V xóa hồ sơ ở Google Sheets, ADMIN "
                           "mở/làm mới app sẽ đối soát theo bảng liên kết; "
                           "báo cáo đã hoàn tất và KHO_PHAN_BO giữ nguyên.")
            except ValueError as exc:
                st.error("Liên kết hoặc đội chưa hợp lệ: "+str(exc))
    provision_team_password()
    st.caption("Chỉ quản lý đội trưởng. Thành viên của đội do đội trưởng tự quản lý.")
    with st.expander("➕ Thêm đội trưởng thủ công (không phải gán nhiệm vụ)", expanded=False):
        saved_team_message=st.session_state.pop("team_saved_message", None)
        if saved_team_message:
            st.success(saved_team_message)
        revision=st.session_state.get("team_form_revision", 0)
        with st.form(f"team_form_{revision}"):
            tid=st.text_input("Mã đội mới", key=f"team_id_{revision}")
            name=st.text_input("Tên đội / Đội trưởng", key=f"team_name_{revision}")
            phone=st.text_input("SĐT đội trưởng", key=f"team_phone_{revision}")
            kind=st.selectbox("Loại nhiệm vụ", ["— Chọn loại nhiệm vụ —","VC","KTV","VC+KTV"],
                              key=f"team_kind_{revision}")
            proj=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN") if r.get("Mã dự án")]
            project=st.selectbox("Dự án", ["— Chọn dự án —"]+proj,
                                 key=f"team_project_{revision}")
            if st.form_submit_button("THÊM ĐỘI"):
                tid, name, phone=tid.strip(), name.strip(), phone.strip()
                if not tid or not name or not phone or kind not in ("VC","KTV","VC+KTV") or project not in proj:
                    st.error("Vui lòng nhập đủ mã đội, tên, số điện thoại và chọn nhiệm vụ, dự án.")
                elif lookup(read_sheet("QUAN_LY_DOI"),"Mã đội",tid):
                    st.error("Mã đội này đã tồn tại; hãy chọn mã khác.")
                elif matching_teams(read_sheet("QUAN_LY_DOI"),name=name,phone=phone,
                                    kind=kind,project=project):
                    st.error("Đã có đội trùng người phụ trách, số điện thoại và dự án.")
                else:
                    try:
                        append("QUAN_LY_DOI",[tid,name,phone,kind,"","Hoạt động",project,""])
                        st.session_state["team_saved_message"]=(
                            f"Đã thêm đội {tid} thành công. Biểu mẫu đã được làm trống "
                            "để nhập đội tiếp theo; đội chưa được cấp tài khoản báo cáo.")
                        st.session_state["team_form_revision"]=revision+1
                        st.rerun()
                    except Exception as exc:
                        st.error("Không lưu được đội ("+type(exc).__name__+
                                 "). Dữ liệu nhập vẫn được giữ nguyên để kiểm tra.")
    st.markdown("#### 📍 GIAO ĐỊA BÀN CHO ĐỘI TRƯỞNG")
    assign_mode=st.radio("Phương thức phân công",
        ["Theo nhiều địa điểm (gõ tìm kiếm)", "Theo từng SKU (nâng cao)"],
        key="preview_assign_mode", horizontal=False)
    if assign_mode.startswith("Theo nhiều"):
        st.caption("ADMIN chỉ chọn đội trưởng và các địa điểm theo hợp đồng; "
                   "hệ thống tự lấy đủ các SKU và số lượng đã phân bổ. "
                   "Có thể gõ tên xã, đơn vị hoặc mã điểm để tìm ngay.")
        saved_notice=st.session_state.pop("assignment_site_notice",None)
        if saved_notice:
            st.success(saved_notice)
        all_projects=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")
                      if r.get("Mã dự án")]
        if not all_projects:
            st.info("Cần tạo dự án trước khi giao địa bàn.")
            return
        project=st.selectbox("1. Dự án",all_projects,key="site_assign_project")
        teams=[t for t in read_sheet("QUAN_LY_DOI") if
               t.get("Mã dự án")==project and t.get("Trạng thái")=="Hoạt động"
               and allowed_modes(t)]
        if not teams:
            st.warning("Dự án chưa có đội trưởng VC/LĐ đã duyệt.")
            return
        selected_team=st.selectbox("2. Đội trưởng nhận địa bàn",teams,
            format_func=lambda t:(t.get("Tên đội/đội trưởng","")+
                                  " • "+t.get("Loại nhiệm vụ","")),
            key=f"site_assign_team_{project}")
        mode_labels={"VC":"Vận chuyển (VC)", "LD":"Lắp đặt (LĐ)",
                     "VC+LD":"Cả vận chuyển và lắp đặt"}
        choices=allowed_modes(selected_team)
        role_mode=st.radio("3. Loại công việc được giao",
            choices,format_func=lambda m:mode_labels[m],
            key=f"site_assign_role_{project}_{selected_team['Mã đội']}",
            horizontal=len(choices)>1)
        kinds=("VAN_CHUYEN","LAP_DAT") if role_mode=="VC+LD" else (
            ("VAN_CHUYEN",) if role_mode=="VC" else ("LAP_DAT",))
        tasksets={tab:read_sheet(tab) for tab in kinds}
        places=read_sheet("DANH_SACH_DIEM")
        try:
            # All project locations remain searchable, including places without
            # stock yet. Eligibility is checked BEFORE confirmation.
            catalog=project_site_catalog(selected_team,role_mode,places,tasksets)
        except ValueError as exc:
            st.error(str(exc))
            return
        eligible={pid:(loc,counts) for pid,(loc,status,counts) in catalog.items()
                  if status=="Sẵn sàng giao"}
        st.caption(f"**{len(catalog)} địa điểm trong dự án** • "
                   f"{len(eligible)} điểm có nhiệm vụ chờ gán. "
                   "Có thể tìm toàn bộ xã/đơn vị; điểm chưa phân bổ hoặc "
                   "đã gán đội sẽ hiện trạng thái rõ ràng.")
        if not catalog:
            st.warning("Dự án chưa có danh sách địa điểm. "
                       "Admin cần nạp DANH_SACH_DIEM trước.")
            return
        def site_name(pid):
            loc,status,_=catalog[pid]
            name=loc.get("Tên xã/phường/đơn vị","") or pid
            return f"{name} • {pid} — {status}"
        # Sort ready sites first, then the rest; do not hide project locations.
        options=sorted(catalog,key=lambda pid:(
            catalog[pid][1]!="Sẵn sàng giao",
            (catalog[pid][0].get("Tên xã/phường/đơn vị","") or pid).casefold()))
        chosen=st.multiselect(
            "4. 🔎 Tìm và chọn nhiều địa điểm theo hợp đồng",
            options,format_func=site_name,
            placeholder="Gõ tên xã, đơn vị hoặc mã điểm để tìm...",
            key=f"site_assign_multi_{project}_{selected_team['Mã đội']}_{role_mode}")
        st.caption("Gõ tên hoặc mã điểm để lọc gợi ý. "
                   "Danh sách không biến mất khi chọn xong một điểm. "
                   "Chỉ điểm 'Sẵn sàng giao' mới được xác nhận phân công.")
        if not chosen:
            st.info("Chọn các địa điểm trong hợp đồng để kiểm tra tình trạng giao việc.")
            return
        ineligible=[pid for pid in chosen if pid not in eligible]
        st.write(f"**Đã chọn {len(chosen)} / {len(catalog)} địa điểm** "
                 f"({len(chosen)-len(ineligible)} sẵn sàng giao).")
        if ineligible:
            st.warning("Có địa điểm chưa đủ điều kiện, chưa thể xác nhận. "
                       "Vẫn có thể tìm trong danh sách nhưng cần phân bổ hàng "
                       "trước hoặc kiểm tra đội đã được giao.")
            for pid in ineligible[:15]:
                st.write("• "+site_name(pid))
            if len(ineligible)>15:
                st.caption(f"Còn {len(ineligible)-15} điểm chưa đủ điều kiện.")
            return
        try:
            planned=site_assignment_plan(
                selected_team,role_mode,chosen,places,tasksets)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.markdown("#### 5. Kiểm tra địa bàn và nhiệm vụ trước khi giao")
        counts={tab:len(rows) for tab,rows in planned.items()}
        st.write(f"**{len(chosen)} địa điểm** · "
                 f"**{sum(counts.values())} nhiệm vụ/SKU** sẽ được gán một lần.")
        summary=[]
        for pid in chosen:
            loc, by_role=eligible[pid]
            summary.append({
                "Địa điểm":loc.get("Tên xã/phường/đơn vị",""),
                "Mã điểm":pid,
                "Nhiệm vụ VC":by_role.get("VAN_CHUYEN",0),
                "Nhiệm vụ LĐ":by_role.get("LAP_DAT",0)
            })
        st.dataframe(summary,hide_index=True,use_container_width=True)
        with st.expander("Xem SKU và số lượng tại các địa điểm đã chọn"):
            for tab,rows in planned.items():
                st.write("**"+("Vận chuyển" if tab=="VAN_CHUYEN" else "Lắp đặt")+"**")
                st.dataframe([{
                    "Điểm":r.get("Mã điểm"),"SKU":r.get("SKU"),
                    "Số lượng":r.get("SL giao" if tab=="VAN_CHUYEN" else "SL lắp")
                } for r in rows],hide_index=True,use_container_width=True)
        review_key="site_contract_checked_"+hashlib.sha256(
            repr((project,selected_team["Mã đội"],role_mode,tuple(sorted(chosen)),
                  tuple(sorted((tab,r.get("Mã nhiệm vụ VC" if tab=="VAN_CHUYEN"
                         else "Mã nhiệm vụ LD")) for tab,rr in planned.items()
                         for r in rr)))).encode("utf-8")).hexdigest()[:14]
        checked=st.checkbox("Tôi đã đối chiếu các địa điểm được giao với hợp đồng.",
                            key=review_key)
        if st.button("✅ XÁC NHẬN GIAO CÁC ĐỊA ĐIỂM ĐÃ CHỌN",
                     type="primary",use_container_width=True,
                     disabled=not checked,
                     key="site_assignment_confirm"):
            try:
                # Re-read the current spreadsheet; reject stale selections.
                read_sheet.clear()
                live_teams=read_sheet("QUAN_LY_DOI")
                live_team=lookup(live_teams,"Mã đội",selected_team["Mã đội"])
                if not live_team:
                    st.error("Đội đã bị xóa hoặc thay đổi.")
                    return
                live_places=read_sheet("DANH_SACH_DIEM")
                live_tasks={tab:read_sheet(tab) for tab in kinds}
                actual=site_assignment_plan(live_team,role_mode,
                    chosen,live_places,live_tasks)
                taskkeys={"VAN_CHUYEN":"Mã nhiệm vụ VC",
                          "LAP_DAT":"Mã nhiệm vụ LD"}
                if any({r[taskkeys[tab]] for r in actual.get(tab,[])} !=
                       {r[taskkeys[tab]] for r in planned.get(tab,[])}
                       for tab in kinds):
                    st.error("Phân bổ/phân công đã thay đổi. Chưa ghi; "
                             "vui lòng đối soát rồi xác nhận lại.")
                    return
                sheetids={tab:sheet(tab).id for tab in kinds}
                updates=compact_site_assignment_requests(
                    sheetids,actual,live_team["Mã đội"])
                client()[0].batch_update({"requests":updates})
                read_sheet.clear()
                st.session_state["assignment_site_notice"]=(
                    f"Đã giao {len(chosen)} địa điểm, {sum(len(x) for x in actual.values())} "
                    f"nhiệm vụ cho đội trưởng {live_team['Tên đội/đội trưởng']}. "
                    "Không thay đổi số lượng hoặc phân bổ kho.")
                st.rerun()
            except Exception as exc:
                read_sheet.clear()
                st.error("Chưa xác nhận được kết quả ghi ("+type(exc).__name__+
                         "). KHÔNG bấm lại ngay; cần kiểm tra VAN_CHUYEN "
                         "và LAP_DAT.")
        return
    st.caption("Chế độ nâng cao: gán một SKU hoặc toàn bộ SKU của một điểm. "
               "Chỉ sử dụng khi cần phân chia nhiệm vụ cho nhiều đội.")
    tab=st.selectbox("Loại nhiệm vụ cần gán",["VAN_CHUYEN","LAP_DAT"])
    task_key = "Mã nhiệm vụ VC" if tab=="VAN_CHUYEN" else "Mã nhiệm vụ LD"
    team_key = "Mã đội VC" if tab=="VAN_CHUYEN" else "Mã đội KTV"
    required_kinds = ("VC","VC+KTV") if tab=="VAN_CHUYEN" else ("KTV","VC+KTV")
    waiting_status = "Chưa giao" if tab=="VAN_CHUYEN" else "Chưa lắp"
    all_tasks=read_sheet(tab)
    tasks=[x for x in all_tasks if x.get(task_key) and not x.get(team_key)
           and x.get("Trạng thái")==waiting_status]
    if not tasks:
        st.info("Chưa có nhiệm vụ đang chờ phân công.")
        return
    selected_task=st.selectbox("Công việc chưa gán",tasks,
        format_func=lambda x:f"{x['Mã dự án']} • {x['Mã điểm']} • {x['SKU']} • {x.get(task_key,'')}")
    teams=[x for x in read_sheet("QUAN_LY_DOI") if
           x.get("Trạng thái")=="Hoạt động"
           and x.get("Mã dự án")==selected_task.get("Mã dự án")
           and x.get("Loại nhiệm vụ") in required_kinds]
    if not teams:
        st.warning("Chưa có đội hoạt động đúng chuyên môn TRONG CÙNG DỰ ÁN.")
        return
    selected_team=st.selectbox("Đội trưởng nhận nhiệm vụ",teams,
        format_func=lambda x:x['Tên đội/đội trưởng'])
    group_site=st.checkbox("Gán tất cả SKU chưa gán tại điểm này cho cùng đội",
                           value=True, key=f"assign_entire_point_{tab}")
    try:
        preview=assignment_rows(
            all_tasks,selected_task,selected_team,task_key,team_key,
            required_kinds,waiting_status,group_site)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.write(f"**Dự kiến gán {len(preview)} dòng nhiệm vụ** cho "
             f"{selected_team['Tên đội/đội trưởng']} tại "
             f"{selected_task['Mã điểm']}.")
    with st.expander("Xem các SKU và số lượng sẽ giao"):
        for task in preview:
            st.write(f"{task['SKU']}: "
                     f"{task.get('SL giao' if tab=='VAN_CHUYEN' else 'SL lắp','')} "
                     f"({task[task_key]})")
    if st.button("✅ XÁC NHẬN GÁN ĐỘI", use_container_width=True):
        try:
            # Re-read live data to reject stale UI, other projects or wrong role.
            read_sheet.clear()
            latest_tasks=read_sheet(tab)
            latest_team=lookup(read_sheet("QUAN_LY_DOI"),"Mã đội",
                               selected_team["Mã đội"])
            if not latest_team:
                st.error("Đội không còn tồn tại.")
                return
            selected_live=lookup(latest_tasks,task_key,selected_task[task_key])
            if not selected_live:
                st.error("Không tìm thấy nhiệm vụ được chọn.")
                return
            now_rows=assignment_rows(
                latest_tasks,selected_live,latest_team,task_key,team_key,
                required_kinds,waiting_status,group_site)
            if {x[task_key] for x in now_rows}!={x[task_key] for x in preview}:
                st.error("Danh sách nhiệm vụ đã thay đổi; không gán. "
                         "Vui lòng kiểm tra và xác nhận lại.")
                return
            batch=assignment_batch_requests(sheet(tab).id,now_rows,
                                            latest_team["Mã đội"])
            client()[0].batch_update({"requests":batch})
            read_sheet.clear()
            st.success(f"Đã gán {len(now_rows)} dòng cho đội "
                       f"{latest_team['Mã đội']} tại {selected_task['Mã điểm']}. "
                       "Chỉ đội trưởng được cấp tài khoản mới báo cáo được.")
            st.rerun()
        except Exception as exc:
            read_sheet.clear()
            st.error("Chưa xác nhận được kết quả ghi ("+type(exc).__name__+
                     "). Không bấm lại ngay; cần kiểm tra sheet "+tab+".")

def sync_progress(project_id, point_id):
    """Derived per-point summary; not a substitute for source task rows."""
    read_sheet.clear()
    vc=[r for r in read_sheet("VAN_CHUYEN") if r.get("Mã dự án")==project_id and r.get("Mã điểm")==point_id]
    ld=[r for r in read_sheet("LAP_DAT") if r.get("Mã dự án")==project_id and r.get("Mã điểm")==point_id]
    vc_done=sum(r.get("Trạng thái")=="Đã giao hàng" for r in vc)
    ld_done=sum(r.get("Trạng thái")=="Đã lắp đặt" for r in ld)
    all_done=bool(vc or ld) and vc_done==len(vc) and ld_done==len(ld)
    some_done=vc_done+ld_done>0
    status="Hoàn thành" if all_done else ("Đang thực hiện" if some_done else "Chưa thực hiện")
    loc=lookup(read_sheet("DANH_SACH_DIEM"),"Mã điểm",point_id) or {}
    current=next((r for r in read_sheet("TIEN_DO") if r.get("Mã dự án")==project_id and r.get("Mã điểm")==point_id),None)
    values=[project_id,point_id,loc.get("Tên xã/phường/đơn vị",""),len(vc),vc_done,len(ld),ld_done,status,now()]
    if current:
        sheet("TIEN_DO").update(f"A{current['_row']}:I{current['_row']}",[values],value_input_option="RAW")
    else:
        append("TIEN_DO",values)
    read_sheet.clear()

def images_to_drive(files, report_id):
    sh, cred=client()
    folder=st.secrets.get("photos_folder_id", "")
    if not folder:
        raise RuntimeError("Thiếu photos_folder_id.")
    drive=build("drive","v3",credentials=cred,cache_discovery=False)
    urls=[]
    for i, f in enumerate(files[:10]):
        img=Image.open(f)
        img=img.convert("RGB")
        img.thumbnail((1280,1280))
        buf=io.BytesIO()
        img.save(buf,format="JPEG",quality=77,optimize=True)
        buf.seek(0)
        uploaded=drive.files().create(
            body={"name":f"{report_id}_{i+1}.jpg","parents":[folder]},
            media_body=MediaIoBaseUpload(buf,mimetype="image/jpeg",resumable=False),
            fields="id,webViewLink").execute()
        urls.append(uploaded.get("webViewLink") or
                    f"https://drive.google.com/file/d/{uploaded['id']}/view")
    return urls

def hub_admin():
    """ADMIN records ONE signed physical transfer to a KTV receiving hub.

    Site quota remains in KHO_PHAN_BO; this ledger does not write 'Đã giao'
    to each commune or silently allocate goods a second time.
    """
    require_role("ADMIN")
    st.subheader("📦 Bàn giao hàng TẬP KẾT cho KTV")
    st.caption("Ví dụ: đội VC giao gộp hàng của Đồng Văn – Yên Minh – "
               "Quản Bạ tại một điểm; KTV ký biên bản giấy nhận đủ, "
               "sau đó tổ chức đi lắp từng xã. KHÔNG tính là giao tận xã.")
    projects=[p["Mã dự án"] for p in read_sheet("DANH_SACH_DU_AN")
              if p.get("Mã dự án")]
    if not projects:
        st.info("Chưa có dự án.")
        return
    if st.button("🔄 Làm mới dữ liệu tập kết",key="refresh_hub"):
        read_sheet.clear()
        st.rerun()
    with st.expander("1. Chọn dự án, đội KTV và các xã thuộc hợp đồng",
                     expanded=True):
        project=st.selectbox("Dự án",projects,index=projects.index("DA880")
                             if "DA880" in projects else 0,key="hub_project")
        teams=[t for t in read_sheet("QUAN_LY_DOI")
               if t.get("Mã dự án")==project and
               t.get("Trạng thái")=="Hoạt động" and
               t.get("Loại nhiệm vụ") in ("KTV","VC+KTV")]
        if not teams:
            st.info("Chưa có đội KTV hoạt động trong dự án. "
                    "Hãy duyệt/gán đội trước khi lập biên bản tập kết.")
            return
        team=st.selectbox("Đội KTV nhận hàng",teams,
                          format_func=lambda x:x.get("Tên đội/đội trưởng",""),
                          key="hub_ktv_team")
        vc_teams=[t for t in read_sheet("QUAN_LY_DOI")
                  if t.get("Mã dự án")==project and
                  t.get("Trạng thái")=="Hoạt động" and
                  t.get("Loại nhiệm vụ") in ("VC","VC+KTV")]
        if not vc_teams:
            st.warning("Chưa có đội VC hoạt động trong dự án. "
                       "Cần gán đội VC trước khi bàn giao tập kết.")
            return
        vc_team=st.selectbox(
            "Đội VC đã giao hàng (theo phân công)",
            vc_teams,
            format_func=lambda x:x.get("Tên đội/đội trưởng",""),
            key="hub_vc_team")
        ld_rows=read_sheet("LAP_DAT")
        points=[p for p in read_sheet("DANH_SACH_DIEM") if
                p.get("Mã dự án")==project and
                any(r.get("Mã đội KTV")==team["Mã đội"] and
                    r.get("Mã dự án")==project and
                    r.get("Mã điểm")==p.get("Mã điểm") for r in ld_rows)]
        if not points:
            waiting={r.get("Mã điểm") for r in ld_rows
                     if r.get("Mã dự án")==project and r.get("Mã điểm")
                     giver=st.text_input(
                     and not r.get("Mã đội KTV")}
            st.warning(
                f"Đội KTV **{team.get('Tên đội/đội trưởng','')}** "
                f"chưa được giao xã/đơn vị nào trong dự án **{project}**. "
                f"Dự án hiện có {len(waiting)} địa điểm còn nhiệm vụ "
                "LĐ chưa gán đội. Đây không phải lỗi phân bổ hàng.")
            st.info("Thứ tự test: **Quản lý đội / Duyệt đăng ký → "
                    "GIAO ĐỊA BÀN CHO ĐỘI TRƯỞNG → chọn dự án → "
                    "chọn đội KTV → chọn Lắp đặt (LĐ) → "
                    "chọn xã → xem bảng SKU → xác nhận giao nhiệm vụ.** "
                    "Sau đó thực hiện tương tự với đội VC trên đúng các xã, "
                    "rồi quay lại Bàn giao tập kết.")
            if st.button("📍 ĐẾN MỤC GIAO ĐỊA BÀN",
                         use_container_width=True,
                         key="hub_go_assignments"):
                st.session_state["_next_menu"]="👥 Đăng ký & quản lý đội"
                st.session_state["_next_assignment_project"]=project
                st.rerun()
            return
        lookup_names={p["Mã điểm"]:p.get("Tên xã/phường/đơn vị","")
                      for p in points}
        options=sorted(lookup_names,key=lambda k:lookup_names[k].casefold())
        selection_key=f"hub_selected_sites_{project}_{team['Mã đội']}"
        if st.button("☑️ CHỌN TẤT CẢ XÃ ĐƯỢC GIAO",
                     key=f"hub_select_all_{project}_{team['Mã đội']}",
                     use_container_width=True):
            st.session_state[selection_key]=list(options)
        selected=st.multiselect(
            "🔎 Tìm và chọn các xã trong chuyến bàn giao",
            options,format_func=lambda k:lookup_names[k],
            placeholder="Gõ tên xã; chọn một hoặc nhiều điểm...",
            key=selection_key
        )
        if not selected:
            st.info("Chọn các xã theo hợp đồng của đội trưởng KTV.")
            return
        try:
            lines,summary=hub_plan(team,selected,ld_rows,points,
                                   read_sheet("KHO_PHAN_BO"))
        except ValueError as exc:
            st.error(str(exc))
            return
        try:
            verify_vc_assignment(
                lines,vc_team["Mã đội"],read_sheet("VAN_CHUYEN"))
        except ValueError as exc:
            st.error("Chưa thể bàn giao tập kết: "+str(exc))
            return
        prior=read_sheet("BAN_GIAO_TAP_KET")
        accepted={(r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
                  for r in prior if r.get("Trạng thái")=="KTV đã nhận tại tập kết"}
        repeats=[l for l in lines if
                 (project,l["point_id"],l["sku"]) in accepted]
        st.write(f"**{len(selected)} địa điểm · {len(lines)} dòng SKU** "
                 "thuộc biên bản tập kết.")
        if repeats:
            st.error(f"Đã có {len(repeats)} dòng SKU thuộc biên bản KTV "
                     "đã nhận tại điểm tập kết. Chưa thể ghi đúp.")
            return
    with st.expander("2. Đối chiếu đủ số hàng trong chuyến giao",
                     expanded=False):
        st.caption("Số thực nhận chỉ xác nhận khi KTV đã kiểm đếm và hai "
                   "bên đã ký biên bản giấy. Trường hợp thiếu hàng hãy "
                   "tách chuyến/xã và báo ADMIN đối soát.")
        qty_ok=True
        for (sku,unit),amount in sorted(summary.items()):
            actual=st.number_input(f"{sku} ({unit}) • phải nhận {qty_label(amount)}",
                min_value=0., value=float(amount),step=1.,
                key=f"hub_qty_{project}_{team['Mã đội']}_{sku}")
            if abs(actual-float(amount))>1e-9:
                qty_ok=False
        if not qty_ok:
            st.warning("SL thực nhận khác số dự kiến. Chưa xác nhận được "
                       "toàn bộ điểm; hãy kiểm tra biên bản/chọn lại các xã.")
        st.caption("Danh sách chi tiết nằm trong bảng cuộn; không cần mở "
                   "thêm nhiều lớp biểu mẫu trên điện thoại.")
        st.dataframe([{"Xã/đơn vị":r["name"],"SKU":r["sku"],
                       "Số lượng":qty_label(r["quantity"]),"ĐVT":r["unit"]}
                      for r in lines],hide_index=True,use_container_width=True,
                     height=180)
    with st.expander("3. Điểm tập kết và BIÊN BẢN GIẤY có ký nhận",
                     expanded=False):
        area=st.text_input("Khu vực hợp đồng (địa danh cũ)",
                           placeholder="Ví dụ: Đồng Văn, Yên Minh, Quản Bạ",
                           key="hub_area")
        hub=st.text_input("Tên điểm tập kết",placeholder="Kho/địa điểm nhận hàng",
                          key="hub_name")
        address=st.text_input("Địa chỉ điểm tập kết",
                              key="hub_address")
                        (
            "Họ tên người/đội VC bàn giao trên biên bản",
            value=vc_team.get("Tên đội/đội trưởng", ""),
            key=f"hub_giver_{project}_{vc_team['Mã đội']}"
        )
        paper=st.text_input("Số biên bản bàn giao giấy",
                            key="hub_paper")
        proof=st.file_uploader(
            "📷 Ảnh biên bản giấy có chữ ký của bên giao và KTV nhận",
            type=["jpg","jpeg","png"],key="hub_scan")
        acknowledged=st.checkbox(
            "Tôi đã đối chiếu hàng THỰC NHẬN và thấy biên bản giấy có "
            "đủ chữ ký hai bên; ghi nhận đây là giao tại điểm tập kết, "
            "KHÔNG phải giao tận xã.",
            key="hub_confirm_paper")
        ready=bool(qty_ok and area.strip() and hub.strip()
                   and address.strip() and giver.strip() and paper.strip()
                   and proof and acknowledged)
        if st.button("✅ GHI NHẬN BÀN GIAO TẬP KẾT",
                     type="primary",use_container_width=True,
                     disabled=not ready,key="hub_commit"):
            try:
                read_sheet.clear()
                live_team=lookup(read_sheet("QUAN_LY_DOI"),
                                 "Mã đội",team["Mã đội"])
                if not live_team or live_team.get("Mã dự án")!=project or (
                    live_team.get("Trạng thái")!="Hoạt động"
                    or live_team.get("Loại nhiệm vụ") not in ("KTV","VC+KTV")
                ):
                    fail("Đội KTV đã thay đổi; chưa ghi dữ liệu.")
                actual,actual_sum=hub_plan(
                    live_team,selected,read_sheet("LAP_DAT"),
                    read_sheet("DANH_SACH_DIEM"),
                    read_sheet("KHO_PHAN_BO"))
                live_vc=lookup(read_sheet("QUAN_LY_DOI"),
                               "Mã đội",vc_team["Mã đội"])
                if (not live_vc or live_vc.get("Mã dự án")!=project
                        or live_vc.get("Trạng thái")!="Hoạt động"
                        or live_vc.get("Loại nhiệm vụ") not in ("VC","VC+KTV")):
                    fail("Đội VC đã thay đổi, chưa được ghi bàn giao.")
                verify_vc_assignment(
                    actual,vc_team["Mã đội"],read_sheet("VAN_CHUYEN"))
                current_set={(r["point_id"],r["sku"],str(r["quantity"]))
                             for r in actual}
                original={(r["point_id"],r["sku"],str(r["quantity"]))
                          for r in lines}
                if current_set!=original:
                    fail("Phân công/định mức đã thay đổi; đối chiếu rồi xác nhận lại.")
                # Prevent two independent delivery proofs for the same site.
                # A signed KTV hub handover is not a retroactive direct VC delivery.
                keys={(r["project"],r["point_id"],r["sku"]) for r in actual}
                direct=[r for r in read_sheet("VAN_CHUYEN")
                        if (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU")) in keys
                        and r.get("Trạng thái")=="Đã giao hàng"]
                completed=[r for r in read_sheet("LAP_DAT")
                           if (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU")) in keys
                           and r.get("Trạng thái")=="Đã lắp đặt"]
                if direct or completed:
                    fail("Một số SKU đã có xác nhận giao tận xã hoặc đã lắp xong. "
                         "Chưa được ghi trùng biên bản tập kết.")
                existed={(r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
                         for r in read_sheet_live("BAN_GIAO_TAP_KET")
                         if r.get("Trạng thái")=="KTV đã nhận tại tập kết"}
                if any((project,r["point_id"],r["sku"]) in existed
                       for r in actual):
                    fail("Các SKU này đã có biên bản tập kết; không ghi đúp.")
                batch="BG-"+uuid.uuid4().hex[:12].upper()
                urls=images_to_drive([proof],batch)
                if not urls:
                    fail("Không lưu được ảnh biên bản; chưa ghi bàn giao.")
                rows=signed_receipt_lines(batch,live_team,actual,
                    area.strip(),hub.strip(),address.strip(),
                    giver.strip(),paper.strip(),urls[0],now(),
                    vc_team_id=vc_team["Mã đội"])
                sheet("BAN_GIAO_TAP_KET").append_rows(rows,
                                                      value_input_option="RAW")
                read_sheet.clear()
                audit(auth()["username"],"BÀN GIAO TẬP KẾT",
                      "BAN_GIAO_TAP_KET",batch,"OK",
                      f"{len(selected)} điểm, {len(rows)} dòng; số giấy {paper}")
                st.success("Đã ghi biên bản tập kết. KTV nhận hàng theo "
                           "từng SKU của các xã đã chọn; chưa đánh dấu "
                           "VC giao tận xã hoặc lắp đặt xong.")
                st.rerun()
            except Exception as exc:
                read_sheet.clear()
                st.error("Chưa xác nhận ghi đủ biên bản ("+
                         type(exc).__name__+"). KHÔNG bấm lại; "
                         "ADMIN cần kiểm tra BAN_GIAO_TAP_KET.")
    st.caption("Biên bản gắn MÃ ĐỘI VC giao và MÃ ĐỘI KTV nhận. "
               "Hai bên có trách nhiệm đối soát theo từng SKU. "
               "Bảng biên bản chỉ dùng trên PREVIEW. "
               "Không thay phiếu xuất kho hoặc biên bản nghiệm thu lắp đặt.")


def report():
    a=require_role("DOI_TRUONG","ADMIN")
    st.subheader("📋 Báo cáo nhiệm vụ")
    tid=a["team_id"]
    if a["role"]=="ADMIN":
        allteams=[x["Mã đội"] for x in read_sheet("QUAN_LY_DOI") if x.get("Mã đội")]
        if not allteams:
            st.info("Chưa có đội.")
            return
        tid=st.selectbox("Kiểm thử theo mã đội (chỉ Admin)",allteams)
    if not tid:
        fail("Chưa liên kết mã đội cho tài khoản.")
    if st.button("🔄 CẬP NHẬT HÀNG VC ĐÃ GIAO",use_container_width=True,
                 key="team_report_refresh"):
        read_sheet.clear()
        st.rerun()
    all_vc=read_sheet("VAN_CHUYEN")
    all_ld=read_sheet("LAP_DAT")
    hub_rows=read_sheet("BAN_GIAO_TAP_KET")
    accepted_hub={
        (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"),
         r.get("Mã đội VC giao"))
        for r in hub_rows
        if r.get("Trạng thái")=="KTV đã nhận tại tập kết"
        and r.get("Số biên bản giấy") and r.get("Link ảnh biên bản ký")
        and r.get("Mã đội VC giao")
    }
    vc=[x for x in all_vc if x.get("Mã đội VC")==tid
        and x.get("Trạng thái")!="Đã giao hàng"
        and (x.get("Mã dự án"),x.get("Mã điểm"),x.get("SKU"),tid)
        not in accepted_hub]
    ld=[x for x in all_ld if x.get("Mã đội KTV")==tid
        and x.get("Trạng thái")!="Đã lắp đặt"]
    handover=installer_handover(tid,all_ld,all_vc,
                                read_sheet("DANH_SACH_DIEM"),hub_rows)
    status_by_site={(r["project"],r["point_id"]):r for r in handover}
    if handover:
        st.caption("Đội KTV xem nơi đã nhận hàng tập kết và các xã đã "
                   "giao trực tiếp, không nhầm hai hình thức bàn giao.")
    with st.expander("📦 1. KIỂM TRA HÀNG VC / TẬP KẾT",
                     expanded=bool(handover)):
        if handover:
            st.markdown("#### Hàng VC đã giao tận xã / KTV nhận tập kết")
            st.caption("Chỉ các địa điểm được giao cho đội LĐ này. "
                       "Số liệu VC được đối chiếu theo từng SKU và SL THỰC GIAO; "
                       "phân bổ hàng chưa phải đã giao hàng.")
            c1,c2=st.columns(2)
            c1.metric("Sẵn sàng đi lắp",
                      sum(r["ready"] for r in handover))
            c2.metric("Chưa sẵn sàng",
                      sum(r["status"] in ("Chưa giao","Đã giao một phần",
                                          "Đã tập kết một phần","Cần đối soát")
                          for r in handover))
            labels=["Tất cả","Sẵn sàng lắp","Sẵn sàng lắp (tập kết)",
                    "Đã tập kết một phần","Đã giao một phần",
                    "Chưa giao","Cần đối soát","Đã lắp xong"]
            kind=st.selectbox("Lọc trạng thái hàng VC",labels,
                              key="team_handover_filter")
            shown=[r for r in handover if kind=="Tất cả" or r["status"]==kind]
            if shown:
                st.dataframe([{
                    "Địa điểm":r["name"],"Dự án":r["project"],
                    "Tình trạng hàng":r["status"],
                    "SKU phải lắp":r["sku_count"]
                } for r in shown],hide_index=True,use_container_width=True)
                detail=st.selectbox(
                    "Xem SL hàng VC đã giao tại một điểm",
                    list(range(len(shown))),
                    format_func=lambda i:shown[i]["name"]+" • "+shown[i]["status"],
                    key="team_handover_details")
                info=shown[detail]
                st.write("**"+info["name"]+"** • "+info["project"])
                signed_hubs=[r for r in hub_rows if
                    r.get("Mã dự án")==info["project"] and
                    r.get("Mã điểm")==info["point_id"] and
                    r.get("Mã đội KTV nhận")==tid and
                    r.get("Trạng thái")=="KTV đã nhận tại tập kết"
                    and r.get("Số biên bản giấy")
                    and r.get("Link ảnh biên bản ký")]
                if signed_hubs:
                    refs=sorted(set((r.get("Điểm tập kết",""),
                                     r.get("Địa chỉ tập kết",""),
                                     r.get("Khu vực theo hợp đồng",""),
                                     r.get("Số biên bản giấy",""))
                                    for r in signed_hubs))
                    for hname,haddress,area,paper in refs:
                        st.info("📦 KTV đã nhận tại **"+hname+"**"+
                                (" — "+haddress if haddress else "")+
                                (" • "+area if area else "")+
                                ". Biên bản giấy: "+paper)
                    image=signed_hubs[0].get("Link ảnh biên bản ký","")
                    if image.startswith("https://drive.google.com/"):
                        st.link_button("📄 Xem ảnh biên bản ký nhận",
                                       image,use_container_width=True)
                # Fallback Maps search is only a candidate, not a verified pin.
                dest=next((p for p in read_sheet("DANH_SACH_DIEM")
                           if p.get("Mã dự án")==info["project"] and
                           p.get("Mã điểm")==info["point_id"]),{})
                if dest.get("Vĩ độ") and dest.get("Kinh độ"):
                    query=dest["Vĩ độ"]+","+dest["Kinh độ"]
                else:
                    query=", ".join(filter(None,[
                        info["name"],dest.get("Địa chỉ chi tiết",""),
                        dest.get("Tỉnh/Thành","")]))
                    st.caption("Chưa có GPS đã xác minh: cần kiểm tra đúng đích "
                               "trên Google Maps trước khi đi.")
                st.link_button("🧭 Xem địa điểm trên Google Maps",
                    "https://www.google.com/maps/search/?api=1&query="+quote(query),
                    use_container_width=True)
                st.dataframe([{
                    "SKU":v["sku"],"Cần lắp":v["need"],
                    "VC giao xã":v["delivered"],
                    "KTV nhận tập kết":v["hub_received"],
                    "LĐ đã lắp":v["installed"],
                    "Đủ hàng":"Có" if v["delivery_ready"] else "Chưa"
                } for v in info["details"]],hide_index=True,use_container_width=True)
                for row in info["details"]:
                    if row["issues"]:
                        st.warning(row["sku"]+": "+"; ".join(row["issues"]))
            else:
                st.info("Không có địa điểm trong trạng thái vừa lọc.")
            st.divider()
    with st.expander("📝 2. BÁO CÁO GIAO HÀNG / LẮP ĐẶT",
                     expanded=not bool(handover)):
        available=sorted(
            set((r["Mã dự án"],r["Mã điểm"]) for r in vc+ld),
            key=lambda k:(0 if status_by_site.get(k,{}).get("ready") else 1,k))
        if not available:
            st.info("Đội chưa được giao nhiệm vụ hoặc đã báo cáo hết.")
            return
        locs={p.get("Mã điểm"):p.get("Tên xã/phường/đơn vị")
              for p in read_sheet("DANH_SACH_DIEM")}
        def site_option(key):
            name=locs.get(key[1],key[1])
            summary=status_by_site.get(key)
            suffix=" • "+summary["status"] if summary else ""
            return f"{key[0]} • {name}{suffix}"
        chosen=st.selectbox("Điểm được giao để báo cáo",available,
                             format_func=site_option)
        vrows=[r for r in vc if (r["Mã dự án"],r["Mã điểm"])==chosen]
        lrows=[r for r in ld if (r["Mã dự án"],r["Mã điểm"])==chosen]
        modes=(["Đã giao hàng"] if vrows else [])+(["Đã lắp đặt"] if lrows else [])
        if vrows and lrows:
            st.caption("Đội VC+LĐ báo GIAO HÀNG trước, sau khi đã xác nhận "
                       "giao đủ mới được báo LẮP ĐẶT XONG. Hai bước lưu riêng.")
        mode=st.radio("Loại báo cáo",modes,horizontal=True)
        if mode=="Đã lắp đặt" and not site_may_complete_installation(
                chosen[0],chosen[1],lrows,all_vc,hub_rows):
            st.warning("⛔ Điểm này chưa có xác nhận VC giao tận xã HOẶC "
                       "biên bản KTV nhận tại điểm tập kết đủ tất cả SKU. "
                       "Chưa được báo LẮP XONG; cần đối soát trước.")
            return
        targets=({"VAN_CHUYEN":vrows} if mode=="Đã giao hàng" else
                 {"LAP_DAT":lrows} if mode=="Đã lắp đặt" else
                 {"VAN_CHUYEN":vrows,"LAP_DAT":lrows})
        st.write("**Thiết bị và SLHH được giao**")
        for tab,rows in targets.items():
            st.caption("VẬN CHUYỂN" if tab=="VAN_CHUYEN" else "LẮP ĐẶT")
            for r in rows:
                st.write(f"{r['SKU']} — {r['SL giao' if tab=='VAN_CHUYEN' else 'SL lắp']}")
        photos=st.file_uploader("📷 Ảnh hiện trường (bắt buộc, tối đa 10)",
                               type=["jpg","jpeg","png"],accept_multiple_files=True)
        require_gps = mode!="Đã giao hàng"
        gps=None
        if require_gps:
            st.markdown("**📍 Check-in GPS bắt buộc**")
            gps=streamlit_geolocation()
        else:
            st.caption("Vận chuyển không bắt buộc GPS check-in.")
        lat=gps.get("latitude") if isinstance(gps,dict) else None
        lon=gps.get("longitude") if isinstance(gps,dict) else None
        eligible=bool(photos) and len(photos)<=10 and (not require_gps or (lat is not None and lon is not None))
        if not eligible:
            st.info("Cần ảnh và" + (" GPS check-in." if require_gps else " đúng số ảnh quy định."))
            return
        if st.button("✅ GỬI BÁO CÁO",type="primary",use_container_width=True):
            # Server-side recheck: never trust a selected team/name from browser.
            live=[]
            for tab, rows in targets.items():
                all_rows=read_sheet(tab)
                id_col="Mã nhiệm vụ VC" if tab=="VAN_CHUYEN" else "Mã nhiệm vụ LD"
                team_col="Mã đội VC" if tab=="VAN_CHUYEN" else "Mã đội KTV"
                closed="Đã giao hàng" if tab=="VAN_CHUYEN" else "Đã lắp đặt"
                for row in rows:
                    current=lookup(all_rows,id_col,row[id_col])
                    if not current or current.get(team_col)!=tid or current.get("Mã dự án")!=chosen[0] or current.get("Mã điểm")!=chosen[1] or current.get("Trạng thái")==closed:
                        fail("Quyền báo cáo hoặc trạng thái nhiệm vụ đã thay đổi. Vui lòng tải lại.")
                    live.append((tab,current))
            # Re-read live VC status before installation; no stale/cached approval.
            if mode=="Đã lắp đặt":
                read_sheet.clear()
                fresh_ld=read_sheet("LAP_DAT")
                fresh=[lookup(fresh_ld,"Mã nhiệm vụ LD",row["Mã nhiệm vụ LD"])
                       for row in lrows]
                if any(not row or row.get("Mã đội KTV")!=tid or
                       row.get("Trạng thái")=="Đã lắp đặt" for row in fresh):
                    fail("Nhiệm vụ lắp đã đổi; không báo cáo. Hãy tải lại.")
                if not site_may_complete_installation(
                        chosen[0],chosen[1],fresh,read_sheet("VAN_CHUYEN"),
                        read_sheet("BAN_GIAO_TAP_KET")):
                    fail("Hàng VC chưa giao đủ hoặc chưa đối soát được; "
                         "không thể xác nhận lắp đặt.")
            if mode=="Đã giao hàng":
                read_sheet.clear()
                current_hub=read_sheet_live("BAN_GIAO_TAP_KET")
                confirmed={(r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
                           for r in current_hub
                           if r.get("Trạng thái")=="KTV đã nhận tại tập kết"
                           and r.get("Số biên bản giấy")
                           and r.get("Link ảnh biên bản ký")}
                if any((chosen[0],chosen[1],r.get("SKU")) in confirmed
                       for r in vrows):
                    fail("Hàng đã được KTV ký nhận tại điểm tập kết. "
                         "Không báo giao tận xã lần thứ hai.")
            rid="BC-"+uuid.uuid4().hex[:16].upper()
            p=lookup(read_sheet("DANH_SACH_DIEM"),"Mã điểm",chosen[1]) or {}
            dest=p.get("Link Google Maps") or ("https://www.google.com/maps/search/?api=1&query="+quote(p.get("Tên xã/phường/đơn vị",chosen[1])))
            maps=(f"https://www.google.com/maps?q={lat},{lon}" if require_gps else dest)
            sku_text=", ".join(f"{row['SKU']}:{row['SL giao' if tab=='VAN_CHUYEN' else 'SL lắp']}" for tab,row in live)
            try:
                urls=images_to_drive(photos,rid)
                row_index=len(sheet("BAO_CAO_TRIEN_KHAI").get_all_values())+1
                append("BAO_CAO_TRIEN_KHAI",[rid,now(),chosen[0],chosen[1],tid,mode,
                    ", ".join(row["Mã nhiệm vụ VC" if tab=="VAN_CHUYEN" else "Mã nhiệm vụ LD"] for tab,row in live),
                    sku_text,", ".join(urls),maps,lat if lat is not None else "",lon if lon is not None else "",
                    "Theo phân bổ","Cần đối soát","Đang cập nhật trạng thái"])
                for tab,row in live:
                    status="Đã giao hàng" if tab=="VAN_CHUYEN" else "Đã lắp đặt"
                    sheet(tab).update(f"H{row['_row']}:N{row['_row']}",
                      [[status,now(),", ".join(urls),maps,rid,
                        row["SL giao" if tab=="VAN_CHUYEN" else "SL lắp"],""]],
                      value_input_option="RAW")
                sync_progress(chosen[0],chosen[1])
                sheet("BAO_CAO_TRIEN_KHAI").update(
                     f"N{row_index}:O{row_index}",[[READY,""]],value_input_option="RAW")
                read_sheet.clear()
                audit(a["username"],"GỬI BÁO CÁO","BAO_CAO_TRIEN_KHAI",rid,"OK")
                st.success("Đã gửi báo cáo và đồng bộ trạng thái thành công.")
            except Exception as e:
                read_sheet.clear()
                audit(a["username"],"GỬI BÁO CÁO","BAO_CAO_TRIEN_KHAI",rid,"CẦN ĐỐI SOÁT",type(e).__name__)
                st.error(f"Chưa xác nhận được đồng bộ hoàn tất ({type(e).__name__}). Liên hệ Admin; không gửi lại liên tục.")

def dashboard():
    """Read-only progress dashboard: strictly ADMIN / LANH_DAO."""
    a=require_role("ADMIN","LANH_DAO")
    st.subheader("📊 Báo cáo tiến độ dự án")
    st.caption("Chỉ ADMIN và LÃNH ĐẠO xem toàn dự án. "
               "Số liệu theo nhiệm vụ và báo cáo đã ghi vào Google Sheets; "
               "chưa phải biên bản nghiệm thu hay đối soát xuất kho vật lý.")
    if st.button("🔄 CẬP NHẬT SỐ LIỆU",use_container_width=True,
                 key="leadership_refresh"):
        read_sheet.clear()
        st.rerun()
    projects=read_sheet("DANH_SACH_DU_AN")
    ids=[p["Mã dự án"] for p in projects if p.get("Mã dự án")]
    if not ids:
        st.info("Chưa có dự án để báo cáo.")
        return
    options=ids+["Tất cả"]
    preferred=ids.index("DA880") if "DA880" in ids else 0
    project=st.selectbox("Dự án cần xem",options,index=preferred,
                         key="leadership_project")
    progress=build_progress(
        project,projects,
        read_sheet("DANH_SACH_DIEM"),
        read_sheet("NHAP_KHO"),
        read_sheet("KHO_PHAN_BO"),
        read_sheet("VAN_CHUYEN"),
        read_sheet("LAP_DAT"),
        read_sheet("BAO_CAO_TRIEN_KHAI"),
        read_sheet("QUAN_LY_DOI"),
        read_sheet("BAN_GIAO_TAP_KET")
    )
    m=progress["metrics"]
    total=m["sites"]
    st.caption("Số liệu đọc lúc "+now().replace("T"," ")[:19]+
               " (giờ Việt Nam). Nhấn CẬP NHẬT để lấy dữ liệu mới nhất.")
    st.markdown("#### 1. Tổng quan tiến độ")
    a1,a2=st.columns(2)
    a1.metric("Điểm dự án",m["sites"])
    a2.metric("Đã phân bổ hàng",m["sites_allocated"])
    b1,b2=st.columns(2)
    b1.metric("VC giao tận xã đủ",m["sites_delivered"])
    b2.metric("LĐ đã lắp đủ",m["sites_installed"])
    h1,h2=st.columns(2)
    h1.metric("VC bàn giao tập kết đủ",m["sites_vc_hub_done"])
    h2.metric("KTV nhận tập kết đủ",m["sites_at_hub"])
    st.caption("Hai số tập kết tính theo SỐ XÃ có đủ SKU; "
               "một biên bản ký tại một điểm tập kết có thể gồm nhiều xã. "
               "Không phải số chuyến xe hay số điểm giao tận xã.")
    st.metric("Đủ hàng, chờ/đang lắp",m["sites_ready_install"])
    if total:
        st.write(f"**VC giao TẬN XÃ đủ: {m['sites_delivered']}/{total} điểm** "
                 f"({m['sites_delivered']/total:.1%})")
        st.progress(min(1.,m["sites_delivered"]/total))
        st.write(f"**Lắp đặt đủ: {m['sites_installed']}/{total} điểm** "
                 f"({m['sites_installed']/total:.1%})")
        st.progress(min(1.,m["sites_installed"]/total))
    with st.expander("Chi tiết nhiệm vụ và việc chưa giao đội",expanded=False):
        st.write(f"VC báo giao tận xã: **{m['vc_tasks_done']}/{m['vc_tasks']}** nhiệm vụ/SKU. "
                 f"VC bàn giao tập kết đủ: **{m['sites_vc_hub_done']}** địa điểm "
                 "(xác nhận theo biên bản có mã đội VC).")
        st.write(f"LĐ báo hoàn thành: **{m['ld_tasks_done']}/{m['ld_tasks']}** nhiệm vụ/SKU.")
        st.write(f"Nhiệm vụ VC chưa có đội: **{m['vc_unassigned']}**; "
                 f"LĐ chưa có đội: **{m['ld_unassigned']}**.")
        st.caption("VC giao tận xã và KTV nhận hàng ở điểm tập kết là "
                   "HAI chỉ tiêu khác nhau. Lắp đặt hoàn thành cần báo cáo "
                   "tại xã với ảnh/GPS và hàng đã giao đủ theo một trong hai "
                   "hình thức. Số nhiệm vụ không phải số xã hoàn thành.")

    if progress["pending_report_count"]:
        st.warning(f"⚠️ Có {progress['pending_report_count']} báo cáo chưa đồng bộ "
                   "hoặc cần ADMIN đối soát. Không coi các báo cáo này là nghiệm thu.")
    if progress["anomalies"]:
        with st.expander(f"⚠️ Cần kiểm tra dữ liệu ({len(progress['anomalies'])} cảnh báo)"):
            for issue in progress["anomalies"][:30]:
                st.write("• "+issue)
            if len(progress["anomalies"])>30:
                st.caption("Còn các cảnh báo khác; ADMIN cần kiểm tra Google Sheets.")

    st.markdown("#### 2. Tra cứu tiến độ từng xã/đơn vị")
    sites=progress["sites"]
    statuses=["Tất cả"]+sorted({p["status"] for p in sites})
    f1,f2=st.columns([1,1])
    status=f1.selectbox("Trạng thái",statuses,key="leadership_status")
    search=f2.text_input("🔎 Tìm địa điểm",placeholder="Tên xã, đơn vị hoặc mã điểm...",
                         key="leadership_search")
    needle=search.casefold().strip()
    matching=[p for p in sites if
              (status=="Tất cả" or p["status"]==status)
              and (not needle or needle in p["name"].casefold()
                   or needle in p["point_id"].casefold()
                   or needle in p["project"].casefold())]
    st.caption(f"Đang hiển thị {len(matching)} / {len(sites)} địa điểm.")
    if matching:
        st.dataframe([{
            "Địa điểm":p["name"],
            "Dự án":p["project"],
            "VC đủ SKU":f"{p['vc_done']}/{p['sku_count']}",
            "LĐ đủ SKU":f"{p['ld_done']}/{p['sku_count']}",
            "Tình trạng":p["status"]
        } for p in matching],hide_index=True,use_container_width=True)
        selected_site=st.selectbox("Xem chi tiết một địa điểm",
            list(range(len(matching))),
            format_func=lambda i:(matching[i]["name"]+
                                  " • "+matching[i]["project"]+
                                  " • "+matching[i]["status"]),
            key="leadership_site_detail")
        site=matching[selected_site]
        st.write("**"+site["name"]+"** • "+site["point_id"])
        st.write(f"**VC:** {', '.join(site['vc_teams']) or 'Chưa gán đội'}")
        st.write(f"**LĐ:** {', '.join(site['ld_teams']) or 'Chưa gán đội'}")
        if site["skus"]:
            st.dataframe([{
                "SKU":item["sku"],"SL phân bổ":display_amount(item["planned"]),
                "VC giao tận xã":display_amount(item["delivered"]),
                "KTV nhận tập kết":display_amount(item["hub"]),
                "LĐ đã báo lắp":display_amount(item["installed"])
            } for item in site["skus"]],hide_index=True,use_container_width=True)
        else:
            st.info("Địa điểm chưa được phân bổ hàng.")
    else:
        st.info("Không có địa điểm khớp điều kiện tìm kiếm.")

    st.markdown("#### 3. Nhập kho – Phân bổ – Giao – Lắp theo SKU")
    st.caption("VC giao tận xã và KTV nhận tập kết được báo riêng, "
               "KHÔNG cộng hai lần. ĐVT theo từng SKU; "
               "'Còn chờ phân bổ' không phải tồn kho vật lý.")
    if progress["skus"]:
        st.dataframe(progress["skus"],hide_index=True,use_container_width=True)
    else:
        st.info("Chưa có dữ liệu nhập kho/phân bổ của dự án.")

    st.markdown("#### 4. Báo cáo hiện trường gần đây")
    activity=progress["activity"]
    if activity:
        st.dataframe([{
            "Thời gian":str(r.get("Thời gian máy chủ","")).replace("T"," ")[:19],
            "Dự án":r.get("Mã dự án",""),
            "Mã điểm":r.get("Mã điểm",""),
            "Đội":r.get("Mã đội",""),
            "Nội dung":r.get("Loại báo cáo",""),
            "Đồng bộ":r.get("Trạng thái đồng bộ","")
        } for r in activity],hide_index=True,use_container_width=True)
        st.caption("Bảng tóm tắt 40 báo cáo mới nhất. Bấm chọn "
                   "một báo cáo dưới đây để xem bằng chứng kèm theo.")
        index=st.selectbox(
            "Xem chi tiết một báo cáo hiện trường",
            list(range(len(activity))),
            format_func=lambda i:(
                str(activity[i].get("Thời gian máy chủ",""))[:19].replace("T"," ")
                +" • "+str(activity[i].get("Loại báo cáo",""))
                +" • "+str(activity[i].get("Mã báo cáo",""))),
            key="leadership_report_detail"
        )
        record=activity[index]
        with st.container(border=True):
            st.write("**Báo cáo:** "+str(record.get("Mã báo cáo","")))
            st.write("**Đội:** "+str(record.get("Mã đội","")))
            st.write("**Dự án/điểm:** "+str(record.get("Mã dự án",""))+
                     " / "+str(record.get("Mã điểm","")))
            st.write("**Nội dung:** "+str(record.get("Loại báo cáo","")))
            st.write("**SKU và SL thực tế:** "+
                     str(record.get("Danh sách SKU:SL thực tế") or "Chưa ghi"))
            st.write("**Kết quả đối soát:** "+
                     str(record.get("Kết quả đối soát") or "Chưa ghi"))
            st.write("**Trạng thái đồng bộ:** "+
                     str(record.get("Trạng thái đồng bộ") or "Chưa ghi"))
            if record.get("Ghi chú"):
                st.caption("Ghi chú: "+str(record.get("Ghi chú")))
            def safe_evidence_url(raw,kind="image"):
                parsed=urlparse(str(raw).strip())
                hosts=({"drive.google.com","docs.google.com",
                         "lh3.googleusercontent.com","storage.googleapis.com"}
                       if kind=="image" else
                       {"www.google.com","google.com","maps.google.com"})
                return str(raw).strip() if (parsed.scheme=="https" and
                                            parsed.hostname in hosts) else ""
            photos=str(record.get("Link ảnh") or "").split(",")
            image_links=[safe_evidence_url(x) for x in photos]
            image_links=[x for x in image_links if x][:10]
            if image_links:
                for i,photo in enumerate(image_links,1):
                    st.link_button(f"📷 Xem ảnh hiện trường {i}",photo,
                                   use_container_width=True)
            else:
                st.caption("Báo cáo chưa có liên kết ảnh được xác minh.")
            url=safe_evidence_url(record.get("Link Google Maps"),"map")
            if url:
                st.link_button("📍 Xem vị trí báo cáo trên Maps",url,
                               use_container_width=True)
            st.caption("Ảnh Drive có thể yêu cầu quyền xem riêng. "
                       "Không có nút sửa/xóa hoặc duyệt từ màn hình này.")
    else:
        st.info("Chưa có báo cáo hiện trường. "
                "Phân bổ và gán đội không được tính là đã giao/lắp.")
    st.caption("Báo cáo chỉ đọc. ADMIN xử lý nhập kho, phân bổ, phân công "
               "và đối soát tại các chức năng riêng; LÃNH ĐẠO không được sửa dữ liệu.")

def main():
    try:
        # Public help is a separate bookmarkable page inside the PREVIEW app.
        # It has no backend reads/writes and does not bypass role permissions.
        if st.query_params.get("guide") == "1":
            render_guide()
            return
        _, guide_col = st.columns([2.5, 1.5])
        with guide_col:
            if st.button("📖 Hướng dẫn sử dụng",
                         key="open_help_from_home",
                         help="Xem cách đăng ký, giao hàng, lắp đặt và thực hành thử",
                         use_container_width=True):
                st.query_params["guide"] = "1"
                st.rerun()
        view=menu()
        if view=="__LEADERSHIP_LOGIN__":leadership_login()
        elif view=="__TEAM_LOGIN__":login(team_only=True)
        elif view=="🔐 Đăng nhập ADMIN / tài khoản khác":login()
        elif view=="📝 Đăng ký tham gia":register()
        elif view=="📝 Đăng ký hộ đội trưởng":register(on_behalf=True)
        elif view=="🗺️ Tìm đường":directions()
        elif view=="📁 Dự án/Điểm/Nhập kho":projects_and_inventory()
        elif view=="📦 Phân bổ":allocate()
        elif view=="👥 Đăng ký & quản lý đội":teams_and_approval()
        elif view=="📦 Bàn giao tập kết":hub_admin()
        elif view=="📋 Báo cáo nhiệm vụ":report()
        elif view=="📊 Báo cáo tiến độ":dashboard()
    except Exception as e:
        st.error("Không thể truy cập dữ liệu Preview: "+type(e).__name__)
        st.caption("Kiểm tra Secrets, quyền Google Sheets và thư mục ảnh; không dùng khóa cũ đã lộ.")
if __name__=="__main__":
    main()
