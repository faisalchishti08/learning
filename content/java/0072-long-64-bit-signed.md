---
card: java
gi: 72
slug: long-64-bit-signed
title: long (64-bit signed)
---

## 1. What it is

`long` is Java's 64-bit signed integer — range **-9,223,372,036,854,775,808 to 9,223,372,036,854,775,807** (roughly ±9.2 × 10¹⁸). Long literals require an `L` suffix to distinguish them from `int` literals.

```java
long fileSize    = 10_737_418_240L;   // 10 GB
long epochMs     = System.currentTimeMillis();
long population  = 8_100_000_000L;   // 8.1 billion — too big for int
long maxLong     = Long.MAX_VALUE;    //  9_223_372_036_854_775_807L
long minLong     = Long.MIN_VALUE;    // -9_223_372_036_854_775_808L

// Without L suffix: int literal (compile error if > Integer.MAX_VALUE)
// long bad = 10_000_000_000;   // ✗ out of range for int literal
long ok  = 10_000_000_000L;     // ✓ long literal
```

The boxed wrapper is `Long`. The JVM uses `long` internally for timestamps, memory addresses, and file positions.

## 2. Why & when

Use `long` when:
- Values can exceed ±2,147,483,647 (`Integer.MAX_VALUE`): epoch milliseconds, file sizes, byte counts for large files, financial totals in smallest units (pence/cents), population, unique IDs from 64-bit sequences.
- You call an API that returns `long`: `System.currentTimeMillis()`, `System.nanoTime()`, `File.length()`, `String.hashCode()` in 64-bit environments.
- Doing bit manipulation on 64-bit patterns (e.g., UUID components, network address masks).

Stay with `int` for counts, indices, and values you know fit in ±2 billion — `long` uses twice the memory and is marginally slower on 32-bit JVMs.

## 3. Core concept

