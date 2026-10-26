"""Authoritative Admin-approved site rights for VC and installation teams.

Site rights are independent of SKU allocation. The two CSV ID fields on each
approved registration are the source of truth; task G columns mirror them only
for allocated, unstarted work. Never infer rights from a signup proposal.
"""
from preview_assignment import ROLE_TABS, TASK_SCHEMA, allowed_modes

RIGHT_FIELDS = {
    "VAN_CHUYEN": ("Điểm VC Admin duyệt", 13),
    "LAP_DAT": ("Điểm LĐ Admin duyệt", 14),
}
ROLE_MODES = {
    "VC": ("VAN_CHUYEN",),
    "KTV": ("LAP_DAT",),
    "VC+KTV": ("VAN_CHUYEN", "LAP_DAT"),
}


def site_ids(text):
    result = [x.strip() for x in str(text or "").split(",") if x.strip()]
    if len(result) != len(set(result)):
        raise ValueError("Danh sách quyền địa điểm có mã điểm trùng.")
    return tuple(result)


def site_text(ids):
    values = sorted(set(ids))
    if any(not x or "," in x for x in values):
        raise ValueError("Mã địa điểm không hợp lệ.")
    return ",".join(values)


def active_registration(registrations, project, team_id):
    rows = [r for r in registrations if
            r.get("Trạng thái duyệt") == "Đã duyệt" and
            r.get("Mã dự án đăng ký") == project and
            r.get("Mã đội được gán") == team_id]
    owned = [r for r in rows if any(
        str(r.get(name) or "").strip() for name, _ in RIGHT_FIELDS.values())]
    if len(owned) > 1:
        raise ValueError("Đội có nhiều hồ sơ mang quyền địa điểm; cần đối soát.")
    if owned:
        return owned[0]
    if len(rows) == 1:
        return rows[0]
    if rows:
        raise ValueError("Hồ sơ đã duyệt của đội bị trùng; cần đối soát.")
    raise ValueError("Đội chưa có hồ sơ đăng ký đã duyệt.")


def approved_team_site_overview(team, registrations, locations, tasksets):
    """Display already-approved site rights even before SKU allocation.

    This is read-only. Actual VC/KTV reports still require allocated tasks.
    """
    project = str(team.get("Mã dự án") or "").strip()
    team_id = str(team.get("Mã đội") or "").strip()
    role = team.get("Loại nhiệm vụ")
    if (not project or not team_id or role not in ROLE_MODES or
            team.get("Trạng thái") != "Hoạt động"):
        raise ValueError("Đội chưa hoạt động hoặc thiếu mã dự án/chuyên môn.")
    registration = active_registration(registrations, project, team_id)
    project_sites = {r.get("Mã điểm"): r for r in locations
                     if r.get("Mã dự án") == project and r.get("Mã điểm")}
    overview = []
    for tab in ROLE_MODES[role]:
        field, _ = RIGHT_FIELDS[tab]
        _, assigned_field, _ = TASK_SCHEMA[tab]
        for site_id in site_ids(registration.get(field)):
            site = project_sites.get(site_id)
            if site is None:
                raise ValueError("Địa điểm đã duyệt không còn thuộc dự án: " + site_id)
            tasks = [r for r in tasksets.get(tab, [])
                     if r.get("Mã dự án") == project and
                     r.get("Mã điểm") == site_id]
            linked = sum(r.get(assigned_field) == team_id for r in tasks)
            if site.get("Trạng thái") != "Hoạt động":
                status = "Địa điểm tạm dừng – cần Admin kiểm tra"
            elif not tasks:
                status = "Đã duyệt điểm – Chưa phân bổ SKU"
            elif linked == len(tasks):
                status = "Đã duyệt điểm – Đã có nhiệm vụ SKU"
            else:
                status = "Đã duyệt điểm – Cần đối soát nhiệm vụ SKU"
            overview.append({
                "site_id": site_id,
                "site_name": site.get("Tên xã/phường/đơn vị") or site_id,
                "role": "Vận chuyển" if tab == "VAN_CHUYEN" else "Lắp đặt",
                "sku_tasks": len(tasks),
                "linked_tasks": linked,
                "status": status,
            })
    return overview


