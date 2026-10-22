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
