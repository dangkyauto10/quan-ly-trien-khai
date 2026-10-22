import unittest
from preview_registration import team_id_from_registration, role_for_specialty

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

if __name__=="__main__":
    unittest.main()
