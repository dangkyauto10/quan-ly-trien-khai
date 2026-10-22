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
