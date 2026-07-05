---
card: java
gi: 105
slug: multiplication
title: Multiplication *
---

## 1. What it is

The `*` operator multiplies two numeric operands, applying the same binary numeric promotion as `+` and `-`: both operands are promoted to the widest type among them (`byte`/`short`/`char` → `int` → `long` → `float` → `double`), and the result has that type. Multiplication is the fastest way for values to blow past a type's range — unlike addition, where doubling the magnitude requires roughly doubling the operand, multiplying two moderately large numbers together can produce a result many orders of magnitude larger than either operand.

```java
int a = 50_000, b = 50_000;
int product = a * b;        // 2,500,000,000 mathematically — overflows int silently
System.out.println(product); // -1794967296 (wrapped)

long safeProduct = (long) a * b;  // cast ONE operand to long BEFORE multiplying
System.out.println(safeProduct);  // 2500000000 (correct)
```

Note the position of the cast: `(long) a * b` casts `a` to `long` *before* the multiplication happens (because `(long)` binds tighter than `*`), which promotes `b` to `long` too via binary numeric promotion — this computes the product in 64-bit arithmetic. Casting the *result* instead, `(long)(a * b)`, would not help, because by then the overflow has already happened in 32-bit `int` arithmetic.

## 2. Why & when

Multiplication is everywhere in size, area, and scaling calculations:

- Buffer/array sizing: `width * height * bytesPerPixel` for image buffers.
- Unit conversion: `hours * 60 * 60 * 1000` to get milliseconds.
- Compound interest / growth: `principal * Math.pow(1 + rate, years)`.
- Combinatorics: `n * (n - 1) * (n - 2)` for permutation counts, which grows extremely fast.

You must watch for overflow whenever any operand could be "large enough" that its product with another operand exceeds the type's range — this happens far sooner than most people expect, since `int` overflows for products over about 2.1 billion, which two 5-digit numbers can already reach.

## 3. Core concept

```java
public class MultiplicationDemo {
    public static void main(String[] args) {
        // Basic int multiplication
        int width = 1920, height = 1080;
        System.out.println("Pixels: " + (width * height));   // 2,073,600 — fits fine

        // Overflow: two moderately large ints multiply past Integer.MAX_VALUE
        int a = 50_000, b = 50_000;
        System.out.println("50000 * 50000 (int)  = " + (a * b));          // wraps, wrong
        System.out.println("50000 * 50000 (long) = " + ((long) a * b));   // correct, cast BEFORE *

        // byte/short promote to int before multiplying
        byte b1 = 100, b2 = 3;
        int byteProduct = b1 * b2;    // type is int even though operands are byte
        System.out.println("byte * byte (as int): " + byteProduct);

        // Mixed numeric types promote to the widest type present
        double scaled = 3 * 2.5;      // int promoted to double
        System.out.println("3 * 2.5 = " + scaled);

        // Math.multiplyExact detects overflow instead of wrapping
        try {
            Math.multiplyExact(a, b);
        } catch (ArithmeticException e) {
            System.out.println("multiplyExact threw: " + e.getMessage());
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiplication overflow diagram: 50000 times 50000 in int arithmetic wraps to a negative number, but casting one operand to long before multiplying computes the correct 2.5 billion result in 64 bit arithmetic.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Cast BEFORE multiplying, not after — the overflow already happened by then</text>

  <rect x="16" y="34" width="320" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">int a = 50000, b = 50000;</text>
  <text x="30" y="70" fill="#e6edf3" font-size="8" font-family="monospace">int product = a * b;</text>
  <text x="30" y="90" fill="#79c0ff" font-size="8.5" font-family="monospace">true value: 2,500,000,000</text>
  <text x="30" y="108" fill="#e6edf3" font-size="8.5" font-family="monospace">stored (32-bit): -1,794,967,296</text>
  <text x="30" y="128" fill="#6db33f" font-size="7.5" font-family="sans-serif">Overflow happened during the</text>
  <text x="30" y="140" fill="#6db33f" font-size="7.5" font-family="sans-serif">int * int computation itself.</text>

  <rect x="352" y="34" width="332" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="518" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">long product = (long) a * b;</text>
  <text x="366" y="70" fill="#e6edf3" font-size="8" font-family="monospace">(long) a  →  a widened to long</text>
  <text x="366" y="86" fill="#e6edf3" font-size="8" font-family="monospace">b promoted to long too (binary</text>
  <text x="366" y="100" fill="#e6edf3" font-size="8" font-family="monospace">numeric promotion, same rule as +)</text>
  <text x="366" y="120" fill="#79c0ff" font-size="8.5" font-family="monospace">result: 2,500,000,000 (correct)</text>
</svg>

Casting one operand widens both before the multiply happens, so the product is computed in the wider type's arithmetic from the start.

## 5. Runnable example

Scenario: an image-buffer allocator that computes the byte size needed for a bitmap, first naively with `int`, then hardened against overflow for large images, and finally validating against a hardware limit.

### Level 1 — Basic

```java
public class MultiplicationBasic {
    public static void main(String[] args) {
        int width = 4000, height = 3000, bytesPerPixel = 4; // typical high-res photo, RGBA
        int bufferSize = width * height * bytesPerPixel;
        System.out.println("Buffer size (bytes): " + bufferSize);  // fits fine: 48,000,000

        // A much larger image (e.g., a stitched panorama) overflows int
        int panoWidth = 40000, panoHeight = 30000;
        int panoBufferSize = panoWidth * panoHeight * bytesPerPixel;
        System.out.println("Panorama buffer size (bytes): " + panoBufferSize); // wraps, wrong
    }
}
```

**How to run:** `java MultiplicationBasic.java`

The first image is a realistic 4000x3000 RGBA photo: `4000 * 3000 * 4 = 48,000,000`, comfortably within `int` range. The panorama at 40,000x30,000 pixels needs `40000 * 30000 * 4 = 4,800,000,000` bytes — more than double `Integer.MAX_VALUE` — so the `int` computation wraps to a small or negative number, and any code that allocates a buffer "of that size" would either crash or silently allocate far too little memory.

### Level 2 — Intermediate

Same allocator, now computing the size in `long` arithmetic and validating it against a reasonable maximum before attempting to allocate.

```java
public class MultiplicationIntermediate {

