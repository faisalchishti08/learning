---
card: java
gi: 108
slug: unary-plus-minus
title: Unary plus/minus (+ -)
---

## 1. What it is

Unary `+` and `-` take a single numeric operand and are distinct operators from the binary `+`/`-` used for addition and subtraction, even though they share the same symbols. Unary `-` negates its operand (flips its sign); unary `+` does essentially nothing to the value but still triggers **unary numeric promotion**: any operand narrower than `int` (`byte`, `short`, `char`) is promoted to `int` before the operator applies, and the result type is always at least `int`, never the original narrower type.

```java
byte b = 5;
byte negated = (byte) -b;   // -b promotes b to int, negates it (-5), then must cast back to byte
int  plussed = +b;          // unary + promotes byte to int; result type is int, not byte

int x = -5;
int y = -x;                 // 5 — double negation
System.out.println(-Integer.MIN_VALUE); // still Integer.MIN_VALUE! overflow edge case
```

The last line is a genuine gotcha: `Integer.MIN_VALUE` is `-2147483648`, but positive `2147483648` does not fit in `int` (`Integer.MAX_VALUE` is `2147483647`), so negating `Integer.MIN_VALUE` overflows and silently produces `Integer.MIN_VALUE` again, unchanged.

## 2. Why & when

Unary minus is used constantly for sign flips:

- Reversing a direction or delta: `velocity = -velocity` to bounce off a wall.
- Computing an absolute-value-like difference manually, or negating a comparison result.
- Negative literals are actually unary minus applied to a positive literal: `-5` is parsed as unary `-` applied to `5`.

Unary plus is rare in practice (it exists mostly for symmetry with unary minus and for explicit emphasis, e.g., `+5` to visually pair with a `-5` elsewhere), but it is worth knowing it still performs numeric promotion — `+aByteVariable` returns an `int`, which can be a subtle source of a "cannot convert" compile error if you expected a `byte` back out.

You must be careful negating `MIN_VALUE` (for `int`, `long`, `byte`, or `short`) because the negation of the most negative representable value cannot be represented as a positive value of the same width — this is the single overflow edge case unary minus can hit, since every other value's negation fits.

## 3. Core concept

