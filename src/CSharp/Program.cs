using System.Text;
using System.Text.Json.Nodes;

// Use this supplied entry point. Implement your algorithms in Algorithms.cs.
public static class Program
{
    private static JsonObject Handle(JsonObject request)
    {
        string task = request["task"]!.GetValue<string>();
        switch (task)
        {
            case "ping":
                return new JsonObject { ["status"] = "ready" };
            case "dsu":
                return Algorithms.dsu(request);
            case "kruskal":
                return Algorithms.kruskal(request);
            case "prim":
                return Algorithms.prim(request);
            case "scc":
                return Algorithms.scc(request);
            case "topo":
                return Algorithms.topo(request);
            case "dag":
                return Algorithms.dag(request);
            default:
                throw new ArgumentException("Unknown task: " + task);
        }
    }

    public static void Main()
    {
        Console.InputEncoding = Encoding.UTF8;
        Console.OutputEncoding = new UTF8Encoding(false);
        string? line;
        while ((line = Console.ReadLine()) != null)
        {
            JsonObject request = JsonNode.Parse(line)!.AsObject();
            try
            {
                Console.WriteLine(Handle(request).ToJsonString());
            }
            catch (NotImplementedException error)
            {
                JsonObject result = new JsonObject { ["error"] = error.Message };
                Console.WriteLine(result.ToJsonString());
            }
        }
    }
}
