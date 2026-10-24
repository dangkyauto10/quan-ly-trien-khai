"""Safety tests for ADMIN release, direct transfer and team suspension."""
import ast
from pathlib import Path
import unittest

from preview_team_reassignment import (
    team_change_plan, team_change_requests, change_signature
)
from preview_team_detach import DETACHED, NEEDS_REVIEW


PROJECT="DA880"
VC_TEAM={"Mã đội":"VC-OLD","Mã dự án":PROJECT,
         "Loại nhiệm vụ":"VC","Trạng thái":"Hoạt động","_row":4}
KTV_TEAM={"Mã đội":"LD-OLD","Mã dự án":PROJECT,
          "Loại nhiệm vụ":"KTV","Trạng thái":"Hoạt động","_row":5}
NEW_VC={"Mã đội":"VC-NEW","Mã dự án":PROJECT,
        "Loại nhiệm vụ":"VC","Trạng thái":"Hoạt động","_row":6}
VC={"Mã nhiệm vụ VC":"VC-1","Mã dự án":PROJECT,"Mã điểm":"P1",
    "SKU":"TB01","Mã đội VC":"VC-OLD","SL giao":"15",
    "Trạng thái":"Chưa giao","_row":12}
LD={"Mã nhiệm vụ LD":"LD-1","Mã dự án":PROJECT,"Mã điểm":"P1",
    "SKU":"TB01","Mã đội KTV":"LD-OLD","SL lắp":"15",
    "Trạng thái":"Chưa lắp","_row":13}
IDS={"VAN_CHUYEN":13,"LAP_DAT":14,"NHAT_KY_HE_THONG":15,
     "QUAN_LY_DOI":16,"TAI_KHOAN_DOI":17,
     "LIEN_KET_DANG_KY_DOI":18}


