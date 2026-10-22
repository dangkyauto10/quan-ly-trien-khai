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
