---
card: java
gi: 597
slug: optional-stream
title: Optional.stream
---

## 1. What it is

`Optional.stream()` is a Java 9 method that converts an `Optional` into a `Stream` of zero or one elements: if the `Optional` contains a value, the stream contains that single element; if the `Optional` is empty, the stream is empty. It bridges the `Optional` and `Stream` APIs, allowing `Optional` values to participate directly in stream pipelines — particularly inside `flatMap` operations where each element may optionally produce a sub-stream.

## 2. Why & when

Before Java 9, converting an `Optional` to a `Stream` required a manual conditional: `opt.map(Stream::of).orElseGet(Stream::empty)`. This pattern was clunky and appeared every time an `Optional`-bearing method needed to contribute to a stream pipeline, which happens frequently in real code (optional fields, nullable query results, conditional processing steps). `Optional.stream()` collapses this into a single, obvious call, making `flatMap(Optional::stream)` the standard idiom for "include this element only if it exists" — directly parallel to how `flatMap(Stream::ofNullable)` handles nullable references.

## 3. Core concept

```java
Optional<String> present = Optional.of("hello");
Optional<String> empty   = Optional.empty();

present.stream().forEach(System.out::println); // prints "hello"
empty.stream().forEach(System.out::println);   // prints nothing

long count = present.stream().count(); // 1
count = empty.stream().count();        // 0
```

`present.stream()` returns `Stream.of("hello")` (one element). `empty.stream()` returns `Stream.empty()` (zero elements). The stream is always a `Stream<T>`, never `null`.

## 4. Diagram

<svg viewBox="0 0 520 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optional.stream converts an Optional to a zero-or-one element Stream">
  <rect x="20" y="10" width="480" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="60" y="30" width="180" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">optional.stream()</text>

  <line x1="150" y1="70" x2="100" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="150" y1="70" x2="250" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <text x="85" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">Empty</text>
  <text x="245" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">Present</text>

  <rect x="30" y="95" width="140" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="100" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Stream.empty()</text>

  <rect x="210" y="95" width="140" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="280" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Stream.of(value)</text>

  <text x="360" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">→ 0 elements</text>
  <text x="360" y="125" fill="#8b949e" font-size="9" font-family="sans-serif">→ 1 element</text>
</svg>

`Optional.stream()` bridges the gap between `Optional` and `Stream` — empty becomes zero, present becomes one.

## 5. Runnable example

Scenario: processing a list of orders where each order optionally has a discount code — starting with a basic `Optional`-to-`Stream` conversion, extending to a `flatMap` pipeline that extracts all present discount codes from a list of orders, and finally handling edge cases with nested optional fields and conditional filtering.

### Level 1 — Basic

```java
// File: OptionalStreamDemo.java
import java.util.Optional;
import java.util.stream.Collectors;

public class OptionalStreamDemo {
    public static void main(String[] args) {
        Optional<String> name = Optional.of("Alice");
        Optional<String> empty = Optional.empty();

        System.out.println("Present Optional → stream:");
        var presentList = name.stream().collect(Collectors.toList());
        System.out.println("  " + presentList);

        System.out.println("Empty Optional → stream:");
        var emptyList = empty.stream().collect(Collectors.toList());
        System.out.println("  " + emptyList);
    }
}
```

**How to run:** `java OptionalStreamDemo.java`

Expected output:
```
Present Optional → stream:
  [Alice]
Empty Optional → stream:
  []
```

The simplest conversion: `name.stream()` produces a one-element stream, `empty.stream()` produces an empty stream. The `collect(toList())` makes the difference visible.

### Level 2 — Intermediate

```java
// File: DiscountProcessor.java
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class DiscountProcessor {
    record Order(String id, String discountCode) {
        Optional<String> getDiscount() {
            return Optional.ofNullable(discountCode);
        }
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("ORD-1", "SUMMER20"),
            new Order("ORD-2", null),
            new Order("ORD-3", "WELCOME10"),
            new Order("ORD-4", null),
            new Order("ORD-5", "SUMMER20")
        );

        // Extract all applied discount codes (skip orders without discounts)
        List<String> appliedCodes = orders.stream()
            .flatMap(order -> order.getDiscount().stream())
            .collect(Collectors.toList());

        System.out.println("Applied discount codes: " + appliedCodes);

        // Count distinct discount codes used
        long distinctCodes = orders.stream()
            .flatMap(order -> order.getDiscount().stream())
            .distinct()
            .count();
        System.out.println("Distinct codes: " + distinctCodes);
    }
}
```