```java
// ---- Suffix L (or l — uppercase preferred) ----
long a = 1L;                      // long literal
long b = 1_000_000_000_000L;      // 1 trillion
// long c = 1;                    // fine: int literal 1 widens to long implicitly

// ---- Arithmetic ----
long x = 3_000_000_000L;
long y = 2_000_000_000L;
System.out.println(x + y);        // 5000000000   (no overflow: long range is huge)
System.out.println(x * y);        // 6000000000000000000 (fits in long)

// Watch: int * int can overflow even if stored in long:
long bad  = 1_000_000 * 1_000_000;   // int overflow BEFORE widening!  = 1000000000000 ?? No!
// 1_000_000 * 1_000_000 = 10^12 > Integer.MAX_VALUE (2.1×10^9) → overflows silently → wrong result
long good = 1_000_000L * 1_000_000;  // ✓ one operand long → result is long

// ---- Division and modulo ----
System.out.println(10L / 3);      // 3 (truncates toward zero)
System.out.println(-10L % 3);     // -1 (sign follows dividend)

// ---- Long API ----
System.out.println(Long.toBinaryString(-1L));  // 64 ones
System.out.println(Long.toHexString(Long.MAX_VALUE));  // 7fffffffffffffff
System.out.println(Long.parseLong("FFFFFFFFFFFFFFFF", 16));  // -1 (signed)
System.out.println(Long.toUnsignedString(-1L));  // 18446744073709551615 (unsigned)
System.out.println(Long.bitCount(-1L));           // 64

// ---- Overflow wraps (same as int) ----
long wrap = Long.MAX_VALUE;
wrap++;    // → Long.MIN_VALUE
System.out.println(wrap);    // -9223372036854775808

// ---- Math.exact for overflow detection ----
try {
    long r = Math.multiplyExact(Long.MAX_VALUE, 2L);
} catch (ArithmeticException e) {
    System.out.println("overflow: " + e.getMessage());
}

// ---- Long boxing cache ----
// Long caches -128..127 (same as Integer)
Long p = 127L, q = 127L;
System.out.println(p == q);          // true  (cached)
Long r = 128L, s = 128L;
System.out.println(r == s);          // false (not cached)
System.out.println(r.equals(s));     // true  (use equals)
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="long: 64-bit signed, range -9.2E18 to +9.2E18; comparison with int; common use cases">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Range comparison bar -->
  <rect x="16" y="20" width="670" height="50" rx="5" fill="#1c2430"/>
  <text x="351" y="34" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">int vs long range</text>
  <!-- int bar -->
  <rect x="170" y="40" width="362" height="10" rx="2" fill="#8b949e" opacity="0.6"/>
  <text x="148" y="49" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">int -2.1B</text>
  <text x="552" y="49" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">+2.1B</text>
  <text x="100" y="49" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">int range ↕</text>
  <!-- long bar -->
  <rect x="30" y="54" width="642" height="10" rx="2" fill="#6db33f" opacity="0.6"/>
  <text x="351" y="62" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">long: -9.2 × 10¹⁸ .................................................. +9.2 × 10¹⁸</text>

  <!-- Use cases -->
  <rect x="16" y="78" width="320" height="84" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="176" y="93" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">When to use long</text>
  <text x="26" y="108" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• System.currentTimeMillis() / nanoTime()</text>
  <text x="26" y="120" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• File.length() / byte counts for large files</text>
  <text x="26" y="132" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Financial totals in pence/cents</text>
  <text x="26" y="144" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Population, unique 64-bit IDs, counters</text>
  <text x="26" y="156" fill="#8b949e" font-size="7" font-family="sans-serif">  (anything > 2,147,483,647)</text>

  <!-- Pitfalls -->
  <rect x="346" y="78" width="340" height="84" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="516" y="93" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Common pitfalls</text>
  <text x="356" y="108" fill="#e6edf3" font-size="7.5" font-family="monospace">1_000_000 * 1_000_000  // int overflow!</text>
  <text x="356" y="120" fill="#6db33f" font-size="7.5" font-family="monospace">1_000_000L * 1_000_000 // ✓ long</text>
  <text x="356" y="132" fill="#e6edf3" font-size="7.5" font-family="monospace">Long a=128L, b=128L; a==b // false</text>
  <text x="356" y="144" fill="#6db33f" font-size="7.5" font-family="monospace">a.equals(b)              // ✓ true</text>
  <text x="356" y="156" fill="#8b949e" font-size="7" font-family="sans-serif">  Missing L suffix: compile error if > MAX_INT</text>
</svg>

`long` covers ±9.2 × 10¹⁸ — use it when values exceed ±2.1 billion. Always suffix literals with `L`. One operand must be `long` for `long` arithmetic.

## 5. Runnable example

Scenario: an order analytics system that processes file-sized datasets, timestamps, and 64-bit financial totals — where `int` would overflow and `long` is required.

### Level 1 — Basic

```java
public class LongBasic {
    public static void main(String[] args) {
        System.out.println("=== long basics ===\n");

        // Range
        System.out.println("Long.MIN_VALUE: " + Long.MIN_VALUE);
        System.out.println("Long.MAX_VALUE: " + Long.MAX_VALUE);
        System.out.println("Long.SIZE:      " + Long.SIZE + " bits");
        System.out.println("Long.BYTES:     " + Long.BYTES + " bytes");

        // Timestamps — int would overflow (milliseconds since 1970 > 2B)
        long nowMs  = System.currentTimeMillis();
        long nowNs  = System.nanoTime();
        System.out.printf("%nCurrent time: %,d ms since epoch%n", nowMs);
        System.out.printf("Nanotime:     %,d ns%n", nowNs);

        // File sizes — can exceed int range
        long fileSize    = 5_368_709_120L;   // 5 GB
        long totalData   = fileSize * 12;    // 60 GB — both long, no overflow
        System.out.printf("%nFile size:  %,d bytes (%.1f GB)%n",
            fileSize, fileSize / 1e9);
        System.out.printf("Total data: %,d bytes (%.1f GB)%n",
            totalData, totalData / 1e9);

        // Financial totals in pence (avoid floating-point)
        long orderPence = 29_999L;         // £299.99 in pence
        long numOrders  = 1_000_000L;      // 1 million orders
        long totalPence = orderPence * numOrders;  // 29,999,000,000 pence > int range
        System.out.printf("%n1M orders of £%.2f = total £%,.2f%n",
            orderPence / 100.0, totalPence / 100.0);

        // L suffix required for > Integer.MAX_VALUE
        // long bad = 10_000_000_000;    // ✗ compile error
        long ok = 10_000_000_000L;       // ✓
        System.out.println("10 billion (with L): " + ok);
    }
}
```

**How to run:** `java LongBasic.java`

`System.currentTimeMillis()` returns the number of milliseconds elapsed since midnight 1 January 1970 UTC. As of 2024 that is ~1.7 × 10¹² — far beyond `int` range (max 2.1 × 10⁹). This is why the method returns `long`.

### Level 2 — Intermediate

Same order analytics system: measure elapsed time with `System.nanoTime()`, demonstrate the `int`×`int` overflow trap, and use `Long.toUnsignedString` for 64-bit ID generation.

```java
public class LongIntermediate {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Intermediate long: timing + ID generation ===\n");

        // 1. Elapsed time measurement
        System.out.println("[ nanoTime elapsed ]");
        long start = System.nanoTime();
        long sum = 0;
        for (long i = 0; i < 10_000_000L; i++) sum += i;
        long elapsed = System.nanoTime() - start;
        System.out.printf("  Sum of 0..9_999_999 = %,d%n", sum);
        System.out.printf("  Elapsed: %,d ns  (%.3f ms)%n", elapsed, elapsed / 1e6);

