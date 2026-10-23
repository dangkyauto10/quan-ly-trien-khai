"""Read-only project progress calculations for ADMIN/LANH_DAO PREVIEW.

Do not mistake warehouse allocation, task completion, or reported installation
for physical warehouse inventory. No writes and no personal contact details.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation


VC_DONE = "Đã giao hàng"
LD_DONE = "Đã lắp đặt"
SYNCED = "Đã đồng bộ"


def qty(value):
    text = str(value if value is not None else "").strip().replace(" ", "")
    if not text:
        return Decimal("0")
    try:
        number = Decimal(text.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Số lượng không hợp lệ: "+repr(text[:32])) from exc
    if not number.is_finite() or number < 0:
        raise ValueError("Số lượng âm hoặc vô hạn.")
    return number


def display_amount(value):
    number = Decimal(value)
    return int(number) if number == number.to_integral_value() else float(number)


def site_label(site):
    return site.get("Tên xã/phường/đơn vị", "") or site.get("Mã điểm", "")


def build_progress(project_id, projects, sites, receipts, allocations,
                   transport, installs, reports, teams):
    """Return a consistent snapshot filtered by project (or 'Tất cả').

    Site delivered/installed counts require a matching status AND confirmed
    actual quantities for EVERY SKU of the site, not just completed task count.
    """
    all_projects={r.get("Mã dự án") for r in projects if r.get("Mã dự án")}
    selected=all_projects if project_id == "Tất cả" else {project_id}
    if not selected or not selected.issubset(all_projects):
        raise ValueError("Dự án không thuộc danh mục cho phép.")

    def project_rows(rows):
        return [r for r in rows if r.get("Mã dự án") in selected]

    ps=project_rows(sites)
    al=project_rows(allocations)
    vc=project_rows(transport)
    ld=project_rows(installs)
    rec=project_rows(receipts)
    rs=project_rows(reports)
    team_rows=project_rows(teams)
    name_by_team={r.get("Mã đội"):r.get("Tên đội/đội trưởng","")
                  for r in team_rows if r.get("Mã đội")}

    anomalies=[]
    site_index={}
    for r in ps:
        key=(r.get("Mã dự án"),r.get("Mã điểm"))
        if not key[1]:
            continue
        if key in site_index:
            anomalies.append("Trùng mã điểm trong dự án: "+str(key))
            continue
        site_index[key]=r

    allocations_by_key=defaultdict(Decimal)
    product_names={}
    row_counts=defaultdict(int)
    for r in al:
        key=(r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
        if not all(key):
            anomalies.append("Có dòng phân bổ thiếu dự án/điểm/SKU.")
            continue
        try:
            amount=qty(r.get("SL phân bổ"))
        except ValueError:
            anomalies.append("SL phân bổ không hợp lệ tại "+str(key))
            continue
        allocations_by_key[key]+=amount
        row_counts[key]+=1
        product_names[(key[0],key[2])]=(r.get("Tên hàng hóa",""),r.get("ĐVT",""))
    for key,count in row_counts.items():
        if count>1:
            anomalies.append("SKU phân bổ nhiều dòng tại cùng điểm: "+str(key))
        if (key[0],key[1]) not in site_index:
            anomalies.append("Phân bổ cho điểm không có trong danh sách: "+str(key[:2]))
    receipt_amount=defaultdict(Decimal)
    for r in rec:
        key=(r.get("Mã dự án"),r.get("SKU"))
        if not all(key):
            continue
        try:
            receipt_amount[key]+=qty(r.get("SL thực nhận"))
        except ValueError:
            anomalies.append("Phiếu nhập có SL lỗi: "+str(key))
        product_names[key]=(r.get("Tên hàng hóa",""),r.get("Đơn vị tính",""))

    def task_index(rows, id_col, team_col, closed):
        index=defaultdict(list)
        for r in rows:
            key=(r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))
            if not all(key):
                anomalies.append("Nhiệm vụ thiếu dự án/điểm/SKU.")
                continue
            index[key].append(r)
        return index

    vci=task_index(vc,"Mã nhiệm vụ VC","Mã đội VC",VC_DONE)
    ldi=task_index(ld,"Mã nhiệm vụ LD","Mã đội KTV",LD_DONE)

    def accomplished(rows, done):
        value=Decimal("0")
        for r in rows:
            if r.get("Trạng thái") != done:
                continue
            # Missing actual quantity cannot prove a full delivery.
            raw=r.get("SL thực tế")
            if raw is None or str(raw).strip()=="":
                anomalies.append("Nhiệm vụ hoàn thành thiếu SL thực tế: "+
                                 str(r.get("Mã nhiệm vụ VC") or r.get("Mã nhiệm vụ LD","")))
                continue
            try:
                value+=qty(raw)
            except ValueError:
                anomalies.append("Nhiệm vụ hoàn thành có SL thực tế sai.")
        return value

    by_point=defaultdict(list)
    totals=defaultdict(lambda:{"allocated":Decimal("0"),"vc":Decimal("0"),
                                "ld":Decimal("0")})
    for key, amount in allocations_by_key.items():
        project, pid, sku=key
        vrows=vci.get(key,[])
        lrows=ldi.get(key,[])
        delivered=accomplished(vrows,VC_DONE)
        installed=accomplished(lrows,LD_DONE)
        totals[(project,sku)]["allocated"]+=amount
        totals[(project,sku)]["vc"]+=delivered
        totals[(project,sku)]["ld"]+=installed
        if amount>0:
            by_point[(project,pid)].append({
                "sku":sku, "planned":amount,
                "delivered":delivered, "installed":installed,
                "vc_count":len(vrows),"ld_count":len(lrows),
                "vc_assigned":any(r.get("Mã đội VC") for r in vrows),
                "ld_assigned":any(r.get("Mã đội KTV") for r in lrows),
                "vc_team_names":sorted({name_by_team.get(r.get("Mã đội VC"),r.get("Mã đội VC"))
                                        for r in vrows if r.get("Mã đội VC")}),
                "ld_team_names":sorted({name_by_team.get(r.get("Mã đội KTV"),r.get("Mã đội KTV"))
                                        for r in lrows if r.get("Mã đội KTV")})
            })
        if delivered>amount or installed>amount or installed>delivered:
            anomalies.append("Số lượng báo cáo vượt phân bổ/đã giao: "+str(key))

    result_sites=[]
    for key,site in sorted(site_index.items(),key=lambda pair:
                           (pair[0][0],site_label(pair[1]).casefold())):
        skus=by_point.get(key,[])
        allocated=bool(skus)
        full_vc=allocated and all(x["vc_count"] and
                                  x["delivered"]>=x["planned"] for x in skus)
        full_ld=full_vc and all(x["ld_count"] and
                                x["installed"]>=x["planned"] for x in skus)
        some_vc=any(x["delivered"]>0 for x in skus)
        some_ld=any(x["installed"]>0 for x in skus)
        assigned_vc=any(x["vc_assigned"] for x in skus)
        assigned_ld=any(x["ld_assigned"] for x in skus)
        if not allocated:
            status="Chưa phân bổ"
        elif full_ld:
            status="Đã lắp xong"
        elif full_vc and some_ld:
            status="Đang lắp đặt"
        elif full_vc:
            status="Sẵn sàng lắp"
        elif some_vc:
            status="Đang giao hàng"
        elif assigned_vc or assigned_ld:
            status="Chờ giao hàng"
        else:
            status="Chờ gán đội"
        result_sites.append({
            "project":key[0],"point_id":key[1],"name":site_label(site),
            "status":status,"skus":skus,"sku_count":len(skus),
            "delivery_full":bool(full_vc),"installation_full":bool(full_ld),
            "has_partial_delivery":bool(some_vc and not full_vc),
            "vc_done":sum(x["delivered"]>=x["planned"] and x["vc_count"]>0 for x in skus),
            "ld_done":sum(x["installed"]>=x["planned"] and x["ld_count"]>0 for x in skus),
            "vc_teams":sorted({name for x in skus for name in x["vc_team_names"]}),
            "ld_teams":sorted({name for x in skus for name in x["ld_team_names"]})
        })

    progress_skus=[]
    for key in sorted(set(receipt_amount)|set(totals)):
        project,sku=key
        values=totals[key]
        name,unit=product_names.get(key,("",""))
        imported=receipt_amount[key]
        allocated=values["allocated"]
        if allocated>imported:
            anomalies.append("Phân bổ vượt thực nhập: "+str(key))
        progress_skus.append({
            "Dự án":project,"SKU":sku,"Hàng hóa":name,"ĐVT":unit,
            "Nhập":display_amount(imported),
            "Phân bổ":display_amount(allocated),
            "Còn chờ phân bổ":display_amount(imported-allocated),
            "VC đã báo giao":display_amount(values["vc"]),
            "LĐ đã báo lắp":display_amount(values["ld"])
        })

    pending=[r for r in rs if r.get("Trạng thái đồng bộ") != SYNCED]
    point_progress=len(result_sites)
    vc_complete=sum(p["delivery_full"] for p in result_sites)
    ld_complete=sum(p["installation_full"] for p in result_sites)
    unassigned_vc=sum(1 for row in vc if not row.get("Mã đội VC"))
    unassigned_ld=sum(1 for row in ld if not row.get("Mã đội KTV"))
    delivery_tasks=sum(r.get("Trạng thái")==VC_DONE for r in vc)
    install_tasks=sum(r.get("Trạng thái")==LD_DONE for r in ld)
    activity=sorted(rs,key=lambda r:str(r.get("Thời gian máy chủ","")),
                    reverse=True)[:40]
    return {
        "sites":result_sites,"skus":progress_skus,"activity":activity,
        "anomalies":anomalies[:70],"pending_report_count":len(pending),
        "metrics":{
            "sites":point_progress,
            "sites_allocated":sum(bool(p["sku_count"]) for p in result_sites),
            "sites_delivered":vc_complete,
            "sites_installed":ld_complete,
            "sites_ready_install":sum(p["delivery_full"] and
                                       not p["installation_full"] for p in result_sites),
            "vc_tasks":len(vc),"vc_tasks_done":delivery_tasks,
            "ld_tasks":len(ld),"ld_tasks_done":install_tasks,
            "vc_unassigned":unassigned_vc,"ld_unassigned":unassigned_ld
        }
    }
