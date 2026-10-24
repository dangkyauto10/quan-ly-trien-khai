"""Preview assignment selection with project/site/team safety checks.
Pure helper: does not write to Google Sheets.
"""


def assignment_rows(tasks, selected_task, team, task_key, team_key,
                    accepted_kinds, pending_status, group_site=True):
    """Return task rows that may be assigned to the selected team."""
    project = selected_task.get("Mã dự án")
    point = selected_task.get("Mã điểm")
    task_id = selected_task.get(task_key)
    if not project or not point or not task_id:
        raise ValueError("Nhiệm vụ thiếu mã dự án, mã điểm hoặc mã công việc.")
    if team.get("Trạng thái") != "Hoạt động" or team.get("Mã dự án") != project:
        raise ValueError("Đội không hoạt động hoặc khác dự án.")
    if team.get("Loại nhiệm vụ") not in accepted_kinds or not team.get("Mã đội"):
        raise ValueError("Đội không đủ chuyên môn hoặc thiếu mã đội.")
    original = [r for r in tasks if r.get(task_key) == task_id]
    if len(original) != 1:
        raise ValueError("Nhiệm vụ đã thay đổi hoặc bị trùng mã.")
    seed = original[0]
    if seed.get(team_key) or seed.get("Trạng thái") != pending_status:
        raise ValueError("Nhiệm vụ đã có đội hoặc không còn chờ giao.")
    if seed.get("Mã dự án") != project or seed.get("Mã điểm") != point:
        raise ValueError("Nhiệm vụ đã chuyển địa điểm hoặc dự án.")
    selected = []
    for r in tasks:
        if r.get("Mã dự án") != project or r.get("Mã điểm") != point:
            continue
        if not r.get(task_key) or r.get(team_key) or r.get("Trạng thái") != pending_status:
            continue
        if not group_site and r.get(task_key) != task_id:
            continue
        if not isinstance(r.get("_row"), int) or r["_row"] < 2:
            raise ValueError("Dòng nhiệm vụ không có chỉ số hợp lệ.")
        selected.append(r)
    ids = [r[task_key] for r in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("Phát hiện mã nhiệm vụ trùng; không gán.")
    if not selected:
        raise ValueError("Không còn nhiệm vụ chờ giao tại điểm.")
    return selected


def assignment_batch_requests(sheet_id, rows, team_id):
    """Build Google Sheets batchUpdate requests touching ONLY team column G."""
    if not team_id or not rows:
        raise ValueError("Thiếu mã đội hoặc nhiệm vụ.")
    return [
        {"updateCells": {
            "start": {"sheetId": sheet_id, "rowIndex": row["_row"] - 1,
                      "columnIndex": 6},
            "rows": [{"values": [{"userEnteredValue": {"stringValue": team_id}}]}],
            "fields": "userEnteredValue"
        }}
        for row in rows
    ]


ROLE_TABS = {
    "VC": ("VAN_CHUYEN",),
    "LD": ("LAP_DAT",),
    "VC+LD": ("VAN_CHUYEN", "LAP_DAT"),
}

TASK_SCHEMA = {
    "VAN_CHUYEN": ("Mã nhiệm vụ VC", "Mã đội VC", "Chưa giao"),
    "LAP_DAT": ("Mã nhiệm vụ LD", "Mã đội KTV", "Chưa lắp"),
}


def allowed_modes(team):
    """Never allow role assignment outside the team leader's approved role."""
    role = team.get("Loại nhiệm vụ")
    if role == "VC":
        return ("VC",)
    if role == "KTV":
        return ("LD",)
    if role == "VC+KTV":
        return ("VC", "LD", "VC+LD")
    return ()


def eligible_site_tasks(team, mode, locations, tasksets):
    """Return safe, searchable eligible points and their pending task counts.

    Exclude sites with tasks already assigned to a DIFFERENT team for one of
    the requested roles. A point with only previously assigned work is excluded.
    """
    if mode not in allowed_modes(team):
        raise ValueError("Đội trưởng không có chuyên môn phù hợp loại việc.")
    project, tid = team.get("Mã dự án"), team.get("Mã đội")
    if not project or not tid or team.get("Trạng thái") != "Hoạt động":
        raise ValueError("Đội trưởng chưa được duyệt hoặc thiếu dự án.")
    if len(set(ROLE_TABS[mode])) != len(ROLE_TABS[mode]):
        raise ValueError("Trùng nhóm nhiệm vụ.")
    locs = {}
    for loc in locations:
        pid = loc.get("Mã điểm")
        if loc.get("Mã dự án") != project or loc.get("Trạng thái") != "Hoạt động" or not pid:
            continue
        if pid in locs:
            raise ValueError(f"Mã địa điểm bị trùng: {pid}.")
        locs[pid] = loc
    ready = {}
    for pid in locs:
        per_tab = {}
        for tab in ROLE_TABS[mode]:
            idcol, teamcol, pending = TASK_SCHEMA[tab]
            associated = [r for r in tasksets.get(tab, []) if
                          r.get("Mã dự án") == project and r.get("Mã điểm") == pid
                          and r.get(idcol)]
            if any(r.get(teamcol) and r.get(teamcol) != tid for r in associated):
                break
            unassigned = [r for r in associated if
                          not r.get(teamcol) and r.get("Trạng thái") == pending]
            if not unassigned:
                break
            per_tab[tab] = len(unassigned)
        else:
            ready[pid] = per_tab
    return {pid: (locs[pid], counts) for pid, counts in ready.items()}


def site_assignment_plan(team, mode, selected_ids, locations, tasksets):
    """Validate selected places; gather ALL pending SKU tasks per requested role."""
    choices = list(selected_ids)
    if not choices or len(choices) != len(set(choices)):
        raise ValueError("Cần chọn ít nhất một địa điểm, không được trùng.")
    eligible = eligible_site_tasks(team, mode, locations, tasksets)
    bad = [pid for pid in choices if pid not in eligible]
    if bad:
        raise ValueError("Các điểm không còn hợp lệ/chưa phân bổ/đã có đội khác: " +
                         ", ".join(bad[:8]))
    out = {}
    project = team["Mã dự án"]
    for tab in ROLE_TABS[mode]:
        idcol, teamcol, pending = TASK_SCHEMA[tab]
        rows = [r for r in tasksets.get(tab, []) if
                r.get("Mã dự án") == project and r.get("Mã điểm") in choices and
                r.get(idcol) and not r.get(teamcol) and
                r.get("Trạng thái") == pending]
        ids = [r[idcol] for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{tab}: trùng mã nhiệm vụ.")
        if len({r.get("_row") for r in rows}) != len(rows) or any(
                not isinstance(r.get("_row"), int) or r["_row"] < 2 for r in rows):
            raise ValueError(f"{tab}: vị trí dòng ghi không hợp lệ.")
        out[tab] = rows
    return out


def compact_site_assignment_requests(sheet_ids, plan, team_id):
    """RepeatCell consecutive task rows, one atomic batch across VC and LD."""
    if not team_id or not plan:
        raise ValueError("Thiếu mã đội hoặc nhiệm vụ.")
    requests = []
    for tab, rows in plan.items():
        if not rows:
            continue
        if tab not in TASK_SCHEMA or tab not in sheet_ids:
            raise ValueError("Thiếu sheet hợp lệ để cập nhật phân công.")
        indices = sorted(r["_row"] - 1 for r in rows)
        if len(indices) != len(set(indices)):
            raise ValueError("Trùng dòng trong phương án giao việc.")
        start = prev = indices[0]
        groups = []
        for row in indices[1:]:
            if row == prev + 1:
                prev = row
            else:
                groups.append((start, prev + 1))
                start = prev = row
        groups.append((start, prev + 1))
        for start_row, end_row in groups:
            requests.append({"repeatCell": {
                "range": {"sheetId": sheet_ids[tab],
                          "startRowIndex": start_row,
                          "endRowIndex": end_row,
                          "startColumnIndex": 6, "endColumnIndex": 7},
                "cell": {"userEnteredValue": {"stringValue": team_id}},
                "fields": "userEnteredValue"
            }})
    if not requests:
        raise ValueError("Không có nhiệm vụ chờ giao.")
    return requests


def project_site_catalog(team, mode, locations, tasksets):
    """List ALL active project sites for searching, not just unassigned ones.

    Returns point_id => (location, display_status, pending_task_counts).
    Only status Sẵn sàng giao may be committed to tasks.
    """
    eligible = eligible_site_tasks(team, mode, locations, tasksets)
    project, team_id = team["Mã dự án"], team["Mã đội"]
    grouped = {}
    for tab in ROLE_TABS[mode]:
        task_id, _, _ = TASK_SCHEMA[tab]
        for task in tasksets.get(tab, []):
            if task.get("Mã dự án") != project or not task.get(task_id):
                continue
            grouped.setdefault((tab, task.get("Mã điểm")), []).append(task)
    result = {}
    for loc in locations:
        pid = loc.get("Mã điểm")
        if (not pid or loc.get("Mã dự án") != project or
                loc.get("Trạng thái") != "Hoạt động"):
            continue
        if pid in result:
            raise ValueError(f"Mã địa điểm trùng trong danh mục: {pid}.")
        if pid in eligible:
            result[pid] = (loc, "Sẵn sàng giao", eligible[pid][1])
            continue
        jobs = [r for tab in ROLE_TABS[mode]
                for r in grouped.get((tab, pid), [])]
        if not jobs:
            status = "Chưa phân bổ hàng"
        elif any(
            r.get(TASK_SCHEMA[tab][1]) not in ("", None, team_id)
            for tab in ROLE_TABS[mode]
            for r in grouped.get((tab, pid), [])
        ):
            status = "Đã gán đội khác"
        elif any(
            not grouped.get((tab, pid), []) for tab in ROLE_TABS[mode]
        ):
            status = "Chưa có đủ nhiệm vụ VC/LĐ"
        elif all(
            r.get(TASK_SCHEMA[tab][1]) == team_id
            for tab in ROLE_TABS[mode]
            for r in grouped.get((tab, pid), [])
        ):
            status = "Đã gán cho đội này"
        else:
            status = "Không còn nhiệm vụ chờ gán"
        result[pid] = (loc, status, {})
    return result


def registered_site_suggestions(team, links, registrations, catalog):
    """Prefill Admin's *reviewable* selection only from an approved linked form.

    Exact project-scoped names only; unmatched/ambiguous free text remains
    visible to Admin. Never creates a task or writes registration data.
    """
    import re

    def normalized(value):
        return " ".join(str(value or "").strip().casefold().split())

    project=str(team.get("Mã dự án") or "").strip()
    team_id=str(team.get("Mã đội") or "").strip()
    active=[row for row in links
            if row.get("Mã đội")==team_id
            and row.get("Mã dự án")==project
            and row.get("Trạng thái liên kết")=="Đang liên kết"]
    if not active:
        return {"site_ids":[],"unmatched":[],"raw":"",
                "note":"Đội chưa có hồ sơ đăng ký liên kết; ADMIN chọn địa điểm thủ công."}
    if len(active)!=1:
        return {"site_ids":[],"unmatched":[],"raw":"",
                "note":"Có nhiều liên kết hồ sơ; chưa tự chọn địa bàn, cần đối soát."}
    rid=str(active[0].get("Mã đăng ký") or "").strip()
    accepted=[row for row in registrations
              if row.get("Mã đăng ký")==rid
              and row.get("Mã đội")==team_id
              and row.get("Mã dự án đăng ký")==project
              and row.get("Trạng thái duyệt")=="Đã duyệt"]
    if len(accepted)!=1:
        return {"site_ids":[],"unmatched":[],"raw":"",
                "note":"Không xác minh được hồ sơ đã duyệt; ADMIN chọn thủ công."}
    raw=str(accepted[0].get("Địa bàn đề xuất") or "").strip()
    if not raw:
        return {"site_ids":[],"unmatched":[],"raw":"",
                "note":"Hồ sơ chưa khai địa bàn; ADMIN chọn thủ công."}
    by_name={}
    for point_id,(location,_status,_counts) in catalog.items():
        name=normalized(location.get("Tên xã/phường/đơn vị"))
        if name:
            by_name.setdefault(name,[]).append(point_id)
    chosen=[]
    unmatched=[]
    for part in re.split(r"[,;\n]+",raw):
        label=part.strip()
        if not label:
            continue
        matches=by_name.get(normalized(label),[])
        if len(matches)==1:
            if matches[0] not in chosen:
                chosen.append(matches[0])
        else:
            unmatched.append(label + (" (trùng tên nhiều điểm)" if matches else
                                      " (chưa khớp danh mục)"))
    return {"site_ids":chosen,"unmatched":unmatched,"raw":raw,
            "note":""}
