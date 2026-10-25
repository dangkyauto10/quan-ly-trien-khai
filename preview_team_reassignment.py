"""Admin-only safe reassignment of site tasks, without touching site stock quotas.

One VC/LĐ task is transferable only while unstarted and without physical
handover evidence.  Completed/partial tasks, proofs and KHO_PHAN_BO stay intact.
"""
from preview_assignment import ROLE_TABS, TASK_SCHEMA, allowed_modes
from preview_team_detach import DETACHED, NEEDS_REVIEW, ACTIVE, text_cell
from preview_site_rights import (
    RIGHT_FIELDS, active_registration, site_ids, site_text,
    owner_index, right_cell_request
)


def _signed_handover_keys(hub_rows, team_id, project):
    ktv_custody=set()
    vc_handoff=set()
    unknown_vc=set()
    for r in hub_rows:
        if r.get("Mã dự án")!=project or r.get("Trạng thái")!="KTV đã nhận tại tập kết":
            continue
        key=(project,r.get("Mã điểm"),r.get("SKU"))
        if r.get("Mã đội KTV nhận")==team_id:
            ktv_custody.add(key)
        if r.get("Mã đội VC giao")==team_id:
            vc_handoff.add(key)
        if not r.get("Mã đội VC giao"):
            unknown_vc.add(key)
    return ktv_custody,vc_handoff,unknown_vc


