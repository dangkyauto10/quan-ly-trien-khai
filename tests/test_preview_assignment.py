import unittest
from preview_assignment import (
    assignment_rows, assignment_batch_requests,
    eligible_site_tasks, site_assignment_plan, compact_site_assignment_requests,
    allowed_modes
)

TASKS=[
    {"_row":2,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
     "Mã nhiệm vụ VC":"VC-1","SKU":"TB-TEST01","Mã đội VC":"",
     "Trạng thái":"Chưa giao","SL giao":"1"},
    {"_row":3,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
     "Mã nhiệm vụ VC":"VC-2","SKU":"TB-TEST02","Mã đội VC":"",
     "Trạng thái":"Chưa giao","SL giao":"4"},
    {"_row":4,"Mã dự án":"DA-TEST01","Mã điểm":"DD-OTHER",
     "Mã nhiệm vụ VC":"VC-3","SKU":"TB-TEST01","Mã đội VC":"",
     "Trạng thái":"Chưa giao","SL giao":"2"},
    {"_row":5,"Mã dự án":"DA-OTHER","Mã điểm":"DD-TEST-127",
     "Mã nhiệm vụ VC":"VC-4","SKU":"TB-TEST01","Mã đội VC":"",
     "Trạng thái":"Chưa giao","SL giao":"3"}
]
TEAM={"Mã đội":"VC-TEST","Mã dự án":"DA-TEST01","Loại nhiệm vụ":"VC",
      "Trạng thái":"Hoạt động"}

def select(rows,team=TEAM,group=True):
    return assignment_rows(rows,rows[0],team,"Mã nhiệm vụ VC","Mã đội VC",
                           ("VC","VC+KTV"),"Chưa giao",group)

class AssignmentTests(unittest.TestCase):
    def test_one_click_all_sku_same_point_only(self):
        rows=select(TASKS)
        self.assertEqual([r["Mã nhiệm vụ VC"] for r in rows],["VC-1","VC-2"])
        batch=assignment_batch_requests(123,rows,"VC-TEST")
        self.assertEqual(len(batch),2)
        self.assertEqual([x["updateCells"]["start"]["rowIndex"] for x in batch],[1,2])
        self.assertTrue(all(x["updateCells"]["start"]["columnIndex"]==6 for x in batch))
    def test_single_sku_optional(self):
        self.assertEqual(len(select(TASKS,group=False)),1)
    def test_other_project_team_not_allowed(self):
        with self.assertRaises(ValueError):
            select(TASKS,dict(TEAM,**{"Mã dự án":"DA-OTHER"}))
    def test_other_specialty_not_allowed(self):
        with self.assertRaises(ValueError):
            select(TASKS,dict(TEAM,**{"Loại nhiệm vụ":"KTV"}))
    def test_reject_already_assigned_seed(self):
        tasks=[dict(TASKS[0],**{"Mã đội VC":"VC-OLD"})]+TASKS[1:]
        with self.assertRaises(ValueError):
            select(tasks)
    def test_skip_other_assigned_task(self):
        tasks=[TASKS[0],dict(TASKS[1],**{"Mã đội VC":"VC-OTHER"})]+TASKS[2:]
        self.assertEqual([x["Mã nhiệm vụ VC"] for x in select(tasks)],["VC-1"])
    def test_reject_duplicate_task_ids(self):
        tasks=[TASKS[0],dict(TASKS[1],**{"Mã nhiệm vụ VC":"VC-1"})]
        with self.assertRaises(ValueError):
            select(tasks)


LOCATIONS=[
    {"Mã điểm":"DD-TEST-127","Mã dự án":"DA-TEST01",
     "Tên xã/phường/đơn vị":"Ban Tổ chức Tỉnh ủy","Trạng thái":"Hoạt động"},
    {"Mã điểm":"DD-TEST-128","Mã dự án":"DA-TEST01",
     "Tên xã/phường/đơn vị":"Xã A","Trạng thái":"Hoạt động"},
    {"Mã điểm":"DD-TEST-129","Mã dự án":"DA-TEST01",
     "Tên xã/phường/đơn vị":"Xã B","Trạng thái":"Hoạt động"},
    {"Mã điểm":"DD-OTHER","Mã dự án":"DA-OTHER",
     "Tên xã/phường/đơn vị":"Xã khác dự án","Trạng thái":"Hoạt động"},
]
MULTI_TASKS = {
    "VAN_CHUYEN": [
        {"_row":2,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
         "Mã nhiệm vụ VC":"VC-1","SKU":"TB-01","Mã đội VC":"","Trạng thái":"Chưa giao"},
        {"_row":3,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
         "Mã nhiệm vụ VC":"VC-2","SKU":"TB-02","Mã đội VC":"","Trạng thái":"Chưa giao"},
        {"_row":4,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-128",
         "Mã nhiệm vụ VC":"VC-3","SKU":"TB-01","Mã đội VC":"","Trạng thái":"Chưa giao"},
        {"_row":5,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-129",
         "Mã nhiệm vụ VC":"VC-4","SKU":"TB-01","Mã đội VC":"VC-OTHER","Trạng thái":"Chưa giao"},
        {"_row":6,"Mã dự án":"DA-OTHER","Mã điểm":"DD-OTHER",
         "Mã nhiệm vụ VC":"VC-5","SKU":"TB-01","Mã đội VC":"","Trạng thái":"Chưa giao"},
    ],
    "LAP_DAT": [
        {"_row":2,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
         "Mã nhiệm vụ LD":"LD-1","SKU":"TB-01","Mã đội KTV":"","Trạng thái":"Chưa lắp"},
        {"_row":3,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-127",
         "Mã nhiệm vụ LD":"LD-2","SKU":"TB-02","Mã đội KTV":"","Trạng thái":"Chưa lắp"},
        {"_row":4,"Mã dự án":"DA-TEST01","Mã điểm":"DD-TEST-128",
         "Mã nhiệm vụ LD":"LD-3","SKU":"TB-01","Mã đội KTV":"","Trạng thái":"Chưa lắp"},
    ]
}
BOTH_TEAM={**TEAM,"Loại nhiệm vụ":"VC+KTV"}
KTV_TEAM={**TEAM,"Loại nhiệm vụ":"KTV"}


