"""Preview-only multi-SKU allocation planning and atomic Google Sheets write spec.

This module has no external imports and is pure: UI must re-read live Google
Sheets before committing any rows. No stock or assignments are modified here.
"""
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict
import math
from preview_progress_rules import site_progress


def quantity(value):
    """Return a finite nonnegative number, capped at three decimal places."""
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        raise ValueError("Thiếu số lượng.")
    try:
        n = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Số lượng không hợp lệ.") from None
    if not n.is_finite() or n < 0 or n.as_tuple().exponent < -3:
        raise ValueError("Số lượng phải >= 0, có tối đa 3 chữ số thập phân.")
    return n


def inventory_by_sku(project, imports, allocations):
    """Build project stock from ALL receipts minus all recorded allocations."""
    stock, metadata, issues = defaultdict(Decimal), {}, []
    for r in imports:
        if r.get("Mã dự án") != project or not r.get("SKU"):
            continue
        sku = str(r["SKU"]).strip()
        name, unit = str(r.get("Tên hàng hóa", "")).strip(), str(r.get("Đơn vị tính", "")).strip()
        if not name or not unit:
            issues.append(f"{sku}: hàng nhập kho thiếu tên hoặc đơn vị tính.")
        elif sku in metadata and metadata[sku] != (name, unit):
            issues.append(f"{sku}: tên/đơn vị tính giữa các phiếu nhập không thống nhất.")
        else:
            metadata[sku] = (name, unit)
        try:
            stock[sku] += quantity(r.get("SL thực nhận") or 0)
        except ValueError:
            issues.append(f"{sku}: số thực nhận không hợp lệ.")
    for r in allocations:
        if r.get("Mã dự án") != project or not r.get("SKU"):
            continue
        sku = str(r["SKU"]).strip()
        try:
            stock[sku] -= quantity(r.get("SL phân bổ") or 0)
        except ValueError:
            issues.append(f"{sku}: đã phân bổ có số lượng không hợp lệ.")
    for sku, v in stock.items():
        if v < 0:
            issues.append(f"{sku}: tồn kho âm, cần đối soát.")
    return {sku: {"name": v[0], "unit": v[1], "remaining": stock[sku]}
            for sku, v in metadata.items()}, issues




def allocation_waiting_summary(project, imports, allocations):
    """Per-SKU reserved-balance summary; not a physical warehouse stock ledger.

    Total receipts minus reserved allocations reaches zero once all imported
    quantity has been assigned to project locations. Warehouse issues must
    be accounted for separately when physical stock tracking is deployed.
    """
    stock, issues = inventory_by_sku(project, imports, allocations)
    imports_by_sku = defaultdict(Decimal)
    allocated_by_sku = defaultdict(Decimal)
    for row in imports:
        if row.get("Mã dự án") == project and row.get("SKU"):
            try:
                imports_by_sku[str(row["SKU"]).strip()] += quantity(
                    row.get("SL thực nhận") or 0)
            except ValueError:
                pass   # inventory_by_sku records the data-quality error.
    for row in allocations:
        if row.get("Mã dự án") == project and row.get("SKU"):
            try:
                allocated_by_sku[str(row["SKU"]).strip()] += quantity(
                    row.get("SL phân bổ") or 0)
            except ValueError:
                pass
    result = []
    for sku, meta in stock.items():
        result.append({
            "SKU": sku, "Tên hàng hóa": meta["name"], "ĐVT": meta["unit"],
            "Tổng nhập": float(imports_by_sku[sku]),
            "Đã phân bổ": float(allocated_by_sku[sku]),
            "Hàng còn chờ phân bổ": float(meta["remaining"])
        })
    return result, issues


def build_plan(selected_points, skus, defaults, overrides=None):
    """Create list of proposed rows; override only chosen (point,sku) pairs."""
    overrides = overrides or {}
    rows = []
    for point in selected_points:
        pid = point["Mã điểm"]
        amounts = {}
        for sku in skus:
            amounts[sku] = overrides.get((pid, sku), defaults.get(sku, 0))
        rows.append({"Mã điểm": pid, "Tên địa điểm": point.get("Tên xã/phường/đơn vị", ""),
                     "quantities": amounts})
    return rows


def verify_plan(project, plans, inventory, allocations, points, max_lines=3000):
    """Reject any invalid/duplicate lines. Zero means no goods allocated."""
    errors, candidates = [], []
    seen = set()
    validpoints = {x["Mã điểm"]: x for x in points if x.get("Mã dự án") == project
                   and x.get("Mã điểm") and x.get("Trạng thái") == "Hoạt động"}
    prior = {(str(r.get("Mã điểm","")), str(r.get("SKU","")))
             for r in allocations if r.get("Mã dự án") == project}
    sums = defaultdict(Decimal)
    if not plans:
        errors.append("Chưa chọn địa điểm nào.")
    for r in plans:
        pid = r.get("Mã điểm")
        if pid not in validpoints:
            errors.append(f"Điểm {pid} không thuộc dự án hoặc không hoạt động.")
            continue
        for sku, raw in r.get("quantities", {}).items():
            if sku not in inventory:
                errors.append(f"SKU {sku} không thuộc hàng nhập của dự án.")
                continue
            try:
                qty = quantity(raw)
            except ValueError as exc:
                errors.append(f"Điểm {pid}, SKU {sku}: {exc}")
                continue
            if not qty:
                continue
            key = (pid, sku)
            if key in seen:
                errors.append(f"Trùng trong phương án: {pid} / {sku}.")
            if key in prior:
                errors.append(f"Đã phân bổ trước đó: {pid} / {sku}.")
            seen.add(key)
            sums[sku] += qty
            candidates.append((pid, sku, qty))
    if not candidates:
        errors.append("Không có dòng phân bổ nào có số lượng > 0.")
    if len(candidates) > max_lines:
        errors.append(f"Phương án vượt {max_lines} dòng/đợt; chia thành nhiều đợt nhỏ.")
    for sku, requested in sums.items():
        available = inventory[sku]["remaining"]
        if requested > available:
            errors.append(f"{sku}: cần {requested:g} nhưng tồn khả dụng chỉ {available:g}.")
    return errors, candidates, dict(sums)


