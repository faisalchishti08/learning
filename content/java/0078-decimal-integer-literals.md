---
card: java
gi: 78
slug: decimal-integer-literals
title: Decimal integer literals
---

## 1. What it is

A decimal integer literal is a sequence of digits (`0`–`9`) written in base 10, optionally prefixed with `-` for a negative value and optionally suffixed with `L` (or `l`) to indicate type `long`. Without the `L` suffix, a decimal integer literal has type `int`. Decimal is the most natural and most common way to write integer values in Java source code.

```java
int  age      = 25;
int  negative = -42;
long population = 7_900_000_000L;   // L suffix required — exceeds int range
int  million    = 1_000_000;        // underscores for readability (Java 7+)
```

Decimal literals cannot start with `0` (that makes them octal) — `010` is octal 8, not decimal 10.

## 2. Why & when

Decimal literals are the default choice for any integer value that is a natural count, index, size, or threshold. They are used everywhere: loop bounds, timeouts, capacities, HTTP status codes, port numbers, and score values. Decimal is immediately readable to anyone who knows basic arithmetic — no mental base conversion needed.

Choose a different base when the value's meaning is tied to its bit pattern:
- **Binary** — bitmask flags (Java 7+: `0b0001_0100`).
- **Hex** — memory addresses, colour codes, protocol constants (`0xFF`, `0xDEADBEEF`).
- **Octal** — rarely used; file permission modes are the main surviving use case.

## 3. Core concept

```java
// ---- Plain int literals ----
int a = 42;
int b = 0;          // zero is valid
int c = -2147483648;// Integer.MIN_VALUE — compiler accepts negative literals

// ---- long literals: L suffix mandatory above int range ----
long bigPositive =  9_223_372_036_854_775_807L;  // Long.MAX_VALUE
long justBig     =  3_000_000_000L;              // exceeds int max — L required
long smallLong   =  42L;                          // L allowed even for small values

// ---- Underscores (Java 7+) for readability ----
int  million    = 1_000_000;
long nanos      = 1_000_000_000L;
int  ssn        = 123_45_6789;   // any grouping is legal
// Rules: no underscore at start, end, or adjacent to decimal point / L suffix
// int bad1 = _42;     // compile error
// int bad2 = 42_;     // compile error

// ---- Type of the literal ----
// Without L suffix: int (even when stored in long)
long x = 100;    // 100 is an int literal; widened to long implicitly
// With L suffix: long
long y = 100L;   // long literal

// ---- Out-of-range int literal is a compile error ----
// int overflow = 2_147_483_648;   // compile error: integer number too large
int maxint   = 2_147_483_647;      // OK — exactly Integer.MAX_VALUE
long okLong  = 2_147_483_648L;     // OK — long literal

// ---- Arithmetic with literals ----
int result = 1_000 * 1_000;        // 1_000_000 — fine, stays in int range
long wide  = 1_000_000L * 1_000_000L;  // 1_000_000_000_000 — must be long
// int overflow: 1_000_000 * 1_000_000 → -727379968 (silently wraps)
System.out.println(1_000_000 * 1_000_000);  // -727379968  (int overflow!)
System.out.println(1_000_000L * 1_000_000); //  1_000_000_000_000  (correct)
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of a decimal integer literal: digits, optional underscore separators, optional L suffix, showing int vs long type">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <!-- Literal anatomy -->
  <rect x="16" y="18" width="668" height="70" rx="6" fill="#1c2430"/>
  <text x="350" y="34" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Decimal integer literal anatomy</text>

  <!-- token: 1_000_000_000L -->
  <text x="72" y="64" fill="#6db33f" font-size="22" font-family="monospace">1_000_000_000L</text>

  <!-- annotations -->
  <!-- digit -->
  <line x1="80" y1="70" x2="80" y2="84" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="94" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">leading digit</text>

  <!-- underscore -->
  <line x1="110" y1="70" x2="110" y2="84" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="94" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">_ separator</text>

  <!-- more digits -->
  <line x1="185" y1="70" x2="185" y2="84" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="185" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">more groups</text>

  <!-- L suffix -->
  <line x1="270" y1="70" x2="270" y2="84" stroke="#8b949e" stroke-width="1.5"/>
  <text x="270" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">L → long</text>

  <!-- int range box -->
  <rect x="16" y="100" width="320" height="62" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="176" y="116" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">int range (no L)</text>
  <line x1="26" y1="122" x2="326" y2="122" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="136" fill="#e6edf3" font-size="8" font-family="monospace">−2 147 483 648 … 2 147 483 647</text>
  <text x="26" y="152" fill="#8b949e" font-size="7.5" font-family="monospace">out-of-range → compile error</text>

  <!-- long range box -->
  <rect x="348" y="100" width="336" height="62" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="516" y="116" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">long range (L suffix)</text>
  <line x1="358" y1="122" x2="674" y2="122" stroke="#8b949e" stroke-width="0.5"/>
  <text x="358" y="136" fill="#e6edf3" font-size="8" font-family="monospace">−9.2×10¹⁸ … 9.2×10¹⁸</text>
  <text x="358" y="152" fill="#8b949e" font-size="7.5" font-family="monospace">use L suffix for values &gt; 2.1B</text>
</svg>

A decimal literal is one or more base-10 digits with optional `_` separators; appending `L` makes it a `long` literal — necessary for values above `Integer.MAX_VALUE`.

## 5. Runnable example

Scenario: an event ticketing system that manages venue capacity, ticket sales, and revenue — the growing example moves from simple integer literals, to overflow detection on ticket counts, to a full sales report with mixed `int` and `long` arithmetic.

### Level 1 — Basic

```java
public class DecimalLiteralsBasic {
    public static void main(String[] args) {
        int  venueCapacity = 80_000;
        int  ticketsSold   = 62_450;
        int  ticketPrice   = 95;        // dollars

        int  ticketsLeft   = venueCapacity - ticketsSold;
        long totalRevenue  = (long) ticketsSold * ticketPrice;  // cast before multiply

        System.out.println("=== Ticket Sales Report ===");
        System.out.printf("Venue capacity : %,d%n",  venueCapacity);
        System.out.printf("Tickets sold   : %,d%n",  ticketsSold);
        System.out.printf("Tickets left   : %,d%n",  ticketsLeft);
        System.out.printf("Total revenue  : $%,d%n", totalRevenue);

        double fillRate = (double) ticketsSold / venueCapacity * 100.0;
        System.out.printf("Fill rate      : %.1f%%%n", fillRate);
    }
}
```

**How to run:** `java DecimalLiteralsBasic.java`

`80_000` and `62_450` use underscores as digit separators for readability — the compiler ignores the underscores entirely. `(long) ticketsSold * ticketPrice` casts `ticketsSold` to `long` before the multiplication so the arithmetic happens in 64-bit space. Without the cast, `62_450 * 95 = 5_932_750`, which fits in `int`, but the pattern must be established consistently: for larger values the int multiplication would overflow silently. The `%,d` format specifier in `printf` inserts locale-appropriate thousands separators.

### Level 2 — Intermediate

Same ticketing system: extend to a multi-day festival with cumulative revenue that exceeds `int` range, demonstrate the silent overflow, and fix it.

```java
public class DecimalLiteralsIntermediate {

