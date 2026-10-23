import unittest
from preview_hub import hub_plan, received_by_site, signed_receipt_lines, ACCEPTED
from preview_handover import installer_handover, site_may_complete_installation
from preview_leadership import build_progress

PROJECT="DA880"
TEAM={"Mã dự án":PROJECT,"Mã đội":"KTV-01","Tên đội/đội trưởng":"Nguyễn Văn A",
      "Trạng thái":"Hoạt động","Loại nhiệm vụ":"KTV"}
PLACES=[{"Mã dự án":PROJECT,"Mã điểm":"P1","Tên xã/phường/đơn vị":"Xã A"},
        {"Mã dự án":PROJECT,"Mã điểm":"P2","Tên xã/phường/đơn vị":"Xã B"}]
LD=[{"Mã dự án":PROJECT,"Mã điểm":pid,"SKU":sku,
     "SL lắp":qty,"Mã đội KTV":"KTV-01","Trạng thái":"Chưa lắp",
     "Mã nhiệm vụ LD":f"LD-{pid}-{sku}"}
    for pid in ("P1","P2") for sku,qty in (("TB01","2"),("TB02","3"))]
ALLOC=[{"Mã dự án":PROJECT,"Mã điểm":r["Mã điểm"],"SKU":r["SKU"],
        "SL phân bổ":r["SL lắp"],"ĐVT":"Bộ","Tên hàng hóa":"Thiết bị"}
       for r in LD]
VC=[{"Mã dự án":PROJECT,"Mã điểm":r["Mã điểm"],"SKU":r["SKU"],
     "Trạng thái":"Chưa giao","SL thực tế":"","Mã nhiệm vụ VC":"VC-"+r["Mã nhiệm vụ LD"],
     "Mã đội VC":"VC01"} for r in LD]


def evidence():
    plan,totals=hub_plan(TEAM,["P1","P2"],LD,PLACES,ALLOC)
    rows=signed_receipt_lines(
        "BG-000001",TEAM,plan,"Đồng Văn / Yên Minh / Quản Bạ",
        "Kho nhận hợp đồng","Đồng Văn, Hà Giang (cũ)",
        "VC Nguyễn Văn B","BB-GIAO-001",
        "https://drive.google.com/file/d/abc/view","2026-10-23T09:00:00+07:00")
    keys=["Mã dòng","Mã biên bản hệ thống","Mã dự án","Mã đội KTV nhận",
          "Tên đội KTV nhận","Khu vực theo hợp đồng","Điểm tập kết",
          "Địa chỉ tập kết","Mã điểm","Tên địa điểm","SKU",
          "SL định mức điểm","SL KTV thực nhận","ĐVT","Tên đội VC giao",
          "Số biên bản giấy","Link ảnh biên bản ký","Thời điểm ghi nhận",
          "Trạng thái","Ghi chú"]
    return [dict(zip(keys,r)) for r in rows],totals


