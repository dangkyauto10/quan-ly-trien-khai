# QUAN LY DU AN — PREVIEW 2026-10-22
# Staged only: never deploy to production without user approval.
import io
import json
import uuid
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote

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
from preview_bulk_allocation import (
    inventory_by_sku, build_plan, verify_plan, atomic_requests
)
from io import BytesIO
from openpyxl import Workbook as ExcelWorkbook
from preview_import_locations import (read_location_file, candidate_names,
    column_choice, is_header, normalize_name, blank_excel_template)

st.set_page_config(page_title="QUẢN LÝ DỰ ÁN • PREVIEW", page_icon="🚀", layout="centered")

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
            account = verify_remember_token(cookie, st.secrets.get("accounts", {}), key)
            if account:
                st.session_state["auth"] = account



st.markdown("""
<style>
.block-container {max-width: 620px; padding: 1.5rem 1rem 3rem;}
.tdv-hero {
  text-align: center;
  padding: 0.45rem 0.25rem 1.05rem;
  margin: 0 auto 0.45rem;
}
.tdv-hero-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  color: #173A73;
  font-weight: 800;
  font-size: clamp(1.45rem, 4.6vw, 1.95rem);
  line-height: 1.35;
  letter-spacing: -0.025em;
  white-space: nowrap;
}
.tdv-hero-icon {font-size: 1.25rem; line-height: 1; flex-shrink: 0;}
.tdv-hero-subtitle {
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.8rem;
  line-height: 1.5;
}
.tdv-preview-tag {
  display: inline-block;
  margin-top: 0.55rem;
  padding: 0.22rem 0.7rem;
  border: 1px solid #dbe5f2;
  background: #f5f8fc;
  border-radius: 999px;
  color: #526581;
  font-size: 0.66rem;
  line-height: 1.5;
  letter-spacing: 0.02em;
}
@media (max-width: 480px) {
  .block-container {padding-top: 1.15rem;}
  .tdv-hero-title {font-size: 1.38rem; gap: 0.35rem;}
  .tdv-hero-icon {font-size: 1.05rem;}
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tdv-hero">
  <div class="tdv-hero-title"><span class="tdv-hero-icon" aria-hidden="true">🚀</span><span>QUẢN LÝ DỰ ÁN</span></div>
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

def valid_login(username, pin):
    accounts = st.secrets.get("accounts", {})
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
                "team_id": str(info.get("team_id", ""))}
    count = record["count"] + 1
    locks[username] = {"count": count, "until": time.time() + 900 if count >= 5 else 0}
    return None

def login():
    with st.form("login_form_preview"):
        username = st.text_input("Mã tài khoản")
        pin = st.text_input("Mã truy cập riêng", type="password")
        remember_key = remember_signing_key()
        remember = st.checkbox(
            "Ghi nhớ đăng nhập trên thiết bị này (30 ngày)",
            value=False, disabled=not bool(remember_key),
            help="Chỉ chọn trên điện thoại hoặc máy tính cá nhân; đừng chọn ở máy dùng chung.")
        if remember_key is None:
            st.caption("Chức năng ghi nhớ sẽ bật sau khi Admin cấu hình remember_login_secret trong Secrets.")
        if st.form_submit_button("ĐĂNG NHẬP", use_container_width=True):
            user = valid_login(username.strip(), pin)
            if not user:
                st.error("Thông tin không hợp lệ hoặc tài khoản tạm khóa.")
            else:
                st.session_state["auth"] = user
                if remember and remember_key:
                    account = st.secrets["accounts"][user["username"]]
                    st.session_state["_remember_token"] = issue_remember_token(
                        user["username"], account, remember_key)
                    st.session_state["_remember_action"] = "set"
                else:
                    # Prevent an old remembered account from being restored later.
                    st.session_state["_remember_action"] = "remove"
                st.rerun()

def auth():
    a = st.session_state.get("auth")
    if not a:
        return None
    accounts = st.secrets.get("accounts", {})
    cur = accounts.get(a["username"])
    if not cur or str(cur.get("role", "")).upper() != a["role"]:
        st.session_state.pop("auth", None)
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
    if not a:
        opts = ["🔐 Đăng nhập", "📝 Đăng ký tham gia"]
    elif a["role"] == "ADMIN":
        opts = ["📊 Điều hành", "📁 Dự án/Điểm/Nhập kho", "📦 Phân bổ",
                "👥 Đăng ký & quản lý đội", "📝 Đăng ký hộ thành viên",
                "📋 Báo cáo nhiệm vụ", "🗺️ Tìm đường"]
    elif a["role"] == "LANH_DAO":
        opts = ["📊 Điều hành", "🗺️ Tìm đường"]
    elif a["role"] == "DOI_TRUONG":
        opts = ["📋 Báo cáo nhiệm vụ", "🗺️ Tìm đường"]
    else:
        opts = ["🗺️ Tìm đường"]
    if a:
        st.caption(f"Đã đăng nhập: {a['username']} • {a['role']}")
        if st.button("Đăng xuất"):
            st.session_state.pop("auth", None)
            st.session_state["_remember_action"] = "remove"
            st.rerun()
    return st.selectbox("CHỌN CHỨC NĂNG", opts)

def register(on_behalf=False):
    """Public registration and Admin-assisted registration use the same pending queue."""
    acting_admin = require_role("ADMIN") if on_behalf else None
    st.subheader("📝 " + ("ADMIN đăng ký hộ thành viên" if on_behalf else "Đăng ký tham gia dự án"))
    st.caption("Khai khu vực đã hợp đồng với công ty. Đây là thông tin đăng ký, "
               "không tự cấp quyền báo cáo; ADMIN sẽ xét duyệt và giao nhiệm vụ.")
    saved_notice = st.session_state.pop("registered_notice", None)
    if saved_notice:
        st.success(saved_notice)
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
             "Điều phối / Giám sát", "Kho vận / Hậu cứ"])
        vehicle = st.selectbox("Phương tiện", ["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        st.caption("Khu vực tự khai chỉ để ADMIN tham khảo khi phân công. "
                   "Chỉ điểm được giao chính thức mới có thể báo cáo.")
        if st.form_submit_button("GỬI ĐĂNG KÝ" if not on_behalf else
                                 "GỬI HỒ SƠ ĐĂNG KÝ HỘ", use_container_width=True):
            normalized_phone = "".join(c for c in phone if c.isdigit())
            described_areas = ", ".join(area + ([area_other.strip()] if area_other.strip() else []))
            if len(full_name.strip()) < 3 or len(normalized_phone) not in (9,10,11):
                st.error("Vui lòng kiểm tra họ tên và số điện thoại (9–11 chữ số).")
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
                    st.warning("Hồ sơ của người này đã được gửi cho dự án này. "
                               "Không tạo bản đăng ký trùng.")
                else:
                    rid = "DK-" + uuid.uuid4().hex[:12].upper()
                    submitter = ("ADMIN:" + acting_admin["username"]) if acting_admin else "Tự đăng ký"
                    try:
                        date_serial = sheet_datetime_serial()
                        sheet("DANG_KY_THANH_VIEN").append_row(
                            [rid, date_serial, full_name.strip(),
                             normalized_phone, described_areas, specialty, vehicle,
                             "Chờ duyệt", "", "", "", project, submitter],
                            value_input_option="RAW")
                        read_sheet.clear()
                        st.session_state["registered_notice"] = (
                            f"Đã nhận hồ sơ {rid} — đang chờ ADMIN duyệt. "
                            "Hồ sơ chưa được cấp quyền báo cáo.")
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
            st.info("Tên điểm mới chưa có tọa độ. Admin cần kiểm tra vị trí trên "
                    "Google Maps trước khi dùng chức năng chỉ đường chính thức.")
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
    with st.form("new_master", clear_on_submit=True):
        if choice == "Dự án":
            code = st.text_input("Mã dự án")
            name = st.text_input("Tên dự án")
            deadline = st.date_input("Hạn hoàn thành")
        elif choice == "Địa điểm":
            code = st.text_input("Mã điểm duy nhất")
            project = st.selectbox("Dự án", ids)
            name = st.text_input("Tên xã/phường/đơn vị")
            address = st.text_input("Địa chỉ chi tiết")
            province = st.text_input("Tỉnh/Thành")
            route = st.text_input("Tuyến/Khu vực")
            latitude = st.text_input("Vĩ độ (nếu có)")
            longitude = st.text_input("Kinh độ (nếu có)")
        else:
            project = st.selectbox("Dự án", ids)
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
                st.success("Đã lưu vào Google Sheets Preview.")
            except Exception as e:
                st.error(f"Lưu thất bại: {type(e).__name__}")

def read_sheet_live(name):
    """Bypass Streamlit's short cache for the final stock/duplicate check."""
    values = sheet(name).get_all_values()
    if not values:
        return []
    headers = values[0]
    return [dict(zip(headers, row + [""] * (len(headers)-len(row))), _row=i)
            for i, row in enumerate(values[1:], 2) if any(str(x).strip() for x in row)]


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
    st.subheader("📦 Phân bổ hàng loạt – đa mặt hàng")
    st.caption("SKU tự lấy từ NHAP_KHO của từng dự án. Số lượng 0 nghĩa là "
               "điểm đó không nhận mặt hàng. Chỉ ADMIN xác nhận mới ghi dữ liệu.")
    prows = read_sheet("DANH_SACH_DU_AN")
    projects = [r["Mã dự án"] for r in prows if r.get("Mã dự án")]
    if not projects:
        st.warning("Cần tạo dự án trước.")
        return
    project = st.selectbox("Dự án", projects, key="bulk_project")
    points = [r for r in read_sheet("DANH_SACH_DIEM")
              if r.get("Mã dự án") == project and r.get("Mã điểm")
              and r.get("Trạng thái") == "Hoạt động"]
    imports = read_sheet("NHAP_KHO")
    allocations = read_sheet("KHO_PHAN_BO")
    inventory, inventory_issues = inventory_by_sku(project, imports, allocations)
    if inventory_issues:
        for issue in inventory_issues:
            st.error(issue)
        st.warning("Phải đối soát kho trước khi phân bổ.")
        return
    if not points or not inventory:
        st.warning("Dự án cần có danh sách địa điểm và ít nhất một SKU trong NHAP_KHO.")
        return
    point_by_id = {r["Mã điểm"]:r for r in points}
    point_ids = list(point_by_id)
    names = {pid:point_by_id[pid]["Tên xã/phường/đơn vị"] for pid in point_ids}
    skus = list(inventory)
    st.write(f"**{len(point_ids)} điểm** • **{len(skus)} SKU** có trong dự án")
    st.markdown("#### 1. Định mức chung cho từng SKU")
    defaults = {}
    for sku in skus:
        itm = inventory[sku]
        st.caption(f"{sku} — {itm['name']} • Tồn khả dụng: "
                   f"{itm['remaining']:g} {itm['unit']}")
        defaults[sku] = st.number_input(
            f"Định mức {sku} / điểm ({itm['unit']})", min_value=0.0,
            value=0.0, step=1.0, format="%.3f",
            key=f"bulk_default_{project}_{sku}")
    chosen_ids = st.multiselect("2. Điểm được đưa vào đợt phân bổ",
        point_ids, default=point_ids,
        format_func=lambda pid: f"{names[pid]} • {pid}",
        key=f"bulk_points_{project}")
    if not chosen_ids:
        st.info("Vui lòng chọn địa điểm cần phân bổ.")
        return
    st.markdown("#### 3. Điều chỉnh những đơn vị có định mức khác")
    exceptions = st.multiselect("Chọn các điểm ngoại lệ (có thể nhiều hoặc ít hơn 15)",
        chosen_ids, format_func=lambda pid:f"{names[pid]} • {pid}",
        key=f"bulk_exception_{project}")
    overrides = {}
    if exceptions:
        source_rows = []
        for pid in exceptions:
            row = {"Mã điểm":pid,"Tên địa điểm":names[pid]}
            row.update({sku:float(defaults[sku]) for sku in skus})
            source_rows.append(row)
        ui_key = hashlib.sha256(
            repr((project, sorted(exceptions),
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
    st.warning("Chỉ bấm XÁC NHẬN khi đã đối chiếu lượng hàng từng SKU và "
               "các xã/đơn vị ngoại lệ. Không thể ghi trùng SKU tại cùng điểm.")
    accepted = st.checkbox("Tôi đã kiểm tra định mức và tồn kho; đồng ý tạo "
                           "nhiệm vụ vận chuyển, lắp đặt.",
                           key=f"bulk_approved_{project}")
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

def teams_and_approval():
    require_role("ADMIN")
    st.subheader("👥 Quản lý đội / Duyệt đăng ký")
    pending=[x for x in read_sheet("DANG_KY_THANH_VIEN") if x.get("Trạng thái duyệt")=="Chờ duyệt"]
    all_projects=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN") if r.get("Mã dự án")]
    if not pending:
        st.info("Hiện không có hồ sơ chờ duyệt.")
    for p in pending:
        rid=p["Mã đăng ký"]
        kind=role_for_specialty(p.get("Chuyên môn", ""))
        st.write(f"**{p['Họ tên']}** • {p['Chuyên môn']} • Mã {rid}")
        if not kind:
            st.warning("Chuyên môn này chưa được tự tạo đội VC/KTV. Admin cần xử lý riêng.")
            continue
        if not all_projects:
            st.warning("Cần tạo dự án trước khi duyệt tạo đội.")
            continue
        chosen_project=st.selectbox("Dự án nhận đội",all_projects,
            key="approve_project_"+rid)
        st.caption("Địa bàn đăng ký chỉ là đề xuất; Admin sẽ gán điểm thực hiện riêng.")
        if st.button("DUYỆT & TẠO ĐỘI "+kind,key="approve_"+rid):
            # Re-read before writing, so repeated clicks/retries cannot create two teams.
            read_sheet.clear()
            live=lookup(read_sheet("DANG_KY_THANH_VIEN"),"Mã đăng ký",rid)
            if not live or live.get("Trạng thái duyệt")!="Chờ duyệt":
                st.warning("Hồ sơ đã được xử lý. Tải lại để xem trạng thái.")
                st.stop()
            if chosen_project not in [r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")]:
                st.error("Dự án không còn tồn tại, chưa ghi dữ liệu.")
                st.stop()
            teams_now=read_sheet("QUAN_LY_DOI")
            matches=matching_teams(teams_now,name=live["Họ tên"],
                phone=live["Số điện thoại"],kind=kind,project=chosen_project)
            if len(matches)>1:
                st.error("Có nhiều đội trùng người và dự án; cần Admin xử lý trước khi duyệt.")
                st.stop()
            tid=(matches[0]["Mã đội"] if matches else
                 team_id_from_registration(rid,kind))
            existing=lookup(teams_now,"Mã đội",tid)
            if existing and (existing.get("Tên đội/đội trưởng")!=live["Họ tên"]
                             or existing.get("SĐT đội trưởng")!=live["Số điện thoại"]
                             or existing.get("Loại nhiệm vụ")!=kind
                             or existing.get("Mã dự án")!=chosen_project
                             or existing.get("Trạng thái")!="Hoạt động"):
                st.error("Đội đã có nhưng thông tin hoặc trạng thái chưa khớp. Cần Admin đối soát.")
                st.stop()
            try:
                if not existing:
                    append("QUAN_LY_DOI",[tid,live["Họ tên"],live["Số điện thoại"],
                           kind,"","Hoạt động",chosen_project,
                           "Duyệt từ "+rid+"; chưa cấp đăng nhập"])
                sheet("DANG_KY_THANH_VIEN").update(
                    f"H{live['_row']}:K{live['_row']}",
                    [["Đã duyệt",tid,auth()["username"],sheet_datetime_serial()]],value_input_option="RAW")
                read_sheet.clear()
                audit(auth()["username"],"DUYỆT & TẠO ĐỘI","QUAN_LY_DOI",tid,"OK",rid)
                st.success(("Đã duyệt và liên kết đội có sẵn " if matches else
                            "Đã duyệt và tạo đội ") + tid + ". "
                           "Chưa cấp quyền đăng nhập hoặc phân công điểm.")
                st.rerun()
            except Exception as exc:
                read_sheet.clear()
                st.error("Chưa hoàn tất việc duyệt ("+type(exc).__name__+"). "
                         "Hãy kiểm tra hai sheet trước khi thao tác lại.")
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
    st.markdown("#### Gán nhiệm vụ theo mã đội")
    tab=st.selectbox("Loại nhiệm vụ cần gán",["VAN_CHUYEN","LAP_DAT"])
    tasks=[x for x in read_sheet(tab) if x.get("Mã nhiệm vụ VC" if tab=="VAN_CHUYEN" else "Mã nhiệm vụ LD") and not x.get("Mã đội VC" if tab=="VAN_CHUYEN" else "Mã đội KTV")]
    teams=[x for x in read_sheet("QUAN_LY_DOI") if x.get("Trạng thái")=="Hoạt động" and (x.get("Loại nhiệm vụ") in (["VC","VC+KTV"] if tab=="VAN_CHUYEN" else ["KTV","VC+KTV"]))]
    if tasks and teams:
        r=st.selectbox("Công việc chưa gán",tasks,format_func=lambda x:f"{x['Mã dự án']} • {x['Mã điểm']} • {x['SKU']}")
        t=st.selectbox("Đội trưởng nhận nhiệm vụ",teams,format_func=lambda x:f"{x['Mã đội']} • {x['Tên đội/đội trưởng']}")
        if st.button("GÁN ĐỘI"):
            sheet(tab).update_cell(r["_row"],7,t["Mã đội"])
            read_sheet.clear()
            st.success("Đã gán. Đội trưởng sẽ thấy nhiệm vụ của mình.")
            st.rerun()
    else:
        st.info("Không có công việc chờ gán hoặc chưa có đội đúng chuyên môn.")

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
    vc=[x for x in read_sheet("VAN_CHUYEN") if x.get("Mã đội VC")==tid and x.get("Trạng thái")!="Đã giao hàng"]
    ld=[x for x in read_sheet("LAP_DAT") if x.get("Mã đội KTV")==tid and x.get("Trạng thái")!="Đã lắp đặt"]
    available=sorted(set((r["Mã dự án"],r["Mã điểm"]) for r in vc+ld))
    if not available:
        st.info("Đội chưa được giao nhiệm vụ hoặc đã báo cáo hết.")
        return
    locs={p.get("Mã điểm"):p.get("Tên xã/phường/đơn vị") for p in read_sheet("DANH_SACH_DIEM")}
    chosen=st.selectbox("Điểm được giao",available,
        format_func=lambda x:f"{x[0]} • {locs.get(x[1],x[1])}")
    vrows=[r for r in vc if (r["Mã dự án"],r["Mã điểm"])==chosen]
    lrows=[r for r in ld if (r["Mã dự án"],r["Mã điểm"])==chosen]
    modes=(["Đã giao hàng"] if vrows else [])+(["Đã lắp đặt"] if lrows else [])
    if vrows and lrows:
        modes.append("Giao & lắp đặt xong")
    mode=st.radio("Loại báo cáo",modes,horizontal=True)
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
    require_role("ADMIN","LANH_DAO")
    st.subheader("📊 Điều hành – Thống kê")
    projects=read_sheet("DANH_SACH_DU_AN")
    points=read_sheet("DANH_SACH_DIEM")
    vc=read_sheet("VAN_CHUYEN")
    ld=read_sheet("LAP_DAT")
    reports=read_sheet("BAO_CAO_TRIEN_KHAI")
    codes=["Tất cả"]+[p["Mã dự án"] for p in projects if p.get("Mã dự án")]
    chosen=st.selectbox("Dự án",codes)
    filt=lambda rows:[x for x in rows if chosen=="Tất cả" or x.get("Mã dự án")==chosen]
    vc,ld,reports,points=map(filt,(vc,ld,reports,points))
    c1,c2=st.columns(2)
    c1.metric("Nhiệm vụ đã giao",sum(x.get("Trạng thái")=="Đã giao hàng" for x in vc))
    c2.metric("Nhiệm vụ đã lắp",sum(x.get("Trạng thái")=="Đã lắp đặt" for x in ld))
    c3,c4=st.columns(2)
    c3.metric("Số điểm trong dự án",len({x.get("Mã điểm") for x in points if x.get("Mã điểm")}))
    c4.metric("Báo cáo cần đối soát",sum(x.get("Trạng thái đồng bộ")!=READY for x in reports))
    if chosen=="Tất cả":
        st.caption("Thống kê nhiệm vụ không phải số địa điểm hoàn thành.")

def main():
    try:
        view=menu()
        if view=="🔐 Đăng nhập":login()
        elif view=="📝 Đăng ký tham gia":register()
        elif view=="📝 Đăng ký hộ thành viên":register(on_behalf=True)
        elif view=="🗺️ Tìm đường":directions()
        elif view=="📁 Dự án/Điểm/Nhập kho":projects_and_inventory()
        elif view=="📦 Phân bổ":allocate()
        elif view=="👥 Đăng ký & quản lý đội":teams_and_approval()
        elif view=="📋 Báo cáo nhiệm vụ":report()
        elif view=="📊 Điều hành":dashboard()
    except Exception as e:
        st.error("Không thể truy cập dữ liệu Preview: "+type(e).__name__)
        st.caption("Kiểm tra Secrets, quyền Google Sheets và thư mục ảnh; không dùng khóa cũ đã lộ.")
if __name__=="__main__":
    main()