class MultipleSiteAssignmentTests(unittest.TestCase):
    def test_only_approved_specialty_can_be_selected(self):
        self.assertEqual(allowed_modes(TEAM),("VC",))
        self.assertEqual(allowed_modes(KTV_TEAM),("LD",))
        self.assertEqual(allowed_modes(BOTH_TEAM),("VC","LD","VC+LD"))

    def test_search_dropdown_only_offers_pending_sites_no_conflicts(self):
        points=eligible_site_tasks(TEAM,"VC",LOCATIONS,MULTI_TASKS)
        self.assertEqual(set(points),{"DD-TEST-127","DD-TEST-128"})
        self.assertEqual(points["DD-TEST-127"][1]["VAN_CHUYEN"],2)

    def test_fifteen_sites_multiple_skus_single_team(self):
        sites=[{"Mã dự án":"DA-TEST01","Mã điểm":f"DD-{n}",
                "Trạng thái":"Hoạt động"} for n in range(15)]
        rows=[{"Mã dự án":"DA-TEST01","Mã điểm":f"DD-{n}",
               "Mã nhiệm vụ VC":f"VC-{n}-{i}","Mã đội VC":"",
               "Trạng thái":"Chưa giao","_row":n*3+i+2}
              for n in range(15) for i in range(3)]
        plan=site_assignment_plan(TEAM,"VC",[p["Mã điểm"] for p in sites],
                                  sites,{"VAN_CHUYEN":rows})
        self.assertEqual(len(plan["VAN_CHUYEN"]),45)
        req=compact_site_assignment_requests({"VAN_CHUYEN":44},plan,TEAM["Mã đội"])
        self.assertEqual(len(req),1)
        self.assertEqual(req[0]["repeatCell"]["range"]["startRowIndex"],1)
        self.assertEqual(req[0]["repeatCell"]["range"]["endRowIndex"],46)

    def test_dual_team_both_sheets_one_batch(self):
        plan=site_assignment_plan(BOTH_TEAM,"VC+LD",["DD-TEST-127"],
                                  LOCATIONS,MULTI_TASKS)
        self.assertEqual(len(plan["VAN_CHUYEN"]),2)
        self.assertEqual(len(plan["LAP_DAT"]),2)
        req=compact_site_assignment_requests(
            {"VAN_CHUYEN":14,"LAP_DAT":15},plan,BOTH_TEAM["Mã đội"])
        self.assertEqual(len(req),2)
        self.assertEqual({v["repeatCell"]["range"]["sheetId"] for v in req},{14,15})

    def test_vc_team_cannot_receive_installation(self):
        with self.assertRaises(ValueError):
            site_assignment_plan(TEAM,"LD",["DD-TEST-127"],LOCATIONS,MULTI_TASKS)

    def test_conflicted_site_fails_no_overwrite(self):
        with self.assertRaises(ValueError):
            site_assignment_plan(TEAM,"VC",["DD-TEST-129"],LOCATIONS,MULTI_TASKS)

    def test_cross_project_site_fails(self):
        with self.assertRaises(ValueError):
            site_assignment_plan(TEAM,"VC",["DD-OTHER"],LOCATIONS,MULTI_TASKS)

    def test_zero_pending_site_fails(self):
        with self.assertRaises(ValueError):
            site_assignment_plan(TEAM,"VC",["DD-TEST-999"],LOCATIONS,MULTI_TASKS)

    def test_role_specific_partial_conflict_blocked_for_combined(self):
        tasks={k:[dict(r) for r in v] for k,v in MULTI_TASKS.items()}
        tasks["LAP_DAT"][0]["Mã đội KTV"]="KTV-OTHER"
        self.assertNotIn("DD-TEST-127",
            eligible_site_tasks(BOTH_TEAM,"VC+LD",LOCATIONS,tasks))

    def test_noncontiguous_lines_make_two_requests(self):
        plan={"VAN_CHUYEN":[
            {"_row":2}, {"_row":5}, {"_row":6}]}
        req=compact_site_assignment_requests({"VAN_CHUYEN":19},plan,"VC-TEST")
        self.assertEqual(len(req),2)
        self.assertEqual(req[0]["repeatCell"]["range"]["endRowIndex"],2)
        self.assertEqual(req[1]["repeatCell"]["range"]["endRowIndex"],6)


if __name__=="__main__":
    unittest.main()
