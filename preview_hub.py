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
                         vc_sender, paper_number, image_url, stamp):
    """Create site/SKU-level signed receipt rows; no fake receipt without evidence."""
    if not all(str(x or "").strip() for x in
               (batch_id,area,hub_name,hub_address,vc_sender,
                paper_number,image_url,stamp)):
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
            "Bàn giao tại điểm tập kết; KHÔNG ghi đã giao tận xã"
        ])
    return result
