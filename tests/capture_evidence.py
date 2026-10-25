"""Run own tests and store actual outputs; does not fabricate expected results."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from public_validate import check


def main():
    folder = ROOT / "tests"
    cases = json.loads((folder / "cases.json").read_text(encoding="utf-8"))
    requests = "".join(json.dumps(case["input"], separators=(",", ":")) + "\n" for case in cases)
    expected = "".join(json.dumps(case["expected"], separators=(",", ":")) + "\n" for case in cases)
    (folder / "my_cases.jsonl").write_text(requests, encoding="utf-8")
    (folder / "expected_outputs.jsonl").write_text(expected, encoding="utf-8")
    run = subprocess.run([sys.executable, str(ROOT / "src" / "Python" / "main.py")],
                         input=requests, capture_output=True, text=True, encoding="utf-8",
                         check=True, timeout=20)
    (folder / "actual_outputs.jsonl").write_text(run.stdout, encoding="utf-8")
    actual = [json.loads(line) for line in run.stdout.splitlines()]
    if len(actual) != len(cases) or run.stderr:
        raise AssertionError("Transport must produce one result per request and no diagnostics")
    for case, result in zip(cases, actual):
        if not check(case["input"], result, case["expected"]):
            raise AssertionError(f"Fixture failed: {case['name']}: {result}")

    stream = io.StringIO()
    stream.write(f"Captured UTC: {datetime.now(timezone.utc).isoformat()}\n")
    stream.write(f"Runtime: {platform.python_implementation()} {platform.python_version()}\n")
    stream.write(f"Platform: {platform.platform()}\n")
    stream.write("Command: python tests/capture_evidence.py\n")
    stream.write(f"JSONL fixtures: {len(cases)}/{len(cases)} semantic checks passed.\n\n")
    suite = unittest.defaultTestLoader.discover(str(folder), pattern="test_algorithms.py")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (folder / "test_results.txt").write_text(stream.getvalue(), encoding="utf-8")
    print(stream.getvalue(), end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
