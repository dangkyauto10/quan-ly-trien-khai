"""Safety tests for Admin site reduction, reassignment and team suspension."""
import ast
from pathlib import Path
import unittest

from preview_team_reassignment import (
    team_change_plan, team_change_requests, change_signature
)

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
     "LIEN_KET_DANG_KY_DOI":18,"DANG_KY_THANH_VIEN":19}
REGS=[
    {"Mã đăng ký":"RVC","Mã dự án đăng ký":PROJECT,"Mã đội được gán":"VC-OLD",
     "Trạng thái duyệt":"Đã duyệt","Điểm VC Admin duyệt":"P1",
     "Điểm LĐ Admin duyệt":"","_row":2},
    {"Mã đăng ký":"RLD","Mã dự án đăng ký":PROJECT,"Mã đội được gán":"LD-OLD",
     "Trạng thái duyệt":"Đã duyệt","Điểm VC Admin duyệt":"",
     "Điểm LĐ Admin duyệt":"P1","_row":3},
    {"Mã đăng ký":"RNEW","Mã dự án đăng ký":PROJECT,"Mã đội được gán":"VC-NEW",
     "Trạng thái duyệt":"Đã duyệt","Điểm VC Admin duyệt":"",
     "Điểm LĐ Admin duyệt":"","_row":4},
]


