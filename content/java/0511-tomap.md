---
card: java
gi: 511
slug: tomap
title: toMap()
---

## 1. What it is

`Collectors.toMap(keyMapper, valueMapper)` collects a stream into a `Map<K, V>`, where `keyMapper` derives each entry's key and `valueMapper` derives its value from the stream's elements. If two elements produce the same key, the two-argument form throws `IllegalStateException` at that point — a duplicate key is treated as an error by default. A three-argument overload, `toMap(keyMapper, valueMapper, mergeFunction)`, adds a `BinaryOperator<V>` that resolves conflicts when duplicate keys occur, instead of throwing.

## 2. Why & when

`toMap` is how you build a lookup table from a stream — turning a list of objects into an ID-to-object map, a name-to-score map, or any other key/value association derived from your data. The two-argument form is the right default whenever keys are expected to be genuinely unique (like unique IDs) — if a duplicate slips through, that's usually a real bug worth surfacing loudly via the exception, rather than silently overwriting one entry with another. The three-argument form is for when duplicates are expected and you have a deliberate rule for resolving them (keep the first, keep the last, combine both, keep whichever is "better").

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Product(String sku, String name, double price) {}

List<Product> products = List.of(new Product("A1", "Widget", 9.99), new Product("B2", "Gadget", 19.99));

Map<String, Double> priceBySku = products.stream()
        .collect(Collectors.toMap(Product::sku, Product::price)); // {A1=9.99, B2=19.99}

// With duplicate keys expected -- keep the higher price
Map<String, Double> maxPriceByCategory = products.stream()
        .collect(Collectors.toMap(p -> "electronics", Product::price, Double::max));
```

`toMap` takes functions to derive the key and value from each element; without a merge function, colliding keys throw — with one, the merge function decides what happens on collision.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toMap derives a key and value from each element, throwing on duplicate keys unless a merge function is supplied">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Product(A1, 9.99)</text>
  <rect x="30" y="60" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="80" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Product(B2, 19.99)</text>
  <text x="230" y="55" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">toMap(sku, price)</text>
  <line x1="230" y1="65" x2="330" y2="65" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowTM)"/>
  <rect x="340" y="35" width="150" height="60" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">A1 -&gt; 9.99</text>
  <text x="415" y="80" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">B2 -&gt; 19.99</text>
  <defs><marker id="arrowTM" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each element contributes one key/value pair — `keyMapper` decides the key, `valueMapper` decides the value, and both together form each `Map` entry.

## 5. Runnable example

Scenario: building lookup structures from a product catalog — evolved from a basic unique-key lookup, through demonstrating the duplicate-key exception, to a version that resolves duplicates with an explicit merge rule.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ToMapBasic {
    record Product(String sku, String name, double price) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("A1", "Widget", 9.99),
                new Product("B2", "Gadget", 19.99),
                new Product("C3", "Gizmo", 14.50)
        );

        Map<String, Double> priceBySku = products.stream()
                .collect(Collectors.toMap(Product::sku, Product::price));

        System.out.println("Price of B2: $" + priceBySku.get("B2"));
        System.out.println("Total SKUs: " + priceBySku.size());
    }
}
```

**How to run:** `java ToMapBasic.java`

Expected output:
```
Price of B2: $19.99
Total SKUs: 3
```

`Collectors.toMap(Product::sku, Product::price)` builds a `Map<String, Double>` from `sku` to `price` — since every SKU here is unique, each product contributes exactly one clean entry, and looking up `"B2"` correctly returns `19.99`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ToMapDuplicateThrows {
    record Product(String sku, String name, double price) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("A1", "Widget", 9.99),
                new Product("A1", "Widget (clearance)", 4.99) // duplicate SKU -- a data problem
        );

        try {
            Map<String, Double> priceBySku = products.stream()
                    .collect(Collectors.toMap(Product::sku, Product::price));
            System.out.println("Built map: " + priceBySku);
        } catch (IllegalStateException e) {
            System.out.println("Failed as expected: duplicate key detected for SKU A1");
        }
    }
}
```

**How to run:** `java ToMapDuplicateThrows.java`

Expected output:
```
Failed as expected: duplicate key detected for SKU A1
```

The real-world concern this adds: real data isn't always clean — here, two `Product` entries share the SKU `"A1"`, which should never happen in a correct catalog. The two-argument `toMap` treats this as an error and throws `IllegalStateException` rather than silently picking one or the other, which is exactly the right default: a duplicate key here signals a genuine data integrity problem worth surfacing loudly, not a bug to paper over.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ToMapMergeFunction {
    record PriceQuote(String sku, double price, String source) {}

    public static void main(String[] args) {
        List<PriceQuote> quotes = List.of(
                new PriceQuote("A1", 9.99, "SupplierX"),
                new PriceQuote("A1", 8.49, "SupplierY"), // same SKU, different supplier quote
                new PriceQuote("B2", 19.99, "SupplierX"),
                new PriceQuote("A1", 9.25, "SupplierZ")
        );

        // Explicit rule: when SKUs collide, keep the LOWEST quoted price.
        Map<String, Double> bestPriceBySku = quotes.stream()
                .collect(Collectors.toMap(
                        PriceQuote::sku,
                        PriceQuote::price,
                        Double::min));

        new TreeMap<>(bestPriceBySku).forEach((sku, price) ->
                System.out.printf("%s: $%.2f%n", sku, price));
    }
}
```

