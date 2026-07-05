---
card: java
gi: 103
slug: addition-and-string-concatenation
title: Addition + (and String concatenation)
---

## 1. What it is

Java overloads the `+` operator for two purposes: numeric addition (`3 + 4` is `7`) and `String` concatenation (`"a" + "b"` is `"ab"`). The compiler decides which meaning applies based on the operand types: if either operand of `+` is a `String`, the operator performs concatenation and the other operand is automatically converted to its `String` form (via `String.valueOf`); otherwise, `+` performs numeric addition with the usual binary numeric promotion.

```java
int a = 2, b = 3;
System.out.println(a + b);          // 5 — both int, numeric addition
System.out.println("" + a + b);     // "23" — String on the left forces concatenation
System.out.println(a + b + "");     // "5" — numeric addition happens first, then concatenation
```

The last two lines look similar but produce very different results because `+` is left-associative: Java evaluates strictly left to right, and once a `String` appears, every `+` after it becomes concatenation — but any `+` *before* the first `String` operand is still numeric.

## 2. Why & when

This dual meaning of `+` is used constantly, and its interaction with left-associativity is one of the most common sources of subtle bugs:

- Building human-readable messages: `"Total: " + total` — clean, but only correct if the numeric parts have already been added.
- Debug/log lines: `"x=" + x + ", y=" + y` relies on `String` appearing early so every subsequent `+` concatenates.
- Off-by-meaning bugs: `System.out.println("Sum: " + a + b)` where the author *intended* `a + b` to be computed first, but Java concatenates `"Sum: "` with `a` first, then with `b`, producing `"Sum: 23"` instead of `"Sum: 5"`.

You need to be careful when:
- Mixing arithmetic and string building in the same expression — parenthesize the arithmetic explicitly: `"Sum: " + (a + b)`.
- Concatenating in a loop — each `+` on `String` objects allocates a new `String` (`String` is immutable), which is fine occasionally but wasteful in a hot loop; use `StringBuilder` there instead.

## 3. Core concept

```java
public class PlusOperatorDemo {
    public static void main(String[] args) {
        int a = 2, b = 3;

        // Pure numeric addition — no String operand
        System.out.println(a + b);              // 5

        // String first — every subsequent + concatenates
        System.out.println("" + a + b);          // "23"

        // Numeric first — addition happens before the String appears
        System.out.println(a + b + "");           // "5"

        // Parentheses force the intended grouping regardless of position
        System.out.println("Sum: " + (a + b));    // "Sum: 5"
        System.out.println("Sum: " + a + b);       // "Sum: 23"  (classic bug)

        // Mixed types: char + int is numeric (char promotes to int)
        char c = 'A';
        System.out.println(c + 1);                 // 66 (numeric: 'A' code point 65 + 1)
        System.out.println("" + c + 1);             // "A1" (String concatenation)

        // null is allowed on the String side of +
        String s = null;
        System.out.println("value: " + s);          // "value: null"
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Left to right evaluation of plus operator: quote plus a plus b evaluates the empty string plus a first giving string two, then concatenates b giving two three. a plus b plus quote evaluates a plus b first as numeric five, then concatenates the empty string giving string five.">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ is left-associative — evaluated strictly left to right</text>

  <text x="20" y="48" fill="#e6edf3" font-size="9" font-family="monospace">"" + a + b</text>
  <rect x="20" y="56" width="150" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">"" + a = "2"</text>
  <text x="185" y="73" fill="#8b949e" font-size="12" text-anchor="middle">→</text>
  <rect x="200" y="56" width="170" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="285" y="73" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">"2" + b = "23"</text>
  <text x="400" y="73" fill="#8b949e" font-size="9" font-family="sans-serif">← String, concatenation from here on</text>

  <text x="20" y="118" fill="#e6edf3" font-size="9" font-family="monospace">a + b + ""</text>
  <rect x="20" y="126" width="150" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="143" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">a + b = 5</text>
  <text x="185" y="143" fill="#8b949e" font-size="12" text-anchor="middle">→</text>
  <rect x="200" y="126" width="170" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="285" y="143" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">5 + "" = "5"</text>
  <text x="400" y="143" fill="#8b949e" font-size="9" font-family="sans-serif">← still numeric until "" appears</text>

  <text x="350" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Same operands, same operator — different order of the String operand gives a different result</text>
</svg>

`+` chains left to right; whichever operand introduces a `String` first switches every subsequent `+` in that chain to concatenation.

## 5. Runnable example

Scenario: a receipt-line formatter that builds a display string from item name, quantity, and unit price — a natural place for the concatenation-vs-addition ambiguity to bite.

### Level 1 — Basic

```java
public class ReceiptBasic {
    public static void main(String[] args) {
        String item = "Widget";
        int quantity = 3;
        double unitPrice = 2.50;

        // Straightforward concatenation: String first, so everything after is stringified
        String line = "Item: " + item + ", Qty: " + quantity + ", Price: " + unitPrice;
        System.out.println(line);

        // A subtotal computed and appended
        double subtotal = quantity * unitPrice;
        System.out.println("Subtotal: " + subtotal);
    }
}
```

**How to run:** `java ReceiptBasic.java`

`"Item: " + item` starts the chain with a `String` operand, so every `+` after it concatenates: `quantity` (an `int`) and `unitPrice` (a `double`) are each converted to their `String` form via `String.valueOf` and appended. `quantity * unitPrice` is computed first (pure numeric multiplication, no `String` involved), giving `7.5`, which is then concatenated onto `"Subtotal: "`.

### Level 2 — Intermediate

Same receipt formatter, now computing a running total across multiple lines — a place where the "numeric first, then concatenate" ordering must be handled correctly, and where the classic bug (`"Total: " + a + b` instead of `"Total: " + (a + b)`) is deliberately shown and fixed.

```java
public class ReceiptIntermediate {

