"""Regression: clearing registration records never hides approved teams or logs them out."""
import ast
from pathlib import Path
import unittest


class RegistrationVsTeamDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        cls.tree=ast.parse(source)
        cls.source=source

    def func(self,name):
        node=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef)
                  and n.name==name)
        return ast.get_source_segment(self.source,node)

    def test_admin_shows_explicit_separate_sheets(self):
        source=self.func("teams_and_approval")
        self.assertIn('read_sheet("DANG_KY_THANH_VIEN")',source)
        self.assertIn('read_sheet("QUAN_LY_DOI")',source)
        self.assertIn('read_sheet("TAI_KHOAN_DOI")',source)
        self.assertIn('admin_team_refresh',source)
        self.assertIn('read_sheet.clear()',source)
        self.assertIn('Xóa đăng ký không tự xóa đội, tài khoản hay nhiệm vụ',source)

    def test_password_picker_uses_approved_team_table(self):
        source=self.func("provision_team_password")
        self.assertIn('teams=[t for t in read_sheet("QUAN_LY_DOI")',source)
        self.assertIn('Chọn đội trưởng đang có trong QUAN_LY_DOI',source)
        self.assertNotIn('teams=[t for t in read_sheet("DANG_KY_THANH_VIEN")',source)

    def test_no_cascade_deletes_on_registration_clear(self):
        source=self.func("teams_and_approval")
        self.assertNotIn('delete_rows(',source)
        self.assertNotIn('delete_sheet(',source)
        self.assertNotIn('clear_sheet(',source)


if __name__=="__main__":
    unittest.main()
