"""Admin-approved site rights: ordering, conflict prevention and rollout."""
import unittest

from preview_site_rights import (
    site_ids, owner_index, allocation_owners, approval_task_plan,
    right_updates_for_approval, right_cell_request,
    approved_team_site_overview
)

PROJECT="DA-TEST"
VC={"Mã đội":"VC1","Mã dự án":PROJECT,"Loại nhiệm vụ":"VC","Trạng thái":"Hoạt động"}
LD={"Mã đội":"LD1","Mã dự án":PROJECT,"Loại nhiệm vụ":"KTV","Trạng thái":"Hoạt động"}
VC2={"Mã đội":"VC2","Mã dự án":PROJECT,"Loại nhiệm vụ":"VC","Trạng thái":"Hoạt động"}
REG_VC={"Mã đăng ký":"R1","Mã đội được gán":"VC1","Mã dự án đăng ký":PROJECT,
        "Trạng thái duyệt":"Đã duyệt","Điểm VC Admin duyệt":"A,B",
        "Điểm LĐ Admin duyệt":"","_row":2}
REG_LD={"Mã đăng ký":"R2","Mã đội được gán":"LD1","Mã dự án đăng ký":PROJECT,
        "Trạng thái duyệt":"Đã duyệt","Điểm VC Admin duyệt":"",
        "Điểm LĐ Admin duyệt":"A","_row":3}
SITES=[{"Mã dự án":PROJECT,"Mã điểm":x,"Trạng thái":"Hoạt động"}
       for x in ("A","B","C")]


def task(point,team="",report="",row=2):
    return {"Mã nhiệm vụ VC":"VC-"+point,"Mã dự án":PROJECT,"Mã điểm":point,
            "SKU":"SKU1","Mã đội VC":team,"Trạng thái":"Chưa giao",
            "Mã báo cáo":report,"_row":row}


class SiteRightsTests(unittest.TestCase):
    def test_approved_sites_show_before_sku_allocation(self):
        locations=[{**r,"Tên xã/phường/đơn vị": "Phường "+r["Mã điểm"]}
                   for r in SITES]
        rows=approved_team_site_overview(
            VC,[REG_VC,REG_LD],locations,
            {"VAN_CHUYEN":[],"LAP_DAT":[]})
        self.assertEqual([r["site_id"] for r in rows],["A","B"])
        self.assertEqual([r["sku_tasks"] for r in rows],[0,0])
        self.assertTrue(all("Đã duyệt điểm" in r["status"] for r in rows))
        self.assertTrue(all("Chưa phân bổ" in r["status"] for r in rows))

    def test_sku_allocation_changes_task_status_not_site_rights(self):
        rows=approved_team_site_overview(
            VC,[REG_VC],SITES,
            {"VAN_CHUYEN":[task("A",team="VC1")],"LAP_DAT":[]})
        self.assertEqual({r["site_id"] for r in rows},{"A","B"})
        self.assertEqual(rows[0]["sku_tasks"],1)
        self.assertEqual(rows[0]["linked_tasks"],1)
        self.assertIn("Đã có nhiệm vụ",rows[0]["status"])
        self.assertIn("Chưa phân bổ",rows[1]["status"])

    def test_unapproved_proposals_not_shown_as_assigned_sites(self):
        pending={**REG_VC,"Trạng thái duyệt":"Chờ duyệt"}
        with self.assertRaisesRegex(ValueError,"chưa có hồ sơ"):
            approved_team_site_overview(
                VC,[pending],SITES,{"VAN_CHUYEN":[]})

    def test_no_allocation_needed_before_approval(self):
        result=approval_task_plan(
            PROJECT,"VC","VC2",["C"],SITES,[REG_VC,REG_LD],
            [VC,LD,VC2],{"VAN_CHUYEN":[],"LAP_DAT":[]},[])
        self.assertEqual(result,{"VAN_CHUYEN":[]})
        self.assertEqual(
            right_updates_for_approval(4,"VC",["C"]),
            {"VAN_CHUYEN":"C","LAP_DAT":""})
        self.assertEqual(right_cell_request(5,4,"VAN_CHUYEN","C")
                         ["updateCells"]["range"]["startColumnIndex"],13)

    def test_existing_allocation_attaches_only_requested_role(self):
        result=approval_task_plan(
            PROJECT,"VC","VC2",["C"],SITES,[REG_VC,REG_LD],
            [VC,LD,VC2],{"VAN_CHUYEN":[task("C")],"LAP_DAT":[]},[])
        self.assertEqual(len(result["VAN_CHUYEN"]),1)
        # Already-approved VC and LD may have DIFFERENT teams at the same point.
        owners=allocation_owners([REG_VC,REG_LD],[VC,LD],PROJECT)
        self.assertEqual(owners[("VAN_CHUYEN","A")],"VC1")
        self.assertEqual(owners[("LAP_DAT","A")],"LD1")

    def test_site_must_be_reclaimed_before_new_approval(self):
        with self.assertRaisesRegex(ValueError,"phải thu hồi"):
            approval_task_plan(PROJECT,"VC","VC2",["B"],SITES,
                [REG_VC,REG_LD],[VC,LD,VC2],
                {"VAN_CHUYEN":[task("B",team="VC1")],"LAP_DAT":[]},[])
        reclaimed={**REG_VC,"Điểm VC Admin duyệt":"A"}
        result=approval_task_plan(PROJECT,"VC","VC2",["B"],SITES,
            [reclaimed,REG_LD],[VC,LD,VC2],
            {"VAN_CHUYEN":[task("B")],"LAP_DAT":[]},[])
        self.assertEqual(len(result["VAN_CHUYEN"]),1)

    def test_no_duplicate_or_wrong_team(self):
        duplicate={**REG_VC,"Mã đăng ký":"R3","Mã đội được gán":"VC2",
                   "Điểm VC Admin duyệt":"B","_row":4}
        with self.assertRaisesRegex(ValueError,"trùng"):
            owner_index([REG_VC,REG_LD,duplicate],[VC,LD,VC2],PROJECT)
        with self.assertRaisesRegex(ValueError,"vẫn có nhiệm vụ"):
            approval_task_plan(PROJECT,"VC","VC2",["C"],SITES,
                [REG_VC,REG_LD],[VC,LD,VC2],
                {"VAN_CHUYEN":[task("C",team="VC1")],"LAP_DAT":[]},[])

    def test_signed_goods_or_report_block_assignment(self):
        receipt={"Mã dự án":PROJECT,"Mã điểm":"C","SKU":"SKU1",
                 "Trạng thái":"KTV đã nhận tại tập kết"}
        with self.assertRaisesRegex(ValueError,"đối soát"):
            approval_task_plan(PROJECT,"VC","VC2",["C"],SITES,
                [REG_VC,REG_LD],[VC,LD,VC2],
                {"VAN_CHUYEN":[task("C")],"LAP_DAT":[]},[receipt])
        with self.assertRaisesRegex(ValueError,"đối soát"):
            approval_task_plan(PROJECT,"VC","VC2",["C"],SITES,
                [REG_VC,REG_LD],[VC,LD,VC2],
                {"VAN_CHUYEN":[task("C",report="B1")],"LAP_DAT":[]},[])


if __name__=="__main__":
    unittest.main()
