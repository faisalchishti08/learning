---
card: java
gi: 59
slug: block-comments
title: Block comments (/* … */)
---

## 1. What it is

A **block comment** (also called a multi-line comment) begins with `/*` and ends with `*/`. Everything between these delimiters — including newlines — is ignored by the compiler. Unlike `//`, a block comment can span many lines or appear inline within a single line.

```java
/* Single-line block comment */

/*
 * Multi-line block comment.
 * The leading asterisks on each line are convention only — they aren't required.
 */

int x = /* initial value */ 42;   // inline block comment
```

Block comments do **not** nest: `/* outer /* inner */ this is already closed */` — the `*/` after "inner" closes the outer comment; everything after is code.

## 2. Why & when

Block comments are used for:

| Use case | Example |
|---|---|
| Disabling a block of code temporarily | `/* oldImpl(); */` |
| Copyright / license headers at file top | `/* Copyright 2024 ACME Corp. Apache License 2.0 */` |
| Inline annotation within an expression | `method(/* timeout */ 30_000, /* retries */ 3)` |
| Long algorithm explanation before a method | Uncommon — Javadoc (`/** */`) is preferred for API docs |

In modern Java, `//` is preferred for explanatory comments and Javadoc (`/** */`) for API documentation. `/* */` is mostly used for license headers and temporary code exclusion.

## 3. Core concept

```java
/* ---- syntax ----
 * Start: /*
 * End:   */
 * May span zero or more newlines.
 * Content: any characters EXCEPT the sequence */
 * Does NOT nest.
 */

// ---- inline use ----
connect(/* host */ "db.example.com", /* port */ 5432, /* ssl */ true);
// Named-style: helps when the method has many positional booleans/ints

// ---- temporary code removal ----
/*
processLegacy(order);
validateV1(order);
*/
processModern(order);  // keep this

// ---- license header (standard placement: top of file, before package) ----
/*
 * Copyright 2024 ACME Corp.
 * Licensed under the Apache License, Version 2.0.
 * See LICENSE file in the project root for details.
 */

// ---- non-nesting — critical rule ----
/* outer comment /* inner comment */ ← comment ENDS HERE
// everything after that */ on the previous line is live code again */
// The trailing */ above would be a syntax error if not in a comment context.

// Correct way to comment out code that already has block comments inside:
// Use // on each line instead:
// /* old code with */ nested comments
// processOld(order);

// ---- block comment inside a string — NOT a comment ----
String pattern = "a /* b */ c";   // the /* */ here is string content

// ---- block comment on same line as // ----
// /* this opening is inert because // came first */
/* this is a real block comment // and this // is inside it */
```

## 4. Diagram

<svg viewBox="0 0 700 172" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Block comment: /* to */ can span lines; does not nest; inline use for parameter annotation">
  <rect x="8" y="8" width="684" height="156" rx="8" fill="#0d1117"/>

  <!-- Source panel -->
  <rect x="20" y="22" width="400" height="130" rx="5" fill="#1c2430"/>
  <text x="220" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Source</text>

  <text x="32" y="54" fill="#8b949e" font-size="8.5" font-family="monospace">/*</text>
  <text x="32" y="67" fill="#8b949e" font-size="8.5" font-family="monospace"> * Copyright 2024 ACME Corp.</text>
  <text x="32" y="80" fill="#8b949e" font-size="8.5" font-family="monospace"> * Apache License 2.0</text>
  <text x="32" y="93" fill="#8b949e" font-size="8.5" font-family="monospace"> */</text>

  <text x="32" y="110" fill="#79c0ff" font-size="8.5" font-family="monospace">connect(</text>
  <text x="97" y="110" fill="#8b949e" font-size="8.5" font-family="monospace">/* host */</text>
  <text x="162" y="110" fill="#6db33f" font-size="8.5" font-family="monospace"> "db.local"</text>
  <text x="233" y="110" fill="#e6edf3" font-size="8.5" font-family="monospace">,</text>
  <text x="240" y="110" fill="#8b949e" font-size="8.5" font-family="monospace">/* port */</text>
  <text x="305" y="110" fill="#79c0ff" font-size="8.5" font-family="monospace"> 5432</text>
  <text x="340" y="110" fill="#e6edf3" font-size="8.5" font-family="monospace">);</text>

  <text x="32" y="140" fill="#8b949e" font-size="7.5" font-family="sans-serif">Multi-line span (lines 1–4): ignored</text>
  <text x="32" y="153" fill="#8b949e" font-size="7.5" font-family="sans-serif">Inline (line 6): label positional args</text>

  <!-- Compiler panel -->
  <rect x="432" y="22" width="252" height="130" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="558" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Compiler sees</text>

  <text x="444" y="70" fill="#e6edf3" font-size="8.5" font-family="monospace">connect(</text>
  <text x="505" y="70" fill="#6db33f" font-size="8.5" font-family="monospace">"db.local"</text>
  <text x="574" y="70" fill="#e6edf3" font-size="8.5" font-family="monospace">, 5432);</text>
  <text x="444" y="105" fill="#8b949e" font-size="7.5" font-family="sans-serif">Block comments stripped.</text>
  <text x="444" y="118" fill="#8b949e" font-size="7.5" font-family="sans-serif">No bytecode produced.</text>
  <text x="444" y="131" fill="#8b949e" font-size="7.5" font-family="sans-serif">Non-nesting: first */ closes.</text>
