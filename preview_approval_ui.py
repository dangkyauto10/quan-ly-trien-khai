"""Captain registration approval screens for desktop and mobile PREVIEW.

Admin explicitly reviews the applicant's declared specialty and contract areas,
checks and corrects registered project sites, then approves and assigns
all allocated SKU tasks in the same atomic Google Sheets transaction.
"""
import streamlit as st
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from preview_assignment import (
    ROLE_TABS, site_assignment_plan, compact_site_assignment_requests
)
from preview_registration import (
    role_for_specialty, team_id_from_registration, matching_teams
)
from preview_signup_credentials import (
    pending_for_registration, approval_credential_requests,
    valid_secret_fields
)
from preview_credential_accounts import (
    visible_credential_state, next_account_id
)
from preview_team_access import normalized_name
from preview_team_detach import approval_link_request


def approval_requests(registration_sheet_id, team_sheet_id, row_number,
                      decision, team_row, team_id, approver, timestamp,
                      credential_changes=None, link_request=None):
    """Build one atomic Sheets batch for review and optional new team."""
    if decision not in ("Đã duyệt", "Từ chối") or row_number < 2:
        raise ValueError("Trạng thái hoặc dòng đăng ký không hợp lệ.")
    if decision == "Đã duyệt" and not team_id:
        raise ValueError("Duyệt phải có mã đội liên kết.")
    if decision == "Từ chối" and (team_id or team_row):
        raise ValueError("Không tạo đội khi từ chối.")
    if team_row is not None and (
        decision != "Đã duyệt" or len(team_row) != 8 or team_row[0] != team_id
    ):
        raise ValueError("Dữ liệu đội không khớp.")
    def text_cell(value):
        return {"userEnteredValue":{"stringValue":str(value if value is not None else "")}}
    requests = []
    if team_row is not None:
        requests.append({"appendCells":{
            "sheetId":team_sheet_id,
            "rows":[{"values":[text_cell(value) for value in team_row]}],
            "fields":"userEnteredValue"
        }})
    requests.append({"updateCells":{
        "range":{"sheetId":registration_sheet_id,
                 "startRowIndex":row_number-1,"endRowIndex":row_number,
                 "startColumnIndex":7,"endColumnIndex":11},
        "rows":[{"values":[text_cell(decision),text_cell(team_id),
                           text_cell(approver),
                           {"userEnteredValue":{"numberValue":float(timestamp)}}]}],
        "fields":"userEnteredValue"
    }})
    requests.append({"repeatCell":{
        "range":{"sheetId":registration_sheet_id,
                 "startRowIndex":row_number-1,"endRowIndex":row_number,
                 "startColumnIndex":10,"endColumnIndex":11},
        "cell":{"userEnteredFormat":{"numberFormat":{
            "type":"DATE_TIME","pattern":"dd/mm/yyyy hh:mm"}}},
        "fields":"userEnteredFormat.numberFormat"
    }})
    if credential_changes:
        requests.extend(credential_changes)
    if link_request is not None:
        if decision!="Đã duyệt" or team_row is None:
            raise ValueError("Chỉ đội mới tạo được gắn liên kết đăng ký.")
        requests.append(link_request)
    return requests



def _area_key(value):
    return " ".join(str(value or "").casefold().split())


def registered_site_defaults(declared_text, locations):
    """Suggest exact project-site matches; never invent ambiguous IDs."""
    by_name = {}
    by_id = {}
    for site in locations:
        sid = str(site.get("Mã điểm", "")).strip()
        name = _area_key(site.get("Tên xã/phường/đơn vị"))
        if not sid:
            continue
        by_id[_area_key(sid)] = sid
        by_name.setdefault(name, []).append(sid)
    proposed = [v.strip() for v in str(declared_text or "").split(",") if v.strip()]
    selected, unmatched = [], []
    for part in proposed:
        key = _area_key(part)
        options = ([by_id[key]] if key in by_id else by_name.get(key, []))
        if len(options) == 1:
            if options[0] not in selected:
                selected.append(options[0])
        else:
            unmatched.append(part)
    return selected, unmatched


def _amount(value):
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Số lượng phân bổ/nhiệm vụ không hợp lệ.") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Số lượng phân bổ/nhiệm vụ phải lớn hơn 0.")
    return amount


