"""Deterministic mappings for Preview registration approval (no credentials)."""

def role_for_specialty(specialty: str) -> str:
    value = str(specialty or "").strip().casefold()
    if "vận chuyển" in value or "giao nhận" in value:
        return "VC"
    if "ktv" in value or "lắp đặt" in value:
        return "KTV"
    return ""

def team_id_from_registration(registration_id: str, kind: str) -> str:
    rid = str(registration_id or "").strip().upper()
    kind = str(kind or "").strip().upper()
    if not rid.startswith("DK-") or not kind in {"VC", "KTV"}:
        raise ValueError("Không thể sinh mã đội từ đăng ký.")
    return kind + "-" + rid[3:]
