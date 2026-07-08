---
card: java
gi: 460
slug: lambda-syntax-params-body
title: Lambda syntax (params) -> body
---

## 1. What it is

A **lambda expression**, added in Java 8, is a compact way to write an implementation of a single method as a value — no class name, no method name, just `(parameters) -> body`. It's Java's answer to "I need to pass a small piece of behaviour somewhere" without writing a whole named class for it. The arrow `->` separates the parameter list on the left from the code that runs on the right.

## 2. Why & when

Before Java 8, passing "a bit of behaviour" as an argument meant writing an **anonymous class** — a full `new Comparator<String>() { public int compare(...) { ... } }` block, with boilerplate (the interface name repeated, the method name repeated, braces, `public`, a `return`) surrounding one line of actual logic. That ceremony discouraged small, ad-hoc behaviour and made simple things like "sort these by length" read far longer than the idea itself.

You reach for a lambda whenever an API expects a **functional interface** — an interface with exactly one abstract method, like `Comparator`, `Runnable`, or the `java.util.function` interfaces covered later in this section — and you have a short, self-contained piece of logic to supply. Sorting a list with a custom comparison, filtering a stream, or defining what happens when a button is clicked are all classic uses; anywhere you would once have written a one-method anonymous class, a lambda now says the same thing in far less code.

## 3. Core concept

```java
import java.util.*;

List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "Bob"));

// The old way: an anonymous class implementing Comparator<String>
names.sort(new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.compareTo(b);
    }
});

// The lambda way: same behaviour, one line
names.sort((a, b) -> a.compareTo(b));
```

`(a, b) -> a.compareTo(b)` reads as: "given two parameters `a` and `b`, evaluate `a.compareTo(b)` and use that as the result." The compiler infers, from context, that this lambda must implement `Comparator<String>.compare(String, String)` — there is no need to repeat the interface or method name anywhere in the lambda itself.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An anonymous class with repeated boilerplate collapses into a single lambda expression with a parameter list and a body">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">Anonymous class (Java 7 and earlier)</text>
  <rect x="20" y="38" width="600" height="46" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="58" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="monospace">new Comparator&lt;String&gt;() { public int compare(String a, String b) { return a.compareTo(b); } }</text>

  <text x="20" y="105" fill="#8b949e" font-size="11" font-family="sans-serif">Lambda expression (Java 8+)</text>
  <rect x="20" y="115" width="600" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="137" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">(a, b)</text>
  <text x="185" y="137" fill="#e6edf3" font-size="12" font-family="monospace">-&gt;</text>
  <text x="330" y="137" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">a.compareTo(b)</text>
</svg>

Same behaviour, same interface implemented — only the ceremony around it disappears.

## 5. Runnable example

Scenario: sorting a small roster of names — evolved from an anonymous-class comparator, through the equivalent lambda form, to a lambda whose body is a full block with multiple statements and an explicit `return`.

### Level 1 — Basic

```java
import java.util.*;

public class LambdaBasicOld {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "Bob"));

        names.sort(new Comparator<String>() {
            @Override
            public int compare(String a, String b) {
                return a.compareTo(b);
            }
        });

        System.out.println(names);
    }
}
```

**How to run:** `java LambdaBasicOld.java`

Expected output:
```
[Alice, Bob, Charlie]
```

This is the pre-lambda way: an anonymous class implementing `Comparator<String>`, overriding its single abstract method `compare`. It works, but every part of the interface's shape — its name, its method name, the `public`, the `return` — has to be spelled out even though the only "new" information is the single line `a.compareTo(b)`.

### Level 2 — Intermediate

```java
import java.util.*;

public class LambdaBasicNew {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "Bob"));

        // Same behaviour as LambdaBasicOld -- a lambda replaces the whole anonymous class.
        names.sort((a, b) -> a.compareTo(b));

        System.out.println(names);
    }
}
```

**How to run:** `java LambdaBasicNew.java`

Expected output:
```
[Alice, Bob, Charlie]
```

