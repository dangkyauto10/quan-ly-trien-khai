"""Pure, preview-only reporting transaction builder.

No live Google Sheets or Drive calls. The caller must re-read task state,
verify the authenticated team and photo/GPS evidence, then submit ALL
returned requests in one spreadsheets.batchUpdate operation.
"""
from decimal import Decimal
from preview_bulk_allocation import _row, quantity


CONFIG={
    "Đã giao hàng":("VAN_CHUYEN","Mã nhiệm vụ VC","Mã đội VC",
                    "SL giao","Đã giao hàng","Đã giao một phần",
                    ("Chưa giao","Đang giao","Đã giao một phần","Giao một phần")),
    "Đã lắp đặt":("LAP_DAT","Mã nhiệm vụ LD","Mã đội KTV",
                    "SL lắp","Đã lắp đặt","Đã lắp một phần",
                    ("Chưa lắp","Đang lắp","Đã lắp một phần")),
}


def numeric(value):
    """Accept Sheets locale comma decimals, reject malformed quantities."""
    if value is None or str(value).strip()=="":
        return Decimal(0)
    return quantity(str(value).strip().replace(",","."))


def pending_quantity(row, mode):
    if mode not in CONFIG:
        raise ValueError("Loại báo cáo không hợp lệ.")
    _,_,_,planned_key,_,_,_=CONFIG[mode]
    planned=numeric(row.get(planned_key))
    already=numeric(row.get("SL thực tế"))
    if planned<=0 or already>planned:
        raise ValueError("SL được giao hoặc SL đã thực hiện cần đối soát.")
    return planned-already



def allocated_report_item(task, allocation_rows, mode):
    """Read the user-visible product and site quota from KHO_PHAN_BO.

    The VC/KTV task is a workflow record. It may never silently override
    the quantity allocated to this project, location and SKU.
    """
    if mode not in CONFIG:
        raise ValueError("Loại báo cáo không hợp lệ.")
    project=str(task.get("Mã dự án") or "").strip()
    point=str(task.get("Mã điểm") or "").strip()
    sku=str(task.get("SKU") or "").strip()
    matches=[
        row for row in allocation_rows
        if str(row.get("Mã dự án") or "").strip()==project
        and str(row.get("Mã điểm") or "").strip()==point
        and str(row.get("SKU") or "").strip()==sku
    ]
    if len(matches)!=1:
        raise ValueError("Thiếu hoặc trùng phân bổ tại điểm; cần ADMIN đối soát.")
    allocation=matches[0]
    allocated=numeric(allocation.get("SL phân bổ"))
    planned_key=CONFIG[mode][3]
    task_planned=numeric(task.get(planned_key))
    if allocated<=0 or allocated!=task_planned:
        raise ValueError("Số lượng nhiệm vụ không khớp KHO_PHAN_BO tại điểm.")
    task_alloc=str(task.get("Mã phân bổ") or "").strip()
    source_alloc=str(allocation.get("Mã phân bổ") or "").strip()
    if task_alloc and source_alloc and task_alloc!=source_alloc:
        raise ValueError("Mã phân bổ nhiệm vụ không khớp KHO_PHAN_BO.")
    name=str(allocation.get("Tên hàng hóa") or
             allocation.get("Tên hàng") or "").strip()
    unit=str(allocation.get("ĐVT") or
             allocation.get("Đơn vị tính") or "").strip()
    if not name or not unit:
        raise ValueError("Phân bổ tại điểm thiếu tên hàng hoặc đơn vị tính.")
    return {
        "name":name,
        "unit":unit,
        "allocated":allocated,
        "already":numeric(task.get("SL thực tế")),
        "remaining":pending_quantity(task,mode)
    }


