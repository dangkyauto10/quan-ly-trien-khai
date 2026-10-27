import ast
from pathlib import Path
import unittest

from preview_leader_access import (
    LEADER_SESSION_USERNAME, check_leader_password,
    make_leader_session, verify_leader_session,
)

ROOT=Path(__file__).resolve().parents[1]


class LeadershipPasswordTests(unittest.TestCase):
    def test_configured_password_is_checked_exactly(self):
        self.assertTrue(check_leader_password("Leader-903", "Leader-903"))
        self.assertFalse(check_leader_password("leader-903", "Leader-903"))
        self.assertFalse(check_leader_password("wrong", "Leader-903"))

    def test_missing_password_never_authenticates(self):
        self.assertFalse(check_leader_password("", ""))
        self.assertFalse(check_leader_password("anything", ""))
        self.assertIsNone(make_leader_session(""))

    def test_session_is_read_only_leader_and_does_not_store_password(self):
        account=make_leader_session("Leader-903")
        self.assertEqual(account["username"],LEADER_SESSION_USERNAME)
        self.assertEqual(account["role"],"LANH_DAO")
        self.assertEqual(account["team_id"],"")
        self.assertNotIn("password",account)
        self.assertTrue(verify_leader_session(account,"Leader-903"))

    def test_password_rotation_invalidates_existing_session(self):
        account=make_leader_session("Leader-903")
        self.assertFalse(verify_leader_session(account,"New-Leader-904"))

    def test_wrong_role_or_session_name_is_rejected(self):
        account=make_leader_session("Leader-903")
        self.assertFalse(verify_leader_session({**account,"role":"ADMIN"},"Leader-903"))
        self.assertFalse(verify_leader_session({**account,"username":"admin"},"Leader-903"))

    def test_login_uses_single_secret_without_account_hash_setup(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        login=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                   and n.name=="leadership_login")
        calls=[n.func.id for n in ast.walk(login)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertIn("check_leader_password",calls)
        self.assertIn("make_leader_session",calls)
        self.assertNotIn("valid_login",calls)
        self.assertNotIn("remember_signing_key",calls)
        self.assertIn('st.secrets.get("leader_view_password", "")',
                      ast.get_source_segment(source,login))

    def test_dashboard_keeps_admin_and_leadership_only_access(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        dashboard=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                       and n.name=="dashboard")
        checks=[n for n in ast.walk(dashboard) if isinstance(n,ast.Call)
                and isinstance(n.func,ast.Name) and n.func.id=="require_role"]
        self.assertEqual(len(checks),1)
        self.assertEqual([x.value for x in checks[0].args],["ADMIN","LANH_DAO"])


if __name__=="__main__":
    unittest.main()