**How to run:** `java ToMapMergeFunction.java`

Expected output:
```
A1: $8.49
B2: $19.99
```

This uses the three-argument `toMap` with an explicit merge rule (`Double::min`) instead of letting duplicates throw: when multiple `PriceQuote`s share the same SKU (`"A1"` appears three times, from three different suppliers), `Double::min` is applied to combine the colliding values, keeping only the lowest price seen for that key. `"B2"` has no collision, so it's unaffected — its single quote passes through unchanged.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `quotes` holds four entries: three for SKU `"A1"` (prices `9.99`, `8.49`, `9.25`, from different suppliers) and one for SKU `"B2"` (`19.99`).

`quotes.stream().collect(Collectors.toMap(PriceQuote::sku, PriceQuote::price, Double::min))` processes each quote in order. For the first, `PriceQuote("A1", 9.99, "SupplierX")`: key `"A1"` has no existing entry, so it's added directly — map now has `{"A1"=9.99}`.

For the second, `PriceQuote("A1", 8.49, "SupplierY")`: key `"A1"` *already* has an entry (`9.99`). The merge function `Double::min` is invoked with the existing value and the new value: `Double.min(9.99, 8.49) = 8.49`. The map's `"A1"` entry is updated to `8.49`.

For the third, `PriceQuote("B2", 19.99, "SupplierX")`: key `"B2"` has no existing entry, added directly — map now has `{"A1"=8.49, "B2"=19.99}`.

For the fourth, `PriceQuote("A1", 9.25, "SupplierZ")`: key `"A1"` already has an entry (`8.49` from the merge above). `Double.min(8.49, 9.25) = 8.49` — the existing, lower value wins again, so `"A1"`'s entry stays `8.49`.

```
PriceQuote(A1, 9.99) -> new key "A1"           -> {A1=9.99}
PriceQuote(A1, 8.49) -> collision: min(9.99,8.49)=8.49 -> {A1=8.49}
PriceQuote(B2, 19.99)-> new key "B2"           -> {A1=8.49, B2=19.99}
PriceQuote(A1, 9.25) -> collision: min(8.49,9.25)=8.49 -> {A1=8.49, B2=19.99}  (unchanged)
```

The final map is `{"A1"=8.49, "B2"=19.99}` — the lowest of the three `"A1"` quotes survived every collision. `new TreeMap<>(...)` orders the two SKUs alphabetically, and the `forEach` prints `"A1: $8.49"` then `"B2: $19.99"`.

## 7. Gotchas & takeaways

> The two-argument `Collectors.toMap(keyMapper, valueMapper)` throws `IllegalStateException` the moment it encounters a second element mapping to a key already present — this is a deliberate design choice, not an oversight, since silently dropping or overwriting data on unexpected key collisions can hide real bugs. Always use the three-argument form with an explicit merge function when duplicate keys are a genuine, expected possibility in your data.

- `Collectors.toMap(keyMapper, valueMapper)` builds a `Map<K, V>` from a stream, treating duplicate keys as an error by default.
- `Collectors.toMap(keyMapper, valueMapper, mergeFunction)` adds a `BinaryOperator<V>` that resolves collisions explicitly — common choices include `Double::min`/`Double::max`, keeping the first (`(a, b) -> a`) or last (`(a, b) -> b`) value seen, or combining both.
- Treat an unexpected `IllegalStateException` from the two-argument form as a signal of a genuine data problem (duplicate IDs, a bad assumption about uniqueness) rather than something to immediately silence with a merge function.
- Like `Collectors.toSet()`, the default `Map` implementation returned is unspecified (typically `HashMap`) — use `Collectors.toMap(..., ..., ..., TreeMap::new)` (a four-argument overload) if a specific `Map` implementation or ordering is required.
- `toMap` fully consumes the value at the moment each key is placed into the map — if a later merge is needed, the merge function receives the two *already-mapped* values, not the original stream elements.
