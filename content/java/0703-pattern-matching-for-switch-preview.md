---
card: java
gi: 703
slug: pattern-matching-for-switch-preview
title: Pattern matching for switch (preview)
---

## 1. What it is

**Java 17** introduced **pattern matching for `switch`** as a **preview feature** (JEP 406), extending `switch` expressions and statements so `case` labels can test and destructure a value's *type*, not just match it against constants. A `case Circle c` label matches when the switch's selector is an instance of `Circle`, binding `c` to that value inside the case body — the same kind of type pattern already familiar from `instanceof` pattern matching (standardized one release earlier, in Java 16). This preview also added `case null` as a legal label (letting `switch` handle `null` explicitly instead of always throwing `NullPointerException`) and guarded patterns using `&&` to add an extra boolean condition to a type pattern, such as `case Integer i && i > 0`.

## 2. Why & when

Before this feature, dispatching behavior based on an object's runtime type meant either a chain of `if (x instanceof Foo f) ... else if (x instanceof Bar b) ...` statements, or a `switch` on some separately-maintained "kind" enum or tag field, both of which are more verbose and error-prone than a single `switch` expression that pattern-matches directly against the type hierarchy. This feature is designed to work hand-in-hand with the sealed types standardized in this same release: a `switch` over a sealed interface's implementations can, in later releases, be checked by the compiler for exhaustiveness without needing a `default` branch, because the compiler knows the complete, closed set of possible types. Reach for pattern matching in `switch` (keeping in mind it required `--enable-preview` in Java 17, and its exact guard syntax changed in later releases) whenever a series of `if/else instanceof` checks against a closed or well-known set of types would read more clearly as a single `switch`.

## 3. Core concept

```java
// Java 17 — requires --enable-preview --release 17
static String describe(Object obj) {
    return switch (obj) {
        case Integer i && i > 0 -> "positive integer: " + i;
        case Integer i -> "non-positive integer: " + i;
        case String s -> "string of length " + s.length();
        case null -> "it was null";
        default -> "something else: " + obj;
    };
}
```

Each `case` both tests `obj`'s type and, on a match, binds a new local variable (`i`, `s`) scoped to that branch — no separate cast needed.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch expression tests an Object against type patterns in order: a guarded Integer pattern, a plain Integer pattern, a String pattern, an explicit null case, and a default">
  <rect x="20" y="20" width="600" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">switch (obj) { ... }</text>

  <rect x="20" y="70" width="600" height="30" rx="5" fill="#161b22" stroke="#6db33f"/>
  <text x="320" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">case Integer i &amp;&amp; i &gt; 0 -&gt; "positive integer: " + i</text>

  <rect x="20" y="105" width="600" height="30" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="320" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">case Integer i -&gt; "non-positive integer: " + i</text>

  <rect x="20" y="140" width="600" height="30" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="320" y="160" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">case String s -&gt; "string of length " + s.length()</text>

  <rect x="20" y="175" width="290" height="30" rx="5" fill="#161b22" stroke="#f0883e"/>
  <text x="165" y="195" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">case null -&gt; "it was null"</text>

  <rect x="330" y="175" width="290" height="30" rx="5" fill="#161b22" stroke="#8b949e"/>
  <text x="475" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">default -&gt; "something else"</text>
</svg>

Labels are tried top to bottom; the first type pattern that matches (and whose guard, if any, is true) wins — including an explicit `null` label.

## 5. Runnable example

Scenario: a small event-classification function for a logging pipeline — first the basic type-pattern `switch` over a few event payload types, then adding a guarded pattern to split one type into sub-cases based on a runtime condition, then a fuller version that also handles `null` explicitly and falls back to a `default` for anything unrecognized, exactly the shape a real log-processing dispatcher would take.

### Level 1 — Basic

```java
// File: EventDescribeBasic.java
// compile & run with: --enable-preview --release 17
public class EventDescribeBasic {
    static String describe(Object event) {
        return switch (event) {
            case Integer i -> "numeric event code: " + i;
            case String s -> "text event: " + s;
            default -> "unrecognized event: " + event;
        };
    }

    public static void main(String[] args) {
        Object[] events = { 404, "user-login", 3.14 };
        for (Object event : events) {
            System.out.println(describe(event));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 17 EventDescribeBasic.java
java --enable-preview EventDescribeBasic
```

Expected output:
```
numeric event code: 404
text event: user-login
unrecognized event: 3.14
```

### Level 2 — Intermediate

```java
// File: EventDescribeGuarded.java
// compile & run with: --enable-preview --release 17
public class EventDescribeGuarded {
    static String describe(Object event) {
        return switch (event) {
            case Integer i && i >= 500 -> "server error code: " + i;
            case Integer i && i >= 400 -> "client error code: " + i;
            case Integer i -> "informational code: " + i;
            case String s -> "text event: " + s;
            default -> "unrecognized event: " + event;
        };
    }

    public static void main(String[] args) {
        Object[] events = { 200, 404, 503, "user-login" };
        for (Object event : events) {
            System.out.println(describe(event));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 17 EventDescribeGuarded.java
java --enable-preview EventDescribeGuarded
```

