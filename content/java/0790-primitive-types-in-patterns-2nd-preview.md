---
card: java
gi: 790
slug: primitive-types-in-patterns-2nd-preview
title: Primitive types in patterns (2nd preview)
---

## 1. What it is

**Java 24** (JEP 507) is the **second preview** of [primitive types in patterns, `instanceof`, and `switch`](0771-primitive-types-in-patterns-instanceof-switch-preview.md), extending the first preview's model in one significant way: primitive patterns now work when the `switch` selector expression is **already a primitive type**, not just when it's a reference type like `Integer` or a record component. `switch (someInt) { case byte b -> ...; case short s -> ...; }` is now legal — narrowing an `int` selector to a smaller exact-fit primitive type directly in a `switch`, something the first preview didn't support since it focused on patterns matching against reference-typed values.

## 2. Why & when

The first preview's motivating case was a record with primitive fields being deconstructed and narrowed — useful, but it left an adjacent, arguably more common case unaddressed: a `switch` whose selector is *already* a primitive `int`, `long`, or similar, where you'd like to route based on which smaller primitive type the value would exactly fit into, without first boxing it to `Object` or `Integer` just to make pattern matching applicable. Boxing purely to enable pattern matching is exactly the kind of unnecessary ceremony pattern matching is supposed to eliminate, so this round closes that gap directly: a primitive-typed selector can be matched against primitive-type patterns with no boxing step, extending the "match on the smallest exact-fit type" idiom from the first preview to the common case of already-primitive numeric values.

## 3. Core concept

```java
int n = 100;

// Java 24 2nd preview: switch selector is already primitive int — no boxing needed.
String size = switch (n) {
    case byte b -> "fits in byte: " + b;
    case short s -> "fits in short: " + s;
    default -> "needs full int: " + n;
};
System.out.println(size); // "fits in byte: 100"
```

`n` is a plain `int`, never boxed to `Integer` — the `switch` directly attempts each primitive pattern's exact-conversion check against it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The second preview extends primitive type patterns to switch statements whose selector is already a primitive value, removing the need to box to a reference type first" >
  <rect x="20" y="20" width="280" height="55" rx="8" fill="#0f1620" stroke="#f85149"/>
  <text x="160" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">1st preview: selector must be Object/Integer</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">boxing required to pattern-match</text>

  <rect x="340" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2nd preview: selector can be primitive int</text>
  <text x="480" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no boxing needed at all</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same exact-conversion matching rule, now usable directly on primitive selectors</text>
</svg>

*Pattern matching no longer requires a value to already be a reference type before it can participate.*

## 5. Runnable example

Scenario: routing numeric sensor readings to the smallest exact-fit primitive representation, growing from the first preview's boxed-selector approach into the second preview's direct primitive-selector matching.

### Level 1 — Basic

```java
public class PrimitiveSwitchBoxed {
    static String classify(Object n) {
        return switch (n) {
            case byte b -> "byte: " + b;
            case short s -> "short: " + s;
            case Integer i -> "int: " + i;
            default -> "other";
        };
    }

    public static void main(String[] args) {
        int reading = 42;
        System.out.println(classify(reading)); // reading is boxed to Integer here
    }
}
```

**How to run:** `java --enable-preview --source 24 PrimitiveSwitchBoxed.java` (JDK 24+).

This is the first preview's style: `classify` takes `Object`, so passing a primitive `int` implicitly **boxes** it to `Integer` first — the `switch` then pattern-matches against the boxed reference type.

### Level 2 — Intermediate

```java
public class PrimitiveSwitchDirect {
    static String classify(int n) {
        return switch (n) {
            case byte b -> "byte: " + b;
            case short s -> "short: " + s;
            default -> "int: " + n;
        };
    }

    public static void main(String[] args) {
        int[] readings = {42, 1000, 200000};
        for (int reading : readings) {
            System.out.println(classify(reading));
        }
    }
}
```

**How to run:** `java --enable-preview --source 24 PrimitiveSwitchDirect.java`.