```java
public class UnaryDemo {
    public static void main(String[] args) {
        int x = 5;
        System.out.println("-x = " + (-x));    // -5
        System.out.println("-(-x) = " + (-(-x))); // 5
        System.out.println("+x = " + (+x));     // 5, no-op value-wise

        // Unary numeric promotion: byte/short/char widen to int
        byte b = 10;
        // byte negB = -b;      // would NOT compile: -b is int, cannot assign to byte without a cast
        int negBAsInt = -b;      // fine: result is int
        byte negB = (byte) -b;   // needs explicit cast back to byte
        System.out.println("-b (as int): " + negBAsInt);
        System.out.println("(byte) -b:   " + negB);

        char c = 'A';
        int negC = -c;           // char promotes to int (65), then negated
        System.out.println("-c (char 'A'): " + negC);   // -65

        // The MIN_VALUE overflow edge case
        int minInt = Integer.MIN_VALUE;
        System.out.println("Integer.MIN_VALUE  = " + minInt);
        System.out.println("-Integer.MIN_VALUE = " + (-minInt));  // still MIN_VALUE! overflow
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unary minus overflow diagram: negating Integer.MIN_VALUE should give 2147483648 but that value does not fit in int range, so it wraps back to Integer.MIN_VALUE unchanged.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int range is asymmetric: one more negative value than positive</text>

  <rect x="16" y="36" width="668" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="30" y="60" fill="#79c0ff" font-size="9" font-family="monospace">MIN_VALUE (-2147483648)</text>
  <text x="350" y="60" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">... 0 ...</text>
  <text x="560" y="60" fill="#79c0ff" font-size="9" font-family="monospace">MAX_VALUE (2147483647)</text>

  <text x="350" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">-MIN_VALUE would need to be +2147483648</text>
  <path d="M 350 106 L 350 122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arrowhead)"/>
  <text x="350" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">but that's one more than MAX_VALUE</text>
  <text x="350" y="156" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">→ wraps back to MIN_VALUE, unchanged</text>
</svg>

`int` has exactly one more negative value than positive value, so negating `MIN_VALUE` has nowhere valid to go and wraps.

## 5. Runnable example

Scenario: a simple 2D bouncing-ball physics simulation where a ball's velocity flips sign when it hits a wall — a natural, visual use of unary minus, extended to handle edge cases around extreme velocity values.

### Level 1 — Basic

```java
public class UnaryBasic {
    public static void main(String[] args) {
        int position = 0;
        int velocity = 3;
        int wallRight = 20, wallLeft = 0;

        for (int step = 0; step < 8; step++) {
            position += velocity;
            if (position >= wallRight || position <= wallLeft) {
                velocity = -velocity;   // unary minus: bounce, reverse direction
            }
            System.out.println("Step " + step + ": position=" + position + ", velocity=" + velocity);
        }
    }
}
```

**How to run:** `java UnaryBasic.java`

Each step advances `position` by `velocity`. When the ball reaches or passes a wall, `velocity = -velocity` flips its sign — a positive velocity (moving right) becomes negative (moving left) and vice versa, which is the simplest, cleanest use of unary minus: reversing direction without needing to know which direction it currently was.

### Level 2 — Intermediate

Same simulation, now tracking a `byte`-sized "damage counter" that decreases velocity magnitude on each bounce (simulating energy loss), which requires unary minus combined with a narrowing cast because of unary numeric promotion.

```java
public class UnaryIntermediate {
    public static void main(String[] args) {
        int position = 0;
        byte velocity = 6;                 // small speed range fits in a byte
        int wallRight = 20, wallLeft = 0;
        byte energyLoss = 1;

        for (int step = 0; step < 10 && Math.abs(velocity) > 0; step++) {
            position += velocity;
            if (position >= wallRight || position <= wallLeft) {
                // -velocity promotes byte to int (unary numeric promotion), so we must cast back
                int reversedMagnitude = Math.abs(-velocity) - energyLoss;
                int sign = velocity > 0 ? -1 : 1;   // flip direction
                velocity = (byte) (sign * reversedMagnitude);  // explicit cast: int -> byte
            }
            System.out.println("Step " + step + ": position=" + position + ", velocity=" + velocity);
        }
    }
}
```

**How to run:** `java UnaryIntermediate.java`

`-velocity` promotes the `byte velocity` to `int` before negating (unary numeric promotion applies to unary `-` exactly as it does to unary `+`), so `Math.abs(-velocity)` and the subsequent arithmetic all operate on `int` values — this is why the final `(byte) (sign * reversedMagnitude)` needs an explicit narrowing cast to store the result back into the `byte velocity` variable; without the cast, the code would not compile, because Java never implicitly narrows an `int` expression into a `byte` variable, even one that originated from that same `byte`.

### Level 3 — Advanced

Same simulation, now handling the `Integer.MIN_VALUE` negation edge case directly by clamping extreme velocities before they can hit the unrepresentable-negation trap, and using `Math.negateExact` to detect the overflow explicitly rather than relying on manual reasoning.

```java
public class UnaryAdvanced {

    static int safeBounce(int velocity) {
        try {
            return Math.negateExact(velocity);   // throws ArithmeticException if velocity == MIN_VALUE
        } catch (ArithmeticException e) {
            // Integer.MIN_VALUE cannot be negated safely; clamp to MAX_VALUE as the safe reversal
            System.out.println("Overflow detected negating " + velocity + " — clamping");
            return Integer.MAX_VALUE;
        }
    }