def team_change_plan(source_team, selected_sites, mode, tasksets, hub_rows,
                     target_team=None, suspend=False, registrations=None,
                     all_teams=None):
    """Preview the exact task rows to release/transfer, leaving proof untouched."""
    team_id=str(source_team.get("Mã đội") or "").strip()
    project=str(source_team.get("Mã dự án") or "").strip()
    if not team_id or not project or source_team.get("Trạng thái")!="Hoạt động":
        raise ValueError("Đội nguồn không còn hoạt động hoặc thiếu thông tin.")
    if registrations is None:
        raise ValueError("Thiếu danh sách quyền địa điểm đã duyệt.")
    if all_teams is not None:
        owner_index(registrations,all_teams,project)
    source_reg=active_registration(registrations,project,team_id)
    rights={tab:set(site_ids(source_reg.get(field)))
            for tab,(field,_) in RIGHT_FIELDS.items()}
    choices=allowed_modes(source_team)
    if not choices:
        raise ValueError("Đội nguồn không có chuyên môn VC/KTV hợp lệ.")
    if suspend:
        if target_team is not None:
            raise ValueError("Ngừng đội chỉ trả việc về chờ cấp lại.")
        tabs=tuple(dict.fromkeys(tab for choice in choices for tab in ROLE_TABS[choice]))
        points=None
    else:
        if mode not in choices:
            raise ValueError("Loại nhiệm vụ không thuộc chuyên môn đội nguồn.")
        tabs=ROLE_TABS[mode]
        ids=list(selected_sites or [])
        if not ids or len(ids)!=len(set(ids)):
            raise ValueError("Phải chọn ít nhất một điểm, không được trùng.")
        points=set(ids)
        for tab in tabs:
            if not points.issubset(rights[tab]):
                raise ValueError("Điểm chưa thuộc quyền Admin duyệt của đội nguồn.")
    target_id=""
    target_reg=None
    if target_team is not None:
        target_id=str(target_team.get("Mã đội") or "").strip()
        if (not target_id or target_id==team_id or
                target_team.get("Mã dự án")!=project or
                target_team.get("Trạng thái")!="Hoạt động" or
                mode not in allowed_modes(target_team)):
            raise ValueError("Đội nhận phải đang hoạt động, khác đội cũ, cùng dự án và đúng chuyên môn.")
        target_reg=active_registration(registrations,project,target_id)
    ktv_custody,vc_handoff,unknown_vc=_signed_handover_keys(
        hub_rows,team_id,project)
    changes=[]
    protected=[]
    found_points=set()
    for tab in tabs:
        id_col, owner_col, waiting=TASK_SCHEMA[tab]
        ids_seen=set()
        rows_seen=set()
        for r in tasksets.get(tab,[]):
            if r.get("Mã dự án")!=project or r.get(owner_col)!=team_id:
                continue
            point=str(r.get("Mã điểm") or "").strip()
            if points is not None and point not in points:
                continue
            if not point:
                raise ValueError("Nhiệm vụ thiếu mã điểm.")
            if point not in rights[tab]:
                raise ValueError("Nhiệm vụ của đội nằm ngoài danh sách điểm "
                                 "Admin đã duyệt; cần đối soát.")
            found_points.add(point)
            task_id=str(r.get(id_col) or "").strip()
            pos=r.get("_row")
            if not task_id or not isinstance(pos,int) or pos<2:
                raise ValueError("Nhiệm vụ thiếu mã hoặc số dòng hợp lệ.")
            if task_id in ids_seen or pos in rows_seen:
                raise ValueError("Mã nhiệm vụ hoặc dòng nhiệm vụ bị trùng.")
            ids_seen.add(task_id)
            rows_seen.add(pos)
            key=(project,point,r.get("SKU"))
            custody=(tab=="LAP_DAT" and key in ktv_custody)
            delivered_hub=(tab=="VAN_CHUYEN" and key in vc_handoff)
            uncertain_hub=(tab=="VAN_CHUYEN" and key in unknown_vc)
            recorded=any(str(r.get(field) or "").strip() for field in
                         ("Mã báo cáo","SL thực tế","Thời gian báo cáo",
                          "Link ảnh","Link ảnh báo cáo"))
            safe=(r.get("Trạng thái")==waiting and not recorded and
                  not custody and not delivered_hub and not uncertain_hub)
            detail={"tab":tab,"id":task_id,"row":pos,"point":point,
                    "sku":str(r.get("SKU") or ""),"old_team":team_id,
                    "status":r.get("Trạng thái","")}
            if safe:
                changes.append(detail)
            else:
                reason=("KTV đang giữ hàng tập kết" if custody else
                        "VC đã ký bàn giao tập kết" if delivered_hub else
                        "Chứng từ tập kết cũ chưa rõ đội VC" if uncertain_hub else
                        "Nhiệm vụ đã bắt đầu/có báo cáo hoặc chứng từ")
                protected.append({**detail,"reason":reason})
    # Rights are site-level: never release some SKUs while keeping evidence
    # for another SKU of the same site and role.
    blocked={(item["tab"],item["point"]) for item in protected}
    for hub in hub_rows:
        if (hub.get("Mã dự án")!=project or
                hub.get("Trạng thái")!="KTV đã nhận tại tập kết"):
            continue
        pid=hub.get("Mã điểm")
        if "VAN_CHUYEN" in tabs and hub.get("Mã đội VC giao") in (team_id,""):
            blocked.add(("VAN_CHUYEN",pid))
        if "LAP_DAT" in tabs and hub.get("Mã đội KTV nhận")==team_id:
            blocked.add(("LAP_DAT",pid))
    if not suspend and any(pid in (points or ()) for _,pid in blocked):
        raise ValueError("Địa điểm đã bắt đầu hoặc có hàng/chứng từ; phải "
                         "đối soát, bàn giao trước khi chuyển cả điểm.")
    if suspend and blocked:
        safe=[]
        for item in changes:
            if (item["tab"],item["point"]) in blocked:
                protected.append({**item,"reason":"Còn nhiệm vụ/chứng từ tại điểm"})
            else:
                safe.append(item)
        changes=safe
    releases={}
    for tab in tabs:
        candidates=rights[tab] if suspend else points
        releases[tab]={pid for pid in candidates if (tab,pid) not in blocked}
    updates=[]
    for tab,ids in releases.items():
        if not ids:
            continue
        if not isinstance(source_reg.get("_row"),int):
            raise ValueError("Không tìm thấy dòng quyền của đội nguồn.")
        updates.append((source_reg["_row"],tab,site_text(rights[tab]-ids)))
        if target_reg is not None:
            field,_=RIGHT_FIELDS[tab]
            target_set=set(site_ids(target_reg.get(field)))
            if not isinstance(target_reg.get("_row"),int):
                raise ValueError("Không tìm thấy dòng quyền của đội nhận.")
            updates.append((target_reg["_row"],tab,site_text(target_set|ids)))
    return {
        "team_id":team_id,"project":project,"mode":mode,
        "suspend":suspend,"target_id":target_id,
        "team_row":source_team.get("_row"),
        "changes":changes,"protected":protected,
        "released_sites":len({pid for ids in releases.values() for pid in ids}),
        "site_updates":updates
    }


