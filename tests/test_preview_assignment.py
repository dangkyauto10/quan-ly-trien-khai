import unittest
from preview_assignment import assignment_rows, assignment_batch_requests

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

if __name__=="__main__":
    unittest.main()
