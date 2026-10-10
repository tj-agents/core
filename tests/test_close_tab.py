import importlib.util
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / ".agents/machine/utility/peer-cli/scripts/close_tab.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("close_tab", PATH); close_tab = importlib.util.module_from_spec(spec); spec.loader.exec_module(close_tab)

class CloseTabTests(unittest.TestCase):
    def test_missing_or_unverified_native_identity_refuses(self):
        with self.assertRaises(close_tab.TerminalRefusal):
            close_tab.close_entry({"pid": 0, "pid_started_at": 0, "terminal": {"kind": "kitty"}})

    def test_windows_adapter_uses_exact_id_and_no_keystrokes(self):
        source = PATH.with_name("windows_terminal_uia.ps1").read_text(encoding="utf-8")
        self.assertIn("AutomationIdProperty, $TabId", source); self.assertIn("WindowsTerminal", source); self.assertNotIn("SendKeys", source)
