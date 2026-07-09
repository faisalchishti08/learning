---
card: java
gi: 493
slug: flatmap
title: flatMap()
---

## 1. What it is

`Stream.flatMap(function)` transforms each element of a stream into its own stream, then flattens all of those inner streams into one continuous output stream. Where `map` is strictly one-to-one, `flatMap` is one-to-*many* (or zero, or one) — each input element can contribute any number of output elements, and the nested structure disappears: a `Stream<List<T>>` becomes a plain `Stream<T>`, not a `Stream<Stream<T>>`.

## 2. Why & when

Real data is often nested: a list of orders, each containing a list of line items; a list of sentences, each containing a list of words; a list of `Optional<T>` values, each containing zero or one value. If you `map` over the outer collection, you get a stream *of* inner collections — useful sometimes, but usually you actually want to work with the inner elements directly, as one flat sequence. `flatMap` does that flattening in one step: map each outer element to its inner stream, then merge every inner stream into a single flat one.

You reach for `flatMap` whenever a mapping function would naturally return a collection, an `Optional`, or another stream instead of a single value — nested lists, splitting strings into words, or filtering out `Optional.empty()` results (as seen in [[stream-empty]]) without an extra `.filter(Optional::isPresent).map(Optional::get)` pair.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<List<Integer>> nested = List.of(List.of(1, 2), List.of(3, 4, 5));

List<Integer> flat = nested.stream()
        .flatMap(List::stream) // each inner List<Integer> becomes a Stream<Integer>, then merged
        .toList(); // [1, 2, 3, 4, 5]
```

`flatMap` calls its function once per outer element to get an inner stream, then concatenates all the inner streams together — the nesting is gone in the result.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="flatMap converts each element into its own stream, then flattens all inner streams into one">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="110" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="85" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">[1, 2]</text>
  <rect x="150" y="20" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="215" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">[3, 4, 5]</text>
  <text x="140" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">flatMap(List::stream)</text>
  <line x1="140" y1="55" x2="140" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowFM)"/>
  <rect x="30" y="90" width="42" height="30" fill="#1c2430" stroke="#6db33f"/><text x="51" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="78" y="90" width="42" height="30" fill="#1c2430" stroke="#6db33f"/><text x="99" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="126" y="90" width="42" height="30" fill="#1c2430" stroke="#6db33f"/><text x="147" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="174" y="90" width="42" height="30" fill="#1c2430" stroke="#6db33f"/><text x="195" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <rect x="222" y="90" width="42" height="30" fill="#1c2430" stroke="#6db33f"/><text x="243" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <defs><marker id="arrowFM" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two nested lists become one flat stream of five elements — the outer grouping structure disappears entirely.

## 5. Runnable example

Scenario: extracting all line-item names from a list of customer orders — evolved from flattening simple nested lists, through combining `flatMap` with `Optional` to drop missing values cleanly, to a version that flattens two levels of nesting at once.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class FlatMapBasic {
    record Order(String id, List<String> itemNames) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("O1", List.of("Book", "Pen")),
                new Order("O2", List.of("Laptop"))
        );

        List<String> allItems = orders.stream()
                .flatMap(order -> order.itemNames().stream())
                .toList();

        System.out.println("All items: " + allItems);
    }
}
```

**How to run:** `java FlatMapBasic.java`

Expected output:
```
All items: [Book, Pen, Laptop]
```

Each `Order` has its own `List<String>` of item names. `.flatMap(order -> order.itemNames().stream())` converts each order's item list into a stream, then merges all of them into one flat `Stream<String>` — the fact that `"Book"` and `"Pen"` came from one order and `"Laptop"` from another is no longer visible in the result; they're just three items in sequence.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class FlatMapOptional {
    record Order(String id, Optional<String> discountCode) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("O1", Optional.of("SAVE10")),
                new Order("O2", Optional.empty()),
                new Order("O3", Optional.of("WELCOME"))
        );

        List<String> activeCodes = orders.stream()
                .flatMap(order -> order.discountCode().stream()) // Optional::stream: 0 or 1 elements
                .toList();

        System.out.println("Active codes: " + activeCodes);
    }
}
```

**How to run:** `java FlatMapOptional.java`

Expected output:
```
Active codes: [SAVE10, WELCOME]
```

The real-world concern this adds: `Optional<String>.stream()` turns a present value into a one-element stream and an absent value into a zero-element stream (much like [[stream-empty]]). `.flatMap(order -> order.discountCode().stream())` uses that to silently drop orders with no discount code, with no explicit `if` check or `.filter(Optional::isPresent)` needed — `O2`'s empty `Optional` simply contributes nothing to the flattened result.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class FlatMapTwoLevels {
    record LineItem(String name, int quantity) {}
    record Order(String id, List<LineItem> items) {}
    record Customer(String name, List<Order> orders) {}

    public static void main(String[] args) {
        List<Customer> customers = List.of(
                new Customer("Alice", List.of(
                        new Order("O1", List.of(new LineItem("Book", 2), new LineItem("Pen", 5))),
                        new Order("O2", List.of(new LineItem("Laptop", 1)))
                )),
                new Customer("Bob", List.of(
                        new Order("O3", List.of(new LineItem("Mouse", 3)))
                ))
        );

        // Two levels of nesting: Customer -> Order -> LineItem, flattened to a single stream of names.
        List<String> allItemNames = customers.stream()
                .flatMap(customer -> customer.orders().stream())
                .flatMap(order -> order.items().stream())
                .map(LineItem::name)
                .toList();

        System.out.println("All purchased items: " + allItemNames);
    }
}
```

