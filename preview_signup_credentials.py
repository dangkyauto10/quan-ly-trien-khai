"""Pending user-selected password workflow for captain registration (PREVIEW).

Only PBKDF2 salt/hash are persisted; passwords are never written to Sheets.
Approval binds pending credential to the exact registration and approved team.
"""
import re
from preview_credential_accounts import create_hash

WAITING="Chờ duyệt"
ACTIVATED="Đã kích hoạt"
REJECTED="Đã từ chối"
HEADERS=("Mã đăng ký","Mã dự án","Salt hex","Mã băm PBKDF2",
         "Trạng thái","Thời gian đăng ký","Ghi chú")


def text_cell(v):
    return {"userEnteredValue":{"stringValue":str(v if v is not None else "")}}


def registration_requests(registration_sheet_id, pending_sheet_id,
                          registration_row, credential_row):
    """Append registration and pending hash in the same Sheets batch."""
    if len(registration_row)!=13 or len(credential_row)!=7:
        raise ValueError("Invalid registration payload.")
    if (registration_row[0]!=credential_row[0] or
            registration_row[11]!=credential_row[1] or
            registration_row[7]!="Chờ duyệt" or
            credential_row[4]!=WAITING):
        raise ValueError("Registration and password do not match.")
    if not valid_secret_fields(credential_row[2],credential_row[3]):
        raise ValueError("Invalid salted secret.")
    def append(sheet_id,values):
        return {"appendCells":{
            "sheetId":sheet_id,
            "rows":[{"values":[text_cell(x) for x in values]}],
            "fields":"userEnteredValue"
        }}
    return [append(registration_sheet_id,registration_row),
            append(pending_sheet_id,credential_row)]


def pending_for_registration(registration_id, project, pending_rows):
    rows=[x for x in pending_rows if x.get("Mã đăng ký")==registration_id]
    if not rows:
        return None  # Legacy registration from before password signup.
    if len(rows)!=1:
        raise ValueError("Trùng mật khẩu chờ duyệt, cần ADMIN đối soát.")
    row=rows[0]
    if (row.get("Mã dự án")!=project or
            row.get("Trạng thái")!=WAITING or
            not valid_secret_fields(row.get("Salt hex"),row.get("Mã băm PBKDF2")) or
            not isinstance(row.get("_row"),int) or row["_row"]<2):
        raise ValueError("Hồ sơ mật khẩu chờ duyệt không nhất quán.")
    return row


def valid_secret_fields(salt,digest):
    return bool(re.fullmatch(r"[0-9a-f]{32}",str(salt or "")) and
                re.fullmatch(r"[0-9a-f]{64}",str(digest or "")))


def pending_row(registration_id, project, password, timestamp):
    salt,digest=create_hash(password)
    return [registration_id,project,salt,digest,WAITING,timestamp,
            "Chỉ mã băm, không lưu mật khẩu gốc"]


def approval_credential_requests(pending_sheet_id,credential_sheet_id,
                                 pending_record,credential_row=None,
                                 rejected=False):
    """Atomic addition to a team account and final pending-state update."""
    if not pending_record or not isinstance(pending_record.get("_row"),int):
        raise ValueError("Cannot finalize ungrounded pending password.")
    if rejected == bool(credential_row):
        raise ValueError("Specify activation row OR rejection.")
    if credential_row is not None:
        if len(credential_row)!=10 or credential_row[3]!="DOI_TRUONG" or (
            credential_row[4]!=pending_record.get("Salt hex") or
            credential_row[5]!=pending_record.get("Mã băm PBKDF2") or
            credential_row[6]!="Hoạt động" or
            not str(credential_row[0]).startswith("tdv_")
        ):
            raise ValueError("Approved account does not match pending password.")
    requests=[]
    if credential_row is not None:
        requests.append({"appendCells":{
            "sheetId":credential_sheet_id,
            "rows":[{"values":[text_cell(v) for v in credential_row]}],
            "fields":"userEnteredValue"
        }})
    requests.append({"updateCells":{
        "range":{"sheetId":pending_sheet_id,
                 "startRowIndex":pending_record["_row"]-1,
                 "endRowIndex":pending_record["_row"],
                 "startColumnIndex":4,"endColumnIndex":5},
        "rows":[{"values":[text_cell(REJECTED if rejected else ACTIVATED)]}],
        "fields":"userEnteredValue"
    }})
    return requests
