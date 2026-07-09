---
card: java
gi: 677
slug: text-blocks-standardized
title: Text blocks — standardized
---

## 1. What it is

**Text blocks**, previewed twice (Java 13 and 14), became a **standard, permanent language feature** in **Java 15** (JEP 378). A text block is a multi-line string literal delimited by triple double-quotes (`"""`) that lets you write multi-line text — JSON, SQL, HTML, plain paragraphs — without escaping every internal quote or manually inserting `\n` at each line break. The compiler strips a common leading-whitespace margin (based on the least-indented non-blank line, including the closing `"""`) and normalizes line terminators, giving you a literal that looks on the page exactly like the text it represents.

## 2. Why & when

Before text blocks, embedding a multi-line SQL query or a JSON payload in Java source meant a wall of `"...\n" + "...\n" +` concatenation with escaped quotes throughout — hard to read, easy to introduce a subtle formatting bug in, and painful to diff when the content changed. Text blocks exist because readability of embedded structured or semi-structured text (queries, markup, request bodies in tests) matters for maintainability, and the two-preview cycle (13, then 14 with minor escape-sequence additions) gave the language committee time to settle the indentation-stripping and escaping rules based on real feedback before locking them in permanently in Java 15. Reach for a text block whenever you're writing a Java string literal that spans more than one line or that contains many double quotes — SQL statements, JSON/XML samples in tests, HTML snippets, usage/help text — since Java 15 onward it requires no preview flag at all.

## 3. Core concept

```java
// Before text blocks
String json = "{\n" +
              "  \"name\": \"Ada\",\n" +
              "  \"role\": \"engineer\"\n" +
              "}\n";

// With a standardized text block (Java 15+, no preview flag needed)
String json = """
              {
                "name": "Ada",
                "role": "engineer"
              }
              """;
```

The compiler determines the *incidental* leading whitespace shared by every line (including the line holding the closing `"""`) and strips exactly that much from each line, so you can indent the whole block to match your code's nesting without that indentation leaking into the string's actual content.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Source text block with common indentation is stripped by the compiler to produce the final string value">
  <rect x="20" y="20" width="280" height="180" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Source (indented to match code)</text>
  <text x="35" y="70" fill="#8b949e" font-size="11" font-family="monospace">    """</text>
  <text x="35" y="90" fill="#e6edf3" font-size="11" font-family="monospace">    {</text>
  <text x="35" y="110" fill="#e6edf3" font-size="11" font-family="monospace">      "name": "Ada"</text>
  <text x="35" y="130" fill="#e6edf3" font-size="11" font-family="monospace">    }</text>
  <text x="35" y="150" fill="#8b949e" font-size="11" font-family="monospace">    """</text>

  <line x1="300" y1="110" x2="340" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <text x="320" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">strip margin</text>

  <rect x="350" y="20" width="270" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="485" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Resulting String value</text>
  <text x="365" y="70" fill="#e6edf3" font-size="11" font-family="monospace">{</text>
  <text x="365" y="90" fill="#e6edf3" font-size="11" font-family="monospace">  "name": "Ada"</text>
  <text x="365" y="110" fill="#e6edf3" font-size="11" font-family="monospace">}</text>

  <defs>
    <marker id="arr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The closing `"""`'s column sets the margin that gets removed from every line, so source indentation and string content are independent.

## 5. Runnable example

Scenario: building a small "user profile" JSON generator — starting with plain concatenation replaced by a text block, then parameterizing it with `String.formatted()`, then assembling a multi-record report that also embeds a SQL query, exercising escapes and the newline-suppression `\` line-continuation feature.

### Level 1 — Basic

```java
// File: ProfileJson.java
public class ProfileJson {
    public static void main(String[] args) {
        String json = """
                      {
                        "name": "Ada",
                        "role": "engineer"
                      }
                      """;
        System.out.println(json);
        System.out.println("Length: " + json.length());
    }
}
```

**How to run:** `java ProfileJson.java` (JDK 17+; text blocks need no preview flag from Java 15 onward).

Expected output:
```
{
  "name": "Ada",
  "role": "engineer"
}

