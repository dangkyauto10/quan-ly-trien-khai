"""Signed central handover model for Preview (never equals doorstep delivery)."""
from collections import defaultdict
from decimal import Decimal, InvalidOperation


ACCEPTED="KTV đã nhận tại tập kết"


def q(value):
    try:
        value=str(value if value is not None else "").strip().replace(" ","")
        number=Decimal(value.replace(",","."))
        if not number.is_finite() or number<0:
            raise ValueError("Số lượng phải >= 0.")
        return number
    except (InvalidOperation, ValueError):
        raise ValueError("Số lượng không hợp lệ.")


def qty_label(amount):
    amount=Decimal(amount)
    return str(int(amount)) if amount==amount.to_integral_value() else format(amount,"f")


def hub_plan(team, chosen_points, install_rows, places, allocation_rows):
    """Prepare auditable point/SKU lines for one team's contracted region.

    One signed transfer may cover many old districts and communes. It reserves
    quantity for each site but does not close per-site transport tasks.
    """
    project=str(team.get("Mã dự án") or "")
    tid=str(team.get("Mã đội") or "")
    if not project or not tid or team.get("Trạng thái")!="Hoạt động" or (
        team.get("Loại nhiệm vụ") not in ("KTV","VC+KTV")
    ):
        raise ValueError("Chỉ đội KTV đã duyệt mới được nhận hàng tập kết.")
    chosen=[str(x) for x in chosen_points]
    if not chosen or len(chosen)!=len(set(chosen)):
        raise ValueError("Danh sách xã phải có và không được trùng.")
    locations={(p.get("Mã dự án"),p.get("Mã điểm")):p
               for p in places if p.get("Mã dự án") and p.get("Mã điểm")}
    by_key=defaultdict(list)
    for task in install_rows:
        key=(task.get("Mã dự án"),task.get("Mã điểm"),task.get("SKU"))
        if task.get("Mã đội KTV")==tid and key[0]==project:
            by_key[key].append(task)
    alloc_index=defaultdict(list)
    for al in allocation_rows:
        key=(al.get("Mã dự án"),al.get("Mã điểm"),al.get("SKU"))
        if key[0]==project:
            alloc_index[key].append(al)
    lines=[]
    summary=defaultdict(Decimal)
    for pid in chosen:
        loc=locations.get((project,pid))
        if not loc:
            raise ValueError("Điểm không thuộc dự án hoặc chưa có trong danh sách.")
        tasks=[(k,rows) for k,rows in by_key.items() if k[1]==pid]
        if not tasks:
            raise ValueError("Địa điểm không được giao cho KTV này.")
        for key, rows in tasks:
            if len(rows)!=1 or len(alloc_index[key])!=1:
                raise ValueError("Trùng/thiếu dòng phân bổ hoặc nhiệm vụ LĐ.")
            al=alloc_index[key][0]
            need=q(rows[0].get("SL lắp"))
            planned=q(al.get("SL phân bổ"))
            if need<=0 or need!=planned:
                raise ValueError("Định mức lắp không trùng dòng phân bổ.")
            item={"project":project,"point_id":pid,"name":loc.get("Tên xã/phường/đơn vị",""),
                  "sku":key[2],"quantity":need,"unit":al.get("ĐVT","")}
            lines.append(item)
            summary[(key[2],item["unit"])]+=need
    return sorted(lines,key=lambda p:(p["name"].casefold(),p["sku"])),dict(summary)


def verify_vc_assignment(lines, vc_team_id, vc_tasks):
    """Confirm the signer team owns every projected transport SKU before hub receipt.

    This closes the lifecycle gap: a hub receipt must be attributable to
    the exact VC team, not just a free-text signer's name.
    """
    if not vc_team_id or not lines:
        raise ValueError("Chưa xác định được đội VC bàn giao.")
    for item in lines:
        key=(item["project"],item["point_id"],item["sku"])
        records=[r for r in vc_tasks
                 if (r.get("Mã dự án"),r.get("Mã điểm"),r.get("SKU"))==key]
        if len(records)!=1:
            raise ValueError("Thiếu/trùng nhiệm vụ VC tại xã hoặc SKU: "+
                             str(item["point_id"])+" / "+str(item["sku"]))
        vc=records[0]
        if vc.get("Mã đội VC")!=vc_team_id:
            raise ValueError("SKU được giao cho đội VC khác: "+
                             str(item["point_id"])+" / "+str(item["sku"]))
        if (vc.get("Trạng thái")!="Chưa giao" or
                str(vc.get("Mã báo cáo","")).strip() or
                str(vc.get("SL thực tế","")).strip() or
                q(vc.get("SL giao"))!=item["quantity"]):
            raise ValueError("VC đã báo cáo hoặc định mức VC khác hợp đồng: "+
                             str(item["point_id"])+" / "+str(item["sku"]))
    return True


