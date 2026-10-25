# Assignment 3: Graph Algorithms

## Implementation and reproducibility

The selected language is **Python 3.12+**. The implementation is in
`src/Python/algorithms.py`; the supplied JSON Lines adapter is unchanged.
Only Python's standard library is required. Python does not need a separate
compilation step. Run these commands from the repository root:

```sh
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tools -p "test_*.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
python tools/run.py --input tests/my_cases.jsonl
python tests/capture_evidence.py
python tests/scale_transport.py
python tests/benchmark.py
```

The manifest selects Python, so no language override is needed. Alternatively,
`python src/Python/main.py` accepts one JSON request per input line. It produces
exactly one result per line; `ping` still returns `{"status":"ready"}`.
No package installation or network access is needed to build or run the solution.

Every request creates its own DSU, adjacency lists, traversal colours, heap,
distance array, and output arrays. There is no mutable global algorithm state,
and input edge lists are not reordered or mutated. Thus a previous graph cannot
affect the next request, including when different tasks alternate in one process.
Original edge IDs are the positions in the input edge list. Python integers keep
costs exact when totals exceed 32 bits; the published limits keep these results
within signed 64-bit range. `None` becomes JSON `null` for unreachable distances.

## Algorithms, invariants, and correctness

### Disjoint-set union

Initially, each vertex is its own root, its size is one, and the component count
is `n`. `find` walks to a root and then compresses every parent on the traversed
path. `union` attaches the smaller root's tree below the larger root, adds their
sizes, decrements the component count, and updates the largest component.

The invariant is that the parent forest partitions vertices exactly according to
connections processed so far, and each root's stored size equals its component's
cardinality. Compression changes only the representation, not the root or
partition. Joining distinct roots merges exactly the two connected components;
joining equal roots changes nothing. Induction over operations proves each
returned `[components, largest]` pair correct. Repeated unions and self-unions
therefore preserve the state. For `n=0`, the largest size is zero and no states
are returned. No initial state is included before the first operation.

### Kruskal minimum spanning forest

Sort original edge IDs by weight. For each edge, add it exactly when DSU reports
that its endpoints were in different components. The selected edges remain an
acyclic forest: every accepted edge joins two previously separate trees.

For optimality, consider a selected edge and one current tree's cut. Any lighter
edge crossing that cut would already have been processed and would have joined
its endpoints. The selected edge is therefore a lightest crossing edge, so the
cut/exchange property permits it in a minimum spanning forest. Repeating this
argument preserves an optimal extension of the selected forest. Once every edge
has been considered, no input edge connects different DSU sets; these sets are
exactly the original graph's connected components. A forest with `c` components
has `n-c` selected edges. Self-loops are rejected by DSU, parallel edges retain
separate IDs, and negative or equal weights do not affect the cut argument.
Isolated vertices remain components; the empty graph returns zero cost and zero
components.

### Prim minimum spanning forest

Build undirected adjacency lists containing `(weight, edge_id, neighbour)`.
Ignore self-loops. Start at each as-yet unvisited vertex, count a new component,
and place its outgoing edges in a minimum heap. Repeatedly discard stale heap
entries whose destination is already visited. Otherwise, accept the edge, visit
its destination, and insert edges from that vertex to unvisited neighbours.

The invariant is that the current selected tree spans the visited vertices of
this component, and every edge crossing from that tree to an unvisited vertex is
available in the heap. After stale entries are removed, the minimum entry is a
lightest crossing edge. The cut property makes that choice safe. It attaches one
new vertex, so it cannot introduce a cycle or repeat a selected edge. An empty
heap means no edge leaves the completed component. Restarting visits every
component, including isolates, and combines their independent minimum trees.
Negative weights, ties, and parallel edges are handled by ordinary heap ordering;
the edge ID breaks equal-weight ties without changing optimality. The empty
graph has no restart and returns the required empty forest.

### Kosaraju strongly connected components

Build the graph and its transpose. The first DFS visits every vertex and records
finish order. The second DFS runs on the transpose, starting at unlabelled
vertices in decreasing first-pass finish order; one traversal assigns one label.
Finally, scan input edges and append each distinct cross-label pair once, using
a set to deduplicate the condensation.

The first-pass invariant is ordinary DFS completion: a vertex enters finish
order only after all its outgoing edges have been examined. For an edge between
distinct SCCs `C -> D`, the maximum first-pass finishing time in `C` is greater
than that in `D`. Processing components in decreasing finish time therefore
starts from a source among remaining original
components, which is a sink in the remaining transpose. A transpose traversal
cannot enter another unlabelled component, but reaches all vertices in its own
SCC by mutual reachability. Each second-pass traversal labels exactly one maximal
SCC. The final scan includes all and only cross-component edges, with no
duplicates. Isolates receive separate labels. Self-loops and repeated edges do
not change the partition; for `n=0`, both arrays are empty.