    static long computeBufferSize(int width, int height, int bytesPerPixel) {
        // Cast the FIRST operand to long so every subsequent * promotes to long too
        return (long) width * height * bytesPerPixel;
    }

    static void validateBufferSize(long size, long maxAllowed) {
        if (size > maxAllowed) {
            throw new IllegalArgumentException(
                "Buffer size " + size + " exceeds max allowed " + maxAllowed);
        }
    }

    public static void main(String[] args) {
        long maxAllowed = 200_000_000L; // e.g., a 200MB cap for this application

        int[][] images = {
            { 4000, 3000, 4 },
            { 40000, 30000, 4 }
        };

        for (int[] dims : images) {
            long size = computeBufferSize(dims[0], dims[1], dims[2]);
            System.out.println("Requested: " + dims[0] + "x" + dims[1] + " -> " + size + " bytes");
            try {
                validateBufferSize(size, maxAllowed);
                System.out.println("  Allocation OK");
            } catch (IllegalArgumentException e) {
                System.out.println("  Rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java MultiplicationIntermediate.java`

`(long) width * height * bytesPerPixel` casts `width` to `long` first; because `*` is left-associative and binary numeric promotion widens both operands of each `*` to match the wider one, `height` and then `bytesPerPixel` are each promoted to `long` in turn, so the entire chain computes in 64-bit arithmetic and the panorama's true size (4,800,000,000 bytes) is computed correctly instead of wrapping. `validateBufferSize` then applies a business rule — even though the `long` computation is now correct, a 4.8GB allocation is still rejected because it exceeds the application's 200MB cap, which is a separate, deliberate policy decision rather than an artifact of overflow.

### Level 3 — Advanced

Same allocator, now using `Math.multiplyExact` to guard even the `long` computation against overflow (for pathological inputs where dimensions themselves are untrusted and could be enormous), and demonstrating why casting the *result* instead of an *operand* does not fix anything.

```java
public class MultiplicationAdvanced {

    static long computeBufferSizeSafely(long width, long height, long bytesPerPixel) {
        long area = Math.multiplyExact(width, height);           // throws if width*height overflows long
        return Math.multiplyExact(area, bytesPerPixel);           // throws if area*bpp overflows long
    }

    public static void main(String[] args) {
        // Normal case
        System.out.println("Normal: " + computeBufferSizeSafely(4000, 3000, 4));

        // Untrusted/corrupted dimensions that would overflow even long arithmetic
        long hugeWidth = 4_000_000_000L, hugeHeight = 4_000_000_000L;
        try {
            computeBufferSizeSafely(hugeWidth, hugeHeight, 4);
        } catch (ArithmeticException e) {
            System.out.println("Rejected corrupted dimensions: " + e.getMessage());
        }

        // Common mistake: casting the RESULT instead of an operand does NOT help
        int w = 50_000, h = 50_000;
        long wrongCast = (long) (w * h);   // overflow already happened inside the parentheses, in int arithmetic
        long rightCast = (long) w * h;      // w widened to long BEFORE multiplying — correct
        System.out.println("Wrong cast (too late):  " + wrongCast);
        System.out.println("Right cast (before *):  " + rightCast);
    }
}
```

**How to run:** `java MultiplicationAdvanced.java`

`Math.multiplyExact(width, height)` computes the product and checks whether it overflowed `long`'s 64-bit range, throwing `ArithmeticException` if so — this catches the pathological case where even `long` arithmetic is insufficient (two 4-billion-scale dimensions multiply to roughly 1.6 * 10^19, which exceeds `Long.MAX_VALUE`, about 9.2 * 10^18). The final comparison is the crux of the lesson: `(long) (w * h)` computes `w * h` entirely in `int` arithmetic first (because the parentheses group the multiplication before the cast applies), so the overflow happens before the cast ever sees the value — the cast then just relabels an already-wrong 32-bit result as `long`. `(long) w * h`, without the inner parentheses, casts `w` alone to `long` first, which forces the whole multiplication into 64-bit arithmetic via promotion, giving the correct answer.

## 6. Walkthrough

Trace both cast variants for `w = 50_000, h = 50_000`:

**`(long) (w * h)`.** The parentheses group `w * h` as a single sub-expression, which Java evaluates first: `w` and `h` are both `int`, so the multiplication happens entirely in 32-bit `int` arithmetic. The true product, 2,500,000,000, exceeds `Integer.MAX_VALUE` (2,147,483,647), so it wraps to a negative number (roughly -1,794,967,296) *before* the outer `(long)` cast ever runs. The cast then converts this already-wrong `int` value to `long` — widening a negative `int` to `long` sign-extends it, so the result is a negative `long`, still wrong.

**`(long) w * h`.** Here, `(long)` has higher precedence than `*` and applies only to `w`, converting it to a `long` value of `50000L` immediately. Now the expression is `50000L * h`, where `h` is still `int`. Binary numeric promotion for `*` requires both operands to share a type, so `h` is implicitly widened to `50000L` (as a `long`) as well. The multiplication `50000L * 50000L` now executes in 64-bit arithmetic from the start, correctly producing `2,500,000,000L`, which fits comfortably within `long`'s range.

```
(long) (w * h):
  w * h            -> computed as int * int = wraps to -1794967296
  (long) (-1794967296) -> -1794967296L        (WRONG: cast happened too late)

(long) w * h:
  (long) w          -> 50000L                  (cast happens FIRST)
  50000L * h        -> h promoted to long -> 50000L * 50000L = 2500000000L  (CORRECT)
```

**Final output.** The program prints the normal-case buffer size, the caught rejection for the pathologically huge dimensions, and then the two cast variants side by side — the wrong one showing a negative number, the correct one showing 2,500,000,000.

## 7. Gotchas & takeaways

> **Casting the result of a multiplication does not undo an overflow that already happened inside it.** `(long) (a * b)` computes `a * b` in the original (narrower) type first — if that overflows, the cast only relabels the wrong value. Cast an *operand* before the `*`, not the whole expression after it.

> **Multiplication overflows far more easily than addition.** Two operands that individually look modest (like 50,000 and 50,000) can produce a product that overflows `int` — always sanity-check the *maximum possible product*, not just the maximum operand.

- `*` applies the same binary numeric promotion as `+` and `-`: operands widen to match the widest type present.
- To multiply safely in a wider type, cast one *operand* before the `*` (e.g., `(long) a * b`), which forces the whole expression into that wider arithmetic.
- Use `Math.multiplyExact` to detect overflow explicitly rather than relying on manual reasoning about magnitudes.
- Always compute the theoretical maximum product for size/area calculations (width * height * bytesPerPixel, etc.) before choosing `int` versus `long`.
