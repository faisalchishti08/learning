---
card: java
gi: 71
slug: int-32-bit-signed
title: int (32-bit signed)
---

## 1. What it is

`int` is Java's **default integer type** — a signed 32-bit two's-complement integer with the range **-2,147,483,648 to 2,147,483,647** (roughly ±2 billion). It is the type the compiler produces for integer literals, the type all smaller integers (`byte`, `short`) promote to in arithmetic, and the type you should reach for first.

```java
int count  = 0;
int max    = Integer.MAX_VALUE;    //  2_147_483_647
int min    = Integer.MIN_VALUE;    // -2_147_483_648
int hex    = 0xFF_FF;              // 65535 — hex literal
int binary = 0b1010_1010;         // 170  — binary literal
int big    = 1_000_000;            // underscores for readability
```

The boxed wrapper is `Integer`. Almost all JDK APIs that return counts, indices, hash codes, or status codes use `int`.

## 2. Why & when

`int` is the workhorse integer. Use it:
- For loop counters, indices, counts, sizes — the vast majority of integer use.
- Whenever the value fits in ±2 billion (i.e., most of the time).
- As the return type for `hashCode()`, `compareTo()`, `indexOf()`, `size()`.

Switch to `long` when values can exceed ±2 billion: file sizes, epoch milliseconds, population counts, financial totals.

## 3. Core concept