The real-world concern added: `classify` now takes a plain `int` (no `Object`, no boxing), and the `switch` selector `n` is directly primitive — this round's extension lets each `case byte b`/`case short s` pattern attempt its exact-conversion check straight against the primitive `int`, with the compiler generating no boxing at all.

### Level 3 — Advanced

```java
public class PrimitiveSwitchGuarded {
    record Reading(int sensorId, long rawValue) {}

    static String classify(Reading reading) {
        return switch (reading.rawValue()) {
            case byte b when b >= 0 -> "sensor " + reading.sensorId() + ": non-negative byte " + b;
            case byte b -> "sensor " + reading.sensorId() + ": negative byte " + b;
            case short s -> "sensor " + reading.sensorId() + ": short " + s;
            case int i -> "sensor " + reading.sensorId() + ": int " + i;
            default -> "sensor " + reading.sensorId() + ": full long " + reading.rawValue();
        };
    }

    public static void main(String[] args) {
        Reading[] readings = {
            new Reading(1, 42L),
            new Reading(2, -5L),
            new Reading(3, 5000L),
            new Reading(4, 5_000_000_000L),
        };
        for (Reading r : readings) {
            System.out.println(classify(r));
        }
    }
}
```

**How to run:** `java --enable-preview --source 24 PrimitiveSwitchGuarded.java`.

This adds the production-flavored hard case: switching directly on a `long` (`reading.rawValue()`, primitive, extracted from a record via an ordinary accessor call, not deconstruction), combined with a **guarded pattern** (`case byte b when b >= 0`) to further split the `byte`-fitting case by sign — showing that this round's primitive-selector matching composes with guards exactly like reference-type pattern matching in `switch` always has.

## 6. Walkthrough

Tracing `PrimitiveSwitchGuarded.main` for `new Reading(2, -5L)`:

1. `classify` is called with a `Reading` whose `rawValue()` returns the primitive `long` value `-5L`.
2. The `switch` selector is `reading.rawValue()`, a primitive `long` — no boxing occurs anywhere in this evaluation.
3. The first case, `byte b when b >= 0`, attempts to match `-5L` against the primitive pattern `byte b`: `-5` **does** fit exactly in a `byte` (`byte` ranges from -128 to 127), so the pattern itself matches, binding `b = -5`. The guard `b >= 0` then evaluates to `false`, so this case as a whole does **not** match, and the `switch` proceeds to the next case.
4. The second case, an unguarded `byte b`, tries the same primitive pattern again: `-5L` still converts exactly to `byte b = -5`, and with no guard to fail, this case matches.
5. The `switch` returns `"sensor 2: negative byte -5"`.

For `new Reading(4, 5_000_000_000L)`: none of `byte`, `short`, or `int` can exactly represent `5,000,000,000` (it exceeds `int`'s maximum of about 2.1 billion), so every primitive-pattern case fails to match, falling through to `default`, which prints the raw `long` value directly.

Expected output:
```
sensor 1: non-negative byte 42
sensor 2: negative byte -5
sensor 3: short 5000
sensor 4: full long 5000000000
```

## 7. Gotchas & takeaways

> **Gotcha:** guard evaluation happens **after** a primitive pattern already succeeds in binding — as with reference-type guarded patterns, a failed guard doesn't mean "try harder to match this case," it means "this case, as a whole, doesn't apply, move to the next one," even though the underlying primitive pattern itself matched. Don't confuse "the pattern matched" with "the case matched" when a `when` clause is involved.

- Second preview in Java 24 (JEP 507) — extends [the first preview](0771-primitive-types-in-patterns-instanceof-switch-preview.md) to `switch` statements whose selector is **already primitive**, not just reference-typed; still requires `--enable-preview`.
- No boxing occurs when a primitive-typed selector (`int`, `long`, etc.) is matched directly against primitive-type patterns — the exact-conversion check runs straight against the primitive value.
- Composes with guarded patterns (`when`) exactly as reference-type pattern matching in `switch` already does.
- The core matching semantics — a primitive pattern matches only on an **exact, lossless** conversion — is unchanged from the first preview.
- Especially useful for numeric classification and routing code that previously needed either manual range-check chains or unnecessary boxing purely to enable pattern matching.
