"""Project-first searchable field-team login regression tests (PREVIEW)."""
import ast
import unittest
from pathlib import Path

from preview_team_access import project_login_choices, resolve_login_username


def team(tid, name, project, role="VC", status="Hoạt động"):
    return {"Mã đội": tid, "Tên đội/đội trưởng": name,
            "Mã dự án": project, "Loại nhiệm vụ": role, "Trạng thái": status}


class ProjectLoginSuggestionTests(unittest.TestCase):
    def setUp(self):
        self.teams = [
            team("V1", "Trần Mai Lan Anh", "DA880", "VC"),
            team("K1", "Nguyễn Văn Bình", "DA880", "KTV"),
            team("K2", "Lê Thị Hoa", "DA880", "VC+KTV"),
            team("V2", "Sai Dự Án", "DA881"),
            team("V3", "Ngừng Hoạt Động", "DA880", status="Ngừng"),
            team("K3", "Chưa Có Tài Khoản", "DA880"),
            team("M1", "Không Phải VC KTV", "DA880", role="ĐIỀU PHỐI"),
        ]
        self.accounts = {
            "tdv_v1": {"role": "DOI_TRUONG", "team_id": "V1"},
            "tdv_k1": {"role": "DOI_TRUONG", "team_id": "K1"},
            "tdv_k2": {"role": "DOI_TRUONG", "team_id": "K2"},
            "tdv_v2": {"role": "DOI_TRUONG", "team_id": "V2"},
            "tdv_v3": {"role": "DOI_TRUONG", "team_id": "V3"},
            "tdv_m1": {"role": "DOI_TRUONG", "team_id": "M1"},
            "admin": {"role": "ADMIN", "team_id": ""},
        }

    def test_project_filters_out_inactive_unauthorized_other_role_and_project(self):
        self.assertEqual(
            project_login_choices(self.teams, "DA880", self.accounts),
            ["Lê Thị Hoa", "Nguyễn Văn Bình", "Trần Mai Lan Anh"],
        )

    def test_no_project_or_account_cannot_suggest(self):
        self.assertEqual(project_login_choices(self.teams, None, self.accounts), [])
        self.assertEqual(project_login_choices(self.teams, "DA880", {}), [])

    def test_project_name_resolves_only_the_correct_team(self):
        username, reason = resolve_login_username(
            "Trần Mai Lan Anh", self.accounts, self.teams, project_id="DA880")
        self.assertEqual((username, reason), ("tdv_v1", "ok"))
        username, reason = resolve_login_username(
            "Trần Mai Lan Anh", self.accounts, self.teams, project_id="DA881")
        self.assertEqual((username, reason), (None, "missing"))

    def test_current_app_retains_signed_remember_and_admin_login(self):
        source = (Path(__file__).resolve().parents[1] / "preview_app.py").read_text(
            encoding="utf-8")
        ast.parse(source)
        self.assertIn('if not team_only:', source)
        self.assertIn("Ghi nhớ đăng nhập trên thiết bị này (30 ngày)", source)
        self.assertIn("issue_remember_token(", source)
        self.assertIn("project_login_choices(", source)


if __name__ == "__main__":
    unittest.main()
