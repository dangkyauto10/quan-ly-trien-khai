import unittest
from decimal import Decimal

from preview_bulk_allocation import (
    quantity, inventory_by_sku, build_plan, verify_plan, atomic_requests
)

PROJECT = "DA-TEST01"
POINTS = [
    {"Mã điểm":"DD-1","Mã dự án":PROJECT,"Tên xã/phường/đơn vị":"Phường A","Trạng thái":"Hoạt động"},
    {"Mã điểm":"DD-2","Mã dự án":PROJECT,"Tên xã/phường/đơn vị":"Xã B","Trạng thái":"Hoạt động"},
    {"Mã điểm":"DD-3","Mã dự án":PROJECT,"Tên xã/phường/đơn vị":"Xã C","Trạng thái":"Hoạt động"}
]
RECEIPTS = [
    {"Mã dự án":PROJECT,"SKU":"TB-01","Tên hàng hóa":"Máy tính","Đơn vị tính":"Bộ","SL thực nhận":"20"},
    {"Mã dự án":PROJECT,"SKU":"TB-01","Tên hàng hóa":"Máy tính","Đơn vị tính":"Bộ","SL thực nhận":"5"},
    {"Mã dự án":PROJECT,"SKU":"TB-02","Tên hàng hóa":"Cáp","Đơn vị tính":"M","SL thực nhận":"15"}
]
IDS = {k:i for i,k in enumerate(
    ["DM_CHUAN","KHO_PHAN_BO","VAN_CHUYEN","LAP_DAT","TIEN_DO",
     "NHAT_KY_HE_THONG"],1)}


class MultiSkuAllocationTests(unittest.TestCase):
    def stock(self):
        return inventory_by_sku(PROJECT,RECEIPTS,[])[0]

    def test_multiple_sku_and_receipts(self):
        inv, problems=inventory_by_sku(PROJECT,RECEIPTS,[])
        self.assertEqual(problems,[])
        self.assertEqual(inv["TB-01"]["remaining"],Decimal("25"))
        self.assertEqual(inv["TB-02"]["remaining"],Decimal("15"))

    def test_general_quota_and_exception_per_sku(self):
        plan=build_plan(POINTS,["TB-01","TB-02"],{"TB-01":2,"TB-02":1},
                        {("DD-3","TB-01"):5,("DD-3","TB-02"):0})
        self.assertEqual(plan[0]["quantities"],{"TB-01":2,"TB-02":1})
        self.assertEqual(plan[2]["quantities"],{"TB-01":5,"TB-02":0})
        errors,rows,sums=verify_plan(PROJECT,plan,self.stock(),[],POINTS)
        self.assertFalse(errors)
        self.assertEqual(len(rows),5)
        self.assertEqual(sums["TB-01"],Decimal("9"))
        self.assertEqual(sums["TB-02"],Decimal("2"))

    def test_stock_shortage_blocks(self):
        plan=build_plan(POINTS,["TB-01"],{"TB-01":10})
        errors,_,_=verify_plan(PROJECT,plan,self.stock(),[],POINTS)
        self.assertTrue(any("tồn khả dụng" in s for s in errors))

    def test_prior_pair_blocks_repeated_allocation(self):
        plan=build_plan([POINTS[0]],["TB-01"],{"TB-01":1})
        prior=[{"Mã dự án":PROJECT,"Mã điểm":"DD-1","SKU":"TB-01","SL phân bổ":"1"}]
        errors,_,_=verify_plan(PROJECT,plan,self.stock(),prior,POINTS)
        self.assertTrue(any("Đã phân bổ trước" in x for x in errors))

    def test_unassigned_zero_not_emitted(self):
        plan=build_plan(POINTS,["TB-01"],{"TB-01":0},
                        {("DD-1","TB-01"):1})
        errors, rows,_=verify_plan(PROJECT,plan,self.stock(),[],POINTS)
        self.assertFalse(errors)
        self.assertEqual(len(rows),1)

    def test_reject_non_finite_and_over_precision(self):
        for n in ("nan","Infinity","-1","0.0001"):
            with self.subTest(n=n),self.assertRaises(ValueError):
                quantity(n)

    def test_reject_duplicate_points(self):
        p=build_plan([POINTS[0],POINTS[0]],["TB-01"],{"TB-01":1})
        errors,_,_=verify_plan(PROJECT,p,self.stock(),[],POINTS)
        self.assertTrue(any("Trùng trong phương án" in x for x in errors))

    def test_reject_unknown_point(self):
        other={"Mã điểm":"DD-999","Tên xã/phường/đơn vị":"X","Mã dự án":"OTHER"}
        p=build_plan([other],["TB-01"],{"TB-01":1})
        errors,_,_=verify_plan(PROJECT,p,self.stock(),[],POINTS)
        self.assertTrue(any("không thuộc dự án" in x for x in errors))

    def test_multi_tab_atomic_batch_integrity(self):
        inv=self.stock()
        req=atomic_requests(
            IDS,[("DD-1","TB-01",Decimal("2")),("DD-2","TB-02",Decimal("1"))],
            "PB-TEST",PROJECT,inv,{"DD-1":"Phường A","DD-2":"Xã B"},
            "admin_preview","2026-10-22T12:00:00+07:00",
            {"VAN_CHUYEN":[],"LAP_DAT":[]},[])
        batch={entry["appendCells"]["sheetId"]:entry["appendCells"]
               for entry in req if "appendCells" in entry}
        self.assertEqual(len(batch[IDS["KHO_PHAN_BO"]]["rows"]),2)
        self.assertEqual(len(batch[IDS["VAN_CHUYEN"]]["rows"]),2)
        self.assertEqual(len(batch[IDS["LAP_DAT"]]["rows"]),2)
        self.assertEqual(len(batch[IDS["DM_CHUAN"]]["rows"]),2)
        self.assertEqual(len(batch[IDS["TIEN_DO"]]["rows"]),2)
        self.assertEqual(len(batch[IDS["NHAT_KY_HE_THONG"]]["rows"]),1)
        # Every allocation/task must reference same deterministic batch+line id.
        kpb=batch[IDS["KHO_PHAN_BO"]]["rows"][0]["values"][0]["userEnteredValue"]["stringValue"]
        vc=batch[IDS["VAN_CHUYEN"]]["rows"][0]["values"][1]["userEnteredValue"]["stringValue"]
        ld=batch[IDS["LAP_DAT"]]["rows"][0]["values"][1]["userEnteredValue"]["stringValue"]
        self.assertEqual(kpb,vc)
        self.assertEqual(kpb,ld)

    def test_progress_updates_current_point(self):
        prior=[{"Mã dự án":PROJECT,"Mã điểm":"DD-1","_row":2}]
        tasks={"VAN_CHUYEN":[{"Mã dự án":PROJECT,"Mã điểm":"DD-1",
                              "Trạng thái":"Đã giao hàng"}],
               "LAP_DAT":[{"Mã dự án":PROJECT,"Mã điểm":"DD-1",
                            "Trạng thái":"Chưa lắp"}]}
        q=atomic_requests(IDS,[("DD-1","TB-02",Decimal("1"))],"PB-TEST",
            PROJECT,self.stock(),{"DD-1":"Phường A"},"admin","date",tasks,prior)
        updates=[r for r in q if "updateCells" in r]
        self.assertEqual(len(updates),1)
        value=updates[0]["updateCells"]["rows"][0]["values"][3]["userEnteredValue"]["numberValue"]
        self.assertEqual(value,2)


if __name__ == "__main__":
    unittest.main()
