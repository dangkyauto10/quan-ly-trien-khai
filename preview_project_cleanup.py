"""Project-scoped PREVIEW data reset; never mutate app or spreadsheet schema."""

import hashlib
import json
import re


# Every row in these operational sheets belongs to exactly one project.
OPERATIONAL_TABS = (
    "NHAP_KHO", "DM_CHUAN", "KHO_PHAN_BO",
    "DANG_KY_THANH_VIEN", "QUAN_LY_DOI", "TAI_KHOAN_DOI",
    "MAT_KHAU_DANG_KY", "LIEN_KET_DANG_KY_DOI",
    "VAN_CHUYEN", "LAP_DAT", "BAN_GIAO_TAP_KET",
    "BAO_CAO_TRIEN_KHAI", "TIEN_DO",
)
MASTER_TABS = ("DANH_SACH_DU_AN", "DANH_SACH_DIEM")
AUDIT_TAB = "NHAT_KY_HE_THONG"
ALL_TABS = MASTER_TABS + OPERATIONAL_TABS + (AUDIT_TAB,)
PROJECT_FIELDS = {"DANG_KY_THANH_VIEN": "Mã dự án đăng ký"}
RESET = "RESET"
DELETE = "DELETE"


def _project_rows(grid, project, project_field="Mã dự án"):
    if not grid:
        raise ValueError("Thiếu hàng tiêu đề hoặc sheet chưa được cấu hình.")
    headers = [str(x).strip() for x in grid[0]]
    if headers.count(project_field) != 1:
        raise ValueError("Cột " + project_field + " bị thiếu hoặc bị trùng.")
    project_col = headers.index(project_field)
    return [(i, list(row)) for i, row in enumerate(grid[1:], start=2)
            if project_col < len(row) and str(row[project_col]).strip() == project]


def _audit_rows(grid, project, known_ids):
    """Only remove historical logs explicitly traceable to this project."""
    if not grid:
        raise ValueError("Thiếu hàng tiêu đề của nhật ký.")
    headers = [str(x).strip() for x in grid[0]]
    if headers.count("Mã đối tượng") != 1:
        raise ValueError("Thiếu cột Mã đối tượng trong nhật ký.")
    target_col = headers.index("Mã đối tượng")
    # Match DA880, DA880_x, but not the *different* project DA880B.
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(project) +
                         r"(?![A-Za-z0-9])")
    return [(i, list(row)) for i, row in enumerate(grid[1:], start=2)
            if (target_col < len(row) and str(row[target_col]).strip() in known_ids)
            or any(pattern.search(str(value)) for value in row[3:])]


