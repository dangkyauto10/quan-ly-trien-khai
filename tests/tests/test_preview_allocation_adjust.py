"""Regression tests for safe ADMIN correction of untouched allocations.

No Google Sheets client or production data is used by these tests.
"""
import copy
import unittest
from decimal import Decimal
from preview_allocation_adjust import prepare_quantity_corrections


PROJECT = "DA880"
IDS = {name: 100 + i for i, name in enumerate(
    ("DM_CHUAN", "KHO_PHAN_BO", "VAN_CHUYEN", "LAP_DAT", "NHAT_KY_HE_THONG"))}


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
        sheets["DM_CHUAN"][0]["SL phân bổ"] = "99"
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


if __name__ == "__main__":
    unittest.main()
