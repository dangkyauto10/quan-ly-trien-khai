import ast
from pathlib import Path
import unittest

from preview_credential_accounts import (
    validate_custom_password,team_accounts,create_hash
)
from preview_signup_credentials import (
    registration_requests,pending_row,pending_for_registration,
    approval_credential_requests,WAITING,ACTIVATED,REJECTED
)

ROOT=Path(__file__).resolve().parents[1]
RID="DK-SELFTEST-001"
PROJECT="DA880"
PASSWORD="Hoa-Hong-Mua-Thu2026"
TEAM={"Mã đội":"KTV-0001","Tên đội/đội trưởng":"Nguyễn Văn A",
      "Mã dự án":PROJECT,"Trạng thái":"Hoạt động"}


def make_pending():
    row=pending_row(RID,PROJECT,PASSWORD,"2026-10-23T10:32:00+07:00")
    return {"Mã đăng ký":row[0],"Mã dự án":row[1],
            "Salt hex":row[2],"Mã băm PBKDF2":row[3],
            "Trạng thái":row[4],"_row":12}


def make_account(p):
    return ["tdv_uniqueid",TEAM["Mã đội"],PROJECT,"DOI_TRUONG",
            p["Salt hex"],p["Mã băm PBKDF2"],"Hoạt động",
            "2026-10-23T10:33:00+07:00","admin_preview","Tự đăng ký"]

