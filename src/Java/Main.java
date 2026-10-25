import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** Provided program entry point. Implement your graph methods in Algorithms.java. */
public final class Main {
    private static Map<String, Object> handle(Map<String, Object> request) {
        String task = (String) request.get("task");

        switch (task) {
            case "ping":
                return Map.of("status", "ready");
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
                throw new IllegalArgumentException("Unknown task: " + task);
        }
    }

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        PrintWriter writer = new PrintWriter(
                new OutputStreamWriter(System.out, StandardCharsets.UTF_8), true);

        String line;
        while ((line = reader.readLine()) != null) {
            Map<String, Object> request = Json.parseRequest(line);
            try {
                writer.println(Json.write(handle(request)));
            } catch (UnsupportedOperationException error) {
                // Keep the JSON Lines protocol while a method still has its TODO.
                writer.println(Json.write(Map.of("error", error.getMessage())));
            }
        }
    }
}
