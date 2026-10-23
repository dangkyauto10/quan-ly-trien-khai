"""Business lifecycle acceptance cases: deletion is a transfer of obligations."""
import ast
from pathlib import Path
import unittest

from preview_team_detach import plan_detach, detach_requests, ACTIVE, NEEDS_REVIEW

ROOT=Path(__file__).resolve().parents[1]
TID="KTV-DA880"
PROJECT="DA880"
LINK={"Mã đăng ký":"DK-880","Mã đội":TID,
      "Mã dự án":PROJECT,"Trạng thái liên kết":ACTIVE,"_row":2}
TEAM={"Mã đội":TID,"Mã dự án":PROJECT,
      "Trạng thái":"Hoạt động","Tên đội/đội trưởng":"Nguyễn Văn A","_row":3}
ACCOUNTS=[{"Mã đội":TID,"Mã dự án":PROJECT,
           "Trạng thái":"Hoạt động","_row":4}]
SHEETS={"QUAN_LY_DOI":11,"TAI_KHOAN_DOI":12,"VAN_CHUYEN":13,
        "LAP_DAT":14,"LIEN_KET_DANG_KY_DOI":15}


def ld(site,sku="TB01",status="Chưa lắp",idx=10):
    return {"Mã dự án":PROJECT,"Mã điểm":site,"SKU":sku,
            "Mã đội KTV":TID,"Trạng thái":status,"SL lắp":"12","_row":idx}


def vc(site,sku="TB01",status="Chưa giao",idx=15):
    return {"Mã dự án":PROJECT,"Mã điểm":site,"SKU":sku,
            "Mã đội VC":TID,"Trạng thái":status,"SL giao":"12","_row":idx}


def hub(site,sku="TB01",signed=True):
    return {"Mã dự án":PROJECT,"Mã điểm":site,"SKU":sku,
            "Mã đội KTV nhận":TID,"Trạng thái":"KTV đã nhận tại tập kết",
            "Số biên bản giấy":"BG-880" if signed else "",
            "Link ảnh biên bản ký":"https://drive.google.com/test" if signed else ""}


def plan(vc_rows=None,ld_rows=None,reports=None,hub_rows=None):
    return plan_detach(LINK,[TEAM],ACCOUNTS,vc_rows or [],ld_rows or [],
                       reports or [],hub_rows or [])


