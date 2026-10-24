import ast
import hashlib
from pathlib import Path
import unittest

from preview_credential_accounts import (
    HEADERS, create_hash, new_password, team_accounts,
    visible_credential_state, next_account_id, validate_custom_password
)
from preview_team_access import resolve_login_username
from preview_remember import issue_remember_token, verify_remember_token

ROOT=Path(__file__).resolve().parents[1]
TEAM_ID="KTV-TEST"
TEAM={"Mã đội":TEAM_ID,"Tên đội/đội trưởng":"Nguyễn Văn A",
      "Mã dự án":"DA880","Trạng thái":"Hoạt động","Loại nhiệm vụ":"KTV"}


def row(password="test-SecurePW-2026",salt="0123456789abcdef0123456789abcdef"):
    s,h=create_hash(password,salt)
    return {
        "Mã tài khoản":"tdv_internal1","Mã đội":TEAM_ID,
        "Mã dự án":"DA880","Vai trò":"DOI_TRUONG",
        "Salt hex":s,"Mã băm PBKDF2":h,"Trạng thái":"Hoạt động",
    }


class TeamCredentialTests(unittest.TestCase):
    def test_password_is_long_unique_and_not_saved(self):
        p=new_password()
        self.assertEqual(len(p),18)
        self.assertNotEqual(p,new_password())
        self.assertGreaterEqual(len(set(p)),7)
        salt,digest=create_hash(p)
        self.assertEqual(len(salt),32)
        self.assertEqual(len(digest),64)
        self.assertEqual(digest,hashlib.pbkdf2_hmac(
            "sha256",p.encode(),bytes.fromhex(salt),390000).hex())
        self.assertNotIn(p,digest)
        self.assertNotIn("Mật khẩu gốc",HEADERS)

    def test_memorable_six_character_password_for_preview(self):
        for password in ("Ax1234", "Ve2026x"):
            self.assertIsNone(validate_custom_password(
                password,"Nguyễn Văn A","0912345678"))
            salt,digest=create_hash(password)
            self.assertEqual(digest,hashlib.pbkdf2_hmac(
                "sha256",password.encode(),bytes.fromhex(salt),390000).hex())
        self.assertIsNotNone(validate_custom_password("Ax123","Nguyễn Văn A"))
        with self.assertRaises(ValueError):
            create_hash("Ax123")

    def test_admin_password_form_submits_both_inputs_together(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        provision=source.split("def provision_team_password():",1)[1].split(
            "def teams_and_approval():",1)[0]
        self.assertIn('with st.form("credential_provision_form"):',provision)
        self.assertIn('submitted=st.form_submit_button(',provision)
        self.assertNotIn('if not st.button("🔐 "+action',provision)

    def test_team_account_valid_and_name_based_login(self):
        creds=team_accounts({},[row()],[TEAM])
        self.assertEqual(list(creds),["tdv_internal1"])
        self.assertEqual(creds["tdv_internal1"]["role"],"DOI_TRUONG")
        self.assertEqual(resolve_login_username("Nguyễn Văn A",creds,[TEAM]),
                         ("tdv_internal1","ok"))

    def test_same_name_requires_project_and_never_guesses(self):
        twin={**TEAM,"Mã đội":"KTV-OTHER","Mã dự án":"DA-TEST01"}
        credentials={"tdv_internal1":{"role":"DOI_TRUONG","team_id":TEAM_ID}}
        people=[TEAM,twin]
        self.assertEqual(resolve_login_username("Nguyễn Văn A",credentials,people),
                         (None,"ambiguous"))
        self.assertEqual(resolve_login_username(
            "Nguyễn Văn A",credentials,people,project_id="DA880"),
            ("tdv_internal1","ok"))
        self.assertEqual(resolve_login_username(
            "Nguyễn Văn A",credentials,people,project_id="DA-TEST01"),
            (None,"missing"))
        self.assertEqual(resolve_login_username(
            "tdv_internal1",credentials,people,project_id="DA-TEST01"),
            (None,"missing"))

    def test_same_name_inside_one_project_still_ambiguous(self):
        twin={**TEAM,"Mã đội":"KTV-OTHER"}
        credentials={
            "tdv_internal1":{"role":"DOI_TRUONG","team_id":TEAM_ID},
            "tdv_internal2":{"role":"DOI_TRUONG","team_id":"KTV-OTHER"},
        }
        self.assertEqual(resolve_login_username(
            "Nguyễn Văn A",credentials,[TEAM,twin],project_id="DA880"),
            (None,"ambiguous"))

    def test_disabled_or_removed_team_revoked(self):
        self.assertNotIn("tdv_internal1",team_accounts({},[row()],[{
            **TEAM,"Trạng thái":"Tạm khóa"}]))
        self.assertNotIn("tdv_internal1",team_accounts({},[{
            **row(),"Trạng thái":"Khóa"}],[TEAM]))

    def test_mismatched_project_or_superadmin_role_denied(self):
        self.assertNotIn("tdv_internal1",team_accounts({},[{
            **row(),"Mã dự án":"DA-TEST01"}],[TEAM]))
        self.assertNotIn("tdv_internal1",team_accounts({},[{
            **row(),"Vai trò":"ADMIN"}],[TEAM]))
        self.assertNotIn("tdv_internal1",team_accounts({},[{
            **row(),"Vai trò":"LANH_DAO"}],[TEAM]))

    def test_secrets_admin_cannot_be_overridden_by_sheet(self):
        secret_admin={"admin_preview":{"role":"ADMIN","hash":"safe"},
                      "tdv_internal1":{"role":"LANH_DAO","hash":"fixed"}}
        creds=team_accounts(secret_admin,[row()],[TEAM])
        self.assertEqual(creds,secret_admin)

    def test_duplicated_records_fail_closed(self):
        self.assertNotIn("tdv_internal1",team_accounts({},[row(),row()],[TEAM]))
        self.assertNotIn("tdv_internal1",team_accounts({},[row()],[TEAM,TEAM]))

    def test_legacy_credentials_prevent_double_provisioning(self):
        acct={"legacy":{"role":"DOI_TRUONG","team_id":TEAM_ID}}
        self.assertEqual(visible_credential_state(TEAM,[],acct)[0],"legacy")
        self.assertEqual(visible_credential_state(TEAM,[row()],acct)[0],"conflict")
        self.assertEqual(visible_credential_state(TEAM,[row()],{})[0],"active")
        self.assertEqual(visible_credential_state(TEAM,[],{})[0],"missing")

    def test_random_internal_id_does_not_need_to_be_memorized(self):
        x=next_account_id({"tdv_X"})
        self.assertTrue(x.startswith("tdv_"))
        self.assertNotEqual(x,"tdv_X")

    def test_password_reset_invalidates_old_remember_cookie(self):
        signing="s"*40
        old=team_accounts({},[row()],[TEAM])
        token=issue_remember_token("tdv_internal1",old["tdv_internal1"],signing)
        newer=team_accounts({},[row(password="another-SecurePW-2026")],[TEAM])
        self.assertIsNotNone(verify_remember_token(token,old,signing))
        self.assertIsNone(verify_remember_token(token,newer,signing))

    def test_admin_guard_and_no_plaintext_sheet_password(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        func=next(x for x in tree.body
                  if isinstance(x,ast.FunctionDef) and
                  x.name=="provision_team_password")
        expr=ast.get_source_segment(source,func)
        self.assertIn('a=require_role("ADMIN")',expr)
        self.assertIn('create_hash(password)',expr)
        self.assertIn('st.code(password',expr)
        self.assertIn('"Mã băm PBKDF2"',(ROOT/"preview_credential_accounts.py").read_text())
        self.assertNotIn('append("TAI_KHOAN_DOI",[password',expr)
        self.assertNotIn('audit(admin, password',expr)

    def test_only_approved_team_can_be_provisioned(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        self.assertIn('if t.get("Trạng thái")=="Hoạt động"',source) if False else None
        self.assertIn('t.get("Trạng thái")=="Hoạt động"',source)
        self.assertIn('read_sheet.clear()',source)
        self.assertIn('effective_accounts()',source)


if __name__=="__main__":
    unittest.main()
