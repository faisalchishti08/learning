---
card: java
gi: 743
slug: guarded-patterns-when-clauses
title: Guarded patterns (when clauses)
---

## 1. What it is

A **guarded pattern** attaches a boolean condition to a `switch` case using a `when` clause: `case Purchase(var user, var amount) when amount >= 100.0 -> ...`. The case only matches when **both** the pattern matches the value's shape **and** the `when` condition evaluates to `true`. This lets a single `switch` express "this type, but only under this extra condition" without falling back to nested `if` statements inside the case body, and — because the guard is part of the case label itself — the compiler can still reason about it when checking exhaustiveness.

## 2. Why & when

Type patterns alone answer "what kind of thing is this?" but real dispatch logic often needs a finer question: "what kind of thing is this, **and** does it also satisfy some runtime condition?" Before guarded patterns, that meant either nesting an `if` inside the case body (which works, but buries the condition a level deeper than the case label, making it easy to overlook when scanning the switch), or splitting the condition into a separate type just to get a distinct case (over-engineering the type model just to satisfy the switch). Guarded patterns let the condition live right at the case label, next to the type it refines, so a reader scanning the `case` lines top to bottom sees the full decision logic — type **and** condition — in one place. This is especially valuable when a single record type covers a range of situations that should be handled differently (a `Purchase` under $100 vs. over $100; an `Order` that's already `shipped` vs. not) without multiplying record types just to distinguish them.

## 3. Core concept

```java
sealed interface Tier {}
record Points(int value) {}

static String classify(int score) {
    return switch (Integer.valueOf(score)) {
        case Integer s when s >= 90 -> "A";
        case Integer s when s >= 80 -> "B";
        case Integer s when s >= 70 -> "C";
        case Integer s -> "F";
    };
}
```

Each `case Integer s when ...` tests the same type (`Integer`) but a different guard; the **first** guard that evaluates to `true`, in top-to-bottom order, wins — so ordering from most to least restrictive matters.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch value is tested against each guarded case in order; a case matches only when its type pattern matches and its when condition is true">
  <rect x="20" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">score = 82</text>

  <rect x="200" y="20" width="180" height="34" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="290" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">when s &gt;= 90 -&gt; false, skip</text>

  <rect x="200" y="64" width="180" height="34" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="290" y="86" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">when s &gt;= 80 -&gt; true, MATCH</text>

  <rect x="200" y="108" width="180" height="34" rx="6" fill="#0f1620" stroke="#8b949e" opacity="0.5"/>
  <text x="290" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">when s &gt;= 70 -&gt; not reached</text>

  <rect x="440" y="64" width="160" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="86" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">result: "B"</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Guards are checked top to bottom; the first true guard wins</text>
</svg>

*A guarded case only fires when both its type pattern and its `when` condition hold.*

## 5. Runnable example

Scenario: a shipping-cost calculator for orders, growing from a flat `if` chain into guarded switch patterns over an order hierarchy.

### Level 1 — Basic

```java
public class ShippingIfElse {
    record Order(double weightKg, String destination) {}

    static double shippingCost(Order order) {
        if (order.destination().equals("domestic") && order.weightKg() <= 1.0) {
            return 5.00;
        } else if (order.destination().equals("domestic")) {
            return 5.00 + (order.weightKg() - 1.0) * 2.00;
        } else {
            return 20.00 + order.weightKg() * 3.00;
        }
    }

    public static void main(String[] args) {
        System.out.println(shippingCost(new Order(0.5, "domestic")));
        System.out.println(shippingCost(new Order(3.0, "domestic")));
        System.out.println(shippingCost(new Order(2.0, "international")));
    }
}
```

**How to run:** `java ShippingIfElse.java` (JDK 21+).

This mixes the type check (there's really only one `Order` shape here) with runtime conditions inside a plain `if/else` chain — workable, but the conditions and the record's shape aren't visually connected the way a switch case label would connect them.

### Level 2 — Intermediate

```java
public class ShippingGuarded {
    record Order(double weightKg, String destination) {}

    static double shippingCost(Order order) {
        return switch (order) {
            case Order(var w, var dest) when dest.equals("domestic") && w <= 1.0 -> 5.00;
            case Order(var w, var dest) when dest.equals("domestic") -> 5.00 + (w - 1.0) * 2.00;
            case Order(var w, var dest) -> 20.00 + w * 3.00;
        };
    }

    public static void main(String[] args) {
        System.out.println(shippingCost(new Order(0.5, "domestic")));
        System.out.println(shippingCost(new Order(3.0, "domestic")));
        System.out.println(shippingCost(new Order(2.0, "international")));
    }
}
```

**How to run:** `java ShippingGuarded.java`.

The real-world concern added: every branch's condition now sits directly on the `case` label next to the destructured fields it depends on (`w`, `dest`), reading top to bottom as an ordered set of rules — light domestic, heavier domestic, everything else — rather than nested boolean expressions.

### Level 3 — Advanced

```java
public class ShippingAdvanced {
    sealed interface Order permits StandardOrder, ExpressOrder {}
    record StandardOrder(double weightKg, String destination) implements Order {}
    record ExpressOrder(double weightKg, String destination, boolean isFragile) implements Order {}

    static double shippingCost(Order order) {
        return switch (order) {
            case StandardOrder(var w, var dest) when dest.equals("domestic") && w <= 1.0 -> 5.00;
            case StandardOrder(var w, var dest) when dest.equals("domestic") -> 5.00 + (w - 1.0) * 2.00;
            case StandardOrder(var w, var dest) -> 20.00 + w * 3.00;
            case ExpressOrder(var w, var dest, var fragile) when fragile ->
                40.00 + w * 5.00 + 15.00; // fragile handling surcharge
            case ExpressOrder(var w, var dest, var fragile) -> 40.00 + w * 5.00;
        };
    }

    public static void main(String[] args) {
        System.out.println(shippingCost(new StandardOrder(0.5, "domestic")));
        System.out.println(shippingCost(new ExpressOrder(2.0, "domestic", true)));
        System.out.println(shippingCost(new ExpressOrder(2.0, "domestic", false)));
    }
}
```

**How to run:** `java ShippingAdvanced.java`.

This adds the production-flavored hard case: **two order kinds** in a sealed hierarchy, each with its own guarded and unguarded cases, mixed in a single switch. The compiler still enforces exhaustiveness across both `StandardOrder` and `ExpressOrder`, and — since each guarded case is paired with an unguarded fallback for the same record type — every combination of fields is covered without needing a `default`.

## 6. Walkthrough

Tracing `ShippingAdvanced.main`'s second call, `shippingCost(new ExpressOrder(2.0, "domestic", true))`:

1. The `switch (order)` expression tests `order`'s runtime type against each case in order. The first three cases all pattern-match against `StandardOrder`, but `order` is an `ExpressOrder`, so none of them match — the switch moves on without evaluating their guards at all (a guard is only checked once its case's type pattern already matches).
2. The fourth case, `ExpressOrder(var w, var dest, var fragile) when fragile`, matches the type: `order` is destructured into `w = 2.0`, `dest = "domestic"`, `fragile = true`. The guard `when fragile` evaluates `true`, so this case wins.
3. The arm computes `40.00 + 2.0 * 5.00 + 15.00 = 65.00` and that becomes the switch's result, returned by `shippingCost`.
4. For the third call, `shippingCost(new ExpressOrder(2.0, "domestic", false))`: the fourth case's type pattern matches again, but this time `fragile` is `false`, so the guard fails and the switch falls through to the fifth case, the unguarded `ExpressOrder(var w, var dest, var fragile)`, which always matches once its type pattern succeeds. That arm computes `40.00 + 2.0 * 5.00 = 50.00`.

Expected output:
```
5.0
65.0
50.0
```

## 7. Gotchas & takeaways

> **Gotcha:** an unguarded case for a type must come **after** every guarded case for that same type, or it will shadow them and the compiler will reject the switch as having unreachable code — the unguarded case always matches once the type matches, so it can never be followed by another case for the same type.

- A guard is only evaluated after its case's pattern already matches the value's shape — it's a refinement, not a replacement, for the type test.
- List guarded cases for the same type from most to least restrictive, ending with an unguarded fallback for that type if you need one.
- Guards can reference any variables the pattern destructured, plus any other value in scope — they're ordinary boolean expressions.
- Keep guard conditions simple and side-effect-free; a guard that mutates state makes switch evaluation order (which the language guarantees is top to bottom) a correctness dependency, which is easy to get wrong on maintenance.
- Combine with [exhaustiveness checking](0745-exhaustiveness-checking-in-switch.md): the compiler only requires *type* coverage to be exhaustive, not guard coverage — you are responsible for making sure your guards for a given type don't leave a gap (Java resolves this by requiring an unguarded case as the catch-all when needed).
