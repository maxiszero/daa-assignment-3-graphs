#pragma once
#include <bits/stdc++.h>
using namespace std;

// Provided JSON transport for integer-valued assignment requests.
// Use input.hpp to read your inputs; no changes to this parser are required.
struct J {
    using A = vector<J>;
    using O = map<string, J>;
    variant<nullptr_t, bool, long long, string, A, O> v;

    J() : v(nullptr) {}
    J(bool value) : v(value) {}
    J(int value) : v(static_cast<long long>(value)) {}
    J(long long value) : v(value) {}
    J(string value) : v(std::move(value)) {}
    J(const char* value) : v(string(value)) {}
    J(A value) : v(std::move(value)) {}
    J(O value) : v(std::move(value)) {}

    J& operator[](const string& key) {
        if (!holds_alternative<O>(v)) {
            v = O{};
        }
        return get<O>(v)[key];
    }

    const J& operator[](const string& key) const {
        return get<O>(v).at(key);
    }

    long long number() const {
        return get<long long>(v);
    }

    string text() const {
        return get<string>(v);
    }

    const A& array() const {
        return get<A>(v);
    }

    static J parse(const string& text) {
        size_t position = 0;
        auto skipWhitespace = [&]() {
            while (position < text.size()
                    && isspace(static_cast<unsigned char>(text[position]))) {
                position++;
            }
        };

        auto appendUtf8 = [](string& result, unsigned int code) {
            if (code <= 0x7f) {
                result += static_cast<char>(code);
            } else if (code <= 0x7ff) {
                result += static_cast<char>(0xc0 | (code >> 6));
                result += static_cast<char>(0x80 | (code & 0x3f));
            } else if (code <= 0xffff) {
                result += static_cast<char>(0xe0 | (code >> 12));
                result += static_cast<char>(0x80 | ((code >> 6) & 0x3f));
                result += static_cast<char>(0x80 | (code & 0x3f));
            } else {
                result += static_cast<char>(0xf0 | (code >> 18));
                result += static_cast<char>(0x80 | ((code >> 12) & 0x3f));
                result += static_cast<char>(0x80 | ((code >> 6) & 0x3f));
                result += static_cast<char>(0x80 | (code & 0x3f));
            }
        };

        auto readString = [&]() -> string {
            skipWhitespace();
            position++; // Opening quote.
            string result;
            while (true) {
                char current = text.at(position++);
                if (current == '"') {
                    return result;
                }
                if (current != '\\') {
                    result += current;
                    continue;
                }
                current = text.at(position++);
                switch (current) {
                    case 'n': result += '\n'; break;
                    case 'r': result += '\r'; break;
                    case 't': result += '\t'; break;
                    case 'b': result += '\b'; break;
                    case 'f': result += '\f'; break;
                    case 'u': {
                        unsigned int code = stoul(text.substr(position, 4), nullptr, 16);
                        position += 4;
                        if (code >= 0xd800 && code <= 0xdbff
                                && text.compare(position, 2, "\\u") == 0) {
                            unsigned int low = stoul(text.substr(position + 2, 4), nullptr, 16);
                            if (low >= 0xdc00 && low <= 0xdfff) {
                                position += 6;
                                code = 0x10000 + ((code - 0xd800) << 10) + (low - 0xdc00);
                            }
                        }
                        appendUtf8(result, code);
                        break;
                    }
                    default:
                        result += current; // Escaped quote, slash or backslash.
                        break;
                }
            }
        };

        function<J()> readValue;
        readValue = [&]() -> J {
            skipWhitespace();
            char current = text.at(position);
            if (current == '"') {
                return J(readString());
            }
            if (current == '{') {
                position++;
                O result;
                skipWhitespace();
                if (text.at(position) == '}') {
                    position++;
                    return J(result);
                }
                while (true) {
                    string key = readString();
                    skipWhitespace();
                    position++; // Colon.
                    result[key] = readValue();
                    skipWhitespace();
                    if (text.at(position++) == '}') {
                        return J(result);
                    }
                }
            }
            if (current == '[') {
                position++;
                A result;
                skipWhitespace();
                if (text.at(position) == ']') {
                    position++;
                    return J(result);
                }
                while (true) {
                    result.push_back(readValue());
                    skipWhitespace();
                    if (text.at(position++) == ']') {
                        return J(result);
                    }
                }
            }
            if (text.compare(position, 4, "null") == 0) {
                position += 4;
                return J();
            }
            if (text.compare(position, 4, "true") == 0) {
                position += 4;
                return J(true);
            }
            if (text.compare(position, 5, "false") == 0) {
                position += 5;
                return J(false);
            }
            size_t start = position;
            if (text.at(position) == '-') {
                position++;
            }
            while (position < text.size()
                    && isdigit(static_cast<unsigned char>(text[position]))) {
                position++;
            }
            return J(stoll(text.substr(start, position - start)));
        };
        return readValue();
    }

    string dump() const {
        if (holds_alternative<nullptr_t>(v)) {
            return "null";
        }
        if (holds_alternative<bool>(v)) {
            return get<bool>(v) ? "true" : "false";
        }
        if (holds_alternative<long long>(v)) {
            return to_string(number());
        }
        if (holds_alternative<string>(v)) {
            string result = "\"";
            for (unsigned char current : text()) {
                if (current == '"' || current == '\\') {
                    result += '\\';
                    result += static_cast<char>(current);
                } else if (current < 32) {
                    char escape[7];
                    snprintf(escape, sizeof(escape), "\\u%04x", static_cast<unsigned int>(current));
                    result += escape;
                } else {
                    result += static_cast<char>(current);
                }
            }
            return result + '"';
        }

        bool first = true;
        if (holds_alternative<A>(v)) {
            string result = "[";
            for (const J& item : array()) {
                if (!first) result += ',';
                first = false;
                result += item.dump();
            }
            return result + ']';
        }

        string result = "{";
        for (const auto& item : get<O>(v)) {
            if (!first) result += ',';
            first = false;
            result += J(item.first).dump() + ':' + item.second.dump();
        }
        return result + '}';
    }
};
