---
card: java
gi: 395
slug: formatted-output-printf-format
title: Formatted output printf/format
---

## 1. What it is

`System.out.printf(formatString, args...)` and the equivalent `String.format(formatString, args...)`, introduced in Java 5, build output according to a **format string** containing substitution specifiers like `%d` (integer), `%s` (string), `%f` (floating-point), and `%n` (platform-correct newline), substituting each specifier with the corresponding argument, formatted according to that specifier's rules. `printf` writes the result directly to standard output; `String.format` builds and returns the formatted string instead, for use anywhere a `String` is needed (logging, building a message, writing to a file).

## 2. Why & when

Building formatted output with plain string concatenation (`"Score: " + score + "/" + total`) works for simple cases, but gets unwieldy fast once you need specific numeric formatting — a fixed number of decimal places, zero-padding, right-aligned columns, thousands separators — none of which plain concatenation or `+` naturally expresses. Format strings, borrowed conceptually from C's `printf`, let you specify exactly how each value should be rendered directly in the specifier itself: `%.2f` means "as a floating-point number with exactly two decimal places," `%5d` means "as an integer, right-padded to at least five characters wide."

You reach for `printf`/`String.format` whenever output needs specific, controlled formatting — displaying currency (`%.2f`), aligning a table of numbers in columns (`%5d`, `%-10s`), or building a log message with several substituted values cleanly (`String.format("User %s logged in at %s", user, time)`). For simple, unformatted concatenation, plain `+` or `StringBuilder` remains simpler and perfectly adequate.

## 3. Core concept

```java
public class PrintfDemo {
    public static void main(String[] args) {
        String name = "Alice";
        double price = 19.5;
        int quantity = 3;

        System.out.printf("Item: %s, Price: $%.2f, Qty: %d%n", name, price, quantity);

        String message = String.format("Total: $%.2f", price * quantity); // returns a String instead of printing
        System.out.println(message);
    }
}
```

**How to run:** `java PrintfDemo.java`

`%s` substitutes `name` as a plain string; `%.2f` substitutes `price` as a floating-point number rounded to exactly two decimal places (`19.50`, note the trailing zero added); `%d` substitutes `quantity` as a plain integer; `%n` inserts a newline appropriate for the current platform (`\n` on Unix/macOS, `\r\n` on Windows). `String.format` uses identical specifier syntax but returns the formatted text as a `String` rather than printing it directly.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each percent-prefixed specifier in the format string is replaced in order by the corresponding argument, formatted according to that specifier's own rules">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">"Item: %s, Price: $%.2f, Qty: %d%n"  with args ("Alice", 19.5, 3)</text>

  <rect x="30" y="50" width="100" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="72" fill="#79c0ff" font-size="10" text-anchor="middle">%s -&gt; Alice</text>

  <rect x="150" y="50" width="130" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="215" y="72" fill="#79c0ff" font-size="10" text-anchor="middle">%.2f -&gt; 19.50</text>

  <rect x="300" y="50" width="90" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="345" y="72" fill="#79c0ff" font-size="10" text-anchor="middle">%d -&gt; 3</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Result: "Item: Alice, Price: $19.50, Qty: 3" -- specifiers matched to arguments strictly by position.</text>
</svg>

## 5. Runnable example

Scenario: printing a receipt, evolved from a version using plain concatenation with awkward, uncontrolled number formatting, through `printf` fixing the decimal formatting, to a version aligning a multi-item table using width and alignment specifiers for genuinely readable columnar output.

### Level 1 — Basic

```java
public class ReceiptConcatenation {
    public static void main(String[] args) {
        String item = "Coffee";
        double price = 3.5;
        int quantity = 2;
        double total = price * quantity;

        System.out.println(item + " x" + quantity + " = $" + total); // uncontrolled formatting
    }
}
```

**How to run:** `java ReceiptConcatenation.java`

Plain concatenation prints whatever `double`'s default `toString()` produces — here `7.0`, which happens to look fine, but for a value like `7.333333333333333` (from a non-round division), this same approach would print an ugly, unrounded, many-digit number with no control over it at all.

### Level 2 — Intermediate

```java
public class ReceiptPrintf {
    public static void main(String[] args) {
        String item = "Coffee";
        double price = 3.5;
        int quantity = 2;
        double total = price * quantity;

        System.out.printf("%s x%d = $%.2f%n", item, quantity, total); // controlled: always 2 decimal places
    }
}
```

**How to run:** `java ReceiptPrintf.java`

