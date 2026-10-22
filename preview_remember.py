"""Signed short-lived browser remembered login (preview only).

Browser cookie includes username, expiration, and a one-way account fingerprint,
but NEVER a password, PIN, password hash or credentials. A separate app signing
secret is mandatory. Revalidates the latest account data on every new session.
"""
import base64
import hashlib
import hmac
import json
import time

COOKIE_NAME = "tdv_preview_remember_v1"
VALID_SECONDS = 30 * 24 * 60 * 60


def account_fingerprint(account):
    payload = "\0".join([
        str(account.get("salt", "")),
        str(account.get("hash", "")),
        str(account.get("role", "")),
        str(account.get("team_id", "")),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _encode(data):
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode(text):
    return json.loads(base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)))


def issue_remember_token(username, account, signing_key, issued_at=None):
    if not isinstance(signing_key, str) or len(signing_key) < 32:
        raise ValueError("Chưa có khóa ký phiên đăng nhập đủ mạnh.")
    now = int(time.time() if issued_at is None else issued_at)
    payload = _encode({"v": 1, "u": str(username), "exp": now + VALID_SECONDS,
                       "fp": account_fingerprint(account)})
    signature = hmac.new(signing_key.encode("utf-8"), payload.encode("ascii"),
                         hashlib.sha256).hexdigest()
    return payload + "." + signature


def verify_remember_token(token, accounts, signing_key, now=None):
    if not isinstance(token, str) or len(token) > 2048 or "." not in token:
        return None
    if not isinstance(signing_key, str) or len(signing_key) < 32:
        return None
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(signing_key.encode("utf-8"), payload.encode("ascii"),
                            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        data = _decode(payload)
        stamp = int(time.time() if now is None else now)
        if data.get("v") != 1 or not isinstance(data.get("exp"), int):
            return None
        if not (stamp < data["exp"] <= stamp + VALID_SECONDS):
            return None
        username = data.get("u")
        if not isinstance(username, str) or not username:
            return None
        account = accounts.get(username)
        if not account or not isinstance(account, dict):
            return None
        if not hmac.compare_digest(str(data.get("fp","")),
                                   account_fingerprint(account)):
            return None
        role = str(account.get("role","")).upper()
        if role not in {"ADMIN","LANH_DAO","DOI_TRUONG","THANH_VIEN"}:
            return None
        return {"username": username, "role": role,
                "team_id": str(account.get("team_id",""))}
    except (ValueError, TypeError, KeyError, UnicodeError, AttributeError, OverflowError):
        return None
