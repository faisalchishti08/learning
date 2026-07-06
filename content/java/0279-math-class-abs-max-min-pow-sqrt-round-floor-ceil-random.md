---
card: java
gi: 279
slug: math-class-abs-max-min-pow-sqrt-round-floor-ceil-random
title: Math class (abs, max, min, pow, sqrt, round, floor, ceil, random)
---

## 1. What it is

`java.lang.Math` is a final utility class providing static methods for common mathematical operations: `abs` (absolute value), `max`/`min` (larger/smaller of two values), `pow` (exponentiation), `sqrt` (square root), `round` (rounds to the nearest integer), `floor`/`ceil` (round down/up to the nearest whole number, returned as a `double`), and `random` (a pseudo-random `double` between `0.0` and `1.0`). Every method is `static`, so none require creating a `Math` object — you call them directly as `Math.methodName(...)`.

```java
public class MathDemo {
    public static void main(String[] args) {
        System.out.println(Math.abs(-7));         // 7
        System.out.println(Math.max(3, 9));         // 9
        System.out.println(Math.min(3, 9));          // 3
        System.out.println(Math.pow(2, 10));          // 1024.0
        System.out.println(Math.sqrt(144));            // 12.0
        System.out.println(Math.round(3.6));             // 4 (rounds to nearest)
        System.out.println(Math.floor(3.9));              // 3.0 (rounds DOWN)
        System.out.println(Math.ceil(3.1));                // 4.0 (rounds UP)
        System.out.println(Math.random() < 1.0);            // always true — random() is in [0.0, 1.0)
    }
}
```

Each method solves a distinct, common numeric problem: `Math.abs` strips a sign, `Math.max`/`Math.min` pick between two values, `Math.pow`/`Math.sqrt` handle exponents and roots, `Math.round`/`Math.floor`/`Math.ceil` each round differently (nearest, down, up), and `Math.random()` provides a source of pseudo-randomness — recognizing which specific method matches your rounding or comparison need is the core skill this topic covers.

## 2. Why & when

`Math`'s methods exist to avoid hand-writing common numeric operations yourself, and to provide precisely defined, well-tested, and often JVM-optimized implementations of operations that are easy to get subtly wrong by hand.

- **Precision and correctness for non-trivial operations** — implementing your own square root or exponentiation function correctly and efficiently is genuinely non-trivial; `Math.sqrt` and `Math.pow` handle this reliably, using well-established numerical algorithms.
- **Distinguishing between different rounding behaviours** — `round`, `floor`, and `ceil` all "round" in some sense, but produce different results for the same input (`3.6` rounds to `4`, floors to `3`, and ceils to `4`; `3.1` rounds to `3`, floors to `3`, and ceils to `4`) — choosing the wrong one is a common source of off-by-one-style bugs in calculations involving money, pagination, or counts.
- **A convenient, always-available source of basic randomness** — `Math.random()` is a simple, no-setup way to get a pseudo-random number when you don't need the more configurable, seedable behaviour `java.util.Random` (a later topic) provides.

Reach for `Math`'s static methods any time you need a standard mathematical operation rather than writing your own — pay particular attention to choosing the correct rounding method for your specific need (nearest, down, or up), since `round`, `floor`, and `ceil` are easy to confuse but behave meaningfully differently, especially for negative numbers, as the advanced example below explores.

## 3. Core concept

```java
public class MathCore {
    static double calculateDiscount(double price, double percentage) {
        double discount = price * (percentage / 100);
        return Math.round(price - discount) / 100.0; // round to 2 decimal places, a common money-rounding technique
    }
}
```

