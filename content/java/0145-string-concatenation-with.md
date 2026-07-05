---
card: java
gi: 145
slug: string-concatenation-with
title: String concatenation with +
---

## 1. What it is

Java overloads the `+` operator for `String`s: when either operand of `+` is a `String`, the operator performs **concatenation** — joining the text of both operands into a brand-new `String` — instead of arithmetic addition. If the other operand isn't already a `String` (an `int`, a `boolean`, an object), Java automatically converts it to its string representation first.

```java
String greeting = "Hello, " + "world" + "!";  // "Hello, world!"
String withNumber = "Count: " + 42;            // "Count: 42" — 42 is converted to "42"
int a = 3, b = 4;
System.out.println("Sum: " + a + b);           // "Sum: 34" — NOT "Sum: 7"! (see part 7)
```

Because `+` is evaluated **left to right**, `"Sum: " + a + b` first concatenates `"Sum: "` with `a` (producing `"Sum: 3"`, a string), and *that* result is then concatenated with `b` — at that point `+` is already working on strings, so it never goes back to being addition.

## 2. Why & when

String concatenation with `+` is the simplest way to build a string out of pieces, and is appropriate for:

- **Small, one-off string building** — a handful of `+` operations to assemble a message, label, or log line.
- **Readability for simple cases** — `"Hello, " + name + "!"` reads naturally and needs no extra machinery.
- **Mixing literal text and values** — automatically converting numbers, booleans, and objects (via their `toString()`) into text inline.

For **building strings inside a loop**, repeated `+` is a performance trap: each `+` creates an entirely new `String` object (recall immutability), so concatenating in a loop `n` times creates roughly `n` discarded intermediate strings — for that pattern, `StringBuilder` (covered separately) is the correct tool, since it can append into one mutable buffer without creating a new object every time.

## 3. Core concept

```java
public class ConcatDemo {
    public static void main(String[] args) {
        String name = "Alice";
        int age = 30;
        boolean active = true;

        String message = "Name: " + name + ", Age: " + age + ", Active: " + active;
        System.out.println(message);
        // "Name: Alice, Age: 30, Active: true"

        // Mixing + as addition vs. concatenation depends on operand types and order
        System.out.println(1 + 2 + "3");   // "33"  — 1+2=3 (int addition) first, THEN + "3" concatenates
        System.out.println("1" + 2 + 3);   // "123" — "1"+2="12" (concat) first, then +3 concatenates again
    }
}
```

`1 + 2 + "3"` and `"1" + 2 + 3` look similar but behave differently, purely because of where the first `String` appears in the left-to-right chain — everything to its left that's already been combined into a number stays numeric addition; everything from that point onward becomes concatenation.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Concatenation evaluation order diagram: the expression 1 + 2 + three-quote is evaluated left to right, first computing 1 plus 2 as integer addition giving 3, then concatenating that 3 with the string three to give the final string 33.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 + 2 + "3"  — evaluated strictly LEFT TO RIGHT</text>

  <rect x="40" y="45" width="90" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="64" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">1 + 2</text>
  <text x="85" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">int + int = int ADDITION</text>

  <path d="M 130 59 L 190 59" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="190" y="45" width="60" height="28" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="220" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">3</text>

  <path d="M 250 59 L 310 59" stroke="#6db33f" stroke-width="2" marker-end="url(#b)"/>
  <text x="280" y="49" fill="#6db33f" font-size="8" font-family="sans-serif">+ "3"</text>

  <rect x="310" y="45" width="120" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="370" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"3" + "3"</text>
  <text x="370" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">int becomes string, then CONCATENATION</text>

  <path d="M 430 59 L 490 59" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="490" y="45" width="80" height="28" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-width="2"/>
  <text x="530" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"33"</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Once a String enters the chain, every "+" after it is concatenation, not addition —</text>
  <text x="350" y="145" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">but everything strictly BEFORE the first String is still ordinary arithmetic.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`+` chains resolve strictly left to right; the operand types at each step decide addition vs. concatenation independently.

## 5. Runnable example

Scenario: building a formatted receipt line for a shopping cart item — starting with basic concatenation of a few pieces, then adding numeric fields where operand order actually matters, then hardening it into a loop-safe building process that avoids the repeated-`+` performance trap for a full multi-item receipt.

### Level 1 — Basic

```java
public class ReceiptBasic {
    public static void main(String[] args) {
        String item = "Coffee";
        double price = 4.50;

        String line = item + ": $" + price;
        System.out.println(line);
    }
}
```

**How to run:** `java ReceiptBasic.java`

`item + ": $" + price` concatenates left to right: `item` (a `String`) forces the very first `+` to be concatenation, so every subsequent `+` in the expression is concatenation too, including `price` (a `double`), which is automatically converted to its string form (`"4.5"`). Output: `"Coffee: $4.5"`.

### Level 2 — Intermediate

Same receipt line, now including a **quantity and computed subtotal**, where getting the operand order right actually matters — computing the subtotal as a genuine multiplication *before* it touches any string.