Length: 40
```

### Level 2 — Intermediate

```java
// File: ProfileJsonTemplate.java
public class ProfileJsonTemplate {
    public static void main(String[] args) {
        String name = "Grace";
        String role = "scientist";

        String json = """
                      {
                        "name": "%s",
                        "role": "%s"
                      }""".formatted(name, role);

        System.out.println(json);
    }
}
```

**How to run:** `java ProfileJsonTemplate.java`

Expected output:
```
{
  "name": "Grace",
  "role": "scientist"
}
```

Here the text block acts as a **format template**: `%s` placeholders are filled in by `String.formatted(...)` (added alongside text blocks). Note the closing `"""` sits right after the last `}` with no trailing newline — the position of the closing delimiter controls both indentation stripping and whether a final line break is included.

### Level 3 — Advanced

```java
// File: ReportBuilder.java
import java.util.List;

public class ReportBuilder {
    record User(String name, String role) {}

    public static void main(String[] args) {
        List<User> users = List.of(new User("Ada", "engineer"), new User("Grace", "scientist"));

        StringBuilder report = new StringBuilder();
        for (User u : users) {
            report.append("""
                          {"name": "%s", "role": "%s"}
                          """.formatted(u.name(), u.role()));
        }

        String sqlTemplate = """
                             SELECT * FROM users \
                             WHERE role = 'engineer' \
                             ORDER BY name;""";

        System.out.println("Report:");
        System.out.print(report);
        System.out.println("SQL (single line, no embedded newlines): " + sqlTemplate);
    }
}
```

**How to run:** `java ReportBuilder.java`

Expected output:
```
Report:
{"name": "Ada", "role": "engineer"}
{"name": "Grace", "role": "scientist"}

SQL (single line, no embedded newlines): SELECT * FROM users WHERE role = 'engineer' ORDER BY name;
```

Level 3 combines a text block inside a loop (building a multi-record JSON-lines report) with the `\` line-continuation escape, which **suppresses** the newline that would otherwise appear at that point in the source — letting you wrap a long logical line (the SQL statement) across several source lines for readability while producing one continuous string with no embedded `\n` characters.

## 6. Walkthrough

1. `main` starts by building `report` as an empty `StringBuilder`, then iterates the two `User` records.
2. For each `User`, a text block `"""{"name": "%s", "role": "%s"}\n"""` is evaluated. The compiler first strips the common indentation margin (set by the column of the closing `"""` on its own line), leaving the literal template `{"name": "%s", "role": "%s"}\n`.
3. `.formatted(u.name(), u.role())` substitutes the two `%s` placeholders with the record's fields, producing e.g. `{"name": "Ada", "role": "engineer"}\n` for the first user, which is then appended to `report`.
4. After the loop, `report` holds two JSON lines concatenated together, each terminated by the newline that was part of the text block's content (because the closing `"""` sat on its own line below the closing `}`).
5. `sqlTemplate` is built from a *different* shaped text block: here, each source line inside the block ends with a backslash (`\`) immediately before the line break. This is the **line-continuation escape** introduced alongside text blocks: it tells the compiler "do not include a newline character here even though the source has one," effectively joining the three visual lines of SQL into one continuous string with single spaces where the line breaks were (since a literal space precedes the `\` on each line).
6. `System.out.println` and `System.out.print` then render both `report` (still holding its internal newlines, hence the JSON lines print on separate lines) and `sqlTemplate` (which prints as one unbroken line despite spanning three lines in the source).
7. Note the asymmetry: `report`'s text block deliberately *keeps* its newlines (no trailing `\`) because each JSON record should be on its own line, while `sqlTemplate`'s text block deliberately *removes* its newlines (via trailing `\`) because the SQL statement should read as a single logical line even though the source wraps it for readability.

```
source text block ──► strip common margin ──► normalize line terminators
                                                     │
                                    trailing "\" on a line? ──yes──► drop that newline
                                                     │no
                                                     ▼
                                          keep newline in final String
```

## 7. Gotchas & takeaways

> The **margin-stripping** rule is based on the *least-indented non-blank line*, and critically **includes the line holding the closing `"""`**. If you dedent the closing delimiter to column 0, every line's leading whitespace up to that point is preserved instead of stripped — a common source of "why does my JSON have extra indentation" surprises.

- Text blocks needed no preview flag from Java 15 onward — earlier JDKs (13, 14) required `--enable-preview` to use them at all.
- Trailing whitespace at the end of a line inside a text block is stripped automatically unless you escape it (`\s` marks an explicit trailing space that should be preserved).
- The `\` line-continuation escape (suppressing a newline) and `\"""` (embedding a literal `"""` sequence) were the two escape additions refined during the preview cycles before standardization.
- `String.formatted(Object...)`, added alongside text blocks, is often nicer than `String.format(block, args)` because it reads left-to-right: template first, arguments after.
- Text blocks are still ordinary `String` instances at runtime — no new type, no different equality or interning behavior versus a regular string literal.
