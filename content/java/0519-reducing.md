---
card: java
gi: 519
slug: reducing
title: reducing()
---

## 1. What it is

`Collectors.reducing(...)` brings `Stream.reduce`'s folding behavior (see [[reduce-3-forms]]) into the `Collectors` world, so it can be used as a downstream collector — most commonly with `groupingBy`, where `Stream.reduce` itself cannot be used directly, since `groupingBy`'s downstream argument must be a `Collector`, not a stream terminal operation. It comes in matching forms: `reducing(BinaryOperator<T>)` (no identity, returns `Optional<T>`), `reducing(T identity, BinaryOperator<T>)` (returns `T` directly), and `reducing(U identity, Function<T,U> mapper, BinaryOperator<U> op)` (maps then reduces, similar in spirit to `mapping` combined with a simpler reduction).

## 2. Why & when

Most of the time, a more specific collector — `Collectors.summingInt`, `Collectors.counting`, `Collectors.maxBy` — already expresses exactly the reduction you need, more readably than `Collectors.reducing`. `Collectors.reducing` is the general-purpose fallback for when the combination logic is custom and doesn't match any of the built-in, purpose-named collectors — most typically as a `groupingBy` downstream when you need "the single combined/best/accumulated value per group" using your own combining rule, not just a sum or a count.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Order(String customer, double amount) {}

List<Order> orders = List.of(
        new Order("Alice", 50.0), new Order("Bob", 30.0), new Order("Alice", 75.0));

// Per-customer highest single order, using a custom combining rule
Map<String, Optional<Order>> biggestOrderByCustomer = orders.stream()
        .collect(Collectors.groupingBy(
                Order::customer,
                Collectors.reducing((a, b) -> a.amount() >= b.amount() ? a : b)));
```

`Collectors.reducing` mirrors `Stream.reduce`'s three forms, but packaged as a `Collector` so it can be composed as a downstream collector inside `groupingBy` or other collector-composition contexts.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="reducing as a downstream collector folds each group down to a single combined value">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="110" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice, $50</text>
  <rect x="140" y="20" width="110" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="195" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice, $75</text>
  <text x="135" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">groupingBy(customer, reducing(max by amount))</text>
  <line x1="135" y1="50" x2="135" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowRD)"/>
  <rect x="60" y="85" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="135" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Alice -&gt; $75 order</text>
  <defs><marker id="arrowRD" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each group's elements are folded down to one value using the reducing rule — here, keeping whichever order had the higher amount.

## 5. Runnable example

Scenario: finding each customer's largest single order in a sales history — evolved from a basic per-group reduction, through a version with an identity value avoiding `Optional`, to a version using `reducing`'s three-argument, mapping form for a computed per-group aggregate.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ReducingBasic {
    record Order(String customer, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("Alice", 50.0),
                new Order("Bob", 30.0),
                new Order("Alice", 75.0),
                new Order("Bob", 45.0)
        );

        Map<String, Optional<Order>> biggestOrderByCustomer = orders.stream()
                .collect(Collectors.groupingBy(
                        Order::customer,
                        Collectors.reducing((a, b) -> a.amount() >= b.amount() ? a : b)));

        new TreeMap<>(biggestOrderByCustomer).forEach((customer, biggest) ->
                biggest.ifPresent(order -> System.out.println(customer + "'s biggest order: $" + order.amount())));
    }
}
```

**How to run:** `java ReducingBasic.java`

Expected output:
```
Alice's biggest order: $75.0
Bob's biggest order: $45.0
```

`Collectors.reducing((a, b) -> a.amount() >= b.amount() ? a : b)` uses the one-argument form (no identity), so each group's result is `Optional<Order>` — always present here since every group is guaranteed at least one element by construction of `groupingBy` itself, but the `Optional` wrapper is still required by this form's contract.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ReducingWithIdentity {
    record Order(String customer, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("Alice", 50.0),
                new Order("Bob", 30.0),
                new Order("Alice", 75.0),
                new Order("Bob", 45.0)
        );

        // Identity value (0.0) avoids Optional -- simpler when a natural "empty" total exists.
        Map<String, Double> totalByCustomer = orders.stream()
                .collect(Collectors.groupingBy(
                        Order::customer,
                        Collectors.reducing(0.0, Order::amount, Double::sum)));

        new TreeMap<>(totalByCustomer).forEach((customer, total) ->
                System.out.printf("%s: $%.2f total%n", customer, total));
    }
}
```

**How to run:** `java ReducingWithIdentity.java`

Expected output:
```
Alice: $125.00 total
Bob: $75.00 total
```

The real-world concern this adds: using the three-argument form, `reducing(identity, mapper, op)`, which both extracts a value from each element (`Order::amount`) *and* combines those values with an identity (`0.0`) — this produces a plain `Double` result per group directly, with no `Optional` wrapping needed, since `0.0` is a perfectly valid "empty group" total (though this specific example is functionally equivalent to `Collectors.summingDouble(Order::amount)`, which reads more clearly for this exact case).

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ReducingCustomMerge {
    record Order(String customer, String product, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("Alice", "Widget", 50.0),
                new Order("Bob", "Gadget", 30.0),
                new Order("Alice", "Gizmo", 75.0),
                new Order("Alice", "Widget", 20.0)
        );

        // Custom merge rule: combine into a single "product1+product2+..." summary string per customer,
        // while tracking the running total inside that same string -- a genuinely custom reduction
        // that no single built-in Collectors method expresses directly.
        Map<String, String> summaryByCustomer = orders.stream()
                .collect(Collectors.groupingBy(
                        Order::customer,
                        Collectors.reducing(
                                "",
                                order -> order.product() + "($" + order.amount() + ")",
                                (a, b) -> a.isEmpty() ? b : a + " + " + b)));

        new TreeMap<>(summaryByCustomer).forEach((customer, summary) -> System.out.println(customer + ": " + summary));
    }
}
```

