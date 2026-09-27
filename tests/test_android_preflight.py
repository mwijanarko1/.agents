import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path.home() / ".agents" / "scripts" / "android_preflight.py"
SPEC = importlib.util.spec_from_file_location("android_preflight", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class AndroidPreflightTest(unittest.TestCase):
    def test_parse_ready_serials_ignores_offline_and_unauthorized(self):
        output = (
            "List of devices attached\n"
            "emulator-5554\tdevice\n"
            "ABC123\tunauthorized\n"
            "emulator-5556\toffline\n"
        )
        self.assertEqual(MODULE.parse_ready_serials(output), ["emulator-5554"])

    def test_parse_ready_serials_empty_list(self):
        self.assertEqual(MODULE.parse_ready_serials("List of devices attached\n\n"), [])


if __name__ == "__main__":
    unittest.main()
