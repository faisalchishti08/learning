# Java 13 Features (2019)

Java 13 introduced text blocks (preview) and a few smaller improvements.

---

## 1. Text Blocks (Preview)

Multi-line strings without escape sequences. Finalized Java 15.

```java
public class TextBlocks13 {
    public static void main(String[] args) {
        // Before Java 13 — escapes, hard to read
        String json1 = "{\n" +
                       "    \"name\": \"Alice\",\n" +
                       "    \"age\": 30\n" +
                       "}";

        // Java 13+ text block — natural formatting
        String json2 = """
                {
                    "name": "Alice",
                    "age": 30
                }
                """;

        System.out.println(json2);
        // {
        //     "name": "Alice",
        //     "age": 30
        // }

        // HTML
        String html = """
                <html>
                    <body>
                        <h1>Hello</h1>
                    </body>
                </html>
                """;

        // SQL
        String sql = """
                SELECT u.name, o.total
                FROM users u
                JOIN orders o ON u.id = o.user_id
                WHERE u.active = true
                ORDER BY o.total DESC
                """;
        System.out.println(sql);
    }
}
```

### Indentation Rules

```java
// Leading whitespace is removed based on the closing """  position
String text = """
        line1
        line2
        """;
// line1
// line2
// (trailing newline included because """ is on its own line)

// Trailing """ position controls indentation strip
String noTrailingNewline = """
        hello"""; // no trailing newline
```

---

## 2. Switch Expressions — yield (Preview Enhancement)

Java 13 added the `yield` keyword for switch expressions.

```java
// Java 13: yield in switch blocks (was 'break value' in Java 12 preview)
String result = switch (42) {
    case 0 -> "zero";
    default -> {
        int half = 42 / 2;
        yield "half is " + half; // yield — return value from block
    }
};
System.out.println(result); // half is 21
```

---

## 3. Socket API Reimplementation

`java.net.Socket` and `java.net.ServerSocket` backed by new `NioSocketImpl` (replacing legacy `PlainSocketImpl`). No API changes — internal improvement for performance and virtual thread compatibility.

---

## Quick Reference

```
Java 13 key features:
  Text blocks (preview)     """ multi-line strings
  yield keyword (preview)   return value from switch block
  Socket reimplementation   NioSocketImpl (internal, no API change)
  Dynamic CDS archives      faster startup
  ZGC returns memory        ZGC now returns unused memory to OS
```
