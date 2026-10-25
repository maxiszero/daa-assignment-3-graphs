# Regression checks for supplied entry points and input helpers, not graph solutions.
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import run

ROOT = Path(__file__).resolve().parents[1]
TASKS = ('dsu', 'kruskal', 'prim', 'scc', 'topo', 'dag')
HAS_DOTNET_SDK = bool(shutil.which('dotnet') and subprocess.run(
    ['dotnet', '--list-sdks'], capture_output=True, text=True).stdout.strip())


class StarterTransportTests(unittest.TestCase):
    def copy_sources(self, language, target, names):
        for name in names:
            shutil.copyfile(ROOT / 'src' / language / name, target / name)

    def verify_transport(self, command):
        requests = [case['input'] for case in json.loads(
            (ROOT / 'tools/public.json').read_text(encoding='utf-8'))]
        unicode_request = {
            'task': 'dsu', 'n': 0, 'operations': [],
            'note': 'Қазақша русский café 🎓\n\t\b\f\r"\\',
        }
        requests.append(unicode_request)
        answers = run.execute(command, requests * 2)
        for request, answer in zip(requests * 2, answers):
            with self.subTest(task=request['task']):
                if request['task'] == 'ping':
                    self.assertEqual(answer, {'status': 'ready'})
                    continue
                self.assertEqual(answer['original'], request)
                self.assertEqual(answer['n'], request['n'])
                self.assertEqual(answer['rows'], request.get('operations', request.get('edges')))
                self.assertEqual(answer['distance'], [0, None, -1, 3000000000])
                self.assertEqual(answer['flags'], [True, False])
                if request['task'] == 'dag':
                    self.assertEqual(answer['source'], request['source'])
        # Also send literal UTF-8 instead of json.dumps' default Unicode escapes.
        result = subprocess.run(command, input=json.dumps(unicode_request, ensure_ascii=False) + '\n',
                                capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['original'], unicode_request)

    def test_python_entry_point(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.copy_sources('Python', target, ['main.py'])
            # Temporary echo methods isolate the framework from unfinished algorithm bodies.
            source = '''def echo(request):
    result = {"original": request, "n": request["n"],
              "rows": request.get("operations", request.get("edges")),
              "distance": [0, None, -1, 3000000000], "flags": [True, False]}
    if request["task"] == "dag":
        result["source"] = request["source"]
    return result
'''
            source += '\n'.join(name + ' = echo' for name in TASKS)
            (target / 'algorithms.py').write_text(source, encoding='utf-8')
            self.verify_transport([sys.executable, str(target / 'main.py')])

    @unittest.skipUnless(shutil.which('g++'), 'C++ compiler not installed')
    def test_cpp_input_helpers_and_entry_point(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.copy_sources('Cpp', target, ['main.cpp', 'json.hpp', 'input.hpp'])
            source = r'''#pragma once
#include "input.hpp"
inline J echo(const J& request) {
    vector<vector<int>> inputRows = request["task"].text() == "dsu"
        ? Input::operations(request) : Input::edges(request);
    J::A rows;
    for (const vector<int>& inputRow : inputRows) {
        J::A row;
        for (int item : inputRow) row.push_back(item);
        rows.push_back(row);
    }
    J result = J::O{{"original", request}, {"n", Input::vertexCount(request)},
        {"rows", rows}, {"distance", J::A{0LL, J(), -1LL, 3000000000LL}},
        {"flags", J::A{true, false}}};
    if (request["task"].text() == "dag") result["source"] = Input::source(request);
    return result;
}
'''
            source += '\n'.join('inline J ' + name + '(const J& x){return echo(x);}' for name in TASKS)
            (target / 'algorithms.hpp').write_text(source, encoding='utf-8')
            binary = target / ('probe.exe' if sys.platform == 'win32' else 'probe')
            build = subprocess.run(['g++', '-std=c++17', '-O2', str(target / 'main.cpp'),
                                    '-o', str(binary)], capture_output=True, text=True,
                                   encoding='utf-8', timeout=60)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.verify_transport([str(binary)])

    @unittest.skipUnless(HAS_DOTNET_SDK, '.NET SDK is not installed')
    def test_csharp_input_helpers_and_entry_point(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            self.copy_sources('CSharp', target, ['Program.cs', 'Input.cs', 'App.csproj'])
            source = r'''using System.Text.Json;
using System.Text.Json.Nodes;
public static class Algorithms {
    private static JsonObject Echo(JsonObject request) {
        int[][] rows = request["task"]!.GetValue<string>() == "dsu"
            ? Input.Operations(request) : Input.Edges(request);
        var result = new JsonObject {
            ["original"] = request.DeepClone(), ["n"] = Input.VertexCount(request),
            ["rows"] = JsonSerializer.SerializeToNode(rows),
            ["distance"] = JsonSerializer.SerializeToNode(new long?[]{0, null, -1, 3000000000L}),
            ["flags"] = JsonSerializer.SerializeToNode(new bool[]{true, false})
        };
        if (request["task"]!.GetValue<string>() == "dag") result["source"] = Input.Source(request);
        return result;
    }
'''
            source += '\n'.join('public static JsonObject ' + name
                                + '(JsonObject x){return Echo(x);}' for name in TASKS) + '\n}'
            (target / 'Algorithms.cs').write_text(source, encoding='utf-8')
            output = target / 'build'
            build = subprocess.run(['dotnet', 'build', str(target / 'App.csproj'), '--nologo',
                                    '-o', str(output)], capture_output=True, text=True,
                                   encoding='utf-8', timeout=60)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.verify_transport(['dotnet', str(output / 'App.dll')])


if __name__ == '__main__':
    unittest.main()