def reviewed_site_assignment(project, role, team_id, selected_ids,
                             locations, allocations, tasksets):
    """Require complete project+site+SKU quantities for every assigned role."""
    mode = {"VC":"VC", "KTV":"LD", "VC+KTV":"VC+LD"}.get(role)
    if not mode:
        raise ValueError("Chuyên môn không được cấp nhiệm vụ VC/KTV.")
    selected = list(selected_ids)
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("ADMIN phải chọn danh sách địa điểm duy nhất.")
    team = {"Mã đội":team_id, "Mã dự án":project,
            "Loại nhiệm vụ":role, "Trạng thái":"Hoạt động"}
    plan = site_assignment_plan(team, mode, selected, locations, tasksets)
    expected = defaultdict(Decimal)
    for item in allocations:
        if (item.get("Mã dự án")==project and
                item.get("Mã điểm") in selected and item.get("SKU")):
            expected[(item["Mã điểm"],item["SKU"])] += _amount(item.get("SL phân bổ"))
    if not expected or any(not any(k[0]==sid for k in expected) for sid in selected):
        raise ValueError("Địa điểm chưa đủ phân bổ hàng; chưa duyệt giao nhiệm vụ.")
    for tab in ROLE_TABS[mode]:
        actual = defaultdict(Decimal)
        key = "SL giao" if tab=="VAN_CHUYEN" else "SL lắp"
        for task in plan.get(tab, []):
            actual[(task.get("Mã điểm"),task.get("SKU"))] += _amount(task.get(key))
        if dict(actual) != dict(expected):
            raise ValueError(tab+": nhiệm vụ SKU/số lượng chưa khớp phân bổ. "
                             "Chưa xác nhận; ADMIN cần đối soát.")
    return plan


