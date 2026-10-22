import io
import unittest
from openpyxl import Workbook
from preview_bulk_excel import parse_exception_excel


def makefile(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


class BulkExcelTests(unittest.TestCase):
    def test_import_exceptions_per_sku(self):
        contents=makefile([
            ["Mã điểm","Tên địa điểm","TB-01","TB-02"],
            ["DD-2","Xã B",5,0],
            ["DD-3","Xã C",10,None]
        ])
        overrides,points=parse_exception_excel("exceptions.xlsx",contents,
            ["DD-1","DD-2","DD-3"],["TB-01","TB-02"])
        self.assertEqual(points,["DD-2","DD-3"])
        self.assertEqual(overrides[("DD-2","TB-01")],5)
        self.assertEqual(overrides[("DD-2","TB-02")],0)
        self.assertNotIn(("DD-3","TB-02"),overrides)

    def test_disallow_unknown_location(self):
        contents=makefile([["Mã điểm","TB-01"],["DD-NOT-IN-PROJECT",1]])
        with self.assertRaises(ValueError):
            parse_exception_excel("exceptions.xlsx",contents,["DD-1"],["TB-01"])

    def test_disallow_repeat_location(self):
        contents=makefile([["Mã điểm","TB-01"],["DD-1",1],["DD-1",2]])
        with self.assertRaises(ValueError):
            parse_exception_excel("exceptions.xlsx",contents,["DD-1"],["TB-01"])

    def test_disallow_negative(self):
        contents=makefile([["Mã điểm","TB-01"],["DD-1",-2]])
        with self.assertRaises(ValueError):
            parse_exception_excel("exceptions.xlsx",contents,["DD-1"],["TB-01"])

    def test_requires_sku_header(self):
        contents=makefile([["Mã điểm","Unrelated"],["DD-1",2]])
        with self.assertRaises(ValueError):
            parse_exception_excel("exceptions.xlsx",contents,["DD-1"],["TB-01"])


if __name__=="__main__":
    unittest.main()
