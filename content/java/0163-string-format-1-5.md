---
card: java
gi: 163
slug: string-format-1-5
title: String.format() (1.5)
---

## 1. What it is

`String.format(String format, Object... args)`, added in Java 1.5, builds a string from a **format template** containing conversion specifiers (like `%s`, `%d`, `%.2f`) that get replaced by the corresponding arguments, formatted according to the specifier. It's a static method, called on the `String` class itself, and it's the same formatting engine that powers `System.out.printf`.

```java
String name = "Alice";
int age = 30;
double balance = 1234.5;

String message = String.format("Name: %s, Age: %d, Balance: $%.2f", name, age, balance);
System.out.println(message);
// "Name: Alice, Age: 30, Balance: $1234.50"
```

`%s` formats any argument as a string (calling `toString()` on it), `%d` formats an integer, and `%.2f` formats a floating-point number to exactly 2 decimal places — the format string and the argument list must line up in both count and compatible type, or a `MissingFormatArgumentException`/`IllegalFormatConversionException` is thrown at runtime.

## 2. Why & when

`String.format` is the right tool whenever you need **precise, structured control** over how values are rendered into text — something plain `+` concatenation can't offer directly:

- **Numeric formatting** — controlling decimal places (`%.2f` for currency), padding with zeros (`%05d`), or displaying in different bases (`%x` for hexadecimal).
- **Column alignment** — `%-10s` left-pads a string to a fixed width, useful for generating readable tabular text output.
- **Readable templates** — a single format string clearly shows the shape of the final output, which can be easier to review at a glance than a long chain of `+` concatenations mixing literal text and variables.

For simple, unformatted concatenation with no special numeric or alignment requirements, plain `+` remains simpler; `String.format` earns its place specifically when formatting rules (decimal places, padding, alignment) actually matter.

## 3. Core concept

```java
public class FormatDemo {
    public static void main(String[] args) {
        System.out.println(String.format("%d", 42));        // "42"
        System.out.println(String.format("%5d", 42));        // "   42" — padded to width 5
        System.out.println(String.format("%-5d|", 42));      // "42   |" — left-aligned, padded to width 5
        System.out.println(String.format("%05d", 42));       // "00042" — zero-padded
        System.out.println(String.format("%.2f", 3.14159));  // "3.14" — 2 decimal places
        System.out.println(String.format("%,d", 1234567));   // "1,234,567" — grouping separator
        System.out.println(String.format("%s and %s", "cats", "dogs")); // "cats and dogs"
    }
}
```

Each format specifier controls a distinct aspect: width (`%5d`), alignment (`%-5d`), zero-padding (`%05d`), decimal precision (`%.2f`), and grouping separators (`%,d`) — these can also be combined (e.g., `%,10.2f` for a grouped, width-padded decimal).

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String format diagram: the format string Name colon percent s comma Balance colon dollar percent dot two f is filled in with the arguments Alice and 1234.5, producing Name colon Alice comma Balance colon dollar one thousand two hundred thirty four point five zero, with the decimal formatted to exactly two places." >
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String.format("Name: %s, Balance: $%.2f", "Alice", 1234.5)</text>

  <rect x="60" y="45" width="120" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="120" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">%s</text>
  <path d="M 120 73 L 120 95" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#a)"/>
  <rect x="60" y="95" width="120" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="120" y="114" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"Alice"</text>

  <rect x="220" y="45" width="140" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="290" y="64" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">%.2f</text>
  <path d="M 290 73 L 290 95" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#b)"/>
  <rect x="220" y="95" width="140" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="290" y="114" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">1234.50</text>

  <text x="350" y="140" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Each specifier consumes the next argument in order, formatting it according to its own rules.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each format specifier consumes the next argument in sequence and renders it according to its own formatting rules.

## 5. Runnable example

Scenario: generating a formatted receipt for a shopping cart — starting with basic currency and quantity formatting, then adding column alignment for a multi-item receipt, then hardening it with proper handling of a locale-aware grouping separator and validated precision for a realistic invoice format.

### Level 1 — Basic

```java
public class ReceiptFormatBasic {
    public static void main(String[] args) {
        String item = "Coffee";
        int quantity = 3;
        double price = 4.5;

        String line = String.format("%s x%d: $%.2f", item, quantity, price * quantity);
        System.out.println(line);
    }
}
```

**How to run:** `java ReceiptFormatBasic.java`

`%s` consumes `item` (`"Coffee"`), `%d` consumes `quantity` (`3`), and `%.2f` consumes the computed subtotal (`13.5`), formatting it to exactly two decimal places — output: `"Coffee x3: $13.50"`, with the trailing zero explicitly added by the `%.2f` specifier, something plain `+` concatenation of `13.5` would not have produced on its own.

### Level 2 — Intermediate

Same receipt, now formatting **multiple items** with aligned columns, using width specifiers so item names and prices line up visually regardless of each item's name length.

```java
public class ReceiptFormatIntermediate {
    public static void main(String[] args) {
        String[] items = { "Coffee", "Bagel", "Orange Juice" };
        int[] quantities = { 3, 2, 1 };
        double[] prices = { 4.5, 2.25, 3.75 };

        for (int i = 0; i < items.length; i++) {
            double subtotal = quantities[i] * prices[i];
            System.out.println(String.format("%-15s x%-3d $%8.2f", items[i], quantities[i], subtotal));
        }
    }
}
```

