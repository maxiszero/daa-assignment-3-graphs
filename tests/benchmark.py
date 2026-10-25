"""Reproducible, independently checked Kruskal/Prim measurements (stdlib only)."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
from statistics import median
import subprocess
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "Python"))
import algorithms


def generate_graph(n, m, seed):
    """A negative spanning tree and nonnegative extra edges: known optimum."""
    rng = random.Random(seed)
    edges = [[v, rng.randrange(v), -rng.randint(1, 1_000_000_000)]
             for v in range(1, n)]
    expected_cost = sum(edge[2] for edge in edges)
    edges.extend([rng.randrange(n), rng.randrange(n), rng.randint(0, 1_000_000_000)]
                 for _ in range(m - len(edges)))
    rng.shuffle(edges)
    return edges, expected_cost


def validate_forest(n, edges, result, expected_cost):
    """Check a connected spanning tree by BFS, without either MST algorithm."""
    ids = result["edge_ids"]
    assert result["components"] == 1
    assert len(ids) == n - 1 and len(set(ids)) == n - 1
    adjacency = [[] for _ in range(n)]
    actual_cost = 0
    for edge_id in ids:
        assert isinstance(edge_id, int) and 0 <= edge_id < len(edges)
        u, v, weight = edges[edge_id]
        assert u != v
        adjacency[u].append(v)
        adjacency[v].append(u)
        actual_cost += weight
    seen = {0}
    queue = [0]
    for vertex in queue:
        for neighbour in adjacency[vertex]:
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    assert len(seen) == n  # Connected and n-1 distinct edges implies a tree.
    assert actual_cost == result["cost"] == expected_cost


def hardware():
    details = {
        "platform": platform.platform(),
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
    }
    if platform.system() == "Windows":
        command = (
            "$c = Get-CimInstance Win32_Processor | Select-Object -First 1; "
            "$s = Get-CimInstance Win32_ComputerSystem; "
            "@{cpu=$c.Name; physical_cores=$c.NumberOfCores; "
            "ram_bytes=$s.TotalPhysicalMemory} | ConvertTo-Json -Compress"
        )
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", command],
                text=True, timeout=20,
            )
            details.update(json.loads(output))
        except (OSError, ValueError, subprocess.SubprocessError):
            details["hardware_note"] = "Detailed Windows hardware query unavailable."
    return details


def route_examples():
    cases = [
        ("negative_route", 5, [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]], [3, 0, 4]),
        ("parallel_and_tied", 4,
         [[0, 1, 2], [0, 1, 2], [0, 2, 1], [2, 1, 1], [1, 3, -1], [2, 3, 0]], [1, 3]),
    ]
    examples = []
    for name, n, edges, targets in cases:
        result = algorithms.dag({"task": "dag", "n": n, "source": 0, "edges": edges})
        assert result["acyclic"]
        calls = []
        for target in targets:
            path = algorithms.reconstruct_path(0, target, result["parent_edge"], edges)
            selected_ids = [result["parent_edge"][v] for v in path[1:]]
            for i, edge_id in enumerate(selected_ids):
                assert edges[edge_id][:2] == path[i:i + 2]
            weight = sum(edges[edge_id][2] for edge_id in selected_ids) if path else None
            assert weight == result["distance"][target]
            calls.append({"source": 0, "target": target, "vertices": path,
                          "edge_ids": selected_ids, "weight": weight})
        examples.append({"name": name, "n": n, "edges": edges,
                         "dag_result": result, "helper_calls": calls})
    return examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tests" / "benchmark_results.json")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("At least three repetitions are required.")
    report = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": hardware(),
        "timer": "time.perf_counter_ns; reported in milliseconds",
        "warm_up": "One untimed verified call to each method on each graph",
        "boundary": "Direct algorithm call, including internal adjacency/sort/heap/result allocation; excludes graph generation, JSON encoding/decoding, validation, I/O, and hardware query",
        "order": "Kruskal then Prim on even repetitions; Prim then Kruskal on odd repetitions",
        "generator": "random.Random(seed); negative random recursive tree; nonnegative extra edges (parallel edges and loops allowed); shuffle once",
        "correctness": "Known optimum is the sum of all negative tree edges; each returned forest checked with independent BFS, distinct edge IDs, n-1 edges and exact total",
        "cases": [],
        "route_examples": route_examples(),
    }
    for n, m, seed in [(1000, 4000, 31001), (10000, 40000, 31002), (100000, 250000, 31003)]:
        edges, expected_cost = generate_graph(n, m, seed)
        request = {"n": n, "edges": edges}
        encoded = json.dumps(edges, separators=(",", ":")).encode("utf-8")
        case = {"n": n, "m": m, "seed": seed, "expected_cost": expected_cost,
                "graph_sha256": hashlib.sha256(encoded).hexdigest(), "methods": {}}
        del encoded
        timings = {"kruskal": [], "prim": []}
        for name in timings:
            validate_forest(n, edges, getattr(algorithms, name)(request), expected_cost)
        for repetition in range(args.repeats):
            names = ("kruskal", "prim") if repetition % 2 == 0 else ("prim", "kruskal")
            for name in names:
                method = getattr(algorithms, name)
                start = perf_counter_ns()
                result = method(request)
                elapsed_ms = (perf_counter_ns() - start) / 1_000_000
                validate_forest(n, edges, result, expected_cost)
                timings[name].append(elapsed_ms)
                del result
        for name, values in timings.items():
            case["methods"][name] = {"milliseconds": values, "median_ms": median(values)}
        case["verified"] = True
        report["cases"].append(case)
        print(json.dumps(case, separators=(",", ":")), flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved measurements: {args.output}")


if __name__ == "__main__":
    main()
