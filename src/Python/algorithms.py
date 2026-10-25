"""Implement the six graph methods and your route helper. See the README at the repository root."""


def dsu(request):
    """DSU with path compression and union by size/rank; return states."""
    n = request["n"]
    operations = request["operations"]

    raise NotImplementedError("TODO dsu")


def kruskal(request):
    """Separate Kruskal implementation; return cost, edge_ids, components."""
    n = request["n"]
    edges = request["edges"]

    raise NotImplementedError("TODO kruskal")


def prim(request):
    """Separate Prim implementation; restart for every unvisited component."""
    n = request["n"]
    edges = request["edges"]

    raise NotImplementedError("TODO prim")


def scc(request):
    """Kosaraju with two DFS passes; return component and condensation."""
    n = request["n"]
    edges = request["edges"]

    raise NotImplementedError("TODO scc")


def topo(request):
    """Three-state DFS and reverse finish order; return acyclic and order."""
    n = request["n"]
    edges = request["edges"]

    raise NotImplementedError("TODO topo")


def dag(request):
    """Whole-graph cycle check and DAG relaxation; add your own route helper."""
    n = request["n"]
    source = request["source"]
    edges = request["edges"]

    raise NotImplementedError("TODO dag")