def make_cleanup_plan(project, mode, grids):
    """Create an exact-match, read-only row plan with a tamper/staleness digest.

    The input is a dict of sheet title -> Google Sheets values matrix. The
    function fails closed on any unknown project, absent sheet, or bad header.
    """
    if mode not in (RESET, DELETE):
        raise ValueError("Chế độ xóa không hợp lệ.")
    if not isinstance(project, str) or not project.strip() or project != project.strip():
        raise ValueError("Mã dự án không hợp lệ.")
    missing = [tab for tab in ALL_TABS if tab not in grids]
    if missing:
        raise ValueError("Thiếu sheet bắt buộc: " + ", ".join(missing))
    matched = {}
    # Validate every sheet even in RESET: the selection must come from the
    # project master, not merely a similarly named string in another sheet.
    for tab in MASTER_TABS + OPERATIONAL_TABS:
        try:
            matched[tab] = _project_rows(
                grids[tab], project,
                project_field=PROJECT_FIELDS.get(tab, "Mã dự án"))
        except ValueError as exc:
            raise ValueError(f"{tab}: {exc}") from exc
    if len(matched["DANH_SACH_DU_AN"]) != 1:
        raise ValueError("Dự án không tồn tại hoặc có mã dự án trùng; không xóa.")
    # Collect only unambiguous foreign keys belonging to this project.
    identifiers = set()
    for tab, field in (("DANH_SACH_DIEM", "Mã điểm"),
                       ("QUAN_LY_DOI", "Mã đội"),
                       ("DANG_KY_THANH_VIEN", "Mã đăng ký")):
        header = [str(v).strip() for v in grids[tab][0]]
        if field not in header:
            raise ValueError(f"{tab}: thiếu cột {field}.")
        col = header.index(field)
        own_ids = {str(row[col]).strip() for _, row in matched[tab]
                   if len(row) > col and str(row[col]).strip()}
        own_numbers = {number for number, _ in matched[tab]}
        other_ids = {str(row[col]).strip()
                     for number, row in enumerate(grids[tab][1:], start=2)
                     if len(row) > col and str(row[col]).strip()
                     and number not in own_numbers}
        identifiers.update(own_ids - other_ids)
    matched[AUDIT_TAB] = _audit_rows(grids[AUDIT_TAB], project, identifiers)
    targets = (MASTER_TABS + OPERATIONAL_TABS + (AUDIT_TAB,)) if mode == DELETE \
        else OPERATIONAL_TABS + (AUDIT_TAB,)
    rows = {tab: matched[tab] for tab in targets}
    digest_payload = {"project": project, "mode": mode,
                      "rows": rows}
    signature = hashlib.sha256(json.dumps(
        digest_payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"project": project, "mode": mode,
            "rows": rows, "counts": {tab: len(rows[tab]) for tab in targets},
            "total": sum(map(len, rows.values())), "signature": signature}


def cleanup_requests(plan, sheet_ids):
    """One atomic Sheets batch: clear target *row values*, leave grid intact."""
    missing = [tab for tab in plan["rows"] if tab not in sheet_ids]
    if missing:
        raise ValueError("Không xác định được sheet: " + ", ".join(missing))
    requests = []
    for tab, entries in plan["rows"].items():
        numbers = sorted(set(row_no for row_no, _ in entries))
        if not numbers:
            continue
        start = last = numbers[0]
        ranges = []
        for row_no in numbers[1:]:
            if row_no == last + 1:
                last = row_no
            else:
                ranges.append((start, last))
                start = last = row_no
        ranges.append((start, last))
        for first, last in ranges:
            requests.append({"repeatCell": {
                "range": {"sheetId": int(sheet_ids[tab]),
                          "startRowIndex": first - 1, "endRowIndex": last},
                "cell": {}, "fields": "userEnteredValue,note"}})
    return requests


def _fetch_current_grids(spreadsheet):
    """Live reads (no Streamlit cache) of all project-owned data tables."""
    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    missing = [tab for tab in ALL_TABS if tab not in worksheets]
    if missing:
        raise ValueError("Thiếu bảng: " + ", ".join(missing))
    ranges = [f"'{tab}'!A:{_column_label(worksheets[tab].col_count)}"
              for tab in ALL_TABS]
    payload = spreadsheet.values_batch_get(ranges)
    value_ranges = payload.get("valueRanges", [])
    if len(value_ranges) != len(ALL_TABS):
        raise ValueError("Không đọc được đủ các bảng dữ liệu.")
    grids = {tab: vr.get("values", [])
             for tab, vr in zip(ALL_TABS, value_ranges)}
    return grids, {tab: worksheets[tab].id for tab in ALL_TABS}


def _column_label(number):
    if not isinstance(number, int) or number < 1:
        raise ValueError("Số cột của Google Sheets không hợp lệ.")
    label = ""
    while number:
        number, digit = divmod(number - 1, 26)
        label = chr(65 + digit) + label
    return label


def _lock_for_cleanup():
    import threading
    import streamlit as st

    @st.cache_resource
    def lock():
        return threading.Lock()
    return lock()


def project_cleanup_admin(require_role, valid_login, client, read_sheet,
                          audit):
    """ADMIN-only project RESET/DELETE page, with a live two-step preview."""
    import streamlit as st

    who = require_role("ADMIN")
    st.subheader("🧹 RESET / XÓA DỮ LIỆU THEO DỰ ÁN")
    st.info("Chọn đúng một dự án. Không ảnh hưởng dự án khác, biểu mẫu, "
            "cấu trúc Google Sheets hoặc chức năng phần mềm.")
    notice = st.session_state.pop("_cleanup_result", None)
    if notice:
        st.success(notice)

    projects = sorted({str(r.get("Mã dự án", "")).strip()
                       for r in read_sheet("DANH_SACH_DU_AN")
                       if str(r.get("Mã dự án", "")).strip()})
    if not projects:
        st.info("Chưa có dự án để thực hiện thao tác.")
        return
    project = st.selectbox("Chọn dự án", projects, key="cleanup_project_code")
    options = {
        "RESET — xóa số liệu để chạy lại từ đầu": RESET,
        "XÓA DỰ ÁN — xóa toàn bộ dữ liệu và địa điểm của dự án": DELETE,
    }
    selected = st.radio("Chọn một trong hai thao tác", list(options),
                        key="cleanup_action_type")
    mode = options[selected]
    if mode == RESET:
        st.warning("RESET: xóa dữ liệu nhập kho, danh mục hàng, số lượng phân "
                   "bổ, đội/thành viên/tài khoản, nhiệm vụ, bàn giao, báo cáo "
                   "và tiến độ. GIỮ mã dự án và danh sách địa điểm.")
    else:
        st.error("XÓA DỰ ÁN: xóa tất cả các dữ liệu trên VÀ cả hồ sơ dự án, "
                 "danh sách địa điểm. Không thể chọn lại dự án này sau khi xóa.")

    if st.button("🔎 BƯỚC 1 — XEM TRƯỚC SỐ LIỆU SẼ XÓA",
                 key="cleanup_preview_button", use_container_width=True):
        try:
            spreadsheet, _ = client()
            grids, _ = _fetch_current_grids(spreadsheet)
            plan = make_cleanup_plan(project, mode, grids)
            st.session_state["_cleanup_verified_preview"] = {
                "project": project, "mode": mode,
                "signature": plan["signature"], "counts": plan["counts"],
                "total": plan["total"]}
            st.rerun()
        except Exception as exc:
            st.error("Chưa đọc được đầy đủ dữ liệu: " + str(exc))
            return

    preview = st.session_state.get("_cleanup_verified_preview", {})
    if preview.get("project") != project or preview.get("mode") != mode:
        st.caption("Cần bấm BƯỚC 1 để xem chính xác dữ liệu của thao tác này.")
        return
    st.markdown(f"**XEM TRƯỚC — {project} • {mode} • "
                f"{preview['total']} dòng dữ liệu**")
    st.dataframe([{"Bảng": tab, "Số dòng sẽ xóa": count}
                  for tab, count in preview["counts"].items()],
                 hide_index=True, use_container_width=True)
    if not preview["total"]:
        st.info("Không có số liệu thuộc dự án này cần xóa.")
        return

    with st.form("cleanup_confirm_form", clear_on_submit=True):
        typed = st.text_input("Nhập lại chính xác mã dự án để xác nhận")
        password = st.text_input("Nhập lại mật khẩu ADMIN", type="password")
        confirmation = st.checkbox(
            "Tôi xác nhận xóa đúng dữ liệu của dự án đã chọn; "
            "hiểu rằng không có nút hoàn tác.")
        submitted = st.form_submit_button(
            "⚠️ BƯỚC 2 — XÁC NHẬN " +
            ("RESET DỰ ÁN" if mode == RESET else "XÓA TOÀN BỘ DỰ ÁN"),
            use_container_width=True)
    if not submitted:
        return
    if typed.strip() != project or not confirmation or not password:
        st.error("Chưa đủ xác nhận: kiểm tra mã dự án, ô xác nhận và mật khẩu.")
        return
    # This re-authenticates against the same PBKDF2 account store as login.
    verified = valid_login(who["username"], password)
    if not verified or verified.get("role") != "ADMIN" or (
            verified.get("username") != who["username"]):
        st.error("Mật khẩu ADMIN không chính xác hoặc tài khoản đang bị khóa.")
        return

    with _lock_for_cleanup():
        try:
            # Reject stale previews and independently re-check permissions.
            who_live = require_role("ADMIN")
            if who_live["username"] != who["username"]:
                raise ValueError("Phiên ADMIN đã thay đổi; phải xác nhận lại.")
            spreadsheet, _ = client()
            live_grids, ids = _fetch_current_grids(spreadsheet)
            live = make_cleanup_plan(project, mode, live_grids)
            if live["signature"] != preview["signature"]:
                st.session_state.pop("_cleanup_verified_preview", None)
                st.error("Dữ liệu đã thay đổi từ lúc xem trước. "
                         "Không xóa; hãy bấm BƯỚC 1 xem lại.")
                return
            requests = cleanup_requests(live, ids)
            if not requests:
                st.info("Không có dữ liệu để xóa.")
                return
            # One atomic Sheets write. No sequential per-tab clearing.
            spreadsheet.batch_update({"requests": requests})
            read_sheet.clear()
            st.session_state.pop("_cleanup_verified_preview", None)
            audit(who["username"], "RESET DỰ ÁN" if mode == RESET
                  else "XÓA DỰ ÁN", "DANH_SACH_DU_AN", project,
                  "OK", f"{live['total']} dòng; {len(requests)} vùng")
            st.session_state["_cleanup_result"] = (
                f"Đã {'RESET' if mode == RESET else 'XÓA DỰ ÁN'} "
                f"{project}: {live['total']} dòng thuộc dự án. "
                "Không thay đổi dữ liệu của dự án khác.")
            st.rerun()
        except Exception as exc:
            read_sheet.clear()
            st.error("CHƯA XÁC NHẬN ĐƯỢC VIỆC XÓA (" +
                     type(exc).__name__ + "). KHÔNG BẤM LẠI NGAY. "
                     "ADMIN cần làm mới và xem trước lần nữa; nếu cần, "
                     "kiểm tra dữ liệu Google Sheets.")
