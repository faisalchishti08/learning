---
card: java
gi: 765
slug: string-templates-2nd-preview
title: String templates (2nd preview)
---

## 1. What it is

**Java 22** (JEP 459) is the **second preview** of [string templates](0750-string-templates-preview.md), continuing from the first preview round in Java 21. The core mechanism — `STR."text \{expr} more text"` for interpolation, `FMT` for `printf`-style formatting per embedded expression, and `StringTemplate.RAW` for building custom template processors — carries forward, with this round's changes centered on refining how templates interact with **text blocks** (multi-line string literals) and tightening the rules around what expressions are legal inside `\{...}`, based on feedback from the first preview round's broader usage. As with the first round, it requires `--enable-preview` to compile and run.

## 2. Why & when

The first preview round validated the basic interpolation mechanism, but real usage surfaced friction specifically where string templates meet **text blocks** — Java's triple-quote multi-line string literal syntax, introduced separately in an earlier release. A template embedded in a multi-line text block needs consistent rules about how embedded expressions interact with the text block's own indentation-stripping behavior, and the first round's rules here weren't fully settled. This second preview round refines exactly that interaction, so a multi-line templated string (a formatted multi-line log message, an embedded multi-line query, a templated block of structured text) behaves predictably regarding indentation and embedded expressions together — a combination the first round hadn't fully worked through given text blocks and string templates arrived in different releases and needed a round of dedicated attention to compose correctly.

## 3. Core concept

```java
String name = "Ada";
int failedAttempts = 2;

String report = STR."""
    User: \{name}
    Failed login attempts: \{failedAttempts}
    Status: \{failedAttempts >= 3 ? "locked" : "active"}
    """;

System.out.println(report);
```

The text block's own indentation-stripping applies to the literal fragments, while `\{...}` expressions are evaluated and substituted in, independent of the surrounding indentation — this round is specifically about making that interaction consistent and predictable.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A templated text block combines multi-line literal text with embedded expressions, requiring consistent rules for how indentation stripping and interpolation interact">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">text block: multi-line literal</text>
  <text x="160" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">indentation stripped per text-block rules</text>

  <rect x="340" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">\{expr}: embedded values</text>
  <text x="480" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">substituted independent of indentation</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Second preview: makes these two features compose predictably together</text>
</svg>

*Multi-line templates need clear rules for how text-block formatting and interpolation combine.*

## 5. Runnable example

Scenario: a multi-line status report generator, growing from single-line interpolation into a fully formatted multi-line templated report.

### Level 1 — Basic

```java
public class ReportSingleLine {
    public static void main(String[] args) {
        String name = "Ada";
        int failedAttempts = 2;
        String line = STR."User \{name} has \{failedAttempts} failed login attempts.";
        System.out.println(line);
    }
}
```

**How to run:** `java --enable-preview --source 22 ReportSingleLine.java` (JDK 22+).

This is the single-line interpolation pattern already available in the first preview round — a good baseline before combining templates with multi-line text blocks.

### Level 2 — Intermediate

```java
public class ReportMultiLine {
    public static void main(String[] args) {
        String name = "Ada";
        int failedAttempts = 2;

        String report = STR."""
            User: \{name}
            Failed login attempts: \{failedAttempts}
            """;

        System.out.println(report);
    }
}
```

**How to run:** `java --enable-preview --source 22 ReportMultiLine.java`.

The real-world concern added: the same interpolation now happens inside a **multi-line text block**, where the literal indentation on each line is stripped according to text-block rules while the `\{...}` expressions are still substituted correctly on each line — the specific combination this round's refinements targeted.

### Level 3 — Advanced

