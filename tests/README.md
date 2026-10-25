# Own verification

Run from the repository root with Python 3.12+; no third-party packages are required.

```sh
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tests -p "test_algorithms.py" -v
python tests/capture_evidence.py
python tests/scale_transport.py
python tools/run.py --input tests/my_cases.jsonl
python tests/benchmark.py
```

`capture_evidence.py` runs 19 stored JSONL cases through the supplied entry point,
checks the actual answers semantically, writes the input/expected/actual files,
and runs the 26-method own unittest suite, saving its real output to
`test_results.txt`. `scale_transport.py` separately runs all six tasks at the full
published limits in one process, with a 20-second timeout, and saves its compact
actual-output summaries and hashes. `tools/run.py --input` only prints results;
it does not compare expected answers.

## Files and expected answers

- `cases.json`: 19 small requests, independently justified expected answers, and
  a `why` explanation for each. Expected witnesses are examples, not mandatory
  output orderings or tie choices.
- `my_cases.jsonl`: the same requests in the required JSON Lines format.
- `expected_outputs.jsonl`: the independently justified example answers.
- `actual_outputs.jsonl`: actual output captured from `src/Python/main.py`.
- `test_algorithms.py`: deterministic randomized oracle comparisons, semantic
  witness checks, transport/state reset and scale tests.
- `test_results.txt`: actual environment, test names and results from the last
  evidence-capture run.
- `public_check_results.txt`: actual successful setup, all 36 public cases, and
  the repeated-batch state-reset check from the supplied launcher.
- `scale_transport.py`, `scale_transport_results.json`: full-limit JSONL batch
  generator and the saved successful subprocess result; large transient inputs
  and outputs are represented by SHA-256 hashes and compact summaries.
- `benchmark.py`, `benchmark_results.json`: reproducible benchmark and its real
  timing/route-helper evidence; details are in the root `ANALYSIS.md`.

The supplied `tools/public_validate.py` validates witnesses against independently
computed expected values. It checks forest edge IDs, cost, acyclicity and spanning;
equivalent SCC partitions and exactly deduplicated condensation; topological
precedence; and shortest distances with correctly directed parent-edge paths.
We do not compare a potentially non-unique witness byte-for-byte.

## Independent oracle design

- DSU: explicitly merge sets on small inputs; count sets and their maximum size.
- Minimum spanning forests: enumerate all subsets with `n-c` edges, retain those
  connecting all original components, and minimize their total weight. This is
  exponential, deliberately limited to tiny graphs, and independent of both
  implemented greedy algorithms.
- SCC: Floyd-Warshall transitive closure defines components by mutual
  reachability; no Kosaraju traversal is used by the oracle.
- Topological cycle detection: Kahn's indegree-elimination algorithm, independent
  of the implementation's DFS states.
- DAG distances: repeated Bellman-Ford relaxation on generated DAGs, independent
  of topological-order relaxation. Vertex labels are shuffled and the source is
  randomized to avoid assuming vertex-number order is topological.
- Seeds `3101` through `3105` make the random inputs reproducible.

The witness-checker tests accept two valid forests, two different SCC labelings,
two topological orders and two shortest-path parent arrays. They reject repeated
or out-of-range forest edge IDs, a cyclic/incorrect-size forest, merged SCCs,
missing/duplicated condensation pairs, reversed precedence, duplicate vertices,
wrong parent direction, missing parents, nonempty source parents and wrong
distances. These tests establish that an alternate valid answer is accepted and
an invalid witness is rejected rather than trusted on cost alone.

## Full published limits

The suite constructs full-size inputs at run time rather than checking in large
data files. Every method is exercised with `n=100000`; DSU has `q=250000`, and
Kruskal, Prim, SCC, topo and DAG each have `m=250000`.

- DSU: a chain of `n-1` unions followed by repeated connections; after operation
  index `i`, the exact expected state is `[max(1,n-i-1), min(n,i+2)]`.
- Kruskal/Prim: a chain of weight `-10^9` edges plus repeated expensive endpoint
  edges. Every negative chain edge is necessary for the optimum
  `-(n-1)*10^9`; both witnesses are checked structurally.
- SCC/topo: a directed chain plus repeated forward endpoint edges. Every vertex
  is a separate SCC, and precedence forces chain order. A separate 100000-vertex
  directed cycle must form one SCC. These exercise deep DFS without recursion.
- DAG: the same long negative chain plus expensive forward endpoint edges.
  Distance to `v` is `-v*10^9`; the reconstructed route to the last vertex must
  equal all vertices in order. This checks a 99999-edge path and 64-bit-scale
  totals, with no recursive reconstruction.

`scale_transport.py` sends those six full-limit requests in one JSONL process,
including actual input parsing and output serialization. Semantic checks use
the closed-form expected values above. This is in addition to direct-call scale
tests, so both algorithm correctness and the production transport are exercised.
Its recorded elapsed time measures process launch, pipe input/output, parsing,
algorithms and output serialization; parent-side input generation and semantic
validation are outside that measurement. It is a limit check, not the
Kruskal-versus-Prim benchmark.

Small cases additionally cover empty graphs, isolates, disconnected components,
self/repeated unions, self-loops, parallel/tied edges, negative weights,
unreachable vertices, finite distance `-1`, and cycles unreachable from the
source. The mixed transport test sends the 19 requests three times (57 requests)
to one process, verifying one JSON result per request, preserved `ping`, empty
stderr and state reset.

## Route helper

The suite calls `reconstruct_path(source, target, parent_edge, edges)` for a
reachable target, the source and an unreachable vertex, and on tied/parallel
edges. The documented no-route result is `[]`; the source route is `[source]`.
Every returned route is checked against the selected original parent-edge IDs:
each edge must have the reported direction and the weights must sum to the
shortest distance. Actual helper call results and selected IDs are also captured
by the benchmark report.
