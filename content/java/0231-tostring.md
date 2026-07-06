---
card: java
gi: 231
slug: tostring
title: toString()
---

## 1. What it is

`toString()` is a method every class inherits from `Object` (the previous topic) whose job is to return a `String` representation of an object. `Object`'s own default implementation returns the class name plus `@` plus the object's hash code in hexadecimal — technically valid, but rarely useful — so classes routinely override `toString()` to return something meaningful for their own data.

```java
class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public String toString() {
        return "Point(" + x + ", " + y + ")";
    }
}

public class ToStringDemo {
    public static void main(String[] args) {
        Point p = new Point(3, 4);
        System.out.println(p);          // calls p.toString() automatically
        System.out.println(p.toString()); // same result, called explicitly
    }
}
```

`System.out.println(p)` does not print the object's memory layout; it calls `p.toString()` automatically and prints whatever `String` comes back — since `Point` overrides `toString()`, both lines print `"Point(3, 4)"` instead of `Object`'s default class-name-and-hash format.

## 2. Why & when

Overriding `toString()` is one of the most common and highest-value overrides you will write, because Java calls it implicitly in many places.

- **Automatic calls in string contexts** — `System.out.println(obj)`, string concatenation (`"Value: " + obj`), and `String.valueOf(obj)` all call `toString()` behind the scenes; without an override, every one of these produces the unhelpful default format.
- **Debugging and logging** — a well-written `toString()` turns a debugger watch window or a log line from a useless hash-based identifier into an immediately readable summary of the object's actual state, which is often the single biggest win for developer productivity on any custom class.
- **Building larger strings** — collections like `ArrayList` call `toString()` on every element when the collection itself is printed, so overriding it on your element type improves how entire collections of your objects display, not just single instances.

Override `toString()` on essentially every class whose instances might end up in a log message, an exception message, a debugger, or printed output — the main exceptions are classes with sensitive data (like passwords) where a deliberately vague or redacted `toString()`, or none at all, is safer.

## 3. Core concept

```java
class Money {
    private final long cents;
    Money(long cents) { this.cents = cents; }

    @Override
    public String toString() {
        return String.format("$%d.%02d", cents / 100, cents % 100);
    }
}
```

`toString()` must return a `String` and take no arguments — that exact signature (`public String toString()`) is what `Object` declares, and any override must match it precisely; here, `Money`'s override formats cents into a familiar dollars-and-cents display, so printing a `Money` value never leaks its raw internal representation.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="println calls toString implicitly, which resolves via dynamic dispatch to either Objects default hash based format or a classs own override">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">System.out.println(obj)</text>

  <line x1="140" y1="55" x2="140" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls obj.toString()</text>

  <rect x="30" y="85" width="220" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="140" y="107" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">no override -&gt; Object default</text>

  <rect x="330" y="85" width="240" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="107" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">overridden -&gt; class's own format</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Whichever toString() the runtime type provides is what println actually prints.</text>
</svg>

`println` always calls `toString()`; whether that resolves to `Object`'s default or a custom override depends on the actual runtime type.

## 5. Runnable example

Scenario: a small `Product` class used in a shop's receipt printing, evolved from a plain override into one that composes nested objects and finally handles edge cases like `null` fields cleanly.

### Level 1 — Basic

```java
public class ToStringBasic {
    static class Product {
        String name;
        double price;

        Product(String name, double price) { this.name = name; this.price = price; }

        @Override
        public String toString() {
            return name + " - $" + price;
        }
    }

    public static void main(String[] args) {
        Product p = new Product("Coffee", 3.50);
        System.out.println(p); // uses the overridden toString()
    }
}
```

**How to run:** `java ToStringBasic.java`

`println(p)` implicitly calls `p.toString()`, which returns `"Coffee - $3.5"` — no manual formatting call was needed at the print site, because the object itself knows how to describe itself.

### Level 2 — Intermediate

Same receipt idea, now with a `Receipt` class whose `toString()` composes the `toString()` of each `Product` it contains — showing how overrides compose naturally through nested objects.

```java
import java.util.List;

public class ToStringIntermediate {
    static class Product {
        String name;
        double price;
        Product(String name, double price) { this.name = name; this.price = price; }
        @Override
        public String toString() { return name + " - $" + price; }
    }

    static class Receipt {
        List<Product> items;
        Receipt(List<Product> items) { this.items = items; }

        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder("Receipt:\n");
            double total = 0;
            for (Product p : items) {
                sb.append("  ").append(p).append("\n"); // implicitly calls p.toString()
                total += p.price;
            }
            sb.append("Total: $").append(total);
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        Receipt receipt = new Receipt(List.of(
            new Product("Coffee", 3.50),
            new Product("Bagel", 2.25)
        ));
        System.out.println(receipt);
    }
}
```

**How to run:** `java ToStringIntermediate.java`

`sb.append(p)` calls `StringBuilder.append(Object)`, which internally calls `p.toString()` — so `Receipt.toString()` never manually invokes `Product.toString()`, it happens automatically anywhere an object is appended to a string or string builder.