    public static void main(String[] args) {
        int normalVelocity = 7;
        System.out.println("Normal bounce: " + safeBounce(normalVelocity));  // -7

        int extremeVelocity = Integer.MIN_VALUE;   // simulate a corrupted/extreme input
        System.out.println("Naive -velocity:  " + (-extremeVelocity));       // still MIN_VALUE! silent bug
        System.out.println("Safe bounce:      " + safeBounce(extremeVelocity)); // detected and clamped

        // Demonstrate the same edge case for byte and short, which are even easier to hit
        byte minByte = Byte.MIN_VALUE;         // -128
        int negatedByteAsInt = -minByte;        // promoted to int first: -(-128) = 128, fits in int fine
        System.out.println("-Byte.MIN_VALUE as int: " + negatedByteAsInt);   // 128 — correct, because promotion widened it
        byte wouldOverflow = (byte) negatedByteAsInt;  // now narrowing back to byte overflows: 128 doesn't fit in byte
        System.out.println("(byte) 128: " + wouldOverflow);  // -128 again! narrowing wraps it back
    }
}
```

**How to run:** `java UnaryAdvanced.java`

`Math.negateExact(velocity)` behaves like unary `-` but throws `ArithmeticException` specifically when the operand is `Integer.MIN_VALUE`, since that is the one value whose negation cannot be represented as an `int` — `safeBounce` catches this and substitutes `Integer.MAX_VALUE` as a defined, safe fallback instead of silently returning the unchanged (and wrong-signed) `MIN_VALUE`. The `byte` example shows an interesting wrinkle: because unary numeric promotion widens `byte` to `int` *before* negating, `-Byte.MIN_VALUE` (`-(-128)`) is computed as `128` in `int` arithmetic, which fits fine in `int` — the overflow only reappears if that `128` is later narrowed back down to `byte`, since `byte`'s range is `-128` to `127` and `128` doesn't fit, wrapping back to `-128`. This demonstrates that promotion defers the overflow problem to `int`'s boundary, but a later narrowing cast can reintroduce it at the smaller type's boundary.

## 6. Walkthrough

Trace `safeBounce(Integer.MIN_VALUE)`:

**Attempted negation.** `Math.negateExact(Integer.MIN_VALUE)` internally checks: is the operand equal to `Integer.MIN_VALUE`? It is, and since `-Integer.MIN_VALUE` mathematically equals `2147483648`, which exceeds `Integer.MAX_VALUE` (`2147483647`), the method throws `ArithmeticException` with a message describing the integer overflow, rather than returning the silently wrapped (and incorrect) `Integer.MIN_VALUE` that plain unary `-` would have returned.

**Caught in `safeBounce`.** The `catch (ArithmeticException e)` block runs, prints a diagnostic message naming the overflowing value, and returns `Integer.MAX_VALUE` as an explicit, documented fallback — this is a deliberate design choice for this simulation (treating the extreme velocity as "as fast as representable in the opposite direction"), not a universally correct answer, but it is at least an intentional, visible decision rather than a silent bug.

**Contrast with the naive call.** `-extremeVelocity` (plain unary minus, no `Math.negateExact`) is evaluated first, independently, in `main` — it silently returns `Integer.MIN_VALUE` unchanged, which `System.out.println` prints right next to the safe version, making the difference between "silent wraparound" and "detected overflow" directly visible in the output.

```
Math.negateExact(Integer.MIN_VALUE):
  operand == MIN_VALUE?  yes
  true negation (2147483648) > MAX_VALUE (2147483647)?  yes -> overflow
  throw ArithmeticException
        |
        v
  catch block: print diagnostic, return Integer.MAX_VALUE (safe, defined fallback)

plain -Integer.MIN_VALUE (no check):
  computed in int arithmetic -> wraps silently -> still Integer.MIN_VALUE (WRONG, unnoticed)
```

**Final output.** The program prints the normal bounce case first (a straightforward `-7`), then the naive negation of `MIN_VALUE` (still `MIN_VALUE`, exposing the silent bug), then the safe version's caught-and-clamped result, and finally the `byte` promotion example showing how the same overflow can reappear at a narrower boundary after an explicit cast.

## 7. Gotchas & takeaways

> **Negating `Integer.MIN_VALUE` (or `Long.MIN_VALUE`, `Byte.MIN_VALUE`, `Short.MIN_VALUE`) silently returns the same negative value unchanged.** This is because the range of two's-complement integers has one more negative value than positive value. Use `Math.negateExact` if you need this overflow detected rather than silently ignored.

> **Unary numeric promotion applies to unary `-` and `+` just like binary numeric promotion applies to `+`, `-`, `*`, `/`.** `byte`/`short`/`char` operands are promoted to `int` before the operator runs, so `-aByteVariable` is an `int`, not a `byte` — assigning it back requires an explicit cast.

- Unary `-` negates; unary `+` is a near no-op but both trigger unary numeric promotion to at least `int`.
- The one overflow edge case for unary minus is negating a type's most negative value (`MIN_VALUE`), which has no corresponding positive representation.
- `Math.negateExact` detects this overflow and throws, instead of silently returning the unchanged value.
- Promotion can defer an overflow to a wider type's boundary, but a later narrowing cast can reintroduce it at the original, smaller type's boundary — as shown by `Byte.MIN_VALUE` negation surviving fine as an `int`, then overflowing again once cast back to `byte`.
