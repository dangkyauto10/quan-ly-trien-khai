"""Regression tests for safe ADMIN correction of untouched allocations.

No Google Sheets client or production data is used by these tests.
"""
import copy
import unittest
from decimal import Decimal
from preview_allocation_adjust import prepare_quantity_corrections, allocation_batch_code


PROJECT = "DA880"
IDS = {name: 100 + i for i, name in enumerate(
    ("DM_CHUAN", "KHO_PHAN_BO", "VAN_CHUYEN", "LAP_DAT", "NHAT_KY_HE_THONG"))}


# Exact header order from the PREVIEW Sheets, including the line break in DM_CHUAN.
LIVE_HEADERS = {
    "DM_CHUAN": ["Mã đợt phân bổ", "Mã dự án", "SKU", "Tên hàng hóa", "ĐVT",
                 "SL \nphân bổ", "Mã điểm", "Tên địa điểm", "Trạng thái",
                 "Người lập", "Thời gian", "Ghi chú"],
    "KHO_PHAN_BO": ["Mã phân bổ", "Mã đợt", "Mã dự án", "Mã điểm", "SKU",
                     "Tên hàng hóa", "ĐVT", "SL phân bổ", "Thời gian phân bổ",
                     "Trạng thái", "Ghi chú"],
    "VAN_CHUYEN": ["Mã nhiệm vụ VC", "Mã phân bổ", "Mã dự án", "Mã điểm", "SKU",
                   "SL giao", "Mã đội VC", "Trạng thái", "Thời gian báo cáo",
                   "Link ảnh", "Link Maps", "Mã báo cáo", "SL thực tế", "Ghi chú"],
    "LAP_DAT": ["Mã nhiệm vụ LD", "Mã phân bổ", "Mã dự án", "Mã điểm", "SKU",
                "SL lắp", "Mã đội KTV", "Trạng thái", "Thời gian báo cáo",
                "Link ảnh", "Link Maps", "Mã báo cáo", "SL thực tế", "Ghi chú"],
}


def as_live_sheet_headers(sheets):
    for name, headers in LIVE_HEADERS.items():
        rebuilt = []
        for item in sheets[name]:
            source = dict(item)
            if name == "DM_CHUAN":
                source["SL \nphân bổ"] = source.pop("SL phân bổ")
            if name == "KHO_PHAN_BO":
                source["Mã đợt"] = source.pop("Mã đợt phân bổ")
            rebuilt.append({**{header: source.get(header, "") for header in headers},
                            "_row": source["_row"]})
        sheets[name] = rebuilt


def example(n=5, amount="13", imported="100"):
    batch = "PB-TEST-001"
    sheets = {name: [] for name in (
        "DM_CHUAN", "KHO_PHAN_BO", "VAN_CHUYEN", "LAP_DAT",
        "NHAP_KHO", "BAO_CAO_TRIEN_KHAI", "BAN_GIAO_TAP_KET")}
    sheets["NHAP_KHO"] = [{"Mã dự án": PROJECT, "SKU": "TB-04",
                             "Tên hàng hóa": "Thiết bị", "Đơn vị tính": "bộ",
                             "SL thực nhận": imported, "_row": 2}]
    changes = []
    for i in range(n):
        aid = f"{batch}-{i+1:05d}"
        site = f"DD-TEST-{i+1}"
        row = i + 2
        sheets["DM_CHUAN"].append({
            "Mã đợt phân bổ": batch, "Mã dự án": PROJECT,
            "SKU": "TB-04", "SL phân bổ": amount,
            "Mã điểm": site, "_row": row})
        sheets["KHO_PHAN_BO"].append({
            "Mã phân bổ": aid, "Mã đợt phân bổ": batch,
            "Mã dự án": PROJECT, "Mã điểm": site, "SKU": "TB-04",
            "SL phân bổ": amount, "Trạng thái": "Đã phân bổ", "_row": row})
        sheets["VAN_CHUYEN"].append({
            "Mã nhiệm vụ VC": "VC-" + aid, "Mã phân bổ": aid,
            "Mã dự án": PROJECT, "Mã điểm": site,
            "SKU": "TB-04", "SL giao": amount,
            "Mã đội VC": "DOI-01", "Trạng thái": "Chưa giao",
            "SL thực tế": "", "Thời gian": "", "_row": row})
        sheets["LAP_DAT"].append({
            "Mã nhiệm vụ LD": "LD-" + aid, "Mã phân bổ": aid,
            "Mã dự án": PROJECT, "Mã điểm": site,
            "SKU": "TB-04", "SL lắp": amount,
            "Mã đội KTV": "DOI-02", "Trạng thái": "Chưa lắp",
            "SL thực tế": "", "Thời gian": "", "_row": row})
        changes.append((aid, amount, "1"))
    as_live_sheet_headers(sheets)
    return sheets, changes


