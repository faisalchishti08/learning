---
card: java
gi: 417
slug: java-util-formatter
title: java.util.Formatter
---

## 1. What it is

`java.util.Formatter`, introduced in Java 5, is the engine behind `String.format()`, `System.out.printf()`, and `PrintStream.format()` — it interprets a **format string** containing `%`-prefixed conversion specifiers (`%d` for integers, `%s` for strings, `%f` for floating point, `%n` for a platform-appropriate newline, and more) and substitutes in the supplied arguments, applying optional width, precision, and flag modifiers along the way. You rarely construct a `Formatter` directly — `String.format(pattern, args...)` and `printf` are the everyday entry points, both built on it internally.

## 2. Why & when

Before this, building formatted output meant manual string concatenation with explicit padding logic — right-aligning a number to a fixed width, for instance, required hand-written loops adding spaces. `Formatter`'s printf-style syntax (borrowed from C) packs alignment, padding, precision, and type conversion into a compact, declarative pattern string: `"%-10s%5.2f%n"` says "left-align a string in a 10-character field, then right-align a floating-point number in a 5-character field with 2 decimal places, then a newline" — far more concise and less error-prone than building the equivalent by hand.

You reach for it constantly: printing aligned tabular output to the console, building log messages with consistent formatting, generating reports with currency or percentage formatting, or anywhere you need a value embedded in text with specific width/precision/alignment rules.

## 3. Core concept

```java
String s = String.format("%-10s%5.2f%n", "Total:", 42.5);
// "%-10s"  -> left-align "Total:" in a 10-char field
// "%5.2f"  -> right-align 42.5 in a 5-char field, 2 decimal places -> "42.50"
// "%n"     -> platform-appropriate newline

System.out.printf("Name: %s, Age: %d%n", "Alice", 30); // printf writes directly, no intermediate String
```

Common conversions: `%d` (integer), `%f` (floating point), `%s` (any object, via `toString()`), `%c` (character), `%b` (boolean), `%x` (hexadecimal), `%%` (a literal percent sign). A width number before the type (`%10d`) sets a minimum field width (right-padded by default with spaces, or zero-padded with `%010d`); a `-` flag (`%-10d`) left-aligns instead; a precision after a dot (`%.2f`) controls decimal places for floating-point values.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A format string with width and precision specifiers maps each %-token to an argument, producing an aligned, padded result">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">"%-10s%6.2f%n"  with  ("Total:", 42.5)</text>

  <rect x="30" y="45" width="150" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="66" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">%-10s -&gt; "Total:    "</text>
  <rect x="200" y="45" width="150" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="275" y="66" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">%6.2f -&gt; " 42.50"</text>

  <text x="20" y="110" fill="#8b949e" font-size="10" font-family="sans-serif">-10  = left-align, minimum 10-char field (10 chars: "Total:" + 4 spaces)</text>
  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">6.2  = minimum 6-char field, 2 decimal places (right-aligned by default: " 42.50")</text>
</svg>

Each specifier independently controls alignment, minimum width, and (for floating point) decimal precision.

## 5. Runnable example

Scenario: printing a small inventory report as an aligned table — the same report, evolved from unaligned, hard-to-read output, through width-and-precision-controlled formatting, to a version handling currency, percentages, and a computed total row.

### Level 1 — Basic

```java
public class InventoryReportUnformatted {
    public static void main(String[] args) {
        String[] items = {"Widget", "Gadget", "Gizmo"};
        int[] quantities = {150, 7, 42};
        double[] prices = {2.5, 199.999, 15.0};

        for (int i = 0; i < items.length; i++) {
            System.out.println(items[i] + " " + quantities[i] + " " + prices[i]); // no alignment at all
        }
    }
}
```

**How to run:** `java InventoryReportUnformatted.java`

Plain concatenation produces ragged, hard-to-scan output — item names of different lengths and numbers of different magnitudes all sit at whatever column their neighboring text happens to push them to, with no consistent alignment.

### Level 2 — Intermediate

```java
public class InventoryReportFormatted {
    public static void main(String[] args) {
        String[] items = {"Widget", "Gadget", "Gizmo"};
        int[] quantities = {150, 7, 42};
        double[] prices = {2.5, 199.999, 15.0};

        System.out.printf("%-10s%8s%10s%n", "Item", "Qty", "Price");
        for (int i = 0; i < items.length; i++) {
            System.out.printf("%-10s%8d%10.2f%n", items[i], quantities[i], prices[i]);
        }
    }
}
```

**How to run:** `java InventoryReportFormatted.java`

