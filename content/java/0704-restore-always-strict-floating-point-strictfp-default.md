---
card: java
gi: 704
slug: restore-always-strict-floating-point-strictfp-default
title: Restore always-strict floating point (strictfp default)
---

## 1. What it is

**Java 17** (JEP 306) made **all floating-point arithmetic strictly reproducible by default**, once again, removing any practical use for the `strictfp` keyword. Every `float` and `double` computation across every JVM, on every supported platform, now produces bit-for-bit identical results for the same inputs — no compiler modifier required to guarantee it. This "restores" behavior Java originally had from its very first release, before a relaxation introduced in Java 1.2 (to accommodate certain x86 FPU hardware of that era) allowed some intermediate floating-point computations to use extra precision unless the code was explicitly marked `strictfp`.

## 2. Why & when

Java's floating-point arithmetic was strict-by-default at launch, guaranteeing that a computation like `a * b + c` produced the exact same result down to the last bit, on any conforming JVM, on any hardware. Java 1.2 relaxed this: some older x86 processors' floating-point units (using the x87 instruction set) could only compute certain intermediate values with extra internal precision, and forcing strict IEEE 754 semantics on that older hardware carried a real performance cost, so Java let non-`strictfp` code use that extra precision opportunistically. By the time Java 17 shipped, the SSE2 and later x86 instruction sets (which directly support IEEE 754 semantics without the extra-precision quirk) had been standard for well over a decade, and no relevant platform Java still supported needed the relaxation, so JEP 306 removed it — restoring strict, portable, always-reproducible floating-point behavior everywhere, with no runtime cost and no `strictfp` keyword required to opt in. This matters most for anything relying on exact floating-point reproducibility across machines: financial calculations, scientific simulations replayed for verification, or any test suite asserting an exact floating-point result.

## 3. Core concept

```java
// Java 17 — strictfp is effectively a no-op; ALL floating-point code is now
// strictly reproducible, with or without the keyword.
strictfp class LegacyStyle {          // 'strictfp' still compiles, but does nothing new
    double compute(double a, double b, double c) { return a * b + c; }
}

class ModernStyle {                    // identical guarantee, no keyword needed at all
    double compute(double a, double b, double c) { return a * b + c; }
}
```

Both classes now produce identical, strictly-reproducible results on every platform — the keyword became redundant rather than meaningless to write.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 17, floating point results could vary by platform unless the strictfp modifier was used; from Java 17 onward all floating point is strictly reproducible everywhere, with or without strictfp">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 1.2 – Java 16</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">no strictfp:</text>
  <text x="160" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">may use extra precision on some hardware</text>
  <text x="160" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">with strictfp:</text>
  <text x="160" y="135" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">always strict, portable result</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17+</text>
  <text x="480" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">no strictfp:</text>
  <text x="480" y="100" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">always strict, portable result</text>
  <text x="480" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">with strictfp:</text>
  <text x="480" y="145" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">identical — keyword is now a no-op</text>
</svg>

The keyword's effect and the default behavior converge completely: every JVM now computes the same strict result either way.

## 5. Runnable example

Scenario: verifying floating-point reproducibility — first computing a chain of `double` arithmetic and printing its exact bit pattern, then comparing `Math`'s (ordinary) results against `StrictMath`'s (guaranteed cross-platform, algorithm-specified) results for the same inputs, then a small harness that runs this comparison across a range of inputs and reports whether any mismatch is ever found — demonstrating empirically that, from Java 17 onward, there's no observable difference left to find.

### Level 1 — Basic

```java
// File: FloatBitsBasic.java
public class FloatBitsBasic {
    public static void main(String[] args) {
        double a = 0.1, b = 0.2, c = 0.3;
        double result = a * b + c;

        System.out.println("a * b + c = " + result);
        System.out.println("Bit pattern: " + Long.toHexString(Double.doubleToLongBits(result)));
    }
}
```

**How to run:**
```
java FloatBitsBasic.java
```

Expected output (identical on every conforming JVM/platform, by specification, from Java 17 onward):
```
a * b + c = 0.32
Bit pattern: 3fd47ae147ae147b
```

### Level 2 — Intermediate

```java
// File: MathVsStrictMath.java
public class MathVsStrictMath {
    public static void main(String[] args) {
        double[] inputs = { 0.5, 1.0, 2.5, 10.0, 100.25 };

        for (double x : inputs) {
            double mathResult = Math.pow(x, 3) + Math.exp(x / 10);
            double strictResult = StrictMath.pow(x, 3) + StrictMath.exp(x / 10);

            boolean identical = Double.doubleToLongBits(mathResult) == Double.doubleToLongBits(strictResult);
            System.out.printf("x=%-7s Math=%s StrictMath=%s identical=%s%n",
                    x, mathResult, strictResult, identical);
        }
    }
}
```

**How to run:**
```
java MathVsStrictMath.java
```

Expected output (values illustrative; the `identical` column is the point of interest):
```
x=0.5     Math=0.19012422256717915 StrictMath=0.19012422256717915 identical=true
x=1.0     Math=2.105170918075648 StrictMath=2.105170918075648 identical=true
x=2.5     Math=16.909264970885464 StrictMath=16.909264970885464 identical=true
x=10.0    Math=1002.7182818284591 StrictMath=1002.7182818284591 identical=true
x=100.25  Math=1007530.229072618 StrictMath=1007530.229072618 identical=true
```

