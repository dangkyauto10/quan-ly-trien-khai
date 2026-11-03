"""Registration onboarding: home-screen setup is available without credentials."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class MobileHomeShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.source)

    def test_home_shortcut_is_instruction_not_auto_install(self):
        source=self.source
        self.assertIn('def home_screen_guide(expanded=False):',source)
        self.assertIn('Thêm vào Màn hình chính',source)
        self.assertIn('Cài đặt và tạo lối tắt',source)
        self.assertIn('Mở bằng trình duyệt',source)
        self.assertIn('Biểu tượng khi ghim lên iPhone/Android vẫn phụ thuộc',source)

    def test_registration_success_displays_expanded_guide(self):
        func=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef)
                  and n.name=="register")
        call_sites=[n for n in ast.walk(func) if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Name)
                    and n.func.id=="home_screen_guide"]
        self.assertEqual(len(call_sites),1)
        self.assertTrue(any(kw.arg=="expanded" and isinstance(kw.value,ast.Constant)
                            and kw.value.value is True
                            for kw in call_sites[0].keywords))

    def test_no_auto_auth_on_home_screen_setup(self):
        func=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef)
                  and n.name=="home_screen_guide")
        text=ast.get_source_segment(self.source,func)
        self.assertNotIn('valid_login(',text)
        self.assertNotIn('session_state["auth"]',text)
        self.assertNotIn('sheet(',text)
        self.assertNotIn('append(',text)

    def test_public_can_reopen_instructions(self):
        func=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef)
                  and n.name=="menu")
        calls=[n for n in ast.walk(func) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Name)
               and n.func.id=="home_screen_guide"]
        self.assertEqual(len(calls),1)

    def test_stable_preview_url_not_production(self):
        self.assertIn(
            '"https://quan-ly-trien-khai-qfzumkrq7escxbxpv9v9tr.streamlit.app"',
            self.source
        )


if __name__=="__main__":
    unittest.main()
