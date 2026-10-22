import base64
import json
import unittest
from preview_remember import (
    issue_remember_token, verify_remember_token, VALID_SECONDS
)
KEY = "a" * 48
ACCOUNT = {"salt":"salt123456", "hash":"hash-should-never-be-saved-in-cookie",
           "role":"ADMIN","team_id":""}


class RememberLoginTests(unittest.TestCase):
    def test_valid(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        self.assertEqual(verify_remember_token(token,{"admin_preview":ACCOUNT},KEY,now=2000001),
                         {"username":"admin_preview","role":"ADMIN","team_id":""})

    def test_password_is_not_stored_in_cookie(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        payload=base64.urlsafe_b64decode(token.split(".")[0] + "==").decode()
        self.assertNotIn(ACCOUNT["hash"],payload)
        self.assertNotIn(ACCOUNT["salt"],payload)
        self.assertNotIn("PIN",payload)

    def test_expired(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        self.assertIsNone(verify_remember_token(token,{"admin_preview":ACCOUNT},
                          KEY,now=2000000+VALID_SECONDS))

    def test_tampered_cookie(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        altered=token[:-1] + ("f" if token[-1]!="f" else "e")
        self.assertIsNone(verify_remember_token(altered,{"admin_preview":ACCOUNT},KEY,
                          now=2000001))

    def test_password_change_revokes_remember(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        changed=dict(ACCOUNT,hash="different-hash")
        self.assertIsNone(verify_remember_token(token,{"admin_preview":changed},KEY,
                          now=2000001))

    def test_role_change_revokes_remember(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        changed=dict(ACCOUNT,role="DOI_TRUONG")
        self.assertIsNone(verify_remember_token(token,{"admin_preview":changed},KEY,
                          now=2000001))

    def test_wrong_signer(self):
        token=issue_remember_token("admin_preview",ACCOUNT,KEY,issued_at=2000000)
        self.assertIsNone(verify_remember_token(token,{"admin_preview":ACCOUNT},"b"*48,
                          now=2000001))

    def test_unsupported_role(self):
        bad=dict(ACCOUNT,role="GUEST")
        token=issue_remember_token("a",bad,KEY,issued_at=2000000)
        self.assertIsNone(verify_remember_token(token,{"a":bad},KEY,now=2000001))

if __name__ == "__main__":
    unittest.main()
