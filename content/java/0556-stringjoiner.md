---
card: java
gi: 556
slug: stringjoiner
title: StringJoiner
---

## 1. What it is

`StringJoiner` (in `java.util`) builds a single string out of many pieces, placing a **delimiter** between each piece and, optionally, a **prefix** before the first piece and a **suffix** after the last one. It exists so you never have to hand-write the classic "add a comma except after the last item" loop again.

## 2. Why & when

Concatenating a list into `"a, b, c"` sounds trivial until you write it by hand: you either check `if (i > 0) sb.append(", ")` inside the loop, or you append a trailing delimiter and then trim it off afterward. Both are easy to get subtly wrong (off-by-one, forgetting the empty-list case). `StringJoiner` handles all of that internally, and it also handles the common case of wrapping the whole thing in brackets, like `[a, b, c]`, without extra code. Reach for it whenever you're manually building a delimited string with a loop — and know that `Collectors.joining()` (covered earlier) is built directly on top of `StringJoiner` for use with streams.

## 3. Core concept

```java
StringJoiner sj = new StringJoiner(", ", "[", "]");
sj.add("a").add("b").add("c");
System.out.println(sj); // [a, b, c]

StringJoiner empty = new StringJoiner(", ", "[", "]");
System.out.println(empty); // []  (no add() calls -> just prefix+suffix)
```

`new StringJoiner(delimiter)` is the simple form; `new StringJoiner(delimiter, prefix, suffix)` adds bracketing. `add(...)` returns the `StringJoiner` itself, so calls chain. An empty joiner (nothing added) still prints prefix+suffix unless you call `setEmptyValue(...)` to override that.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StringJoiner assembles prefix, elements separated by delimiter, and suffix">
  <rect x="8" y="10" width="624" height="60" rx="8" fill="#0d1117"/>
  <text x="20" y="35" fill="#8b949e" font-size="11" font-family="sans-serif">add("a") -&gt; add("b") -&gt; add("c")</text>
  <text x="20" y="55" fill="#e6edf3" font-size="12" font-family="monospace">internal buffer: a , b , c</text>

  <rect x="8" y="90" width="624" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="20" y="120" fill="#6db33f" font-size="14" font-family="monospace">[</text>
  <text x="35" y="120" fill="#e6edf3" font-size="14" font-family="monospace">a, b, c</text>
  <text x="130" y="120" fill="#6db33f" font-size="14" font-family="monospace">]</text>
  <text x="180" y="120" fill="#8b949e" font-size="11" font-family="sans-serif">&lt;- prefix and suffix wrap the joined result</text>
</svg>

Prefix and suffix wrap the whole joined string; the delimiter appears only between elements, never at the ends.

## 5. Runnable example

Scenario: rendering a shopping cart's item list as a human-readable string — starting with a plain comma list, then adding bracket formatting and an empty-cart message, then building a reusable summary line that mixes a `StringJoiner` with running totals.

### Level 1 — Basic

```java
import java.util.StringJoiner;

public class CartBasic {
    public static void main(String[] args) {
        StringJoiner items = new StringJoiner(", ");
        items.add("Apples").add("Bread").add("Milk");
        System.out.println("Cart: " + items);
    }
}
```

**How to run:** `java CartBasic.java`

Expected output:
```
Cart: Apples, Bread, Milk
```

`new StringJoiner(", ")` creates a joiner with only a delimiter. Each `add(...)` appends one item and, from the second call onward, a leading `", "` separator is inserted automatically. Printing the joiner (via `toString()`, called implicitly by string concatenation) yields the fully assembled string — no manual comma bookkeeping was needed.

### Level 2 — Intermediate

```java
import java.util.StringJoiner;
import java.util.List;

public class CartFormatted {
    static String renderCart(List<String> itemNames) {
        StringJoiner sj = new StringJoiner(", ", "[", "]");
        sj.setEmptyValue("(cart is empty)");
        for (String name : itemNames) {
            sj.add(name);
        }
        return sj.toString();
    }

    public static void main(String[] args) {
        System.out.println(renderCart(List.of("Apples", "Bread", "Milk")));
        System.out.println(renderCart(List.of()));
    }
}
```

**How to run:** `java CartFormatted.java`

Expected output:
```
[Apples, Bread, Milk]
(cart is empty)
```

`setEmptyValue(...)` replaces the *entire* output (not just the inner content) whenever zero elements were added, so the second call prints `(cart is empty)` with no brackets at all — the brackets only surround real content. This version adds two real-world concerns over Level 1: bracket formatting via the three-argument constructor, and a graceful empty-cart message via `setEmptyValue(...)`, which avoids printing a bare, confusing `[]` to the user.

