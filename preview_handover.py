"""Read-only handover board for installation team leaders.

Only receives LD tasks belonging to the logged-in team; VC rows are
cross-referenced by exact (project, point, SKU), never displayed as an
unrestricted all-project dashboard.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from preview_hub import received_by_site


DONE_VC = ("Đã giao hàng", "Đã giao một phần", "Giao một phần")
DONE_LD = "Đã lắp đặt"


def quantity(value):
    text=str(value if value is not None else "").strip().replace(" ", "")
    if not text:
        return None
    try:
        parsed=Decimal(text.replace(",", "."))
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() and parsed>=0 else None


def count_text(value):
    value=Decimal(value)
    return str(int(value)) if value==value.to_integral_value() else format(value,"f")


def installer_handover(team_id, ld_rows, vc_rows, place_rows, hub_rows=None):
    """Return summaries ONLY for locations assigned to team_id.

    An installed task does not prove delivery. A 'ready' site requires
    completed transport evidence for *every* assigned SKU and quantity.
    """
    if not team_id:
        return []
    locations={(p.get("Mã dự án"),p.get("Mã điểm")):
               p.get("Tên xã/phường/đơn vị","")
               for p in place_rows if p.get("Mã dự án") and p.get("Mã điểm")}
    per_site=defaultdict(list)
    for row in ld_rows:
        if row.get("Mã đội KTV") != team_id:
            continue
        key=(row.get("Mã dự án"),row.get("Mã điểm"))
        if not all(key) or not row.get("SKU"):
            continue
        per_site[key].append(row)

    vc_index=defaultdict(list)
    for row in vc_rows:
        key=(row.get("Mã dự án"),row.get("Mã điểm"),row.get("SKU"))
        if key[:2] not in per_site:
            continue
        vc_index[key].append(row)

    result=[]
    by_project={p:received_by_site(hub_rows or [],p,team_id)
                for p,_ in per_site}
    for (project,point), assigned_rows in per_site.items():
        details=[]
        all_completed=True
        has_delivery=False
        all_ready=True
        needs_check=False
        some_hub=False
        all_hub=True
        has_installed_partial=False
        for row in assigned_rows:
            sku=row.get("SKU","")
            planned=quantity(row.get("SL lắp"))
            if planned is None or planned==0:
                planned=Decimal(0)
                needs_check=True
            delivered=Decimal(0)
            received_hub=by_project[project].get((project,point,sku),Decimal(0))
            if received_hub>0:
                some_hub=True
            if received_hub<planned:
                all_hub=False
            seen_transport=False
            issues=[]
            for vc in vc_index.get((project,point,sku),()):
                seen_transport=True
                if vc.get("Trạng thái") in DONE_VC:
                    actual=quantity(vc.get("SL thực tế"))
                    if actual is None:
                        issues.append("VC báo giao nhưng thiếu SL thực tế")
                        needs_check=True
                    else:
                        delivered+=actual
                elif vc.get("SL thực tế") and quantity(vc.get("SL thực tế")):
                    # Quantity in an open task alone is not a confirmed receipt.
                    issues.append("VC có số lượng nhưng chưa xác nhận trạng thái")
                    needs_check=True
            if not seen_transport and received_hub<planned:
                needs_check=True
                issues.append("Không có VC giao tận xã hoặc biên bản tập kết đủ hàng")
            if received_hub>planned:
                needs_check=True
                issues.append("Bàn giao tập kết vượt định mức của xã")
            if delivered>0 and received_hub>0:
                needs_check=True
                issues.append("Trùng hình thức giao trực tiếp và giao tập kết; cần đối soát")
            if delivered>0:
                has_delivery=True
            if delivered<planned and received_hub<planned:
                all_ready=False
            if delivered>planned:
                needs_check=True
                issues.append("VC giao vượt số lượng giao cho đội lắp")
            installed=(row.get("Trạng thái")==DONE_LD)
            partial_install=row.get("Trạng thái")=="Đã lắp một phần"
            actual_install=(quantity(row.get("SL thực tế"))
                            if installed or partial_install else Decimal(0))
            if partial_install:
                if actual_install is None or actual_install<=0 or actual_install>=planned:
                    needs_check=True
                    issues.append("SL lắp một phần không hợp lệ")
                else:
                    has_installed_partial=True
            if installed and (actual_install is None or actual_install<planned):
                needs_check=True
                issues.append("Lắp đặt xong nhưng thiếu SL thực tế")
            if not installed:
                all_completed=False
            details.append({
                "sku":sku,
                "need":count_text(planned),
                "delivered":count_text(delivered),
                "hub_received":count_text(received_hub),
                "installed":count_text(actual_install or 0),
                "delivery_ready":bool(planned>0 and
                                       (delivered>=planned or received_hub>=planned)
                                       and not issues),
                "hub_ready":bool(planned>0 and received_hub>=planned and not issues),
                "issues":issues
            })
        if needs_check:
            label="Cần đối soát"
        elif all_completed and all_ready:
            label="Đã lắp xong"
        elif all_ready and details and has_installed_partial:
            label="Đang lắp một phần"
        elif all_ready and details and all_hub and some_hub:
            label="Sẵn sàng lắp (tập kết)"
        elif all_ready and details:
            label="Sẵn sàng lắp"
        elif some_hub:
            label="Đã tập kết một phần"
        elif has_delivery:
            label="Đã giao một phần"
        else:
            label="Chưa giao"
        result.append({
            "project":project,"point_id":point,
            "name":locations.get((project,point)) or point,
            "status":label,"sku_count":len(details),"details":details,
            "ready":label in ("Sẵn sàng lắp","Sẵn sàng lắp (tập kết)",
                              "Đang lắp một phần")
        })
    order={"Sẵn sàng lắp":0,"Sẵn sàng lắp (tập kết)":0,
           "Đang lắp một phần":0,
           "Đã giao một phần":1,"Đã tập kết một phần":1,
           "Cần đối soát":2,"Chưa giao":3,"Đã lắp xong":4}
    return sorted(result,key=lambda p:(order.get(p["status"],9),
                                       p["name"].casefold(),p["project"],p["point_id"]))


def site_may_complete_installation(project, point, installer_tasks, all_vc,
                                   hub_rows=None):
    """Require sufficient actual direct VC delivery OR accepted hub receipt.

    A hub acceptance is NOT per-site VC delivery. Completion is permitted
    only for the actual installing crew's allocated site after evidence exists.
    """
    selected=[t for t in installer_tasks
              if t.get("Mã dự án")==project and t.get("Mã điểm")==point]
    tids={t.get("Mã đội KTV") for t in selected}
    if len(tids)!=1 or not next(iter(tids)) or not selected:
        return False
    result=installer_handover(next(iter(tids)),selected,all_vc,[],
                              hub_rows=hub_rows)
    return bool(result and result[0]["status"] in (
        "Sẵn sàng lắp","Sẵn sàng lắp (tập kết)",
        "Đang lắp một phần"))
