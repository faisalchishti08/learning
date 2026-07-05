---
card: java
gi: 58
slug: line-comments
title: Line comments (//)
---

## 1. What it is

A **line comment** starts with `//` and runs to the end of the physical line. The compiler ignores everything from `//` to the newline. Line comments are the most common comment form in Java for brief, inline annotations.

```java
// This is a full-line comment
int maxRetries = 3;   // End-of-line comment: why 3? see RFC-7231 §6.5.4

// Commented-out code (discouraged — use version control instead)
// oldAlgorithm();
newAlgorithm();
```

Line comments cannot span lines — each continuation line must start with `//`.

## 2. Why & when

Comments are for **why**, not what. Well-named identifiers already express what code does. Write a line comment only when the code hides a non-obvious reason:

| Write a comment | Skip the comment |
|---|---|
| A specific business rule or constraint | What the code obviously does |
| A workaround for a known external bug | A trivial operation like `i++` |
| Units or non-obvious scale (ms not seconds) | A well-named method call |
| Protocol or spec reference (`// per RFC 7231`) | Auto-generated code |
| Intentional deviation from normal practice | Repetitive explanations across many similar lines |

## 3. Core concept

```java
// ---- syntax ----
// Everything after // on the same line is ignored by the compiler.
// There is no closing token — the newline ends the comment.

int timeout = 30_000;   // 30 s expressed in ms — API accepts only ms

// ---- legal positions ----
// 1. Full line
// 2. After a statement
// 3. After an opening brace
void start() {   // called once at startup
    connect();
}

// ---- what the compiler actually sees ----
// Source:   int x = /* load */ 5; // always 5
// Compiler: int x =             5;
// Line comment swallows the rest; block comment can appear inline.

// ---- common anti-patterns ----

// BAD: says what (obvious from code)
i++;   // increment i

// BAD: stale — code changed, comment wasn't updated
// int timeout = 5000;  // 5s  ← now the real timeout is 30_000 above

// GOOD: says why (not deducible from the code)
Thread.sleep(200);   // give the OS scheduler time to yield on slow CI machines

// BAD: commented-out code — just noise; use git if you need to recover it
// oldService.process(order);

// ---- URL references ----
// https://tools.ietf.org/html/rfc7231#section-6.5.4
// Using URL is fine when citing spec; keep URL on its own line.

// ---- special IDE markers (recognised by many tools) ----
// TASK: switch to async once the API is stable
// WARN: this silently drops orders larger than Integer.MAX_VALUE
// NOTE: this branch is only reachable under concurrent load

// ---- comment inside string literal — NOT a comment ----
String s = "// this is just a string, not a comment";
```

## 4. Diagram

<svg viewBox="0 0 700 168" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Line comment: // to end of line ignored by compiler; three positions: full-line, end-of-line, and inside block comment">
  <rect x="8" y="8" width="684" height="152" rx="8" fill="#0d1117"/>

  <!-- Source code -->
  <rect x="20" y="22" width="370" height="125" rx="5" fill="#1c2430"/>
  <text x="32" y="40" fill="#8b949e" font-size="8.5" font-family="monospace">// give the OS scheduler time to yield</text>
  <text x="32" y="55" fill="#79c0ff" font-size="8.5" font-family="monospace">Thread</text><text x="72" y="55" fill="#e6edf3" font-size="8.5" font-family="monospace">.sleep(200);</text><text x="165" y="55" fill="#8b949e" font-size="8.5" font-family="monospace">// 200 ms</text>
  <text x="32" y="70" fill="#e6edf3" font-size="8.5" font-family="monospace">int timeout = 30_000;</text><text x="210" y="70" fill="#8b949e" font-size="8.5" font-family="monospace">// ms not s</text>
  <text x="32" y="85" fill="#e6edf3" font-size="8.5" font-family="monospace">String label = </text><text x="140" y="85" fill="#6db33f" font-size="8.5" font-family="monospace">"// not a comment"</text><text x="276" y="85" fill="#e6edf3" font-size="8.5" font-family="monospace">;</text>
  <text x="32" y="110" fill="#8b949e" font-size="8" font-family="sans-serif">Full-line: entire line ignored</text>
  <text x="32" y="124" fill="#8b949e" font-size="8" font-family="sans-serif">End-of-line: statement + ignored suffix</text>
  <text x="32" y="138" fill="#8b949e" font-size="8" font-family="sans-serif">In string: // is literal text, not a comment</text>

  <!-- Compiler view -->
  <rect x="406" y="22" width="276" height="125" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="544" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Compiler sees</text>
  <text x="418" y="55" fill="#e6edf3" font-size="8.5" font-family="monospace">Thread.sleep(200);</text>
  <text x="418" y="70" fill="#e6edf3" font-size="8.5" font-family="monospace">int timeout = 30_000;</text>
  <text x="418" y="85" fill="#e6edf3" font-size="8.5" font-family="monospace">String label = </text><text x="533" y="85" fill="#6db33f" font-size="8.5" font-family="monospace">"// not a comment"</text><text x="647" y="85" fill="#e6edf3" font-size="8.5" font-family="monospace">;</text>
  <text x="418" y="115" fill="#8b949e" font-size="7.5" font-family="sans-serif">Comments stripped at</text>
  <text x="418" y="128" fill="#8b949e" font-size="7.5" font-family="sans-serif">tokenisation — zero</text>
  <text x="418" y="141" fill="#8b949e" font-size="7.5" font-family="sans-serif">runtime overhead</text>
</svg>

The compiler strips `//` comments during tokenisation; they produce no bytecode and carry zero runtime cost.

## 5. Runnable example

Scenario: an order validation service where each comment explains a non-obvious constraint — showing purposeful `//` use in real code.

### Level 1 — Basic

```java
// LineCommentsBasic.java — demonstrates purposeful line comment usage
public class LineCommentsBasic {

    // Maximum items per order — enforced by the warehouse pick system (Ticket WH-412)
    static final int MAX_ITEMS = 50;

    // Timeout in milliseconds — the payment gateway SLA is 30 s
    static final int PAYMENT_TIMEOUT_MS = 30_000;

    public static void main(String[] args) {
        System.out.println("=== Line comments demo ===\n");

        // Validate an order — each line comment explains a constraint, not the code itself
        String orderId = "ORD-001";
        int    items   = 47;
        double amount  = 1_250.00;   // GBP — API does not convert currency

        // Early exit on invalid order to avoid processing partial state
        if (items > MAX_ITEMS) {
            System.out.println("Order " + orderId + " rejected: too many items");
            return;
        }

        // Round to 2 dp — downstream billing rounds down, causing £0.001 discrepancies
        double rounded = Math.round(amount * 100.0) / 100.0;

        System.out.println("Order:   " + orderId);
        System.out.println("Items:   " + items + " / " + MAX_ITEMS);
        System.out.println("Amount:  £" + rounded);
        System.out.println("Timeout: " + PAYMENT_TIMEOUT_MS + " ms");

        System.out.println("\n[ Comment rules ]");
        System.out.println("  // starts a line comment; ends at newline");
        System.out.println("  Compiler strips them — zero runtime cost");
        System.out.println("  Use for: WHY, constraints, units, spec references");
        System.out.println("  Avoid:   restating the obvious, commented-out code");
    }
}
```

**How to run:** `java LineCommentsBasic.java`

Each `//` comment here answers "why does this value/logic exist?" rather than "what does this line do?" — the code is already clear; the comment adds the missing business context.

### Level 2 — Intermediate

Same order system: show how `//` comments interact with string literals, character literals, and multi-line strings — edge cases where `//` is NOT a comment.

```java
// LineCommentsIntermediate.java — edge cases where // is NOT a comment
public class LineCommentsIntermediate {
    public static void main(String[] args) {
        System.out.println("=== Line comment edge cases ===\n");

        // 1. Inside a String literal — // is literal text
        String url     = "https://api.example.com/orders";   // URL in a string — // is data
        String pattern = "^//[a-z]+";                        // regex: line starting with //
        System.out.println("URL:     " + url);
        System.out.println("Pattern: " + pattern);

        // 2. Inside a char literal
        char slash = '/';   // single slash character, not a comment start
        System.out.println("Slash char: " + slash);
        // char comment = '/'; // Note: two slashes IN A ROW in source start a comment
        // char notComment = '/';  // this // is already comment — char ends with ;

        // 3. Text block (JDK 15+) — // inside is literal
        String json = """
            {
              "baseUrl": "https://api.example.com",
              "note": "// this is a JSON string value, not a comment"
            }
            """;
        System.out.println("JSON text block:");
        System.out.println(json);

        // 4. Block comment inside a line comment — line comment wins
        // /* this opening block comment marker is ignored because // comes first */
        System.out.println("Block comment marker inside line comment is inert.");

        // 5. Multi-line continuation — must repeat // on each line
        // This is line 1 of a long explanation
        // This is line 2 — note: no trailing \ or any continuation syntax
        // This is line 3 — each physical line needs its own //
        System.out.println("\nMulti-line comment is just consecutive // lines.");

        // 6. URL-style double slash
        System.out.println("\nURL with // in source string (not a comment):");
        System.out.println("  " + url);

        System.out.println("\n[ What IS and ISN'T a comment ]");
        System.out.println("  // outside a string   → comment (stripped)");
        System.out.println("  // inside \"...\"      → literal string content");
        System.out.println("  // inside '...'       → impossible (char is one char)");
        System.out.println("  // inside /* ... */   → the block comment wins; // is inert");
        System.out.println("  /* inside // ...      → line comment wins; /* is inert");
    }
}
```

**How to run:** `java LineCommentsIntermediate.java`

The tokeniser processes comments before any other analysis. A `//` that appears inside a string literal token is never seen as a comment — the string token was already delimited by the preceding `"`.

### Level 3 — Advanced

Same order system: use `javax.tools` to compile a source string containing `//` comments, then inspect the resulting bytecode size to confirm comments produce zero bytecode, and scan source lines for anti-pattern comments programmatically.

```java
// LineCommentsAdvanced.java — verify comments are stripped by inspecting bytecode
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

public class LineCommentsAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Line comments: compile + bytecode size demo ===\n");

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            System.out.println("JDK compiler not available. Showing analysis only.");
            analyseCommentPatterns();
            return;
        }

        Path tmp = Files.createTempDirectory("comments-demo");

        // Source WITH many comments
        String srcWithComments = """
            // Order processing service
            // Author: payment team
            // Reviewed: 2024-01
            public class OrderWithComments {
                // Maximum amount — per payment gateway docs (PGW-2023-11)
                static final double MAX_AMOUNT = 10_000.00;   // GBP limit

                // Process an order and return confirmation
                // Params: id — order identifier (UUID format)
                //         amount — order value in GBP
                public static String process(String id, double amount) {
                    // Reject oversized orders early — PGW rejects silently above limit
                    if (amount > MAX_AMOUNT) return "REJECTED";
                    return "CONFIRMED:" + id;   // caller logs this
                }
            }
            """;

        // Source WITHOUT comments (functionally identical)
        String srcWithout = """
            public class OrderWithout {
                static final double MAX_AMOUNT = 10_000.00;
                public static String process(String id, double amount) {
                    if (amount > MAX_AMOUNT) return "REJECTED";
                    return "CONFIRMED:" + id;
                }
            }
            """;

        long sizeWith    = compileAndSize(compiler, tmp, "OrderWithComments", srcWithComments);
        long sizeWithout = compileAndSize(compiler, tmp, "OrderWithout",      srcWithout);

        System.out.println("[ Bytecode size comparison ]");
        System.out.printf("  OrderWithComments.class : %d bytes%n", sizeWith);
        System.out.printf("  OrderWithout.class      : %d bytes%n", sizeWithout);
        System.out.printf("  Difference              : %d bytes%n", sizeWith - sizeWithout);
        System.out.println("  Conclusion: comments do NOT increase bytecode size.");
        System.out.println("  (small differences may come from constant pool string entries for class names)");

        Files.walk(tmp).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);

        analyseCommentPatterns();
    }

    static long compileAndSize(JavaCompiler compiler, Path tmp, String className, String src)
            throws IOException {
        Path srcFile = tmp.resolve(className + ".java");
        Files.writeString(srcFile, src);
        compiler.run(null, null, null, srcFile.toString());
        Path clsFile = tmp.resolve(className + ".class");
        return Files.exists(clsFile) ? Files.size(clsFile) : -1;
    }

    static void analyseCommentPatterns() {
        System.out.println("\n[ Comment pattern analyser ]");

        String[] lines = {
            "i++;   // increment i",                           // anti-pattern: states the obvious
            "Thread.sleep(200);   // yield to OS scheduler on slow CI",  // good: explains why
            "// TASK: switch to async API",                    // IDE marker — OK
            "// oldService.process(order);",                   // commented-out code — bad
            "int x = computeHash();   // see HashingUtils",    // reference — borderline
            "// per RFC 7231 §6.5.4 — 429 Too Many Requests", // spec reference — good
        };

        for (String line : lines) {
            String verdict = classifyComment(line);
            System.out.printf("  %-55s → %s%n", line.length() > 55 ? line.substring(0,52)+"..." : line, verdict);
        }

        System.out.println("\n[ Summary ]");
        System.out.println("  // : single-line comment, ends at newline");
        System.out.println("  Zero bytecode overhead — stripped at tokenisation");
        System.out.println("  Best for: constraints, units, spec refs, workaround notes");
        System.out.println("  Avoid:    obvious restatements, stale code, commented-out code");
    }

    static String classifyComment(String line) {
        String comment = "";
        int idx = line.indexOf("//");
        if (idx >= 0) comment = line.substring(idx + 2).trim().toLowerCase();

        if (comment.startsWith("task") || comment.startsWith("warn") || comment.startsWith("note"))
            return "IDE marker — OK";
        if (line.strip().startsWith("//") && line.strip().length() > 2 &&
            !line.strip().substring(2).strip().isEmpty() &&
            (line.strip().substring(2).strip().matches(".*\\b(increment|decrement|add|set|return|call|get|check)\\b.*")))
            return "ANTI-PATTERN: states what, not why";
        if (comment.contains("per rfc") || comment.contains("see ") || comment.contains("§"))
            return "GOOD: spec/cross-reference";
        if (line.strip().startsWith("//") && !comment.startsWith("task") && !comment.startsWith("warn"))
            return "Full-line comment — verify it's useful";
        if (comment.contains("yield") || comment.contains("workaround") || comment.contains("ci") ||
            comment.contains("limit") || comment.contains("because") || comment.contains("scheduler"))
            return "GOOD: explains non-obvious why";
        return "OK";
    }
}
```

**How to run:** `java LineCommentsAdvanced.java`

The bytecode size comparison confirms that `//` comments are stripped entirely during compilation — they occupy no space in `.class` files and incur no runtime cost whatsoever.

## 6. Walkthrough

Execution trace in `LineCommentsAdvanced.main`:

**Compilation.** `compiler.run(null, null, null, srcFile.toString())` compiles `OrderWithComments.java`. During tokenisation, the Java lexer encounters `//` and discards everything up to the next newline before producing any tokens. The parser never sees comment text.

**Bytecode size.** `Files.size(clsFile)` reads the `.class` file size. Both `OrderWithComments.class` and `OrderWithout.class` compile to bytecode of equal (or near-equal) size because comments are stripped before any intermediate representation is built. Any tiny difference comes from the class name string in the constant pool, not from comment content.

**Comment pattern analysis.** `classifyComment()` checks for anti-patterns heuristically: if the comment merely restates a verb already in the code (`increment`, `decrement`, `set`), it's flagged. Spec references (`per RFC`, `see §`) and explanations of external constraints (`yield`, `scheduler`, `CI`) are flagged as good. This mirrors code-review automation tools like CheckStyle, Spotless, or SonarQube.

**Lexer priority.** The Java spec (JLS §3.7) defines: if `//` appears outside a string/char literal, everything to the end of the line is a comment. The lexer processes characters left-to-right — so `// /* unclosed` is a valid line comment; the `/*` inside is inert.

## 7. Gotchas & takeaways

> **Commented-out code is worse than no comment.** It clutters the file, never gets updated, accumulates stale logic, and confuses future readers who wonder if the code should be active. Delete it — version control preserves history.

> **`//` inside a string literal is NOT a comment.** The lexer sees the string token before looking for comment markers. `String url = "https://..."` is safe; the `//` in the URL is part of the string value.

- `//` ends at the first newline — no multiline span possible.
- No runtime or bytecode overhead — stripped at tokenisation.
- Write comments for WHY, never WHAT.
- `TASK`, `NOTE`, `WARN` (and similar task markers) are surfaced by IDE and CI tools — configure the exact words in your project's IDE settings.
- Don't commit commented-out code — use git history instead.
- `//` inside `"..."`, `"""..."""`, `/* ... */` is NOT a comment.
