"""Captain registration approval screens for desktop and mobile PREVIEW.

Admin explicitly reviews the applicant's declared specialty and contract areas,
chooses approval status, and confirms. Job and site assignment remain separate.
"""
import streamlit as st
from preview_registration import (
    role_for_specialty, team_id_from_registration, matching_teams
)


def approval_requests(registration_sheet_id, team_sheet_id, row_number,
                      decision, team_row, team_id, approver, timestamp):
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
    return requests


def render_pending_approvals(*, read_sheet, sheet, client, auth, audit,
                             lookup, sheet_datetime_serial):
    notice=st.session_state.pop("approval_notice",None)
    if notice:
        st.success(notice)
    pending=[r for r in read_sheet("DANG_KY_THANH_VIEN")
             if r.get("Trạng thái duyệt")=="Chờ duyệt"]
    project_ids=[r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")
                 if r.get("Mã dự án")]
    st.markdown("### 📥 Hồ sơ đội trưởng chờ duyệt")
    st.caption("Đội trưởng tự khai từ xa hoặc ADMIN đăng ký hộ. "
               "Kiểm tra hồ sơ, chọn trạng thái, bấm XÁC NHẬN. "
               "Việc gán điểm, SKU và số lượng là bước riêng sau khi duyệt.")
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

            with st.form("review_form_"+rid):
                decision=st.selectbox("Trạng thái duyệt",
                    ["Chờ duyệt","Đã duyệt","Từ chối"],
                    index=0,key="review_status_"+rid)
                submitted=st.form_submit_button(
                    "XÁC NHẬN TRẠNG THÁI",use_container_width=True)
            if not submitted:
                continue
            if decision=="Chờ duyệt":
                st.info("Hồ sơ vẫn chờ duyệt; chưa ghi thay đổi.")
                continue
            if decision=="Đã duyệt" and not kind:
                st.error("Chuyên môn không thuộc VC, KTV hay VC+KTV. "
                         "Cần ADMIN đối soát trước khi duyệt.")
                continue

            # Ignore stale UI rows or changes made by another Admin.
            read_sheet.clear()
            live=lookup(read_sheet("DANG_KY_THANH_VIEN"),"Mã đăng ký",rid)
            if not live or live.get("Trạng thái duyệt")!="Chờ duyệt":
                st.warning("Hồ sơ đã thay đổi hoặc được xử lý. Tải lại trang.")
                continue
            registered_now=str(live.get("Mã dự án đăng ký","")).strip()
            if registered_now not in ("",project):
                st.error("Dự án trong hồ sơ đã đổi, không ghi dữ liệu.")
                continue
            if project not in [r["Mã dự án"] for r in read_sheet("DANH_SACH_DU_AN")]:
                st.error("Dự án không còn hợp lệ.")
                continue

            tid=""
            new_team=None
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

            try:
                request=approval_requests(
                    sheet("DANG_KY_THANH_VIEN").id,
                    sheet("QUAN_LY_DOI").id,
                    live["_row"],decision,new_team,tid,
                    auth()["username"],sheet_datetime_serial())
                client()[0].batch_update({"requests":request})
                read_sheet.clear()
                audit(auth()["username"],"XÉT DUYỆT ĐỘI TRƯỞNG",
                      "DANG_KY_THANH_VIEN",rid,"OK",
                      f"{decision}/{tid}/{project}")
                if decision=="Đã duyệt":
                    st.session_state["approval_notice"]=(
                        f"Đã duyệt hồ sơ và liên kết mã đội {tid}. "
                        "Chưa tự gán điểm, SKU, số lượng hoặc cấp tài khoản.")
                else:
                    st.session_state["approval_notice"]=(
                        f"Đã cập nhật hồ sơ {rid} thành TỪ CHỐI. Không tạo đội.")
                st.rerun()
            except Exception as exc:
                read_sheet.clear()
                st.error("Chưa xác nhận được trạng thái ghi ("+
                         type(exc).__name__+"). KHÔNG bấm lại ngay; cần "
                         "kiểm tra DANG_KY_THANH_VIEN và QUAN_LY_DOI.")
