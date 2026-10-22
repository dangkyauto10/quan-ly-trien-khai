import io
import unittest
from openpyxl import Workbook
from decimal import Decimal
from preview_allocation_groups import (
    normalized, match_contract_locations,
    read_contract_locations_excel, preview_basket
)
from preview_bulk_allocation import build_plan, verify_plan, inventory_by_sku


PROJECT="DA-TEST01"
POINTS=[
    {"Mã dự án":PROJECT,"Mã điểm":f"DD-{i:03d}",
     "Tên xã/phường/đơn vị":f"Xã Kiểm Thử {i}",
     "Trạng thái":"Hoạt động"} for i in range(1,137)
]
ITEMS=[
    ("TB-01","Máy tính", "Bộ", "3000"),
    ("TB-02","Bản quyền", "Bản", "3000"),
    ("TB-03","Phần mềm", "Bản", "3000"),
    ("TB-04","Switch", "Chiếc", "400"),
    ("TB-05","Cáp mạng", "M", "50000")
]
RECEIPTS=[
    {"Mã dự án":PROJECT,"SKU":sku,"Tên hàng hóa":name,
     "Đơn vị tính":unit,"SL thực nhận":amount}
    for sku,name,unit,amount in ITEMS
]


class TenderAllocationGroupTests(unittest.TestCase):
    def test_121_locations_five_skus_quota_for_each_point(self):
        ids=[p["Mã điểm"] for p in POINTS[:121]]
        actual,errors=match_contract_locations(PROJECT,POINTS,ids)
        self.assertFalse(errors)
        self.assertEqual(len(actual),121)
        quotas={"TB-01":12,"TB-02":12,"TB-03":12,"TB-04":1,"TB-05":305}
        self.assertEqual(preview_basket(quotas,quotas,121),
            {"TB-01":Decimal(1452),"TB-02":Decimal(1452),
             "TB-03":Decimal(1452),"TB-04":Decimal(121),
             "TB-05":Decimal(36905)})
        inv,issues=inventory_by_sku(PROJECT,RECEIPTS,[])
        self.assertFalse(issues)
        plan=build_plan(POINTS[:121],list(quotas),quotas)
        problems,candidates,totals=verify_plan(
            PROJECT,plan,inv,[],POINTS,max_lines=3000)
        self.assertFalse(problems)
        self.assertEqual(len(candidates),605)
        self.assertEqual(totals["TB-05"],Decimal(36905))

    def test_15_exception_locations_different_basket(self):
        quotas={"TB-01":4, "TB-05":0}
        plan=build_plan(POINTS[121:136],list(quotas),quotas,
            {("DD-136","TB-01"):8})
        inv,_=inventory_by_sku(PROJECT,RECEIPTS,[])
        errors,candidates,totals=verify_plan(PROJECT,plan,inv,[],POINTS)
        self.assertFalse(errors)
        self.assertEqual(len(candidates),15)
        self.assertEqual(totals["TB-01"],Decimal(64))

    def test_search_by_code_or_name_and_accent_insensitive(self):
        result,problems=match_contract_locations(PROJECT,POINTS,
            ["xA Kiem Thu 1", "DD-002", "Xã Kiểm Thử 136"])
        self.assertEqual(result,["DD-001","DD-002","DD-136"])
        self.assertFalse(problems)

    def test_duplicates_block(self):
        result,errors=match_contract_locations(PROJECT,POINTS,
            ["DD-001","Xã Kiểm Thử 1"])
        self.assertEqual(result,["DD-001"])
        self.assertTrue(any("đã được chọn" in e for e in errors))

    def test_unknown_or_wrong_project_blocks(self):
        outside=[*POINTS,{"Mã dự án":"DA-OTHER","Mã điểm":"DD-OTHER",
                          "Tên xã/phường/đơn vị":"Xã Khác","Trạng thái":"Hoạt động"}]
        _,errors=match_contract_locations(PROJECT,outside,["DD-OTHER"])
        self.assertTrue(any("không tìm thấy" in e for e in errors))

    def test_ambiguous_name_never_guessed(self):
        same=POINTS[:2]
        same[0]["Tên xã/phường/đơn vị"]="Xã trùng"
        same[1]["Tên xã/phường/đơn vị"]="Xã trùng"
        _,errors=match_contract_locations(PROJECT,same,["Xã trùng"])
        self.assertTrue(any("trùng tên" in e for e in errors))

    def test_excel_lists_location_column(self):
        wb=Workbook()
        ws=wb.active
        ws.append(["Mã điểm", "Ghi chú"])
        ws.append(["DD-001","A"])
        ws.append(["DD-002","B"])
        b=io.BytesIO()
        wb.save(b)
        names=read_contract_locations_excel("places.xlsx",b.getvalue())
        self.assertEqual(names,["DD-001","DD-002"])

    def test_500_locations_five_items_under_safe_limit(self):
        pts=[{"Mã dự án":PROJECT,"Mã điểm":f"X-{i:03d}",
              "Tên xã/phường/đơn vị":f"Xã {i}",
              "Trạng thái":"Hoạt động"} for i in range(500)]
        inv,_=inventory_by_sku(PROJECT,RECEIPTS,[])
        plan=build_plan(pts,["TB-04"],{"TB-04":1})
        errors,rows,_=verify_plan(PROJECT,plan,inv,[],pts)
        self.assertFalse(errors)
        self.assertEqual(len(rows),500)


if __name__=="__main__":
    unittest.main()