### Level 3 — Advanced

Same receipt system, now handling a `null` product name gracefully and avoiding infinite recursion risk if two objects ever reference each other (a classic `toString()` pitfall), using `Objects.requireNonNullElse` and careful composition.

```java
import java.util.List;
import java.util.Objects;

public class ToStringAdvanced {
    static class Product {
        String name;
        double price;
        Product(String name, double price) { this.name = name; this.price = price; }

        @Override
        public String toString() {
            String safeName = Objects.requireNonNullElse(name, "(unnamed item)"); // guard against null
            return safeName + " - $" + String.format("%.2f", price);
        }
    }

    static class Receipt {
        List<Product> items;
        Receipt(List<Product> items) { this.items = items; }

        @Override
        public String toString() {
            if (items.isEmpty()) return "Receipt: (empty)";
            StringBuilder sb = new StringBuilder("Receipt:\n");
            double total = 0;
            for (Product p : items) {
                sb.append("  ").append(p).append("\n");
                total += p.price;
            }
            sb.append(String.format("Total: $%.2f", total));
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        Receipt receipt = new Receipt(List.of(
            new Product(null, 1.999),   // null name, unusual price precision
            new Product("Muffin", 2.5)
        ));
        System.out.println(receipt);

        Receipt empty = new Receipt(List.of());
        System.out.println(empty);
    }
}
```

**How to run:** `java ToStringAdvanced.java`

`Objects.requireNonNullElse(name, "(unnamed item)")` substitutes a safe fallback label instead of letting `null` flow into string concatenation as the literal text `"null"`, and `Receipt.toString()` special-cases the empty list up front — both are small defensive touches that keep `toString()` output readable and crash-free even with messy input data.

## 6. Walkthrough

Trace `main` in `ToStringAdvanced` from the first `println` to the second.

**Building `receipt`.** Two `Product` instances are created: one with `name = null` and `price = 1.999`, one with `name = "Muffin"` and `price = 2.5`. Both are wrapped in a `List.of(...)` and passed to `Receipt`'s constructor.

**`println(receipt)` calls `receipt.toString()`.** `items.isEmpty()` is `false` (two items), so the method proceeds. It starts `sb` with `"Receipt:\n"`.

**First loop iteration (`null`-named product).** `sb.append("  ").append(p)` implicitly calls `p.toString()`. Inside it, `Objects.requireNonNullElse(null, "(unnamed item)")` returns `"(unnamed item)"` since the first argument is `null`. `String.format("%.2f", 1.999)` rounds to `"2.00"`. The product's `toString()` returns `"(unnamed item) - $2.00"`, which gets appended followed by `"\n"`. `total` becomes `1.999`.

**Second loop iteration (`"Muffin"`).** `Objects.requireNonNullElse("Muffin", ...)` returns `"Muffin"` unchanged (the fallback is not used). Formats to `"Muffin - $2.50"`. `total` becomes `1.999 + 2.5 = 4.499`.

**Finishing `Receipt.toString()`.** `String.format("Total: $%.2f", 4.499)` rounds to `"Total: $4.50"`. The full assembled string is returned and printed.

**Second `println(empty)`.** `empty.items.isEmpty()` is `true`, so `toString()` short-circuits and returns `"Receipt: (empty)"` directly, skipping the loop and total calculation entirely.

```
receipt.toString():
  item 1: null name -> "(unnamed item)" ; price 1.999 -> "$2.00"
  item 2: "Muffin"                       ; price 2.5   -> "$2.50"
  total: 1.999 + 2.5 = 4.499 -> "$4.50"

empty.toString():
  items.isEmpty() -> true -> "Receipt: (empty)" (short-circuit, no loop)
```

**Final output.**
```
Receipt:
  (unnamed item) - $2.00
  Muffin - $2.50
Total: $4.50
Receipt: (empty)
```

## 7. Gotchas & takeaways

> **Never have two objects' `toString()` methods reference each other** (for example, `A.toString()` prints `B`, and `B.toString()` prints `A`) — this causes infinite recursion and a `StackOverflowError` at runtime, since each call triggers the other endlessly. This is a classic real-world bug in bidirectional object relationships (like parent/child links).

> **`toString()` must be annotated `@Override` and match `Object`'s exact signature** — `public String toString()`, no arguments, returning `String`. A typo like `public String toString(int x)` or `String tostring()` silently defines an unrelated overload/method instead of overriding, and callers will keep getting `Object`'s default format with no compiler warning.

- `println`, string concatenation, and `String.valueOf` all call `toString()` implicitly — overriding it improves output everywhere, not just at one call site.
- `Object`'s default `toString()` (class name + `@` + hex hash) is a fallback, not something meant for end users to read.
- `toString()` overrides compose naturally: appending an object to a `StringBuilder` or string calls its `toString()` automatically, so nested objects "just work."
- Guard against `null` fields explicitly inside `toString()` (for example with `Objects.requireNonNullElse`) so output stays readable instead of showing the literal text `"null"` or throwing exceptions.
