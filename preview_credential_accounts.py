"""Preview-only team credentials, separate from privileged Secrets accounts.

The credential sheet stores PBKDF2 salted hashes, NEVER passwords.
Only approved, active team identities may authenticate through these records.
A compromised credential row may impersonate one team, but can never create
ADMIN/LANH_DAO roles. Keep this worksheet private to system administrators.
"""
import hashlib
import hmac
import re
import secrets
from collections import Counter
from collections.abc import Mapping

STATUS_ACTIVE = "Hoạt động"
ROLE_TEAM = "DOI_TRUONG"
HEADERS = (
    "Mã tài khoản", "Mã đội", "Mã dự án", "Vai trò",
    "Salt hex", "Mã băm PBKDF2", "Trạng thái",
    "Cập nhật lúc", "ADMIN cấp", "Ghi chú",
)
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#"


def new_password(length=18):
    if length < 14:
        raise ValueError("Password too short.")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def validate_custom_password(password, full_name="", phone=""):
    """Validate memorable user-requested passphrase without storing it.

    Unicode letters are permitted, including Vietnamese. Long phrases with
    mixed words and digits are easier to remember than short PINs.
    """
    if not isinstance(password, str):
        return "Mật khẩu chưa hợp lệ."
    if len(password)<6 or len(password)>128:
        return "Mật khẩu cần từ 6 đến 128 ký tự."
    if password != password.strip():
        return "Không nhập khoảng trắng ở đầu hoặc cuối mật khẩu."
    if any(ord(ch)<32 or ord(ch)==127 for ch in password):
        return "Mật khẩu không được chứa ký tự điều khiển/xuống dòng."
    if not any(ch.isalpha() for ch in password):
        return "Mật khẩu phải có chữ cái."
    if not any(ch.isdigit() for ch in password):
        return "Mật khẩu cần có ít nhất một chữ số."
    compact="".join(ch for ch in password.casefold() if ch.isalnum())
    if any(x in compact for x in ("123456","654321","password",
                                "matkhau","qwerty","abcdef",
                                "admin123","111111","000000")):
        return "Mật khẩu quá dễ đoán hoặc có chuỗi đơn giản. Hãy chọn cụm từ khác."
    # Block name/phone substring in both accented and unaccented forms.
    from unicodedata import normalize
    def fold(value):
        return "".join(
            c for c in normalize("NFKD", str(value).casefold())
            if c.isalnum() and not (0x300 <= ord(c) <= 0x36f)
        ).replace("đ","d")
    candidate=fold(password)
    fullname=fold(full_name)
    if len(fullname)>=5 and fullname in candidate:
        return "Không dùng họ và tên đội trưởng làm một phần của mật khẩu."
    phone_digits="".join(c for c in str(phone) if c.isdigit())
    if len(phone_digits)>=6 and phone_digits[-6:] in "".join(c for c in password if c.isdigit()):
        return "Không dùng số điện thoại làm mật khẩu."
    return None


def create_hash(password, salt=None):
    if not isinstance(password, str) or len(password) < 6:
        raise ValueError("Password too short.")
    salt = salt if salt is not None else secrets.token_hex(16)
    if not re.fullmatch(r"[0-9a-fA-F]{32}", salt):
        raise ValueError("Invalid salt.")
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 390000
    ).hex()
    return salt.lower(), digest


def team_accounts(secret_accounts, credential_rows, teams):
    """Merge trusted Secrets and active sheet-backed team accounts only.

    Fail closed for duplicate account IDs/team IDs and mismatched project/team.
    Privileged roles can ONLY come from trusted Streamlit Secrets.
    """
    accounts = dict(secret_accounts or {})
    active_teams = {}
    duplicate_teams = set()
    for t in teams or ():
        team_id = str(t.get("Mã đội", "")).strip()
        if not team_id or t.get("Trạng thái") != STATUS_ACTIVE:
            continue
        if team_id in active_teams:
            duplicate_teams.add(team_id)
        active_teams[team_id] = t
    counter_ids = Counter()
    counter_teams = Counter()
    valid = []
    for r in credential_rows or ():
        username = str(r.get("Mã tài khoản", "")).strip()
        tid = str(r.get("Mã đội", "")).strip()
        project = str(r.get("Mã dự án", "")).strip()
        status = str(r.get("Trạng thái", "")).strip()
        role = str(r.get("Vai trò", "")).strip()
        salt = str(r.get("Salt hex", "")).strip().lower()
        digest = str(r.get("Mã băm PBKDF2", "")).strip().lower()
        if status != STATUS_ACTIVE:
            continue
        counter_ids[username] += 1
        counter_teams[tid] += 1
        t = active_teams.get(tid)
        if (not username.startswith("tdv_") or username in accounts
                or not tid or tid in duplicate_teams or not t
                or not project or project != t.get("Mã dự án")
                or role != ROLE_TEAM
                or not re.fullmatch(r"[0-9a-f]{32}", salt)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            continue
        valid.append((username, tid, salt, digest))
    for username, tid, salt, digest in valid:
        if counter_ids[username] != 1 or counter_teams[tid] != 1:
            continue
        accounts[username] = {
            "role": ROLE_TEAM, "team_id": tid,
            "salt": salt, "hash": digest,
        }
    return accounts


def visible_credential_state(team, credential_rows, secret_accounts):
    """One team -> available / existing sheet login / legacy Secrets login."""
    tid = str(team.get("Mã đội", ""))
    active_rows = [
        r for r in credential_rows
        if r.get("Mã đội") == tid and r.get("Trạng thái") == STATUS_ACTIVE
    ]
    legacy = [
        name for name, info in (secret_accounts or {}).items()
        if isinstance(info, Mapping)
        and str(info.get("role", "")).upper() == ROLE_TEAM
        and str(info.get("team_id", "")) == tid
    ]
    if len(active_rows) > 1 or len(legacy) > 1 or (active_rows and legacy):
        return "conflict", None
    if legacy:
        return "legacy", None
    if active_rows:
        return "active", active_rows[0]
    return "missing", None


def next_account_id(existing_ids):
    """Private random identifier; users log in by name instead."""
    existing = set(existing_ids)
    for _ in range(8):
        candidate = "tdv_" + secrets.token_hex(10)
        if candidate not in existing:
            return candidate
    raise RuntimeError("Cannot generate unique login ID.")