### DFS topological ordering

The DFS helper has three colours: unvisited, active, and finished. Every explicit
stack frame stores `[vertex, next_neighbour_index]`. The neighbour index advances
before descending, preserving progress when the child finishes. Encountering an
active neighbour closes a path on the active DFS stack and proves a directed
cycle. An edge to a finished vertex is harmless. Starting DFS at every unvisited
vertex checks all components, including ones disconnected from any chosen source.

Without a back edge, every directed edge `u -> v` has `v` finish before `u`:
either DFS explores `v` from `u`, or `v` was already finished when the edge was
examined. Reversing finish order therefore places every edge forward and includes
every vertex once. Conversely, every directed cycle produces a back edge during
DFS, so the algorithm rejects it and returns an empty order. A self-loop is a
back edge; duplicate edges are safe. Empty graphs are acyclic with empty order.

### DAG shortest paths

First run the same three-colour DFS over the **entire** graph. A cycle anywhere,
even outside source reachability, returns `acyclic=false` with two empty arrays.
Otherwise initialize the source distance to zero, all other distances to `None`,
and all parent IDs to `-1`. Process vertices in reverse finish order. Skip an
unreachable vertex; for each outgoing edge of a reachable vertex, replace the
destination's distance and parent edge only for a strictly better distance.

Before a vertex is processed, all its predecessors are already processed, so all
possible last edges of a source path to that vertex have been relaxed. Induction
over the topological order proves its stored distance is the shortest possible.
Every improvement records the original ID of an edge ending at that vertex and
coming from a reachable predecessor. Following parents moves backward in a
topological order and must terminate at the source, proving the route witness is
valid. Negative weights are allowed because no later vertex can lead back and
improve an earlier vertex. An unreachable distance remains `None`, not `-1`,
which can be a valid finite distance. Equal shortest routes retain the first
recorded parent, and parallel edges remain distinguishable by ID. A DAG cannot
have a reachable path back into its source, so the source retains distance zero
and parent `-1`.

### Route reconstruction and actual calls

`reconstruct_path(source, target, parent_edge, edges)` follows incoming edge IDs
backward, checks their direction, collects vertices, and reverses the result.
The no-route convention is `[]`. The route from the source to itself is
`[source]`. The helper expects a successful DAG result; it raises `ValueError`
for invalid edge IDs, edges ending at the wrong vertex, or cyclic parent chains.
It does not rescan the graph or search for predecessor edges.

The following outputs were actually produced by `route_examples()` in
`tests/benchmark.py` and are stored in `tests/benchmark_results.json`. The unit
tests also call the helper directly.

```python
edges = [[0,1,3], [0,2,8], [1,2,-7], [2,3,4]]
result = dag({"n": 5, "source": 0, "edges": edges})
# distance: [0, 3, -4, 0, None]
# parent_edge: [-1, 0, 2, 3, -1]
p = result["parent_edge"]
reconstruct_path(0, 3, p, edges)  # [0, 1, 2, 3]
reconstruct_path(0, 0, p, edges)  # [0]
reconstruct_path(0, 4, p, edges)  # []
```

The reachable route uses IDs `[0,2,3]`, directed `0->1`, `1->2`, `2->3`, with
total weight `3-7+4=0`. The source route uses no edges and has cost zero. Vertex
4 has no parent path and a null distance, so no route cost is assigned.

```python
edges = [[0,1,2], [0,1,2], [0,2,1], [2,1,1], [1,3,-1], [2,3,0]]
result = dag({"n": 4, "source": 0, "edges": edges})
# distance: [0, 2, 1, 1]
# parent_edge: [-1, 0, 2, 5]
p = result["parent_edge"]
reconstruct_path(0, 1, p, edges)  # [0, 1], ID [0], weight 2
reconstruct_path(0, 3, p, edges)  # [0, 2, 3], IDs [2, 5], weight 1+0=1
```

IDs 0 and 1 are parallel equal-weight edges, and `0->2->1` is another route of
cost 2. Both `0->1->3` and `0->2->3` have cost 1. The stored parents select valid
directed shortest paths without requiring one particular answer among ties.
The benchmark checks every selected edge's endpoints against adjacent vertices
of the reconstructed path and compares its total weight with the distance.

## Complexity and deep graphs