    record LineItem(String name, int quantity, double unitPrice) {
        double subtotal() { return quantity * unitPrice; }
    }

    public static void main(String[] args) {
        LineItem[] items = {
            new LineItem("Widget", 3, 2.50),
            new LineItem("Gadget", 1, 9.99),
            new LineItem("Gizmo", 2, 4.25)
        };

        double total = 0.0;
        for (LineItem li : items) {
            double sub = li.subtotal();
            total += sub;
            System.out.println(li.name() + " x" + li.quantity() + " = $" + sub);
        }

        // BUGGY version: numbers land after a String too late — but here total is already numeric
        // so this specific case still works. The real danger is shown below.
        System.out.println("Total: $" + total);

        // Demonstrate the classic bug directly with two raw numbers
        int discountPercent = 10, itemsCount = 5;
        System.out.println("BUGGY: " + discountPercent + itemsCount);        // "105" not 15
        System.out.println("FIXED: " + (discountPercent + itemsCount));       // "15"
    }
}
```

**How to run:** `java ReceiptIntermediate.java`

Each line's `sub = li.subtotal()` is computed as pure numeric multiplication *before* any `String` is involved, so concatenating it afterward is safe — the danger only arises when raw operands are concatenated in sequence without parentheses forcing the arithmetic first. The `"BUGGY"` line shows the trap directly: `"BUGGY: " + discountPercent + itemsCount` concatenates `"BUGGY: "` with `10` (giving `"BUGGY: 10"`), then concatenates that with `5` (giving `"BUGGY: 105"`) — the two numbers are stuck together as digits instead of summed. Wrapping the arithmetic in parentheses, `(discountPercent + itemsCount)`, forces it to evaluate as `15` before any concatenation touches it.

### Level 3 — Advanced

Same receipt system, now building a multi-line receipt efficiently with `StringBuilder` (avoiding repeated immutable `String` allocation in a loop), and formatting numbers explicitly with `String.format` instead of relying on default `+`-driven `String.valueOf` conversions (which do not control decimal places or locale).

```java
import java.util.*;

public class ReceiptAdvanced {

    record LineItem(String name, int quantity, double unitPrice) {
        double subtotal() { return quantity * unitPrice; }
    }

    static String formatReceipt(List<LineItem> items) {
        // StringBuilder avoids allocating a new String object on every append in the loop
        StringBuilder sb = new StringBuilder();
        sb.append("=== Receipt ===\n");

        double total = 0.0;
        for (LineItem li : items) {
            double sub = li.subtotal();
            total += sub;
            // String.format avoids the "+"-driven default toString, giving controlled precision
            sb.append(String.format("%-10s x%-3d $%6.2f%n", li.name(), li.quantity(), sub));
        }

        sb.append("---------------\n");
        sb.append(String.format("Total:        $%6.2f%n", total));
        return sb.toString();
    }

