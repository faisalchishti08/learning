---
card: java
gi: 98
slug: numeric-promotion-in-expressions
title: Numeric promotion in expressions
---

## 1. What it is

Numeric promotion is the set of automatic type conversions the JVM applies to operands *before* evaluating an arithmetic or bitwise expression. Java defines two rules (JLS §5.6):

1. **Unary promotion** — if the operand of a unary operator (`~`, `+`, `-`) is `byte`, `short`, or `char`, it is promoted to `int`.
2. **Binary promotion** — both operands of a binary operator are widened to a common type:
   - If either operand is `double` → both become `double`.
   - Else if either operand is `float` → both become `float`.
   - Else if either operand is `long` → both become `long`.
   - Else → both become `int` (even if both were `byte`, `short`, or `char`).

```java
byte a = 10, b = 20;
// a + b is int, NOT byte — binary promotion applied
// byte sum = a + b;    // COMPILE ERROR: possible loss from int to byte
int  sum = a + b;       // OK
```

## 2. Why & when

Numeric promotion exists to avoid defining dozens of operator overloads for every type pair and to match CPU register widths (most CPUs operate in 32- or 64-bit). You encounter the rules most when:
- Assigning the result of arithmetic on `byte`/`short` — you must cast back.
- Mixing `int` and `long` or `long` and `double` — the smaller type silently widens.
- Compound assignment operators (`+=`, `-=`, etc.) apply an **implicit cast** back to the left-hand type, hiding the promotion from the programmer.

## 3. Core concept

```java
public class NumericPromotion {

    public static void main(String[] args) {
        // ---- byte + byte → int ----
        byte a = 100, b = 27;
        // byte sum = a + b;  // COMPILE ERROR: int result, not byte
        int sum = a + b;       // OK
        System.out.println("byte + byte = int: " + sum);

        // ---- compound assignment hides the promotion (implicit cast) ----
        byte x = 100;
        x += 27;    // equivalent to x = (byte)(x + 27); — implicit cast back to byte
        System.out.println("x += 27 → " + x);   // 127

        // ---- char promotion ----
        char c1 = 'A', c2 = 'B';
        // char diff = c2 - c1;   // COMPILE ERROR
        int charDiff = c2 - c1;   // 1
        System.out.println("'B' - 'A' = " + charDiff);

        // ---- int + long → long ----
        int  i = 1_000_000;
        long l = 5_000_000_000L;
        long result = i + l;   // i promoted to long before +
        System.out.println("int + long = long: " + result);

        // ---- int + double → double ----
        int    n = 7;
        double d = 2.5;
        double r = n / d;   // n promoted to double: 7.0 / 2.5 = 2.8
        System.out.println("int / double = " + r);

        // ---- integer division trap (no promotion if both are int) ----
        int p = 7, q = 2;
        double trap = p / q;   // integer division first: 7/2=3, then 3 widened to double
        System.out.println("int/int then double: " + trap);  // 3.0, not 3.5
        double correct = (double) p / q;   // cast first: 7.0/2=3.5
        System.out.println("(double)int/int: " + correct);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary promotion decision tree: if either is double both become double; else if float both float; else if long both long; else both int. Boxes show byte+short promoted to int; int+long promoted to long; float+double promoted to double.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Binary numeric promotion — applied before every arithmetic/bitwise operator</text>

  <!-- decision chain -->
  <!-- either double? -->
  <rect x="246" y="32" width="208" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Either operand is double?</text>
  <!-- yes -->
  <line x1="454" y1="44" x2="490" y2="44" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <rect x="492" y="32" width="108" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="546" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">→ double</text>
  <text x="470" y="42" fill="#6db33f" font-size="7" font-family="sans-serif">yes</text>
  <!-- no -->
  <line x1="350" y1="56" x2="350" y2="74" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <text x="356" y="68" fill="#8b949e" font-size="7" font-family="sans-serif">no</text>

  <rect x="246" y="76" width="208" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Either operand is float?</text>
  <line x1="454" y1="88" x2="490" y2="88" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <rect x="492" y="76" width="108" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="546" y="92" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">→ float</text>
  <text x="470" y="86" fill="#6db33f" font-size="7" font-family="sans-serif">yes</text>
  <line x1="350" y1="100" x2="350" y2="118" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <text x="356" y="112" fill="#8b949e" font-size="7" font-family="sans-serif">no</text>

  <rect x="246" y="120" width="208" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Either operand is long?</text>
  <line x1="454" y1="132" x2="490" y2="132" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <rect x="492" y="120" width="108" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="546" y="136" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">→ long</text>
  <text x="470" y="130" fill="#6db33f" font-size="7" font-family="sans-serif">yes</text>
  <line x1="350" y1="144" x2="350" y2="155" stroke="#8b949e" stroke-width="1" marker-end="url(#a)"/>
  <text x="356" y="153" fill="#8b949e" font-size="7" font-family="sans-serif">no</text>

  <rect x="246" y="155" width="208" height="5" rx="2" fill="#1c2430"/>
  <text x="350" y="163" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">→ int  (byte, short, char, int all become int)</text>

  <!-- examples left column -->
  <text x="20" y="56" fill="#8b949e" font-size="7.5" font-family="monospace">byte + byte → int</text>
  <text x="20" y="92" fill="#8b949e" font-size="7.5" font-family="monospace">int + float → float</text>
  <text x="20" y="128" fill="#8b949e" font-size="7.5" font-family="monospace">int + long → long</text>
  <text x="20" y="163" fill="#8b949e" font-size="7.5" font-family="monospace">char + short → int</text>

  <defs>
    <marker id="a" markerWidth="5" markerHeight="5" refX="2.5" refY="2.5" orient="auto">
      <path d="M0,0 L0,5 L5,2.5 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

The decision tree is evaluated in order — the first matching rule wins and determines the common type.

## 5. Runnable example

Scenario: a temperature analytics system that accumulates readings stored as `short` values, computes averages with `double` precision, and mixes types in conversion formulas — numeric promotion governs every arithmetic step.

### Level 1 — Basic

```java
public class PromotionBasic {
    public static void main(String[] args) {
        // Temperatures stored as short (tenths of a degree)
        short t1 = 236, t2 = 198, t3 = 212;  // 23.6, 19.8, 21.2 °C

        // short + short → int; must store in int or cast
        // short sumShort = t1 + t2;   // COMPILE ERROR
        int sumInt = t1 + t2 + t3;     // OK: shorts promoted to int for each +
        System.out.println("Sum (int): " + sumInt);

        // int / int → int: integer division
        int avgTenths = sumInt / 3;
        System.out.println("Average tenths (int/int): " + avgTenths);  // 215

        // int / double → double for true decimal average
        double avgC = sumInt / 3.0;    // 3.0 is double → sumInt promoted to double
        System.out.printf("Average °C: %.2f%n", avgC / 10.0);          // 21.53

        // Compound assignment: hidden promotion + cast
        short acc = 0;
        acc += t1;    // acc = (short)(acc + t1); — result is int internally, cast back
        acc += t2;
        acc += t3;
        System.out.println("Accumulator (short via +=): " + acc);   // 646 — fits in short
    }
}
```

**How to run:** `java PromotionBasic.java`

`t1 + t2 + t3` promotes each `short` to `int` before the additions — there is no `short` addition in Java. The result is `int`. `sumInt / 3.0` promotes `sumInt` (`int`) to `double` because `3.0` is a `double` literal — the result is `double`, giving decimal precision. `acc += t1` is shorthand for `acc = (short)(acc + t1)` — the promotion happens, the result is `int`, and the compound assignment operator inserts an implicit cast back to `short`. Without the compound assignment, `acc = acc + t1` would be a compile error.

### Level 2 — Intermediate

Same system: Celsius-to-Fahrenheit conversion formula `F = C * 9 / 5 + 32` where operand types determine whether the result is integer or decimal.

```java
public class PromotionIntermediate {

