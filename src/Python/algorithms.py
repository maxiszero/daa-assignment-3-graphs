"""Graph algorithms for the supplied JSON Lines interface.

All state is local to one request. DFS uses explicit stacks so a chain of
100,000 vertices does not depend on Python's recursion limit.
"""

from heapq import heappop, heappush


class _DSU:
    """Disjoint sets with iterative path compression and union by size."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n else 0

    def find(self, vertex):
        root = vertex
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[vertex] != vertex:
            next_vertex = self.parent[vertex]
            self.parent[vertex] = root
            vertex = next_vertex
        return root

    def union(self, u, v):
        u, v = self.find(u), self.find(v)
        if u == v:
            return False
        if self.size[u] < self.size[v]:
            u, v = v, u
        self.parent[v] = u
        self.size[u] += self.size[v]
        self.components -= 1
        self.largest = max(self.largest, self.size[u])
        return True


def dsu(request):
    """Return component count and largest component after every union."""
    sets = _DSU(request["n"])
    states = []
    for u, v in request["operations"]:
        sets.union(u, v)
        states.append([sets.components, sets.largest])
    return {"states": states}


def kruskal(request):
    """Sort original edge IDs by weight and accept only component joins."""
    edges = request["edges"]
    sets = _DSU(request["n"])
    selected = []
    cost = 0
    for edge_id in sorted(range(len(edges)), key=lambda i: edges[i][2]):
        u, v, weight = edges[edge_id]
        if sets.union(u, v):
            selected.append(edge_id)
            cost += weight
    return {"cost": cost, "edge_ids": selected, "components": sets.components}


def prim(request):
    """Grow every component using its cheapest crossing edge in a lazy heap."""
    n = request["n"]
    adjacency = [[] for _ in range(n)]
    for edge_id, (u, v, weight) in enumerate(request["edges"]):
        if u != v:
            adjacency[u].append((weight, edge_id, v))
            adjacency[v].append((weight, edge_id, u))

    visited = bytearray(n)
    selected = []
    cost = components = 0
    for root in range(n):
        if visited[root]:
            continue
        components += 1
        visited[root] = 1
        heap = []
        for edge in adjacency[root]:
            if not visited[edge[2]]:
                heappush(heap, edge)
        while heap:
            weight, edge_id, vertex = heappop(heap)
            if visited[vertex]:
                continue
            visited[vertex] = 1
            selected.append(edge_id)
            cost += weight
            for edge in adjacency[vertex]:
                if not visited[edge[2]]:
                    heappush(heap, edge)
    return {"cost": cost, "edge_ids": selected, "components": components}


def _finish_order(adjacency, detect_cycles):
    """Return DFS finish order, or None for a cycle when detection is enabled.

    A frame [vertex, next_neighbour] preserves traversal progress. Colours are
    0 (unvisited), 1 (active), and 2 (finished).
    """
    colour = bytearray(len(adjacency))
    finished = []
    for root in range(len(adjacency)):
        if colour[root]:
            continue
        colour[root] = 1
        stack = [[root, 0]]
        while stack:
            vertex, next_neighbour = stack[-1]
            if next_neighbour == len(adjacency[vertex]):
                stack.pop()
                colour[vertex] = 2
                finished.append(vertex)
                continue
            neighbour = adjacency[vertex][next_neighbour]
            stack[-1][1] += 1
            if colour[neighbour] == 0:
                colour[neighbour] = 1
                stack.append([neighbour, 0])
            elif detect_cycles and colour[neighbour] == 1:
                return None
    return finished


def scc(request):
    """Kosaraju: finish order on the graph, then DFS on its transpose."""
    n = request["n"]
    edges = request["edges"]
    adjacency = [[] for _ in range(n)]
    transpose = [[] for _ in range(n)]
    for u, v in edges:
        adjacency[u].append(v)
        transpose[v].append(u)
    finished = _finish_order(adjacency, detect_cycles=False)
    component = [-1] * n
    label = 0
    for root in reversed(finished):
        if component[root] != -1:
            continue
        component[root] = label
        stack = [root]
        while stack:
            vertex = stack.pop()
            for neighbour in transpose[vertex]:
                if component[neighbour] == -1:
                    component[neighbour] = label
                    stack.append(neighbour)
        label += 1
    pairs = set()
    condensation = []
    for u, v in edges:
        pair = (component[u], component[v])
        if pair[0] != pair[1] and pair not in pairs:
            pairs.add(pair)
            condensation.append(list(pair))
    return {"component": component, "condensation": condensation}


def topo(request):
    """Check all components with three-state DFS, then reverse finish order."""
    adjacency = [[] for _ in range(request["n"])]
    for u, v in request["edges"]:
        adjacency[u].append(v)
    finished = _finish_order(adjacency, detect_cycles=True)
    if finished is None:
        return {"acyclic": False, "order": []}
    finished.reverse()
    return {"acyclic": True, "order": finished}


def dag(request):
    """Reject cycles anywhere, then relax reachable vertices in DFS order."""
    n = request["n"]
    source = request["source"]
    edges = request["edges"]
    adjacency = [[] for _ in range(n)]
    outgoing = [[] for _ in range(n)]
    for edge_id, (u, v, weight) in enumerate(edges):
        adjacency[u].append(v)
        outgoing[u].append(edge_id)
    finished = _finish_order(adjacency, detect_cycles=True)
    if finished is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    distance = [None] * n
    parent_edge = [-1] * n
    distance[source] = 0
    for u in reversed(finished):
        if distance[u] is None:
            continue
        for edge_id in outgoing[u]:
            _, v, weight = edges[edge_id]
            candidate = distance[u] + weight
            if distance[v] is None or candidate < distance[v]:
                distance[v] = candidate
                parent_edge[v] = edge_id
    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


def reconstruct_path(source, target, parent_edge, edges):
    """Return source-to-target vertices, [] if unreachable, [source] at source.

    Parent entries are original edge IDs from a successful DAG result. The
    helper also rejects malformed or cyclic parent witnesses with ValueError.
    It takes O(L) time and space for a route containing L vertices.
    """
    path = []
    vertex = target
    while vertex != source:
        if not 0 <= vertex < len(parent_edge):
            raise ValueError("Parent path contains an invalid vertex")
        edge_id = parent_edge[vertex]
        if edge_id == -1:
            return []
        if not 0 <= edge_id < len(edges):
            raise ValueError("Parent path contains an invalid edge ID")
        u, v, _ = edges[edge_id]
        if v != vertex:
            raise ValueError("Parent edge does not end at the current vertex")
        path.append(vertex)
        if len(path) >= len(parent_edge):
            raise ValueError("Parent path contains a cycle")
        vertex = u
    path.append(source)
    path.reverse()
    return path