`Math.round(price - discount)` here is intentionally combined with the surrounding `* 100` / `/ 100.0` pattern (not shown fully in this snippet, but a standard technique) to round a `double` to a specific number of decimal places rather than to the nearest whole number — understanding exactly what each `Math` rounding method does, and how to combine them for practical needs like currency rounding, is a genuinely useful, frequently applied skill.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="round rounds to the nearest integer, floor always rounds down toward negative infinity, ceil always rounds up toward positive infinity, shown against the same input value 3.6">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <line x1="60" y1="90" x2="540" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">3</text>
  <text x="540" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">4</text>

  <circle cx="380" cy="90" r="5" fill="#e6edf3"/>
  <text x="380" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">3.6</text>

  <line x1="60" y1="90" x2="60" y2="90" stroke="#6db33f"/>
  <text x="150" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Math.round(3.6) -&gt; 4 (nearest)</text>
  <text x="300" y="145" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Math.floor(3.6) -&gt; 3.0 (always down)</text>
  <text x="450" y="40" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Math.ceil(3.6) -&gt; 4.0 (always up)</text>
</svg>

`round`, `floor`, and `ceil` each treat the same input value differently — nearest, always down, or always up.

## 5. Runnable example

Scenario: a pricing calculator using several `Math` methods together, evolved from basic discount rounding into a version handling negative adjustments correctly, then hardened with a comparison of rounding methods on negative numbers, a frequent source of confusion.

### Level 1 — Basic

```java
public class MathBasic {
    public static void main(String[] args) {
        double price = 49.999;
        long roundedCents = Math.round(price * 100); // round to the nearest cent
        System.out.println("Rounded price: $" + (roundedCents / 100.0));
    }
}
```

**How to run:** `java MathBasic.java`

`price * 100` shifts the decimal to work in cents (`4999.9`), `Math.round(...)` rounds that to the nearest whole cent (`5000`), and dividing back by `100.0` produces the correctly rounded dollar amount, `$50.0` — a standard technique for rounding currency to a fixed number of decimal places.

### Level 2 — Intermediate

Same pricing idea, now clamping a discount percentage between `0` and `100` using `Math.max`/`Math.min` together, and computing a square-footage-based price adjustment with `Math.sqrt` — demonstrating several `Math` methods combined in one realistic calculation.

```java
public class MathIntermediate {
    static double clampPercentage(double percentage) {
        return Math.max(0, Math.min(100, percentage)); // clamps into the range [0, 100]
    }

    static double areaBasedFee(double area) {
        return Math.sqrt(area) * 2.5; // fee scales with the square root of the area
    }

    public static void main(String[] args) {
        System.out.println(clampPercentage(150)); // 100.0 — clamped down
        System.out.println(clampPercentage(-20));  // 0.0 — clamped up
        System.out.println(clampPercentage(45));    // 45.0 — already in range, unchanged

        System.out.println("Fee for 400 sq ft: $" + areaBasedFee(400)); // sqrt(400)=20, 20*2.5=50.0
    }
}
```

**How to run:** `java MathIntermediate.java`

`Math.max(0, Math.min(100, percentage))` is a standard "clamp" idiom: `Math.min(100, percentage)` first caps the value at `100` from above, and the outer `Math.max(0, ...)` then floors it at `0` from below — combined, they guarantee the result always falls within `[0, 100]`, regardless of how far outside that range the input started.

### Level 3 — Advanced

Same pricing system, now demonstrating the important, commonly surprising difference between `round`, `floor`, and `ceil` specifically for *negative* numbers — a real source of bugs when calculations involve refunds, negative adjustments, or debts.

```java
public class MathAdvanced {
    public static void main(String[] args) {
        double[] values = { 3.6, -3.6, 3.4, -3.4 };

        for (double v : values) {
            System.out.println("Value: " + v);
            System.out.println("  round: " + Math.round(v));  // rounds to NEAREST (ties round toward positive infinity)
            System.out.println("  floor: " + Math.floor(v));   // always rounds toward NEGATIVE infinity
            System.out.println("  ceil:  " + Math.ceil(v));     // always rounds toward POSITIVE infinity
        }
    }
}
```

**How to run:** `java MathAdvanced.java`