def received_by_site(hub_rows, project, team_id):
    """Accepted proof only: signed paper reference + image + explicit site qty."""
    result=defaultdict(Decimal)
    for r in hub_rows:
        if r.get("Mã dự án")!=project or r.get("Mã đội KTV nhận")!=team_id:
            continue
        if r.get("Trạng thái")!=ACCEPTED:
            continue
        if not r.get("Số biên bản giấy") or not r.get("Link ảnh biên bản ký"):
            continue
        key=(project,r.get("Mã điểm"),r.get("SKU"))
        if not all(key):
            continue
        try:
            actual=q(r.get("SL KTV thực nhận"))
        except ValueError:
            continue
        result[key]+=actual
    return result


def signed_receipt_lines(batch_id, team, lines, area, hub_name, hub_address,
                         vc_sender, paper_number, image_url, stamp,
                         vc_team_id):
    """Create site/SKU-level signed receipt rows; no fake receipt without evidence."""
    if not all(str(x or "").strip() for x in
               (batch_id,area,hub_name,hub_address,vc_sender,
                paper_number,image_url,stamp,vc_team_id)):
        raise ValueError("Thiếu tên điểm tập kết, bên giao, số biên bản, ảnh ký hoặc thời gian.")
    if not lines:
        raise ValueError("Không có địa điểm nhận hàng.")
    result=[]
    for i,line in enumerate(lines,1):
        result.append([
            batch_id+"-"+str(i).zfill(5), batch_id,team["Mã dự án"],
            team["Mã đội"],team["Tên đội/đội trưởng"],area,hub_name,
            hub_address,line["point_id"],line["name"],line["sku"],
            qty_label(line["quantity"]),qty_label(line["quantity"]),line["unit"],
            vc_sender,paper_number,image_url,stamp,ACCEPTED,
            "Bàn giao tại điểm tập kết; KHÔNG ghi đã giao tận xã",
            vc_team_id
        ])
    return result

def verified_vc_hub_receipts(hub_rows, vc_tasks, install_tasks):
    """Prove completed VC work at a hub without claiming delivery to each xã.

    Only one signed, full-quantity receipt per project/point/SKU qualifies.
    Its VC and KTV must match the *assigned* tasks. No Sheets writes occur.
    """
    transport=defaultdict(list)
    installation=defaultdict(list)
    accepted=defaultdict(list)
    for task in vc_tasks:
        key=(task.get("Mã dự án"),task.get("Mã điểm"),task.get("SKU"))
        if all(key):
            transport[key].append(task)
    for task in install_tasks:
        key=(task.get("Mã dự án"),task.get("Mã điểm"),task.get("SKU"))
        if all(key):
            installation[key].append(task)
    for receipt in hub_rows:
        if receipt.get("Trạng thái")!=ACCEPTED:
            continue
        key=(receipt.get("Mã dự án"),receipt.get("Mã điểm"),receipt.get("SKU"))
        if not all(key):
            continue
        accepted[key].append(receipt)

    completed={}
    warnings=[]
    for key, receipts in accepted.items():
        if len(receipts)!=1 or len(transport[key])!=1 or len(installation[key])!=1:
            warnings.append("Trùng/thiếu chứng từ hoặc nhiệm vụ tập kết: "+str(key))
            continue
        proof=receipts[0]
        vc=transport[key][0]
        ktv=installation[key][0]
        if not all(str(proof.get(field) or "").strip() for field in (
                "Số biên bản giấy","Link ảnh biên bản ký",
                "Mã đội VC giao","Mã đội KTV nhận")):
            warnings.append("Biên bản tập kết thiếu chứng từ/đội: "+str(key))
            continue
        if (vc.get("Mã đội VC")!=proof["Mã đội VC giao"] or
                ktv.get("Mã đội KTV")!=proof["Mã đội KTV nhận"]):
            warnings.append("Đội VC/KTV trong biên bản không khớp phân công: "+str(key))
            continue
        if (vc.get("Trạng thái")!="Chưa giao" or
                str(vc.get("Mã báo cáo") or "").strip() or
                str(vc.get("SL thực tế") or "").strip()):
            warnings.append("VC có giao trực tiếp/báo cáo trước bàn giao: "+str(key))
            continue
        try:
            quantity=q(proof.get("SL KTV thực nhận"))
            planned=q(vc.get("SL giao"))
            need=q(ktv.get("SL lắp"))
        except ValueError:
            warnings.append("Số lượng tập kết không hợp lệ: "+str(key))
            continue
        if planned<=0 or quantity!=planned or quantity!=need:
            warnings.append("Bàn giao chưa đủ hoặc lệch định mức: "+str(key))
            continue
        completed[key]=quantity
    return completed,warnings
