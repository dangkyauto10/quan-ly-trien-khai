"""Public guide must be accessible without login and safely simulate field work."""
import ast
from pathlib import Path
import unittest

from preview_user_guide import GUIDE_URL, TOPICS, READY_EXAMPLES, can_demo_install


ROOT=Path(__file__).resolve().parents[1]


class PublicGuideTests(unittest.TestCase):
    def test_route_is_bookmarkable_preview_only(self):
        self.assertEqual(
            GUIDE_URL,
            "https://quan-ly-trien-khai-qfzumkrq7escxbxpv9v9tr.streamlit.app/?guide=1"
        )

    def test_steps_cover_actual_users(self):
        joined=" ".join(TOPICS)
        for text in ("Đăng ký", "Đăng nhập", "VC", "KTV", "tập kết",
                     "Lãnh đạo", "Thực hành"):
            self.assertIn(text,joined)

    def test_simulation_requires_received_goods_photos_gps(self):
        for label,ready in READY_EXAMPLES.items():
            self.assertEqual(can_demo_install(label,True,True),ready)
            self.assertFalse(can_demo_install(label,False,True))
            self.assertFalse(can_demo_install(label,True,False))

    def test_no_auth_or_spreadsheet_data_access_inside_guide(self):
        source=(ROOT/"preview_user_guide.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        render=next(n for n in tree.body
                    if isinstance(n,ast.FunctionDef) and n.name=="render_guide")
        calls=[n for n in ast.walk(render) if isinstance(n,ast.Call)]
        restricted={"read_sheet","sheet","append","audit","valid_login",
                    "images_to_drive","client","get_all_values"}
        self.assertTrue(restricted.isdisjoint({
            n.func.id for n in calls if isinstance(n.func,ast.Name)}))
        self.assertNotIn("st.secrets",source)
        self.assertNotIn("st.session_state[\"auth\"]",source)

    def test_main_checks_help_before_role_based_menu(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        main=next(n for n in tree.body
                  if isinstance(n,ast.FunctionDef) and n.name=="main")
        body=ast.get_source_segment(source,main)
        self.assertLess(body.index('st.query_params.get("guide")'),
                        body.index("view=menu()"))
        self.assertIn("render_guide()",body)
        self.assertIn('st.query_params["guide"] = "1"',body)
        self.assertIn("📖 Hướng dẫn sử dụng",body)

    def test_successful_registration_links_guide(self):
        source=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        reg=source[source.index("def register("):source.index("\ndef ",source.index("def register(")+1)]
        self.assertIn("XEM HƯỚNG DẪN & THỰC HÀNH THỬ",reg)
        self.assertIn("GUIDE_URL",reg)
        self.assertIn("home_screen_guide(expanded=True)",reg)


if __name__=="__main__":
    unittest.main()
