---
card: java
gi: 771
slug: primitive-types-in-patterns-instanceof-switch-preview
title: Primitive types in patterns, instanceof, and switch (preview)
---

## 1. What it is

**Java 23** (JEP 455) is a **preview** feature that extends pattern matching — until now limited to reference types — to **primitive types** as well. You can write `instanceof int i`, use `case float f` inside a `switch`, and nest primitive type patterns inside [record patterns](0740-record-patterns-standardized.md) (e.g. `case Point(int x, int y)` where `Point` actually holds `double` fields). The runtime checks that the value can be converted to the requested primitive type **exactly**, without loss of information, before the pattern matches.

## 2. Why & when

Once [pattern matching for `switch`](0742-pattern-matching-for-switch-standardized.md) and record patterns became standard, one gap remained: patterns only worked on reference types. If a `record Reading(double x, double y)` held values that happened to be whole numbers, there was no pattern-based way to say "match this record, but only if both fields are exactly representable as `int`" — you had to deconstruct manually, cast, and range-check by hand, with plenty of room for an off-by-one or a silently truncated value. JEP 455 closes that gap: primitive patterns let you ask for a **narrower or different primitive type** as part of the match, and the match itself only succeeds if the conversion is exact (no truncation, no rounding, no overflow). This matters whenever code processes numeric data from many sources — sensor readings, JSON numbers, protocol fields — and needs to route or optimize based on whether a value fits a smaller, cheaper representation.

## 3. Core concept

```java
Object value = 42.0; // a Double

// instanceof with a primitive pattern
if (value instanceof int i) {
    System.out.println("fits in int: " + i);
}

// switch with primitive patterns and a guard
Object n = 200;
String size = switch (n) {
    case byte b -> "byte: " + b;
    case short s when s > 127 -> "short (too big for byte): " + s;
    case int i -> "int: " + i;
    default -> "other";
};
```

`value instanceof int i` only matches because `42.0` converts to `42` **exactly** — `42.5` would not match.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A primitive type pattern checks that a value converts exactly to the target primitive type before it matches">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">value instanceof int i / case int i -&gt; ...</text>

  <rect x="40" y="90" width="220" height="60" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="115" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">42.0 (double)</text>
  <text x="150" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">exact conversion to int -&gt; matches</text>

  <rect x="380" y="90" width="220" height="60" rx="8" fill="#0f1620" stroke="#f85149"/>
  <text x="490" y="115" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">42.5 (double)</text>
  <text x="490" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no exact int -&gt; does not match</text>

  <text x="320" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Works in instanceof, switch, and nested inside record patterns</text>
</svg>

*Primitive patterns match only when the value converts to the target primitive without any loss.*

## 5. Runnable example

Scenario: a stream of numeric sensor readings that should be routed to the cheapest primitive representation that can hold them exactly, growing from a single `instanceof` check into a record-pattern-based classifier.

### Level 1 — Basic

```java
public class PrimitivePatternBasic {
    public static void main(String[] args) {
        Object[] readings = {42.0, 42.5, 1000.0};

        for (Object reading : readings) {
            if (reading instanceof int i) {
                System.out.println(reading + " -> fits exactly in int: " + i);
            } else {
                System.out.println(reading + " -> does not fit exactly in int");
            }
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 PrimitivePatternBasic.java` (JDK 23+).

`42.0 instanceof int i` succeeds because `42.0` is exactly representable as the `int` `42`; `42.5 instanceof int i` fails because truncating to `42` would lose the fractional part — the pattern requires an **exact**, lossless conversion, not just "convertible."

### Level 2 — Intermediate

```java
public class PrimitivePatternSwitch {
    static String classify(Object n) {
        return switch (n) {
            case byte b -> "byte: " + b;
            case short s when s > Byte.MAX_VALUE -> "short (too big for byte): " + s;
            case int i when i > Short.MAX_VALUE -> "int (too big for short): " + i;
            case Integer boxed -> "int: " + boxed;
            default -> "unrecognized: " + n;
        };
    }

    public static void main(String[] args) {
        Object[] values = {(byte) 5, (short) 200, 70000, 42};
        for (Object v : values) {
            System.out.println(classify(v));
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 PrimitivePatternSwitch.java`.