def owner_index(registrations, teams, project):
    """(task tab, site id) -> (team id, registration record)."""
    team_by_id = {t.get("Mã đội"): t for t in teams
                  if t.get("Mã dự án") == project and t.get("Mã đội")}
    result = {}
    for r in registrations:
        if (r.get("Trạng thái duyệt") != "Đã duyệt" or
                r.get("Mã dự án đăng ký") != project):
            continue
        tid = str(r.get("Mã đội được gán") or "")
        has_rights = any(str(r.get(name) or "").strip()
                         for name, _ in RIGHT_FIELDS.values())
        if not has_rights:
            continue
        team = team_by_id.get(tid)
        if not team:
            raise ValueError("Có quyền địa điểm của đội không thuộc dự án.")
        permitted = ROLE_MODES.get(team.get("Loại nhiệm vụ"), ())
        if not permitted:
            raise ValueError("Đội đã duyệt có chuyên môn không hợp lệ.")
        for tab, (field, _) in RIGHT_FIELDS.items():
            assigned = site_ids(r.get(field))
            if assigned and tab not in permitted:
                raise ValueError("Hồ sơ có quyền địa điểm sai chuyên môn.")
            for pid in assigned:
                key = (tab, pid)
                if key in result:
                    raise ValueError(
                        "Địa điểm đang cấp trùng cho hai đội cùng chuyên môn: " +
                        pid)
                result[key] = (tid, r)
    return result


def allocation_owners(registrations, teams, project):
    """Current rights to bind future SKU tasks; stopped teams cannot receive."""
    index = owner_index(registrations, teams, project)
    states = {t.get("Mã đội"): t.get("Trạng thái")
              for t in teams if t.get("Mã dự án") == project}
    return {key: tid for key, (tid, _) in index.items()
            if states.get(tid) == "Hoạt động"}


def task_proven(task, tab, hub_rows, project):
    """Any status, report or signed/uncertain hub custody blocks site release."""
    _, owner_field, waiting = TASK_SCHEMA[tab]
    if task.get("Trạng thái") != waiting:
        return True
    if any(str(task.get(name) or "").strip() for name in (
            "Mã báo cáo", "SL thực tế", "Thời gian báo cáo",
            "Link ảnh", "Link ảnh báo cáo")):
        return True
    pid, sku = task.get("Mã điểm"), task.get("SKU")
    return any(r.get("Mã dự án") == project and
               r.get("Mã điểm") == pid and r.get("SKU") == sku and
               r.get("Trạng thái") == "KTV đã nhận tại tập kết"
               for r in hub_rows)


def approval_task_plan(project, specialty, team_id, selected_ids,
                       locations, registrations, teams, tasksets, hub_rows):
    """Reject double owners; assign existing pending tasks if allocation exists."""
    tabs = ROLE_MODES.get(specialty)
    selected = tuple(selected_ids)
    if not tabs or not selected or len(selected) != len(set(selected)):
        raise ValueError("Chuyên môn hoặc danh sách địa điểm không hợp lệ.")
    valid = {r.get("Mã điểm") for r in locations if
             r.get("Mã dự án") == project and
             r.get("Trạng thái") == "Hoạt động"}
    if not set(selected).issubset(valid):
        raise ValueError("Địa điểm đã chọn không thuộc dự án đang hoạt động.")
    owners = owner_index(registrations, teams, project)
    plan = {}
    for tab in tabs:
        for pid in selected:
            current = owners.get((tab, pid))
            if current and current[0] != team_id:
                raise ValueError("Địa điểm " + pid +
                    " đang được giao cho đội khác. ADMIN phải thu hồi điểm "
                    "chưa thực hiện ở đội cũ trước khi duyệt đội mới.")
        id_field, owner_field, waiting = TASK_SCHEMA[tab]
        proposed = []
        for task in tasksets.get(tab, []):
            if (task.get("Mã dự án") != project or
                    task.get("Mã điểm") not in selected):
                continue
            assigned = str(task.get(owner_field) or "")
            if assigned and assigned != team_id:
                raise ValueError("Điểm " + str(task.get("Mã điểm")) +
                                 " vẫn có nhiệm vụ của đội cũ.")
            if task_proven(task, tab, hub_rows, project):
                if assigned != team_id:
                    raise ValueError("Điểm đã có báo cáo/bàn giao; phải đối soát.")
                continue
            if not assigned:
                if not task.get(id_field) or not isinstance(task.get("_row"), int):
                    raise ValueError("Nhiệm vụ chờ giao có dòng hoặc mã không hợp lệ.")
                proposed.append(task)
        plan[tab] = proposed
    return plan


def right_updates_for_approval(row, specialty, selected_ids):
    if not isinstance(row, int) or row < 2:
        raise ValueError("Hồ sơ duyệt thiếu số dòng.")
    return {tab: site_text(selected_ids if tab in
            ROLE_MODES[specialty] else ())
            for tab in RIGHT_FIELDS}


def right_cell_request(sheet_id, row, tab, value):
    name, column = RIGHT_FIELDS[tab]
    if not isinstance(row, int) or row < 2:
        raise ValueError("Dòng quyền địa điểm không hợp lệ.")
    return {"updateCells": {
        "range": {"sheetId": sheet_id, "startRowIndex": row - 1,
                  "endRowIndex": row, "startColumnIndex": column,
                  "endColumnIndex": column + 1},
        "rows": [{"values": [{"userEnteredValue": {"stringValue": value}}]}],
        "fields": "userEnteredValue"
    }}