def render_pending_approvals(*, read_sheet, sheet, client, auth, audit,
                             lookup, sheet_datetime_serial,
                             secret_accounts, current_time, read_sheet_live=None):
    notice=st.session_state.pop("approval_notice",None)
    if notice:
        st.success(notice)
    pending=[r for r in read_sheet("DANG_KY_THANH_VIEN")
             if r.get("Trạng thái duyệt")=="Chờ duyệt"]
    project_ids=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")
                 if r.get("Mã dự án")]
    st.markdown("### 📥 Hồ sơ đội trưởng chờ duyệt")
    st.caption("ADMIN đối chiếu danh sách địa điểm đã đăng ký với hợp đồng; "
               "được thêm, bỏ hoặc thay địa điểm trước khi xác nhận. "
               "Duyệt và giao đủ nhiệm vụ VC/KTV theo SKU phân bổ trong cùng một lần ghi.")
    if not pending:
        st.info("Hiện không có hồ sơ chờ duyệt.")
        return

    for p in pending:
        rid=p["Mã đăng ký"]
        kind=role_for_specialty(p.get("Chuyên môn",""))
        with st.container(border=True):
            st.markdown(f"**{p.get('Họ tên','')}** • {rid}")
            st.write("**Điện thoại:** "+p.get("Số điện thoại",""))
            st.write(f"**Chuyên môn tự đăng ký:** {p.get('Chuyên môn','')} "
                     f"→ {kind or 'Cần xử lý riêng'}")
            st.write("**Phương tiện:** "+p.get("Phương tiện",""))
            st.caption("Người gửi: "+(p.get("Người nhập hồ sơ") or "Hồ sơ cũ")+
                       " • Đăng ký: "+p.get("Thời gian",""))
            with st.expander("Xem khu vực đã khai theo hợp đồng"):
                st.write(p.get("Địa bàn đề xuất") or "Chưa khai")
            registered_project=str(p.get("Mã dự án đăng ký","")).strip()
            if registered_project and registered_project not in project_ids:
                st.error("Dự án trong hồ sơ không tồn tại; ADMIN phải đối soát.")
                continue
            if registered_project:
                project=registered_project
                st.write("**Dự án đã khai:** "+project)
            elif project_ids:
                project=st.selectbox(
                    "Dự án của hồ sơ cũ (chưa ghi mã dự án)",
                    project_ids, key="review_project_"+rid)
            else:
                st.error("Chưa có dự án để tiếp nhận hồ sơ.")
                continue

            locations=[r for r in read_sheet("DANH_SACH_DIEM")
                       if r.get("Mã dự án")==project
                       and r.get("Trạng thái")=="Hoạt động" and r.get("Mã điểm")]
            point_by_id={r["Mã điểm"]:r for r in locations}
            defaults,unknown=registered_site_defaults(
                p.get("Địa bàn đề xuất"),locations)
            with st.form("review_form_"+rid):
                decision=st.selectbox("Trạng thái duyệt",
                    ["Chờ duyệt","Đã duyệt","Từ chối"],
                    index=0,key="review_status_"+rid)
                selected_ids=st.multiselect(
                    "Địa điểm đội trưởng đã đăng ký — ADMIN thêm/bỏ/sửa tại đây",
                    list(point_by_id),default=defaults,
                    format_func=lambda sid:(
                        point_by_id[sid].get("Tên xã/phường/đơn vị",sid)+
                        " • "+sid),key="review_sites_"+rid)
                if unknown:
                    st.warning("Địa điểm tự khai chưa khớp danh mục dự án: "+
                               ", ".join(unknown)+
                               ". ADMIN chọn lại địa điểm đúng bên trên.")
                allocations=[r for r in read_sheet("KHO_PHAN_BO")
                             if r.get("Mã dự án")==project
                             and r.get("Mã điểm") in selected_ids]
                if selected_ids:
                    st.caption(f"Đã chọn {len(selected_ids)} địa điểm. "
                               "Đối chiếu SKU và số lượng phân bổ trước khi xác nhận.")
                    st.dataframe([{
                        "Địa điểm":point_by_id[r["Mã điểm"]].get("Tên xã/phường/đơn vị",""),
                        "SKU":r.get("SKU",""),
                        "SL phân bổ":r.get("SL phân bổ","")}
                        for r in allocations],hide_index=True,
                        use_container_width=True,height=180)
                reviewed=st.checkbox(
                    "Tôi đã đối chiếu hợp đồng, danh sách địa điểm và SKU "
                    "được phân bổ; xác nhận giao nhiệm vụ đúng đội.",
                    key="review_contract_"+rid)
                submitted=st.form_submit_button(
                    "XÁC NHẬN DUYỆT / TỪ CHỐI",use_container_width=True)
            if not submitted:
                continue
            if decision=="Chờ duyệt":
                st.info("Hồ sơ vẫn chờ duyệt; chưa ghi thay đổi.")
                continue
            if decision=="Đã duyệt" and not kind:
                st.error("Chuyên môn không thuộc VC, KTV hay VC+KTV. "
                         "Cần ADMIN đối soát trước khi duyệt.")
                continue
            if decision=="Đã duyệt" and (not reviewed or not selected_ids):
                st.error("ADMIN cần kiểm tra hợp đồng và chọn địa điểm trước khi duyệt.")
                continue

            # Ignore stale UI rows or changes made by another Admin.
            read_sheet.clear()
            fresh=read_sheet_live or read_sheet
            live=lookup(fresh("DANG_KY_THANH_VIEN"),"Mã đăng ký",rid)
            if not live or live.get("Trạng thái duyệt")!="Chờ duyệt":
                st.warning("Hồ sơ đã thay đổi hoặc được xử lý. Tải lại trang.")
                continue
            registered_now=str(live.get("Mã dự án đăng ký","")).strip()
            if registered_now not in ("",project):
                st.error("Dự án trong hồ sơ đã đổi, không ghi dữ liệu.")
                continue
            if live.get("Địa bàn đề xuất")!=p.get("Địa bàn đề xuất"):
                st.error("Danh sách đăng ký đã thay đổi, cần ADMIN tải lại.")
                continue
            if project not in [r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")]:
                st.error("Dự án không còn hợp lệ.")
                continue

            try:
                pending=pending_for_registration(
                    rid,project,read_sheet("MAT_KHAU_DANG_KY"))
            except ValueError as exc:
                st.error(str(exc))
                continue

            tid=""
            new_team=None
            credential_changes=[]
            activated=False
            reused_account=False
            if decision=="Đã duyệt":
                if role_for_specialty(live.get("Chuyên môn",""))!=kind:
                    st.error("Chuyên môn đăng ký đã đổi; không thể duyệt.")
                    continue
                teams=read_sheet("QUAN_LY_DOI")
                matches=matching_teams(
                    teams,name=live.get("Họ tên",""),
                    phone=live.get("Số điện thoại",""),
                    kind=kind,project=project)
                if len(matches)>1:
                    st.error("Đội trùng tên, số điện thoại và dự án; cần đối soát.")
                    continue
                # Names are used as login identifiers. Do not approve a
                # duplicate among active captains without resolving identity.
                collisions=[t for t in teams if
                    t.get("Trạng thái")=="Hoạt động"
                    and normalized_name(t.get("Tên đội/đội trưởng"))==
                        normalized_name(live.get("Họ tên"))]
                if any(t not in matches for t in collisions):
                    st.error("Đã có đội trưởng trùng họ tên đang hoạt động. "
                             "ADMIN cần đối soát trước khi cấp tài khoản "
                             "đăng nhập bằng tên.")
                    continue
                tid=matches[0]["Mã đội"] if matches else team_id_from_registration(rid,kind)
                existing=lookup(teams,"Mã đội",tid)
                if existing and (existing.get("Tên đội/đội trưởng")!=live.get("Họ tên")
                    or existing.get("SĐT đội trưởng")!=live.get("Số điện thoại")
                    or existing.get("Loại nhiệm vụ")!=kind
                    or existing.get("Mã dự án")!=project
                    or existing.get("Trạng thái")!="Hoạt động"):
                    st.error("Mã đội tồn tại nhưng thông tin không khớp. "
                             "Chưa ghi duyệt.")
                    continue
                if not existing:
                    new_team=[tid,live["Họ tên"],live["Số điện thoại"],
                              kind,"","Hoạt động",project,
                              "Duyệt từ "+rid+"; chưa cấp đăng nhập"]

            # Approving the registration activates the *already hashed*
            # password from public signup. Old and ADMIN-assisted forms have
            # no pending password and retain the manual provisioning path.
            if pending and decision=="Đã duyệt":
                credentials=read_sheet("TAI_KHOAN_DOI")
                state,account=visible_credential_state(
                    {"Mã đội":tid},credentials,secret_accounts)
                if state=="missing":
                    usernames={r.get("Mã tài khoản") for r in credentials}
                    usernames.update(secret_accounts.keys())
                    username=next_account_id(usernames)
                    hashed_account=[
                        username,tid,project,"DOI_TRUONG",
                        pending["Salt hex"],pending["Mã băm PBKDF2"],
                        "Hoạt động",current_time(),auth()["username"],
                        "Kích hoạt theo hồ sơ "+rid
                    ]
                    credential_changes=approval_credential_requests(
                        sheet("MAT_KHAU_DANG_KY").id,
                        sheet("TAI_KHOAN_DOI").id,
                        pending,hashed_account)
                    activated=True
                elif state=="active" and existing is not None:
                    # A second signup for the SAME previously approved captain.
                    # Preserve the current account/password; dispose of the
                    # second signup's unused hash in the same approval batch.
                    linked=[
                        r for r in read_sheet("LIEN_KET_DANG_KY_DOI")
                        if r.get("Mã đội")==tid
                        and r.get("Mã dự án")==project
                        and r.get("Trạng thái liên kết")=="Đang liên kết"
                    ]
                    old_approvals=[
                        r for r in read_sheet("DANG_KY_THANH_VIEN")
                        if r.get("Mã đăng ký")!=rid
                        and r.get("Trạng thái duyệt")=="Đã duyệt"
                        and r.get("Mã đội được gán")==tid
                        and r.get("Mã dự án đăng ký")==project
                        and r.get("Họ tên")==live.get("Họ tên")
                        and r.get("Số điện thoại")==live.get("Số điện thoại")
                        and role_for_specialty(r.get("Chuyên môn",""))==kind
                    ]
                    if (len(linked)!=1
                        or not any(r.get("Mã đăng ký")==linked[0].get("Mã đăng ký")
                                   for r in old_approvals)
                        or account.get("Mã dự án")!=project
                        or account.get("Vai trò")!="DOI_TRUONG"
                        or not valid_secret_fields(account.get("Salt hex"),
                                                   account.get("Mã băm PBKDF2"))):
                        st.error("Có tài khoản nhưng chưa xác minh được "
                                 "hồ sơ đã duyệt và liên kết đội. "
                                 "ADMIN phải đối soát; chưa ghi dữ liệu.")
                        continue
                    credential_changes=approval_credential_requests(
                        sheet("MAT_KHAU_DANG_KY").id,
                        sheet("TAI_KHOAN_DOI").id,
                        pending,reused=True)
                    reused_account=True
                else:
                    st.error("Đội trưởng đã có tài khoản hoặc tài khoản "
                             "bị xung đột. Cần ADMIN đối soát trước khi duyệt.")
                    continue
            elif pending and decision=="Từ chối":
                credential_changes=approval_credential_requests(
                    sheet("MAT_KHAU_DANG_KY").id,
                    sheet("TAI_KHOAN_DOI").id,pending,rejected=True)

            site_plan=None
            if decision=="Đã duyệt":
                # Re-read live allocations and unassigned task rows immediately
                # before approving. No partial approval/assignment is permitted.
                actual_locations=fresh("DANH_SACH_DIEM")
                actual_tasks={tab:fresh(tab) for tab in ("VAN_CHUYEN","LAP_DAT")}
                try:
                    site_plan=reviewed_site_assignment(
                        project,kind,tid,selected_ids,actual_locations,
                        fresh("KHO_PHAN_BO"),actual_tasks)
                except ValueError as exc:
                    st.error("Chưa duyệt/giao địa điểm: "+str(exc))
                    continue

            # Establish ownership ONLY if this approval creates a NEW team.
            # Never guess that pre-existing/manual teams came from the
            # registration being reviewed (old deleted registrations are many).
            link_request=None
            if (decision=="Đã duyệt" and new_team is not None
                    and registered_now==project):
                link_request=approval_link_request(
                    sheet("LIEN_KET_DANG_KY_DOI").id,
                    rid,tid,project,current_time())

            try:
                request=approval_requests(
                    sheet("DANG_KY_THANH_VIEN").id,
                    sheet("QUAN_LY_DOI").id,
                    live["_row"],decision,new_team,tid,
                    auth()["username"],sheet_datetime_serial(),
                    credential_changes=credential_changes,
                    link_request=link_request)
                if site_plan is not None:
                    tables={tab:sheet(tab).id for tab in site_plan}
                    request.extend(compact_site_assignment_requests(
                        tables,site_plan,tid))
                client()[0].batch_update({"requests":request})
                read_sheet.clear()
                audit(auth()["username"],"XÉT DUYỆT ĐỘI TRƯỞNG",
                      "DANG_KY_THANH_VIEN",rid,"OK",
                      f"{decision}/{tid}/{project}"+
                      ("/điểm:"+",".join(selected_ids) if site_plan else ""))
                if decision=="Đã duyệt":
                    st.session_state["approval_notice"]=(
                        f"Đã duyệt hồ sơ đội trưởng {live.get('Họ tên','')}. "
                        "Mã đội đã được lưu nội bộ để gán nhiệm vụ. "
                        +("Mật khẩu đã tự đặt khi đăng ký ĐÃ KÍCH HOẠT. "
                          if activated else
                          "Đã xác nhận đăng ký lại: giữ nguyên tài khoản "
                          "và mật khẩu hiện có. "
                          if reused_account else
                          "Đây là hồ sơ cũ/ADMIN đăng ký hộ, cần ADMIN cấp "
                          "mật khẩu riêng. ")
                        +f"ĐÃ GIAO {len(selected_ids)} địa điểm và "
                        f"{sum(len(rows) for rows in site_plan.values())} "
                        "nhiệm vụ/SKU theo phân bổ.")
                else:
                    st.session_state["approval_notice"]=(
                        f"Đã cập nhật hồ sơ {rid} thành TỪ CHỐI. Không tạo đội.")
                st.rerun()
            except Exception as exc:
                read_sheet.clear()
                st.error("Chưa xác nhận được trạng thái ghi ("+
                         type(exc).__name__+"). KHÔNG bấm lại ngay; cần "
                         "kiểm tra DANG_KY_THANH_VIEN và QUAN_LY_DOI.")