class TeamReassignmentTests(unittest.TestCase):
    def test_release_only_pending_owner_cell_and_preserve_site_stock(self):
        plan=team_change_plan(VC_TEAM,["P1"],"VC",
                              {"VAN_CHUYEN":[VC],"LAP_DAT":[LD]},[])
        self.assertEqual(len(plan["changes"]),1)
        self.assertEqual(plan["target_id"],"")
        requests=team_change_requests(plan,IDS,"2026-10-24","admin")
        self.assertEqual(len(requests),2)
        release=requests[0]["repeatCell"]
        self.assertEqual(release["range"]["sheetId"],13)
        self.assertEqual((release["range"]["startColumnIndex"],
                          release["range"]["endColumnIndex"]),(6,7))
        self.assertEqual(release["cell"]["userEnteredValue"]["stringValue"],"")
        self.assertEqual(requests[1]["appendCells"]["sheetId"],15)
        self.assertNotIn("KHO_PHAN_BO",IDS)

    def test_direct_transfer_only_same_project_correct_role(self):
        tasks={"VAN_CHUYEN":[VC],"LAP_DAT":[]}
        plan=team_change_plan(VC_TEAM,["P1"],"VC",tasks,[],
                              target_team=NEW_VC)
        self.assertEqual(plan["target_id"],"VC-NEW")
        updates=team_change_requests(plan,IDS,"2026-10-24","admin")
        self.assertEqual(updates[0]["repeatCell"]["cell"]
                         ["userEnteredValue"]["stringValue"],"VC-NEW")
        with self.assertRaisesRegex(ValueError,"đúng chuyên môn"):
            team_change_plan(VC_TEAM,["P1"],"VC",tasks,[],
                             target_team=KTV_TEAM)
        with self.assertRaisesRegex(ValueError,"đúng chuyên môn"):
            team_change_plan(VC_TEAM,["P1"],"VC",tasks,[],
                             target_team={**NEW_VC,"Mã dự án":"OTHER"})
        with self.assertRaisesRegex(ValueError,"đúng chuyên môn"):
            team_change_plan(VC_TEAM,["P1"],"VC",tasks,[],
                             target_team=VC_TEAM)

    def test_started_completed_or_with_photo_cannot_transfer(self):
        for row in [
            {**VC,"Trạng thái":"Đã giao hàng"},
            {**VC,"Trạng thái":"Đã giao một phần","SL thực tế":"2"},
            {**VC,"Mã báo cáo":"BC-ONE"},
            {**VC,"Thời gian báo cáo":"2026-10-24"},
        ]:
            plan=team_change_plan(VC_TEAM,[],"",
                                 {"VAN_CHUYEN":[row],"LAP_DAT":[]},
                                 [],suspend=True)
            self.assertEqual(plan["changes"],[])
            self.assertEqual(len(plan["protected"]),1)
            self.assertEqual(plan["protected"][0]["point"],"P1")

    def test_signed_hub_prevents_accidental_reassignment(self):
        signed={"Mã dự án":PROJECT,"Mã điểm":"P1","SKU":"TB01",
                "Trạng thái":"KTV đã nhận tại tập kết",
                "Mã đội VC giao":"VC-OLD","Mã đội KTV nhận":"LD-OLD"}
        for source,tasks in [
            (VC_TEAM,{"VAN_CHUYEN":[VC],"LAP_DAT":[]}),
            (KTV_TEAM,{"VAN_CHUYEN":[],"LAP_DAT":[LD]}),
        ]:
            plan=team_change_plan(source,[],"",tasks,[signed],suspend=True)
            self.assertEqual(plan["changes"],[])
            self.assertEqual(len(plan["protected"]),1)

    def test_suspend_team_releases_unstarted_and_disables_account(self):
        tasks={"VAN_CHUYEN":[VC],"LAP_DAT":[LD]}
        plan=team_change_plan(VC_TEAM,[],"",tasks,[],suspend=True)
        self.assertEqual(len(plan["changes"]),1)
        updates=team_change_requests(plan,IDS,"2026-10-24","admin",
                                     account_rows=[3],active_links=[9])
        status=[r["updateCells"] for r in updates if "updateCells" in r]
        self.assertEqual(len(status),4)
        self.assertEqual([
            r["rows"][0]["values"][0]["userEnteredValue"]["stringValue"]
            for r in status],[DETACHED,DETACHED,DETACHED,"2026-10-24"])
        self.assertEqual([
            r["range"]["startColumnIndex"] for r in status],[5,6,3,5])
        self.assertEqual(updates[-1]["appendCells"]["sheetId"],15)

    def test_suspend_with_started_work_flags_reconciliation(self):
        started={**VC,"Trạng thái":"Đã giao hàng","Mã báo cáo":"BC-ONE"}
        plan=team_change_plan(
            VC_TEAM,[],"",{"VAN_CHUYEN":[started],"LAP_DAT":[]},[],
            suspend=True)
        updates=team_change_requests(plan,IDS,"2026-10-24","admin",
                                     account_rows=[3],active_links=[9])
        status=[r["updateCells"] for r in updates if "updateCells" in r]
        self.assertEqual(status[0]["rows"][0]["values"][0]
                         ["userEnteredValue"]["stringValue"],NEEDS_REVIEW)
        self.assertEqual(len(plan["protected"]),1)

    def test_bulk_release_compacts_contiguous_rows(self):
        rows=[{**VC,"Mã nhiệm vụ VC":f"VC-{i}","Mã điểm":f"P{i}",
               "_row":i+2} for i in range(2500)]
        plan=team_change_plan(VC_TEAM,[],"",
                              {"VAN_CHUYEN":rows,"LAP_DAT":[]},[],
                              suspend=True)
        self.assertEqual(len(plan["changes"]),2500)
        requests=team_change_requests(plan,IDS,"2026-10-24","admin")
        chunks=[r["repeatCell"] for r in requests if "repeatCell" in r]
        self.assertEqual(len(chunks),1)
        self.assertEqual(chunks[0]["range"]["endRowIndex"]-
                         chunks[0]["range"]["startRowIndex"],2500)

    def test_app_has_admin_live_recheck_and_explicit_confirmation(self):
        source=(Path(__file__).resolve().parents[1]/
                "preview_app.py").read_text(encoding="utf-8")
        funcs={n.name:n for n in ast.parse(source).body
               if isinstance(n,ast.FunctionDef)}
        self.assertIn("team_reassignment_admin",funcs)
        fragment=ast.get_source_segment(source,funcs["team_reassignment_admin"])
        for token in [
            'require_role("ADMIN")','team_change_plan(',
            'change_signature(live_plan)!=change_signature(planned)',
            'client()[0].batch_update({"requests":requests})',
            'disabled=not ack','read_sheet_live("VAN_CHUYEN")',
        ]:
            self.assertIn(token,fragment)
        self.assertIn("    team_reassignment_admin()",source)


if __name__=="__main__":
    unittest.main()
