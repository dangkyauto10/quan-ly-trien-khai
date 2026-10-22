"""Regression: import approval UI even if registration helper is older.

The previous CI compiled Python syntax but did not import the runtime modules,
allowing ImportError at Streamlit startup.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch


class ApprovalRuntimeImportTests(unittest.TestCase):
    def test_module_import_and_atomic_request_with_legacy_registration(self):
        legacy = types.ModuleType("preview_registration")
        legacy.role_for_specialty = lambda value: "KTV"
        legacy.team_id_from_registration = lambda rid, kind: f"KTV-{rid}"
        legacy.matching_teams = lambda *args, **kwargs: []
        fake_streamlit = types.ModuleType("streamlit")
        module_file = pathlib.Path(__file__).resolve().parents[1] / "preview_approval_ui.py"
        spec = importlib.util.spec_from_file_location("preview_approval_ui_runtime_test", module_file)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"streamlit": fake_streamlit,
                                      "preview_registration": legacy}):
            spec.loader.exec_module(module)
        self.assertTrue(callable(module.render_pending_approvals))
        self.assertTrue(callable(module.approval_requests))
        team=["KTV-123","A","0912345678","KTV","","Hoạt động","DA-TEST01",""]
        req=module.approval_requests(1,2,3,"Đã duyệt",team,"KTV-123","admin",46317.6)
        self.assertEqual(len(req),3)
        self.assertIn("appendCells",req[0])
        self.assertIn("updateCells",req[1])
        self.assertEqual(req[2]["repeatCell"]["cell"]["userEnteredFormat"]["numberFormat"]["pattern"],"dd/mm/yyyy hh:mm")

if __name__ == "__main__":
    unittest.main()
