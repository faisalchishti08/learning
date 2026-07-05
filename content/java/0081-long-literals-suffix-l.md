---
card: java
gi: 81
slug: long-literals-suffix-l
title: long literals (suffix L)
---

## 1. What it is

A `long` literal is an integer literal — decimal, hex, octal, or binary — that ends with the suffix `L` (or `l`). Without the suffix, any integer literal that fits in 32 bits is an `int`. Adding `L` extends the type to 64-bit `long`, which can hold values from −9 223 372 036 854 775 808 to 9 223 372 036 854 775 807.

```java
long normal     = 42L;              // 42 as long (L suffix required for type)
long bigPop     = 8_000_000_000L;   // 8 billion — exceeds int max
long hexLong    = 0xDEAD_BEEF_CAFEL;// hex long
long binLong    = 0b1010_0000_0000L; // binary long
```

The lowercase `l` suffix is legal but strongly discouraged because it looks identical to the digit `1` in most fonts: `1l` is ambiguous to human readers. Always write the uppercase `L`.

## 2. Why & when

Use `long` when:
- A value can exceed ~2.1 billion (file sizes, timestamps in milliseconds or nanoseconds, population figures, product IDs).
- Computing a product or sum that may overflow `int` even if the operands are small (e.g., `width * height` in pixels for a large image).
- Working with `System.currentTimeMillis()` or `System.nanoTime()`, which return `long`.
- Storing bit fields wider than 32 bits.

All numeric literals without a suffix are `int` by default. Forgetting `L` when the value exceeds `Integer.MAX_VALUE` is a compile-time error for out-of-range literals, but for within-range values it is a silent source of overflow later in arithmetic.

## 3. Core concept

```java
// ---- Literal type rules ----
int  i = 100;      // int literal; fits in int
long l = 100;      // 100 is still an int literal; widened to long on assignment
long l2 = 100L;    // long literal — explicit

// ---- Required when value exceeds int range ----
// long big = 3_000_000_000;  // compile error: integer number too large
long big = 3_000_000_000L;    // OK

// ---- Overflow in arithmetic (literal type matters) ----
long wrong = 1_000_000 * 1_000_000;   // both int literals: int overflow first
long right = 1_000_000L * 1_000_000;  // long * int: promotes to long first
System.out.println(wrong);    // -727379968   (silently overflowed)
System.out.println(right);    //  1000000000000

// ---- Timestamps ----
long nowMs  = System.currentTimeMillis();    // epoch millis
long nowNs  = System.nanoTime();             // nanoseconds (relative)
System.out.println("now (ms): " + nowMs);

// ---- Hex, octal, binary long literals ----
long mask64 = 0xFFFF_FFFF_FFFF_FFFFL;   // -1 as long (all bits set)
long oct    = 0777_777_777_777L;         // long octal
long bin    = 0b11111111_11111111_11111111_11111111L;  // 32 bits set → 4294967295L

// ---- long MIN/MAX ----
System.out.println(Long.MAX_VALUE);    // 9223372036854775807
System.out.println(Long.MIN_VALUE);    // -9223372036854775808

// ---- Two's complement wrap for long ----
System.out.println(Long.MAX_VALUE + 1L);  // -9223372036854775808 (wraps to MIN_VALUE)

// ---- uppercase L vs lowercase l ----
long l3 = 100l;   // legal but 100l looks like 1001 — always use L
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="long literal: 8_000_000_000L showing digits, underscore separators, and L suffix that selects 64-bit type vs default 32-bit int">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <!-- Token anatomy -->
  <rect x="16" y="18" width="668" height="55" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">long literal anatomy: 8_000_000_000L</text>

  <!-- digit 8 -->
  <rect x="60" y="38" width="30" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="75" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">8</text>

  <!-- underscore -->
  <rect x="94" y="38" width="18" height="26" rx="3" fill="#8b949e" opacity="0.3"/>
  <text x="103" y="55" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">_</text>

  <!-- 000 groups (simplified) -->
  <rect x="116" y="38" width="150" height="26" rx="3" fill="#79c0ff" opacity="0.5"/>
  <text x="191" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">000_000_000</text>

  <!-- L suffix -->
  <rect x="270" y="38" width="28" height="26" rx="3" fill="#6db33f" opacity="0.9"/>
  <text x="284" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">L</text>

  <!-- labels -->
  <text x="75"  y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">digit</text>
  <text x="103" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">separator</text>
  <text x="191" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">more digits</text>
  <text x="284" y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">→ long type</text>

  <!-- int vs long range box -->
  <rect x="16" y="90" width="320" height="66" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">int (no suffix)</text>
  <line x1="26" y1="112" x2="326" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="126" fill="#e6edf3" font-size="8" font-family="monospace">−2 147 483 648 … 2 147 483 647</text>
  <text x="26" y="140" fill="#8b949e" font-size="7.5" font-family="monospace">overflow wraps silently</text>
  <text x="26" y="153" fill="#8b949e" font-size="7.5" font-family="monospace">out-of-range literal = compile error</text>

  <!-- long range box -->
  <rect x="348" y="90" width="336" height="66" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="516" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">long (L suffix)</text>
  <line x1="358" y1="112" x2="674" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="358" y="126" fill="#e6edf3" font-size="8" font-family="monospace">−9.2×10¹⁸ … 9.2×10¹⁸</text>
  <text x="358" y="140" fill="#6db33f" font-size="7.5" font-family="monospace">use for timestamps, file sizes</text>
  <text x="358" y="153" fill="#8b949e" font-size="7.5" font-family="monospace">System.currentTimeMillis(): long</text>
</svg>

The `L` suffix is the only difference between an `int` literal and a `long` literal; without it any arithmetic that overflows 32 bits will silently wrap before any widening occurs.

## 5. Runnable example

Scenario: a log file analyser that processes timestamps and byte offsets — quantities that routinely exceed `int` range. The example grows from simple timestamp arithmetic, to detecting the overflow hazard, to a complete log-replay report.

### Level 1 — Basic

```java
public class LongLiteralsBasic {
    public static void main(String[] args) {
        // Log file: start time and duration in milliseconds
        long startMs    = 1_700_000_000_000L;   // Unix epoch ms (Nov 2023)
        long durationMs =        86_400_000L;   // 24 hours in ms

        long endMs      = startMs + durationMs;

        System.out.println("=== Log file window ===");
        System.out.println("Start  (ms): " + startMs);
        System.out.println("End    (ms): " + endMs);
        System.out.println("Duration   : " + durationMs / 3_600_000L + " hours");
        System.out.println("Within int range? start > MAX_INT: " + (startMs > Integer.MAX_VALUE));
    }
}
```

**How to run:** `java LongLiteralsBasic.java`

`1_700_000_000_000L` is approximately 1.7 trillion — 800 times larger than `Integer.MAX_VALUE` (about 2.1 billion). Storing a Unix millisecond timestamp in an `int` is impossible: the value silently wraps. `durationMs / 3_600_000L` divides by a `long` constant; using `3_600_000` (without `L`) would also work here because both operands widen to `long`, but the explicit `L` makes the intent clear.

### Level 2 — Intermediate

Same analyser: compute the total bytes read across multiple log segments, demonstrate the overflow trap when the segment count exceeds `int` capacity, and fix it.

```java
public class LongLiteralsIntermediate {

