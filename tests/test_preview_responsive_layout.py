"""Responsive PREVIEW shell without regressions to the field reporting UI."""
import ast
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]


class ResponsiveLayoutTests(unittest.TestCase):
    def source(self):
        return (ROOT/"preview_app.py").read_text(encoding="utf-8")

    def test_pc_uses_wide_streamlit_layout(self):
        src=self.source()
        tree=ast.parse(src)
        calls=[n for n in ast.walk(tree)
               if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute)
               and n.func.attr=="set_page_config"]
        self.assertEqual(len(calls),1)
        opts={k.arg:k.value for k in calls[0].keywords}
        self.assertEqual(opts["layout"].value,"wide")
        self.assertIn("max-width: 100% !important;",src)
        self.assertIn("width: 100% !important;",src)

    def test_mobile_breakpoint_and_approved_typography_preserved(self):
        src=self.source()
        self.assertIn("@media (max-width: 900px)",src)
        self.assertIn("@media (max-width: 600px)",src)
        self.assertIn("max-width: 720px !important;",src)
        self.assertIn(".tdv-hero-title",src)
        self.assertIn("font-size: 1.1rem !important;",src)

    def test_no_changes_to_camera_or_gps_verification_path(self):
        src=self.source()
        self.assertIn('st.camera_input(',src)
        self.assertIn('key=f"report_camera_{photo_key}"',src)
        self.assertIn('streamlit_geolocation()',src)
        self.assertIn('st.file_uploader(',src)


if __name__=="__main__":
    unittest.main()