class TeamReassignmentTests(unittest.TestCase):
    def plan(self, team=VC_TEAM, sites=("P1",), mode="VC", vc=None, ld=None,
             hubs=None, target=None, suspend=False, registrations=None):
        return team_change_plan(
            team,list(sites),mode,
            {"VAN_CHUYEN":[VC] if vc is None else vc,
             "LAP_DAT":[] if ld is None else ld},
            hubs or [],target_team=target,suspend=suspend,
            registrations=REGS if registrations is None else registrations)

    def test_release_removes_only_points_not_site_stock(self):
        plan=self.plan()
        self.assertEqual(plan["released_sites"],1)
        self.assertEqual(len(plan["changes"]),1)
        self.assertIn((2,"VAN_CHUYEN",""),plan["site_updates"])
        req=team_change_requests(plan,IDS,"2026-10-25","admin")
        self.assertEqual(len(req),3)
        self.assertEqual(req[0]["repeatCell"]["range"]["sheetId"],13)
        self.assertEqual(req[0]["repeatCell"]["cell"]["userEnteredValue"]["stringValue"],"")
        self.assertEqual(req[1]["updateCells"]["range"]["sheetId"],19)
        self.assertEqual(req[-1]["appendCells"]["sheetId"],15)
        self.assertNotIn("KHO_PHAN_BO",IDS)

    def test_transfer_to_active_approved_team_rewrites_both_rights(self):
        plan=self.plan(target=NEW_VC)
        self.assertEqual(plan["target_id"],"VC-NEW")
        self.assertIn((2,"VAN_CHUYEN",""),plan["site_updates"])
        self.assertIn((4,"VAN_CHUYEN","P1"),plan["site_updates"])
        self.assertEqual(team_change_requests(plan,IDS,"now","admin")[0]
                         ["repeatCell"]["cell"]["userEnteredValue"]["stringValue"],"VC-NEW")
        for wrong in [KTV_TEAM,{**NEW_VC,"Mã dự án":"OTHER"},VC_TEAM]:
            with self.assertRaisesRegex(ValueError,"đúng chuyên môn"):
                self.plan(target=wrong)

    def test_unallocated_site_can_be_reclaimed_and_reapproved(self):
        plan=self.plan(vc=[])
        self.assertEqual(plan["changes"],[])
        self.assertEqual(plan["released_sites"],1)
        self.assertEqual(plan["site_updates"],[(2,"VAN_CHUYEN","")])

    def test_proof_cannot_transfer_the_whole_site(self):
        for row in [
            {**VC,"Trạng thái":"Đã giao hàng"},
            {**VC,"Trạng thái":"Đã giao một phần","SL thực tế":"2"},
            {**VC,"Mã báo cáo":"BC-ONE"},
            {**VC,"Thời gian báo cáo":"2026-10-24"},
        ]:
            with self.assertRaisesRegex(ValueError,"đối soát"):
                self.plan(vc=[row])

    def test_hub_proof_blocks_release_without_handover(self):
        signed={"Mã dự án":PROJECT,"Mã điểm":"P1","SKU":"TB01",
                "Trạng thái":"KTV đã nhận tại tập kết",
                "Mã đội VC giao":"VC-OLD","Mã đội KTV nhận":"LD-OLD"}
        with self.assertRaisesRegex(ValueError,"đối soát"):
            self.plan(hubs=[signed])
        with self.assertRaisesRegex(ValueError,"đối soát"):
            self.plan(team=KTV_TEAM,mode="LD",vc=[],ld=[LD],hubs=[signed])

    def test_suspend_returns_only_safe_work_and_locks_account(self):
        plan=self.plan(sites=(),mode="",suspend=True)
        self.assertEqual(len(plan["changes"]),1)
        req=team_change_requests(plan,IDS,"now","admin",
                                 account_rows=[3],active_links=[9])
        status=[x["updateCells"] for x in req if "updateCells" in x]
        self.assertEqual(len(status),5)
        self.assertEqual([x["rows"][0]["values"][0]["userEnteredValue"]["stringValue"]
                          for x in status],["","Tạm khóa","Đã gỡ","Đã gỡ","now"])
        self.assertEqual(req[-1]["appendCells"]["sheetId"],15)

    def test_suspended_started_point_keeps_right_until_audit(self):
        row={**VC,"Trạng thái":"Đã giao hàng","Mã báo cáo":"BC-ONE"}
        plan=self.plan(sites=(),mode="",vc=[row],suspend=True)
        self.assertEqual(plan["changes"],[])
        self.assertEqual(len(plan["protected"]),1)
        self.assertEqual(plan["site_updates"],[])
        req=team_change_requests(plan,IDS,"now","admin",
                                 account_rows=[3],active_links=[9])
        self.assertEqual(req[0]["updateCells"]["rows"][0]["values"][0]
                         ["userEnteredValue"]["stringValue"],"Tạm khóa")
        self.assertNotEqual(change_signature(self.plan(sites=(),mode="",suspend=True)),
                            change_signature(plan))

    def test_bulk_release_compacts_rows(self):
        rows=[{**VC,"Mã nhiệm vụ VC":f"VC-{i}","Mã điểm":f"P{i}",
               "_row":i+2} for i in range(2500)]
        reg={**REGS[0],"Điểm VC Admin duyệt":",".join(f"P{i}" for i in range(2500))}
        plan=self.plan(sites=(),mode="",vc=rows,suspend=True,
                       registrations=[reg]+REGS[1:])
        self.assertEqual(len(plan["changes"]),2500)
        chunks=[r["repeatCell"] for r in
                team_change_requests(plan,IDS,"now","admin")
                if "repeatCell" in r]
        self.assertEqual(len(chunks),1)
        self.assertEqual(chunks[0]["range"]["endRowIndex"]-
                         chunks[0]["range"]["startRowIndex"],2500)

    def test_app_has_confirmation_and_live_recheck(self):
        source=(Path(__file__).resolve().parents[1]/
                "preview_app.py").read_text(encoding="utf-8")
        funcs={n.name:n for n in ast.parse(source).body
               if isinstance(n,ast.FunctionDef)}
        fragment=ast.get_source_segment(source,funcs["team_reassignment_admin"])
        for token in ['require_role("ADMIN")','team_change_plan(',
            'change_signature(live_plan)!=change_signature(planned)',
            'client()[0].batch_update({"requests":requests})',
            'disabled=not ack','read_sheet_live("VAN_CHUYEN")',
            'registrations=read_sheet_live("DANG_KY_THANH_VIEN")']:
            self.assertIn(token,fragment)


if __name__=="__main__":
    unittest.main()
