---
card: java
gi: 205
slug: constants-static-final
title: Constants (static final)
---

## 1. What it is

A **constant** in Java is conventionally a field declared `static final` — `static` so there's exactly one shared copy, and `final` so that copy can never be reassigned once initialized. By strong convention, constant names are written in `UPPER_SNAKE_CASE`, immediately signaling to any reader that the value is fixed and shared, not ordinary per-instance state.

```java
class Physics {
    static final double SPEED_OF_LIGHT = 299_792_458.0; // meters per second — never changes
    static final int MAX_RETRIES = 3;
}

System.out.println(Physics.SPEED_OF_LIGHT); // 2.99792458E8
// Physics.SPEED_OF_LIGHT = 5.0; // COMPILE ERROR — cannot reassign a final field
```

`static` ensures the constant exists once, shared class-wide, exactly like any other static field; `final` adds the additional guarantee that no code, anywhere, can ever reassign it after its initial value is set — attempting to do so is a compile-time error, not a runtime one.

## 2. Why & when

Constants exist to name and centralize fixed values that would otherwise be scattered as unexplained "magic numbers" or repeated literal strings throughout a codebase:

- **Self-documenting code** — `MAX_RETRIES` immediately communicates intent, whereas a bare `3` appearing in the middle of a method leaves a reader wondering what that particular `3` means and why.
- **Single source of truth** — if a limit, rate, or fixed configuration value ever needs to change, updating one constant declaration updates every place that references it, rather than requiring a search-and-replace across scattered literal values.
- **Compile-time safety** — `final` guarantees the compiler will catch any accidental reassignment immediately, rather than allowing a bug where some code path unexpectedly mutates a value that was meant to be fixed forever.

You declare a constant whenever a value is genuinely fixed for the lifetime of the program and shared conceptually across all uses — as opposed to configuration that might reasonably change at runtime (which calls for an ordinary, non-`final` field) or data that's meant to vary per instance (an ordinary instance field).

## 3. Core concept

```java
class GameConfig {
    static final int MAX_PLAYERS = 4;
    static final String DEFAULT_DIFFICULTY = "Normal";
    static final double VERSION = 1.2;
}

public class ConstantsDemo {
    public static void main(String[] args) {
        System.out.println("Max players: " + GameConfig.MAX_PLAYERS);
        System.out.println("Default difficulty: " + GameConfig.DEFAULT_DIFFICULTY);
        System.out.println("Version: " + GameConfig.VERSION);
        // GameConfig.MAX_PLAYERS = 8; // would NOT compile
    }
}
```

Every use of `GameConfig.MAX_PLAYERS` throughout an entire codebase refers to the exact same, permanently fixed value — there is no way for one part of the program to see `4` while another sees something different, which is precisely the guarantee `static final` provides.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single static final constant shared and referenced from multiple different places in the code, all reading the exact same fixed, unchangeable value, contrasted with an attempted reassignment which the compiler rejects">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>

  <rect x="240" y="20" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">MAX_PLAYERS = 4</text>

  <line x1="270" y1="55" x2="120" y2="90" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="315" y1="55" x2="315" y2="90" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="360" y1="55" x2="490" y2="90" stroke="#79c0ff" stroke-width="1.5"/>

  <text x="80" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Lobby code</text>
  <text x="315" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Matchmaking code</text>
  <text x="490" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">UI display code</text>

  <text x="300" y="125" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">MAX_PLAYERS = 8;  -&gt;  COMPILE ERROR (final)</text>
</svg>

Every reader of a `static final` constant sees the same, permanently fixed value — reassignment is a compile error.

## 5. Runnable example

Scenario: a small e-commerce order calculator relying on fixed business rules — starting with basic named constants replacing magic numbers, then extending to constants used across multiple related methods consistently, then hardening into a case demonstrating why using constants (rather than repeated literals) prevents a class of bugs when a business rule changes.

### Level 1 — Basic

```java
public class OrderBasic {
    static final double TAX_RATE = 0.08;
    static final double FREE_SHIPPING_THRESHOLD = 50.0;

    public static void main(String[] args) {
        double subtotal = 42.0;
        double tax = subtotal * TAX_RATE;
        System.out.println("Tax: $" + tax);
        System.out.println("Free shipping? " + (subtotal >= FREE_SHIPPING_THRESHOLD));
    }
}
```

**How to run:** `java OrderBasic.java`

`TAX_RATE` and `FREE_SHIPPING_THRESHOLD` give clear names to values that would otherwise be unexplained literals (`0.08`, `50.0`) scattered through the calculation logic — anyone reading `subtotal * TAX_RATE` immediately understands what's being computed, without needing surrounding comments to explain a bare `0.08`.

### Level 2 — Intermediate

Same order system, now with several methods all consistently referencing the same constants, demonstrating that the fixed business rules stay perfectly synchronized across every use.

