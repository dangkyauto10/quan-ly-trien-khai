"""Safe display-name login for field team leaders (Preview only).

The team id remains internal for authorization and routing. No PIN is
stored or checked here; callers must authenticate the resolved account with
the original PBKDF2/lockout mechanism.
"""
import unicodedata
from collections.abc import Mapping


def normalized_name(value):
    return " ".join(unicodedata.normalize("NFKC",str(value or "")).split()).casefold()


def resolve_login_username(typed, accounts, teams):
    """Return (username, reason): reasons ok/missing/ambiguous.

    Human name is accepted only for a single active team leader whose
    account's team_id matches the approved team. A collision with any
    configured username is rejected, never guessed.
    """
    raw=str(typed or "").strip()
    if not raw or not isinstance(accounts,Mapping):
        return None,"missing"
    candidates=set()
    if raw in accounts and isinstance(accounts.get(raw),Mapping):
        candidates.add(raw)
    needle=normalized_name(raw)
    teams_by_id={}
    for row in teams or ():
        if not isinstance(row,Mapping):
            continue
        tid=str(row.get("Mã đội","") or "").strip()
        if tid and row.get("Trạng thái")=="Hoạt động":
            teams_by_id.setdefault(tid,[]).append(row)
    matched_ids={
        tid for tid,rows in teams_by_id.items()
        if any(normalized_name(r.get("Tên đội/đội trưởng"))==needle for r in rows)
    }
    ambiguous=False
    for username,info in accounts.items():
        if not isinstance(info,Mapping) or str(info.get("role","")).upper()!="DOI_TRUONG":
            continue
        tid=str(info.get("team_id","") or "").strip()
        if tid in matched_ids:
            # Reused id or mismatched team records cannot be a unique identity.
            if len(teams_by_id[tid])!=1:
                ambiguous=True
                continue
            candidates.add(str(username))
    if ambiguous or len(candidates)>1:
        return None,"ambiguous"
    if len(candidates)!=1:
        # Names of approved leaders who are not yet credentialed fail closed.
        return None,"missing"
    return next(iter(candidates)),"ok"


def friendly_account_name(account, teams):
    """Only returns a leader name from an active linked team, else username."""
    username=str((account or {}).get("username",""))
    if (account or {}).get("role")!="DOI_TRUONG":
        return username
    tid=str(account.get("team_id","") or "").strip()
    matches=[t for t in teams if t.get("Mã đội")==tid and
             t.get("Trạng thái")=="Hoạt động"]
    return matches[0].get("Tên đội/đội trưởng") or username if len(matches)==1 else username
