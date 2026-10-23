"""Safe cascade when a newly approved registration is removed from Sheets.

Registration-team provenance is immutable, recorded only on approval that
CREATES a new team. Never infer ownership from matching names, team ID shapes,
or an empty legacy DANG_KY_THANH_VIEN sheet.

A stock allocation belongs to PROJECT+SITE+SKU, never a team; changing team
assignment must not edit KHO_PHAN_BO quantities or real signed handovers.
"""
from collections import defaultdict

ACTIVE = "Đang liên kết"
DETACHED = "Đã gỡ"
NEEDS_REVIEW = "Cần đối soát"

HEADERS = ("Mã đăng ký", "Mã đội", "Mã dự án",
           "Trạng thái liên kết", "Thời gian gắn", "Thời gian gỡ")


def text_cell(value):
    return {"userEnteredValue":{"stringValue":str(value if value is not None else "")}}


def approval_link_request(sheet_id, registration_id, team_id, project, created_at):
    """Append registration->newly created team in the SAME approval batch."""
    if not all((sheet_id,registration_id,team_id,project,created_at)):
        raise ValueError("Missing registration/team provenance.")
    return {"appendCells":{
        "sheetId":sheet_id,
        "rows":[{"values":[text_cell(x) for x in
            (registration_id,team_id,project,ACTIVE,created_at,"")]}],
        "fields":"userEnteredValue"}}


def lost_registrations(registrations, links):
    """Find only recorded, active provenance with a no-longer-existing row."""
    present={str(r.get("Mã đăng ký","")).strip() for r in registrations
             if r.get("Mã đăng ký")}
    active=[r for r in links if r.get("Trạng thái liên kết")==ACTIVE]
    count=defaultdict(int)
    per_team=defaultdict(int)
    for r in active:
        count[(r.get("Mã đăng ký"),r.get("Mã đội"),r.get("Mã dự án"))]+=1
        per_team[r.get("Mã đội")]+=1
    found=[]
    for r in active:
        rid=str(r.get("Mã đăng ký","")).strip()
        team_id=str(r.get("Mã đội","")).strip()
        project=str(r.get("Mã dự án","")).strip()
        if rid in present:
            continue
        key=(rid,team_id,project)
        if (not all(key) or count[key]!=1 or per_team[team_id]!=1
                or not isinstance(r.get("_row"),int)):
            # Ambiguous duplicate / corrupt links are NOT auto-removed.
            continue
        found.append(r)
    return found


def revoked_team_ids(registrations,links):
    """Public auth denies linked team as soon as registration is absent.

    Treat duplicate or invalid live links as unsafe and deny as well.
    Legacy teams, without a link, remain unchanged.
    """
    present={str(r.get("Mã đăng ký","")).strip():r for r in registrations
             if r.get("Mã đăng ký")}
    active=[r for r in links if r.get("Trạng thái liên kết")==ACTIVE]
    groups=defaultdict(list)
    for r in active:
        groups[str(r.get("Mã đội","")).strip()].append(r)
    revoked={str(r.get("Mã đội","")).strip() for r in links
             if r.get("Trạng thái liên kết") in (DETACHED,NEEDS_REVIEW)}
    for tid,group in groups.items():
        if not tid or len(group)!=1:
            revoked.add(tid)
            continue
        r=group[0]
        present_reg=present.get(str(r.get("Mã đăng ký","")).strip())
        if (not present_reg or
            present_reg.get("Trạng thái duyệt")!="Đã duyệt" or
            present_reg.get("Mã đội được gán")!=tid or
            present_reg.get("Mã dự án đăng ký")!=r.get("Mã dự án")):
            revoked.add(tid)
    return revoked