`%-10s` left-aligns item names in a fixed 10-character column, `%8d` right-aligns quantities in an 8-character column, and `%10.2f` right-aligns prices in a 10-character column rounded to exactly 2 decimal places — the header row uses the same widths, so everything lines up into clean, readable columns.

### Level 3 — Advanced

```java
public class InventoryReportWithTotals {
    public static void main(String[] args) {
        String[] items = {"Widget", "Gadget", "Gizmo"};
        int[] quantities = {150, 7, 42};
        double[] prices = {2.5, 199.999, 15.0};

        System.out.printf("%-10s%8s%10s%12s%n", "Item", "Qty", "Price", "Subtotal");
        double grandTotal = 0;

        for (int i = 0; i < items.length; i++) {
            double subtotal = quantities[i] * prices[i];
            grandTotal += subtotal;
            System.out.printf("%-10s%8d%10.2f%12.2f%n", items[i], quantities[i], prices[i], subtotal);
        }

        System.out.printf("%-10s%8s%10s%12.2f%n", "TOTAL", "", "", grandTotal);
        System.out.printf("(that's $%,.2f)%n", grandTotal); // %, adds thousands-separator grouping
    }
}
```

**How to run:** `java InventoryReportWithTotals.java`

`%12.2f` adds a fourth aligned column for the computed subtotal, and the final `%,.2f` demonstrates the `,` flag, which inserts thousands-separator commas into large numbers automatically — useful for currency-style output without manually inserting separators.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The header line prints first: `System.out.printf("%-10s%8s%10s%12s%n", "Item", "Qty", "Price", "Subtotal")` produces `"Item"` left-aligned in 10 characters, `"Qty"` right-aligned in 8, `"Price"` right-aligned in 10, `"Subtotal"` right-aligned in 12, followed by a newline.

The loop then processes each item. For `i=0` (`"Widget"`, quantity 150, price 2.5): `subtotal = 150 * 2.5 = 375.0`; `grandTotal` becomes `375.0`. The `printf` call formats `"Widget"` left-aligned in 10 chars, `150` right-aligned in 8 chars, `2.5` as `"2.50"` right-aligned in 10 chars (2 decimal places), and `375.0` as `"375.00"` right-aligned in 12 chars.

For `i=1` (`"Gadget"`, quantity 7, price 199.999): `subtotal = 7 * 199.999 = 1399.993`; `grandTotal` becomes `375.0 + 1399.993 = 1774.993`. Note `199.999` formatted with `%10.2f` **rounds** to `"199.99"` — wait, more precisely, `199.999` rounded to 2 decimal places is `200.00` (since the third decimal digit, 9, rounds the second decimal up from 99 to 100, carrying into the whole number) — printed as `"    200.00"` right-aligned in 10 characters. This is a good example of `%f`'s rounding behavior surfacing a value that looks different from the raw input at a glance.

For `i=2` (`"Gizmo"`, quantity 42, price 15.0): `subtotal = 42 * 15.0 = 630.0`; `grandTotal` becomes `1774.993 + 630.0 = 2404.993`.

After the loop, the `"TOTAL"` row prints with empty strings for the Qty and Price columns (still occupying their column widths as blank space) and `grandTotal` (`2404.993`) formatted as `%12.2f`, rounding to `"2404.99"` — note `2404.993` rounds to `2404.99`, not `2405.00`, since the third decimal digit here is `3`, which rounds down.

Finally, `%,.2f` on `grandTotal` inserts a thousands separator, producing `"$2,404.99"`.

Expected output:
```
Item            Qty     Price    Subtotal
Widget          150      2.50      375.00
Gadget            7    200.00     1399.99
Gizmo            42     15.00      630.00
TOTAL                            2404.99
(that's $2,404.99)
```

## 7. Gotchas & takeaways

> `%f` formatting **rounds** the displayed value to the requested precision (using half-up rounding) — the printed text can look different from a quick mental read of the raw `double`, especially near a rounding boundary like `199.999` becoming `"200.00"`. Never rely on formatted output as a substitute for the actual stored value in calculations; format only at the point of display.

- `String.format(pattern, args...)` returns a formatted `String`; `System.out.printf(pattern, args...)` writes it directly — both are built on `java.util.Formatter` internally.
- A width number (`%10d`) sets a minimum field width, right-aligned by default; add `-` (`%-10d`) to left-align instead.
- A precision after a dot (`%.2f`) controls decimal places for floating-point conversions, applying standard rounding.
- The `,` flag (`%,.2f` or `%,d`) inserts locale-appropriate thousands separators — handy for currency and large-number formatting.
- `%n` is preferred over a literal `\n` inside format strings, since it produces the platform-correct line separator (`\r\n` on Windows, `\n` elsewhere).