        // 2. int × int overflow trap
        System.out.println("\n[ int × int overflow trap ]");
        int items = 100_000;
        int price = 100_000;   // pence (£1000)
        long wrongTotal = items * price;           // int×int overflows first!
        long rightTotal = (long) items * price;    // cast one operand to long first
        System.out.printf("  int×int (wrong): %,d%n", wrongTotal);  // negative: overflowed
        System.out.printf("  long×int (right): %,d pence = £%,.2f%n",
            rightTotal, rightTotal / 100.0);

        // 3. 64-bit unique order IDs
        System.out.println("\n[ 64-bit unique IDs ]");
        long timestamp = System.currentTimeMillis();
        long counter   = 1L;
        // Pack: high 32 bits = timestamp (ms since epoch, lower 32 bits),
        //       low 32 bits  = counter
        long orderId = ((timestamp & 0xFFFFFFFFL) << 32) | (counter & 0xFFFFFFFFL);
        System.out.printf("  timestamp: %,d ms%n", timestamp);
        System.out.printf("  orderId:   %,d%n", orderId);
        System.out.printf("  orderId hex: 0x%016X%n", orderId);
        System.out.printf("  unsigned string: %s%n", Long.toUnsignedString(orderId));

        // Extract components
        long extractedTs = (orderId >>> 32) & 0xFFFFFFFFL;
        long extractedCt = orderId & 0xFFFFFFFFL;
        System.out.printf("  Extracted timestamp: %,d (matches: %b)%n",
            extractedTs, extractedTs == (timestamp & 0xFFFFFFFFL));
        System.out.printf("  Extracted counter: %d%n", extractedCt);
    }
}
```

**How to run:** `java LongIntermediate.java`

`(long) items * price` — the cast `(long)` widens `items` to `long` before the multiplication. Java evaluates left-to-right: `(long)(100_000) * 100_000` = `100_000L * 100_000` = `10_000_000_000L`. Without the cast, `int * int` computes `100_000 * 100_000 = 10,000,000,000` — which overflows `int` before widening to `long`.

### Level 3 — Advanced

Same order analytics: process a dataset of long-valued order IDs and amounts, sort and partition by timestamp embedded in IDs, compute aggregate statistics overflow-safely, and use `LongStream` for efficient processing.

```java
import java.util.*;
import java.util.stream.*;

public class LongAdvanced {
    record OrderRecord(long id, long amountPence, long timestampMs) {}

    // Generate a packed ID: [32 bits timestamp ms lower | 32 bits sequence]
    static long makeId(long timestampMs, long seq) {
        return ((timestampMs & 0xFFFFFFFFL) << 32) | (seq & 0xFFFFFFFFL);
    }

    static long extractTimestamp(long id) { return (id >>> 32) & 0xFFFFFFFFL; }
    static long extractSeq(long id)       { return id & 0xFFFFFFFFL; }