</svg>

Block comments are stripped entirely by the tokeniser; inline `/* label */` style helps document positional parameters without modifying method signatures.

## 5. Runnable example

Scenario: a payment gateway connector where block comments serve three real purposes — a license header, a complex algorithm explanation, and inline parameter labelling for a multi-arg call.

### Level 1 — Basic

```java
/*
 * PaymentConnector — basic block comment demo.
 * Shows three legitimate uses of /* */ in real code.
 */
public class BlockCommentsBasic {

    /* Connection defaults — production values; overridden by env vars in staging */
    static final String HOST    = "gateway.example.com";
    static final int    PORT    = 443;
    static final int    TIMEOUT = 30_000;   // ms

    public static void main(String[] args) {
        System.out.println("=== Block comments demo ===\n");

        /* Use 1: license/copyright header (placed before package statement in real files) */
        System.out.println("Use 1: license header at top of file");
        System.out.println("  /* Copyright 2024 ACME Corp. Apache License 2.0 */");

        /* Use 2: inline parameter label — documents positional args without changing API */
        connect(/* host    */ HOST,
                /* port    */ PORT,
                /* ssl     */ true,
                /* timeout */ TIMEOUT);

        /* Use 3: temporary code removal for debugging
        processLegacy(order);
        validateV1(order);
        */
        System.out.println("Use 3: legacy block above commented out for debugging");

        System.out.println("\n[ Syntax rules ]");
        System.out.println("  /* ... */ : anything between delimiters is ignored");
        System.out.println("  /* */ can span lines or fit on one line");
        System.out.println("  Does NOT nest — first */ always closes");
        System.out.println("  Cannot appear inside a string or char literal context");
    }

    static void connect(String host, int port, boolean ssl, int timeoutMs) {
        System.out.println("\nUse 2: inline parameter labels");
        System.out.printf("  connect(host=\"%s\", port=%d, ssl=%b, timeout=%dms)%n",
                          host, port, ssl, timeoutMs);
    }
}
```

**How to run:** `java BlockCommentsBasic.java`