**How to run:** `java DiscountProcessor.java`

Expected output:
```
Applied discount codes: [SUMMER20, WELCOME10, SUMMER20]
Distinct codes: 2
```

The real-world concern added: a `flatMap` pipeline where each order's discount code is optional. `Order.getDiscount()` returns `Optional<String>` — `Optional.of(discountCode)` when present, `Optional.empty()` when `null`. `.flatMap(order -> order.getDiscount().stream())` converts each `Optional` to a zero-or-one-element stream, and `flatMap` merges them into a flat stream of discount codes. Orders without discounts simply contribute nothing to the output — no null checks, no `filter`, no conditional logic.

### Level 3 — Advanced

```java
// File: OrderPipeline.java
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public class OrderPipeline {
    record Customer(String id, String name) {}
    record Order(String id, Customer customer, String discountCode) {
        Optional<String> getDiscount() {
            return Optional.ofNullable(discountCode);
        }
    }

    // Simulated: only some customers have loyalty tiers
    static Optional<String> getLoyaltyTier(Customer c) {
        // In reality, this would query a database
        return switch (c.id()) {
            case "C1" -> Optional.of("GOLD");
            case "C2" -> Optional.of("SILVER");
            default   -> Optional.empty();
        };
    }

    public static void main(String[] args) {
        Customer alice = new Customer("C1", "Alice");
        Customer bob   = new Customer("C2", "Bob");
        Customer carol = new Customer("C3", "Carol");

        List<Order> orders = List.of(
            new Order("ORD-1", alice, "SALE15"),
            new Order("ORD-2", bob,   null),
            new Order("ORD-3", carol, "VIP10"),
            new Order("ORD-4", alice, null),
            new Order("ORD-5", bob,   "SALE15")
        );

        // Build a report: for each order, if both a discount and a loyalty tier
        // exist, produce a "qualified" entry; otherwise skip the order.
        record QualifiedOrder(String orderId, String customerName, String tier, String code) {}

        List<QualifiedOrder> qualified = orders.stream()
            .flatMap(order -> {
                // Nested Optional.stream: only proceed if tier exists
                return getLoyaltyTier(order.customer())
                    .stream()
                    .flatMap(tier ->
                        order.getDiscount()
                            .stream()
                            .map(code -> new QualifiedOrder(
                                order.id(), order.customer().name(), tier, code
                            ))
                    );
            })
            .collect(Collectors.toList());

        System.out.println("Qualified orders (loyalty tier + discount):");
        qualified.forEach(q -> System.out.printf(
            "  %s | %s | %s | %s%n", q.orderId(), q.customerName(), q.tier(), q.code()
        ));
    }
}
```

**How to run:** `java OrderPipeline.java`

Expected output:
```
Qualified orders (loyalty tier + discount):
  ORD-1 | Alice | GOLD | SALE15
  ORD-5 | Bob | SILVER | SALE15
```

The production-flavoured edge cases: (1) nested optional fields — both `getLoyaltyTier()` and `getDiscount()` return `Optional`, and only orders where both are present qualify; (2) Carol's order (ORD-3) has a discount ("VIP10") but no loyalty tier, so `getLoyaltyTier` returns empty → the outer `.stream()` produces an empty stream → nothing contributes; (3) Alice's second order (ORD-4) has a loyalty tier (GOLD) but no discount → the inner `order.getDiscount().stream()` produces empty → nothing for that order; (4) the nested `flatMap` pattern with `.stream()` reads as "if X exists, then also check if Y exists, and if so, map them together" — a purely declarative join of two optional values.

## 6. Walkthrough

Tracing the `qualified` stream in the Level 3 example from `orders.stream()` to the final `List<QualifiedOrder>`:

The terminal operation `.collect(Collectors.toList())` triggers stream consumption. The source `orders` yields five `Order` elements sequentially:

**ORD-1** (`alice`, `"SALE15"`): The outer `flatMap` lambda receives `order`. `getLoyaltyTier(alice)` is called — `alice.id()` is `"C1"`, returns `Optional.of("GOLD")`. `.stream()` converts this to a one-element stream `Stream.of("GOLD")`. The inner `flatMap` receives `tier = "GOLD"`. Inside: `order.getDiscount()` → `Optional.of("SALE15")`, `.stream()` → `Stream.of("SALE15")`, `.map(...)` → `Stream.of(new QualifiedOrder("ORD-1", "Alice", "GOLD", "SALE15"))`. This one-element stream merges into the outer result. Contributed: 1 element.