    // Returns double for precision
    static double celsiusToFahrenheitDouble(double c) {
        return c * 9.0 / 5.0 + 32.0;   // all double from the start
    }

    // Demonstrates integer vs floating-point promotion difference
    static void compare(int cInt) {
        // All int: 9/5 = 1 (integer division!) before multiplying
        int intResult = cInt * 9 / 5 + 32;
        // int * double: cInt promoted to double, then / 5.0 is double
        double doubleResult = cInt * 9.0 / 5.0 + 32.0;

        System.out.printf("  %3d°C → int formula: %d°F  double formula: %.1f°F%n",
            cInt, intResult, doubleResult);
    }

    public static void main(String[] args) {
        System.out.println("Temperature conversions:");
        for (int c : new int[]{0, 20, 37, 100, -40}) {
            compare(c);
        }

        // Mixed long + double
        long epochMs = 1_700_000_000_000L;
        double epochSeconds = epochMs / 1_000.0;  // long / double → double
        System.out.printf("Epoch: %.0f seconds%n", epochSeconds);

        // Promotion in conditional expressions (?:)
        int x = 5;
        double result = (x > 3) ? 1 : 2.5;  // int 1 promoted to double 1.0
        System.out.println("Ternary int/double: " + result);  // 1.0
    }
}
```

**How to run:** `java PromotionIntermediate.java`

`cInt * 9 / 5` is `int * int / int` — all integer. `9 / 5` would be 1 by integer division if computed first, but operator precedence makes it `(cInt * 9) / 5` — still integer. For 20: `20 * 9 = 180`, `180 / 5 = 36`, `36 + 32 = 68`. `cInt * 9.0 / 5.0 + 32.0`: `cInt` is promoted to `double` by `* 9.0`, then all remaining operations are `double`. The ternary `(x > 3) ? 1 : 2.5` has operands `int 1` and `double 2.5` — binary promotion makes the whole expression `double`, so `1` becomes `1.0`.

### Level 3 — Advanced

Same system: an `int`-based accumulator that must track running statistics, with promotion rules determining where overflow can silently occur and where precision is preserved.

```java
import java.util.*;

public class PromotionAdvanced {

    record Stats(double mean, double variance, int count) {}

