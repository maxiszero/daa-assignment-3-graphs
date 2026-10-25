import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;

/**
 * Provided JSON input/output for the assignment's integer-valued requests.
 * Use this parser as supplied; you do not need to implement or modify it.
 * Use Input.java to obtain numbers and arrays in Algorithms.java.
 */
final class Json {
    private final String text;
    private int position;

    private Json(String text) {
        this.text = text;
        this.position = 0;
    }

    static Object parse(String text) {
        return new Json(text).readValue();
    }

    @SuppressWarnings("unchecked")
    static Map<String, Object> parseRequest(String line) {
        return (Map<String, Object>) parse(line);
    }

    private void skipWhitespace() {
        while (position < text.length()
                && Character.isWhitespace(text.charAt(position))) {
            position++;
        }
    }

    private Object readValue() {
        skipWhitespace();
        char current = text.charAt(position);

        if (current == '"') {
            return readString();
        }
        if (current == '{') {
            return readObject();
        }
        if (current == '[') {
            return readArray();
        }
        if (text.startsWith("null", position)) {
            position += 4;
            return null;
        }
        if (text.startsWith("true", position)) {
            position += 4;
            return true;
        }
        if (text.startsWith("false", position)) {
            position += 5;
            return false;
        }

        int start = position;
        if (current == '-') {
            position++;
        }
        while (position < text.length()
                && Character.isDigit(text.charAt(position))) {
            position++;
        }
        return Long.parseLong(text.substring(start, position));
    }

    private Map<String, Object> readObject() {
        position++; // Opening brace.
        Map<String, Object> result = new LinkedHashMap<>();
        skipWhitespace();
        if (text.charAt(position) == '}') {
            position++;
            return result;
        }

        while (true) {
            String key = readString();
            skipWhitespace();
            position++; // Colon.
            result.put(key, readValue());
            skipWhitespace();

            char separator = text.charAt(position++);
            if (separator == '}') {
                return result;
            }
            skipWhitespace(); // After the comma.
        }
    }

    private List<Object> readArray() {
        position++; // Opening bracket.
        List<Object> result = new ArrayList<>();
        skipWhitespace();
        if (text.charAt(position) == ']') {
            position++;
            return result;
        }

        while (true) {
            result.add(readValue());
            skipWhitespace();
            char separator = text.charAt(position++);
            if (separator == ']') {
                return result;
            }
        }
    }

    private String readString() {
        skipWhitespace();
        position++; // Opening quote.
        StringBuilder result = new StringBuilder();

        while (true) {
            char current = text.charAt(position++);
            if (current == '"') {
                return result.toString();
            }
            if (current == '\\') {
                current = text.charAt(position++);
                switch (current) {
                    case 'n':
                        current = '\n';
                        break;
                    case 'r':
                        current = '\r';
                        break;
                    case 't':
                        current = '\t';
                        break;
                    case 'b':
                        current = '\b';
                        break;
                    case 'f':
                        current = '\f';
                        break;
                    case 'u':
                        current = (char) Integer.parseInt(
                                text.substring(position, position + 4), 16);
                        position += 4;
                        break;
                    default:
                        // Escaped quote, backslash or slash.
                        break;
                }
            }
            result.append(current);
        }
    }

    static String write(Object value) {
        if (value == null) {
            return "null";
        }
        if (value instanceof String) {
            return writeString((String) value);
        }
        if (value instanceof Map) {
            StringJoiner fields = new StringJoiner(",", "{", "}");
            for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                fields.add(writeString(entry.getKey().toString())
                        + ":" + write(entry.getValue()));
            }
            return fields.toString();
        }
        if (value instanceof Iterable) {
            StringJoiner elements = new StringJoiner(",", "[", "]");
            for (Object element : (Iterable<?>) value) {
                elements.add(write(element));
            }
            return elements.toString();
        }
        if (value.getClass().isArray()) {
            return writeArray(value);
        }
        return value.toString();
    }

    private static String writeString(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (char current : value.toCharArray()) {
            if (current == '"' || current == '\\') {
                result.append('\\').append(current);
            } else if (current < 32) {
                result.append(String.format("\\u%04x", (int) current));
            } else {
                result.append(current);
            }
        }
        return result.append('"').toString();
    }

    private static String writeArray(Object value) {
        // Internal transport detail: handles primitive and nested Java arrays.
        StringJoiner elements = new StringJoiner(",", "[", "]");
        int length = java.lang.reflect.Array.getLength(value);
        for (int i = 0; i < length; i++) {
            elements.add(write(java.lang.reflect.Array.get(value, i)));
        }
        return elements.toString();
    }
}