```java
// ---- Constants ----
System.out.println(Integer.MAX_VALUE);    //  2147483647
System.out.println(Integer.MIN_VALUE);    // -2147483648
System.out.println(Integer.SIZE);         // 32 (bits)
System.out.println(Integer.BYTES);        // 4

// ---- Overflow ---- silently wraps, no exception
int wrap = Integer.MAX_VALUE;
wrap++;       // → -2147483648   (MIN_VALUE)
System.out.println(wrap);

// ---- Integer literals ----
int decimal  = 255;
int hex      = 0xFF;      // same as 255
int octal    = 0377;      // same as 255 — prefix 0 means octal (avoid in modern code)
int binary   = 0b1111_1111;  // same as 255
// Underscores improve readability — ignored by compiler:
int million  = 1_000_000;
int credit   = 4_012_345_678;   // ✗ too big for int: > MAX_VALUE — compile error

// ---- Arithmetic ----
int a = 1_000_000, b = 3;
System.out.println(a + b);    // 1000003
System.out.println(a * b);    // 3000000
System.out.println(a / b);    // 333333  (integer division — truncates toward zero)
System.out.println(a % b);    // 1       (remainder: sign follows dividend)
System.out.println(-7 % 3);   // -1 (not 2 — Java modulo keeps sign of dividend)

// ---- Integer API ----
System.out.println(Integer.toBinaryString(255));  // 11111111
System.out.println(Integer.toHexString(255));     // ff
System.out.println(Integer.toOctalString(255));   // 377
System.out.println(Integer.parseInt("FF", 16));   // 255
System.out.println(Integer.bitCount(255));         // 8 (popcount)
System.out.println(Integer.highestOneBit(100));   // 64
System.out.println(Integer.numberOfLeadingZeros(1)); // 31
System.out.println(Integer.reverse(1));            // −2147483648 (bit reversal)

// ---- Autoboxing ----
Integer boxed = 42;    // autoboxing
int     prim  = boxed; // unboxing
// Cache: Integer.valueOf(n) for n in -128..127 returns cached instances:
Integer a2 = 127, b2 = 127;
System.out.println(a2 == b2);   // true  (same cached object)
Integer a3 = 128, b3 = 128;
System.out.println(a3 == b3);   // false (different objects — outside cache)
System.out.println(a3.equals(b3)); // true  (always use equals() for Integer)
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="int: 32-bit signed, range -2B to +2B, bit layout, arithmetic rules, Integer cache -128 to 127">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Number line -->
  <rect x="16" y="20" width="670" height="42" rx="5" fill="#1c2430"/>
  <line x1="30" y1="46" x2="672" y2="46" stroke="#8b949e" stroke-width="1"/>
  <line x1="30"  y1="42" x2="30"  y2="50" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="30" y="57" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="monospace">-2,147,483,648</text>
  <line x1="351" y1="40" x2="351" y2="52" stroke="#79c0ff" stroke-width="2"/>
  <text x="351" y="57" fill="#79c0ff" font-size="6.5" text-anchor="middle" font-family="monospace">0</text>
  <line x1="672" y1="42" x2="672" y2="50" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="672" y="57" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="monospace">2,147,483,647</text>
  <!-- Integer cache region -->
  <rect x="338" y="32" width="26" height="8" rx="2" fill="#6db33f" opacity="0.4"/>
  <text x="351" y="27" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">Integer cache: -128..127</text>

  <!-- Bit layout -->
  <rect x="16" y="72" width="340" height="90" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="186" y="88" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">32-bit layout (MAX_VALUE = 0x7FFF_FFFF)</text>
  <!-- 8 blocks of 4 bits -->
  <text x="26" y="106" fill="#8b949e" font-size="7.5" font-family="monospace">bit 31</text>
  <rect x="70" y="96" width="14" height="16" rx="2" fill="#0d1117" stroke="#8b949e"/>
  <text x="77" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">0</text>
  <!-- remaining bits -->
  <rect x="86"  y="96" width="14" height="16" rx="2" fill="#0d1117" stroke="#6db33f"/>
  <text x="93"  y="108" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">1</text>
  <rect x="102" y="96" width="14" height="16" rx="2" fill="#0d1117" stroke="#6db33f"/>
  <text x="109" y="108" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">1</text>
  <rect x="118" y="96" width="14" height="16" rx="2" fill="#0d1117" stroke="#6db33f"/>
  <text x="125" y="108" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">1</text>
  <text x="148" y="108" fill="#8b949e" font-size="8" font-family="monospace">... 28 more 1-bits ...</text>
  <text x="26" y="126" fill="#8b949e" font-size="7.5" font-family="sans-serif">bit 31 = sign bit. MAX = 0 followed by 31 ones.</text>
  <text x="26" y="139" fill="#8b949e" font-size="7.5" font-family="sans-serif">MIN = 1 followed by 31 zeros = -2,147,483,648</text>
  <text x="26" y="152" fill="#8b949e" font-size="7.5" font-family="sans-serif">-1  = all 32 bits set = 0xFFFF_FFFF</text>

  <!-- API box -->
  <rect x="366" y="72" width="320" height="90" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="526" y="88" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Integer API highlights</text>
  <text x="376" y="103" fill="#e6edf3" font-size="7.5" font-family="monospace">parseInt("FF", 16)  → 255</text>
  <text x="376" y="116" fill="#e6edf3" font-size="7.5" font-family="monospace">toBinaryString(10)  → "1010"</text>
  <text x="376" y="129" fill="#e6edf3" font-size="7.5" font-family="monospace">bitCount(255)       → 8</text>
  <text x="376" y="142" fill="#e6edf3" font-size="7.5" font-family="monospace">compare(a, b)       → -1/0/1</text>
  <text x="376" y="155" fill="#8b949e" font-size="7" font-family="monospace">Integer.valueOf(n): cached -128..127</text>
</svg>

`int` is the default integer — 32 bits, signed. Use `long` only when values exceed ±2 billion; use `Integer.valueOf()` and `.equals()` for boxed comparisons.

## 5. Runnable example

Scenario: an order statistics calculator — uses `int` for counts and indices, demonstrates overflow, bit manipulation, and the `Integer` API in a growing realistic context.

### Level 1 — Basic

```java
public class IntBasic {
    public static void main(String[] args) {
        System.out.println("=== int basics ===\n");

        // Constants
        System.out.println("MAX_VALUE: " + Integer.MAX_VALUE);
        System.out.println("MIN_VALUE: " + Integer.MIN_VALUE);

        // Order statistics
        int totalOrders   = 1_248_392;
        int paidOrders    = 1_100_000;
        int pendingOrders = totalOrders - paidOrders;
        int avgAmount     = 15_499;   // in pence: £154.99

        System.out.printf("%nTotal orders:   %,d%n", totalOrders);
        System.out.printf("Paid orders:    %,d%n", paidOrders);
        System.out.printf("Pending orders: %,d%n", pendingOrders);

        // Integer arithmetic
        int paidPercent = paidOrders * 100 / totalOrders;   // integer division
        System.out.printf("Paid %%:         %d%%%n", paidPercent);

        // Overflow demo
        System.out.println("\n[ Overflow (wraps silently) ]");
        int nearMax = Integer.MAX_VALUE;
        System.out.printf("MAX_VALUE + 1 = %d (wraps to MIN_VALUE)%n", nearMax + 1);

        // Hex/binary literals
        int mask = 0xFF00_FF00;   // bit mask
        int flags = 0b0000_0101;  // bits 0 and 2 set
        System.out.printf("%nMask:  0x%08X  Flags: %s%n",
            mask, Integer.toBinaryString(flags));
    }
}
```

**How to run:** `java IntBasic.java`

`paidOrders * 100 / totalOrders` — both operands are `int`, so division truncates toward zero. The order matters: multiply first to maximise precision before dividing. If you divided first (`paidOrders / totalOrders`), you'd get `0` since it's integer division.

### Level 2 — Intermediate

Same order system: use the `Integer` API (parsing, bit operations, compare), demonstrate the Integer cache behaviour, and use `int` for a hash code implementation.

```java
import java.util.*;

