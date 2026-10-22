import unittest
from preview_registration import team_id_from_registration, role_for_specialty, matching_teams

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

if __name__=="__main__":
    unittest.main()
