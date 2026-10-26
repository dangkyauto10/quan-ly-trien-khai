import ast
from pathlib import Path
import unittest
from preview_report_commit import (atomic_report_requests, pending_quantity,
                                   allocated_report_item)


IDS={"BAO_CAO_TRIEN_KHAI":1,"VAN_CHUYEN":2,"LAP_DAT":3,
     "TIEN_DO":4,"NHAT_KY_HE_THONG":5}
VC={"Mã nhiệm vụ VC":"VC-A","Mã dự án":"DA880","Mã điểm":"X-01",
    "Mã đội VC":"VC-1","SKU":"SKU-A","SL giao":"10",
    "SL thực tế":"","Trạng thái":"Chưa giao","_row":4}
LD={"Mã nhiệm vụ LD":"LD-A","Mã dự án":"DA880","Mã điểm":"X-01",
    "Mã đội KTV":"KTV-1","SKU":"SKU-A","SL lắp":"10",
    "SL thực tế":"","Trạng thái":"Chưa lắp","_row":5}
PROGRESS={"Mã dự án":"DA880","Mã điểm":"X-01","_row":8}


def request(row, amounts, mode="Đã giao hàng", **changes):
    options=dict(sheet_ids=IDS,rid="BC-ONE",stamp="24/10/2026 08:30",
                 actor="captain",role="DOI_TRUONG",team_id="VC-1",
                 project="DA880",point="X-01",mode=mode,
                 live_rows=[row],increments=amounts,
                 photo_urls=["https://drive.google.com/photo"],
                 maps_url="https://maps.google.com",latitude=None,
                 longitude=None,all_vc=[VC],all_ld=[LD],
                 progress=[PROGRESS],place_name="Địa điểm thử nghiệm")
    options.update(changes)
    return atomic_report_requests(**options)


