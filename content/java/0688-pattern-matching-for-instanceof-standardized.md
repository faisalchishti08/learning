---
card: java
gi: 688
slug: pattern-matching-for-instanceof-standardized
title: Pattern matching for instanceof — standardized
---

## 1. What it is

**Pattern matching for `instanceof`**, previewed in Java 14 and re-previewed in Java 15, became a **standard, permanent language feature** in **Java 16** (JEP 394). The syntax is unchanged: `if (obj instanceof String s)` tests `obj`'s type and, if it matches, binds `s` as an already-narrowed `String` — usable anywhere the compiler can prove the check was true, including flow-sensitive positions after negated checks or guard clauses. From Java 16 onward, this works with a plain `javac`/`java` invocation, with no `--enable-preview` flag required.

## 2. Why & when

The two preview rounds existed to validate the trickier parts of this feature — specifically, the flow-scoping rules that determine exactly where a pattern-bound variable is considered definitely assigned (inside an `if`'s true branch, after a negated check with an early return, on one side of `&&` or `||`). By Java 16, those rules had proven solid across real usage, and the feature moved to standard status alongside [records](0687-records-standardized.md) in the very same release — a natural pairing, since pattern-matching `instanceof` is exactly the tool you reach for immediately after receiving an object whose concrete type you need to narrow, records included. Use it anywhere you'd otherwise write an `instanceof` check immediately followed by a manual cast: type-dispatch logic, defensive narrowing of `Object`-typed parameters, or (as shown in the previous tutorial) walking a small closed hierarchy of record types.

## 3. Core concept

```java
// Java 14: preview — needs --enable-preview --release 14
// Java 15: 2nd preview — needs --enable-preview --release 15
// Java 16 onward: standard, no preview flag needed
Object obj = "hello";
if (obj instanceof String s) {
    System.out.println(s.length()); // s already narrowed to String, no cast needed
}
```

The same test-and-bind syntax that required preview flags in Java 14 and 15 compiles and runs on Java 16+ without any special compiler options.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pattern matching for instanceof timeline: preview in Java 14, second preview in Java 15, standardized in Java 16">
  <line x1="40" y1="80" x2="580" y2="80" stroke="#8b949e" stroke-width="2"/>

  <circle cx="100" cy="80" r="8" fill="#f0883e"/>
  <text x="100" y="55" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 14</text>
  <text x="100" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">preview</text>

  <circle cx="340" cy="80" r="8" fill="#f0883e"/>
  <text x="340" y="55" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 15</text>
  <text x="340" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2nd preview</text>

  <circle cx="520" cy="80" r="8" fill="#6db33f"/>
  <text x="520" y="55" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 16</text>
  <text x="520" y="105" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">standard, no flag needed</text>
</svg>

Standardization arrived in the same release as records — the two features are commonly used together.

## 5. Runnable example

Scenario: a small shape-processing utility over a mix of `Object`s — starting with a simple type-narrowing dispatch, then adding flow-scoped negated-pattern guard clauses, then combining pattern-matching `instanceof` with standardized records to build a compact, no-preview-flags-needed area calculator.

### Level 1 — Basic

```java
// File: TypeNarrowBasic.java
public class TypeNarrowBasic {
    static String describe(Object obj) {
        if (obj instanceof Integer i) {
            return "Integer: " + (i * i) + " (squared)";
        }
        if (obj instanceof String s) {
            return "String of length " + s.length();
        }
        return "Unknown: " + obj;
    }

    public static void main(String[] args) {
        System.out.println(describe(6));
        System.out.println(describe("hello"));
        System.out.println(describe(3.14));
    }
}
```

**How to run:** `java TypeNarrowBasic.java` (no preview flags needed, JDK 16+)

Expected output:
```
Integer: 36 (squared)
String of length 5
Unknown: 3.14
```

### Level 2 — Intermediate

```java
// File: GuardClauseValidation.java
public class GuardClauseValidation {
    static int parsePositiveInt(Object value) {
        if (!(value instanceof String s) || s.isBlank()) {
            throw new IllegalArgumentException("expected a non-blank string, got: " + value);
        }
        int parsed = Integer.parseInt(s.trim());
        if (parsed <= 0) {
            throw new IllegalArgumentException("expected a positive number, got: " + parsed);
        }
        return parsed;
    }

    public static void main(String[] args) {
        System.out.println("Parsed: " + parsePositiveInt("  42  "));

        try {
            parsePositiveInt(100);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        try {
            parsePositiveInt("-5");
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java GuardClauseValidation.java`

Expected output:
```
Parsed: 42
Rejected: expected a non-blank string, got: 100
Rejected: expected a positive number, got: -5
```

`!(value instanceof String s) || s.isBlank()` binds `s` inside a negated check, yet `s` remains valid on the very next line — the compiler proves the only way to reach `Integer.parseInt(s.trim())` is if `value instanceof String s` was true, since the negated-or-blank condition would have already thrown otherwise.

### Level 3 — Advanced

```java
// File: RecordAreaCalculator.java
public class RecordAreaCalculator {
    sealed interface Shape permits Circle, Rectangle {}
    record Circle(double radius) implements Shape {}
    record Rectangle(double width, double height) implements Shape {}

    static double area(Object maybeShape) {
        if (!(maybeShape instanceof Shape shape)) {
            throw new IllegalArgumentException("not a Shape: " + maybeShape);
        }
        if (shape instanceof Circle c && c.radius() > 0) {
            return Math.PI * c.radius() * c.radius();
        }
        if (shape instanceof Rectangle r && r.width() > 0 && r.height() > 0) {
            return r.width() * r.height();
        }
        throw new IllegalArgumentException("invalid shape dimensions: " + shape);
    }

    public static void main(String[] args) {
        Object[] inputs = { new Circle(2.0), new Rectangle(3.0, 4.0), new Circle(-1.0), "not a shape" };
        for (Object input : inputs) {
            try {
                System.out.printf("%s -> area %.2f%n", input, area(input));
            } catch (IllegalArgumentException e) {
                System.out.println(input + " -> rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java RecordAreaCalculator.java`

Expected output:
```
Circle[radius=2.0] -> area 12.57
Rectangle[width=3.0, height=4.0] -> area 12.00
Circle[radius=-1.0] -> rejected: invalid shape dimensions: Circle[radius=-1.0]
not a shape -> rejected: not a Shape: not a shape
```

Level 3 layers two pattern-matching `instanceof` checks: the outer `!(maybeShape instanceof Shape shape)` guard narrows an arbitrary `Object` down to the sealed `Shape` type (or rejects it immediately), and the inner checks (`shape instanceof Circle c && c.radius() > 0`) both narrow to a specific record type *and* validate its data in the same expression via `&&` composition — no separate cast, no separate `if` for the validation.

## 6. Walkthrough

1. `main` builds an `Object[]` mixing valid shapes, an invalid shape, and a non-shape `String`, then calls `area(input)` for each inside a `try`/`catch`.
2. Inside `area`, the first check is `!(maybeShape instanceof Shape shape)`. For the first three inputs (`Circle`, `Rectangle`, and the invalid `Circle`), this negated check is `false` (they *are* `Shape`s), so the guard doesn't throw, and `shape` is bound and usable for the rest of the method. For the fourth input (a plain `String`), the check is `true`, and the method throws immediately with `"not a Shape: not a shape"`.
3. For the valid `Circle(2.0)`, the check `shape instanceof Circle c && c.radius() > 0` first confirms `shape` is a `Circle` (binding `c`), then evaluates `c.radius() > 0` using the just-bound `c` — `2.0 > 0` is `true`, so both conditions hold and the method returns `Math.PI * 2.0 * 2.0 ≈ 12.57`.
4. For `Rectangle(3.0, 4.0)`, the first `instanceof Circle` check fails (it's not a `Circle`), so control moves to the next check: `shape instanceof Rectangle r && r.width() > 0 && r.height() > 0` — both dimensions are positive, so the method returns `3.0 * 4.0 = 12.00`.
5. For the invalid `Circle(-1.0)`, `shape instanceof Circle c` succeeds (it *is* a `Circle`), but `c.radius() > 0` evaluates to `false` (since `-1.0` is not greater than `0`) — so the whole `&&` expression is `false`, and this `if` doesn't match. Since it's also not a `Rectangle`, execution falls through to the final `throw`, reporting `"invalid shape dimensions: Circle[radius=-1.0]"` (using the record's auto-generated `toString()`).
6. Back in `main`, each result — whether a computed area or a caught exception's message — is printed alongside the original input's `toString()`, giving a line-by-line trace of how each of the four inputs was classified and either computed or rejected.

```
area(maybeShape)
      │
!(maybeShape instanceof Shape shape)? ──true──► throw "not a Shape"
      │false
      ▼
shape instanceof Circle c && c.radius()>0? ──true──► return circle area
      │false
      ▼
shape instanceof Rectangle r && dims>0? ──true──► return rectangle area
      │false
      ▼
throw "invalid shape dimensions"
```

## 7. Gotchas & takeaways

> Standardization in Java 16 changed **no runtime behavior or syntax** compared to the Java 15 second preview — flow-scoping rules (negation, `&&`/`||` composition, guard clauses) are identical; the only change is that `--enable-preview` is no longer required.

- Composing a pattern with `&&` (`instanceof Circle c && c.radius() > 0`) lets you narrow the type *and* validate its data in a single boolean expression — a very common idiom once records make "narrow, then check a field" a frequent pattern.
- The negated-pattern-plus-early-exit idiom (`if (!(x instanceof T t)) throw/return; // t usable below`) is a standard, compiler-verified way to write guard clauses without nesting the rest of the method inside an `if` block.
- Pattern-matching `instanceof` and records were standardized in the **same** Java 16 release — not a coincidence, since narrowing to a specific record type to access its components is one of the most common uses of this feature.
- This feature is a stepping stone toward pattern matching in `switch` expressions/statements (finalized in later JDK releases), which generalizes the same test-and-bind idea across multiple `case` arms at once instead of one `if` at a time.
- A pattern variable behaves like an ordinary local variable once in scope — it can be reassigned, passed to methods, or captured by a lambda, subject to the same rules as any other local variable.