    record LogSegment(String name, long startMs, int bytesRead) {}

    public static void main(String[] args) {
        var segments = java.util.List.of(
            new LogSegment("auth.log",   1_700_000_000_000L, 1_048_576),    // 1 MB
            new LogSegment("access.log", 1_700_000_086_400L, 524_288_000),  // 500 MB
            new LogSegment("app.log",    1_700_000_172_800L, 2_000_000_000) // ~2 GB
        );

        long totalBytes = 0L;
        int  totalBytesInt = 0;    // will overflow

        System.out.printf("%-12s  %20s  %14s%n", "Segment", "Start (ms)", "Bytes");
        System.out.println("-".repeat(50));

        for (var s : segments) {
            System.out.printf("%-12s  %20d  %,14d%n",
                s.name(), s.startMs(), s.bytesRead());
            totalBytes    += s.bytesRead();   // widened to long each step
            totalBytesInt += s.bytesRead();   // int overflow risk
        }

        System.out.println("-".repeat(50));
        System.out.printf("%-12s  %20s  %,14d  (long, correct)%n",
            "TOTAL", "", totalBytes);
        System.out.printf("%-12s  %20s  %,14d  (int,  OVERFLOW)%n",
                "TOTAL", "", totalBytesInt);

        // Convert to MB
        double totalMB = totalBytes / 1_048_576.0;
        System.out.printf("%nTotal: %.2f MB%n", totalMB);
    }
}
```

**How to run:** `java LongLiteralsIntermediate.java`

`totalBytes += s.bytesRead()` widens `bytesRead` (an `int`) to `long` before adding, so the 64-bit accumulator never overflows. `totalBytesInt += s.bytesRead()` stays in `int`, and after adding ~2.5 GB total it wraps to a negative value. `1_048_576.0` is a `double` literal, which causes the `long / double` division to produce a `double` result — no explicit cast needed.

### Level 3 — Advanced

Same analyser: measure nanosecond timing precision for batch reads, demonstrate `Math.multiplyExact` for long arithmetic, and build a throughput report.

```java
public class LongLiteralsAdvanced {
    public static void main(String[] args) throws Exception {
        // Simulate reading chunks and measuring time
        int     chunkSize   = 65_536;        // bytes per read (64 KB)
        int     numChunks   = 100_000;
        long    totalBytes  = (long) chunkSize * numChunks;  // 6.4 GB

        // Math.multiplyExact for safe long multiplication
        long safeTotal = Math.multiplyExact((long) chunkSize, (long) numChunks);
        System.out.printf("Chunks: %,d × %,d bytes = %,d bytes%n",
            numChunks, chunkSize, safeTotal);

        // Nanosecond timing of a simulated batch
        long startNs = System.nanoTime();
        long dummy = 0L;
        for (int i = 0; i < numChunks; i++) {
            dummy += i;   // simulate work
        }
        long elapsedNs = System.nanoTime() - startNs;

        // Convert ns → ms with long arithmetic
        long elapsedMs = elapsedNs / 1_000_000L;
        System.out.printf("Elapsed  : %,d ns  (%,d ms)%n", elapsedNs, elapsedMs);

        // Throughput in bytes/sec
        double throughputMBps = (totalBytes / 1_048_576.0)
                                / (elapsedNs / 1_000_000_000.0);
        System.out.printf("Throughput (simulated): %.2f MB/s%n", throughputMBps);

        // Long boundary arithmetic
        System.out.println();
        System.out.println("Long.MAX_VALUE     : " + Long.MAX_VALUE);
        System.out.println("Long.MAX_VALUE + 1L: " + (Long.MAX_VALUE + 1L));  // wraps to MIN
        try {
            long overflow = Math.addExact(Long.MAX_VALUE, 1L);
        } catch (ArithmeticException e) {
            System.out.println("Math.addExact caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java LongLiteralsAdvanced.java`

`(long) chunkSize * numChunks` casts `chunkSize` to `long` before the multiplication so the product `6_553_600_000` is computed in 64-bit arithmetic — it exceeds `Integer.MAX_VALUE` and would overflow without the cast. `1_000_000L` (the nanosecond-to-millisecond divisor) uses the `L` suffix as a reminder that `elapsedNs` is `long`; Java would widen `1_000_000` anyway, but the explicit suffix documents intent. `Math.addExact(Long.MAX_VALUE, 1L)` throws `ArithmeticException` instead of silently wrapping — the safe way to add when overflow must not be silently ignored.

## 6. Walkthrough

Execution trace through `LongLiteralsAdvanced.main`:

**`totalBytes` computation.** `(long) chunkSize` promotes `65_536` (an `int`) to `long(65_536)`. The multiplication `65_536L * 100_000` is performed in `long` arithmetic: `6_553_600_000L`, which is well within `long` range. Without the cast: `65_536 * 100_000 = 6_553_600_000` — this exceeds `Integer.MAX_VALUE (2_147_483_647)` and wraps to `1_311_116_352` before widening to `long`. The explicit `(long)` cast prevents this.

**`System.nanoTime()`.** Returns a `long` representing nanoseconds elapsed since some arbitrary origin. Subtracting two `nanoTime()` readings gives the elapsed time in nanoseconds. Dividing by `1_000_000L` converts to milliseconds; the `L` suffix ensures the division is `long / long` rather than `long / int` (which would also work, but `int` can represent `1_000_000` fine — the `L` is for clarity).

**Throughput.** `totalBytes / 1_048_576.0` divides a `long` by a `double` literal; Java widens `totalBytes` to `double` for the division. `elapsedNs / 1_000_000_000.0` similarly converts nanoseconds to fractional seconds as `double`. The final result is `double` throughput in MB/s.

**`Math.addExact` boundary check.** `Long.MAX_VALUE + 1L` silently wraps to `Long.MIN_VALUE` in unchecked arithmetic. `Math.addExact` internally checks `((result ^ a) & (result ^ b)) < 0` — a standard two's-complement overflow detection — and throws if true.

```
(long) chunkSize * numChunks:
  chunkSize = 65_536  (int)
  → cast → 65_536L   (long)
  × 100_000           (int, widened to long)
  = 6_553_600_000L    (long, no overflow)

vs.
  chunkSize * numChunks:
  = 65_536 * 100_000  (int arithmetic)
  = 6_553_600_000     (overflows int → 1_311_116_352)
  → 1_311_116_352L    (widened after overflow — wrong)
```

## 7. Gotchas & takeaways

> **Use uppercase `L`, never lowercase `l`.** In most fonts `100l` is indistinguishable from `1001`. The Java compiler accepts both, but the Java style guides and all major code-review tools treat `l` as a defect.

> **Overflow happens at the operand type, not at the assignment type.** `long x = 1_000_000 * 1_000_000;` multiplies two `int` literals — the overflow occurs before the result is widened to `long`. Append `L` to at least one operand: `1_000_000L * 1_000_000`.

- A bare integer literal (decimal, hex, octal, or binary) is an `int`; adding `L` makes it a `long`.
- For values exceeding `Integer.MAX_VALUE` (2 147 483 647), the `L` suffix is mandatory — without it the literal is a compile error.
- `System.currentTimeMillis()` and `System.nanoTime()` return `long`; store them in `long`, not `int`.
- `Math.multiplyExact`, `Math.addExact`, and `Math.subtractExact` throw `ArithmeticException` on long overflow instead of silently wrapping.
- `Long.MAX_VALUE + 1L` wraps silently to `Long.MIN_VALUE` — two's complement overflow is not an exception unless you use `Math.*Exact`.
- `Long.parseLong(s)` parses a string to `long`; `Long.toHexString(l)`, `Long.toBinaryString(l)`, `Long.toOctalString(l)` convert the other way.
