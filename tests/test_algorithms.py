"""Independent expected values and semantic checks for all graph tasks."""

import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "Python"))
sys.path.insert(0, str(ROOT / "tools"))
import algorithms
from public_validate import check


def partition(n, edges):
    """Small-graph oracle: merge explicit sets, without using tested DSU."""
    groups = [{v} for v in range(n)]
    for u, v, *_ in edges:
        a = next(group for group in groups if u in group)
        b = next(group for group in groups if v in group)
        if a is not b:
            groups.remove(b)
            a.update(b)
    return groups


def brute_forest(n, edges):
    """Enumerate all n-c edge subsets; minimum connected witness is optimal."""
    components = len(partition(n, edges))
    best = None
    for ids in itertools.combinations(range(len(edges)), n - components):
        selected = [edges[i] for i in ids]
        if len(partition(n, selected)) == components:
            cost = sum(edge[2] for edge in selected)
            best = cost if best is None else min(best, cost)
    return {"cost": best, "components": components}


def closure_components(n, edges):
    """Floyd-Warshall reachability, independent of DFS/Kosaraju."""
    reach = [[u == v for v in range(n)] for u in range(n)]
    for u, v in edges:
        reach[u][v] = True
    for k in range(n):
        for u in range(n):
            for v in range(n):
                reach[u][v] |= reach[u][k] and reach[k][v]
    return [min(v for v in range(n) if reach[u][v] and reach[v][u])
            for u in range(n)]


def kahn_acyclic(n, edges):
    """Cycle oracle uses indegrees, not DFS states."""
    outgoing = [[] for _ in range(n)]
    degree = [0] * n
    for u, v, *_ in edges:
        outgoing[u].append(v)
        degree[v] += 1
    queue = [v for v in range(n) if degree[v] == 0]
    index = 0
    while index < len(queue):
        u = queue[index]
        index += 1
        for v in outgoing[u]:
            degree[v] -= 1
            if degree[v] == 0:
                queue.append(v)
    return len(queue) == n


def bellman_ford(n, edges, source):
    distance = [None] * n
    distance[source] = 0
    for _ in range(n - 1):
        changed = False
        for u, v, weight in edges:
            if distance[u] is not None:
                candidate = distance[u] + weight
                if distance[v] is None or candidate < distance[v]:
                    distance[v] = candidate
                    changed = True
        if not changed:
            break
    return distance


