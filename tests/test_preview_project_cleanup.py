import unittest

from preview_project_cleanup import (
    ALL_TABS, OPERATIONAL_TABS, DELETE, RESET,
    make_cleanup_plan, cleanup_requests,
)


def sample_grids():
    sheets = {name: [["Mã dự án", "Mã", "Ghi chú"],
                     ["DA880", "own-1", "first"],
                     ["OTHER", "foreign", "must stay"],
                     ["DA880", "own-2", "second"]]
              for name in ALL_TABS}
    sheets["DANH_SACH_DU_AN"] = [
        ["Mã dự án", "Tên dự án"],
        ["DA880", "Demo 880"], ["OTHER", "Other"]]
    sheets["DANG_KY_THANH_VIEN"][0][0] = "Mã dự án đăng ký"
    sheets["DANG_KY_THANH_VIEN"][0][1] = "Mã đăng ký"
    sheets["DANH_SACH_DIEM"][0][1] = "Mã điểm"
    sheets["QUAN_LY_DOI"][0][1] = "Mã đội"
    sheets["NHAT_KY_HE_THONG"] = [
        ["Thời gian", "Tài khoản", "Vai trò", "Hành động",
         "Đối tượng", "Mã đối tượng", "Kết quả", "Chi tiết"],
        ["now", "admin", "ADMIN", "Duyệt DA880", "QUAN_LY_DOI",
         "own-1", "OK", ""],
        ["now", "admin", "ADMIN", "Duyệt OTHER", "QUAN_LY_DOI",
         "foreign", "OK", ""],
        ["now", "admin", "ADMIN", "Phân bổ", "KHO_PHAN_BO",
         "own-2", "OK", "DA880"]]
    return sheets


class CleanupTests(unittest.TestCase):
    def test_reset_preserves_project_and_sites(self):
        plan = make_cleanup_plan("DA880", RESET, sample_grids())
        self.assertEqual(set(plan["rows"]), set(OPERATIONAL_TABS) | {"NHAT_KY_HE_THONG"})
        self.assertEqual(plan["total"], len(OPERATIONAL_TABS) * 2 + 2)
        for tab, entries in plan["rows"].items():
            self.assertEqual([number for number, _ in entries], [2, 4])

    def test_delete_includes_master_and_site_catalog(self):
        plan = make_cleanup_plan("DA880", DELETE, sample_grids())
        self.assertEqual(set(plan["rows"]), set(ALL_TABS))
        self.assertEqual(plan["counts"]["DANH_SACH_DU_AN"], 1)
        self.assertEqual(plan["counts"]["DANH_SACH_DIEM"], 2)

    def test_untouched_other_project_across_all_sheets(self):
        grids = sample_grids()
        for mode in (RESET, DELETE):
            plan = make_cleanup_plan("DA880", mode, grids)
            reqs = cleanup_requests(plan, {tab: i for i, tab in enumerate(ALL_TABS, 1)})
            for req in reqs:
                cell_range = req["repeatCell"]["range"]
                self.assertNotIn(3 - 1, range(cell_range["startRowIndex"],
                                              cell_range["endRowIndex"]))
                self.assertGreaterEqual(cell_range["startRowIndex"], 1)
                self.assertEqual(req["repeatCell"]["fields"], "userEnteredValue,note")

    def test_reject_nonexistent_or_ambiguous_project(self):
        sheets = sample_grids()
        with self.assertRaises(ValueError):
            make_cleanup_plan("NOT-HERE", RESET, sheets)
        sheets["DANH_SACH_DU_AN"].append(["DA880", "Duplicate"])
        with self.assertRaises(ValueError):
            make_cleanup_plan("DA880", DELETE, sheets)

    def test_reject_missing_sheet_and_bad_header(self):
        sheets = sample_grids()
        del sheets["NHAP_KHO"]
        with self.assertRaisesRegex(ValueError, "NHAP_KHO"):
            make_cleanup_plan("DA880", RESET, sheets)
        sheets = sample_grids()
        sheets["DM_CHUAN"][0] = ["Unknown", "Mã", "Ghi chú"]
        with self.assertRaisesRegex(ValueError, "DM_CHUAN"):
            make_cleanup_plan("DA880", RESET, sheets)

    def test_change_detection_includes_modified_cell_and_mode(self):
        first = sample_grids()
        second = sample_grids()
        second["NHAP_KHO"][1][2] = "changed while preview open"
        self.assertNotEqual(
            make_cleanup_plan("DA880", RESET, first)["signature"],
            make_cleanup_plan("DA880", RESET, second)["signature"])
        self.assertNotEqual(
            make_cleanup_plan("DA880", RESET, first)["signature"],
            make_cleanup_plan("DA880", DELETE, first)["signature"])

    def test_group_contiguous_rows_into_one_request(self):
        sheets = sample_grids()
        sheets["NHAP_KHO"][2][0] = "DA880"
        plan = make_cleanup_plan("DA880", RESET, sheets)
        ids = {tab: i for i, tab in enumerate(ALL_TABS, 1)}
        reqs = cleanup_requests(plan, ids)
        stock = [r for r in reqs if r["repeatCell"]["range"]["sheetId"]
                 == ids["NHAP_KHO"]]
        self.assertEqual(len(stock), 1)
        self.assertEqual(stock[0]["repeatCell"]["range"]["startRowIndex"], 1)
        self.assertEqual(stock[0]["repeatCell"]["range"]["endRowIndex"], 4)


if __name__ == "__main__":
    unittest.main()
