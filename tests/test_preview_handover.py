import ast
from pathlib import Path
import unittest

from preview_handover import installer_handover, site_may_complete_installation
from preview_team_access import resolve_login_username, friendly_account_name

PROJECT="DA880"
SITE="DD-X"
KTV="KTV-H"
def ld(sku, amount):
    return {"Mã dự án":PROJECT,"Mã điểm":SITE,"SKU":sku,
            "SL lắp":str(amount),"Mã đội KTV":KTV,
            "Trạng thái":"Chưa lắp","Mã nhiệm vụ LD":"LD-"+sku}
def vc(sku, amount, status="Chưa giao", actual=""):
    return {"Mã dự án":PROJECT,"Mã điểm":SITE,"SKU":sku,
            "SL giao":str(amount),"Trạng thái":status,
            "SL thực tế":str(actual)}
PLACES=[{"Mã dự án":PROJECT,"Mã điểm":SITE,
         "Tên xã/phường/đơn vị":"Xã Thử nghiệm"}]


class InstallerHandoverTests(unittest.TestCase):
    def test_unconfirmed_transport_not_ready(self):
        result=installer_handover(KTV,[ld("TB01",2)],
                                  [vc("TB01",2)],PLACES)
        self.assertEqual(result[0]["status"],"Chưa giao")
        self.assertFalse(site_may_complete_installation(
            PROJECT,SITE,[ld("TB01",2)],[vc("TB01",2)]))

    def test_all_skus_required_before_ready(self):
        lds=[ld("TB01",2),ld("TB02",3)]
        vrows=[vc("TB01",2,"Đã giao hàng",2),vc("TB02",3)]
        self.assertEqual(installer_handover(KTV,lds,vrows,PLACES)[0]["status"],
                         "Đã giao một phần")
        vrows[1]=vc("TB02",3,"Đã giao hàng",3)
        self.assertEqual(installer_handover(KTV,lds,vrows,PLACES)[0]["status"],
                         "Sẵn sàng lắp")
        self.assertTrue(site_may_complete_installation(PROJECT,SITE,lds,vrows))

    def test_partial_actual_quantity(self):
        vrows=[vc("TB01",2,"Đã giao hàng",1)]
        self.assertEqual(installer_handover(KTV,[ld("TB01",2)],vrows,PLACES)[0]["status"],
                         "Đã giao một phần")
        self.assertFalse(site_may_complete_installation(
            PROJECT,SITE,[ld("TB01",2)],vrows))

    def test_completed_without_real_quantity_requires_review(self):
        vrows=[vc("TB01",2,"Đã giao hàng","")]
        self.assertEqual(installer_handover(KTV,[ld("TB01",2)],vrows,PLACES)[0]["status"],
                         "Cần đối soát")

    def test_over_delivery_requires_review(self):
        vrows=[vc("TB01",2,"Đã giao hàng","3")]
        self.assertEqual(installer_handover(KTV,[ld("TB01",2)],vrows,PLACES)[0]["status"],
                         "Cần đối soát")

    def test_do_not_leak_other_team_sites(self):
        other=ld("TB02",3)
        other["Mã đội KTV"]="KTV-OTHER"
        other["Mã điểm"]="DD-Y"
        places=PLACES+[{"Mã dự án":PROJECT,"Mã điểm":"DD-Y",
                        "Tên xã/phường/đơn vị":"Xã Riêng"}]
        result=installer_handover(KTV,[ld("TB01",2),other],
                                  [vc("TB01",2),vc("TB02",3)],places)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["name"],"Xã Thử nghiệm")

    def test_unassigned_captain_cannot_view(self):
        self.assertEqual(installer_handover("",[ld("TB01",2)],
                                            [vc("TB01",2)],PLACES),[])

    def test_vc_only_does_not_get_ktv_board(self):
        self.assertEqual(installer_handover("VC-A",[],
                                            [vc("TB01",2)],PLACES),[])

    def test_installation_requires_evidence_even_if_closed(self):
        done={**ld("TB01",2),"Trạng thái":"Đã lắp đặt","SL thực tế":"2"}
        result=installer_handover(KTV,[done],[vc("TB01",2,"Đã giao hàng",2)],PLACES)
        self.assertEqual(result[0]["status"],"Đã lắp xong")

    def test_partial_installation_can_continue_after_full_delivery(self):
        task={**ld("TB01",2),"Trạng thái":"Đã lắp một phần",
              "SL thực tế":"1"}
        delivered=[vc("TB01",2,"Đã giao hàng",2)]
        state=installer_handover(KTV,[task],delivered,PLACES)[0]
        self.assertEqual(state["status"],"Đang lắp một phần")
        self.assertEqual(state["details"][0]["installed"],"1")
        self.assertTrue(site_may_complete_installation(
            PROJECT,SITE,[task],delivered))

    def test_source_requires_guard_at_final_submit(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8"))
        report=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="report")
        calls=[n for n in ast.walk(report) if isinstance(n,ast.Call) and
               isinstance(n.func,ast.Name) and n.func.id=="site_may_complete_installation"]
        self.assertGreaterEqual(len(calls),2)


class TeamNameLoginTests(unittest.TestCase):
    def test_name_credential_matches_internal_team(self):
        accounts={"user_1":{"role":"DOI_TRUONG","team_id":"KTV-H"},
                  "admin":{"role":"ADMIN"}}
        teams=[{"Mã đội":"KTV-H","Tên đội/đội trưởng":"Nguyễn Văn Huân",
                "Trạng thái":"Hoạt động"}]
        self.assertEqual(resolve_login_username("  Nguyễn  Văn Huân  ",
                         accounts,teams),("user_1","ok"))
        self.assertEqual(friendly_account_name(
            {"username":"user_1","role":"DOI_TRUONG","team_id":"KTV-H"},teams),
            "Nguyễn Văn Huân")

    def test_approved_but_uncredentialed_cannot_login(self):
        self.assertEqual(resolve_login_username(
            "Nguyễn Văn A",{},[{"Mã đội":"KTV-H",
                "Tên đội/đội trưởng":"Nguyễn Văn A",
                "Trạng thái":"Hoạt động"}]),(None,"missing"))

    def test_identical_names_are_ambiguous_even_if_one_no_account(self):
        accounts={"user_1":{"role":"DOI_TRUONG","team_id":"KTV-H"}}
        teams=[{"Mã đội":"KTV-H","Tên đội/đội trưởng":"Nguyễn Văn A",
                "Trạng thái":"Hoạt động"},
               {"Mã đội":"KTV-Z","Tên đội/đội trưởng":"Nguyễn Văn A",
                "Trạng thái":"Hoạt động"}]
        self.assertEqual(resolve_login_username("Nguyễn Văn A",accounts,teams),
                         (None,"ambiguous"))


if __name__=="__main__":
    unittest.main()
