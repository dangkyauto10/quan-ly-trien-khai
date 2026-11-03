"""Safe display-name login for field team leaders (Preview only).

The team id remains internal for authorization and routing. No PIN is
stored or checked here; callers must authenticate the resolved account with
the original PBKDF2/lockout mechanism.
"""
import unicodedata
from collections.abc import Mapping


def normalized_name(value):
    return " ".join(unicodedata.normalize("NFKC",str(value or "")).split()).casefold()


def resolve_login_username(typed, accounts, teams, project_id=None):
    """Resolve an approved team by name and, only if needed, project.

    Without project selection a duplicate active name must remain ambiguous,
    including teams that have no credentials yet. The original password,
    account lockout and team role checks are enforced by the caller.
    """
    raw=str(typed or "").strip()
    if not raw or not isinstance(accounts,Mapping):
        return None,"missing"
    project=str(project_id or "").strip()
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
        if any(normalized_name(r.get("Tên đội/đội trưởng"))==needle
               and (not project or str(r.get("Mã dự án","")).strip()==project)
               for r in rows)
    }
    if len(matched_ids)>1:
        return None,"ambiguous"
    ambiguous=False
    for username,info in accounts.items():
        if not isinstance(info,Mapping) or str(info.get("role","")).upper()!="DOI_TRUONG":
            continue
        tid=str(info.get("team_id","") or "").strip()
        if tid in matched_ids:
            if len(teams_by_id[tid])!=1:
                ambiguous=True
                continue
            candidates.add(str(username))
    # Selecting a project must never allow a team username from another
    # project to bypass the project filter.
    if project and raw in accounts:
        raw_info=accounts.get(raw)
        if (isinstance(raw_info,Mapping)
                and str(raw_info.get("role","")).upper()=="DOI_TRUONG"
                and str(raw_info.get("team_id","") or "").strip() not in matched_ids):
            return None,"missing"
    if ambiguous or len(candidates)>1:
        return None,"ambiguous"
    if len(candidates)!=1:
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