**How to run:** `java ReducingCustomMerge.java`

Expected output:
```
Alice: Widget($50.0) + Gizmo($75.0) + Widget($20.0)
Bob: Gadget($30.0)
```

This uses `reducing`'s three-argument form with a genuinely custom merge rule that no single built-in collector expresses directly: each `Order` is first mapped to a formatted `"product($amount)"` string, then those strings are combined per customer with `" + "` between them — starting from an empty-string identity, and specially handling the first element (where the running accumulator is still `""`) to avoid a leading `" + "`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four orders are defined: three for `"Alice"` (`Widget` $50, `Gizmo` $75, `Widget` $20) and one for `"Bob"` (`Gadget` $30).

`orders.stream().collect(Collectors.groupingBy(Order::customer, Collectors.reducing("", order -> order.product() + "($" + order.amount() + ")", (a, b) -> a.isEmpty() ? b : a + " + " + b)))` processes each order. For the first `Alice` order, `Order("Alice", "Widget", 50.0)`: the mapper transforms it to `"Widget($50.0)"`. Since this is the first element for the `"Alice"` group, the reduction starts from the identity `""` and combines it with the mapped value: `(a, b) -> a.isEmpty() ? b : a + " + " + b` is called with `a=""` and `b="Widget($50.0)"` — since `a.isEmpty()` is `true`, the result is just `b`, i.e. `"Widget($50.0)"`.

For the `Bob` order, `Order("Bob", "Gadget", 30.0)`: mapped to `"Gadget($30.0)"`. First element for `"Bob"`'s group, combined with identity `""`: `a.isEmpty()` true, result is `"Gadget($30.0)"`.

For the second `Alice` order, `Order("Alice", "Gizmo", 75.0)`: mapped to `"Gizmo($75.0)"`. Now the running accumulator for `"Alice"` is `"Widget($50.0)"` (not empty), so `a.isEmpty()` is `false`, and the result is `a + " + " + b` = `"Widget($50.0) + Gizmo($75.0)"`.

For the third `Alice` order, `Order("Alice", "Widget", 20.0)`: mapped to `"Widget($20.0)"`. Running accumulator is `"Widget($50.0) + Gizmo($75.0)"` (not empty), so the result is `"Widget($50.0) + Gizmo($75.0)" + " + " + "Widget($20.0)"` = `"Widget($50.0) + Gizmo($75.0) + Widget($20.0)"`.

```
Alice, Widget $50 -> mapped "Widget($50.0)" -> acc="" (empty) -> result="Widget($50.0)"
Bob, Gadget $30    -> mapped "Gadget($30.0)" -> acc="" (empty) -> result="Gadget($30.0)"
Alice, Gizmo $75   -> mapped "Gizmo($75.0)"  -> acc="Widget($50.0)" (not empty) -> "Widget($50.0) + Gizmo($75.0)"
Alice, Widget $20  -> mapped "Widget($20.0)" -> acc="Widget($50.0) + Gizmo($75.0)" -> "...+ Widget($20.0)"
```

The final map holds `"Alice"` mapped to the full concatenated summary of all three of her orders, and `"Bob"` mapped to just his one order's summary. `new TreeMap<>(...)` orders alphabetically, and the `forEach` prints both customers' complete order summaries.

## 7. Gotchas & takeaways

> Before reaching for `Collectors.reducing`, check whether a more specific, purpose-built collector already expresses what you need — `Collectors.summingInt`/`summingDouble`, `Collectors.counting`, `Collectors.maxBy`/`minBy`, `Collectors.joining` all cover common reductions more readably than a general `reducing` call would. `Collectors.reducing` earns its place specifically for genuinely custom combination logic, as in Level 3, where no built-in collector fits.

- `Collectors.reducing(...)` mirrors `Stream.reduce`'s three overloads (see [[reduce-3-forms]]), packaged as a `Collector` so it can be used as a `groupingBy` downstream argument, where `Stream.reduce` itself cannot be used directly.
- The one-argument form (`reducing(BinaryOperator<T>)`) returns `Optional<T>` per group; the identity-based forms return `T`/`U` directly.
- The three-argument form (`reducing(identity, mapper, op)`) both transforms each element and combines the transformed values — similar in spirit to combining `mapping` with a simpler binary reduction.
- Prefer a more specific, named collector when one exists (`summingInt`, `counting`, `maxBy`, `joining`) — they communicate intent more clearly than a general-purpose `reducing` call expressing the same logic.
- `Collectors.reducing` is the right tool specifically when the per-group combination logic is genuinely custom and doesn't match any purpose-built collector, as with the formatted, order-dependent summary string built in Level 3.