public class IntIntermediate {
    record Order(String id, int amountPence, int statusCode) {}

    public static void main(String[] args) {
        System.out.println("=== Intermediate int: Integer API + hashing ===\n");

        // 1. Integer.parseInt with radix
        System.out.println("[ Parsing ]");
        System.out.printf("  decimal: %d%n", Integer.parseInt("12345"));
        System.out.printf("  hex:     %d%n", Integer.parseInt("FF", 16));
        System.out.printf("  binary:  %d%n", Integer.parseInt("10101010", 2));
        System.out.printf("  octal:   %d%n", Integer.parseInt("377", 8));

        // 2. Bit operations on flags
        System.out.println("\n[ Bit flags ]");
        int PAID      = 1;       // bit 0
        int VERIFIED  = 1 << 1;  // bit 1 = 2
        int SHIPPED   = 1 << 2;  // bit 2 = 4
        int RETURNED  = 1 << 3;  // bit 3 = 8

        int orderFlags = PAID | VERIFIED | SHIPPED;  // 7 = 0b0111

        System.out.printf("  flags: %d (binary: %s)%n",
            orderFlags, Integer.toBinaryString(orderFlags));
        System.out.println("  isPaid:     " + ((orderFlags & PAID) != 0));
        System.out.println("  isShipped:  " + ((orderFlags & SHIPPED) != 0));
        System.out.println("  isReturned: " + ((orderFlags & RETURNED) != 0));

        // Set a flag:
        orderFlags |= RETURNED;
        System.out.println("  After set RETURNED: " + Integer.toBinaryString(orderFlags));
        // Clear a flag:
        orderFlags &= ~RETURNED;
        System.out.println("  After clear RETURNED: " + Integer.toBinaryString(orderFlags));

        // 3. Integer cache
        System.out.println("\n[ Integer cache (-128..127) ]");
        Integer a = 127, b = 127;
        Integer c = 128, d = 128;
        System.out.println("  127 == 127: " + (a == b) + "  (same cached instance)");
        System.out.println("  128 == 128: " + (c == d) + "  (different objects)");
        System.out.println("  128.equals(128): " + c.equals(d) + "  (always use equals)");

        // 4. Custom hash code using Integer API
        System.out.println("\n[ hashCode using Integer.hashCode ]");
        var orders = List.of(
            new Order("ORD-001", 29999, 1),
            new Order("ORD-002",  5000, 2),
            new Order("ORD-003", 12000, 1)
        );
        for (Order o : orders) {
            int hash = Objects.hash(o.id(), o.amountPence(), o.statusCode());
            System.out.printf("  %s  hash=%d  (0x%08X)%n", o.id(), hash, hash);
        }
    }
}
```

**How to run:** `java IntIntermediate.java`

`orderFlags |= RETURNED` sets bit 3 by OR-ing with `8` (`0b1000`). `orderFlags &= ~RETURNED` clears bit 3 by AND-ing with the bitwise complement of `8` = `0xFFFFFFF7`. This pattern is the standard bit-flag idiom in C/Java — no allocation, no boxing.

### Level 3 — Advanced

Same order system: overflow-safe arithmetic using `Math.addExact`/`multiplyExact`, unsigned 32-bit arithmetic with `Integer.toUnsignedLong` and `Integer.compareUnsigned`, and a performance comparison between `int[]` and `Integer[]` for summing.

```java
import java.util.*;
import java.util.stream.*;