def atomic_report_requests(sheet_ids, rid, stamp, actor, role, team_id,
                           project, point, mode, live_rows, increments,
                           photo_urls, maps_url, latitude, longitude,
                           all_vc, all_ld, progress, place_name,
                           existing_report_ids=()):
    """Plan an atomic append+task update+progress update+journal transaction.

    Increments is the user-entered quantity for each selected task ID,
    NOT the allocation. Partial evidence is cumulative and never complete.
    This is atomic at Sheets request level; external Drive uploads are not.
    """
    required={"BAO_CAO_TRIEN_KHAI","VAN_CHUYEN","LAP_DAT",
              "TIEN_DO","NHAT_KY_HE_THONG"}
    if not required.issubset(sheet_ids) or mode not in CONFIG:
        raise ValueError("Thiếu bảng dữ liệu hoặc loại báo cáo không hợp lệ.")
    if not rid or rid in existing_report_ids or not photo_urls:
        raise ValueError("Trùng mã báo cáo hoặc thiếu ảnh hiện trường.")
    if mode=="Đã lắp đặt" and (latitude is None or longitude is None):
        raise ValueError("Lắp đặt phải có GPS thực tế.")
    tab,id_key,team_key,planned_key,done,partial,allowed=CONFIG[mode]
    task_updates=[]
    changes={}
    items=[]
    seen=set()
    for row in live_rows:
        task_id=str(row.get(id_key) or "").strip()
        if not task_id or task_id in seen:
            raise ValueError("Mã nhiệm vụ rỗng hoặc bị trùng.")
        seen.add(task_id)
        if (row.get("Mã dự án")!=project or row.get("Mã điểm")!=point
                or row.get(team_key)!=team_id):
            raise ValueError("Nhiệm vụ không thuộc đúng dự án, điểm hoặc đội.")
        inc=numeric(increments.get(task_id,0))
        if not inc:
            continue
        if row.get("Trạng thái") not in allowed:
            raise ValueError("Trạng thái nhiệm vụ không được phép báo cáo tiếp.")
        planned=numeric(row.get(planned_key))
        already=numeric(row.get("SL thực tế"))
        if planned<=0 or already>planned or (already>0 and
                row.get("Trạng thái")!=partial and
                not (tab=="VAN_CHUYEN" and row.get("Trạng thái")=="Giao một phần")):
            raise ValueError("Nhiệm vụ có SL hoặc trạng thái cũ cần đối soát.")
        actual=already+inc
        if actual>planned:
            raise ValueError("SL thực báo vượt SL được giao.")
        row_num=row.get("_row")
        if not isinstance(row_num,int) or row_num<2:
            raise ValueError("Không tìm thấy dòng nhiệm vụ hợp lệ.")
        status=done if actual==planned else partial
        note="" if status==done else "Còn "+format(planned-actual,"f")+" đơn vị"
        task_updates.append({"updateCells":{
            "start":{"sheetId":sheet_ids[tab],"rowIndex":row_num-1,
                     "columnIndex":7},
            "rows":[_row([status,stamp,", ".join(photo_urls),maps_url,
                          rid,actual,note])],"fields":"userEnteredValue"}})
        changes[task_id]=status
        items.append((task_id,str(row.get("SKU") or ""),inc))
    if not items:
        raise ValueError("Phải nhập ít nhất một SL thực tế lớn hơn 0.")
    if any(key not in seen and numeric(v)>0 for key,v in increments.items()):
        raise ValueError("SL đã nhập có nhiệm vụ không thuộc danh sách được phép.")
    vc=[r for r in all_vc if r.get("Mã dự án")==project and
        r.get("Mã điểm")==point]
    ld=[r for r in all_ld if r.get("Mã dự án")==project and
        r.get("Mã điểm")==point]
    def updated_status(r, which):
        key="Mã nhiệm vụ VC" if which=="VAN_CHUYEN" else "Mã nhiệm vụ LD"
        return changes.get(str(r.get(key) or ""),r.get("Trạng thái")) if tab==which else r.get("Trạng thái")
    vc_done=sum(updated_status(r,"VAN_CHUYEN")=="Đã giao hàng" for r in vc)
    ld_done=sum(updated_status(r,"LAP_DAT")=="Đã lắp đặt" for r in ld)
    total_vc,total_ld=len(vc),len(ld)
    all_done=bool(total_vc or total_ld) and vc_done==total_vc and ld_done==total_ld
    started=any(updated_status(r,"VAN_CHUYEN") in
                ("Đã giao hàng","Đã giao một phần","Giao một phần") for r in vc)
    started|=any(updated_status(r,"LAP_DAT") in
                 ("Đã lắp đặt","Đã lắp một phần") for r in ld)
    pstatus="Hoàn thành" if all_done else ("Đang thực hiện" if started else "Chưa thực hiện")
    progress_values=[project,point,place_name,total_vc,vc_done,
                     total_ld,ld_done,pstatus,stamp]
    matches=[r for r in progress if r.get("Mã dự án")==project and
             r.get("Mã điểm")==point]
    if len(matches)>1:
        raise ValueError("TIEN_DO có nhiều dòng cùng dự án và địa điểm.")
    if matches:
        row_num=matches[0].get("_row")
        if not isinstance(row_num,int) or row_num<2:
            raise ValueError("Dòng TIEN_DO không hợp lệ.")
        progress_request={"updateCells":{
            "start":{"sheetId":sheet_ids["TIEN_DO"],
                     "rowIndex":row_num-1,"columnIndex":0},
            "rows":[_row(progress_values)],"fields":"userEnteredValue"}}
    else:
        progress_request={"appendCells":{
            "sheetId":sheet_ids["TIEN_DO"],
            "rows":[_row(progress_values)],"fields":"userEnteredValue"}}
    relevant=vc if tab=="VAN_CHUYEN" else ld
    if not relevant:
        raise ValueError("Không tìm thấy nhiệm vụ tại địa điểm.")
    reported_kind=(mode if all(updated_status(r,tab)==done for r in relevant)
                   else partial)
    reported=[rid,stamp,project,point,team_id,reported_kind,
              ", ".join(id_ for id_,_,_ in items),
              ", ".join(sku+":"+format(q,"f") for _,sku,q in items),
              ", ".join(photo_urls),maps_url,
              latitude if latitude is not None else "",
              longitude if longitude is not None else "",
              "Theo phân bổ","Đã đồng bộ",""]
    report_request={"appendCells":{
        "sheetId":sheet_ids["BAO_CAO_TRIEN_KHAI"],
        "rows":[_row(reported)],"fields":"userEnteredValue"}}
    journal=[stamp,actor,role,"GỬI BÁO CÁO","BAO_CAO_TRIEN_KHAI",
             rid,"OK",project+" / "+point+" / "+str(len(items))+" nhiệm vụ"]
    audit_request={"appendCells":{
        "sheetId":sheet_ids["NHAT_KY_HE_THONG"],
        "rows":[_row(journal)],"fields":"userEnteredValue"}}
    return [report_request,*task_updates,progress_request,audit_request], changes
