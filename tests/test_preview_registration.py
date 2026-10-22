import unittest
from preview_registration import team_id_from_registration, role_for_specialty, matching_teams, approval_requests

class ApprovalMappingTests(unittest.TestCase):
    def test_role_vc(self):
        self.assertEqual(role_for_specialty("Vận chuyển / Giao nhận"),"VC")
    def test_role_ktv(self):
        self.assertEqual(role_for_specialty("KTV lắp đặt"),"KTV")
    def test_other_not_auto_team(self):
        self.assertEqual(role_for_specialty("Điều phối / Giám sát"),"")
    def test_deterministic_team_id(self):
        self.assertEqual(team_id_from_registration("DK-FB983DF8F23E","KTV"),
                         "KTV-FB983DF8F23E")
    def test_reject_invalid_role(self):
        with self.assertRaises(ValueError):
            team_id_from_registration("DK-123","ADMIN")


    def test_reuses_existing_team(self):
        teams=[{"Mã đội":"TQ-01","Tên đội/đội trưởng":"Nguyễn Ngọc Hiền",
                "SĐT đội trưởng":"0913878775","Loại nhiệm vụ":"KTV",
                "Mã dự án":"DA-TEST01","Trạng thái":"Hoạt động"}]
        found=matching_teams(teams,name="Nguyễn Ngọc Hiền",phone="0913878775",
                             kind="KTV",project="DA-TEST01")
        self.assertEqual(found[0]["Mã đội"],"TQ-01")

    def test_cannot_match_wrong_project_or_role(self):
        teams=[{"Mã đội":"TQ-01","Tên đội/đội trưởng":"Nguyễn Ngọc Hiền",
                "SĐT đội trưởng":"0913878775","Loại nhiệm vụ":"KTV",
                "Mã dự án":"DA-TEST01","Trạng thái":"Hoạt động"}]
        self.assertEqual(matching_teams(teams,name="Nguyễn Ngọc Hiền",
            phone="0913878775",kind="VC",project="DA-TEST01"), [])
        self.assertEqual(matching_teams(teams,name="Nguyễn Ngọc Hiền",
            phone="0913878775",kind="KTV",project="DA-OTHER"), [])


    def test_combined_vc_ld_specialty(self):
        self.assertEqual(role_for_specialty("Vận chuyển & Lắp đặt"),"VC+KTV")
        self.assertEqual(team_id_from_registration("DK-123","VC+KTV"),"VC-LD-123")

    def test_atomic_approve_new_team(self):
        team=["KTV-123","Đội trưởng thử","0912345678","KTV","","Hoạt động","DA-TEST01",""]
        requests=approval_requests(101,202,4,"Đã duyệt",team,"KTV-123","admin",46317.75)
        self.assertEqual(len(requests),3)
        self.assertIn("appendCells",requests[0])
        self.assertEqual(requests[0]["appendCells"]["sheetId"],202)
        update=requests[1]["updateCells"]
        self.assertEqual(update["range"]["sheetId"],101)
        self.assertEqual(update["range"]["startRowIndex"],3)
        self.assertEqual(update["rows"][0]["values"][0]["userEnteredValue"]["stringValue"],"Đã duyệt")
        fmt=requests[-1]["repeatCell"]
        self.assertEqual(fmt["range"]["startColumnIndex"],10)
        self.assertEqual(fmt["range"]["startRowIndex"],3)
        self.assertEqual(fmt["cell"]["userEnteredFormat"]["numberFormat"]["pattern"],"dd/mm/yyyy hh:mm")

    def test_approve_existing_team_without_duplicate(self):
        requests=approval_requests(101,202,2,"Đã duyệt",None,"TQ-01","admin",46317.5)
        self.assertEqual(len(requests),2)
        self.assertIn("updateCells",requests[0])

    def test_reject_without_team(self):
        requests=approval_requests(101,202,2,"Từ chối",None,"","admin",46317.5)
        self.assertEqual(len(requests),2)
        values=requests[0]["updateCells"]["rows"][0]["values"]
        self.assertEqual(values[0]["userEnteredValue"]["stringValue"],"Từ chối")
        self.assertEqual(values[1]["userEnteredValue"]["stringValue"],"")

    def test_reject_cannot_create_team(self):
        with self.assertRaises(ValueError):
            approval_requests(101,202,2,"Từ chối",
                              ["TQ-01"]*8,"TQ-01","admin",46317.5)

if __name__=="__main__":
    unittest.main()
