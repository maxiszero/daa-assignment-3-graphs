#pragma once
#include "input.hpp"

// Implement the six graph methods and your route helper. See the README at the repository root.

// DSU with path compression and union by size/rank; return states.
inline J dsu(const J& input) {
    int n = Input::vertexCount(input);
    vector<vector<int>> operations = Input::operations(input);

    throw runtime_error("TODO dsu");
}

// Separate Kruskal implementation; return cost, edge_ids, components.
inline J kruskal(const J& input) {
    int n = Input::vertexCount(input);
    vector<vector<int>> edges = Input::edges(input);

    throw runtime_error("TODO kruskal");
}

// Separate Prim implementation; restart for every unvisited component.
inline J prim(const J& input) {
    int n = Input::vertexCount(input);
    vector<vector<int>> edges = Input::edges(input);

    throw runtime_error("TODO prim");
}

// Kosaraju with two DFS passes; return component and condensation.
inline J scc(const J& input) {
    int n = Input::vertexCount(input);
    vector<vector<int>> edges = Input::edges(input);

    throw runtime_error("TODO scc");
}

// Three-state DFS and reverse finish order; return acyclic and order.
inline J topo(const J& input) {
    int n = Input::vertexCount(input);
    vector<vector<int>> edges = Input::edges(input);

    throw runtime_error("TODO topo");
}

// Whole-graph cycle check and DAG relaxation; add your own route helper.
inline J dag(const J& input) {
    int n = Input::vertexCount(input);
    int source = Input::source(input);
    vector<vector<int>> edges = Input::edges(input);

    throw runtime_error("TODO dag");
}