**How to run:** `java FlatMapTwoLevels.java`

Expected output:
```
All purchased items: [Book, Pen, Laptop, Mouse]
```

This adds a second level of nesting: `Customer` contains `Order`s, and each `Order` contains `LineItem`s — three levels deep in total. Chaining two `.flatMap(...)` calls flattens both levels in sequence: the first turns a `Stream<Customer>` into a `Stream<Order>`, the second turns that into a `Stream<LineItem>`, and a final `.map(LineItem::name)` extracts just the names — showing that `flatMap` composes cleanly across multiple levels of nesting, one level per call.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `customers` holds two `Customer` records: `Alice` with two orders (four line items total across both), and `Bob` with one order (one line item).

`customers.stream()` begins with a two-element `Stream<Customer>`. The first `.flatMap(customer -> customer.orders().stream())` calls the lambda once per customer: for `Alice`, `customer.orders().stream()` produces a stream of her two `Order` objects (`O1`, `O2`); for `Bob`, it produces a stream of his one `Order` (`O3`). Flattening these together produces a single `Stream<Order>` of three orders total: `O1, O2, O3`, in that order.

The second `.flatMap(order -> order.items().stream())` calls the lambda once per order: for `O1`, `order.items().stream()` produces a stream of its two `LineItem`s (`Book`, `Pen`); for `O2`, one `LineItem` (`Laptop`); for `O3`, one `LineItem` (`Mouse`). Flattening these together produces a single `Stream<LineItem>` of four items total: `Book, Pen, Laptop, Mouse`.

```
Customer Alice -> orders [O1, O2]  --\
Customer Bob   -> orders [O3]      --+--> flat Stream<Order>: [O1, O2, O3]

O1 -> items [Book, Pen]    --\
O2 -> items [Laptop]       ---+--> flat Stream<LineItem>: [Book, Pen, Laptop, Mouse]
O3 -> items [Mouse]        --/
```

`.map(LineItem::name)` then extracts just the `name` field from each `LineItem`, producing the flat `Stream<String>`: `"Book", "Pen", "Laptop", "Mouse"`. `.toList()` collects this into `allItemNames`, and it's printed as `[Book, Pen, Laptop, Mouse]` — all the way from a three-level-deep nested structure (customers containing orders containing line items) down to one flat list of item names, in the original traversal order.

## 7. Gotchas & takeaways

> Using `.map(...)` where `.flatMap(...)` was needed leaves you with a nested stream type you probably don't want — e.g. `orders.stream().map(order -> order.itemNames().stream())` produces a `Stream<Stream<String>>`, not the flat `Stream<String>` you likely intended. If your mapping function's return type is itself a stream, list, or `Optional` and you want a flat result, that's the signal to use `flatMap`, not `map`.

- `flatMap(function)` maps each element to its own stream, then flattens all those inner streams into one continuous output stream — one-to-many, not one-to-one like `map`.
- Nested collections (`Stream<List<T>>`) become flat (`Stream<T>`) via `flatMap(List::stream)`.
- `Optional<T>.stream()` combined with `flatMap` is a clean way to drop absent values from a stream without an explicit `filter`/`get` pair.
- Multiple levels of nesting can be flattened by chaining multiple `.flatMap(...)` calls, one per level, as shown with the three-level customer/order/line-item example.
- If a mapping function would return a collection, stream, or `Optional` instead of a plain value, that's the signal to use `flatMap` instead of `map` to avoid ending up with an unwanted nested stream type.