    static Stats compute(short[] readings) {
        // long accumulator to avoid int overflow when summing many shorts
        long sum = 0;
        long sumSq = 0;

        for (short r : readings) {
            // r (short) + sum (long) → long (r promoted to long)
            sum   += r;        // sum = sum + r (short promoted to long)
            sumSq += (long) r * r;  // (long)r * r — ensures no int overflow
            // Without cast: r * r is int * int → may overflow for r near Short.MAX_VALUE
        }

        int n = readings.length;
        // long / int → long; but we want double for mean — cast first
        double mean     = (double) sum / n;           // long → double, then / int(→double)
        double meanSq   = (double) sumSq / n;
        double variance = meanSq - mean * mean;       // all double

        return new Stats(mean, variance, n);
    }

    public static void main(String[] args) {
        // Synthetic sensor readings (tenths of degree)
        short[] readings = new short[200];
        Random rng = new Random(7);
        for (int i = 0; i < readings.length; i++) {
            readings[i] = (short)(200 + rng.nextInt(50));  // 200–249
        }

        Stats s = compute(readings);
        System.out.printf("Count   : %d%n", s.count());
        System.out.printf("Mean    : %.4f (%.2f°C)%n", s.mean(), s.mean() / 10.0);
        System.out.printf("Variance: %.4f%n", s.variance());
        System.out.printf("StdDev  : %.4f%n", Math.sqrt(s.variance()));

        // Promotion in array initializer expressions
        byte base = 10;
        short step = 5;
        // int[] arr = {base, step};    // OK: both promoted to int
        int[] arr = {base, step, base + step};
        System.out.println("Array: " + Arrays.toString(arr));

        // Promotion with shift operators
        long mask = 1L << 32;   // 1 (int) << 32... but left operand is long → long shift
        System.out.printf("1L << 32 = %d%n", mask);
        int  badMask = 1 << 32;  // int << int: 32 mod 32 = 0, so 1 << 0 = 1
        System.out.printf("1 << 32  = %d  (shift amount mod 32)%n", badMask);
    }
}
```

**How to run:** `java PromotionAdvanced.java`

`sum += r` where `sum` is `long` and `r` is `short`: binary promotion makes `r` a `long` before the addition — the result is `long`. Without the `(long)` cast in `sumSq += (long) r * r`, the expression would be `(short) r * (short) r` → promoted to `int * int` → int product, which overflows for `r` values near 32767 (`32767^2 = 1_073_676_289`, just under `Integer.MAX_VALUE`, actually fine for short values, but near `short` max it is safe here — the cast is defensive). `(double) sum / n` — the cast makes `sum` a `double` first, then `n` (int) is promoted to `double` for the division. Shift operators: `1L << 32` is a `long` shift — `long` has 64 bits so shift 32 is valid, giving `4294967296`. `1 << 32`: both operands are `int`, shift amount is taken mod 32, giving `1 << 0 = 1`.

## 6. Walkthrough

Trace the compound assignment `acc += t1` where `acc` (short, value 0) and `t1` (short, 236):

**Expansion.** `acc += t1` is equivalent to `acc = (short)(acc + t1)`.

**Promotion in `acc + t1`.** Both are `short` — binary promotion applies rule 4 (neither is double/float/long) → both promoted to `int`. Expression is `int(0) + int(236) = int(236)`. The static type of `acc + t1` is `int`.

**Implicit cast.** The compound assignment operator inserts `(short)` — narrowing `int(236)` to `short(236)`. 236 fits in `short` (range -32768 to 32767), so no data loss.

**After all three additions.** `acc = 0 + 236 + 198 + 212 = 646`. 646 < 32767 — safe. If the sum exceeded 32767, the compound assignment would silently wrap (e.g., 32768 would become -32768).

```
Promotion trace: (short)0 + (short)236
  Step 1: short → int (both operands)
  Step 2: int(0) + int(236) = int(236)
  Step 3: (short) int(236) = short(236)   [via compound assignment implicit cast]
  Result: acc = 236 (short)
```

## 7. Gotchas & takeaways

> **`byte + byte` and `short + short` are always `int`.** This surprises beginners who expect the result to be `byte` or `short`. The compound assignment operators (`+=`) hide this by inserting an implicit narrowing cast — which can silently overflow.

> **`int / int` is integer division even if the result is assigned to `double`.** `double x = 7 / 2` gives `3.0`. Cast at least one operand: `double x = 7.0 / 2` or `(double) 7 / 2`.

> **Shift operators use the left operand type.** `1 << 40` is `int` shift — shift amount taken mod 32, result is 256 (not 0). Use `1L << 40` for a 64-bit shift.

- `byte`, `short`, `char` operands are always promoted to `int` in arithmetic/bitwise expressions.
- Binary promotion chooses `double > float > long > int` — first matching rule wins.
- Compound assignments (`+=`, `*=`, etc.) apply binary promotion internally, then implicitly cast the result back to the left-hand type.
- `int / int` → `int` — ensure at least one operand is `double` or `float` for decimal division.
- Ternary operator `? :` also applies binary promotion to its two value operands.
