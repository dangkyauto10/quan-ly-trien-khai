# QUAN LY DU AN — PREVIEW 2026-10-22
# Staged only: never deploy to production without user approval.
import io
import uuid
import hmac
import hashlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="QUẢN LÝ DỰ ÁN • PREVIEW", page_icon="🚀", layout="centered")
st.title("🚀 QUẢN LÝ DỰ ÁN")
st.caption("BẢN PREVIEW — CHƯA ĐƯỢC NGHIỆM THU / CHƯA VẬN HÀNH")

st.markdown("""
<style>
.block-container {max-width: 620px; padding: 1.3rem 1rem 3rem;}
h1 {color: #163C88; font-weight: 850; text-align: center; font-size: 2rem;}
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


SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"]
READY = "Đã đồng bộ"

def now():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(timespec="seconds")

def fail(message):
    st.error(message)
    st.stop()

@st.cache_resource
def client():
    if "gcp_service_account" not in st.secrets or "spreadsheet_id" not in st.secrets:
        raise RuntimeError("Thiếu cấu hình kết nối Google Sheets trong Streamlit Secrets.")
    info = dict(st.secrets["gcp_service_account"])
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
    with st.form("auth"):
        username = st.text_input("Mã tài khoản")
        pin = st.text_input("Mã truy cập riêng", type="password")
        if st.form_submit_button("ĐĂNG NHẬP", use_container_width=True):
            user = valid_login(username.strip(), pin)
            if not user:
                st.error("Thông tin không hợp lệ hoặc tài khoản tạm khóa.")
            else:
                st.session_state["auth"] = user
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
    a = auth()
    if not a:
        opts = ["🔐 Đăng nhập", "📝 Đăng ký tham gia"]
    elif a["role"] == "ADMIN":
        opts = ["📊 Điều hành", "📁 Dự án/Điểm/Nhập kho", "📦 Phân bổ",
                "👥 Đăng ký & quản lý đội", "📋 Báo cáo nhiệm vụ", "🗺️ Tìm đường"]
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
            st.rerun()
    return st.selectbox("CHỌN CHỨC NĂNG", opts)

def register():
    st.subheader("📝 Đăng ký tham gia dự án")
    points = read_sheet("DANH_SACH_DIEM")
    with st.form("registration", clear_on_submit=True):
        full_name = st.text_input("Họ tên *")
        phone = st.text_input("Điện thoại liên hệ *")
        area = st.multiselect("Địa bàn đề xuất",
             sorted(set(r.get("Tên xã/phường/đơn vị", "") for r in points if r.get("Tên xã/phường/đơn vị"))))
        specialty = st.selectbox("Chuyên môn",
             ["Vận chuyển / Giao nhận", "KTV lắp đặt", "Điều phối / Giám sát", "Kho vận / Hậu cứ"])
        vehicle = st.selectbox("Phương tiện", ["Xe máy", "Xe tải", "Xe bán tải", "Khác"])
        if st.form_submit_button("GỬI ĐĂNG KÝ", use_container_width=True):
            if len(full_name.strip()) < 3 or not phone.strip().isdigit() or len(phone.strip()) < 9:
                st.error("Kiểm tra lại họ tên và số điện thoại.")
            else:
                rid = "DK-" + uuid.uuid4().hex[:12].upper()
                try:
                    append("DANG_KY_THANH_VIEN", [rid, now(), full_name.strip(), phone.strip(),
                           ", ".join(area), specialty, vehicle, "Chờ duyệt", "", "", ""])
                    st.success("Đã nhận đăng ký. Admin sẽ kiểm tra và duyệt.")
                except Exception as e:
                    st.error(f"Không gửi được đăng ký: {type(e).__name__}")

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

def projects_and_inventory():
    require_role("ADMIN")
    st.subheader("📁 Danh mục do Admin quản lý")
    choice = st.radio("Nhập mới", ["Dự án", "Địa điểm", "Hàng nhập kho"], horizontal=True)
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

def allocate():
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
    for p in pending:
        st.write(f"**{p['Họ tên']}** • {p['Số điện thoại']} • {p['Chuyên môn']}")
        if st.button("Duyệt "+p["Mã đăng ký"],key=p["Mã đăng ký"]):
            sheet("DANG_KY_THANH_VIEN").update(f"H{p['_row']}:K{p['_row']}",
                      [["Đã duyệt","",""+auth()["username"],now()]],value_input_option="RAW")
            read_sheet.clear()
            st.success("Đã duyệt hồ sơ. Admin cần tạo/gán tài khoản đội trưởng riêng.")
            st.rerun()
    with st.form("team"):
        tid=st.text_input("Mã đội mới")
        name=st.text_input("Tên đội / Đội trưởng")
        phone=st.text_input("SĐT đội trưởng")
        kind=st.selectbox("Loại nhiệm vụ",["VC","KTV","VC+KTV"])
        proj=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN") if r.get("Mã dự án")]
        project=st.selectbox("Dự án",proj)
        if st.form_submit_button("THÊM ĐỘI"):
            if not tid or not name or lookup(read_sheet("QUAN_LY_DOI"),"Mã đội",tid):
                fail("Mã đội đã tồn tại hoặc thiếu tên.")
            append("QUAN_LY_DOI",[tid,name,phone,kind,"","Hoạt động",project,""])
            st.success("Đã thêm đội. Cần cấp tài khoản trong Secrets trước khi cho báo cáo.")
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