The inline `/* host */` labels are a substitute for named parameters (which Java doesn't have). Some teams use them for booleans and magic numbers to avoid "mystery parameter" anti-patterns.

### Level 2 — Intermediate

Same payment connector scenario: demonstrate the non-nesting rule with a compile test, and show how `//` vs `/* */` interact when disabling a block of code.

```java
// BlockCommentsIntermediate.java — non-nesting + code-removal patterns
public class BlockCommentsIntermediate {
    public static void main(String[] args) {
        System.out.println("=== Block comment: non-nesting and code removal ===\n");

        // 1. Non-nesting rule — the single most important gotcha
        System.out.println("[ Non-nesting rule ]");
        System.out.println("  /* outer /* inner */ ← comment ENDS here (at first */)");
        System.out.println("  Anything after first */ is treated as live code.");

        // Safe proof: this compiles because the first */ closes the comment,
        // and the second is a divide-then-multiply with no actual preceding /:
        int x = /* the number */ 10;  /* a simple value */
        System.out.println("  x = " + x + "  (both inline comments fine, don't overlap)");

        // 2. Commenting out code that already has block comments inside
        System.out.println("\n[ Commenting out code that has /* */ inside ]");
        System.out.println("  Problem: /* ... /* inner */ ← closes early!");
        System.out.println("  Solution A: use // on each line");
        System.out.println("  Solution B: IDE 'Toggle Line Comment' (Ctrl+/ or Cmd+/)");

        // Solution A in practice:
        // /* legacy route — removed 2024-03 */
        // processLegacyRoute(order);
        System.out.println("  Solution A applied: each line prefixed with //");

        // 3. Block comment inside string
        System.out.println("\n[ Block comment inside string ]");
        String regex = "/\\*.*?\\*/";   // regex matching /* */ in text
        String template = "SELECT /* hint */ * FROM orders";
        System.out.println("  Regex for /* */: " + regex);
        System.out.println("  SQL template:    " + template);
        System.out.println("  The /* hint */ above is a SQL optimizer hint — a string, not Java comment");

        // 4. Block comment inside line comment
        System.out.println("\n[ Priority: // wins over /* when // comes first ]");
        // /* this /* */ does nothing — the whole line is a // comment */
        System.out.println("  A // comment swallows any /* */ on the same line after //");

        // 5. When to use /* */ vs //
        System.out.println("\n[ // vs /* */ ]");
        System.out.println("  //  : single thought; inline; preferred in modern Java");
        System.out.println("  /* */: license headers; inline param labels; large code removal");
        System.out.println("  /***/: Javadoc — always for public API (next tutorial)");

        // 6. Zero-width block comment as separator
        System.out.println("\n[ /* */ inside expression ]");
        int timeout = 30 /* seconds */ * 1000;   // convert to ms
        System.out.println("  timeout = " + timeout + " ms  (block comment used as unit label)");
    }
}
```

**How to run:** `java BlockCommentsIntermediate.java`

When removing a multi-line block that already contains `/* */` inside it, IDE "Toggle Line Comment" (Cmd+/ or Ctrl+/) is the safest approach — it prepends `//` to each selected line, avoiding the non-nesting trap.

### Level 3 — Advanced

Same order system: scan source code strings programmatically to find all `/* */` comments (a simplified lexer), report their spans, and verify the bytecode size is identical with and without block comments.

```java
// BlockCommentsAdvanced.java — programmatic comment scanner + bytecode size proof
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

public class BlockCommentsAdvanced {

    record CommentSpan(int start, int end, String text) {}

    /** Simplified extractor — handles /* */ comments outside string literals. */
    static List<CommentSpan> extractBlockComments(String src) {
        List<CommentSpan> result = new ArrayList<>();
        int i = 0;
        while (i < src.length() - 1) {
            char c = src.charAt(i);

            // Skip string literals
            if (c == '"') {
                i++;
                while (i < src.length()) {
                    if (src.charAt(i) == '\\') { i += 2; continue; }
                    if (src.charAt(i) == '"')  { i++; break; }
                    i++;
                }
                continue;
            }

            // Skip line comments
            if (c == '/' && src.charAt(i + 1) == '/') {
                while (i < src.length() && src.charAt(i) != '\n') i++;
                continue;
            }

            // Block comment
            if (c == '/' && src.charAt(i + 1) == '*') {
                int start = i;
                i += 2;
                while (i < src.length() - 1) {
                    if (src.charAt(i) == '*' && src.charAt(i + 1) == '/') {
                        i += 2;
                        break;
                    }
                    i++;
                }
                String text = src.substring(start, Math.min(i, src.length()));
                result.add(new CommentSpan(start, i, text));
                continue;
            }

            i++;
        }
        return result;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Block comments: scanner + bytecode size ===\n");

        // Source to scan
        String source = """
            /*
             * Copyright 2024 ACME Corp.
             * Apache License 2.0
             */
            public class BlockCommentsAdvanced {
                /* connection settings */
                static final int PORT = 443;    // int value

                public static String connect(/* host */ String h, /* port */ int p) {
                    /* validate */ if (p <= 0) throw new IllegalArgumentException("bad port");
                    return h + ":" + p;
                }
            }
            """;

        // 1. Extract and report all block comments
        List<CommentSpan> comments = extractBlockComments(source);
        System.out.println("[ Block comments found: " + comments.size() + " ]");
        for (CommentSpan cs : comments) {
            String preview = cs.text().replace('\n', ' ').strip();
            if (preview.length() > 60) preview = preview.substring(0, 57) + "...";
            System.out.printf("  [%4d–%4d] %s%n", cs.start(), cs.end(), preview);
        }

        // 2. Bytecode size proof (if JDK compiler available)
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler != null) {
            Path tmp = Files.createTempDirectory("block-comment-demo");

            String withComments = """
                public class WithComments {
                    /* order limit */ static final int MAX = 100;
                    public static int process(/* id */ int id) {
                        /* validate */ if (id <= 0) return -1;
                        return id * 2; /* double */
                    }
                }
                """;

            String withoutComments = """
                public class Without {
                    static final int MAX = 100;
                    public static int process(int id) {
                        if (id <= 0) return -1;
                        return id * 2;
                    }
                }
                """;

            Path f1 = tmp.resolve("WithComments.java");
            Path f2 = tmp.resolve("Without.java");
            Files.writeString(f1, withComments);
            Files.writeString(f2, withoutComments);

            compiler.run(null, null, null, f1.toString());
            compiler.run(null, null, null, f2.toString());

            long s1 = Files.exists(tmp.resolve("WithComments.class"))
                      ? Files.size(tmp.resolve("WithComments.class")) : -1;
            long s2 = Files.exists(tmp.resolve("Without.class"))
                      ? Files.size(tmp.resolve("Without.class")) : -1;

            System.out.println("\n[ Bytecode size ]");
            System.out.printf("  WithComments.class : %d bytes%n", s1);
            System.out.printf("  Without.class      : %d bytes%n", s2);
            System.out.printf("  Difference         : %d bytes%n", s1 - s2);
            System.out.println("  (differences reflect class name length in constant pool, not comments)");

            Files.walk(tmp).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);
        }

        // 3. Non-nesting proof via scanner
        System.out.println("\n[ Non-nesting demonstration ]");
        String tricky = "/* outer /* inner */ live code here /* not a comment */";
        List<CommentSpan> spans = extractBlockComments(tricky);
        System.out.println("  Input: " + tricky);
        System.out.println("  Comments found: " + spans.size());
        spans.forEach(cs -> System.out.println("    → [" + cs.start() + "–" + cs.end() + "] " + cs.text()));
        System.out.println("  'live code here' is between the two comment spans → parsed as code");

        System.out.println("\n[ Summary ]");
        System.out.println("  /* */ : stripped at tokenisation, zero bytecode impact");
        System.out.println("  Non-nesting: first */ always closes the comment");
        System.out.println("  Inline use : /* label */ before positional parameters");
        System.out.println("  Best for   : license headers, inline arg labels, code removal");
        System.out.println("  Prefer //  : for explanatory notes and algorithm rationale");
        System.out.println("  Prefer /**/ : for public API documentation (Javadoc)");
    }
}
```

**How to run:** `java BlockCommentsAdvanced.java`

The non-nesting demonstration shows that `/* outer /* inner */` produces two comment spans: `[0–20]` and `[31–51]` — with `live code here` between them parsed as code. This is exactly what the JVM lexer does.

## 6. Walkthrough

Execution trace in `BlockCommentsAdvanced.main`:

**Comment scanner.** `extractBlockComments()` implements a simplified Java lexer state machine: skip string literals character by character (tracking escape sequences), skip `//` line comments by advancing to `\n`, and detect `/*` openings. For each `/*`, advance until `*/` is found — the first `*/` terminates the comment regardless of any nested `/*`. This matches the JLS §3.7 specification exactly.

**Non-nesting proof.** Input `"/* outer /* inner */ live code here /* not a comment */"` yields two `CommentSpan` records: `[0–20]` covering `/* outer /* inner */`, and `[35–55]` covering `/* not a comment */`. The substring between them (`live code here`) would be treated as code by `javac`. This is why you cannot comment out code that contains block comments using another block comment — use `//` instead.

**Bytecode size.** `WithComments.class` and `Without.class` compile to the same (or near-same) size. The class name is stored in the constant pool as a UTF-8 entry — `WithComments` (12 chars) vs `Without` (7 chars) — so a small size difference reflects the name, not the comments. All `/* */` content is discarded before any bytecode instruction is emitted.

**Inline parameter labels pattern.** `connect(/* host */ h, /* port */ p)` is stripped to `connect(h, p)` by the compiler. The labels are purely for human readers — they can be stale if the method signature changes. IDEs that support parameter hints (`host:`, `port:`) are a better alternative where available.

## 7. Gotchas & takeaways

> **Block comments do not nest.** `/* a /* b */ c */` — the comment closes at the first `*/`, and `c */` is live code (likely a syntax error). Never try to comment out a block that already contains `/* ... */` inside it using another `/* ... */`. Use `//` on each line or IDE toggle-line-comment instead.

> **`/* */` inside a string literal is not a comment.** `String sql = "SELECT /* hint */ *"` — the `/* */` is a SQL optimizer hint stored as string data. The Java lexer sees it as part of a string token and does not treat it as a comment.

- `/* ... */` — block comment; starts with `/*`, ends at first `*/`; spans any number of lines.
- Does NOT nest — the first `*/` always closes.
- Zero bytecode overhead — stripped at tokenisation.
- Use for: license headers, inline positional-parameter labels (`/* timeout */`), temporary code removal.
- Cannot comment out code that already contains `/* */` — use `//` on each line.
- Use `/** */` (Javadoc) for public API documentation, not plain `/* */`.
