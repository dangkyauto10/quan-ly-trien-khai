"""Cascade cancellation after physically deleting a registration from Sheets."""
import ast
from pathlib import Path
import unittest

from preview_team_detach import (
    approval_link_request, lost_registrations, revoked_team_ids,
    plan_detach, detach_requests, ACTIVE, DETACHED, NEEDS_REVIEW
)


PROJECT="DA880"
RID="DK-SELF-2026"
TID="KTV-NEW-01"
SHEETS={
    "QUAN_LY_DOI":11,"TAI_KHOAN_DOI":12,
    "VAN_CHUYEN":13,"LAP_DAT":14,"LIEN_KET_DANG_KY_DOI":15,
}
TEAM={"Mã đội":TID,"Mã dự án":PROJECT,"Trạng thái":"Hoạt động",
      "Tên đội/đội trưởng":"Nguyễn Văn A","_row":4}
CREDS=[{"Mã tài khoản":"tdv_123","Mã đội":TID,
        "Mã dự án":PROJECT,"Trạng thái":"Hoạt động","_row":3}]
LINK={"Mã đăng ký":RID,"Mã đội":TID,"Mã dự án":PROJECT,
      "Trạng thái liên kết":ACTIVE,"_row":2}
REG={"Mã đăng ký":RID,"Mã đội được gán":TID,
     "Mã dự án đăng ký":PROJECT,"Trạng thái duyệt":"Đã duyệt"}
VC={"Mã dự án":PROJECT,"Mã đội VC":TID,"Trạng thái":"Chưa giao",
    "Mã điểm":"P1","SKU":"TB01","SL giao":"12","_row":8}
LD={"Mã dự án":PROJECT,"Mã đội KTV":TID,"Trạng thái":"Chưa lắp",
    "Mã điểm":"P1","SKU":"TB01","SL lắp":"12","_row":9}


class CascadeTests(unittest.TestCase):
    def test_approval_registers_team_provenance_with_same_batch(self):
        newteam=[TID,"Nguyễn Văn A","09xxxxx","KTV","",
                 "Hoạt động",PROJECT,"Duyệt từ "+RID]
        request=approval_link_request(SHEETS["LIEN_KET_DANG_KY_DOI"],
                                      RID,TID,PROJECT,"2026-10-23")
        approval_source=(Path(__file__).resolve().parents[1]/
                         "preview_approval_ui.py").read_text(encoding="utf-8")
        self.assertIn('link_request=link_request',approval_source)
        self.assertIn('requests.append(link_request)',approval_source)
        self.assertIn('if decision!="Đã duyệt" or team_row is None:',approval_source)
        values=[v["userEnteredValue"]["stringValue"] for v in
                request["appendCells"]["rows"][0]["values"]]
        self.assertEqual(values[:4],[RID,TID,PROJECT,ACTIVE])

    def test_delete_recognized_without_clearing_legacy(self):
        self.assertEqual(lost_registrations([REG],[LINK]),[])
        self.assertEqual(lost_registrations([],[]),[])
        self.assertEqual(lost_registrations([],[LINK]),[LINK])
        self.assertEqual(revoked_team_ids([],[LINK]),{TID})
        self.assertEqual(revoked_team_ids([REG],[LINK]),set())
        self.assertEqual(revoked_team_ids([],[]),set())

    def test_registration_not_approved_denies_signin(self):
        reg={**REG,"Trạng thái duyệt":"Chờ duyệt"}
        self.assertIn(TID,revoked_team_ids([reg],[LINK]))
        reg={**REG,"Mã đội được gán":"OTHER"}
        self.assertIn(TID,revoked_team_ids([reg],[LINK]))

    def test_duplicate_team_links_cannot_be_auto_removed(self):
        other={**LINK,"Mã đăng ký":"DK-02","_row":3}
        self.assertEqual(lost_registrations([],[LINK,other]),[])
        self.assertIn(TID,revoked_team_ids([],[LINK,other]))

    def test_safe_pending_release_keeps_stock_and_site_quantities(self):
        plan=plan_detach(
            LINK,[TEAM],CREDS,[VC],[LD],[],[])
        self.assertEqual(len(plan["pending_tasks"]),2)
        self.assertFalse(plan["review"])
        changes=detach_requests(plan,SHEETS,"2026-10-23")
        self.assertEqual(len(changes),6)
        cell_values=[]
        for r in changes:
            c=r["updateCells"]
            cell_values.append((
                c["range"]["sheetId"],c["range"]["startColumnIndex"],
                c["rows"][0]["values"][0]["userEnteredValue"]["stringValue"]))
        self.assertIn((SHEETS["VAN_CHUYEN"],6,""),cell_values)
        self.assertIn((SHEETS["LAP_DAT"],6,""),cell_values)
        self.assertIn((SHEETS["QUAN_LY_DOI"],5,DETACHED),cell_values)
        self.assertIn((SHEETS["TAI_KHOAN_DOI"],6,DETACHED),cell_values)
        self.assertIn((SHEETS["LIEN_KET_DANG_KY_DOI"],3,DETACHED),cell_values)
        # Absolutely no physical stock/point allocation adjustment.
        self.assertNotIn("KHO_PHAN_BO",SHEETS)
        self.assertTrue(all(x["updateCells"]["range"]["startColumnIndex"]==6
                            for x in changes[:2]))

    def test_completed_proof_not_removed_and_team_needs_reconciliation(self):
        closed={**VC,"Trạng thái":"Đã giao hàng",
                "Thời gian báo cáo":"2026-10-23T12:00:00"}
        plan=plan_detach(LINK,[TEAM],CREDS,[closed],[LD],[],[])
        self.assertEqual(len(plan["pending_tasks"]),1)
        self.assertTrue(plan["review"])
        self.assertEqual(len(plan["protected_tasks"]),1)
        changes=detach_requests(plan,SHEETS,"2026-10-23")
        team_change=next(x["updateCells"] for x in changes
                         if x["updateCells"]["range"]["sheetId"]==
                         SHEETS["QUAN_LY_DOI"])
        self.assertEqual(team_change["rows"][0]["values"][0]
                         ["userEnteredValue"]["stringValue"],NEEDS_REVIEW)
        self.assertFalse(any(x["updateCells"]["range"]["sheetId"]==
                             SHEETS["VAN_CHUYEN"] for x in changes))

    def test_signed_hub_is_protected(self):
        signed={"Mã đội KTV nhận":TID,"Mã dự án":PROJECT,
                "Trạng thái":"KTV đã nhận tại tập kết"}
        plan=plan_detach(LINK,[TEAM],CREDS,[],[LD],[],[signed])
        self.assertTrue(plan["review"])

    def test_credentials_and_team_scoped_to_correct_project(self):
        impostor={**TEAM,"Mã dự án":"DA-OTHER"}
        with self.assertRaises(ValueError):
            plan_detach(LINK,[impostor],CREDS,[],[],[],[])

    def test_app_enforces_revocation_and_admin_guard(self):
        source=(Path(__file__).resolve().parents[1]/
                "preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                and n.name=="reconcile_deleted_captains")
        body=ast.get_source_segment(source,fn)
        self.assertIn('who.get("role")!="ADMIN"',body)
        self.assertIn('lost_registrations(fresh_regs,fresh_links)',body)
        self.assertIn('detach_requests(plan,ids,now())',body)
        self.assertIn('client()[0].batch_update({"requests":changes})',body)
        self.assertIn('revoked_team_ids(',source)
        self.assertNotIn('sheet("KHO_PHAN_BO").update',body)


if __name__=="__main__":
    unittest.main()
