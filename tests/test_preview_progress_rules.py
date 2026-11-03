"""PREVIEW regression tests for KTV-as-source-of-truth and atomic allocation."""
import ast
from pathlib import Path
import unittest

from preview_progress_rules import site_progress


PROJECT = "DA880"
OTHER = "DA-TEST01"
VC = [{"Mã nhiệm vụ VC":"VC1","Mã dự án":PROJECT,"Mã điểm":"P1",
       "Trạng thái":"Chưa giao","SL giao":"2","SL thực tế":""}]
LD = [{"Mã nhiệm vụ LD":"LD1","Mã dự án":PROJECT,"Mã điểm":"P1",
       "Trạng thái":"Chưa lắp","SL lắp":"2","SL thực tế":""}]


class SiteProgressRulesTests(unittest.TestCase):
    def test_full_verified_ktv_completion_without_vc_report(self):
        ld=[{**LD[0],"Trạng thái":"Đã lắp đặt","SL thực tế":"2"}]
        result=site_progress(PROJECT,"P1",VC,ld)
        self.assertEqual(result["status"],"Hoàn thành")
        self.assertEqual(result["ld_done"],1)
        self.assertEqual(result["vc_done"],0)

    def test_ktv_partial_install_is_in_progress(self):
        ld=[{**LD[0],"Trạng thái":"Đã lắp một phần","SL thực tế":"1"}]
        self.assertEqual(site_progress(PROJECT,"P1",VC,ld)["status"],
                         "Đang thực hiện")

    def test_closed_status_without_valid_qty_does_not_complete(self):
        for qty in ("", "1", "3", "-1", "nan"):
            with self.subTest(qty=qty):
                ld=[{**LD[0],"Trạng thái":"Đã lắp đặt","SL thực tế":qty}]
                self.assertEqual(site_progress(PROJECT,"P1",VC,ld)["ld_done"],0)

    def test_vc_complete_not_same_as_ktv_complete(self):
        vc=[{**VC[0],"Trạng thái":"Đã giao hàng","SL thực tế":"2"}]
        self.assertEqual(site_progress(PROJECT,"P1",vc,LD)["status"],
                         "Đang thực hiện")

    def test_status_and_actual_overrides_simulate_atomic_ktv_report(self):
        snap=site_progress(PROJECT,"P1",VC,LD,{"LD1":"Đã lắp đặt"},{"LD1":2})
        self.assertEqual(snap["status"],"Hoàn thành")

    def test_projects_and_sites_never_leak_into_each_other(self):
        others=[{**LD[0],"Mã dự án":OTHER,"Mã điểm":"P1",
                 "Trạng thái":"Đã lắp đặt","SL thực tế":"2"}]
        self.assertEqual(site_progress(PROJECT,"P1",VC,LD+others)["ld_done"],0)
        self.assertEqual(site_progress(PROJECT,"P2",VC,LD)["total_ld"],0)

    def test_single_site_ui_uses_atomic_batch_not_sequential_appends(self):
        text=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(text)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                and n.name=="allocate_single")
        snippet=ast.get_source_segment(text,fn)
        self.assertIn("atomic_requests(",snippet)
        self.assertIn("verify_plan(",snippet)
        self.assertIn("read_sheet_live(",snippet)
        self.assertIn('spreadsheet.batch_update({"requests":reqs})',snippet)
        self.assertNotIn('append("KHO_PHAN_BO"',snippet)
        self.assertNotIn('append("VAN_CHUYEN"',snippet)
        self.assertNotIn('append("LAP_DAT"',snippet)

    def test_leadership_ui_filters_one_project(self):
        text=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(text)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                and n.name=="dashboard")
        snippet=ast.get_source_segment(text,fn)
        self.assertIn('project=st.selectbox("Dự án cần xem",ids',snippet)
        self.assertNotIn('options=ids+["Tất cả"]',snippet)


if __name__=="__main__":
    unittest.main()