```java
public class OrderIntermediate {
    static final double TAX_RATE = 0.08;
    static final double FREE_SHIPPING_THRESHOLD = 50.0;
    static final double SHIPPING_COST = 5.99;

    static double calculateTax(double subtotal) {
        return subtotal * TAX_RATE;
    }

    static double calculateShipping(double subtotal) {
        return subtotal >= FREE_SHIPPING_THRESHOLD ? 0.0 : SHIPPING_COST;
    }

    static double calculateTotal(double subtotal) {
        return subtotal + calculateTax(subtotal) + calculateShipping(subtotal);
    }

    public static void main(String[] args) {
        System.out.println("Total for $42: $" + calculateTotal(42.0));
        System.out.println("Total for $60: $" + calculateTotal(60.0));
    }
}
```

**How to run:** `java OrderIntermediate.java`

All three methods reference the same three constants — if `TAX_RATE` ever needed updating (say, a tax law change), editing that single declaration would correctly update `calculateTax`, and therefore `calculateTotal`, consistently everywhere at once, with no risk of one method being updated while another is accidentally missed.

### Level 3 — Advanced

Same order system, now demonstrating concretely what changing one constant does — and why hard-coding the same value as separate literals in multiple places (the mistake constants prevent) would have been far riskier to maintain correctly.

```java
public class OrderAdvanced {
    static final double TAX_RATE = 0.08;
    static final double FREE_SHIPPING_THRESHOLD = 50.0;
    static final double SHIPPING_COST = 5.99;

    static double calculateTax(double subtotal) {
        return subtotal * TAX_RATE;
    }

    static double calculateShipping(double subtotal) {
        return subtotal >= FREE_SHIPPING_THRESHOLD ? 0.0 : SHIPPING_COST;
    }

    static double calculateTotal(double subtotal) {
        return subtotal + calculateTax(subtotal) + calculateShipping(subtotal);
    }

    static void printReceipt(double subtotal) {
        System.out.printf("Subtotal: $%.2f%n", subtotal);
        System.out.printf("Tax (%.0f%%): $%.2f%n", TAX_RATE * 100, calculateTax(subtotal));
        System.out.printf("Shipping: $%.2f%n", calculateShipping(subtotal));
        System.out.printf("Total: $%.2f%n", calculateTotal(subtotal));
    }

    public static void main(String[] args) {
        System.out.println("--- Order 1 ---");
        printReceipt(42.0);

        System.out.println("--- Order 2 (qualifies for free shipping) ---");
        printReceipt(55.0);
    }
}
```

**How to run:** `java OrderAdvanced.java`

`printReceipt` reads `TAX_RATE` directly to display the tax *rate* (`TAX_RATE * 100` for a percentage) as well as calling `calculateTax` to display the tax *amount* — both derived from the exact same single constant, guaranteeing the displayed rate and the actually-charged tax can never drift out of sync with each other, which would be a real risk if the rate were hard-coded separately in the display logic and the calculation logic.

## 6. Walkthrough

Trace `printReceipt(55.0)` from `OrderAdvanced.main`:

**Subtotal line.** `System.out.printf("Subtotal: $%.2f%n", 55.0)` prints `"Subtotal: $55.00"`.

**Tax line.** `TAX_RATE * 100` is `0.08 * 100 = 8.0`, formatted as `%.0f%%` gives `"8%"`. `calculateTax(55.0)` computes `55.0 * 0.08 = 4.4`. Prints `"Tax (8%): $4.40"`.

**Shipping line.** `calculateShipping(55.0)` checks `55.0 >= FREE_SHIPPING_THRESHOLD (50.0)` — true, so it returns `0.0`. Prints `"Shipping: $0.00"`.

**Total line.** `calculateTotal(55.0)` computes `55.0 + calculateTax(55.0) + calculateShipping(55.0) = 55.0 + 4.4 + 0.0 = 59.4`. Prints `"Total: $59.40"`.

```
subtotal = 55.0
TAX_RATE = 0.08 -> tax = 55.0 * 0.08 = 4.4
FREE_SHIPPING_THRESHOLD = 50.0 -> 55.0 >= 50.0 -> shipping = 0.0
total = 55.0 + 4.4 + 0.0 = 59.4
```

**Final output for Order 2.** `"Subtotal: $55.00"`, `"Tax (8%): $4.40"`, `"Shipping: $0.00"`, `"Total: $59.40"` — every figure traces back to the same three `static final` constants, guaranteeing consistency across the entire receipt.

## 7. Gotchas & takeaways

> **`final` only prevents *reassigning* the field itself — it does not make the referenced object immutable if that object is itself mutable.** `static final List<String> ITEMS = new ArrayList<>();` prevents `ITEMS = someOtherList;`, but `ITEMS.add("new item")` is still perfectly legal, since the list object's own contents aren't protected by `final` — only the reference variable is.

> **Uppercase naming (`MAX_RETRIES`) is a strong convention, not a compiler-enforced rule** — Java will happily compile `static final int maxRetries = 3;` with lowercase naming, but doing so breaks a near-universal convention that helps every Java developer instantly recognize a constant at a glance.

- A constant is conventionally a `static final` field: one shared copy (`static`), never reassignable after initialization (`final`).
- Constants replace unexplained "magic numbers" and repeated literals with self-documenting, centrally-defined names.
- Changing a constant's declared value updates every place in the code that references it, keeping related calculations and displays consistently in sync.
- `final` only protects the field's own reference from reassignment — it does not automatically make a referenced mutable object's contents immutable.