    record DayReport(String day, int tickets, int pricePerTicket) {
        long revenue() { return (long) tickets * pricePerTicket; }
    }

    public static void main(String[] args) {
        int dailyCapacity = 80_000;
        int priceVIP      = 350;
        int priceGeneral  = 95;

        var days = java.util.List.of(
            new DayReport("Friday",   75_200, priceGeneral),
            new DayReport("Saturday", 80_000, priceVIP),
            new DayReport("Sunday",   79_500, priceGeneral)
        );

        long totalRevenue = 0L;
        long totalTickets = 0L;

        System.out.printf("%-10s  %8s  %8s  %14s%n", "Day", "Tickets", "Price", "Revenue");
        System.out.println("-".repeat(46));

        for (var d : days) {
            long rev = d.revenue();
            totalRevenue += rev;
            totalTickets += d.tickets();
            System.out.printf("%-10s  %,8d  $%,7d  $%,14d%n",
                d.day(), d.tickets(), d.pricePerTicket(), rev);
        }

        System.out.println("-".repeat(46));
        System.out.printf("%-10s  %,8d           $%,14d%n", "TOTAL", totalTickets, totalRevenue);

        // Demonstrate int overflow on same calculation
        int wrongTotal = 0;
        for (var d : days) {
            wrongTotal += d.tickets() * d.pricePerTicket();   // both int — may overflow
        }
        System.out.println();
        System.out.println("Correct (long) : $" + String.format("%,d", totalRevenue));
        System.out.println("Wrong  (int)   : $" + String.format("%,d", wrongTotal));
        System.out.println("Difference     : " + (totalRevenue != wrongTotal ? "OVERFLOW DETECTED" : "same"));
    }
}
```

**How to run:** `java DecimalLiteralsIntermediate.java`

Saturday alone generates `80_000 × 350 = 28_000_000` — well within `int`. But the cumulative festival revenue (`≈ 43 M`) also fits in `int`. However, the `wrongTotal` calculation uses `d.tickets() * d.pricePerTicket()` without a cast — both are `int`, so Java performs `int` multiplication. For Saturday: `80_000 * 350 = 28_000_000`, which is within `int` range. The overflow here is subtle — on a larger festival or higher price it would silently corrupt. `(long) tickets * price` prevents it by widening before the multiply.

### Level 3 — Advanced

Same system: a stress test calculates the total revenue for a hypothetical 1-billion-ticket event, demonstrates overflow at each integer type boundary, and uses `Math.multiplyExact` for safe detection.

```java
public class DecimalLiteralsAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Overflow boundary tests ===");

        // 1. int overflow at the multiply step
        int tickets   = 100_000;
        int priceHigh = 25_000;   // premium event
        int productInt = tickets * priceHigh;  // 100_000 * 25_000 = 2_500_000_000 > INT_MAX
        long productLong = (long) tickets * priceHigh;

        System.out.printf("tickets=%,d  price=%,d%n", tickets, priceHigh);
        System.out.printf("int  multiply : %,d   (overflow: %b)%n",
            productInt, productInt < 0);
        System.out.printf("long multiply : %,d   (correct)%n", productLong);

        // 2. Math.multiplyExact — throws on overflow
        System.out.println();
        System.out.println("[ Math.multiplyExact ]");
        try {
            int exact = Math.multiplyExact(tickets, priceHigh);
            System.out.println("exact: " + exact);   // should not reach here
        } catch (ArithmeticException e) {
            System.out.println("Caught overflow: " + e.getMessage());
        }
        // Long version succeeds
        long safeProduct = Math.multiplyExact((long) tickets, (long) priceHigh);
        System.out.println("long exact: " + String.format("%,d", safeProduct));

        // 3. Underscores do not affect value
        int a = 1_000_000;
        int b = 1000000;
        System.out.println();
        System.out.println("1_000_000 == 1000000: " + (a == b));  // true

        // 4. Literal type in compound expression
        // Without L suffix the intermediate result wraps before being widened
        long wrong = 1_000_000 * 1_000_000;   // int*int = -727379968, then widened to long
        long right = 1_000_000L * 1_000_000;  // long*int = 1_000_000_000_000

        System.out.println();
        System.out.printf("1_000_000  * 1_000_000  = %,d (int overflow then widen)%n", wrong);
        System.out.printf("1_000_000L * 1_000_000  = %,d (correct)%n", right);
    }
}
```

**How to run:** `java DecimalLiteralsAdvanced.java`

`100_000 * 25_000 = 2_500_000_000`, which exceeds `Integer.MAX_VALUE` (2 147 483 647). Java computes the multiplication in `int` arithmetic and silently wraps. The cast `(long) tickets * priceHigh` promotes `tickets` to `long` first, so the multiplication proceeds in `long` arithmetic. `Math.multiplyExact(int, int)` computes the same multiplication but detects the overflow and throws `ArithmeticException` — ideal for any code path where silent corruption would be worse than a failure. The `1_000_000 * 1_000_000` example shows that the literal type matters in compound expressions: both operands are `int`, so the product is computed as `int` (wrapping to `-727_379_968`) before the assignment widens it to `long`. Appending `L` to one operand makes it a `long` literal, which forces `long` arithmetic and gives the correct result.

## 6. Walkthrough

Execution trace through `DecimalLiteralsAdvanced.main`:

**Overflow test.** `tickets * priceHigh` is `100_000 * 25_000`. The Java compiler evaluates both as `int`. In two's complement 32-bit arithmetic, `2_500_000_000` decimal is `0x9502F900`, which has its sign bit set, giving `-1_794_967_296`. The result is stored in `productInt`. `(long) tickets * priceHigh` promotes `tickets` (100 000 as an `int`) to `long` (100 000 as a `long`), then multiplies by `priceHigh` widened to `long`. The result `2_500_000_000L` fits within `long` range.

**`Math.multiplyExact`.** Internally, `Math.multiplyExact(int a, int b)` promotes both to `long`, multiplies, and checks whether the result fits back in an `int`. If not, it throws `ArithmeticException("integer overflow")`. The `long` overload `Math.multiplyExact(long, long)` performs the same check in 64-bit. Both land in the `catch` / success path respectively.

**Underscore equality.** The compiler strips all underscores before evaluating the literal. `1_000_000` and `1000000` produce identical bytecode. The `==` comparison confirms they are the same `int` value.

**Literal type in compound expression.** Java evaluates `1_000_000 * 1_000_000` left to right with both operands as `int`. The intermediate result (`-727_379_968`, an overflow) is produced before the assignment widens it to `long`. Once `long` is assigned, the damage is already done. Appending `L` to the first operand changes its type to `long`; Java then widens the second operand to `long` for the multiplication, preventing overflow.

```
Expression type rules:
  int_literal  * int_literal  → int  (may overflow)
  long_literal * int_literal  → long (int widened)
  (long) int   * int_literal  → long (cast forces long arithmetic)
```

## 7. Gotchas & takeaways

> **A decimal literal that exceeds `Integer.MAX_VALUE` without the `L` suffix is a compile-time error.** Write `3_000_000_000L`, not `3_000_000_000` — the latter does not compile because it is out of the `int` range.

> **`long wrong = 1_000_000 * 1_000_000;` silently overflows.** The multiplication is performed in `int` arithmetic before the assignment widens the result to `long`. Append `L` to at least one operand or cast one to `long` to force `long` arithmetic.

- Decimal literals use digits `0`–`9` and never start with `0` (that is octal).
- The `L` suffix (preferably uppercase to distinguish from digit `1`) makes the literal type `long`.
- Underscores (`_`) may appear between digits from Java 7 onwards — they are ignored by the compiler and exist solely for human readability.
- When multiplying two `int` values whose product might exceed `Integer.MAX_VALUE`, cast one operand to `long` before the multiplication, or use `Math.multiplyExact`.
- `%,d` in `printf`/`format` adds locale-appropriate thousands separators (commas in the US locale).
- Always use `Integer.MAX_VALUE` (2 147 483 647) rather than magic numbers; it is self-documenting and correct regardless of platform.
