"""Full-limit six-task JSONL batch through the real entry point, timeout 20s."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from public_validate import check


def run_scale_batch():
    n, m = 100000, 250000
    pairs = [[v, v + 1] for v in range(n - 1)]
    pairs.extend([[0, n - 1]] * (m - len(pairs)))
    weighted = [[v, v + 1, -10**9] for v in range(n - 1)]
    weighted.extend([[0, n - 1, 10**9]] * (m - len(weighted)))
    requests = [
        {"task": "dsu", "n": n, "operations": pairs},
        {"task": "kruskal", "n": n, "edges": weighted},
        {"task": "prim", "n": n, "edges": weighted},
        {"task": "scc", "n": n, "edges": pairs},
        {"task": "topo", "n": n, "edges": pairs},
        {"task": "dag", "n": n, "source": 0, "edges": weighted},
    ]
    input_text = "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in requests)
    started = perf_counter()
    completed = subprocess.run([sys.executable, str(ROOT / "src" / "Python" / "main.py")],
                               input=input_text, capture_output=True, text=True,
                               encoding="utf-8", timeout=20, check=True)
    elapsed = perf_counter() - started
    outputs = completed.stdout.splitlines()
    if len(outputs) != 6 or completed.stderr:
        raise AssertionError("Expected six JSON results and empty stderr")
    summaries = []
    for request, line in zip(requests, outputs):
        answer = json.loads(line)
        task = request["task"]
        if task == "dsu":
            expected = {"states": [[max(1, n - i - 1), min(n, i + 2)] for i in range(m)]}
            summary = {"states": len(answer["states"]), "last_state": answer["states"][-1]}
        elif task in ("kruskal", "prim"):
            expected = {"cost": -(n - 1) * 10**9, "components": 1}
            summary = {"cost": answer["cost"], "components": answer["components"],
                       "selected_edges": len(answer["edge_ids"])}
        elif task == "scc":
            expected = {"component": list(range(n))}
            summary = {"components": len(set(answer["component"])),
                       "condensation_pairs": len(answer["condensation"])}
        elif task == "topo":
            expected = {"acyclic": True}
            summary = {"acyclic": answer["acyclic"], "order_length": len(answer["order"])}
        else:
            expected = {"acyclic": True, "distance": [-v * 10**9 for v in range(n)]}
            summary = {"acyclic": answer["acyclic"], "distance_length": len(answer["distance"]),
                       "last_distance": answer["distance"][-1]}
        if not check(request, answer, expected):
            raise AssertionError(f"Full-limit transport witness failed: {task}")
        summaries.append({"task": task, "n": n, "m_or_q": m, "passed": True, **summary})
    return {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": f"{platform.python_implementation()} {platform.python_version()}",
        "platform": platform.platform(),
        "command": "python tests/scale_transport.py",
        "generator": "n=100000,m/q=250000; chain then repeated 0-to-n-1 edges; chain weights -10^9, extras +10^9",
        "timeout_seconds": 20,
        "elapsed_process_seconds": elapsed,
        "timing_boundary": "Process launch, JSON serialization inside child, parsing inside child, all algorithms, pipe input/output; excludes parent input generation and semantic validation",
        "input_utf8_bytes": len(input_text.encode("utf-8")),
        "input_sha256": hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        "actual_output_utf8_bytes": len(completed.stdout.encode("utf-8")),
        "actual_output_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "exit_code": completed.returncode,
        "stderr": completed.stderr,
        "results": summaries,
    }


def main():
    report = run_scale_batch()
    target = ROOT / "tests" / "scale_transport_results.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
