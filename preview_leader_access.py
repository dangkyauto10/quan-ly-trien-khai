"""Select a single approved leadership account for password-only entry.

The password remains the PBKDF2 hashed secret of a dedicated LANH_DAO
account.  Multiple leader accounts require a separately configured username;
never pick one accidentally or downgrade ADMIN into leadership.
"""
from collections.abc import Mapping


def leadership_username(accounts, configured_username=""):
    if not isinstance(accounts, Mapping):
        return None
    valid = [
        name for name, info in accounts.items()
        if isinstance(name, str) and name and isinstance(info, Mapping)
        and str(info.get("role", "")).upper() == "LANH_DAO"
    ]
    if configured_username:
        return configured_username if configured_username in valid else None
    return valid[0] if len(valid) == 1 else None
