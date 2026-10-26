"""Guards for compact mobile report layout and safe image submission."""
from pathlib import Path
import ast
import unittest


APP = Path(__file__).resolve().parents[1] / "preview_app.py"
SOURCE = APP.read_text(encoding="utf-8")
REPORT = SOURCE.split("def report():", 1)[1].split("def dashboard():", 1)[0]


class PreviewMobileReportTests(unittest.TestCase):
    def test_app_compiles(self):
        ast.parse(SOURCE)

    def test_sku_summary_is_compact_and_preserves_counts(self):
        # All SKU rows now live under ONE site header/table on PC and phone.
        self.assertIn('sku_display=[]', REPORT)
        self.assertIn('sku_display.append({', REPORT)
        self.assertIn('"Thiết bị":item["name"]', REPORT)
        self.assertIn('st.dataframe(sku_display,hide_index=True,use_container_width=True)', REPORT)
        self.assertIn('Mã điểm: {chosen[1]}', REPORT)
        self.assertIn('Đã trừ', REPORT.replace('đã trừ', 'Đã trừ'))
        self.assertNotIn("st.write(f\"Đơn vị tính:", REPORT)
        self.assertEqual(REPORT.count("increments[r[id_key]]=remaining"), 1)

    def test_missing_drive_folder_is_checked_before_send(self):
        first = REPORT.index('if not str(st.secrets.get("photos_folder_id", "")).strip():')
        send = REPORT.index('if st.button("✅ GỬI BÁO CÁO"')
        self.assertLess(first, send)
        self.assertIn("Chưa cấu hình thư mục lưu ảnh PREVIEW", REPORT)

    def test_ambiguous_commit_is_not_retried(self):
        self.assertIn('phase="lưu ảnh Drive"', REPORT)
        self.assertIn('phase="đối soát dữ liệu sau tải ảnh"', REPORT)
        self.assertIn('phase="ghi đồng bộ Google Sheets"', REPORT)
        self.assertIn('if phase=="ghi đồng bộ Google Sheets":', REPORT)
        self.assertIn("_report_attempt_pending", REPORT)
        self.assertIn("KHÔNG bấm lại", REPORT)


if __name__ == "__main__":
    unittest.main()