The real-world concern this adds: readability at the call site. `names.sort((a, b) -> a.compareTo(b))` puts the *sorting logic itself* front and center — a reader sees immediately "sort by comparing `a` to `b`" without first mentally skipping past interface and method declarations to find the one line that matters.

### Level 3 — Advanced

```java
import java.util.*;

public class LambdaBlockBody {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "bob", "alice"));

        // A block-body lambda: multiple statements, braces, and an explicit return --
        // needed here because the comparison logic is more than one expression.
        names.sort((a, b) -> {
            String normalizedA = a.toLowerCase();
            String normalizedB = b.toLowerCase();
            int result = normalizedA.compareTo(normalizedB);
            if (result != 0) {
                return result;
            }
            // Case-insensitive tie: fall back to natural (case-sensitive) order for stability.
            return a.compareTo(b);
        });

        System.out.println(names);
    }
}
```

**How to run:** `java LambdaBlockBody.java`

Expected output:
```
[Alice, alice, bob, Charlie]
```

When the logic needs more than one expression — local variables, an `if`, multiple steps — the lambda body becomes a **block**: braces `{ }` wrap ordinary statements, and an explicit `return` supplies the result, exactly like a normal method body would.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `names` holds `["Charlie", "Alice", "bob", "alice"]` before sorting.

`names.sort(lambda)` calls `List.sort(Comparator)`, which internally performs a comparison-based sort (Java's `List.sort` uses a stable merge-sort-derived algorithm), invoking the supplied lambda every time it needs to compare two elements to decide their relative order.

Each invocation runs the lambda's block body with two `String` parameters, `a` and `b`, bound to whichever two names the sort algorithm is currently comparing. `normalizedA` and `normalizedB` lower-case both inputs, so `"Alice"` and `"alice"` become indistinguishable at this stage. `result = normalizedA.compareTo(normalizedB)` compares those lower-cased forms lexicographically. If `result != 0`, the two names differ even ignoring case, and that comparison result is returned immediately, driving the sort order.

If `result == 0`, the two names are equal ignoring case — this happens, for example, when comparing `"Alice"` and `"alice"`. In that case, the lambda falls through to `return a.compareTo(b)`, comparing the **original**, case-sensitive strings instead, so the tie is broken deterministically rather than left to chance.

```
compare("Charlie","Alice") -> normalized "charlie" vs "alice" -> result != 0 -> return that
compare("Alice","alice")   -> normalized "alice" vs "alice"   -> result == 0 -> tie-break: "Alice".compareTo("alice")
```

After the sort completes, `names` is ordered case-insensitively, with case-sensitive order used only to break ties between names that are equal ignoring case — producing `[Alice, alice, bob, Charlie]` (uppercase `'A'` sorts before lowercase `'a'` in `String.compareTo`'s character-code ordering, since uppercase letters have lower Unicode code points than their lowercase counterparts, and `"bob"`/`"Charlie"` differ enough in their first letters that case doesn't create a tie for them).

## 7. Gotchas & takeaways

> A lambda with a **single expression** (no braces) implicitly returns that expression's value — you must *not* write `return` in that form, and you must *not* add a semicolon before the closing context. `(a, b) -> a.compareTo(b)` is correct; `(a, b) -> { return a.compareTo(b); }` is also correct (block form), but `(a, b) -> return a.compareTo(b)` is a compile error — you cannot mix the two forms.

- `(parameters) -> expression` is the single-expression form: no braces, no `return`, the expression's value is the result automatically.
- `(parameters) -> { statements }` is the block form: braces required, and an explicit `return` is required if the lambda produces a value.
- A lambda's shape (parameter count and types, return type) must exactly match the single abstract method of whatever functional interface the context expects — the compiler works out which interface that is from where the lambda is used.
- Lambdas replace the *boilerplate* of anonymous classes, not the underlying mechanism — under the hood, a lambda still ultimately provides an implementation of one interface method (Java 8 in fact implements this compilation using `invokedynamic`, not an anonymous class file).
- Reach for the block form only when you genuinely need more than one statement — a single-expression lambda is almost always more readable when the logic fits on one line.