    public static void main(String[] args) {
        List<LineItem> items = List.of(
            new LineItem("Widget", 3, 2.50),
            new LineItem("Gadget", 1, 9.99),
            new LineItem("Gizmo", 2, 4.25)
        );

        System.out.print(formatReceipt(items));

        // Show why + in a loop is costly: each concatenation would allocate a new String
        int n = 5;
        String naive = "";
        for (int i = 0; i < n; i++) {
            naive = naive + i + ",";   // allocates a new String object every iteration
        }
        System.out.println("Naive loop result: " + naive);
    }
}
```

**How to run:** `java ReceiptAdvanced.java`

`StringBuilder.append` mutates an internal, resizable character buffer in place, so building a multi-line receipt allocates far fewer objects than repeated `String` `+` concatenation would, which matters once the loop runs many times (a compiler *may* optimize a single chained `+` expression into a `StringBuilder` automatically, but a `+=` inside a loop generally cannot be optimized this way because a new `StringBuilder` is implicitly created on every iteration). `String.format("%6.2f", sub)` explicitly controls the number of decimal places, unlike relying on `+` to call `Double.toString`, which does not let you specify precision. The final naive loop is left in to make the cost concrete: each `naive + i + ","` allocates a new immutable `String` holding the whole growing text, copying all previous characters — `StringBuilder` avoids that repeated copying.

## 6. Walkthrough

Trace `formatReceipt(items)` for the three-item list:

**Header.** `sb.append("=== Receipt ===\n")` writes the header directly into the buffer; no `+` concatenation is involved here at all.

**First item ("Widget", 3, 2.50).** `li.subtotal()` computes `3 * 2.50 = 7.5` (numeric multiplication, `int * double` promotes to `double`). `total` becomes `7.5`. `String.format("%-10s x%-3d $%6.2f%n", "Widget", 3, 7.5)` produces the line `"Widget     x3   $  7.50\n"`, which is appended to the buffer.

**Second item ("Gadget", 1, 9.99).** Subtotal `9.99`, `total` becomes `17.49`. A similarly formatted line is appended.

**Third item ("Gizmo", 2, 4.25).** Subtotal `8.5`, `total` becomes `25.99`. Appended.

**Footer.** `String.format("Total:        $%6.2f%n", 25.99)` appends the final total line.

**`sb.toString()`** converts the internal character buffer into one immutable `String`, which `main` prints with `System.out.print`.

```
StringBuilder buffer (grows in place):
"=== Receipt ===\n"
+ "Widget     x3   $  7.50\n"
+ "Gadget     x1   $  9.99\n"
+ "Gizmo      x2   $  8.50\n"
+ "---------------\n"
+ "Total:        $ 25.99\n"
= one final String returned by toString()
```

**The naive loop, for contrast.** At `i=0`, `naive = "" + 0 + "," = "0,"` (a new `String` object). At `i=1`, `naive = "0," + 1 + "," = "0,1,"` (another new `String`, copying the previous 2 characters plus the new ones). Each iteration re-copies everything accumulated so far into a brand-new `String` — this is the quadratic-cost pattern that `StringBuilder.append` avoids by growing one shared buffer instead.

## 7. Gotchas & takeaways

> **Once a `String` operand appears in a left-to-right `+` chain, every `+` after it concatenates — but any `+` before it is still numeric if all its operands are numeric.** `"Sum: " + a + b` is the classic bug: it concatenates `a`'s digits and `b`'s digits instead of adding them. Fix with parentheses: `"Sum: " + (a + b)`.

> **`+=` inside a `String`-building loop reallocates on every iteration.** Each `String` is immutable, so `naive = naive + x` creates an entirely new `String`, copying all prior characters. Use `StringBuilder` for loops that build up text incrementally.

- `+` means numeric addition unless at least one operand is a `String`, in which case it means concatenation and the other operand is converted with `String.valueOf`.
- Left-associativity means the *position* of the first `String` operand in the expression determines where concatenation starts.
- Parenthesize arithmetic that must happen before concatenation: `"Total: " + (a + b)`, not `"Total: " + a + b`.
- Prefer `StringBuilder` (or `String.join`/`String.format` for one-shot formatting) over chained `+` inside loops.
