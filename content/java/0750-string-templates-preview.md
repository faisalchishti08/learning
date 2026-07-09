---
card: java
gi: 750
slug: string-templates-preview
title: String templates (preview)
---

## 1. What it is

**Java 21** (JEP 430) previews **string templates**: a new syntax, `STR."text \{expression} more text"`, that embeds Java expressions directly inside a string literal and interpolates their values, similar to interpolated strings in many other languages (JavaScript template literals, Python f-strings, Kotlin string templates). `STR` is a built-in **template processor** — the piece that turns the template plus its embedded expressions into a final value — and it's not the only one: `FMT` supports `printf`-style format specifiers per embedded expression, and libraries or application code can define **custom template processors** that produce something other than a plain string entirely (a safely-escaped SQL query, a validated JSON object). Being a preview feature, it requires `--enable-preview` at both compile and run time, and its final syntax changed before eventual withdrawal from later JDKs in favor of a different approach — so treat this specifically as a Java 21 preview snapshot.

## 2. Why & when

String concatenation and `String.format` both have real, well-known problems once a string is built from several dynamic pieces: `"Hello, " + name + "! You have " + count + " new messages."` is hard to read once there are more than two or three interpolated values, because the literal text and the expressions are visually interleaved with `+` operators that add noise without adding meaning; `String.format("Hello, %s! You have %d new messages.", name, count)` fixes the readability of the literal text but separates it from its arguments, so matching `%s`/`%d` conversion slots to the right variable requires counting positions. String templates put the expression **directly where its value will appear** in the text — `STR."Hello, \{name}! You have \{count} new messages."` — which is both more readable and, importantly, safer: because the template processor sees the literal fragments and the expressions as separate, structured pieces (not a single already-concatenated string), a processor can validate or escape each embedded value appropriately for its destination — critical for avoiding injection vulnerabilities when the output is SQL, HTML, or a shell command, which plain concatenation cannot help with at all.

## 3. Core concept

```java
String name = "Ada";
int count = 3;

String message = STR."Hello, \{name}! You have \{count} new messages.";
// "Hello, Ada! You have 3 new messages."

String formatted = FMT."Balance: %,.2f\{1234.5}"; // FMT applies printf-style specifiers
// "Balance: 1,234.50"
```

`\{...}` marks an embedded expression; `STR` interpolates it as-is (via `toString()`), while `FMT` additionally applies a `printf`-style conversion specifier placed just before the `\{...}`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A string template splits into literal fragments and embedded expressions, which a template processor combines into a final value, with the option to validate or escape each expression along the way">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">STR."Hello, \{name}! You have \{count} messages."</text>

  <rect x="20" y="90" width="180" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">literal fragments</text>

  <rect x="230" y="90" width="180" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">embedded expressions</text>

  <rect x="440" y="90" width="180" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="530" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">template processor</text>

  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The processor decides HOW fragments and expressions combine — plain text, formatted, escaped, or validated</text>
</svg>

*A template is structured data — fragments plus expressions — until a processor decides how to combine them.*

## 5. Runnable example

Scenario: building a user-facing status message, growing from concatenation into `STR`, `FMT`, and a small custom processor that guards against unsafe input.

### Level 1 — Basic

```java
public class TemplateConcat {
    public static void main(String[] args) {
        String name = "Ada";
        int unread = 3;
        String message = "Hello, " + name + "! You have " + unread + " new messages.";
        System.out.println(message);
    }
}
```

**How to run:** `java TemplateConcat.java` (JDK 21+, no preview flag needed for plain concatenation).

This is the baseline `+`-concatenation style: correct, but the literal text and the two variables are interleaved with operators, and it only gets harder to scan as more values are added.

### Level 2 — Intermediate

```java
public class TemplateStr {
    public static void main(String[] args) {
        String name = "Ada";
        int unread = 3;
        double balance = 1234.5;

        String message = STR."Hello, \{name}! You have \{unread} new messages.";
        String formatted = FMT."Account balance: $%,.2f\{balance}";

        System.out.println(message);
        System.out.println(formatted);
    }
}
```

**How to run:** `java --enable-preview --source 21 TemplateStr.java` (preview features require the flag at both compile and run time; running the single-file source-launcher form still needs `--enable-preview`).

The real-world concern added: `STR` interpolates `name` and `unread` directly at the point they appear in the text (no `+` operators, no counting positional slots), and `FMT` additionally applies a `printf`-style specifier (`%,.2f`, meaning "comma-grouped, two decimal places") immediately before each embedded expression — combining formatting and interpolation in one place.

### Level 3 — Advanced

