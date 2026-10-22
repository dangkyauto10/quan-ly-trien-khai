"""Deterministic mappings for Preview registration approval (no credentials)."""

def role_for_specialty(specialty: str) -> str:
    value = str(specialty or "").strip().casefold()
    transport = "vận chuyển" in value or "giao nhận" in value
    installation = "ktv" in value or "lắp đặt" in value
    if transport and installation:
        return "VC+KTV"
    if transport:
        return "VC"
    if installation:
        return "KTV"
    return ""

def team_id_from_registration(registration_id: str, kind: str) -> str:
    rid = str(registration_id or "").strip().upper()
    kind = str(kind or "").strip().upper()
    if not rid.startswith("DK-") or kind not in {"VC", "KTV", "VC+KTV"}:
        raise ValueError("Không thể sinh mã đội từ đăng ký.")
    prefix = "VC-LD" if kind == "VC+KTV" else kind
    return prefix + "-" + rid[3:]


def clean_phone(value: str) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())


def clean_name(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def matching_teams(rows, *, name: str, phone: str, kind: str, project: str):
    """Return exact identity+assignment matches for reconciliation."""
    return [
        row for row in rows
        if clean_name(row.get("Tên đội/đội trưởng")) == clean_name(name)
        and clean_phone(row.get("SĐT đội trưởng")) == clean_phone(phone)
        and clean_phone(phone)
        and row.get("Loại nhiệm vụ") == kind
        and row.get("Mã dự án") == project
    ]


def approval_requests(registration_sheet_id, team_sheet_id, row_number,
                      decision, team_row, team_id, approver, timestamp):
    """One atomic spreadsheets.batchUpdate for approval/rejection.

    team_row must be a complete list of 8 columns for a new approved team,
    or None for a linked existing team or rejected registration.
    """
    if decision not in ("Đã duyệt", "Từ chối") or row_number < 2:
        raise ValueError("Trạng thái hoặc dòng đăng ký không hợp lệ.")
    if decision == "Đã duyệt" and not team_id:
        raise ValueError("Duyệt phải có mã đội liên kết.")
    if decision == "Từ chối" and (team_id or team_row):
        raise ValueError("Từ chối không được tạo đội.")
    if team_row and (decision != "Đã duyệt" or len(team_row) != 8 or
                     team_row[0] != team_id):
        raise ValueError("Dữ liệu đội không khớp.")
    def cell_text(value):
        return {"userEnteredValue":{"stringValue":str(value if value is not None else "")}}
    req = []
    if team_row:
        req.append({"appendCells":{
            "sheetId":team_sheet_id,
            "rows":[{"values":[cell_text(x) for x in team_row]}],
            "fields":"userEnteredValue"
        }})
    req.append({"updateCells":{
        "range":{"sheetId":registration_sheet_id,
                 "startRowIndex":row_number-1,"endRowIndex":row_number,
                 "startColumnIndex":7,"endColumnIndex":11},
        "rows":[{"values":[
            cell_text(decision),
            cell_text(team_id),
            cell_text(approver),
            {"userEnteredValue":{"numberValue":float(timestamp)}}
        ]}],
        "fields":"userEnteredValue"
    }})
    return req