    public static void main(String[] args) {
        System.out.println("=== Advanced long: analytics on 64-bit data ===\n");

        long baseTime = System.currentTimeMillis();

        // Simulate 10 orders over 1 second
        List<OrderRecord> orders = new ArrayList<>();
        for (long i = 0; i < 10; i++) {
            long ts = baseTime + i * 100;     // 100 ms apart
            long id = makeId(ts, i + 1);
            long amount = 5_000L + (i * 3_333L);   // pence: £50..£83
            orders.add(new OrderRecord(id, amount, ts));
        }

        // 1. Print order table
        System.out.println("[ Order table ]");
        System.out.printf("  %-20s  %-14s  %-10s  %s%n",
            "ID (hex)", "Timestamp", "Seq", "Amount (£)");
        System.out.println("  " + "-".repeat(60));
        for (var o : orders)
            System.out.printf("  0x%016X  %,d  %-10d  £%,.2f%n",
                o.id(), extractTimestamp(o.id()), extractSeq(o.id()),
                o.amountPence() / 100.0);

        // 2. Aggregate statistics using LongStream
        System.out.println("\n[ LongStream aggregates ]");
        LongSummaryStatistics stats = orders.stream()
            .mapToLong(OrderRecord::amountPence)
            .summaryStatistics();
        System.out.printf("  Count:   %,d%n",   stats.getCount());
        System.out.printf("  Sum:     %,d pence = £%,.2f%n", stats.getSum(), stats.getSum()/100.0);
        System.out.printf("  Min:     £%,.2f%n", stats.getMin()/100.0);
        System.out.printf("  Max:     £%,.2f%n", stats.getMax()/100.0);
        System.out.printf("  Average: £%,.2f%n", stats.getAverage()/100.0);

        // 3. Overflow-safe sum
        System.out.println("\n[ Overflow-safe accumulation ]");
        long safeSum = 0L;
        for (var o : orders) {
            safeSum = Math.addExact(safeSum, o.amountPence());
        }
        System.out.printf("  Safe sum: %,d pence = £%,.2f%n", safeSum, safeSum/100.0);

        // 4. Sort by embedded timestamp (LSB of ID)
        System.out.println("\n[ Sorted by ID (timestamp embedded) ]");
        orders.stream()
            .sorted(Comparator.comparingLong(OrderRecord::id))
            .limit(5)
            .forEach(o -> System.out.printf("  0x%016X  seq=%d%n",
                o.id(), extractSeq(o.id())));

        // 5. Long API summary
        System.out.println("\n[ Long API ]");
        long val = -1L;
        System.out.printf("  -1L unsigned string:  %s%n",  Long.toUnsignedString(val));
        System.out.printf("  -1L hex:              %s%n",  Long.toHexString(val));
        System.out.printf("  -1L bit count:        %d%n",  Long.bitCount(val));
        System.out.printf("  MAX leadingZeros:     %d%n",  Long.numberOfLeadingZeros(Long.MAX_VALUE));
        System.out.printf("  1L highestOneBit:     %d%n",  Long.highestOneBit(1L));
        System.out.printf("  MAX_VALUE+1:          %d%n",  Long.MAX_VALUE + 1); // overflow to MIN
    }
}
```

**How to run:** `java LongAdvanced.java`

`id >>> 32` — the **unsigned** right shift `>>>` fills the vacated bits with zeros regardless of the sign bit, so `((timestampMs & 0xFFFFFFFFL) << 32) >>> 32` correctly recovers the lower 32 bits of the timestamp. Using `>>` (signed shift) would fill with 1s when bit 63 is set, producing a negative result.

## 6. Walkthrough

Execution trace in `LongAdvanced.main`:

**`makeId(ts, seq)`.** `timestampMs & 0xFFFFFFFFL` keeps only the lower 32 bits of the timestamp (the upper 32 bits of a Unix millisecond timestamp are 0 through roughly year 2106). `<< 32` places those bits in the upper half of the 64-bit `long`. `seq & 0xFFFFFFFFL` keeps the lower 32 bits of the sequence; bitwise `|` combines them into a single `long`. The result is a time-ordered, unique 64-bit identifier.

**`LongSummaryStatistics`.** `mapToLong(OrderRecord::amountPence)` creates a `LongStream`. `.summaryStatistics()` computes count, sum, min, max, average in a single pass. The sum is computed in `long` arithmetic — no overflow for realistic financial totals.

**`Math.addExact(safeSum, o.amountPence())`.** Each addition is checked for overflow before returning. For 10 orders totalling ~£650 in pence, no overflow occurs. In a production billing system processing millions of transactions this guard prevents a silent arithmetic error that would produce a wrong total.

**`id >>> 32`.** The unsigned right shift moves the timestamp bits from positions 32–63 down to positions 0–31. `& 0xFFFFFFFFL` clears any sign-extension bits. `comparingLong(OrderRecord::id)` sorts records by their `long` ID — because timestamps are in the upper 32 bits, records are naturally sorted in time order.

## 7. Gotchas & takeaways

> **`int * int` overflows before being assigned to `long`.** `long total = 1_000_000 * 1_000_000;` computes the multiplication as `int` (overflows to 1,000,000,000,000 → wrong), THEN widens to `long`. Always cast at least one operand: `1_000_000L * 1_000_000`.

> **`>>>` (unsigned right shift) vs `>>` (signed right shift).** For extracting fields from packed `long` values, always use `>>>` — it fills vacated bits with zeros. `>>` fills with the sign bit, which corrupts the extracted value for negative `long` values.

- Range: ±9,223,372,036,854,775,807. `Long.MIN_VALUE` / `MAX_VALUE`. `Long.BYTES = 8`.
- Suffix `L` (uppercase preferred): `10_000_000_000L`. Omitting `L` causes a compile error for values > `Integer.MAX_VALUE`.
- Use `long` for: timestamps (`currentTimeMillis`, `nanoTime`), file sizes, financial totals, population counts, 64-bit IDs.
- `long` arithmetic overflow wraps silently; use `Math.addExact`/`multiplyExact` for critical paths.
- Cast one operand to `long` before a large multiplication: `(long) a * b`, not `(long)(a * b)`.
- `Long.toUnsignedString(n)` — get unsigned decimal representation of a negative `long`.
- `>>>` for unsigned right shift; `>>` for arithmetic (sign-filling) right shift.
- `Long` boxes and caches -128..127; use `.equals()` for `Long` comparisons.