class AlgorithmTests(unittest.TestCase):
    def assert_valid(self, request, expected):
        result = getattr(algorithms, request["task"])(request)
        self.assertTrue(check(request, result, expected), (request, result, expected))
        return result

    def test_empty_graphs_and_singleton_dag(self):
        cases = [
            ({"task": "dsu", "n": 0, "operations": []}, {"states": []}),
            ({"task": "kruskal", "n": 0, "edges": []}, {"cost": 0, "components": 0}),
            ({"task": "prim", "n": 0, "edges": []}, {"cost": 0, "components": 0}),
            ({"task": "scc", "n": 0, "edges": []}, {"component": []}),
            ({"task": "topo", "n": 0, "edges": []}, {"acyclic": True}),
            ({"task": "dag", "n": 1, "edges": [], "source": 0},
             {"acyclic": True, "distance": [0]}),
        ]
        for request, expected in cases:
            with self.subTest(task=request["task"]):
                self.assert_valid(request, expected)

    def test_dsu_repeated_self_unions_and_isolates(self):
        self.assert_valid({"task": "dsu", "n": 6,
                           "operations": [[0, 0], [0, 1], [1, 0], [2, 3], [1, 3], [5, 5]]},
                          {"states": [[6, 1], [5, 2], [5, 2], [4, 2], [3, 4], [3, 4]]})

    def test_dsu_random_against_set_partition(self):
        rng = random.Random(3101)
        for _ in range(40):
            n = rng.randrange(1, 9)
            operations = [[rng.randrange(n), rng.randrange(n)] for _ in range(20)]
            states = []
            for end in range(1, len(operations) + 1):
                groups = partition(n, operations[:end])
                states.append([len(groups), max(map(len, groups))])
            self.assert_valid({"task": "dsu", "n": n, "operations": operations}, {"states": states})

    def test_forests_disconnected_negative_parallel_tied_and_self_loops(self):
        edges = [[0, 0, -100], [0, 1, 8], [0, 1, -4], [1, 2, 2],
                 [0, 2, 2], [3, 4, -7], [3, 4, -7], [4, 4, -99]]
        for task in ("kruskal", "prim"):
            self.assert_valid({"task": task, "n": 6, "edges": edges},
                              {"cost": -9, "components": 3})

    def test_forests_random_against_exhaustive_subsets(self):
        rng = random.Random(3102)
        for _ in range(60):
            n = rng.randrange(1, 6)
            edges = [[rng.randrange(n), rng.randrange(n), rng.randrange(-7, 8)]
                     for _ in range(rng.randrange(9))]
            expected = brute_forest(n, edges)
            for task in ("kruskal", "prim"):
                self.assert_valid({"task": task, "n": n, "edges": edges}, expected)

    def test_forest_totals_exceed_signed_32_bits(self):
        for weight in (-10**9, 10**9):
            edges = [[v, v + 1, weight] for v in range(5)]
            for task in ("kruskal", "prim"):
                self.assert_valid({"task": task, "n": 6, "edges": edges},
                                  {"cost": 5 * weight, "components": 1})

    def test_scc_random_against_transitive_closure(self):
        rng = random.Random(3103)
        for _ in range(70):
            n = rng.randrange(1, 9)
            edges = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randrange(25))]
            self.assert_valid({"task": "scc", "n": n, "edges": edges},
                              {"component": closure_components(n, edges)})

    def test_scc_condensation_deduplicates_and_keeps_isolates(self):
        edges = [[0, 1], [1, 0], [0, 2], [1, 2], [1, 2], [2, 2], [2, 3], [3, 2]]
        self.assert_valid({"task": "scc", "n": 5, "edges": edges},
                          {"component": [0, 0, 2, 2, 4]})

    def test_topological_finished_neighbor_is_not_a_cycle(self):
        self.assert_valid({"task": "topo", "n": 5,
                           "edges": [[0, 1], [0, 2], [2, 1], [2, 1]]}, {"acyclic": True})

    def test_topological_self_loop_and_disconnected_cycle(self):
        for edges in ([[3, 3]], [[0, 1], [2, 3], [3, 2]]):
            self.assert_valid({"task": "topo", "n": 5, "edges": edges}, {"acyclic": False})

    def test_topological_random_against_kahn(self):
        rng = random.Random(3104)
        for _ in range(80):
            n = rng.randrange(1, 11)
            edges = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randrange(25))]
            self.assert_valid({"task": "topo", "n": n, "edges": edges},
                              {"acyclic": kahn_acyclic(n, edges)})

    def test_dag_negative_distance_minus_one_and_unreachable(self):
        self.assert_valid({"task": "dag", "n": 5, "source": 0,
                           "edges": [[0, 1, -1], [1, 2, -10**9], [3, 4, -10**9]]},
                          {"acyclic": True, "distance": [0, -1, -1000000001, None, None]})

    def test_dag_cycle_outside_source_reachability(self):
        self.assert_valid({"task": "dag", "n": 5, "source": 0,
                           "edges": [[0, 1, 7], [2, 3, -1], [3, 2, 2]]}, {"acyclic": False})
        self.assert_valid({"task": "dag", "n": 3, "source": 0,
                           "edges": [[2, 2, 0]]}, {"acyclic": False})

    def test_dag_random_against_bellman_ford(self):
        rng = random.Random(3105)
        for _ in range(80):
            n = rng.randrange(2, 10)
            order = list(range(n))
            rng.shuffle(order)
            edges = []
            for _ in range(rng.randrange(25)):
                u, v = sorted(rng.sample(range(n), 2))
                edges.append([order[u], order[v], rng.randrange(-20, 21)])
            source = rng.randrange(n)
            self.assert_valid({"task": "dag", "n": n, "source": source, "edges": edges},
                              {"acyclic": True, "distance": bellman_ford(n, edges, source)})

    def test_route_helper_reachable_source_unreachable_parallel_and_ties(self):
        edges = [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4], [0, 1, 3], [0, 3, 0]]
        result = self.assert_valid({"task": "dag", "n": 5, "source": 0, "edges": edges},
                                   {"acyclic": True, "distance": [0, 3, -4, 0, None]})
        parent = result["parent_edge"]
        self.assertEqual(algorithms.reconstruct_path(0, 0, parent, edges), [0])
        self.assertEqual(algorithms.reconstruct_path(0, 4, parent, edges), [])
        for target in (1, 2, 3):
            route = algorithms.reconstruct_path(0, target, parent, edges)
            self.assertEqual((route[0], route[-1]), (0, target))
            total = 0
            for u, v in zip(route, route[1:]):
                a, b, weight = edges[parent[v]]
                self.assertEqual((a, b), (u, v))
                total += weight
            self.assertEqual(total, result["distance"][target])

    def test_transport_mixed_requests_repeat_and_reset_state(self):
        cases = load_cases()
        requests = [case["input"] for case in cases] * 3
        completed = subprocess.run([sys.executable, str(ROOT / "src" / "Python" / "main.py")],
                                   input="".join(json.dumps(x) + "\n" for x in requests),
                                   text=True, encoding="utf-8", capture_output=True, check=True, timeout=20)
        self.assertEqual(completed.stderr, "")
        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), len(requests))
        for case, line in zip(cases * 3, lines):
            self.assertTrue(check(case["input"], json.loads(line), case["expected"]), case["name"])