### Level 3 — Advanced

```java
import java.util.StringJoiner;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;

public class CartSummary {
    record LineItem(String name, int quantity, double unitPrice) {}

    static String summarize(List<LineItem> lines) {
        StringJoiner sj = new StringJoiner("; ", "Receipt[", "]");
        sj.setEmptyValue("Receipt[empty]");
        double total = 0.0;

        for (LineItem line : lines) {
            double subtotal = line.quantity() * line.unitPrice();
            total += subtotal;
            sj.add(String.format("%s x%d = $%.2f", line.name(), line.quantity(), subtotal));
        }

        String body = sj.toString();
        return body.equals("Receipt[empty]") ? body : body + String.format(" Total: $%.2f", total);
    }

    public static void main(String[] args) {
        List<LineItem> cart = List.of(
            new LineItem("Apples", 3, 0.50),
            new LineItem("Bread", 1, 2.75),
            new LineItem("Milk", 2, 1.20)
        );
        System.out.println(summarize(cart));
        System.out.println(summarize(List.of()));
    }
}
```

**How to run:** `java CartSummary.java`

Expected output:
```
Receipt[Apples x3 = $1.50; Bread x1 = $2.75; Milk x2 = $2.40] Total: $6.65
Receipt[empty]
```

This combines `StringJoiner` with an accumulator variable (`total`) computed alongside each `add(...)` call — a pattern real receipt-printing or logging code uses constantly: build a formatted list *and* a running aggregate in a single pass, then decide how to present the aggregate based on whether the collection was empty.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `cart` is a `List<LineItem>` with three records: Apples (3 @ $0.50), Bread (1 @ $2.75), Milk (2 @ $1.20).

`summarize(cart)` is called. Inside, `sj` is created with delimiter `"; "`, prefix `"Receipt["`, suffix `"]"`, and an empty-value override of `"Receipt[empty]"`. `total` starts at `0.0`.

The loop processes each `LineItem` in order:

```
line=Apples, qty=3, price=0.50 -> subtotal=1.50 -> total=1.50 -> sj.add("Apples x3 = $1.50")
line=Bread,  qty=1, price=2.75 -> subtotal=2.75 -> total=4.25 -> sj.add("Bread x1 = $2.75")
line=Milk,   qty=2, price=1.20 -> subtotal=2.40 -> total=6.65 -> sj.add("Milk x2 = $2.40")
```

Each `sj.add(...)` call internally appends the delimiter (except before the very first element) followed by the formatted string, so after the loop the joiner's internal state, once rendered, is `Receipt[Apples x3 = $1.50; Bread x1 = $2.75; Milk x2 = $2.40]`.

`body = sj.toString()` captures that string. Since `body` does not equal the empty-value sentinel `"Receipt[empty]"`, the method appends `" Total: $6.65"` (formatted from `total`) and returns the combined string.

`main` prints the result: `Receipt[Apples x3 = $1.50; Bread x1 = $2.75; Milk x2 = $2.40] Total: $6.65`.

The second call, `summarize(List.of())`, never enters the loop (empty list), so `sj.toString()` returns exactly `"Receipt[empty]"` (the `setEmptyValue` override, not `"Receipt[]"`). Since `body.equals("Receipt[empty]")` is `true`, the method short-circuits and returns `body` unchanged — no `" Total: $0.00"` is appended, avoiding a nonsensical total on an empty receipt.

## 7. Gotchas & takeaways

> `setEmptyValue(...)` replaces the **entire** output, prefix and suffix included, not just the space between them. If you call `sj.setEmptyValue("none")` on a joiner with prefix `"["` and suffix `"]"`, an empty joiner prints `none`, not `[none]`. Forgetting this leads to code that checks `result.equals("[]")` to detect emptiness and silently never matches once `setEmptyValue` is introduced.

- `StringJoiner(delimiter)` handles plain delimited lists; `StringJoiner(delimiter, prefix, suffix)` adds bracket-style wrapping in one step.
- `add(...)` returns `this`, so calls chain: `sj.add("a").add("b")`.
- Without `setEmptyValue`, an empty joiner still prints prefix+suffix (e.g., `[]`) — decide whether that's the message you want before shipping.
- `Collectors.joining(...)` used with streams is implemented on top of `StringJoiner` internally, so the same delimiter/prefix/suffix vocabulary applies to both.
- `merge(otherStringJoiner)` combines two joiners' contents (using the receiver's delimiter), useful for combining partial results built in different code paths.