```java
import java.util.*;

public class ReportAdvanced {
    record LoginAttempt(String user, boolean succeeded, String ipAddress) {}

    static String formatReport(String name, List<LoginAttempt> attempts) {
        long failedCount = attempts.stream().filter(a -> !a.succeeded()).count();
        String status = failedCount >= 3 ? "LOCKED" : "active";

        StringBuilder attemptLines = new StringBuilder();
        for (LoginAttempt a : attempts) {
            attemptLines.append(STR."  - \{a.succeeded() ? "OK  " : "FAIL"} from \{a.ipAddress()}\n");
        }

        return STR."""
            User: \{name}
            Status: \{status}
            Failed attempts: \{failedCount} / \{attempts.size()}
            Attempt log:
            \{attemptLines}""";
    }

    public static void main(String[] args) {
        List<LoginAttempt> attempts = List.of(
            new LoginAttempt("ada", true, "10.0.0.1"),
            new LoginAttempt("ada", false, "10.0.0.2"),
            new LoginAttempt("ada", false, "10.0.0.3"),
            new LoginAttempt("ada", false, "10.0.0.4")
        );

        System.out.println(formatReport("ada", attempts));
    }
}
```

**How to run:** `java --enable-preview --source 22 ReportAdvanced.java`.

This adds the production-flavored hard case: a **nested embedded expression** (`\{attemptLines}`, itself a `StringBuilder` built from another templated interpolation per attempt) inside a multi-line templated text block, combining computed status text, counts, and a dynamically-built multi-line sub-report — the kind of composed, real-world reporting output a templated text block needs to handle correctly.

## 6. Walkthrough

Tracing `ReportAdvanced.main`:

1. `main` builds a list of four login attempts for user `"ada"`, one successful and three failed, and calls `formatReport("ada", attempts)`.
2. Inside `formatReport`, `failedCount` is computed via a stream filter-and-count: `3` (the three `succeeded() == false` entries). `status` becomes `"LOCKED"` since `failedCount >= 3`.
3. The loop builds `attemptLines`, appending one line per attempt using a single-line template (`STR."  - \{a.succeeded() ? "OK  " : "FAIL"} from \{a.ipAddress()}\n"`), producing four lines of text, each ending in an explicit `\n` since `StringBuilder` doesn't know about text-block indentation rules.
4. The final `STR."""..."""` templated text block interpolates `name`, `status`, `failedCount`, `attempts.size()`, and — as its last embedded expression — the entire `attemptLines` string, which itself contains multiple lines built up from the loop.
5. Text-block indentation stripping applies to the *literal* portions of this multi-line template (removing the common leading whitespace from each line of the source code), while every `\{...}` expression's value — including the multi-line `attemptLines` content — is substituted in as-is, without additional indentation manipulation applied to the substituted values themselves.
6. `formatReport` returns the combined multi-line string, which `main` prints directly.

Expected output:
```
User: ada
Status: LOCKED
Failed attempts: 3 / 4
Attempt log:
  - OK   from 10.0.0.1
  - FAIL from 10.0.0.2
  - FAIL from 10.0.0.3
  - FAIL from 10.0.0.4
```

## 7. Gotchas & takeaways

> **Gotcha:** an embedded expression's *substituted value* is inserted exactly as computed — it does **not** get re-indented to match the surrounding text block's indentation level. If `attemptLines` in the example above had its own inconsistent leading whitespace, that whitespace would appear verbatim in the final output, since only the literal fragments of the *outer* template participate in text-block indentation stripping.

- Second preview round, Java 22 — refines how string templates interact with multi-line text blocks specifically.
- `STR."""..."""` combines a text block's multi-line literal syntax with `\{...}` interpolation; indentation stripping applies only to the literal fragments, not to substituted expression values.
- Nesting templated expressions (a template's `\{...}` evaluating to a string built by another template) works, but the inner content isn't re-indented to match the outer block.
- Still a preview — the exact rules for text-block-and-template interaction were still being refined in this round; treat this as a Java 22 snapshot of an evolving feature (see [string templates (preview)](0750-string-templates-preview.md) for the broader caveat about this feature's eventual direction).
- Prefer explicit `\n` or a clearly separated helper string when building multi-line content that will itself be embedded into an outer template, to keep indentation behavior predictable.
