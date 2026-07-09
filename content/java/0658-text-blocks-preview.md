---
card: java
gi: 658
slug: text-blocks-preview
title: Text blocks (preview)
---

## 1. What it is

**Text blocks**, introduced as a **preview feature** (JEP 355) in **Java 13**, let you write multi-line string literals without manually inserting `\n` escapes or `+` concatenation between lines. A text block starts with three double-quotes (`"""`) followed immediately by a newline, contains raw lines of text, and ends with another `"""`. The compiler automatically strips a common leading-whitespace margin (based on the least-indented line, including the closing delimiter's position) and normalizes line terminators to `\n`, so you can write embedded HTML, JSON, or SQL that looks exactly like it would in its own file, indented naturally within your Java source. Like switch expressions in the same release cycle, this shipped behind `--enable-preview` and evolved before becoming a permanent feature two releases later, in Java 15.

## 2. Why & when

Embedding any multi-line text — an SQL query, a JSON payload, an HTML snippet — as a traditional Java string literal is painful: every line needs a trailing `\n`, every line needs `+` to join with the next, and every embedded `"` needs escaping to `\"`. The result reads nothing like the text it represents, and small formatting mistakes are easy to make and hard to spot in a wall of escape characters. Text blocks solve this directly: paste the text almost verbatim between `"""` delimiters and the compiler handles line joining and reasonable indentation for you. Reach for a text block whenever a literal would otherwise span multiple lines glued together with `+` and `\n` — SQL, JSON, HTML fragments, usage/help text, or any test fixture data — and keep ordinary `"..."` literals for genuinely single-line strings.

## 3. Core concept

```java
// Old style: painful to read, painful to write
String json = "{\n" +
              "  \"name\": \"Ada\",\n" +
              "  \"age\": 36\n" +
              "}\n";

// Text block: looks like the actual JSON
String json2 = """
    {
      "name": "Ada",
      "age": 36
    }
    """;
```

The opening `"""` must be immediately followed by a line break (no content on that first line); the compiler determines the "incidental" leading whitespace to strip by looking at the least-indented non-blank line *and* the position of the closing `"""`, then removes that common margin from every line.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Source indentation in a text block is stripped down to the least-indented line, producing the final string content">
  <rect x="10" y="10" width="280" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="30" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Source (indented in code)</text>
  <text x="25" y="55" fill="#e6edf3" font-size="10" font-family="monospace">String s = """</text>
  <text x="25" y="70" fill="#79c0ff" font-size="10" font-family="monospace">    {</text>
  <text x="25" y="85" fill="#79c0ff" font-size="10" font-family="monospace">      "name": "Ada"</text>
  <text x="25" y="100" fill="#79c0ff" font-size="10" font-family="monospace">    }</text>
  <text x="25" y="115" fill="#e6edf3" font-size="10" font-family="monospace">    """;</text>
  <text x="25" y="150" fill="#8b949e" font-size="9" font-family="sans-serif">Least-indented line (incl.</text>
  <text x="25" y="165" fill="#8b949e" font-size="9" font-family="sans-serif">closing """) sets the margin</text>
  <text x="25" y="180" fill="#8b949e" font-size="9" font-family="sans-serif">to strip from every line.</text>

  <line x1="300" y1="100" x2="340" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#tb1)"/>

  <rect x="350" y="10" width="260" height="180" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="30" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Resulting String value</text>
  <text x="365" y="60" fill="#e6edf3" font-size="10" font-family="monospace">{</text>
  <text x="365" y="80" fill="#e6edf3" font-size="10" font-family="monospace">  "name": "Ada"</text>
  <text x="365" y="100" fill="#e6edf3" font-size="10" font-family="monospace">}</text>
  <text x="365" y="140" fill="#8b949e" font-size="9" font-family="sans-serif">Margin stripped; relative</text>
  <text x="365" y="155" fill="#8b949e" font-size="9" font-family="sans-serif">indentation between lines</text>
  <text x="365" y="170" fill="#8b949e" font-size="9" font-family="sans-serif">is preserved.</text>

  <defs><marker id="tb1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

The block can sit naturally indented inside your Java code; the compiler strips the shared margin so the runtime string value has clean, minimal indentation.

## 5. Runnable example

Scenario: building a small JSON payload for a "create user" request — first as a traditional escaped string, then as a text block, then combining a text block with `String.format`-style substitution for dynamic values and demonstrating how embedded quotes behave.

### Level 1 — Basic

```java
// File: TextBlockOld.java
public class TextBlockOld {
    public static void main(String[] args) {
        String json = "{\n" +
                      "  \"name\": \"Ada\",\n" +
                      "  \"role\": \"engineer\"\n" +
                      "}\n";
        System.out.print(json);
        System.out.println("Length: " + json.length());
    }
}
```

**How to run:** `java TextBlockOld.java`

Expected output:
```
{
  "name": "Ada",
  "role": "engineer"
}
Length: 39
```

### Level 2 — Intermediate

```java
// File: TextBlockPreview.java
public class TextBlockPreview {
    public static void main(String[] args) {
        String json = """
            {
              "name": "Ada",
              "role": "engineer"
            }
            """;
        System.out.print(json);
        System.out.println("Length: " + json.length());
    }
}
```

**How to run:** requires the preview flag since text blocks are a Java 13 preview feature:
```
javac --release 13 --enable-preview TextBlockPreview.java
java --enable-preview TextBlockPreview
```
(On modern JDKs 15+, text blocks are permanent and this runs with no flags at all.)

Expected output is identical to Level 1's — same characters, same length — but the source code needed no `\n` escapes, no `+` concatenation, and no `\"` escaping around the JSON's own quotes, because the text block's raw content is exactly the JSON as written.

### Level 3 — Advanced

```java
// File: TextBlockDynamic.java
public class TextBlockDynamic {
    static String userJson(String name, String role, int age) {
        String template = """
            {
              "name": "%s",
              "role": "%s",
              "age": %d,
              "bio": "Says \"hello\" in every language."
            }
            """;
        return template.formatted(name, role, age);
    }

    public static void main(String[] args) {
        System.out.print(userJson("Grace", "admiral", 79));
        System.out.print(userJson("Alan", "researcher", 41));
    }
}
```

**How to run:** `javac --release 13 --enable-preview TextBlockDynamic.java && java --enable-preview TextBlockDynamic`

Expected output:
```
{
  "name": "Grace",
  "role": "admiral",
  "age": 79,
  "bio": "Says "hello" in every language."
}
{
  "name": "Alan",
  "role": "researcher",
  "age": 41,
  "bio": "Says "hello" in every language."
}
```

Level 3 combines a text block with `String.formatted(...)` (a companion method also introduced around this era) to substitute `%s`/`%d` placeholders — showing that text blocks support the same escape sequences as regular strings (`\"` still works for an embedded literal quote inside the block) and that format specifiers work exactly as they would in a normal string.

## 6. Walkthrough

1. `main` calls `userJson("Grace", "admiral", 79)`. Inside, the compiler has already, at compile time, processed the `template` text block's source: it found the least-indented line (the closing `"""`, which sets the stripped margin), removed that common leading whitespace from every line, and normalized line endings — producing a runtime `String` value that looks like clean, unindented JSON with a trailing newline.
2. `template.formatted(name, role, age)` runs next — this calls `String.format` internally, substituting `%s` with `"Grace"`, `%s` with `"admiral"`, and `%d` with `79`, in the order the arguments were given.
3. The `\"hello\"` escape sequences inside the text block are processed exactly as they would be in a regular string literal: `\"` becomes a literal `"` character in the resulting string, which is why the printed "bio" field shows `Says "hello" in every language.` with real quote characters, not the escape sequence.
4. `formatted(...)` returns the fully substituted string, which `userJson` returns to `main`.
5. `System.out.print(userJson(...))` prints Grace's JSON block. Since the text block's raw content already ended with a trailing newline (because the closing `"""` sits on its own line, after the last content line), no extra `println` newline is needed — `print` (not `println`) is used deliberately to avoid a doubled blank line.
6. The exact same sequence repeats for `userJson("Alan", "researcher", 41)`, producing Alan's JSON block right after Grace's, with no manual `\n` bookkeeping anywhere in `userJson`'s implementation.

```
template (compile-time) ──► margin stripped, "\n" normalized ──► clean multi-line String
        │
        ▼ .formatted(name, role, age)
"{\n  \"name\": \"Grace\",\n  ... }\n"  ──► printed as-is
```

## 7. Gotchas & takeaways

> This is a **preview feature** in Java 13 — it requires `--enable-preview` on both `javac` and `java`, and the exact rules (especially around trailing-whitespace handling on individual lines, and the `\` line-continuation escape) were still being refined; they changed again in the Java 14 second preview before becoming final in Java 15. Don't assume Java 13's text-block semantics are byte-identical to the finalized version.

- The opening `"""` must be followed immediately by a line break — you can't put content on the same line as the opening delimiter.
- Indentation stripping is based on the *least-indented* line, including the closing `"""` — moving the closing delimiter left or right changes how much margin gets stripped from every line.
- All standard escape sequences (`\n`, `\"`, `\\`, etc.) still work inside a text block; you rarely need `\"` since embedded quotes usually don't need escaping in `"""`-delimited blocks, but it's supported when you do.
- A trailing line consisting only of the closing `"""` contributes a trailing newline to the string; put `"""` right after the last content character (no line break) if you don't want that trailing newline.
- Combine text blocks with `String.formatted(...)` or `String.format(...)` for template-style substitution — text blocks themselves don't do interpolation on their own.
