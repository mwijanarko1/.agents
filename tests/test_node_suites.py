import subprocess
import unittest
from pathlib import Path


class NodeSuitesTest(unittest.TestCase):
    def test_node_suites(self) -> None:
        tests = sorted(Path(__file__).parent.glob("test_*.mjs"))
        result = subprocess.run(
            ["node", "--test", *(str(test) for test in tests)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
