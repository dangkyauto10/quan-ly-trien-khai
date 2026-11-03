"""Approved TDV favicon and mobile masthead are deployed only to PREVIEW."""
import ast
import json
from pathlib import Path
import re
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]


class TDVIconTests(unittest.TestCase):
    def test_png_asset_is_valid_square_icon(self):
        p=ROOT/"assets"/"tdv_icon_144.png"
        data=p.read_bytes()
        self.assertEqual(data[:8],b"\x89PNG\r\n\x1a\n")
        w,h=struct.unpack(">II",data[16:24])
        self.assertEqual((w,h),(144,144))
        self.assertGreater(len(data),3000)

    def test_page_config_uses_tdv_favicon_not_old_emoji(self):
        content=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        tree=ast.parse(content)
        self.assertIn('page_icon=str(APP_ICON)',content)
        self.assertNotIn('page_icon="🚀"',content)
        self.assertIn('APP_ICON_DATA = base64.b64encode(APP_ICON.read_bytes())',content)
        self.assertIn('class="tdv-hero-icon" src="data:image/png;base64,{APP_ICON_DATA}"',content)
        page_config_calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call)
                           and isinstance(x.func,ast.Attribute)
                           and x.func.attr=="set_page_config"]
        self.assertEqual(len(page_config_calls),1)

    def test_mobile_manifest_uses_current_transparent_icon(self):
        app=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        manifest=json.loads((ROOT/"static"/"manifest.json").read_text(encoding="utf-8"))
        app_version=re.search(r'manifest\.json\?v=([0-9a-z]+)',app).group(1)
        icon=manifest["icons"][0]
        icon_version=re.search(r'\?v=([0-9a-z]+)',icon["src"]).group(1)
        self.assertEqual(app_version,icon_version)
        self.assertTrue((ROOT/"static"/"tdv_icon_144.png").is_file())
        self.assertEqual((ROOT/"static"/"tdv_icon_144.png").read_bytes(),
                         (ROOT/"assets"/"tdv_icon_144.png").read_bytes())

    def test_home_screen_guide_does_not_overpromise_native_icon(self):
        src=(ROOT/"preview_app.py").read_text(encoding="utf-8")
        self.assertIn("Biểu tượng khi ghim lên iPhone/Android vẫn phụ thuộc",src)
        self.assertIn("xóa lối tắt cũ, mở lại app sau khi PREVIEW cập nhật",src)
        self.assertIn("rồi ghim lại để kiểm tra",src)


if __name__=="__main__":
    unittest.main()