def plan_detach(link, teams, credentials, vc_tasks, ld_tasks,
                reports, hub_receipts):
    """Return exact row references to detach, preserving completed work.

    A completed / started work item is retained for audit. Pending tasks are
    set back to unassigned by clearing ONLY Mã đội VC / Mã đội KTV.
    """
    tid=str(link.get("Mã đội",""))
    project=str(link.get("Mã dự án",""))
    if not tid or not project or not link.get("Mã đăng ký"):
        raise ValueError("Invalid link.")
    matching=[t for t in teams if t.get("Mã đội")==tid and
              t.get("Mã dự án")==project]
    if len(matching)!=1 or not isinstance(matching[0].get("_row"),int):
        raise ValueError("Team is absent or ambiguous; requires audit.")
    team=matching[0]
    creds=[r for r in credentials if r.get("Mã đội")==tid and
           r.get("Mã dự án")==project and
           r.get("Trạng thái")=="Hoạt động"]
    if any(not isinstance(r.get("_row"),int) for r in creds):
        raise ValueError("Invalid credential row.")
    if len(creds)>1:
        raise ValueError("Duplicated credentials; requires audit.")
    pending=[]
    protected=[]
    pending_details=[]
    protected_details=[]
    # When a KTV has signed for goods at a central hub, the goods remain
    # physically in that person's custody. The assigned installation tasks
    # MUST NOT be released to another team as if the goods were free.
    hub_custody={
        (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
        for r in hub_receipts
        if r.get("Mã đội KTV nhận")==tid
        and r.get("Mã dự án")==project
        and r.get("Trạng thái")=="KTV đã nhận tại tập kết"
        # Even if photo/number is missing, goods may already be physically
        # in KTV custody. Do not silently hand such goods to a new team.
    }
    vc_hub_handoffs={
        (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
        for r in hub_receipts
        if r.get("Mã đội VC giao")==tid
        and r.get("Mã dự án")==project
        and r.get("Trạng thái")=="KTV đã nhận tại tập kết"
        # Signed at the hub is VC work DONE, though not delivered to each
        # commune. Preserve the original VC assignment as delivery evidence.
    }
    unverified_vc_hub={
        (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
        for r in hub_receipts
        if not r.get("Mã đội VC giao")
        and r.get("Mã dự án")==project
        and r.get("Trạng thái")=="KTV đã nhận tại tập kết"
        # Legacy signed paper proves some VC delivered, but not which crew.
        # Prevent any automatic reallocation of that site/SKU until checked.
    }
    for table, records, team_col, waiting_status in (
        ("VAN_CHUYEN",vc_tasks,"Mã đội VC","Chưa giao"),
        ("LAP_DAT",ld_tasks,"Mã đội KTV","Chưa lắp"),
    ):
        for row in records:
            if row.get(team_col)!=tid or row.get("Mã dự án")!=project:
                continue
            if not isinstance(row.get("_row"),int):
                raise ValueError("Invalid task row.")
            key=(project,row.get("Mã điểm"),row.get("SKU"))
            has_custody=(table=="LAP_DAT" and key in hub_custody)
            vc_hub_done=(table=="VAN_CHUYEN" and key in vc_hub_handoffs)
            unknown_vc=(table=="VAN_CHUYEN" and key in unverified_vc_hub)
            # Only unstarted tasks without disputed stock custody,
            # signed transfer or unverifiable legacy handoff can be freed.
            unstarted=(row.get("Trạng thái")==waiting_status and not any(
                str(row.get(k,"")).strip() for k in
                ("Mã báo cáo","SL thực tế","Thời gian báo cáo")
            ))
            detail={
                "table":table,
                "point_id":str(row.get("Mã điểm","")),
                "sku":str(row.get("SKU","")),
                "quantity":row.get("SL giao" if table=="VAN_CHUYEN" else "SL lắp",""),
            }
            if unstarted and not has_custody and not vc_hub_done and not unknown_vc:
                pending.append((table,row["_row"],team_col))
                pending_details.append({**detail,"state":"Chờ phân công lại"})
            else:
                reason=("KTV còn giữ hàng tại điểm tập kết"
                        if has_custody else
                        "VC đã bàn giao tại điểm tập kết"
                        if vc_hub_done else
                        "Biên bản tập kết cũ thiếu mã đội VC giao"
                        if unknown_vc else "Đã có tiến độ/chứng từ")
                protected.append((table,row["_row"],row.get("Trạng thái","")))
                protected_details.append({**detail,"state":"Cần bàn giao/đối soát",
                                          "reason":reason})
    if any(r.get("Mã đội")==tid and r.get("Mã dự án")==project
           for r in reports):
        protected.append(("BAO_CAO_TRIEN_KHAI",0,"Đã có báo cáo"))
    if any(r.get("Mã dự án")==project and
           r.get("Trạng thái")=="KTV đã nhận tại tập kết" and
           (r.get("Mã đội KTV nhận")==tid or r.get("Mã đội VC giao")==tid)
           for r in hub_receipts):
        protected.append(("BAN_GIAO_TAP_KET",0,"Đã ký bàn giao"))
    return {
        "team_row":team["_row"], "account_rows":[r["_row"] for r in creds],
        "pending_tasks":pending,"protected_tasks":protected,
        "pending_details":pending_details,
        "protected_details":protected_details,
        "released_sites":len({d["point_id"] for d in pending_details}),
        "custody_sites":len({d["point_id"] for d in protected_details
                             if d.get("reason")=="KTV còn giữ hàng tại điểm tập kết"}),
        "vc_hub_sites":len({d["point_id"] for d in protected_details
                             if d.get("reason")=="VC đã bàn giao tại điểm tập kết"}),
        "unknown_hub_sites":len({d["point_id"] for d in protected_details
                             if d.get("reason")=="Biên bản tập kết cũ thiếu mã đội VC giao"}),
        "review":bool(protected),
        "team_id":tid,"project":project,
        "link_row":link.get("_row")
    }


def detach_requests(plan, sheet_ids, timestamp):
    """One atomic Sheets batch, never delete stock allocation/physical proof."""
    for tab in ("QUAN_LY_DOI","TAI_KHOAN_DOI",
                "VAN_CHUYEN","LAP_DAT","LIEN_KET_DANG_KY_DOI"):
        if tab not in sheet_ids:
            raise ValueError("Missing sheet: "+tab)
    if not isinstance(plan.get("link_row"),int):
        raise ValueError("Missing provenance row.")

    def update_one(tab,row_number,col_index,value):
        if not isinstance(row_number,int) or row_number<2:
            raise ValueError("Invalid row.")
        return {"updateCells":{
            "range":{"sheetId":sheet_ids[tab],
                     "startRowIndex":row_number-1,"endRowIndex":row_number,
                     "startColumnIndex":col_index,"endColumnIndex":col_index+1},
            "rows":[{"values":[text_cell(value)]}],
            "fields":"userEnteredValue"}}
    requests=[]
    by_tab=defaultdict(set)
    for tab,row_number,col in plan["pending_tasks"]:
        if tab not in ("VAN_CHUYEN","LAP_DAT") or row_number<2:
            raise ValueError("Invalid task.")
        by_tab[tab].add(row_number)
    for tab,rows in by_tab.items():
        ordered=sorted(rows)
        chunks=[]
        lo=hi=ordered[0]
        for n in ordered[1:]:
            if n==hi+1:
                hi=n
            else:
                chunks.append((lo,hi))
                lo=hi=n
        chunks.append((lo,hi))
        for lo,hi in chunks:
            requests.append({"repeatCell":{
                "range":{"sheetId":sheet_ids[tab],
                         "startRowIndex":lo-1,"endRowIndex":hi,
                         "startColumnIndex":6,"endColumnIndex":7},
                "cell":text_cell(""),
                "fields":"userEnteredValue"}})
    # Do not hard delete the team: retain identity/previous signed evidence.
    # Existing UI and login only accept "Hoạt động" teams.
    requests.append(update_one("QUAN_LY_DOI",plan["team_row"],5,
                               NEEDS_REVIEW if plan["review"] else DETACHED))
    for row_number in plan["account_rows"]:
        requests.append(update_one("TAI_KHOAN_DOI",row_number,6,DETACHED))
    requests.append(update_one("LIEN_KET_DANG_KY_DOI",
                               plan["link_row"],3,
                               NEEDS_REVIEW if plan["review"] else DETACHED))
    requests.append(update_one("LIEN_KET_DANG_KY_DOI",
                               plan["link_row"],5,timestamp))
    return requests