`%.2f` guarantees exactly two decimal places every time, regardless of what the underlying `double` value actually is — `$7.00` here, and it would correctly show `$7.33` (properly rounded) for a value like `7.333333333333333`, unlike Level 1's uncontrolled concatenation.

### Level 3 — Advanced

```java
import java.util.List;

public class ReceiptAlignedTable {
    record Item(String name, int quantity, double price) { }

    public static void main(String[] args) {
        List<Item> items = List.of(
                new Item("Coffee", 2, 3.5),
                new Item("Croissant", 1, 4.25),
                new Item("Orange Juice", 3, 2.75)
        );

        System.out.printf("%-15s %5s %8s%n", "Item", "Qty", "Total"); // header row, left/right-aligned columns
        double grandTotal = 0;
        for (Item item : items) {
            double lineTotal = item.quantity() * item.price();
            grandTotal += lineTotal;
            System.out.printf("%-15s %5d %8.2f%n", item.name(), item.quantity(), lineTotal);
        }
        System.out.printf("%-15s %5s %8.2f%n", "", "", grandTotal); // total row, aligned with the columns above
    }
}
```

**How to run:** `java ReceiptAlignedTable.java`

`%-15s` left-aligns a string within a 15-character-wide field (the `-` means left-align; without it, `%15s` would right-align instead); `%5d` right-aligns an integer within a 5-character field; `%8.2f` right-aligns a floating-point number, rounded to two decimals, within an 8-character field. Applying the exact same width specifiers to every row (header, each item, and the total) produces genuinely aligned columns, regardless of how long each item's name happens to be.

## 6. Walkthrough

Execution starts in `main`. The header row prints first: `%-15s` applied to `"Item"` pads it with trailing spaces to fill 15 characters (left-aligned), `%5s` applied to `"Qty"` pads it with leading spaces to fill 5 characters (right-aligned, the default for `%s` without a `-`), `%8s` applied to `"Total"` similarly right-pads... right-aligns within 8 characters.

The loop then processes each `Item`. For the first, `Coffee`, quantity `2`, price `3.5`: `lineTotal = 2 * 3.5 = 7.0`. `grandTotal` becomes `7.0`. `printf("%-15s %5d %8.2f%n", "Coffee", 2, 7.0)` renders `"Coffee"` left-aligned in 15 characters, `2` right-aligned in 5 characters, and `7.0` as `7.00` right-aligned in 8 characters.

For the second, `Croissant`, quantity `1`, price `4.25`: `lineTotal = 1 * 4.25 = 4.25`. `grandTotal` becomes `7.0 + 4.25 = 11.25`. The row prints `"Croissant"` (a longer name, but still fits within and is padded to 15 characters, keeping the `Qty`/`Total` columns aligned with the row above), `1`, and `4.25` formatted as `4.25`.

For the third, `Orange Juice`, quantity `3`, price `2.75`: `lineTotal = 3 * 2.75 = 8.25`. `grandTotal` becomes `11.25 + 8.25 = 19.5`.

Finally, the total row prints with empty strings for the item name and quantity columns (kept only to preserve alignment) and `grandTotal` (`19.5`) formatted as `19.50` in the `Total` column, lined up exactly under the individual line totals above it.

Expected output:
```
Item                  Qty    Total
Coffee                  2     7.00
Croissant               1     4.25
Orange Juice            3     8.25
                             19.50
```

## 7. Gotchas & takeaways

> `%n` (a platform-correct newline) and `\n` (always a literal Unix-style newline) are not the same thing — in a `printf`/`String.format` format string, always prefer `%n` for portability, since it correctly produces `\r\n` on Windows and `\n` elsewhere, matching what the underlying platform actually expects.

- Format specifiers (`%s`, `%d`, `%f`, and others) must match their arguments' types and be supplied in the same order they appear in the format string — a mismatch (like `%d` given a `String` argument) throws `IllegalFormatConversionException` at runtime.
- `%.Nf` controls the number of decimal places for floating-point values; `%Nd`/`%Ns` control minimum field width (right-aligned by default; add `-` for left-aligned, as in `%-15s`).
- `printf` writes formatted output directly to a stream (typically standard output); `String.format` builds and returns the same formatted text as a `String`, useful for logging, building messages, or writing to a file.
- Applying the exact same width specifiers to a header row and every subsequent data row is the standard way to produce genuinely aligned columnar text output.
- Always use `%n` rather than a literal `\n` inside a format string intended to be portable across operating systems.
