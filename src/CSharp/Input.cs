using System.Text.Json.Nodes;

// Use these supplied input helpers; no changes are required.
public static class Input
{
    public static int VertexCount(JsonObject request)
    {
        return request["n"]!.GetValue<int>();
    }

    public static int Source(JsonObject request)
    {
        return request["source"]!.GetValue<int>();
    }

    public static int[][] Operations(JsonObject request)
    {
        return Rows(request["operations"]!.AsArray());
    }

    public static int[][] Edges(JsonObject request)
    {
        return Rows(request["edges"]!.AsArray());
    }

    private static int[][] Rows(JsonArray rows)
    {
        int[][] result = new int[rows.Count][];
        for (int i = 0; i < rows.Count; i++)
        {
            JsonArray row = rows[i]!.AsArray();
            result[i] = new int[row.Count];
            for (int j = 0; j < row.Count; j++)
            {
                // All input endpoints, weights, n and source fit int.
                result[i][j] = row[j]!.GetValue<int>();
            }
        }
        return result;
    }
}
