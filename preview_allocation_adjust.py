"""ADMIN correction of allocated quantities, limited to untouched VC/KTV tasks.

Pure planner: this module never talks to Google or modifies application state.
The caller must re-read all relevant sheets LIVE before one batchUpdate.
"""
from collections import defaultdict
from decimal import Decimal
from preview_bulk_allocation import inventory_by_sku, quantity

REQUIRED = ("DM_CHUAN", "KHO_PHAN_BO", "VAN_CHUYEN", "LAP_DAT", "NHAT_KY_HE_THONG")


def _unique(rows, predicate, label):
    matches = [r for r in rows if predicate(r)]
    if len(matches) != 1:
        raise ValueError(f"{label}: cần đúng 1 dòng, hiện có {len(matches)}.")
    return matches[0]


def _position(row, label):
    number = row.get("_row")
    if not isinstance(number, int) or number < 2:
        raise ValueError(f"{label}: thiếu số dòng hợp lệ để chỉnh sửa.")
    return number - 1


def _unstarted(task, expected, label):
    if task.get("Trạng thái") != expected:
        raise ValueError(f"{label}: đã bắt đầu hoặc trạng thái bất thường; không được sửa phân bổ.")
    fields = list(task)
    if "Trạng thái" not in fields:
        raise ValueError(f"{label}: thiếu cột trạng thái.")
    following = fields[fields.index("Trạng thái") + 1:]
    if any(str(task.get(field, "")).strip() for field in following if field != "_row"):
        raise ValueError(f"{label}: đã có chứng từ/thời điểm; cần đối soát riêng.")


def _number_cell(sheet_id, row, column, new):
    return {"updateCells": {
        "start": {"sheetId": sheet_id, "rowIndex": row, "columnIndex": column},
        "rows": [{"values": [{"userEnteredValue": {"numberValue": float(new)}}]}],
        "fields": "userEnteredValue"
    }}


def prepare_quantity_corrections(project, changes, snapshots, sheet_ids, actor, stamp):
    """Return one atomic Sheets request list for (allocation_id, old, new) edits.

    Zero/negative quantities and started transport/installation are rejected.
    Any actual report or hub handover at a selected location blocks editing.
    """
    if not project or not actor or not stamp or not changes:
        raise ValueError("Thiếu dự án, người thực hiện, thời gian hoặc dòng cần sửa.")
    if any(name not in sheet_ids for name in REQUIRED):
        raise ValueError("Thiếu mã bảng cần ghi đồng bộ.")
    for name in (*REQUIRED[:4], "NHAP_KHO", "BAO_CAO_TRIEN_KHAI", "BAN_GIAO_TAP_KET"):
        if name not in snapshots:
            raise ValueError("Thiếu dữ liệu đối soát: " + name)
    stock, errors = inventory_by_sku(
        project, snapshots["NHAP_KHO"], snapshots["KHO_PHAN_BO"])
    if errors:
        raise ValueError("Tồn kho chưa khớp: " + "; ".join(errors[:3]))
    requests, audit_rows, difference = [], [], defaultdict(Decimal)
    used = set()
    for alloc_id, old_raw, new_raw in changes:
        if alloc_id in used:
            raise ValueError("Trùng mã phân bổ trong đề nghị sửa: " + alloc_id)
        used.add(alloc_id)
        old, new = quantity(old_raw), quantity(new_raw)
        if new <= 0 or old <= 0 or old == new:
            raise ValueError("Số lượng mới phải > 0 và khác số cũ; thu hồi về 0 là quy trình riêng.")
        allocation = _unique(snapshots["KHO_PHAN_BO"],
            lambda r: r.get("Mã phân bổ") == alloc_id and r.get("Mã dự án") == project,
            "KHO_PHAN_BO " + alloc_id)
        if allocation.get("Trạng thái") != "Đã phân bổ" or quantity(allocation.get("SL phân bổ")) != old:
            raise ValueError("Số lượng/trạng thái vừa thay đổi; hãy tải lại trước khi sửa: " + alloc_id)
        pid, sku, batch = (allocation.get("Mã điểm"), allocation.get("SKU"),
                           allocation.get("Mã đợt phân bổ"))
        if not pid or not sku or not batch or sku not in stock:
            raise ValueError("Thiếu thông tin điểm/SKU/đợt: " + alloc_id)
        dm = _unique(snapshots["DM_CHUAN"], lambda r:
            r.get("Mã đợt phân bổ") == batch and r.get("Mã dự án") == project
            and r.get("Mã điểm") == pid and r.get("SKU") == sku,
            "DM_CHUAN " + alloc_id)
        vc = _unique(snapshots["VAN_CHUYEN"], lambda r:
            r.get("Mã phân bổ") == alloc_id and r.get("Mã dự án") == project,
            "VAN_CHUYEN " + alloc_id)
        ld = _unique(snapshots["LAP_DAT"], lambda r:
            r.get("Mã phân bổ") == alloc_id and r.get("Mã dự án") == project,
            "LAP_DAT " + alloc_id)
        for row, name, field in ((dm, "DM_CHUAN", "SL phân bổ"),
                                 (vc, "VAN_CHUYEN", "SL giao"),
                                 (ld, "LAP_DAT", "SL lắp")):
            if quantity(row.get(field)) != old:
                raise ValueError(name + ": số lượng lệch KHO_PHAN_BO, không được sửa tự động.")
        _unstarted(vc, "Chưa giao", "VC " + alloc_id)
        _unstarted(ld, "Chưa lắp", "LĐ " + alloc_id)
        for name in ("BAO_CAO_TRIEN_KHAI", "BAN_GIAO_TAP_KET"):
            if any(r.get("Mã dự án") == project and r.get("Mã điểm") == pid
                   for r in snapshots[name]):
                raise ValueError("Điểm " + pid + " đã có báo cáo/bàn giao; cần đối soát riêng.")
        difference[sku] += new - old
        for name, row, column in (("DM_CHUAN", dm, 5),
                                  ("KHO_PHAN_BO", allocation, 7),
                                  ("VAN_CHUYEN", vc, 5),
                                  ("LAP_DAT", ld, 5)):
            requests.append(_number_cell(sheet_ids[name], _position(row, name), column, new))
        audit_rows.append([stamp, actor, "ADMIN", "ĐIỀU CHỈNH PHÂN BỔ",
                           "KHO_PHAN_BO", alloc_id, "OK",
                           f"{project}/{pid}/{sku}: {old:g} -> {new:g}; đợt {batch}"])
    for sku, delta in difference.items():
        if delta > stock[sku]["remaining"]:
            raise ValueError(f"{sku}: bổ sung {delta:g} vượt tồn còn phân bổ {stock[sku]['remaining']:g}.")
    requests.append({"appendCells": {
        "sheetId": sheet_ids["NHAT_KY_HE_THONG"],
        "rows": [{"values": [{"userEnteredValue": {"stringValue": str(v)}}
                            for v in row]} for row in audit_rows],
        "fields": "userEnteredValue"
    }})
    return requests, dict(difference)
