"""Password-only identity for the read-only leadership dashboard.

The ADMIN stores one independent password in the PREVIEW app Streamlit
Secrets as leader_view_password. The password itself is never stored in
session state; a SHA-256 fingerprint invalidates sessions when ADMIN
changes the configured password.
"""
from hashlib import sha256
from hmac import compare_digest
from collections.abc import Mapping

LEADER_SESSION_USERNAME = "__tdv_leadership_password_only__"


def check_leader_password(entered, configured):
    """Constant-time check for the separate leadership password."""
    if not isinstance(entered, str) or not isinstance(configured, str) or not configured:
        return False
    return compare_digest(entered, configured)


def make_leader_session(configured):
    """Create a minimal read-only role session without storing the password."""
    if not isinstance(configured, str) or not configured:
        return None
    fingerprint = sha256(configured.encode("utf-8")).hexdigest()
    return {
        "username": LEADER_SESSION_USERNAME,
        "role": "LANH_DAO",
        "team_id": "",
        "_fp": fingerprint,
    }


def verify_leader_session(account, configured):
    """Validate the session against the current Secret, including rotations."""
    expected = make_leader_session(configured)
    if expected is None or not isinstance(account, Mapping):
        return False
    return (
        account.get("username") == LEADER_SESSION_USERNAME
        and account.get("role") == "LANH_DAO"
        and account.get("team_id") == ""
        and isinstance(account.get("_fp"), str)
        and compare_digest(account["_fp"], expected["_fp"])
    )