For negative numbers, `floor` and `ceil` do *not* behave like a simple "round down"/"round up" in the everyday sense of "toward zero" or "away from zero" — `floor` always moves toward negative infinity (making `-3.6` floor to `-4.0`, a "larger magnitude" negative number), while `ceil` always moves toward positive infinity (making `-3.6` ceil to `-3.0`, a "smaller magnitude" negative number) — this directionality, not "toward/away from zero," is the correct mental model for both.

## 6. Walkthrough

Trace the loop in `MathAdvanced.main` for each value.

**`v = 3.6`.** `Math.round(3.6)`: rounds to the nearest integer, which is `4` (since `3.6` is closer to `4` than to `3`). `Math.floor(3.6)`: rounds down toward negative infinity, giving `3.0`. `Math.ceil(3.6)`: rounds up toward positive infinity, giving `4.0`.

**`v = -3.6`.** `Math.round(-3.6)`: rounds to the nearest integer; `-3.6` is closer to `-4` than to `-3`, so it rounds to `-4`. `Math.floor(-3.6)`: rounds toward negative infinity — since `-4` is further in the negative direction than `-3.6` itself, and `-4` is the nearest whole number in that direction, `floor` gives `-4.0`. `Math.ceil(-3.6)`: rounds toward positive infinity — `-3` is the nearest whole number in the positive direction from `-3.6`, so `ceil` gives `-3.0`.

**`v = 3.4`.** `Math.round(3.4)`: nearest integer is `3` (closer to `3` than `4`). `Math.floor(3.4)`: `3.0`. `Math.ceil(3.4)`: `4.0`.

**`v = -3.4`.** `Math.round(-3.4)`: nearest integer is `-3` (closer to `-3` than `-4`). `Math.floor(-3.4)`: toward negative infinity gives `-4.0`. `Math.ceil(-3.4)`: toward positive infinity gives `-3.0`.

```
3.6:  round=4, floor=3.0,  ceil=4.0
-3.6: round=-4, floor=-4.0, ceil=-3.0   <- floor moves AWAY from zero here (toward -infinity)
3.4:  round=3, floor=3.0,  ceil=4.0
-3.4: round=-3, floor=-4.0, ceil=-3.0   <- floor still moves toward -infinity, ceil toward +infinity
```

**Final output.**
```
Value: 3.6
  round: 4
  floor: 3.0
  ceil:  4.0
Value: -3.6
  round: -4
  floor: -4.0
  ceil:  -3.0
Value: 3.4
  round: 3
  floor: 3.0
  ceil:  4.0
Value: -3.4
  round: -3
  floor: -4.0
  ceil:  -3.0
```

## 7. Gotchas & takeaways

> **`floor` and `ceil` always round toward negative and positive infinity respectively — never "toward zero" or "away from zero"** — for negative numbers, this means `floor` produces a *more* negative (larger magnitude) result, and `ceil` produces a *less* negative (smaller magnitude) result, which is the opposite of what "round down"/"round up" might intuitively suggest if you're thinking in terms of magnitude rather than position on the number line. Always think in terms of direction on the number line (toward `-∞` or toward `+∞`), not magnitude, when reasoning about `floor`/`ceil` for negative inputs.

> **`Math.round(double)` returns a `long`, while `Math.round(float)` returns an `int`** — this overload distinction matters when you need the result as a specific type; assigning `Math.round(someDouble)` directly to an `int` variable requires an explicit cast (`(int) Math.round(someDouble)`), since the `double` overload's return type is `long`, not `int`, and Java does not implicitly narrow a `long` to an `int`.

- `Math` provides static methods for common numeric operations: `abs`, `max`, `min`, `pow`, `sqrt`, `round`, `floor`, `ceil`, and `random`, all callable directly without creating a `Math` instance.
- `round` rounds to the nearest whole number (with ties rounding toward positive infinity); `floor` always rounds toward negative infinity; `ceil` always rounds toward positive infinity.
- For negative numbers, `floor` and `ceil`'s behaviour is often counter-intuitive relative to "rounding down/up in magnitude" — always reason about direction on the number line instead.
- `Math.round(double)` returns a `long`; an explicit cast is needed to assign its result directly to an `int` variable.