def _row(values):
    cells = []
    for value in values:
        if isinstance(value, Decimal):
            value = float(value)
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValueError("Không thể ghi số lượng không hữu hạn.")
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            entered = {"numberValue": value}
        else:
            entered = {"stringValue": str(value if value is not None else "")}
        cells.append({"userEnteredValue": entered})
    return {"values": cells}


def atomic_requests(sheet_ids, entries, batch_id, project, inventory, point_names,
                    actor, stamp, existing_tasks=None, progress=None, approved_owners=None):
    """One spreadsheets.batchUpdate for 4 business sheets + progress + journal.

    entries is [(point_id,sku,qty)] pre-validated against freshly loaded data.
    API request validation is all-or-nothing. No external mutable work here.
    """
    required = ("DM_CHUAN", "KHO_PHAN_BO", "VAN_CHUYEN", "LAP_DAT",
                "TIEN_DO", "NHAT_KY_HE_THONG")
    if any(k not in sheet_ids for k in required):
        raise ValueError("Thiếu sheet để phân bổ và ghi nhận tiến độ.")
    approved_owners = approved_owners or {}
    records = {k: [] for k in required}
    vc_per_point = Counter()
    ld_per_point = Counter()
    for i, (pid, sku, qty) in enumerate(entries, 1):
        alloc_id = f"{batch_id}-{i:05d}"
        name, unit = inventory[sku]["name"], inventory[sku]["unit"]
        vc_per_point[pid] += 1
        ld_per_point[pid] += 1
        records["DM_CHUAN"].append([batch_id, project, sku, name, unit, qty, pid,
                                   point_names[pid], "Đã phân bổ", actor, stamp, "Hàng loạt"])
        records["KHO_PHAN_BO"].append([alloc_id, batch_id, project, pid, sku, name,
                                      unit, qty, stamp, "Đã phân bổ", ""])
        records["VAN_CHUYEN"].append([f"VC-{alloc_id}", alloc_id, project, pid,
                                     sku, qty, approved_owners.get(("VAN_CHUYEN", pid), ""),
                                      "Chưa giao", "", "", "", "", "", ""])
        records["LAP_DAT"].append([f"LD-{alloc_id}", alloc_id, project, pid,
                                  sku, qty, approved_owners.get(("LAP_DAT", pid), ""),
                                   "Chưa lắp", "", "", "", "", "", ""])
    old_progress = {}
    for row in (progress or []):
        if row.get("Mã dự án") != project:
            continue
        pid=row.get("Mã điểm")
        if pid in old_progress:
            raise ValueError("TIEN_DO có nhiều dòng cùng dự án và địa điểm.")
        old_progress[pid]=row
    vc_old=(existing_tasks or {}).get("VAN_CHUYEN", [])
    ld_old=(existing_tasks or {}).get("LAP_DAT", [])
    new_progress_updates = []
    for pid in vc_per_point:
        prior = old_progress.get(pid)
        snapshot=site_progress(project,pid,vc_old,ld_old)
        v_count=snapshot["total_vc"]+vc_per_point[pid]
        l_count=snapshot["total_ld"]+ld_per_point[pid]
        # Adding new SKU tasks makes a previously finished site incomplete.
        status=("Chưa thực hiện" if snapshot["status"]=="Chưa thực hiện"
                else "Đang thực hiện")
        vals=[project,pid,point_names[pid],v_count,snapshot["vc_done"],
              l_count,snapshot["ld_done"],status,stamp]
        if prior:
            row_num = prior.get("_row")
            if not isinstance(row_num,int) or row_num < 2:
                raise ValueError("Dòng tiến độ hiện tại không có vị trí ghi hợp lệ.")
            new_progress_updates.append({"updateCells":{
                "start":{"sheetId":sheet_ids["TIEN_DO"],"rowIndex":row_num-1,"columnIndex":0},
                "rows":[_row(vals)],"fields":"userEnteredValue"}})
        else:
            records["TIEN_DO"].append(vals)
    records["NHAT_KY_HE_THONG"].append(
        [stamp,actor,"ADMIN","PHÂN BỔ HÀNG LOẠT","KHO_PHAN_BO",batch_id,"OK",
         f"{project}: {len(entries)} dòng, {len(vc_per_point)} địa điểm"])
    requests = []
    for key in required:
        if records[key]:
            requests.append({"appendCells":{"sheetId":sheet_ids[key],
                "rows":[_row(values) for values in records[key]],
                "fields":"userEnteredValue"}})
    requests.extend(new_progress_updates)
    return requests
