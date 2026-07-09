---
card: java
gi: 680
slug: pattern-matching-for-instanceof-2nd-preview
title: Pattern matching for instanceof (2nd preview)
---

## 1. What it is

**Pattern matching for `instanceof`**, first previewed in Java 14, returned for a **second preview** in **Java 15** (JEP 375) essentially unchanged in syntax but re-previewed to gather further feedback before finalization. The feature lets `instanceof` both **test** an object's type and **bind** a variable of that type in one expression: `if (obj instanceof String s)` checks whether `obj` is a `String` and, if so, makes `s` available (already cast) inside the `if`'s scope — eliminating the old pattern of `instanceof` followed by a separate, redundant explicit cast.

## 2. Why & when

The traditional idiom — `if (obj instanceof String) { String s = (String) obj; ... }` — repeats the type name three times (the check, the cast, the declared variable's type) and forces an extra line purely to introduce a variable the compiler could already prove was safe to create. This redundancy is exactly the kind of boilerplate pattern matching eliminates: the compiler already knows, right after a successful `instanceof String` check, that the value is safely a `String`, so it can simply hand you a variable of that narrowed type immediately. Reach for pattern-matching `instanceof` anywhere you would otherwise write an `instanceof` check immediately followed by a cast — type-dispatch logic over a small hierarchy (especially once paired with [sealed classes (preview)](0678-sealed-classes-preview.md)), visitor-style code, or defensive type-narrowing in methods that accept a general supertype like `Object`.

## 3. Core concept

```java
Object obj = "hello";

// Before pattern matching: check, then separately cast
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.length());
}

// Java 15 (2nd preview) — requires --enable-preview --release 15
if (obj instanceof String s) {
    System.out.println(s.length()); // s is already a String here, no cast needed
}
```

The pattern variable `s` is only in scope where the compiler can prove the `instanceof` check succeeded — inside the `if`'s true branch, or in code paths reachable only when the check is true (a subtlety the second preview clarified further, see part 6).

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="instanceof pattern match narrows the type and binds a variable that is scoped to where the check is known to be true">
  <rect x="30" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">obj instanceof String s</text>
  <text x="140" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">test + bind, one expression</text>

  <line x1="140" y1="70" x2="140" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="200" y="90" fill="#79c0ff" font-size="10" font-family="sans-serif">true</text>

  <rect x="30" y="110" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">"s" is in scope here</text>
  <text x="140" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">s.length() — no cast</text>

  <rect x="330" y="110" width="220" height="60" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="440" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"s" is NOT in scope here</text>
  <text x="440" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(the "false" branch)</text>

  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The bound pattern variable only exists where the compiler has statically proven the type check succeeded.

## 5. Runnable example

Scenario: a small "describe any object" utility — first a simple type-narrowing check, then chained `instanceof` patterns across an `Object`-typed collection, then flow-scoping tricks (negated checks with early `return`, and combining patterns with `&&`) that only work because the compiler tracks *where* a pattern variable is definitely true.

### Level 1 — Basic

```java
// File: DescribeBasic.java
// compile & run with: --enable-preview --release 15
public class DescribeBasic {
    static String describe(Object obj) {
        if (obj instanceof String s) {
            return "String of length " + s.length();
        }
        if (obj instanceof Integer i) {
            return "Integer, doubled = " + (i * 2);
        }
        return "Unknown: " + obj;
    }

    public static void main(String[] args) {
        System.out.println(describe("hello"));
        System.out.println(describe(21));
        System.out.println(describe(3.14));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 DescribeBasic.java
java --enable-preview DescribeBasic
```

Expected output:
```
String of length 5
Integer, doubled = 42
Unknown: 3.14
```

### Level 2 — Intermediate

```java
// File: DescribeList.java
// compile & run with: --enable-preview --release 15
import java.util.List;

public class DescribeList {
    static String describe(Object obj) {
        if (obj instanceof String s && !s.isBlank()) {
            return "Non-blank string: \"" + s + "\"";
        }
        if (obj instanceof String s) {
            return "Blank or empty string of length " + s.length();
        }
        if (obj instanceof List<?> list && !list.isEmpty()) {
            return "Non-empty list of size " + list.size();
        }
        return "Other: " + obj;
    }

    public static void main(String[] args) {
        List<Object> items = List.of("hello", "", List.of(1, 2, 3), 42);
        for (Object item : items) {
            System.out.println(describe(item));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 DescribeList.java
java --enable-preview DescribeList
```

Expected output:
```
Non-blank string: "hello"
Blank or empty string of length 0
Non-empty list of size 3
Other: 42
```

`obj instanceof String s && !s.isBlank()` shows patterns composing with `&&`: the right side of `&&` can reference `s` because the compiler knows `&&`'s right operand only evaluates when the left operand (the `instanceof` check) was already true — this **flow scoping** is central to how pattern matching for `instanceof` reasons about where a bound variable is valid.

### Level 3 — Advanced

```java
// File: DescribeGuardClause.java
// compile & run with: --enable-preview --release 15
import java.util.List;

public class DescribeGuardClause {
    static String firstWord(Object obj) {
        // Negated pattern + early return: "s" is in scope AFTER this
        // statement because the only way to fall through is if the
        // instanceof check was true (the negated branch always returns).
        if (!(obj instanceof String s) || s.isBlank()) {
            return "no words: input was " + obj;
        }
        String[] parts = s.trim().split("\\s+");
        return "first word: " + parts[0];
    }

    static int totalLength(List<Object> items) {
        int total = 0;
        for (Object item : items) {
            if (!(item instanceof String s)) {
                continue; // "s" not usable here, but that's fine — we skip
            }
            total += s.length(); // "s" is in scope: we only reach here when it matched
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(firstWord("  hello world  "));
        System.out.println(firstWord(""));
        System.out.println(firstWord(42));

        List<Object> items = List.of("ab", 1, "cde", List.of(), "f");
        System.out.println("Total string length: " + totalLength(items));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 DescribeGuardClause.java
java --enable-preview DescribeGuardClause
```

Expected output:
```
first word: hello
no words: input was 
no words: input was 42
Total string length: 6
```

Level 3 demonstrates **negated-pattern flow scoping**: `if (!(obj instanceof String s) || s.isBlank()) return ...;` binds `s` inside a **negated** check, yet `s` remains usable in the code *after* the `if` block — because the compiler proves that the only way execution reaches past that `if` (without returning) is if `obj instanceof String s` was true. This scoping analysis is exactly what the two preview rounds refined and tested against realistic idioms like guard clauses.

## 6. Walkthrough

1. `firstWord` is called with `"  hello world  "`. The condition `!(obj instanceof String s) || s.isBlank()` first evaluates `obj instanceof String s`: since `obj` is indeed a `String`, this sub-expression is `true`, so its negation `!(...)` is `false`. Java short-circuits `||` only when the left side is `true`; here it's `false`, so the right side `s.isBlank()` is evaluated next, using the just-bound `s`. `"  hello world  ".isBlank()` is `false` (it has non-whitespace content), so the whole condition is `false`, and the `if` body (the early return) is **skipped**.
2. Because the `if`'s early return didn't execute, control falls through to `String[] parts = s.trim().split("\\s+");` — and `s` is valid here precisely because the compiler proved the only path to this line requires `obj instanceof String s` to have been `true` (any path where it was `false` would have already returned inside the `if`).
3. `s.trim()` removes the leading/trailing spaces, producing `"hello world"`; `.split("\\s+")` splits on runs of whitespace, yielding `["hello", "world"]`. `parts[0]` is `"hello"`, so `firstWord` returns `"first word: hello"`.
4. The second call, `firstWord("")`, has `obj instanceof String s` true (`s` bound to `""`), so `!(...)` is `false`, then `s.isBlank()` evaluates to `true` for an empty string — making the whole `||` expression `true`, so the early return **does** execute, printing `"no words: input was "`.
5. The third call, `firstWord(42)`, has `obj instanceof String s` false for an `Integer` — so `!(...)` is `true` immediately, short-circuiting `||` (the right side `s.isBlank()` is never evaluated, which is important: `s` was never successfully bound in this path, so referencing it here would be unsound, and indeed the language ensures you can't reach code depending on `s` in that branch). The early return fires, printing `"no words: input was 42"`.
6. `totalLength` iterates the `items` list; for each `item`, `if (!(item instanceof String s)) continue;` skips non-`String` items immediately (like `1` and the empty `List.of()`), and for `String` items, control proceeds past the `if` to `total += s.length()`, again relying on flow scoping to make `s` available exactly where it's guaranteed to have matched.
7. Across `"ab"`, `1`, `"cde"`, `List.of()`, `"f"`, the `String` items are `"ab"` (length 2), `"cde"` (length 3), and `"f"` (length 1); the two non-`String` items (`1` and the empty list) are skipped by `continue`. The running total accumulates `2 + 3 + 1 = 6`, matching the printed result.

```
!(obj instanceof String s) || s.isBlank()
        │true                  │
        ▼                      ▼
  return early            (s bound & valid here too,
  (s not used)             since instanceof was true)
        │false
        ▼
  fall through — "s" valid below, compiler-proven
```

## 7. Gotchas & takeaways

> Pattern matching for `instanceof` was still a **preview feature in both Java 14 and 15** — `--enable-preview` was required on `javac` and `java` for both rounds, and the feature did not become permanent, standard syntax until Java 16. The two preview rounds existed specifically to validate flow-scoping edge cases (negation, `&&`/`||` composition, guard-clause idioms) before locking the rules in.

- The bound pattern variable (`s` in `obj instanceof String s`) is **not** a new kind of variable — it behaves like a regular local variable, just one whose scope is determined by flow analysis (definite-true / definite-false regions) rather than simple lexical nesting.
- Composing patterns with `&&` works naturally (`instanceof String s && !s.isBlank()`) because `&&`'s right side only runs when the left side was true; composing with `||` requires care, since the right side of `||` runs when the left side was *false*, which is exactly the negated-instanceof idiom shown in Level 3.
- A pattern variable's name can shadow an existing variable in an enclosing scope only under the same shadowing rules as any other local variable — the compiler will flag genuine conflicts.
- Pairing pattern-matching `instanceof` with a hierarchy sealed via `permits` (see [sealed classes (preview)](0678-sealed-classes-preview.md)) foreshadows Java's later pattern-matching `switch`, which formalizes this same test-and-bind idea across a whole set of cases at once instead of one `if` at a time.
- Because this was a *re-preview* rather than a first preview, the syntax itself was already fairly stable by Java 15 — most of the remaining refinement was around clarifying scoping rules and interactions with other preview features active in the same release.
