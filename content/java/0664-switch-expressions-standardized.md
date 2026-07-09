---
card: java
gi: 664
slug: switch-expressions-standardized
title: Switch expressions — standardized
---

## 1. What it is

**Java 14** (JEP 361) made switch expressions a **permanent, standard language feature** — the same arrow-based (`case X -> value`) syntax previewed in Java 12 and refined with `yield` in Java 13's second preview, now finalized with no `--enable-preview` flag required. This is the point where `switch` genuinely became two things: the classic colon-based `switch` **statement** (unchanged, still fall-through by default), and the new arrow-based `switch` **expression** that produces a value, has no fall-through, and requires exhaustiveness. Both forms coexist permanently in the language from Java 14 onward — you choose whichever fits your situation, statement for pure control flow, expression for computing a value.

## 2. Why & when

By the time this stabilized, two full preview cycles (Java 12, Java 13) had exercised the design against real feedback, settling questions like exhaustiveness checking, how `yield` interacts with nested constructs, and multi-label arms (`case A, B, C ->`). Standardizing it means you can now use switch expressions in production code on any Java 14+ runtime without preview flags, without worrying the syntax might still change, and without the awkwardness of gating a whole build on an experimental feature. Reach for a switch expression any time you're mapping an input to a computed value — this was already the guidance during the preview phases (see [Switch expressions (preview)](0647-switch-expressions-preview.md) and [Switch expressions yield (2nd preview)](0659-switch-expressions-yield-2nd-preview.md)); the only change now is that it's simply part of the language, usable freely.

## 3. Core concept

```java
// No preview flag needed anymore — this just compiles and runs on Java 14+
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    default -> {
        String name = day.toString();
        yield name.length();
    }
};

// The classic switch STATEMENT is untouched — still available, still fall-through
switch (day) {
    case MONDAY:
        System.out.println("Start of week");
        break;
    default:
        System.out.println("Some other day");
}
```

`javac SwitchDemo.java` and `java SwitchDemo` now just work — Java 14 removed the `--enable-preview`/`--release` gymnastics that Java 12 and 13 required for this exact syntax.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 12 preview and Java 13 second preview converge into a permanent, standard switch expression feature in Java 14">
  <rect x="10" y="15" width="160" height="50" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="35" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Java 12</text>
  <text x="90" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1st preview (break value)</text>

  <rect x="220" y="15" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="300" y="35" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Java 13</text>
  <text x="300" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">2nd preview (yield)</text>

  <line x1="170" y1="40" x2="215" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#sw1)"/>
  <line x1="380" y1="40" x2="425" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#sw2)"/>

  <rect x="220" y="95" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="115" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 14: STANDARD</text>
  <text x="320" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">No flags. Permanent language feature.</text>

  <defs>
    <marker id="sw1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="sw2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Two preview cycles of refinement converge into one permanent feature — the arrow syntax and `yield` from Java 13 are exactly what shipped as final in Java 14.

## 5. Runnable example

Scenario: classifying an HTTP status code into a category — first as a plain standardized switch expression (no preview flags), then extended with multi-statement arms using `yield`, then a version demonstrating exhaustiveness checking by working over a `sealed`-style fixed set of values (an enum) where the compiler can verify every case is handled without a `default`.

### Level 1 — Basic

```java
// File: StatusCategory.java
public class StatusCategory {
    static String category(int status) {
        return switch (status / 100) {
            case 1 -> "Informational";
            case 2 -> "Success";
            case 3 -> "Redirection";
            case 4 -> "Client Error";
            case 5 -> "Server Error";
            default -> "Unknown";
        };
    }

    public static void main(String[] args) {
        for (int code : new int[]{101, 200, 301, 404, 500, 999}) {
            System.out.println(code + " -> " + category(code));
        }
    }
}
```

**How to run:** `java StatusCategory.java` — no `--enable-preview`, no `--release` flag; this is now completely standard Java.

Expected output:
```
101 -> Informational
200 -> Success
301 -> Redirection
404 -> Client Error
500 -> Server Error
999 -> Unknown
```

### Level 2 — Intermediate

```java
// File: StatusCategoryDetailed.java
public class StatusCategoryDetailed {
    static String describe(int status) {
        return switch (status / 100) {
            case 2 -> "Success (" + status + ")";
            case 4, 5 -> {
                String severity = status / 100 == 5 ? "server-side" : "client-side";
                yield "Error [" + severity + "]: " + status;
            }
            default -> "Other: " + status;
        };
    }

    public static void main(String[] args) {
        for (int code : new int[]{200, 404, 500, 302}) {
            System.out.println(describe(code));
        }
    }
}
```