class QuantityCorrectionTests(unittest.TestCase):
    def plan(self, sheets, changes):
        return prepare_quantity_corrections(
            PROJECT, changes, sheets, IDS, "admin", "2026-10-26T12:30:00")

    def test_five_locations_13_to_1_releases_60(self):
        sheets, changes = example()
        before = copy.deepcopy(sheets)
        requests, delta = self.plan(sheets, changes)
        self.assertEqual(delta, {"TB-04": Decimal("-60")})
        self.assertEqual(len(requests), 21)  # 5 × 4 cells + one journal append
        self.assertEqual(sheets, before)      # planning never mutates data
        positions = {(req["updateCells"]["start"]["sheetId"],
                      req["updateCells"]["start"]["rowIndex"],
                      req["updateCells"]["start"]["columnIndex"])
                     for req in requests[:-1]}
        self.assertEqual(len(positions), 20)
        self.assertEqual({req["updateCells"]["rows"][0]["values"][0]
                          ["userEnteredValue"]["numberValue"]
                          for req in requests[:-1]}, {1.0})
        self.assertEqual({p[2] for p in positions}, {5, 7})
        self.assertEqual(len(requests[-1]["appendCells"]["rows"]), 5)
        self.assertEqual(requests[-1]["appendCells"]["sheetId"],
                         IDS["NHAT_KY_HE_THONG"])

    def test_real_and_legacy_batch_headers(self):
        sheets, _ = example(n=1)
        row = sheets["KHO_PHAN_BO"][0]
        self.assertEqual(allocation_batch_code(row), "PB-TEST-001")
        self.assertEqual(allocation_batch_code({"Mã đợt phân bổ": "PB-OLD"}), "PB-OLD")
        with self.assertRaises(ValueError):
            allocation_batch_code({"Mã đợt": "PB-1", "Mã đợt phân bổ": "PB-2"})

    def test_missing_or_ambiguous_quantity_header_rejected(self):
        sheets, changes = example(n=1)
        del sheets["DM_CHUAN"][0]["SL \nphân bổ"]
        with self.assertRaises(ValueError):
            self.plan(sheets, changes)
        sheets, changes = example(n=1)
        sheets["DM_CHUAN"][0]["SL phân bổ"] = "13"
        with self.assertRaises(ValueError):
            self.plan(sheets, changes)

    def test_changed_sheet_column_order_maps_correctly(self):
        sheets, changes = example(n=1)
        row = sheets["DM_CHUAN"][0]
        sheets["DM_CHUAN"][0] = {"SL \nphân bổ": row["SL \nphân bổ"],
                                **{key: value for key, value in row.items()
                                   if key != "SL \nphân bổ"}}
        requests, _ = self.plan(sheets, changes)
        self.assertEqual(requests[0]["updateCells"]["start"]["columnIndex"], 0)

    def test_started_transport_blocks_everything(self):
        sheets, changes = example(n=1)
        sheets["VAN_CHUYEN"][0]["Trạng thái"] = "Đã giao hàng"
        with self.assertRaises(ValueError):
            self.plan(sheets, changes)

    def test_started_installation_blocks_everything(self):
        sheets, changes = example(n=1)
        sheets["LAP_DAT"][0]["SL thực tế"] = "1"
        with self.assertRaises(ValueError):
            self.plan(sheets, changes)

    def test_report_or_hub_blocks_adjustment(self):
        for tab in ("BAO_CAO_TRIEN_KHAI", "BAN_GIAO_TAP_KET"):
            with self.subTest(tab=tab):
                sheets, changes = example(n=1)
                sheets[tab] = [{"Mã dự án": PROJECT, "Mã điểm": "DD-TEST-1"}]
                with self.assertRaises(ValueError):
                    self.plan(sheets, changes)

    def test_over_allocate_blocks(self):
        sheets, changes = example(n=1, amount="13", imported="13")
        with self.assertRaises(ValueError):
            self.plan(sheets, [(changes[0][0], "13", "14")])

    def test_stale_and_cross_project_do_not_change(self):
        sheets, changes = example(n=1)
        with self.assertRaises(ValueError):
            self.plan(sheets, [(changes[0][0], "12", "1")])
        with self.assertRaises(ValueError):
            prepare_quantity_corrections("DA999", changes, sheets, IDS,
                                         "admin", "2026-10-26T12:30:00")

    def test_inconsistent_linked_quantity_rejected(self):
        sheets, changes = example(n=1)
        sheets["DM_CHUAN"][0]["SL \nphân bổ"] = "99"
        with self.assertRaises(ValueError):
            self.plan(sheets, changes)

    def test_zero_quantity_rejected(self):
        sheets, changes = example(n=1)
        with self.assertRaises(ValueError):
            self.plan(sheets, [(changes[0][0], "13", "0")])

    def test_duplicate_allocation_rejected(self):
        sheets, changes = example(n=1)
        with self.assertRaises(ValueError):
            self.plan(sheets, changes + changes)


    def test_admin_input_starts_empty_and_site_names_visible(self):
        from pathlib import Path
        import ast
        app = Path(__file__).resolve().parents[1].joinpath("preview_app.py")
        tree = ast.parse(app.read_text(encoding="utf-8"))
        fn = next(n for n in tree.body
                  if isinstance(n, ast.FunctionDef)
                  and n.name == "adjust_allocated_quantities")
        widgets = [n for n in ast.walk(fn)
                   if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "number_input"]
        self.assertEqual(len(widgets), 1)
        arguments = {kw.arg: kw.value for kw in widgets[0].keywords}
        self.assertIsNone(ast.literal_eval(arguments["value"]))
        self.assertIsNotNone(arguments.get("placeholder"))
        source = ast.get_source_segment(app.read_text(encoding="utf-8"), fn)
        self.assertIn('if new_qty is None:', source)
        self.assertIn('"Tên đơn vị": point_names.get(', source)
        self.assertIn('"SL đang phân bổ": r.get(', source)

if __name__ == "__main__":
    unittest.main()
