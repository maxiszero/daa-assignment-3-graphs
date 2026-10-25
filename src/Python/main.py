"""Use this supplied JSON Lines entry point. Implement your algorithms in algorithms.py."""

import json
import sys

import algorithms


def handle(request):
    task = request["task"]
    if task == "ping":
        return {"status": "ready"}
    if task == "dsu":
        return algorithms.dsu(request)
    if task == "kruskal":
        return algorithms.kruskal(request)
    if task == "prim":
        return algorithms.prim(request)
    if task == "scc":
        return algorithms.scc(request)
    if task == "topo":
        return algorithms.topo(request)
    if task == "dag":
        return algorithms.dag(request)
    raise ValueError("Unknown task: " + task)


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    for line in sys.stdin:
        request = json.loads(line)
        try:
            result = handle(request)
        except NotImplementedError as error:
            result = {"error": str(error)}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