Let `n` be vertices, `m` edges, `q` union operations, and `L` route vertices.
Memory bounds include returned results and adjacency structures.

| Method | Time | Memory |
|---|---|---|
| DSU | `O(n + q alpha(n))` amortized | `O(n+q)` |
| Kruskal | `O(n + m log(m+1))` | `O(n+m)` |
| Prim with lazy heap | `O(n + m log(m+1))` | `O(n+m)` |
| Kosaraju SCC | `O(n+m)` expected | `O(n+m)` |
| DFS topological ordering | `O(n+m)` | `O(n+m)` |
| DAG shortest paths | `O(n+m)` | `O(n+m)` |
| Route helper | `O(L)` for a returned route | `O(L)` |

DSU's inverse-Ackermann bound uses both compression and union by size. Kruskal
sorts `m` IDs and performs at most `m` unions. Prim inserts at most a constant
number of heap entries per edge, and its heap can contain `O(m)` entries. SCC
uses expected constant-time hashing for condensation pairs. Each DFS examines
each adjacency entry once because its stack retains the next-neighbour index.
All traversals and DSU operations are iterative; a 100,000-vertex chain uses heap
memory for explicit stacks instead of Python's recursive call stack. Increasing
the interpreter recursion limit is unnecessary.

## Own tests and semantic checks

`tests/test_algorithms.py` uses independent reference calculations for small
graphs: explicit set partitions for DSU, exhaustive feasible edge subsets for
minimum forest costs, transitive closure for SCC equivalence, Kahn's algorithm
for acyclicity, and Bellman-Ford relaxation for DAG distances. Randomized small
cases use fixed seeds. Expected values are derived from these references or
simple mathematical constructions, rather than copied from the implementation.

Non-unique outputs are checked with the supplied semantic validator, using
independently calculated expected values. Tests deliberately show that alternate
optimal forests, SCC labelings, topological orders, and parent edges are accepted,
and that duplicate/cyclic forest edges, incorrect SCCs or condensation, reversed
precedence, and invalid parent edges or distances are rejected.

Boundary tests cover empty graphs, isolates and disconnected graphs, repeated
and self-unions, self-loops, parallel and tied edges, negative weights, finite
distance `-1`, totals beyond signed 32 bits, unreachable vertices, and cycles in
a component unreachable from the DAG source. Mixed requests repeat in one
subprocess to test JSON Lines transport and state reset.

Full-limit tests use `n=100000` and `m` or `q=250000` for DSU, both forest
algorithms, SCC, topological ordering, and DAG shortest paths. Their chain-based
construction gives exact expected answers without running another copy of the
same algorithm. An additional 100,000-vertex directed cycle checks SCC merging;
the DAG chain also reconstructs the complete 100,000-vertex route. Stored inputs,
expected answers, actual outputs, and execution logs are described in
`tests/README.md`.

Actual verification recorded on 2026-10-25:

| Check | Result | Evidence |
|---|---|---|
| Supplied launcher and public checks | Setup ping passed; all 36 public cases passed; two complete batches passed in one process | `tests/public_check_results.txt` |
| Own unit tests, including full-limit and semantic-checker tests | 26 passed, 1.976 s | `tests/test_results.txt` |
| Stored JSON Lines fixtures | 19/19 semantic checks passed | `tests/cases.json`, `tests/my_cases.jsonl`, `tests/expected_outputs.jsonl`, `tests/actual_outputs.jsonl` |
| Six full-limit requests in one real JSON Lines subprocess | All passed; 1.9854 s within a 20 s timeout | `tests/scale_transport_results.json` |
| Template tool tests | 16 tests run, 4 skipped for unavailable unselected runtimes | Local `python -m unittest discover -s tools -p "test_*.py"` run |

`python tests/capture_evidence.py` regenerates the fixture actual outputs and the
own-test execution log. Fixture expectations and their reasoning are in
`tests/cases.json`; they are not regenerated from the algorithm's answers.
`python tests/scale_transport.py` generates the six full-limit requests, sends
them together to the unchanged entry point, and validates all returned witnesses.
The scale report stores summaries and SHA-256 hashes of the complete input and
actual output rather than committing a large redundant graph/output file. Its
elapsed time includes process launch, pipe input/output, child JSON parsing and
serialization, and all six algorithms, but excludes parent-side graph generation
and semantic validation. This is a transport/scale check, not the MST benchmark
timing boundary below.

## Kruskal versus Prim: measured experiment

The recorded run started at **2026-10-25 17:39:11 UTC**. Environment:
CPython 3.12.6, 64-bit, Windows 10 build 19045, Intel Core i5-13450HX,
10 physical cores / 16 logical CPUs, 16,873,545,728 bytes reported RAM.
Both algorithms execute in one Python process on one thread.