```java
public class ReceiptIntermediate {
    public static void main(String[] args) {
        String item = "Coffee";
        int quantity = 3;
        double unitPrice = 4.50;

        double subtotal = quantity * unitPrice;         // pure numeric multiplication first
        String line = item + " x" + quantity + ": $" + subtotal; // THEN build the string
        System.out.println(line);
    }
}
```

**How to run:** `java ReceiptIntermediate.java`

`subtotal` is computed as `quantity * unitPrice` entirely in numeric form (`3 * 4.50 = 13.5`) *before* any concatenation happens — this avoids the classic mistake of accidentally writing something like `item + " x" + quantity * unitPrice` and getting confused about operator precedence between `+` and `*`. Once `subtotal` is a finished number, it's concatenated into `line` just like any other value.

### Level 3 — Advanced

Same receipt, now building a **multi-item receipt** where the correct tool for repeated concatenation is `StringBuilder`, not chained `+` — because looping with `+` would create and discard a new intermediate `String` on every single iteration, which is wasteful for anything beyond a handful of items.

```java
public class ReceiptAdvanced {
    public static void main(String[] args) {
        String[] items = { "Coffee", "Bagel", "Juice" };
        int[] quantities = { 3, 2, 1 };
        double[] unitPrices = { 4.50, 2.25, 3.00 };

        StringBuilder receipt = new StringBuilder(); // mutable buffer — no new object created per append
        double total = 0.0;

        for (int i = 0; i < items.length; i++) {
            double subtotal = quantities[i] * unitPrices[i];
            total += subtotal;
            receipt.append(items[i]).append(" x").append(quantities[i])
                   .append(": $").append(subtotal).append("\n");
        }
        receipt.append("Total: $").append(total);

        System.out.println(receipt.toString());
    }
}
```

**How to run:** `java ReceiptAdvanced.java`

Inside the loop, `receipt.append(...)` mutates the *same* `StringBuilder` object in place on every call, rather than creating a new `String` each time the way `receipt = receipt + items[i] + ...` would — this is exactly the fix the "Why & when" section pointed to. `+` is still used for the arithmetic (`quantities[i] * unitPrices[i]`, `total += subtotal`), since those really are numeric operations, not string building.

## 6. Walkthrough

Trace the loop for `i = 0` (`item = "Coffee"`, `quantity = 3`, `unitPrice = 4.50`):

**Numeric computation.** `subtotal = quantities[0] * unitPrices[0]` = `3 * 4.50` = `13.5` — pure `int * double` arithmetic, no strings involved yet. `total` accumulates: `total += 13.5` makes `total = 13.5`.

**Building the line.** `receipt.append(items[0])` appends `"Coffee"` into the buffer. `.append(" x")` appends the literal text. `.append(quantities[0])` appends the `int` `3`, which `StringBuilder.append` automatically converts to `"3"` internally (an overload exists for `int`, just as `+` has automatic conversion for concatenation). `.append(": $")` and `.append(subtotal)` (which converts `13.5` to `"13.5"`) follow the same pattern, then `.append("\n")` adds a newline.

```
i=0: subtotal = 3 * 4.50 = 13.5      total = 13.5
     buffer so far: "Coffee x3: $13.5\n"
i=1: subtotal = 2 * 2.25 = 4.5       total = 18.0
     buffer so far: "Coffee x3: $13.5\nBagel x2: $4.5\n"
i=2: subtotal = 1 * 3.00 = 3.0       total = 21.0
     buffer so far: "Coffee x3: $13.5\nBagel x2: $4.5\nJuice x1: $3.0\n"
```

**After the loop.** `receipt.append("Total: $").append(total)` appends the final summary line using the fully accumulated `total` (`21.0`).

**Final output.** `receipt.toString()` converts the whole buffer into one final `String`, and `println` prints the four lines: the three item lines followed by `"Total: $21.0"`.

## 7. Gotchas & takeaways

> **`+` resolves strictly left to right, and only becomes concatenation once a `String` operand actually appears in the chain — everything purely numeric before that point stays numeric addition.** `1 + 2 + "3"` prints `"33"` (numeric `1+2=3` first, then concatenated with `"3"`), while `"1" + 2 + 3` prints `"123"` (string from the very first `+` onward). Always double-check where the first `String` sits in a mixed chain.

> **Repeated `+` concatenation inside a loop creates a new discarded `String` object on every iteration** — for anything beyond a handful of concatenations, especially inside a loop, use `StringBuilder.append(...)` instead, which mutates one buffer in place.

- `+` performs string concatenation whenever either operand is a `String`; non-`String` operands are automatically converted to their text form.
- Evaluation is strictly left to right — parenthesize explicitly (`"Sum: " + (a + b)`) if you want the numeric addition to happen before concatenation.
- For simple, small, one-off string building, `+` is perfectly fine and more readable than `StringBuilder`.
- For building strings across many iterations of a loop, prefer `StringBuilder.append(...)` to avoid creating and discarding a new `String` object on every pass.