**How to run:** `java StatusCategoryDetailed.java`

Expected output:
```
Success (200)
Error [client-side]: 404
Error [server-side]: 500
Other: 302
```

Grouping `4` and `5` into one arm and using `yield` inside a `{ }` block to compute a multi-part message — exactly the syntax finalized from the Java 13 preview, now used without any flags.

### Level 3 — Advanced

```java
// File: HttpMethodHandler.java
public class HttpMethodHandler {
    enum Method { GET, POST, PUT, DELETE, PATCH }

    static String handle(Method method) {
        // No 'default' needed: the compiler proves this covers every Method value.
        return switch (method) {
            case GET -> "Fetching resource";
            case POST -> "Creating resource";
            case PUT -> "Replacing resource";
            case DELETE -> "Removing resource";
            case PATCH -> {
                String note = "(partial update)";
                yield "Updating resource " + note;
            }
        };
    }

    public static void main(String[] args) {
        for (Method m : Method.values()) {
            System.out.println(m + " -> " + handle(m));
        }
    }
}
```

**How to run:** `java HttpMethodHandler.java`

Expected output:
```
GET -> Fetching resource
POST -> Creating resource
PUT -> Replacing resource
DELETE -> Removing resource
PATCH -> Updating resource (partial update)
```

Level 3 switches over an `enum`, where the compiler can statically verify all five `Method` constants are handled — no `default` arm is written or needed; if a sixth constant were added to `Method` later without updating `handle`, this code would **fail to compile**, catching the omission immediately rather than silently falling through to an unhandled case at runtime.

## 6. Walkthrough

1. `main` iterates `Method.values()`, which returns all five enum constants in declaration order: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`.
2. For `m = Method.PATCH`, `handle(PATCH)` is called. Control enters `switch (method)`, and the compiler-generated dispatch matches `PATCH` against the `case PATCH ->` arm's block.
3. Inside that block, `note` is assigned the literal string `"(partial update)"`.
4. `yield "Updating resource " + note;` concatenates the strings and produces `"Updating resource (partial update)"` as this arm's value — which becomes the value of the entire switch expression for this call.
5. `handle` returns that string to `main`, which prints `"PATCH -> Updating resource (partial update)"`.
6. Compare this to what the compiler checked **before** any of this ran: because `Method` is an `enum` with exactly five constants, and the `switch` here has one arm per constant with no `default`, the Java compiler performed **exhaustiveness analysis** at compile time — verifying every possible `Method` value has a matching arm. This is a compile-time guarantee, not a runtime check: if `Method` gained a new constant (say, `HEAD`) without a corresponding `case HEAD ->` arm being added, this file would fail to compile with an error about a non-exhaustive switch, long before the missing case could cause a runtime surprise.
7. This exhaustiveness checking is one of the concrete payoffs of switch expressions being standardized: it turns "did I forget to handle a case?" from a runtime bug class into a compile-time error.

```
Method.values() = [GET, POST, PUT, DELETE, PATCH]
       │
       ▼ handle(PATCH)
switch matches case PATCH -> { yield "Updating resource (partial update)" }
       │
       ▼
"PATCH -> Updating resource (partial update)"
```

## 7. Gotchas & takeaways

> Standardization in Java 14 means the arrow-based switch expression syntax and `yield` are now **permanent** — but it also means any Java 12/13 preview-flag code (`--enable-preview`) written against the *evolving* preview syntax should be recompiled without preview flags on Java 14+; the preview flags themselves are gone for this specific feature (it's no longer a preview at all), and attempting to pass `--enable-preview` for switch expressions specifically is unnecessary from Java 14 onward.

- The classic colon-based `switch` **statement** is untouched and remains fully supported — arrow expressions are an addition, not a replacement.
- Exhaustiveness checking is a compile-time guarantee for `enum` switches (and, from Java 17+, for `sealed` type hierarchies) with no `default` arm — genuinely useful for catching missed cases early.
- `yield` remains scoped to switch-expression block arms; it has no special meaning inside a plain `switch` statement.
- No performance difference exists between the two switch forms at runtime — the choice is purely about which form fits your code's intent (control flow vs. value computation).
- If you see `--enable-preview` in build scripts targeting switch expressions specifically on Java 14+, it's stale and can be removed — the feature no longer requires it.