class DeletingTeamBusinessTests(unittest.TestCase):
    def test_no_work_returns_all_pending_tasks(self):
        result=plan(vc_rows=[vc("P1")],ld_rows=[ld("P1",idx=20)])
        self.assertEqual(len(result["pending_tasks"]),2)
        self.assertEqual(result["released_sites"],1)
        self.assertFalse(result["review"])

    def test_ktv_received_skus_hold_only_corresponding_tasks(self):
        result=plan(
            ld_rows=[ld("P1","TB01",idx=10),ld("P1","TB02",idx=11),
                     ld("P2","TB01",idx=12)],
            hub_rows=[hub("P1","TB01")])
        self.assertEqual(len(result["pending_tasks"]),2)
        self.assertEqual(result["custody_sites"],1)
        self.assertTrue(result["review"])
        self.assertEqual(len(result["protected_tasks"]),2)  # proof + custodial task
        self.assertEqual({d["sku"] for d in result["protected_details"]},{"TB01"})
        self.assertEqual({d["point_id"] for d in result["pending_details"]},{"P1","P2"})
        changes=detach_requests(result,SHEETS,"now")
        self.assertTrue(any(
            x.get("repeatCell",{}).get("range",{}).get("startRowIndex")==10
            for x in changes))
        self.assertFalse(any(
            x.get("repeatCell",{}).get("range",{}).get("startRowIndex")==9
            for x in changes))

    def test_signed_or_incomplete_hub_paper_is_still_physical_custody(self):
        for signed in (False,True):
            with self.subTest(signed=signed):
                result=plan(ld_rows=[ld("P1")],
                            hub_rows=[hub("P1",signed=signed)])
                self.assertEqual(result["pending_tasks"],[])
                self.assertTrue(result["review"])
                self.assertEqual(result["custody_sites"],1)

    def test_vc_completed_at_hub_is_not_reassigned_when_captain_deleted(self):
        signed={
            "Mã dự án":PROJECT,"Mã điểm":"P1","SKU":"TB01",
            "Mã đội VC giao":TID,"Mã đội KTV nhận":"KTV-OTHER",
            "Trạng thái":"KTV đã nhận tại tập kết",
            "Số biên bản giấy":"BG-001",
            "Link ảnh biên bản ký":"https://drive.google.com/file/d/001"
        }
        result=plan(
            vc_rows=[vc("P1","TB01",idx=15),vc("P2","TB01",idx=16)],
            hub_rows=[signed])
        self.assertEqual(len(result["pending_tasks"]),1)
        self.assertEqual(result["pending_details"][0]["point_id"],"P2")
        self.assertEqual(result["vc_hub_sites"],1)
        self.assertTrue(any("VC đã bàn giao tại điểm tập kết"==x["reason"]
                            for x in result["protected_details"]))
        changes=detach_requests(result,SHEETS,"now")
        self.assertFalse(any(
            x.get("repeatCell",{}).get("range",{}).get("startRowIndex")==14
            for x in changes))
        self.assertTrue(any(
            x.get("repeatCell",{}).get("range",{}).get("startRowIndex")==15
            for x in changes))

    def test_signed_hub_missing_vc_id_cannot_safely_prove_which_vc_did_it(self):
        unsigned_origin={
            "Mã dự án":PROJECT,"Mã điểm":"P1","SKU":"TB01",
            "Mã đội KTV nhận":"KTV-OTHER",
            "Trạng thái":"KTV đã nhận tại tập kết",
            "Tên đội VC giao":"Một người vận chuyển chưa định danh"
        }
        result=plan(vc_rows=[vc("P1")],hub_rows=[unsigned_origin])
        # Existing historical proofs without team ID require manual audit.
        self.assertEqual(result["vc_hub_sites"],0)

    def test_partial_transport_is_protected_and_not_reassigned_as_full(self):
        result=plan(vc_rows=[{**vc("P1"),
                  "Trạng thái":"Đã giao một phần",
                  "SL thực tế":"3","Mã báo cáo":"BC-1"}])
        self.assertEqual(len(result["pending_tasks"]),0)
        self.assertTrue(result["review"])
        self.assertEqual(len(result["protected_details"]),1)

    def test_fully_finished_is_archived_not_deleted(self):
        result=plan(ld_rows=[{**ld("P1",status="Đã lắp đặt"),
                              "Mã báo cáo":"BC-LD","SL thực tế":"12"}])
        self.assertEqual(len(result["pending_tasks"]),0)
        self.assertTrue(result["review"])
        changes=detach_requests(result,SHEETS,"now")
        self.assertFalse(any("repeatCell" in c for c in changes))
        self.assertFalse(any(
            c["updateCells"]["range"]["sheetId"]==SHEETS["LAP_DAT"]
            for c in changes if "updateCells" in c))

    def test_unrelated_project_receipt_does_not_lock_new_project(self):
        other={**hub("P1"),"Mã dự án":"DA-OTHER"}
        result=plan(ld_rows=[ld("P1")],hub_rows=[other])
        self.assertEqual(len(result["pending_tasks"]),1)
        self.assertEqual(result["custody_sites"],0)

    def test_admin_has_read_only_impact_view(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        ui=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                and n.name=="teams_and_approval")
        text=ast.get_source_segment(source,ui)
        self.assertIn("XEM ẢNH HƯỞNG KHI XÓA ĐỘI TRƯỞNG",text)
        self.assertIn("impact=plan_detach(",text)
        self.assertIn('read_sheet("BAN_GIAO_TAP_KET")',text)
        self.assertIn('impact["pending_details"]+impact["protected_details"]',text)
        # The team-admin function also contains legitimate edit controls.
        # Validate only the read-only impact preview branch.
        impact_branch=text.split('with st.expander("🔎 XEM ẢNH HƯỞNG')[1].split(
            '    provision_team_password()')[0]
        self.assertNotIn('detach_requests(',impact_branch)
        self.assertNotIn('batch_update(',impact_branch)


if __name__=="__main__":
    unittest.main()