**How to run:** `java ReceiptFormatIntermediate.java`

`%-15s` left-aligns the item name within a 15-character field (padding with spaces on the right), `%-3d` left-aligns the quantity within 3 characters, and `%8.2f` right-aligns the subtotal within an 8-character field with 2 decimal places — the combination produces neatly aligned columns regardless of each item name's actual length, since every row's fields occupy the same fixed widths.

### Level 3 — Advanced

Same receipt, now formatting the **grand total** with a thousands-grouping separator (relevant for larger totals) and validating that quantities/prices are non-negative before formatting, since a format specifier alone won't catch invalid business data.

```java
public class ReceiptFormatAdvanced {

    static double computeAndValidateSubtotal(String item, int quantity, double price) {
        if (quantity < 0 || price < 0) {
            throw new IllegalArgumentException("Invalid data for " + item + ": quantity=" + quantity + ", price=" + price);
        }
        return quantity * price;
    }

    public static void main(String[] args) {
        String[] items = { "Coffee", "Bagel", "Premium Gift Basket" };
        int[] quantities = { 3, 2, 1 };
        double[] prices = { 4.5, 2.25, 1250.0 };

        double total = 0.0;
        for (int i = 0; i < items.length; i++) {
            double subtotal = computeAndValidateSubtotal(items[i], quantities[i], prices[i]);
            total += subtotal;
            System.out.println(String.format("%-20s x%-3d $%,10.2f", items[i], quantities[i], subtotal));
        }
        System.out.println(String.format("%-24s $%,10.2f", "TOTAL:", total));
    }
}
```

**How to run:** `java ReceiptFormatAdvanced.java`

`%,10.2f` combines the grouping flag (`,`) with width (`10`) and precision (`.2f`) in one specifier — for the `1250.0` gift basket, this renders as `"  1,250.00"` (comma-grouped, right-aligned, two decimals), and for the final `total` line, any total exceeding a thousand dollars will display its own grouping separator too. `computeAndValidateSubtotal` runs *before* any formatting happens, ensuring bad data (a negative quantity or price) is caught and rejected as an explicit error, rather than being silently formatted into a nonsensical-looking but "successfully" printed negative subtotal.

## 6. Walkthrough

Trace the loop for `items[2] = "Premium Gift Basket"`, `quantities[2] = 1`, `prices[2] = 1250.0`:

**Validation.** `computeAndValidateSubtotal` checks `quantity < 0 || price < 0` — both are non-negative, so no exception is thrown. `subtotal = 1 * 1250.0 = 1250.0` is returned.

**Accumulation.** `total += 1250.0` adds this subtotal to the running total.

**Formatting the line.** `String.format("%-20s x%-3d $%,10.2f", "Premium Gift Basket", 1, 1250.0)` processes each specifier in order: `%-20s` renders `"Premium Gift Basket"` left-aligned in a 20-character field (the name itself is exactly 20 characters, so no padding is visibly added here); `x%-3d` renders the literal `"x"` followed by `1` left-aligned in 3 characters (`"1  "`); `$%,10.2f` renders `1250.0` with comma-grouping, right-aligned in 10 characters, 2 decimal places, producing `"  1,250.00"`.

```
subtotal = 1 * 1250.0 = 1250.0  (validated: quantity>=0, price>=0)
total += 1250.0
format: "%-20s x%-3d $%,10.2f" with ("Premium Gift Basket", 1, 1250.0)
  %-20s -> "Premium Gift Basket" (exactly 20 chars, no padding needed)
  x%-3d -> "x1  " (1 left-aligned in width 3)
  $%,10.2f -> "$  1,250.00" (comma-grouped, width 10, 2 decimals)
```

**Final output.** The three item lines print with aligned columns, the gift basket's price showing its comma-grouped `1,250.00`, and the final line prints `TOTAL:` followed by the comma-grouped grand total across all three items' subtotals, right-aligned to match the item rows above it.

## 7. Gotchas & takeaways

> **The number and types of arguments must match the format string's specifiers, or `String.format` throws at runtime, not compile time** — `String.format("%d", "not a number")` throws `IllegalFormatConversionException` immediately, since `%d` requires an integer type argument, not a `String`. There is no compile-time checking of format strings in standard Java.

> **`%d` is strictly for integer types (`int`, `long`, etc.) — using it with a `double` throws an exception; use `%f` (or `%.Nf` for N decimal places) for floating-point values.** Mixing these up is a very common source of `IllegalFormatConversionException` at runtime.

- `String.format(template, args...)` builds a string using `%`-prefixed specifiers, offering precise control over width, alignment, padding, and decimal precision that plain `+` concatenation can't provide.
- `%s` formats any object as a string; `%d` formats an integer; `%f`/`%.Nf` formats a floating-point number, optionally to N decimal places; `%,d`/`%,.Nf` adds thousands-grouping.
- Width and alignment flags (`%-15s`, `%8.2f`) are the standard way to produce neatly aligned, tabular text output.
- Format string errors (wrong argument count or type) surface only at runtime, so testing format strings with representative data matters more than it would for ordinary string concatenation.