Reproduce with `python tests/benchmark.py`. The raw five timings, graph SHA-256
hashes, seeds, runtime, hardware, and route examples are saved to
`tests/benchmark_results.json`. The generator first creates a random recursive
tree: vertex `v>0` connects to a uniformly selected earlier vertex, with a
strictly negative weight. It adds nonnegative random edges, allowing parallel
edges and loops, then shuffles the complete edge list once. `random.Random(seed)`
is local to each size. Both methods receive the exact same list at that size.

This construction has an independently known optimum: all `n-1` negative edges
already form a spanning tree. Any other spanning tree replaces one or more
negative edges with nonnegative edges, increasing cost. Before timing, one
untimed call per method is checked for distinct valid edge IDs, no self-loops,
`n-1` edges, connectivity by an independent BFS, component count one, and the
known optimal cost. Every timed result is checked again outside the timer.

| n | m | Seed | Independently known optimum cost |
|---:|---:|---:|---:|
| 1,000 | 4,000 | 31001 | -506,438,124,296 |
| 10,000 | 40,000 | 31002 | -4,962,383,938,702 |
| 100,000 | 250,000 | 31003 | -49,930,103,787,251 |

Timing uses `time.perf_counter_ns()`, converted to milliseconds. A timed region
contains only the direct method call, including internal adjacency construction,
sorting or heap operations, and result allocation. Input graph generation, JSON
parsing/serialization, hardware queries, validation, and input/output are
excluded for both methods. Compilation is excluded (Python requires none).
The order alternates Kruskal/Prim and Prim/Kruskal across repetitions to reduce
systematic ordering effects. Garbage collection remains at its default setting.

| n | Method | Run 1 ms | Run 2 ms | Run 3 ms | Run 4 ms | Run 5 ms | Median ms |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1,000 | Kruskal | 3.1834 | 2.3635 | 2.3402 | 2.3731 | 2.3433 | 2.3635 |
| 1,000 | Prim | 3.7119 | 3.5922 | 2.9291 | 2.8955 | 2.8897 | 2.9291 |
| 10,000 | Kruskal | 68.7075 | 51.0246 | 38.5297 | 46.4603 | 65.6152 | 51.0246 |
| 10,000 | Prim | 84.9395 | 77.6440 | 64.3804 | 67.3533 | 87.4419 | 77.6440 |
| 100,000 | Kruskal | 459.2477 | 464.2094 | 466.6174 | 495.1188 | 550.9607 | 466.6174 |
| 100,000 | Prim | 1000.8551 | 988.4304 | 802.8542 | 868.1307 | 1124.3591 | 988.4304 |

All warm-up and timed forests passed the independent checks. On these graphs,
Kruskal had the lower median at every size. Prim creates two adjacency entries
per non-loop edge and manages a lazy heap with stale entries, while Kruskal uses
Python's built-in sort and DSU; these implementation costs are a plausible
explanation for the measured difference. These observations are measurements,
not a proof of relative asymptotic growth: both implementations have the stated
`O(n + m log(m+1))` upper bound.

Limitations: only one generated graph per size and five timed repetitions were
measured, on a general-purpose laptop without CPU affinity or clock control.
Background activity, garbage collection, cache behaviour, and frequency changes
can affect timings. The graphs are sparse and connected with a planted negative tree and
nonnegative extra edges, not a representative sample of every graph or weight
distribution; the largest graph also has a different edge-to-vertex ratio.
Results cannot establish that Kruskal always beats Prim, and they do not include
JSON transport costs or measure peak memory.

## Sources, assistance, and verification

The task contract, required algorithms, examples, and public checking tools come
from the supplied [course template](https://github.com/RZhaniya/daa-assignment-3-graphs)
and `docs/Assignment_3_EN.pdf`. The unchanged starter provides JSON input/output.
No third-party graph library or prewritten graph implementation is used.

**AI assistance:** OpenAI Codex assisted with implementing the algorithms and
route helper, writing the independent tests and benchmark, and drafting this
analysis. Codex executed the reported checks and measurements in the local
environment. The recorded outputs are actual executions, not invented timings
or assumed passes. This statement does not claim that the student independently
performed those executions or manually reviewed every line. The submitted work
must still be understood and checked by the student under the course syllabus.

Passing public checks demonstrates the published cases, not a guaranteed grade
or completion of the separate defence quiz. Exact executed commands and outputs
are retained under `tests/`; benchmark values above match the stored JSON report.