class ReportAtomicTests(unittest.TestCase):
    def test_zero_quantity_cannot_be_reported_as_complete(self):
        self.assertEqual(pending_quantity(VC,"Đã giao hàng"),10)
        with self.assertRaisesRegex(ValueError,"lớn hơn 0"):
            request(VC,{"VC-A":0})

    def test_full_allocated_quantity_completes_transport(self):
        full=pending_quantity(VC,"Đã giao hàng")
        requests,states=request(VC,{"VC-A":full})
        self.assertEqual(states["VC-A"],"Đã giao hàng")
        self.assertEqual(requests[1]["updateCells"]["rows"][0]
                         ["values"][5]["userEnteredValue"],{"numberValue":10})

    def test_display_reads_exact_site_allocation_and_product_name(self):
        allocation={"Mã dự án":"DA880","Mã điểm":"X-01",
                    "SKU":"SKU-A","Tên hàng hóa":"Máy tính để bàn",
                    "ĐVT":"Bộ","SL phân bổ":"10"}
        line=allocated_report_item(VC,[allocation],"Đã giao hàng")
        self.assertEqual(line["name"],"Máy tính để bàn")
        self.assertEqual(line["unit"],"Bộ")
        self.assertEqual(line["allocated"],10)
        self.assertEqual(line["remaining"],10)
        self.assertEqual(line["already"],0)

    def test_display_rejects_wrong_site_duplicate_or_mismatched_quota(self):
        allocation={"Mã dự án":"DA880","Mã điểm":"X-01",
                    "SKU":"SKU-A","Tên hàng":"Máy tính để bàn",
                    "Đơn vị tính":"Bộ","SL phân bổ":"10"}
        with self.assertRaisesRegex(ValueError,"Thiếu hoặc trùng"):
            allocated_report_item(VC,[{**allocation,"Mã điểm":"X-02"}],
                                  "Đã giao hàng")
        with self.assertRaisesRegex(ValueError,"Thiếu hoặc trùng"):
            allocated_report_item(VC,[allocation,allocation],"Đã giao hàng")
        with self.assertRaisesRegex(ValueError,"không khớp"):
            allocated_report_item(VC,[{**allocation,"SL phân bổ":"2"}],
                                  "Đã giao hàng")

    def test_staff_report_shows_descriptions_not_internal_sku_codes(self):
        source=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        report=next(node for node in ast.parse(source).body
                    if isinstance(node,ast.FunctionDef) and node.name=="report")
        snippet=ast.get_source_segment(source,report)
        self.assertIn('site_allocations=[row for row in read_sheet("KHO_PHAN_BO")',snippet)
        self.assertIn('item=allocated_report_item(r,site_allocations,mode)',snippet)
        self.assertIn('"Thiết bị":item["name"]',snippet)
        self.assertIn('st.dataframe(sku_display,hide_index=True,use_container_width=True)',snippet)
        self.assertNotIn("st.write(f\"**{r['SKU']}**",snippet)

    def test_report_ui_shows_allocated_quantities_without_manual_inputs(self):
        source=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        report=next(node for node in ast.parse(source).body
                    if isinstance(node,ast.FunctionDef) and node.name=="report")
        snippet=ast.get_source_segment(source,report)
        self.assertIn("increments[r[id_key]]=remaining",snippet)
        self.assertNotIn("st.number_input(",snippet)
        self.assertIn('require_gps = mode!="Đã giao hàng"',snippet)
        self.assertIn('eligible=bool(photos)',snippet)
        self.assertLess(snippet.index('if not eligible:'),
                        snippet.index('if st.button("✅ GỬI BÁO CÁO"'))

    def test_report_camera_and_searchable_evidence_metadata(self):
        source=(Path(__file__).resolve().parents[1]/"preview_app.py").read_text(encoding="utf-8")
        funcs={n.name:n for n in ast.parse(source).body
               if isinstance(n,ast.FunctionDef)}
        report=ast.get_source_segment(source,funcs["report"])
        save=ast.get_source_segment(source,funcs["images_to_drive"])
        self.assertIn('st.camera_input(',report)
        self.assertIn('key=f"report_camera_{photo_key}"',report)
        self.assertIn('photos=([captured] if captured is not None else [])+list(uploaded or [])',report)
        self.assertIn('submitted_at=now()',report)
        self.assertIn('sheets,rid,submitted_at,',report)
        self.assertIn('urls=images_to_drive(',report)
        for detail in ('safe(project_id)','safe(point_id)','stamp','photo_prefix',
                       'Thời điểm gửi:','Mã báo cáo:','"description":description'):
            self.assertIn(detail,save)

    def test_partial_transport_is_not_marked_delivered(self):
        requests,states=request(VC,{"VC-A":3})
        self.assertEqual(states,{"VC-A":"Đã giao một phần"})
        self.assertEqual(len(requests),4)
        update=requests[1]["updateCells"]
        self.assertEqual(update["start"],{"sheetId":2,"rowIndex":3,
                                           "columnIndex":7})
        self.assertEqual(update["rows"][0]["values"][0]["userEnteredValue"],
                         {"stringValue":"Đã giao một phần"})
        self.assertEqual(update["rows"][0]["values"][5]["userEnteredValue"],
                         {"numberValue":3})
        report=requests[0]["appendCells"]["rows"][0]["values"]
        self.assertEqual(report[7]["userEnteredValue"],{"stringValue":"SKU-A:3"})
        self.assertEqual(report[5]["userEnteredValue"],
                         {"stringValue":"Đã giao một phần"})
        self.assertEqual(report[13]["userEnteredValue"],{"stringValue":"Đã đồng bộ"})
        progress=requests[2]["updateCells"]["rows"][0]["values"]
        self.assertEqual(progress[7]["userEnteredValue"],
                         {"stringValue":"Đang thực hiện"})
        self.assertEqual(requests[-1]["appendCells"]["sheetId"],5)
        self.assertEqual(set(IDS.values()),{1,2,3,4,5})

    def test_partial_repeated_only_adds_entered_increment(self):
        partly={**VC,"SL thực tế":"3","Trạng thái":"Đã giao một phần"}
        self.assertEqual(pending_quantity(partly,"Đã giao hàng"),7)
        requests,states=request(partly,{"VC-A":7})
        self.assertEqual(states["VC-A"],"Đã giao hàng")
        actual=requests[1]["updateCells"]["rows"][0]["values"][5]
        self.assertEqual(actual["userEnteredValue"],{"numberValue":10})
        with self.assertRaisesRegex(ValueError,"vượt"):
            request(partly,{"VC-A":8})

    def test_report_rejects_wrong_team_or_project(self):
        with self.assertRaisesRegex(ValueError,"không thuộc"):
            request(VC,{"VC-A":1},team_id="VC-OTHER")
        with self.assertRaisesRegex(ValueError,"không thuộc"):
            request(VC,{"VC-A":1},project="OTHER")

    def test_duplicate_id_and_missing_photo_rejected(self):
        with self.assertRaisesRegex(ValueError,"Trùng mã"):
            request(VC,{"VC-A":1},existing_report_ids=["BC-ONE"])
        with self.assertRaisesRegex(ValueError,"thiếu ảnh"):
            request(VC,{"VC-A":1},photo_urls=[])

    def test_installation_requires_real_gps_and_does_not_complete_partial(self):
        with self.assertRaisesRegex(ValueError,"GPS"):
            request(LD,{"LD-A":2},mode="Đã lắp đặt",team_id="KTV-1")
        reqs,states=request(LD,{"LD-A":2},mode="Đã lắp đặt",
                            team_id="KTV-1",latitude=20.1,longitude=105.2)
        self.assertEqual(states["LD-A"],"Đã lắp một phần")
        self.assertEqual(reqs[1]["updateCells"]["start"]["sheetId"],3)

    def test_ktv_full_report_completes_site_without_vc_delivery(self):
        reqs,changes=request(LD,{"LD-A":10},mode="Đã lắp đặt",
                             team_id="KTV-1",latitude=20.1,longitude=105.2)
        self.assertEqual(changes["LD-A"],"Đã lắp đặt")
        progress=reqs[-2]["updateCells"]["rows"][0]["values"]
        self.assertEqual(progress[7]["userEnteredValue"],
                         {"stringValue":"Hoàn thành"})
        self.assertEqual(progress[4]["userEnteredValue"],{"numberValue":0})
        self.assertEqual(progress[6]["userEnteredValue"],{"numberValue":1})

    def test_ktv_partial_does_not_complete_site(self):
        reqs,_=request(LD,{"LD-A":3},mode="Đã lắp đặt",
                       team_id="KTV-1",latitude=20.1,longitude=105.2)
        progress=reqs[-2]["updateCells"]["rows"][0]["values"]
        self.assertEqual(progress[7]["userEnteredValue"],
                         {"stringValue":"Đang thực hiện"})
        self.assertEqual(progress[6]["userEnteredValue"],{"numberValue":0})

    def test_vc_full_without_ktv_report_is_not_site_completion(self):
        reqs,_=request(VC,{"VC-A":10})
        progress=reqs[-2]["updateCells"]["rows"][0]["values"]
        self.assertEqual(progress[7]["userEnteredValue"],
                         {"stringValue":"Đang thực hiện"})

    def test_inconsistent_legacy_quantity_fails_closed(self):
        wrong={**VC,"SL thực tế":"5","Trạng thái":"Chưa giao"}
        with self.assertRaisesRegex(ValueError,"cần đối soát"):
            request(wrong,{"VC-A":1})


if __name__=="__main__":
    unittest.main()