def supplemental_site_plan(team, mode, selected_ids, locations, registrations,
                           teams, tasksets, hub_rows):
    """Add *unowned* sites to an approved team and link all waiting SKU tasks.

    Registration rights and task assignments must be committed in ONE Sheets
    batch. Existing rights, already assigned work and proof remain unchanged.
    """
    selected = tuple(selected_ids)
    if (mode not in allowed_modes(team) or not selected or
            len(selected) != len(set(selected))):
        raise ValueError("Chọn chuyên môn hợp lệ và điểm bổ sung không trùng.")
    project, team_id = team.get("Mã dự án"), team.get("Mã đội")
    if not project or not team_id or team.get("Trạng thái") != "Hoạt động":
        raise ValueError("Đội nhận điểm không còn hoạt động.")
    registration = active_registration(registrations, project, team_id)
    owners = owner_index(registrations, teams, project)
    for tab in ROLE_TABS[mode]:
        for pid in selected:
            if (tab, pid) in owners:
                raise ValueError("Điểm " + pid +
                                 " đã có đội được duyệt; không phải điểm bổ sung trống.")
    valid_sites = {r.get("Mã điểm") for r in locations if
                   r.get("Mã dự án") == project and
                   r.get("Trạng thái") == "Hoạt động"}
    if not set(selected).issubset(valid_sites):
        raise ValueError("Điểm bổ sung không thuộc dự án đang hoạt động.")
    # Rights may be approved BEFORE any SKU allocation. Subsequent allocation
    # automatically binds new tasks from these approved rights.
    tasks = {}
    for tab in ROLE_TABS[mode]:
        id_key, owner_key, waiting = TASK_SCHEMA[tab]
        pending = []
        for pid in selected:
            associated = [r for r in tasksets.get(tab, []) if
                          r.get("Mã dự án") == project and r.get("Mã điểm") == pid]
            if any(
                    r.get(owner_key) or r.get("Trạng thái") != waiting or
                    task_proven(r, tab, hub_rows, project)
                    for r in associated):
                raise ValueError("Điểm " + pid +
                                 " đã có việc/bằng chứng hoặc không còn nguyên trạng chờ giao.")
            for row in associated:
                if (not row.get(id_key) or
                        not isinstance(row.get("_row"), int) or row["_row"] < 2):
                    raise ValueError("Nhiệm vụ chờ giao thiếu mã hoặc số dòng.")
                pending.append(row)
        ids = [r[id_key] for r in pending]
        if len(ids) != len(set(ids)) or len({r["_row"] for r in pending}) != len(pending):
            raise ValueError("Trùng nhiệm vụ hoặc số dòng tại điểm bổ sung.")
        tasks[tab] = pending
    new_rights = {}
    for tab in ROLE_TABS[mode]:
        field, _ = RIGHT_FIELDS[tab]
        new_rights[tab] = site_text(
            (*site_ids(registration.get(field)), *selected))
    return {
        "project": project, "team_id": team_id, "mode": mode,
        "sites": selected, "registration_row": registration.get("_row"),
        "registration_id": registration.get("Mã đăng ký"),
        "tasks": tasks, "new_rights": new_rights,
        "old_rights": {tab: site_text(site_ids(registration.get(RIGHT_FIELDS[tab][0])))
                       for tab in ROLE_TABS[mode]},
    }


def supplemental_site_signature(plan):
    """All critical inputs must match a fresh read before committing."""
    return (
        plan["project"], plan["team_id"], plan["mode"],
        tuple(sorted(plan["sites"])), plan["registration_id"],
        plan["registration_row"],
        tuple(sorted(plan["old_rights"].items())),
        tuple(sorted(plan["new_rights"].items())),
        tuple(sorted((tab, r.get(TASK_SCHEMA[tab][0]), r.get("_row"))
                     for tab, rows in plan["tasks"].items() for r in rows)),
    )


def supplemental_site_requests(plan, sheet_ids):
    """Atomic registration rights + task G-column updates; never touch stock."""
    from preview_assignment import compact_site_assignment_requests
    requests = (compact_site_assignment_requests(
        sheet_ids, plan["tasks"], plan["team_id"])
        if any(plan["tasks"].values()) else [])
    if "DANG_KY_THANH_VIEN" not in sheet_ids:
        raise ValueError("Thiếu bảng quyền địa điểm đã duyệt.")
    for tab, value in plan["new_rights"].items():
        requests.append(right_cell_request(
            sheet_ids["DANG_KY_THANH_VIEN"],
            plan["registration_row"], tab, value))
    return requests
