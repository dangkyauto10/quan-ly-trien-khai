"""PREVIEW-only per-site progress rules shared by report and reconciliation paths.

Installation is complete only after a KTV task has a completed report and
the actual installed quantity equals its assigned quantity. VC delivery,
including a signed hub handover, is tracked separately and never substitutes
for installation evidence. No external reads or writes.
"""
from decimal import Decimal, InvalidOperation


def _amount(raw):
    if raw is None or str(raw).strip() == "":
        return None
    try:
        result = Decimal(str(raw).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() and result >= 0 else None


def site_progress(project, point, transports, installations,
                  statuses=None, actuals=None):
    """Summarize one project's location without mixing project IDs."""
    statuses = statuses or {}
    actuals = actuals or {}
    vc = [r for r in transports
          if r.get("Mã dự án") == project and r.get("Mã điểm") == point]
    ld = [r for r in installations
          if r.get("Mã dự án") == project and r.get("Mã điểm") == point]

    def state(r, key):
        task_id = str(r.get(key) or "")
        return statuses.get(task_id, r.get("Trạng thái") or "")

    def complete(r, key, planned_key, done_status):
        task_id = str(r.get(key) or "")
        if state(r, key) != done_status:
            return False
        planned = _amount(r.get(planned_key))
        actual = _amount(actuals.get(task_id, r.get("SL thực tế")))
        return planned is not None and planned > 0 and actual == planned

    vc_done = sum(
        complete(r, "Mã nhiệm vụ VC", "SL giao", "Đã giao hàng")
        or complete(r, "Mã nhiệm vụ VC", "SL giao", "Đã bàn giao tập kết")
        for r in vc)
    ld_done = sum(complete(r, "Mã nhiệm vụ LD", "SL lắp", "Đã lắp đặt")
                  for r in ld)
    finished = bool(ld) and ld_done == len(ld)
    started = any(state(r, "Mã nhiệm vụ VC") not in ("", "Chưa giao")
                  for r in vc)
    started |= any(state(r, "Mã nhiệm vụ LD") not in ("", "Chưa lắp")
                   for r in ld)
    status = ("Hoàn thành" if finished else
              "Đang thực hiện" if started else "Chưa thực hiện")
    return {"total_vc": len(vc), "vc_done": vc_done,
            "total_ld": len(ld), "ld_done": ld_done, "status": status}