def change_signature(plan):
    """Optimistic UI recheck; detect edits, evidence and row moves before commit."""
    return (
        plan["team_id"],plan["project"],plan["mode"],
        plan["suspend"],plan["target_id"],
        tuple(sorted((x["tab"],x["id"],x["row"],x["point"]) for x in plan["changes"])),
        tuple(sorted((x["tab"],x["id"],x["row"],x["reason"]) for x in plan["protected"])),
        tuple(sorted(plan.get("site_updates",[])))
    )


def team_change_requests(plan, sheet_ids, stamp, admin,
                         account_rows=(), active_links=()):
    """One atomic Sheets batch: only assignee column G, optional team status, audit."""
    required={"VAN_CHUYEN","LAP_DAT","NHAT_KY_HE_THONG"}
    if plan["suspend"]:
        required|={"QUAN_LY_DOI","TAI_KHOAN_DOI","LIEN_KET_DANG_KY_DOI"}
    if plan.get("site_updates"):
        required.add("DANG_KY_THANH_VIEN")
    if not required.issubset(sheet_ids):
        raise ValueError("Thiếu sheet phục vụ thu hồi.")
    if not admin or not stamp:
        raise ValueError("Thiếu người thực hiện hoặc thời điểm.")
    def update(tab,row,col,value):
        if not isinstance(row,int) or row<2:
            raise ValueError("Dòng dữ liệu không hợp lệ.")
        return {"updateCells":{"range":{
            "sheetId":sheet_ids[tab],
            "startRowIndex":row-1,"endRowIndex":row,
            "startColumnIndex":col,"endColumnIndex":col+1},
            "rows":[{"values":[text_cell(value)]}],
            "fields":"userEnteredValue"}}
    requests=[]
    for tab in ("VAN_CHUYEN","LAP_DAT"):
        nums=sorted(x["row"] for x in plan["changes"] if x["tab"]==tab)
        if len(nums)!=len(set(nums)):
            raise ValueError("Trùng dòng nhiệm vụ khi lập lệnh.")
        if not nums:
            continue
        spans=[]
        lo=hi=nums[0]
        for n in nums[1:]:
            if n==hi+1:
                hi=n
            else:
                spans.append((lo,hi))
                lo=hi=n
        spans.append((lo,hi))
        for lo,hi in spans:
            requests.append({"repeatCell":{
                "range":{"sheetId":sheet_ids[tab],
                         "startRowIndex":lo-1,"endRowIndex":hi,
                         "startColumnIndex":6,"endColumnIndex":7},
                "cell":text_cell(plan["target_id"]),
                "fields":"userEnteredValue"}})
    for row, tab, value in plan.get("site_updates",[]):
        requests.append(right_cell_request(
            sheet_ids["DANG_KY_THANH_VIEN"],row,tab,value))
    if plan["suspend"]:
        status=NEEDS_REVIEW if plan["protected"] else DETACHED
        # QUAN_LY_DOI uses a strict dropdown: Hoạt động / Tạm khóa.
        requests.append(update("QUAN_LY_DOI",plan["team_row"],5,"Tạm khóa"))
        for row in account_rows:
            requests.append(update("TAI_KHOAN_DOI",row,6,DETACHED))
        for row in active_links:
            requests.append(update("LIEN_KET_DANG_KY_DOI",row,3,status))
            requests.append(update("LIEN_KET_DANG_KY_DOI",row,5,stamp))
    detail=(f"{plan['project']} | đội {plan['team_id']} | "
            f"{len(plan['changes'])} nhiệm vụ | "
            f"{len(plan['protected'])} giữ đối soát | "
            f"đội nhận: {plan['target_id'] or 'chờ cấp lại'}")
    action=("DỪNG ĐỘI / THU HỒI" if plan["suspend"] else
            "GIAO LẠI ĐỘI KHÁC" if plan["target_id"] else
            "THU HỒI PHÂN CÔNG")
    requests.append({"appendCells":{
        "sheetId":sheet_ids["NHAT_KY_HE_THONG"],
        "rows":[{"values":[text_cell(x) for x in
                           (stamp,admin,"ADMIN",action,"VAN_CHUYEN/LAP_DAT",
                            plan["team_id"],"OK",detail)]}],
        "fields":"userEnteredValue"}})
    return requests