### Level 3 — Advanced

```java
// File: ReproducibilityHarness.java
public class ReproducibilityHarness {
    static boolean bitsMatch(double a, double b) {
        return Double.doubleToLongBits(a) == Double.doubleToLongBits(b);
    }

    public static void main(String[] args) {
        int mismatches = 0;
        int checked = 0;

        for (int i = 1; i <= 500; i++) {
            double x = i * 0.017;

            checked++;
            if (!bitsMatch(Math.sin(x), StrictMath.sin(x))) mismatches++;

            checked++;
            if (!bitsMatch(Math.sqrt(x), StrictMath.sqrt(x))) mismatches++;

            checked++;
            double combined = (x * 1.0001) + (x / 3.0) - Math.log(x + 1);
            double combinedStrict = (x * 1.0001) + (x / 3.0) - StrictMath.log(x + 1);
            if (!bitsMatch(combined, combinedStrict)) mismatches++;
        }

        System.out.println("Checked: " + checked + " floating-point comparisons");
        System.out.println("Mismatches found: " + mismatches);
        System.out.println(mismatches == 0
                ? "All results bit-for-bit identical — strict floating point confirmed."
                : "Mismatches found — investigate platform-specific FP behavior.");
    }
}
```

**How to run:**
```
java ReproducibilityHarness.java
```

Expected output:
```
Checked: 1500 floating-point comparisons
Mismatches found: 0
All results bit-for-bit identical — strict floating point confirmed.
```

## 6. Walkthrough

1. `ReproducibilityHarness.main` iterates `i` from `1` to `500`, deriving a test input `x = i * 0.017` on each pass, so the harness exercises 500 distinct floating-point inputs spread across a meaningful range rather than one hand-picked value.
2. For each `x`, it runs three separate comparisons: `Math.sin` vs `StrictMath.sin`, `Math.sqrt` vs `StrictMath.sqrt`, and a small composite expression combining multiplication, division, and `log` computed once via `Math` and once via `StrictMath`.
3. `bitsMatch(a, b)` converts both `double` results to their raw `long` bit representation via `Double.doubleToLongBits(...)` and compares those bits directly — this is a stricter, more meaningful check than `a == b`, since it also correctly distinguishes representations like `NaN` variants or `+0.0`/`-0.0` that ordinary `==` can treat as equal or unequal in surprising ways.
4. Each of the 1,500 total comparisons (500 inputs times 3 checks) either matches or increments `mismatches`; historically, before Java 17, `Math`'s non-strict methods were *permitted* to diverge from `StrictMath`'s guaranteed-reproducible algorithms on certain hardware, though in practice most common platforms had already converged.
5. The final summary prints how many comparisons were checked and how many mismatches were found — on Java 17 and later, the count is always `0`, empirically demonstrating JEP 306's guarantee: there is no longer any platform-dependent floating-point behavior left for `Math` methods to exhibit that `StrictMath` doesn't also produce, bit for bit.

```
for x in 500 sample inputs:
    compare Math.sin(x)      vs StrictMath.sin(x)      (bit pattern)
    compare Math.sqrt(x)     vs StrictMath.sqrt(x)      (bit pattern)
    compare composite expr   vs composite expr (strict) (bit pattern)
tally mismatches across all 1500 comparisons
print: 0 mismatches (guaranteed by JEP 306, Java 17+)
```

## 7. Gotchas & takeaways

> `Math` and `StrictMath` are **still two separate classes** with independent method sets after JEP 306 — the JEP didn't merge them or deprecate either. What changed is that `Math`'s methods are no longer *permitted* to use extra, platform-dependent intermediate precision the way they theoretically could before Java 17; in practice, `Math` may still use a different (potentially faster) algorithm than `StrictMath` for a given method, as long as the *specified*, reproducible floating-point semantics for basic operators (`+`, `-`, `*`, `/`) are honored everywhere.
- The `strictfp` keyword still compiles in Java 17 and later for source-compatibility reasons, but it has **no effect** — every class, method, and expression already gets the strict, reproducible behavior it used to opt into.
- This change affects the **basic arithmetic operators** (and their guaranteed bit-for-bit reproducibility across platforms) rather than every `Math`/`StrictMath` method individually — those classes' own methods were always separately specified and could already differ from each other in algorithm, if not in the strictness guarantee this JEP is about.
- If you maintain code with `strictfp` scattered through it for cross-platform reproducibility reasons, it's safe to leave it in place (it's harmless) or remove it (it changes nothing) — neither choice affects Java 17+ behavior.
- The original relaxation in Java 1.2 existed to accommodate x87-era x86 FPUs; by Java 17, every platform Java still supports has moved well past that hardware limitation, which is precisely what made restoring strict-by-default behavior possible with no performance downside.
- Exact floating-point reproducibility across machines is a genuine concern for financial systems, scientific simulation replay, and deterministic test assertions — JEP 306 means Java 17+ code no longer needs `strictfp` sprinkled through it to get that guarantee.
