using System.Text.Json.Nodes;

// Implement the six methods and your route helper. See the README at the repository root.
public static class Algorithms
{
    // DSU with path compression and union by size/rank; return states.
    public static JsonObject dsu(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int[][] operations = Input.Operations(input);

        throw new NotImplementedException("TODO dsu");
    }

    // Separate Kruskal implementation; return cost, edge_ids, components.
    public static JsonObject kruskal(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int[][] edges = Input.Edges(input);

        throw new NotImplementedException("TODO kruskal");
    }

    // Separate Prim implementation; restart for every unvisited component.
    public static JsonObject prim(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int[][] edges = Input.Edges(input);

        throw new NotImplementedException("TODO prim");
    }

    // Kosaraju with two DFS passes; return component and condensation.
    public static JsonObject scc(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int[][] edges = Input.Edges(input);

        throw new NotImplementedException("TODO scc");
    }

    // Three-state DFS and reverse finish order; return acyclic and order.
    public static JsonObject topo(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int[][] edges = Input.Edges(input);

        throw new NotImplementedException("TODO topo");
    }

    // Whole-graph cycle check and DAG relaxation; add your own route helper.
    public static JsonObject dag(JsonObject input)
    {
        int n = Input.VertexCount(input);
        int source = Input.Source(input);
        int[][] edges = Input.Edges(input);

        throw new NotImplementedException("TODO dag");
    }
}
