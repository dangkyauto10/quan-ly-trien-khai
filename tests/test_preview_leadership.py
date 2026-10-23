import ast
from pathlib import Path
import unittest
from preview_leadership import build_progress


P="DA880"
PROJECTS=[{"Mã dự án":P}]
SITES=[{"Mã dự án":P,"Mã điểm":"P1","Tên xã/phường/đơn vị":"Xã A"},
       {"Mã dự án":P,"Mã điểm":"P2","Tên xã/phường/đơn vị":"Xã B"},
       {"Mã dự án":P,"Mã điểm":"P3","Tên xã/phường/đơn vị":"Xã C"}]
RECEIPTS=[{"Mã dự án":P,"SKU":"TB01","Tên hàng hóa":"Máy tính",
           "Đơn vị tính":"Bộ","SL thực nhận":"6"}]
ALLOC=[{"Mã dự án":P,"Mã điểm":"P1","SKU":"TB01",
        "Tên hàng hóa":"Máy tính","ĐVT":"Bộ","SL phân bổ":"2"},
       {"Mã dự án":P,"Mã điểm":"P2","SKU":"TB01",
        "Tên hàng hóa":"Máy tính","ĐVT":"Bộ","SL phân bổ":"2"}]
VC=[{"Mã dự án":P,"Mã điểm":"P1","SKU":"TB01",
     "Mã nhiệm vụ VC":"VC1","Mã đội VC":"VC-A","Trạng thái":"Chưa giao",
     "SL thực tế":""},
    {"Mã dự án":P,"Mã điểm":"P2","SKU":"TB01",
     "Mã nhiệm vụ VC":"VC2","Mã đội VC":"VC-B","Trạng thái":"Chưa giao",
     "SL thực tế":""}]
LD=[{"Mã dự án":P,"Mã điểm":"P1","SKU":"TB01",
     "Mã nhiệm vụ LD":"LD1","Mã đội KTV":"KTV-A","Trạng thái":"Chưa lắp",
     "SL thực tế":""},
    {"Mã dự án":P,"Mã điểm":"P2","SKU":"TB01",
     "Mã nhiệm vụ LD":"LD2","Mã đội KTV":"KTV-B","Trạng thái":"Chưa lắp",
     "SL thực tế":""}]
TEAMS=[{"Mã dự án":P,"Mã đội":"VC-A","Tên đội/đội trưởng":"Đội A"},
       {"Mã dự án":P,"Mã đội":"KTV-A","Tên đội/đội trưởng":"Đội lắp A"}]


def view(vc=None,ld=None,alloc=None,sites=None,reports=None,projects=None):
    return build_progress(P, projects or PROJECTS, sites or SITES,
                          RECEIPTS,alloc if alloc is not None else ALLOC,
                          vc if vc is not None else VC,
                          ld if ld is not None else LD,
                          reports if reports is not None else [],TEAMS)


class LeadershipProgressTests(unittest.TestCase):
    def test_allocation_not_equivalent_to_delivery(self):
        m=view()["metrics"]
        self.assertEqual(m["sites"],3)
        self.assertEqual(m["sites_allocated"],2)
        self.assertEqual(m["sites_delivered"],0)
        self.assertEqual(m["sites_installed"],0)

    def test_delivery_ready_install_but_not_installed(self):
        vc=[{**r,"Trạng thái":"Đã giao hàng","SL thực tế":"2"} for r in VC]
        result=view(vc=vc)
        self.assertEqual(result["metrics"]["sites_delivered"],2)
        self.assertEqual(result["metrics"]["sites_ready_install"],2)
        self.assertEqual(result["metrics"]["sites_installed"],0)
        self.assertEqual([r for r in result["sites"] if r["point_id"]=="P1"][0]["status"],
                         "Sẵn sàng lắp")

    def test_installation_only_counts_when_delivery_confirmed(self):
        ld=[{**r,"Trạng thái":"Đã lắp đặt","SL thực tế":"2"} for r in LD]
        m=view(ld=ld)["metrics"]
        self.assertEqual(m["sites_installed"],0)
        self.assertEqual(m["sites_delivered"],0)

    def test_full_delivery_and_installation(self):
        vc=[{**r,"Trạng thái":"Đã giao hàng","SL thực tế":"2"} for r in VC]
        ld=[{**r,"Trạng thái":"Đã lắp đặt","SL thực tế":"2"} for r in LD]
        m=view(vc=vc,ld=ld)["metrics"]
        self.assertEqual(m["sites_installed"],2)
        self.assertEqual(m["sites_delivered"],2)

    def test_closed_task_missing_actual_quantity_not_counted(self):
        vc=[{**r,"Trạng thái":"Đã giao hàng","SL thực tế":""} for r in VC]
        progress=view(vc=vc)
        self.assertEqual(progress["metrics"]["sites_delivered"],0)
        self.assertTrue(any("thiếu SL thực tế" in t for t in progress["anomalies"]))

    def test_partial_quantity_not_full_site(self):
        vc=[{**VC[0],"Trạng thái":"Đã giao hàng","SL thực tế":"1"},VC[1]]
        result=view(vc=vc)
        self.assertEqual(result["metrics"]["sites_delivered"],0)
        self.assertEqual(result["metrics"]["vc_tasks_done"],1)
        self.assertEqual(result["sites"][0]["status"],"Đang giao hàng")

    def test_multi_sku_site_requires_all_products(self):
        alloc=ALLOC+[{"Mã dự án":P,"Mã điểm":"P1","SKU":"TB02",
                      "SL phân bổ":"3","ĐVT":"Bản"}]
        vc=[{**VC[0],"Trạng thái":"Đã giao hàng","SL thực tế":"2"},VC[1],
            {"Mã dự án":P,"Mã điểm":"P1","SKU":"TB02",
             "Mã nhiệm vụ VC":"VC3","Mã đội VC":"VC-A",
             "Trạng thái":"Chưa giao","SL thực tế":""}]
        self.assertEqual(view(vc=vc,alloc=alloc)["metrics"]["sites_delivered"],0)

    def test_unsynced_report_counted_for_attention(self):
        reports=[{"Mã dự án":P,"Trạng thái đồng bộ":"Cần đối soát"},
                 {"Mã dự án":P,"Trạng thái đồng bộ":"Đã đồng bộ"}]
        self.assertEqual(view(reports=reports)["pending_report_count"],1)

    def test_another_project_not_leaking(self):
        others=[{"Mã dự án":"DA-OTHER","Mã điểm":"P20","SKU":"TB01",
                 "SL phân bổ":"50"}]
        self.assertEqual(view(alloc=ALLOC+others)["metrics"]["sites_allocated"],2)

    def test_no_phone_numbers_in_snapshot(self):
        t=view()
        self.assertNotIn("0912345678",str(t))
        self.assertEqual(t["sites"][0]["status"],"Chờ giao hàng")

    def test_read_only_menu_role_guards_in_code(self):
        # AST check catches accidental widening of dashboard permissions.
        file=Path(__file__).resolve().parents[1]/"preview_app.py"
        tree=ast.parse(file.read_text(encoding="utf-8"))
        funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="dashboard"]
        self.assertEqual(len(funcs),1)
        node=funcs[0]
        role_checks=[n for n in ast.walk(node) if isinstance(n,ast.Call)
                     and isinstance(n.func,ast.Name) and n.func.id=="require_role"]
        self.assertEqual(len(role_checks),1)
        self.assertEqual([arg.value for arg in role_checks[0].args],["ADMIN","LANH_DAO"])


if __name__=="__main__":
    unittest.main()
