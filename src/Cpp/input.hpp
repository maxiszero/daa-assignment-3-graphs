#pragma once
#include "json.hpp"

// Use these supplied JSON-to-int/vector helpers; no changes are required.
namespace Input {
    inline int vertexCount(const J& request) {
        return static_cast<int>(request["n"].number());
    }

    inline int source(const J& request) {
        return static_cast<int>(request["source"].number());
    }

    inline vector<vector<int>> rows(const J& value) {
        vector<vector<int>> result;
        result.reserve(value.array().size());
        for (const J& inputRow : value.array()) {
            vector<int> row;
            row.reserve(inputRow.array().size());
            for (const J& item : inputRow.array()) {
                // Every individual endpoint and weight fits int.
                row.push_back(static_cast<int>(item.number()));
            }
            result.push_back(std::move(row));
        }
        return result;
    }

    inline vector<vector<int>> operations(const J& request) {
        return rows(request["operations"]);
    }

    inline vector<vector<int>> edges(const J& request) {
        return rows(request["edges"]);
    }
}