public class IntAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Advanced int: overflow safety + unsigned + perf ===\n");

        // 1. Overflow-safe arithmetic (Math.addExact throws on overflow)
        System.out.println("[ Overflow-safe arithmetic ]");
        try {
            int a = Integer.MAX_VALUE;
            int b = 1;
            int result = Math.addExact(a, b);  // throws ArithmeticException
            System.out.println("  Result: " + result);
        } catch (ArithmeticException e) {
            System.out.println("  Math.addExact overflow: " + e.getMessage());
        }

        // Safe multiplication
        try {
            int items  = 100_000;
            int price  = 100_000;   // pence
            long total = Math.multiplyExact((long) items, price);
            System.out.printf("  100000 × 100000 = %,d pence = £%,.2f%n",
                total, total / 100.0);
        } catch (ArithmeticException e) {
            System.out.println("  overflow: " + e.getMessage());
        }

        // 2. Unsigned 32-bit operations
        System.out.println("\n[ Unsigned 32-bit ]");
        int signedNeg  = -1;                      // 0xFFFF_FFFF as bits
        long unsigned  = Integer.toUnsignedLong(signedNeg);   // 4294967295
        System.out.printf("  -1 as signed int:   %d%n", signedNeg);
        System.out.printf("  -1 as unsigned:     %,d  (0x%08X)%n", unsigned, signedNeg);

        int a = -1;
        int b = 1;
        System.out.printf("  Signed compare(-1, 1):   %d%n", Integer.compare(a, b));      // -1
        System.out.printf("  Unsigned compare(-1, 1): %d%n", Integer.compareUnsigned(a, b));  // 1 (0xFFFF>0x0001)

        // 3. int[] vs Integer[] sum performance
        System.out.println("\n[ int[] vs Integer[] performance ]");
        int n = 1_000_000;
        int[]     primitiveArr = IntStream.range(0, n).toArray();
        Integer[] boxedArr     = IntStream.range(0, n).boxed().toArray(Integer[]::new);

        long t1 = System.nanoTime();
        long sum1 = 0; for (int x : primitiveArr) sum1 += x;
        long t2 = System.nanoTime();
        long sum2 = 0; for (int x : boxedArr)     sum2 += x;   // unboxing on each access
        long t3 = System.nanoTime();

        System.out.printf("  int[%,d]:     sum=%,d  time=%,d µs%n", n, sum1, (t2-t1)/1000);
        System.out.printf("  Integer[%,d]: sum=%,d  time=%,d µs%n", n, sum2, (t3-t2)/1000);
        System.out.println("  (int[] faster: no unboxing, better cache locality)");

        // 4. Integer bit operations summary
        System.out.println("\n[ Integer bit ops ]");
        int val = 0b1010_1100;   // 172
        System.out.printf("  value:           %d (0x%02X, binary: %s)%n",
            val, val, Integer.toBinaryString(val));
        System.out.printf("  bitCount:        %d (set bits)%n",       Integer.bitCount(val));
        System.out.printf("  leadingZeros:    %d%n",                   Integer.numberOfLeadingZeros(val));
        System.out.printf("  trailingZeros:   %d%n",                   Integer.numberOfTrailingZeros(val));
        System.out.printf("  highestOneBit:   %d%n",                   Integer.highestOneBit(val));
        System.out.printf("  lowestOneBit:    %d%n",                   Integer.lowestOneBit(val));
        System.out.printf("  reverse:         0x%08X%n",               Integer.reverse(val));
        System.out.printf("  reverseBytes:    0x%08X%n",               Integer.reverseBytes(val));
    }
}
```

**How to run:** `java IntAdvanced.java`

`Math.addExact(a, b)` performs the addition and checks for overflow before returning — it throws `ArithmeticException` rather than silently wrapping. This is essential in financial calculations where overflow would produce a wrong total with no error signal.

## 6. Walkthrough

Execution trace in `IntAdvanced.main`:

**`Math.addExact(Integer.MAX_VALUE, 1)`.** Internally the JVM performs the addition as a 64-bit operation, then checks if the result fits in 32 bits. `2,147,483,647 + 1 = 2,147,483,648` exceeds `Integer.MAX_VALUE` — `ArithmeticException("integer overflow")` is thrown. This prevents the silent wrap to `-2,147,483,648`.

**`Math.multiplyExact((long) items, price)`.** The cast `(long) items` widens one operand to `long` before the multiplication, so the result is computed in 64 bits: `100,000 × 100,000 = 10,000,000,000`. This fits in `long` (max ~9.2 × 10¹⁸). If both operands had stayed `int`, the multiplication would overflow silently.

**`Integer.toUnsignedLong(-1)`.** `-1` as a 32-bit pattern is `0xFFFFFFFF`. Treating the bits as unsigned gives 4,294,967,295. `toUnsignedLong` zero-extends the `int` bits into a `long`, producing `0x00000000FFFFFFFF = 4,294,967,295`.

**`Integer.compareUnsigned(-1, 1)`.** Treats both values as unsigned: `-1` → `0xFFFFFFFF = 4,294,967,295`; `1` → `1`. `4,294,967,295 > 1`, so the result is positive (greater than). The standard `Integer.compare(-1, 1)` returns `-1` (less than, signed).

**Performance.** The `Integer[]` loop unboxes each element from a heap object reference to a primitive `int` for addition. The `int[]` loop reads packed 4-byte values from a contiguous memory region — better cache locality and no object header overhead per element.

## 7. Gotchas & takeaways

> **Integer overflow is silent and wraps.** `Integer.MAX_VALUE + 1 == Integer.MIN_VALUE`. Use `Math.addExact`/`multiplyExact`/`subtractExact` in financial or safety-critical code. Or switch to `long` if the range is borderline.

> **`Integer == Integer` uses reference equality above 127.** `Integer a = 128; Integer b = 128; a == b` is `false` — they are different objects. Always use `.equals()` or `Integer.compare()` to compare `Integer` values. The cached range (-128..127) is an implementation detail you should not rely on.

- Range: -2,147,483,648 to 2,147,483,647. `Integer.MIN_VALUE` / `MAX_VALUE`. `Integer.BYTES = 4`.
- Default integer type — use `int` first; switch to `long` only when necessary.
- Integer literals: decimal, `0x` hex, `0b` binary, `0` octal (avoid octal). Underscores for readability.
- `int` division truncates toward zero; `-7 % 3 == -1` (sign follows dividend).
- Overflow wraps silently — use `Math.addExact`/`multiplyExact` to throw on overflow.
- Integer cache: `Integer.valueOf(n)` caches -128..127; always use `.equals()` for `Integer` comparison.
- `Integer.toUnsignedLong` / `compareUnsigned` for unsigned 32-bit semantics.
- Bit operations: `bitCount`, `highestOneBit`, `numberOfLeadingZeros`, `reverse`, `reverseBytes`.