Expected output:
```
informational code: 200
client error code: 404
server error code: 503
text event: user-login
```

Guarded patterns (`case Integer i && i >= 500`) are tried in source order, and the **first** matching guarded case wins — `503` matches `i && i >= 500` before it ever reaches the `i >= 400` case, so ordering guarded patterns from most to least specific matters, exactly like a chain of `if/else if`.

### Level 3 — Advanced

```java
// File: EventDescribeFull.java
// compile & run with: --enable-preview --release 17
import java.util.List;

public class EventDescribeFull {
    record LogEntry(String source, int code) {}

    static String describe(Object event) {
        return switch (event) {
            case null -> "no event (null received)";
            case LogEntry entry && entry.code() >= 500 -> "[" + entry.source() + "] server error " + entry.code();
            case LogEntry entry && entry.code() >= 400 -> "[" + entry.source() + "] client error " + entry.code();
            case LogEntry entry -> "[" + entry.source() + "] ok, code " + entry.code();
            case String s -> "raw text event: " + s;
            default -> "unrecognized event: " + event;
        };
    }

    public static void main(String[] args) {
        List<Object> events = new java.util.ArrayList<>(List.of(
                new LogEntry("auth-service", 200),
                new LogEntry("billing-service", 404),
                new LogEntry("payments-service", 503),
                "raw-heartbeat-ping"
        ));
        events.add(null); // explicitly test the null-handling branch

        for (Object event : events) {
            System.out.println(describe(event));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 17 EventDescribeFull.java
java --enable-preview EventDescribeFull
```

Expected output:
```
[auth-service] ok, code 200
[billing-service] client error 404
[payments-service] server error 503
raw text event: raw-heartbeat-ping
no event (null received)
```

## 6. Walkthrough

1. `main` builds a mutable `List<Object>` of four real events (three `LogEntry` records and one plain `String`), then appends a `null` at the end — using `new ArrayList<>(List.of(...))` rather than `List.of(...)` directly, since `List.of` produces an immutable list that would reject `add(null)`.
2. Iterating the list, each element is passed to `describe`, whose `switch` expression evaluates its `case` labels **in source order**, stopping at the first one that both matches the value's type and (if present) satisfies its guard.
3. For `new LogEntry("auth-service", 200)`: `case null` doesn't match (it's not null); `case LogEntry entry && entry.code() >= 500` matches the type but fails the guard (`200 >= 500` is false); the same happens for the `>= 400` guard; finally `case LogEntry entry` (no guard) matches unconditionally, binding `entry` and producing `"[auth-service] ok, code 200"`.
4. For `new LogEntry("payments-service", 503)`: the very first `LogEntry` case's guard (`entry.code() >= 500`) succeeds immediately, so the switch short-circuits there without ever evaluating the `>= 400` or unguarded `LogEntry` cases — order matters precisely because guards are evaluated top to bottom like an `if/else if` chain, not by "most specific match wins" the way overload resolution works.
5. For the plain `String` element, none of the `LogEntry` cases can match at all (a type pattern only matches if the value actually *is* that type), so control falls through to `case String s`.
6. Finally, for the `null` appended at the end, `case null` matches explicitly and short-circuits before any type pattern is even attempted — without this label, passing `null` into this `switch` would throw a `NullPointerException`, since ordinary `switch` (before this feature) never permitted a `null` selector.

```
switch (event):
  event == null?              -> case null
  event instanceof LogEntry && code>=500?   -> "server error"
  event instanceof LogEntry && code>=400?   -> "client error"
  event instanceof LogEntry?                -> "ok"
  event instanceof String?                  -> "raw text event"
  (none matched)                            -> default
```

## 7. Gotchas & takeaways

> Pattern matching for `switch` was a **preview feature in Java 17** — both `javac` and `java` required `--enable-preview`, and the exact guard syntax shown here (`case Pattern p && condition`) was **replaced in a later release's preview** by a dedicated `when` clause (`case Pattern p when condition`) for improved readability and to avoid ambiguity with pattern combinators. Code written against this Java 17 preview's `&&`-guard syntax will not compile unchanged against later JDK previews or the eventual standardized feature.
- `case null` must be written explicitly to handle `null`; without it, a `null` selector still throws `NullPointerException` just as it always has, for full backward compatibility with existing `switch` code.
- Guarded and unguarded patterns are matched **in source order**, top to bottom — put more specific guarded cases before more general ones, exactly as you would order an `if/else if` chain.
- A pattern-matching `switch` used as an *expression* (as in all the examples here) must still be **exhaustive** — the compiler requires a `default` branch (or, for a sealed hierarchy in later releases, proof that every permitted subtype is covered) so every possible input produces a value.
- This feature is designed to pair with [sealed classes & interfaces](0701-sealed-classes-interfaces-standardized.md), standardized in this very same release — a `switch` over a sealed hierarchy's known subtypes is the case this feature was built to make both concise and, eventually, compiler-verified exhaustive.
- Because it remained a preview feature through Java 17, treat any production use as experimental — re-verify behavior and syntax against whichever later JDK release you actually deploy on before relying on it outside of learning or prototyping contexts.