class SignupCredentialTests(unittest.TestCase):
    def test_memorable_password_and_bad_password_rules(self):
        self.assertIsNone(validate_custom_password(PASSWORD,"Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password("123456","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password("MatKhau-12345678","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password("Nguyễn Văn A-2026","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password("XuanHa-0912345678","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password("aBcdEfgHiJKL123 ","Nguyễn Văn A","0912345678"))

    def test_memorable_ten_character_password_is_supported(self):
        valid="HoaNha8!xY"
        self.assertEqual(len(valid),10)
        self.assertIsNone(validate_custom_password(
            valid,"Nguyễn Văn A","0912345678"))
        salt,digest=create_hash(valid)
        self.assertEqual(len(salt),32)
        self.assertEqual(len(digest),64)
        self.assertIsNotNone(validate_custom_password(
            "Abc12Xyz","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password(
            "1234567890","Nguyễn Văn A","0912345678"))
        self.assertIsNotNone(validate_custom_password(
            "NguyenVanA26","Nguyễn Văn A","0912345678"))

    def test_manual_admin_choice_is_available_and_checked(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        func=next(n for n in ast.parse(source).body
                  if isinstance(n,ast.FunctionDef)
                  and n.name=="provision_team_password")
        snippet=ast.get_source_segment(source,func)
        self.assertIn('"Đội trưởng đề nghị / ADMIN nhập hộ"',snippet)
        self.assertIn('"Hệ thống tự tạo mật khẩu"',snippet)
        self.assertIn('custom_password=st.text_input(',snippet)
        self.assertIn('confirm_custom=st.text_input(',snippet)
        self.assertIn('custom_password!=confirm_custom',snippet)
        self.assertIn('validate_custom_password(',snippet)
        self.assertIn('password=(custom_password if method.startswith("Đội trưởng")',snippet)
        self.assertIn('salt,digest=create_hash(password)',snippet)

    def test_registration_batch_is_atomic_and_never_contains_plaintext(self):
        reg=[RID,123,"Nguyễn Văn A","0912345678","Xã A",
             "KTV lắp đặt","Xe máy","Chờ duyệt","","","",PROJECT,"Tự đăng ký"]
        pending=pending_row(RID,PROJECT,PASSWORD,"now")
        requests=registration_requests(101,102,reg,pending)
        self.assertEqual(len(requests),2)
        self.assertTrue(all("appendCells" in x for x in requests))
        self.assertEqual(requests[0]["appendCells"]["sheetId"],101)
        self.assertEqual(requests[1]["appendCells"]["sheetId"],102)
        self.assertNotIn(PASSWORD,str(requests))
        self.assertEqual(pending[4],WAITING)
        with self.assertRaises(ValueError):
            registration_requests(101,102,reg,{})  # Mismatched payload.

    def test_pending_before_approval_cannot_log_in(self):
        p=make_pending()
        self.assertFalse(team_accounts({},[],[]))
        self.assertEqual(pending_for_registration(RID,PROJECT,[p]),p)
        self.assertIsNone(pending_for_registration("DK-OLD",PROJECT,[p]))

    def test_one_confirm_activates_exact_saved_hash(self):
        p=make_pending()
        credential=make_account(p)
        changes=approval_credential_requests(111,112,p,credential)
        self.assertEqual(len(changes),2)
        self.assertNotIn(PASSWORD,str(changes))
        self.assertEqual(changes[0]["appendCells"]["sheetId"],112)
        self.assertEqual(changes[1]["updateCells"]["range"]["startRowIndex"],11)
        self.assertEqual(changes[1]["updateCells"]["rows"][0]["values"][2]
                         ["userEnteredValue"]["stringValue"],ACTIVATED)
        self.assertEqual(changes[1]["updateCells"]["range"]["startColumnIndex"],2)
        self.assertEqual([x["userEnteredValue"]["stringValue"] for x in
                          changes[1]["updateCells"]["rows"][0]["values"][:2]],
                         ["",""])
        account_rows=[{
            "Mã tài khoản":credential[0],"Mã đội":credential[1],
            "Mã dự án":credential[2],"Vai trò":credential[3],
            "Salt hex":credential[4],"Mã băm PBKDF2":credential[5],
            "Trạng thái":credential[6]}]
        result=team_accounts({},account_rows,[TEAM])
        self.assertEqual(result["tdv_uniqueid"]["role"],"DOI_TRUONG")
        self.assertEqual(result["tdv_uniqueid"]["hash"],p["Mã băm PBKDF2"])

    def test_rejection_marks_hash_rejected_no_account(self):
        p=make_pending()
        req=approval_credential_requests(111,112,p,rejected=True)
        self.assertEqual(len(req),1)
        self.assertEqual(req[0]["updateCells"]["rows"][0]["values"][2]
                         ["userEnteredValue"]["stringValue"],REJECTED)
        with self.assertRaises(ValueError):
            approval_credential_requests(111,112,p)
        with self.assertRaises(ValueError):
            approval_credential_requests(111,112,p,make_account(p),rejected=True)

    def test_duplicate_or_wrong_project_cannot_activate(self):
        p=make_pending()
        with self.assertRaises(ValueError):
            pending_for_registration(RID,PROJECT,[p,p])
        with self.assertRaises(ValueError):
            pending_for_registration(RID,"DA-OTHER",[p])
        bad={**p,"Trạng thái":ACTIVATED}
        with self.assertRaises(ValueError):
            pending_for_registration(RID,PROJECT,[bad])
        bad_credentials=make_account(p)
        bad_credentials[3]="ADMIN"
        with self.assertRaises(ValueError):
            approval_credential_requests(111,112,p,bad_credentials)

    def test_public_form_uses_password_confirmation_and_server_hash(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        fn=next(n for n in ast.parse(source).body
                if isinstance(n,ast.FunctionDef) and n.name=="register")
        s=ast.get_source_segment(source,fn)
        self.assertIn('desired_password=st.text_input(',s)
        self.assertIn('confirm_password=st.text_input(',s)
        self.assertIn('desired_password!=confirm_password',s)
        self.assertIn('validate_custom_password(',s)
        self.assertIn('pending_row(rid,project,desired_password,now())',s)
        self.assertIn('registration_requests(',s)
        self.assertIn('client()[0].batch_update({"requests":batch})',s)

    def test_admin_approval_is_mandatory_for_activation(self):
        s=(ROOT/"preview_approval_ui.py").read_text(encoding="utf-8")
        self.assertIn('if pending and decision=="Đã duyệt":',s)
        self.assertIn('approval_credential_requests(',s)
        self.assertIn('credential_changes=credential_changes',s)
        self.assertIn('if pending and decision=="Từ chối":',s)

if __name__=="__main__":
    unittest.main()
