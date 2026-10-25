"""Regression: Admin-approved site rights become SKU task owners at allocation."""
import unittest
from preview_site_rights import allocation_owners, approved_team_site_overview
from preview_bulk_allocation import atomic_requests

PROJECT = "DA-TEST"
VC_TEAM = {"Mã đội":"VC1","Mã dự án":PROJECT,"Loại nhiệm vụ":"VC",
           "Trạng thái":"Hoạt động"}
LD_TEAM = {"Mã đội":"LD1","Mã dự án":PROJECT,"Loại nhiệm vụ":"KTV",
           "Trạng thái":"Hoạt động"}
REGISTRATIONS = [
    {"Trạng thái duyệt":"Đã duyệt","Mã dự án đăng ký":PROJECT,
     "Mã đội được gán":"VC1","Điểm VC Admin duyệt":"A","Điểm LĐ Admin duyệt":""},
    {"Trạng thái duyệt":"Đã duyệt","Mã dự án đăng ký":PROJECT,
     "Mã đội được gán":"LD1","Điểm VC Admin duyệt":"","Điểm LĐ Admin duyệt":"A"}
]
SHEET_IDS = {name:i+1 for i,name in enumerate((
    "DM_CHUAN","KHO_PHAN_BO","VAN_CHUYEN","LAP_DAT","TIEN_DO",
    "NHAT_KY_HE_THONG"))}

class ApprovedAllocationIntegrationTests(unittest.TestCase):
    def test_approved_site_visible_before_stock_allocation(self):
        locations=[{"Mã dự án":PROJECT,"Mã điểm":"A",
                    "Tên xã/phường/đơn vị":"Phường A","Trạng thái":"Hoạt động"}]
        view=approved_team_site_overview(VC_TEAM,REGISTRATIONS,locations,
                                         {"VAN_CHUYEN":[],"LAP_DAT":[]})
        self.assertEqual(len(view),1)
        self.assertEqual(view[0]["status"],"Đã duyệt điểm – Chưa phân bổ SKU")

    def test_allocation_auto_assigns_approved_roles_and_leaves_other_site_pending(self):
        owners=allocation_owners(REGISTRATIONS,[VC_TEAM,LD_TEAM],PROJECT)
        requests=atomic_requests(
            SHEET_IDS,[("A","SKU1",2),("B","SKU1",1)],
            "BATCH1",PROJECT,{"SKU1":{"name":"Thiết bị","unit":"Bộ"}},
            {"A":"Phường A","B":"Phường B"},"ADMIN","2026-10-26",
            approved_owners=owners)
        by_id={r["appendCells"]["sheetId"]:r["appendCells"]["rows"]
               for r in requests if "appendCells" in r}
        vc_rows=by_id[SHEET_IDS["VAN_CHUYEN"]]
        ld_rows=by_id[SHEET_IDS["LAP_DAT"]]
        def owner(row):
            return row["values"][6]["userEnteredValue"].get("stringValue","")
        self.assertEqual([owner(row) for row in vc_rows],["VC1",""])
        self.assertEqual([owner(row) for row in ld_rows],["LD1",""])

if __name__ == "__main__":
    unittest.main()