**ORD-2** (`bob`, `null`): `getLoyaltyTier(bob)` → `"C2"` maps to `Optional.of("SILVER")` → `.stream()` → `Stream.of("SILVER")`. Inner: `order.getDiscount()` → `Optional.ofNullable(null)` → `Optional.empty()` → `.stream()` → `Stream.empty()`. The inner `flatMap` receives an empty stream → contributes nothing. Contributed: 0 elements.

**ORD-3** (`carol`, `"VIP10"`): `getLoyaltyTier(carol)` → `"C3"` has no mapping → `Optional.empty()` → `.stream()` → `Stream.empty()`. The outer `flatMap` lambda returns an empty stream directly. The inner `flatMap` is never evaluated. Contributed: 0 elements.

**ORD-4** (`alice`, `null`): `getLoyaltyTier(alice)` → `Optional.of("GOLD")` → `Stream.of("GOLD")`. Inner: `order.getDiscount()` → `Optional.empty()` → `Stream.empty()` → contributes nothing. Contributed: 0 elements.

**ORD-5** (`bob`, `"SALE15"`): `getLoyaltyTier(bob)` → `Optional.of("SILVER")` → `Stream.of("SILVER")`. Inner: `order.getDiscount()` → `Optional.of("SALE15")` → `Stream.of("SALE15")` → maps to `QualifiedOrder("ORD-5", "Bob", "SILVER", "SALE15")`. Contributed: 1 element.

The collector accumulates two `QualifiedOrder` instances. These are printed via `forEach`.

```
                                 ┌───────────────────────────────────┐
  orders.stream()                │   nested flatMap + Optional.stream │      collect(toList())
  ───────────────────────────────►│                                    │──────────────────────►
                                  │                                    │
  ORD-1 (alice, SALE15) ─────────┤  loyalty(GOLD).stream()            │
                                  │    → discount(SALE15).stream() ────┤  QualifiedOrder(ORD-1, Alice, GOLD, SALE15)
                                  │                                    │
  ORD-2 (bob, null) ─────────────┤  loyalty(SILVER).stream()          │
                                  │    → discount(null)→empty ────────┤  (skipped — no discount)
                                  │                                    │
  ORD-3 (carol, VIP10) ──────────┤  loyalty(empty).stream() → empty ──┤  (skipped — no tier)
                                  │                                    │
  ORD-4 (alice, null) ───────────┤  loyalty(GOLD).stream()            │
                                  │    → discount(null)→empty ────────┤  (skipped — no discount)
                                  │                                    │
  ORD-5 (bob, SALE15) ───────────┤  loyalty(SILVER).stream()          │
                                  │    → discount(SALE15).stream() ────┤  QualifiedOrder(ORD-5, Bob, SILVER, SALE15)
                                  └───────────────────────────────────┘
```

## 7. Gotchas & takeaways

> `Optional.stream()` is a **terminal** operation in the `Optional` API — after calling `.stream()`, you are in the `Stream` API and all subsequent operations are stream operations, not `Optional` operations. You cannot call `.orElse(...)` on the result of `.stream()`; you must use stream terminal operations like `.findFirst()`, `.collect()`, or `.forEach()`.

- `Optional.stream()` is a **one-way** conversion — there is no built-in `Stream.toOptional()` or `Stream.findOnly()`. To go back from a stream to an `Optional`, use `.findFirst()` (which returns `Optional<T>`) or `.reduce((a, b) -> { throw ... })` for a single-element expectation.
- The method is `stream()`, not `toStream()` — consistent with the naming of `Collection.stream()`, making `Optional` feel like a zero-or-one-element collection.
- Combined with `flatMap`, `Optional.stream()` provides the same "skip empties" behaviour as `Stream.ofNullable`, but works on `Optional` values rather than nullable references. The choice between them depends on whether the upstream API returns `Optional<T>` or a nullable `T`.
- There is no performance overhead — `Optional.stream()` on an empty `Optional` returns the same `Stream.empty()` singleton that all empty streams share, and on a present `Optional` it returns a lightweight one-element stream.
- `Optional.stream()` does not exist on the primitive optional types (`OptionalInt`, `OptionalLong`, `OptionalDouble`) in Java 9 — those gained their own `.stream()` methods in Java 10, returning `IntStream`, `LongStream`, and `DoubleStream` respectively. 