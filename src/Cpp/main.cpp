#include "algorithms.hpp"

// Use this supplied entry point. Implement your algorithms in algorithms.hpp.
J handle(const J& request) {
    string task = request["task"].text();
    if (task == "ping") {
        return J::O{{"status", "ready"}};
    }
    if (task == "dsu") {
        return dsu(request);
    }
    if (task == "kruskal") {
        return kruskal(request);
    }
    if (task == "prim") {
        return prim(request);
    }
    if (task == "scc") {
        return scc(request);
    }
    if (task == "topo") {
        return topo(request);
    }
    if (task == "dag") {
        return dag(request);
    }
    throw runtime_error("Unknown task: " + task);
}

int main() {
    string line;
    while (getline(cin, line)) {
        try {
            J request = J::parse(line);
            cout << handle(request).dump() << "\n";
        } catch (const exception& error) {
            cout << J(J::O{{"error", error.what()}}).dump() << "\n";
        }
    }
}