```java
import java.util.*;

public class TemplateSafeQuery {
    // A minimal custom template processor: validates that no embedded value
    // contains a single quote, to guard against naive SQL string injection.
    static String safeSql(StringTemplate template) {
        List<String> fragments = template.fragments();
        List<Object> values = template.values();
        StringBuilder result = new StringBuilder(fragments.get(0));
        for (int i = 0; i < values.size(); i++) {
            String value = String.valueOf(values.get(i));
            if (value.contains("'")) {
                throw new IllegalArgumentException("unsafe value rejected: " + value);
            }
            result.append("'").append(value).append("'");
            result.append(fragments.get(i + 1));
        }
        return result.toString();
    }

    public static void main(String[] args) {
        String safeName = "Ada Lovelace";
        String unsafeName = "Robert'); DROP TABLE users; --";

        StringTemplate query1 = StringTemplate.RAW."SELECT * FROM users WHERE name = \{safeName}";
        System.out.println(safeSql(query1));

        StringTemplate query2 = StringTemplate.RAW."SELECT * FROM users WHERE name = \{unsafeName}";
        try {
            System.out.println(safeSql(query2));
        } catch (IllegalArgumentException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview --source 21 TemplateSafeQuery.java`.

This adds the production-flavored hard case: a **custom template processor**, `safeSql`, built on `StringTemplate.RAW` (which gives access to the raw fragments and unprocessed embedded values, rather than an already-interpolated string) so it can inspect each embedded value **before** it's woven into the final string — rejecting one that contains a single quote, the classic vector for naive SQL string injection. This is the concrete reason string templates exist as structured data rather than pre-built strings: `STR` alone can't protect against this, but a processor built on the same mechanism can.

## 6. Walkthrough

Tracing `TemplateSafeQuery.main`'s handling of `query2`:

1. `StringTemplate.RAW."SELECT * FROM users WHERE name = \{unsafeName}"` does **not** produce a `String` — `StringTemplate.RAW` is itself a template processor, but a trivial one that just packages the template's literal fragments and embedded expression values into a `StringTemplate` object without combining them, ready for a custom processor to inspect.
2. The resulting `StringTemplate` has `fragments() = ["SELECT * FROM users WHERE name = ", ""]` (the literal text before and after the single embedded expression) and `values() = [unsafeName]` (the actual runtime value of `\{unsafeName}`, i.e. `"Robert'); DROP TABLE users; --"`).
3. `safeSql(query2)` is called. Inside, `result` starts as a copy of `fragments.get(0)`, `"SELECT * FROM users WHERE name = "`.
4. The loop's single iteration (`i = 0`) reads `values.get(0)`, the unsafe name string, and checks `value.contains("'")`. Since the string does contain a single quote, this check is `true`, and the method immediately throws `IllegalArgumentException` **before** the value is ever appended into the query string — the injection attempt never reaches the point of being embedded in SQL text at all.
5. Back in `main`, the `try` block catches this exception and prints the rejection message instead of the (unsafe) query.

For `query1` (the safe name), the same walkthrough applies but the `contains("'")` check is `false`, so execution proceeds past it: `result` becomes `"SELECT * FROM users WHERE name = 'Ada Lovelace"`, then `fragments.get(1)` (the empty trailing fragment) is appended, giving the final string `"SELECT * FROM users WHERE name = 'Ada Lovelace'"`.

Expected output:
```
SELECT * FROM users WHERE name = 'Ada Lovelace'
rejected: unsafe value rejected: Robert'); DROP TABLE users; --
```

## 7. Gotchas & takeaways

> **Gotcha:** this is a **preview** feature in Java 21, and it later changed shape (and was ultimately withdrawn as a preview in favor of a different direction) in subsequent JDK releases. Code written against this exact `STR`/`FMT`/`StringTemplate.RAW` syntax should be treated as a snapshot of the Java 21 preview, not a long-term API to build production code on without checking the JDK version you actually intend to ship on.

- Requires `--enable-preview` at both compile time and run time on JDK 21.
- `STR` interpolates embedded expressions as plain text (via `toString()`); `FMT` additionally applies `printf`-style conversion specifiers per expression.
- A template is structured data (fragments + values) until a processor combines them — `StringTemplate.RAW` exposes that structure directly for writing custom processors.
- The real safety benefit over concatenation is that a custom processor can validate or escape each embedded value individually, before it becomes part of the output — something string concatenation offers no hook for at all.
- Treat this feature as preview-only and version-sensitive; check your target JDK's actual final string-interpolation mechanism before relying on this exact syntax in real code.
