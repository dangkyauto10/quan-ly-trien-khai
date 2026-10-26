"""Adding new unowned sites to an existing approved VC/KTV team."""
import ast
from pathlib import Path
import unittest

from preview_site_rights import (
    supplemental_site_plan, supplemental_site_signature,
    supplemental_site_requests,
)

PROJECT = "DA880"
TEAM = {"Mã đội": "KTV-VY", "Mã dự án": PROJECT,
        "Loại nhiệm vụ": "KTV", "Trạng thái": "Hoạt động"}
OTHER = {"Mã đội": "KTV-OTHER", "Mã dự án": PROJECT,
         "Loại nhiệm vụ": "KTV", "Trạng thái": "Hoạt động"}
REG = {"Mã đăng ký": "DK-VY", "Mã đội được gán": "KTV-VY",
       "Mã dự án đăng ký": PROJECT, "Trạng thái duyệt": "Đã duyệt",
       "Điểm VC Admin duyệt": "", "Điểm LĐ Admin duyệt": "A", "_row": 5}
SITES = [{"Mã dự án": PROJECT, "Mã điểm": pid, "Trạng thái": "Hoạt động"}
         for pid in ("A", "B", "C")]


def task(pid, sku, row, assigned="", status="Chưa lắp", report=""):
    return {"Mã nhiệm vụ LD": "LD-" + pid + "-" + sku,
            "Mã dự án": PROJECT, "Mã điểm": pid, "SKU": sku,
            "SL lắp": "3", "Mã đội KTV": assigned,
            "Trạng thái": status, "Mã báo cáo": report, "_row": row}


def plan(selected=("B",), registrations=None, tasks=None, hubs=None,
         team=TEAM):
    return supplemental_site_plan(
        team, "LD", selected, SITES,
        [REG] if registrations is None else registrations,
        [TEAM, OTHER],
        {"LAP_DAT": [task("B", "TB01", 12), task("B", "TB02", 13)]
         if tasks is None else tasks},
        [] if hubs is None else hubs)


class SupplementalTests(unittest.TestCase):
    def test_admin_ui_is_reachable_and_groups_each_site_sku(self):
        source = (Path(__file__).resolve().parents[1] / "preview_app.py")\
            .read_text(encoding="utf-8")
        funcs = {node.name: node for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef)}
        self.assertIn("supplemental_site_assignment_admin", funcs)
        ui = ast.get_source_segment(source, funcs["supplemental_site_assignment_admin"])
        self.assertIn("GIAO BỔ SUNG ĐIỂM CHƯA CÓ ĐỘI", ui)
        self.assertIn('with st.container(border=True):', ui)
        self.assertIn('st.dataframe(preview, hide_index=True, use_container_width=True)', ui)
        approval = ast.get_source_segment(source, funcs["teams_and_approval"])
        self.assertLess(approval.index("supplemental_site_assignment_admin()"),
                        approval.index("team_reassignment_admin()"))
        self.assertLess(approval.index("supplemental_site_assignment_admin()"),
                        approval.index("    return"))

    def test_adds_unowned_site_and_preserves_existing_rights(self):
        p = plan()
        self.assertEqual(p["sites"], ("B",))
        self.assertEqual(p["old_rights"]["LAP_DAT"], "A")
        self.assertEqual(p["new_rights"]["LAP_DAT"], "A,B")
        self.assertEqual(len(p["tasks"]["LAP_DAT"]), 2)
        reqs = supplemental_site_requests(
            p, {"LAP_DAT": 10, "DANG_KY_THANH_VIEN": 20})
        self.assertEqual(len(reqs), 2)
        task_req = reqs[0]["repeatCell"]
        self.assertEqual(task_req["range"]["startColumnIndex"], 6)
        self.assertEqual(task_req["range"]["endColumnIndex"], 7)
        right_req = reqs[1]["updateCells"]
        self.assertEqual(right_req["range"]["startColumnIndex"], 14)
        self.assertEqual(right_req["rows"][0]["values"][0][
            "userEnteredValue"]["stringValue"], "A,B")
        # Only assignment and approved rights; no warehouse/billing writes.
        self.assertFalse(any("KHO_PHAN_BO" in str(r) for r in reqs))

    def test_plan_signature_catches_changed_task_or_rights(self):
        first = plan()
        changed = plan(tasks=[task("B", "TB01", 12)])
        self.assertNotEqual(supplemental_site_signature(first),
                            supplemental_site_signature(changed))
        new_reg = {**REG, "Điểm LĐ Admin duyệt": "A,C"}
        changed_rights = plan(registrations=[new_reg])
        self.assertNotEqual(supplemental_site_signature(first),
                            supplemental_site_signature(changed_rights))

    def test_rejects_second_team_rights_or_assigned_work(self):
        other_reg = {**REG, "Mã đăng ký": "DK-OTHER",
                     "Mã đội được gán": "KTV-OTHER",
                     "Điểm LĐ Admin duyệt": "B", "_row": 6}
        with self.assertRaisesRegex(ValueError, "đã có đội"):
            plan(registrations=[REG, other_reg])
        with self.assertRaises(ValueError):
            plan(tasks=[task("B", "TB01", 12, assigned="KTV-OTHER")])

    def test_rejects_proven_or_nonpending_work(self):
        with self.assertRaisesRegex(ValueError, "bằng chứng"):
            plan(tasks=[task("B", "TB01", 12, report="BC-1")])
        with self.assertRaises(ValueError):
            plan(tasks=[task("B", "TB01", 12, status="Đã lắp đặt")])
        hub = {"Mã dự án": PROJECT, "Mã điểm": "B", "SKU": "TB01",
               "Trạng thái": "KTV đã nhận tại tập kết"}
        with self.assertRaisesRegex(ValueError, "bằng chứng"):
            plan(hubs=[hub])

    def test_allows_new_site_before_sku_allocation(self):
        p = plan(selected=("C",))
        self.assertEqual(p["tasks"]["LAP_DAT"], [])
        self.assertEqual(p["new_rights"]["LAP_DAT"], "A,C")
        reqs = supplemental_site_requests(
            p, {"DANG_KY_THANH_VIEN": 20})
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["updateCells"]["range"]["startColumnIndex"], 14)

    def test_rejects_unauthorized_team(self):
        with self.assertRaises(ValueError):
            plan(team={**TEAM, "Trạng thái": "Tạm dừng"})
        with self.assertRaises(ValueError):
            plan(registrations=[])
        with self.assertRaises(ValueError):
            plan(selected=("B", "B"))


if __name__ == "__main__":
    unittest.main()
