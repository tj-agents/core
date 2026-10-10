import importlib.util
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / ".agents/machine/utility/peer-cli/scripts/peer_cli.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("peer_cli", PATH); peer_cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(peer_cli)

class PeerCliTests(unittest.TestCase):
    def test_ambiguous_prefix_refuses(self):
        with self.assertRaises(Exception): peer_cli.select([{"title": "one", "session_id": "a"}, {"title": "once", "session_id": "b"}], "on")

    def test_exact_session_id_wins(self):
        self.assertEqual("b", peer_cli.select([{"title": "one", "session_id": "a"}, {"title": "once", "session_id": "b"}], "b")["session_id"])