class HubPlanningTests(unittest.TestCase):
    def test_three_old_districts_can_share_one_delivery_hub(self):
        plan,totals=hub_plan(TEAM,["P1","P2"],LD,PLACES,ALLOC)
        self.assertEqual(len(plan),4)
        self.assertEqual(totals[("TB01","Bộ")],4)
        self.assertEqual(totals[("TB02","Bộ")],6)
        rows,_=evidence()
        self.assertEqual({x["Mã biên bản hệ thống"] for x in rows},{"BG-000001"})
        self.assertEqual({x["Điểm tập kết"] for x in rows},{"Kho nhận hợp đồng"})
        self.assertEqual({x["Mã điểm"] for x in rows},{"P1","P2"})
        self.assertEqual({x["Trạng thái"] for x in rows},{ACCEPTED})
        self.assertTrue(all(len(x)==20 for x in [list(row.values()) for row in rows]))

    def test_outside_contract_location_rejected(self):
        with self.assertRaises(ValueError):
            hub_plan(TEAM,["P3"],LD,PLACES,ALLOC)

    def test_wrong_team_role_rejected(self):
        with self.assertRaises(ValueError):
            hub_plan({**TEAM,"Loại nhiệm vụ":"VC"},["P1"],LD,PLACES,ALLOC)

    def test_duplicate_site_is_rejected(self):
        with self.assertRaises(ValueError):
            hub_plan(TEAM,["P1","P1"],LD,PLACES,ALLOC)

    def test_signature_photo_and_paper_are_required(self):
        plan,_=hub_plan(TEAM,["P1"],LD,PLACES,ALLOC)
        with self.assertRaises(ValueError):
            signed_receipt_lines("BG1",TEAM,plan,"Vùng cũ","Kho","Địa chỉ",
                                 "VC","Số BB","","2026-10-23")

    def test_only_signed_accepted_receipt_counted(self):
        rows,_=evidence()
        receipt=received_by_site(rows,PROJECT,TEAM["Mã đội"])
        self.assertEqual(receipt[(PROJECT,"P1","TB01")],2)
        self.assertEqual(receipt[(PROJECT,"P2","TB02")],3)
        self.assertFalse(received_by_site(rows,PROJECT,"OTHER"))
        rows[0]["Link ảnh biên bản ký"]=""
        rows[1]["Trạng thái"]="Chờ ký"
        receipt=received_by_site(rows,PROJECT,TEAM["Mã đội"])
        self.assertNotIn((PROJECT,"P1","TB01"),receipt)
        self.assertNotIn((PROJECT,"P1","TB02"),receipt)

    def test_ktv_sees_hub_stock_not_direct_site_delivery(self):
        rows,_=evidence()
        result=installer_handover("KTV-01",LD,VC,PLACES,rows)
        self.assertEqual(len(result),2)
        self.assertTrue(all(r["status"]=="Sẵn sàng lắp (tập kết)" for r in result))
        self.assertEqual(result[0]["details"][0]["delivered"],"0")
        self.assertTrue(all(int(x["hub_received"])>0 for r in result for x in r["details"]))
        self.assertTrue(site_may_complete_installation(
            PROJECT,"P1",LD,VC,rows))

    def test_ktv_cannot_install_if_signed_hub_short_for_site(self):
        rows,_=evidence()
        rows[0]["SL KTV thực nhận"]="1"
        result=installer_handover("KTV-01",LD,VC,PLACES,rows)
        self.assertEqual(next(r for r in result if r["point_id"]=="P1")["status"],
                         "Đã tập kết một phần")
        self.assertFalse(site_may_complete_installation(
            PROJECT,"P1",LD,VC,rows))

    def test_unknown_or_other_team_hub_does_not_authorize_install(self):
        rows,_=evidence()
        for row in rows:
            row["Mã đội KTV nhận"]="KTV-OTHER"
        self.assertFalse(site_may_complete_installation(
            PROJECT,"P1",LD,VC,rows))

    def test_direct_vc_and_hub_double_claim_needs_audit(self):
        rows,_=evidence()
        direct=[{**r,"Trạng thái":"Đã giao hàng","SL thực tế":r["SL giao"]}
                for r in VC if r["Mã điểm"]=="P1"] if False else [
                 {**r,"Trạng thái":"Đã giao hàng","SL thực tế":"2"}
                 if r["Mã điểm"]=="P1" and r["SKU"]=="TB01" else r for r in VC]
        result=installer_handover("KTV-01",LD,direct,PLACES,rows)
        self.assertEqual(next(r for r in result if r["point_id"]=="P1")["status"],
                         "Cần đối soát")

    def test_leadership_counts_hub_not_direct_vc(self):
        rows,_=evidence()
        project_list=[{"Mã dự án":PROJECT}]
        receipts=[{"Mã dự án":PROJECT,"SKU":"TB01","SL thực nhận":"4"},
                  {"Mã dự án":PROJECT,"SKU":"TB02","SL thực nhận":"6"}]
        progress=build_progress(PROJECT,project_list,PLACES,receipts,ALLOC,VC,
                                LD,[],[TEAM],rows)
        m=progress["metrics"]
        self.assertEqual(m["sites_delivered"],0)
        self.assertEqual(m["sites_at_hub"],2)
        self.assertEqual(m["sites_installed"],0)
        self.assertEqual(m["sites_ready_install"],2)
        installed=[{**r,"Trạng thái":"Đã lắp đặt","SL thực tế":r["SL lắp"]}
                   for r in LD]
        m=build_progress(PROJECT,project_list,PLACES,receipts,ALLOC,VC,
                         installed,[],[TEAM],rows)["metrics"]
        self.assertEqual(m["sites_installed"],2)
        self.assertEqual(m["sites_delivered"],0)


if __name__=="__main__":
    unittest.main()