The real-world concern added: a `switch` that classifies a value by the **smallest exact primitive type** it fits, using guarded patterns (`when`) to distinguish "fits in `byte`" from "needs a `short`" from "needs a full `int`" — the same value-narrowing logic that used to require nested `if`/range-check chains is now expressed as ordered pattern cases.

### Level 3 — Advanced

```java
public class PrimitivePatternRecords {
    record Reading(double x, double y) {}

    static String describe(Object obj) {
        return switch (obj) {
            case Reading(int x, int y) -> "whole-number point: (" + x + ", " + y + ")";
            case Reading(double x, double y) when Double.isNaN(x) || Double.isNaN(y) ->
                "invalid point: (" + x + ", " + y + ")";
            case Reading(double x, double y) -> "fractional point: (" + x + ", " + y + ")";
            default -> "not a reading";
        };
    }

    public static void main(String[] args) {
        Object[] readings = {
            new Reading(3.0, 4.0),
            new Reading(3.5, 4.0),
            new Reading(Double.NaN, 1.0),
        };
        for (Object r : readings) {
            System.out.println(describe(r));
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 PrimitivePatternRecords.java`.

This adds the production-flavored hard case: a primitive pattern **nested inside a record pattern** (`Reading(int x, int y)`) — the record deconstructs into its two `double` fields, and each is separately checked for exact conversion to `int`; only when *both* succeed does the whole record pattern match, letting the `switch` distinguish whole-number points, fractional points, and invalid (`NaN`) points in one ordered set of cases.

## 6. Walkthrough

Tracing `PrimitivePatternRecords.describe`:

1. `describe` is called with a `Reading` whose fields are `(3.0, 4.0)`. The `switch` evaluates cases top to bottom.
2. The first case, `Reading(int x, int y)`, deconstructs the record and attempts to match **each field** as a primitive `int` pattern: `3.0` converts exactly to `3`, and `4.0` converts exactly to `4`. Both succeed, so the whole pattern matches, binding `x = 3` and `y = 4`.
3. The `switch` short-circuits on this first successful match and returns `"whole-number point: (3, 4)"` — the later `NaN` and fractional cases are never evaluated for this input.
4. For `(3.5, 4.0)`: the first case tries `x = 3.5 instanceof int` — `3.5` has no exact `int` representation, so this component pattern fails and the whole `Reading(int x, int y)` case fails to match, without needing to check `y` at all.
5. The `switch` falls through to the second case, `Reading(double x, double y) when Double.isNaN(x) || Double.isNaN(y)` — here the fields simply bind as `double` (no narrowing needed), and the guard checks for `NaN`. Neither `3.5` nor `4.0` is `NaN`, so the guard is false and this case also fails.
6. The third case, an unguarded `Reading(double x, double y)`, always matches any remaining `Reading` — it returns `"fractional point: (3.5, 4.0)"`.
7. For `(NaN, 1.0)`: the first case's `int` pattern on `NaN` fails (no primitive `int` represents `NaN`), so it falls to the second case, whose guard `Double.isNaN(x)` is true — it returns `"invalid point: (NaN, 1.0)"`.

Expected output:
```
whole-number point: (3, 4)
fractional point: (3.5, 4.0)
invalid point: (NaN, 1.0)
```

## 7. Gotchas & takeaways

> **Gotcha:** the conversion checked by a primitive pattern is **exactness**, not "would compile with a cast." `(Object) 300 instanceof byte b` fails even though `(byte) 300` compiles fine in ordinary code — a plain cast silently truncates, but a primitive pattern refuses to match anything that would lose information. Don't assume primitive-pattern matching and primitive casting behave the same way.

- Preview in Java 23 (JEP 455) — requires `--enable-preview` and a matching `--source`/`--release`.
- A primitive type pattern (`case int i`, `instanceof float f`) matches only on an **exact, lossless** conversion, unlike a normal narrowing cast.
- Primitive patterns can nest inside [record patterns](0740-record-patterns-standardized.md), letting a single `switch` case narrow several primitive fields of a record at once.
- Combine with guarded patterns (`when`) to express "matches this shape, and also satisfies this extra condition" — replacing manual range-check chains with ordered, readable cases.
- As a preview feature, exact syntax and semantics may still change before this becomes a standard part of pattern matching for [`switch`](0742-pattern-matching-for-switch-standardized.md).