class WitnessCheckerTests(unittest.TestCase):
    """Prove checking allows non-unique solutions and rejects bad witnesses."""

    def test_forest_alternative_and_invalid_cycle_or_id(self):
        request = {"task": "kruskal", "n": 3, "edges": [[0, 1, 1], [1, 2, 1], [0, 2, 1]]}
        expected = {"cost": 2, "components": 1}
        for ids in ([0, 1], [2, 1]):
            self.assertTrue(check(request, dict(expected, edge_ids=ids), expected))
        for ids in ([0, 0], [0, 3], [0, 1, 2], [0]):
            self.assertFalse(check(request, dict(expected, edge_ids=ids), expected))

    def test_scc_alternative_labels_and_invalid_partition_or_condensation(self):
        request = {"task": "scc", "n": 3, "edges": [[0, 1], [1, 0], [1, 2]]}
        expected = {"component": [0, 0, 2]}
        self.assertTrue(check(request, {"component": [7, 7, 9], "condensation": [[7, 9]]}, expected))
        self.assertTrue(check(request, {"component": [4, 4, 1], "condensation": [[4, 1]]}, expected))
        for result in ({"component": [7, 7, 7], "condensation": []},
                       {"component": [7, 7, 9], "condensation": []},
                       {"component": [7, 7, 9], "condensation": [[7, 9], [7, 9]]}):
            self.assertFalse(check(request, result, expected))

    def test_topological_alternative_and_invalid_precedence_or_duplicate(self):
        request = {"task": "topo", "n": 3, "edges": [[0, 2], [1, 2]]}
        expected = {"acyclic": True}
        for order in ([0, 1, 2], [1, 0, 2]):
            self.assertTrue(check(request, {"acyclic": True, "order": order}, expected))
        for order in ([2, 0, 1], [0, 0, 2]):
            self.assertFalse(check(request, {"acyclic": True, "order": order}, expected))

    def test_dag_alternative_parent_edges_and_invalid_direction_or_distance(self):
        request = {"task": "dag", "n": 3, "source": 0,
                   "edges": [[0, 1, 1], [0, 1, 1], [1, 2, 1], [0, 2, 2]]}
        expected = {"acyclic": True, "distance": [0, 1, 2]}
        for parents in ([-1, 0, 2], [-1, 1, 3]):
            self.assertTrue(check(request, dict(expected, parent_edge=parents), expected))
        for parents in ([-1, 3, 2], [-1, -1, 2], [0, 1, 2]):
            self.assertFalse(check(request, dict(expected, parent_edge=parents), expected))
        self.assertFalse(check(request, {"acyclic": True, "distance": [0, 1, 3],
                                         "parent_edge": [-1, 0, 2]}, expected))


class FullLimitTests(unittest.TestCase):
    def test_dsu_100000_vertices_250000_operations(self):
        n = 100000
        operations = [[v, v + 1] for v in range(n - 1)]
        operations.extend([[0, n - 1]] * (250000 - len(operations)))
        result = algorithms.dsu({"n": n, "operations": operations})["states"]
        self.assertEqual(len(result), 250000)
        for i, state in enumerate(result):
            self.assertEqual(state, [max(1, n - i - 1), min(n, i + 2)])

    def test_forests_100000_vertices_250000_edges(self):
        n = 100000
        edges = [[v, v + 1, -10**9] for v in range(n - 1)]
        edges.extend([[0, n - 1, 10**9]] * (250000 - len(edges)))
        expected = {"cost": -(n - 1) * 10**9, "components": 1}
        for task in ("kruskal", "prim"):
            request = {"task": task, "n": n, "edges": edges}
            self.assertTrue(check(request, getattr(algorithms, task)(request), expected), task)

    def test_scc_100000_deep_chain_250000_edges(self):
        n = 100000
        edges = [[v, v + 1] for v in range(n - 1)]
        edges.extend([[0, n - 1]] * (250000 - len(edges)))
        request = {"task": "scc", "n": n, "edges": edges}
        self.assertTrue(check(request, algorithms.scc(request), {"component": list(range(n))}))

    def test_scc_100000_cycle(self):
        n = 100000
        edges = [[v, (v + 1) % n] for v in range(n)]
        request = {"task": "scc", "n": n, "edges": edges}
        self.assertTrue(check(request, algorithms.scc(request), {"component": [0] * n}))

    def test_topological_100000_deep_chain_250000_edges(self):
        n = 100000
        edges = [[v, v + 1] for v in range(n - 1)]
        edges.extend([[0, n - 1]] * (250000 - len(edges)))
        request = {"task": "topo", "n": n, "edges": edges}
        self.assertTrue(check(request, algorithms.topo(request), {"acyclic": True}))

    def test_dag_100000_deep_chain_250000_edges_and_route(self):
        n = 100000
        edges = [[v, v + 1, -10**9] for v in range(n - 1)]
        edges.extend([[0, n - 1, 10**9]] * (250000 - len(edges)))
        request = {"task": "dag", "n": n, "source": 0, "edges": edges}
        result = algorithms.dag(request)
        expected = {"acyclic": True, "distance": [-v * 10**9 for v in range(n)]}
        self.assertTrue(check(request, result, expected))
        self.assertEqual(algorithms.reconstruct_path(0, n - 1, result["parent_edge"], edges), list(range(n)))


def load_cases():
    return json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
