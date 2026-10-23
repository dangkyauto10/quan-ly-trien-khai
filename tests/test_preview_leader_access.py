import ast
from pathlib import Path
import unittest

from preview_leader_access import leadership_username


ROOT=Path(__file__).resolve().parents[1]

class LeadershipAccessTests(unittest.TestCase):
    def test_one_leader_password_only_resolution(self):
        accounts={"admin":{"role":"ADMIN"},
                  "captain":{"role":"DOI_TRUONG"},
                  "leader_preview":{"role":"LANH_DAO"}}
        self.assertEqual(leadership_username(accounts),"leader_preview")

    def test_missing_leader_never_falls_back_to_admin(self):
        self.assertIsNone(leadership_username({"admin":{"role":"ADMIN"}}))

    def test_multiple_leaders_requires_explicit_allowlist(self):
        accounts={"a":{"role":"LANH_DAO"},"b":{"role":"LANH_DAO"}}
        self.assertIsNone(leadership_username(accounts))
        self.assertEqual(leadership_username(accounts,"b"),"b")
        self.assertIsNone(leadership_username(accounts,"admin"))
        self.assertIsNone(leadership_username({"admin":{"role":"ADMIN"}},"admin"))

    def test_invalid_account_does_not_count_as_leadership(self):
        self.assertIsNone(leadership_username({"bad":None}))
        self.assertIsNone(leadership_username(None))

    def test_leader_password_only_login_reuses_secured_pbkdf_login(self):
        tree=ast.parse((ROOT/"preview_app.py").read_text(encoding="utf-8"))
        login=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and
                   n.name=="leadership_login")
        calls=[n.func.id for n in ast.walk(login)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertIn("valid_login",calls)
        self.assertIn("remember_signing_key",calls)
        self.assertIn("issue_remember_token",calls)
        self.assertIn("leadership_username",calls)
        self.assertNotIn("pbkdf",calls)  # Only use common locked-down authentication.

    def test_leader_menu_goes_directly_to_report(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        self.assertIn('return "📊 Báo cáo tiến độ"',source)
        self.assertIn('return "__LEADERSHIP_LOGIN__"',source)
        self.assertIn('if view=="__LEADERSHIP_LOGIN__":leadership_login()',source)
        self.assertIn('"Ghi nhớ đăng nhập trên thiết bị này (30 ngày)"',source)
        self.assertIn('st.session_state["_remember_action"]="set"',source)
        self.assertIn('st.session_state["_remember_action"]="remove"',source)


if __name__=="__main__":
    unittest.main()
