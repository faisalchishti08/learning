---
card: java
gi: 469
slug: bifunction-t-u-r
title: BiFunction<T,U,R>
---

## 1. What it is

`BiFunction<T, U, R>` is `Function<T, R>`'s two-argument sibling: "take one input of type `T` and one input of type `U`, produce one output of type `R`." Its single abstract method is `R apply(T t, U u)`. It exists for exactly the cases where a single-argument `Function` isn't enough — combining two values, comparing two values and producing something other than a `boolean`, or any transformation that genuinely needs two independent inputs.

## 2. Why & when

Plenty of real transformations take two inputs, not one — merging two values into a combined result, applying a key and a value together, computing something from a pair of related pieces of data. `BiFunction<T, U, R>` gives those cases the same first-class, reusable-as-a-value treatment `Function<T, R>` gives single-argument transformations, without forcing you to awkwardly bundle two arguments into one object just to fit `Function`'s one-argument shape.

You reach for `BiFunction` when an API explicitly calls for it — `Map.merge(key, value, BiFunction<V, V, V>)` for combining an existing value with a new one, `Map.replaceAll(BiFunction<K, V, V>)` for computing a new value from each key and its current value — or when you're designing your own method that needs the caller to combine two inputs into one result. It has an `andThen` `default` method too (chaining its result into a following single-argument `Function`), but no `compose`, since composing "before" a two-argument function isn't as naturally single-shaped.

## 3. Core concept

```java
import java.util.function.*;

BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
int sum = add.apply(3, 4); // 7

BiFunction<String, Integer, String> repeat = (text, times) -> text.repeat(times);
String result = repeat.apply("ab", 3); // "ababab"

// andThen: feed this BiFunction's result into a following single-argument Function
BiFunction<Integer, Integer, String> addAsText = add.andThen(n -> "sum=" + n);
System.out.println(addAsText.apply(3, 4)); // "sum=7"
```

`apply` takes exactly two arguments and produces one result — the two-input analogue of `Function.apply`'s single input.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A BiFunction takes two inputs, T and U, and produces one output of type R">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="25" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">T input</text>
  <rect x="30" y="80" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">U input</text>

  <rect x="255" y="50" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="72" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">BiFunction&lt;T,U,R&gt;</text>
  <text x="330" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">apply(t, u)</text>

  <rect x="490" y="55" width="120" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="82" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">R output</text>

  <line x1="140" y1="45" x2="250" y2="65" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="140" y1="100" x2="250" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="405" y1="77" x2="485" y2="77" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

Two inputs converge into one `BiFunction`, which produces a single output.

## 5. Runnable example

Scenario: merging price and quantity data into order totals — evolved from a basic two-argument computation, through `Map.merge` using a `BiFunction` to combine values when keys collide, to a small inventory system where a `BiFunction` combines a product's current stock with an incoming shipment.

### Level 1 — Basic

```java
import java.util.function.*;

public class BiFunctionBasic {
    public static void main(String[] args) {
        BiFunction<Double, Integer, Double> lineTotal = (unitPrice, quantity) -> unitPrice * quantity;

        System.out.println(lineTotal.apply(9.99, 3));
        System.out.println(lineTotal.apply(2.50, 10));
    }
}
```

**How to run:** `java BiFunctionBasic.java`

Expected output:
```
29.97
25.0
```

`lineTotal.apply(unitPrice, quantity)` runs the lambda with both arguments bound at once — `9.99 * 3 = 29.97`, `2.50 * 10 = 25.0`. `BiFunction<Double, Integer, Double>` means: takes a `Double` and an `Integer`, returns a `Double`.

### Level 2 — Intermediate

```java
import java.util.*;

public class BiFunctionMapMerge {
    public static void main(String[] args) {
        Map<String, Integer> inventory = new HashMap<>();
        inventory.put("widget", 50);
        inventory.put("gadget", 20);

        // Map.merge takes a key, a value, and a BiFunction<V, V, V> --
        // if the key already exists, the BiFunction combines the OLD and NEW values;
        // if the key is absent, the new value is simply inserted.
        inventory.merge("widget", 30, (oldStock, incoming) -> oldStock + incoming);
        inventory.merge("sprocket", 15, (oldStock, incoming) -> oldStock + incoming);

        System.out.println(inventory.get("widget"));
        System.out.println(inventory.get("sprocket"));
        System.out.println(inventory.get("gadget"));
    }
}
```

**How to run:** `java BiFunctionMapMerge.java`

Expected output:
```
80
15
20
```

The real-world concern this adds: `merge`'s `BiFunction<Integer, Integer, Integer>` only runs when the key **already exists** — for `"widget"` (already present with `50`), it combines old (`50`) and new (`30`) into `80`; for `"sprocket"` (absent), `merge` skips the `BiFunction` entirely and simply inserts `15` directly. `"gadget"` was untouched by either `merge` call, so it stays at its original `20`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class BiFunctionShipmentProcessor {
    record Stock(int quantity, String lastUpdated) {}

    static void applyShipment(Map<String, Stock> inventory, String product, int incoming, String date,
                               BiFunction<Stock, Integer, Stock> combiner) {
        Stock current = inventory.getOrDefault(product, new Stock(0, "never"));
        Stock updated = combiner.apply(current, incoming);
        inventory.put(product, updated);
        System.out.println(product + " -> qty=" + updated.quantity() + " updated=" + updated.lastUpdated());
    }

    public static void main(String[] args) {
        Map<String, Stock> inventory = new HashMap<>();
        inventory.put("widget", new Stock(50, "2026-01-01"));

        // The BiFunction combines a Stock RECORD with an incoming int quantity,
        // producing a NEW Stock -- records are immutable, so this must build a fresh one.
        BiFunction<Stock, Integer, Stock> receiveShipment =
                (stock, qty) -> new Stock(stock.quantity() + qty, "2026-07-09");

        applyShipment(inventory, "widget", 30, "2026-07-09", receiveShipment);
        applyShipment(inventory, "sprocket", 15, "2026-07-09", receiveShipment);
    }
}
```

**How to run:** `java BiFunctionShipmentProcessor.java`

Expected output:
```
widget -> qty=80 updated=2026-07-09
sprocket -> qty=15 updated=2026-07-09
```

This extends the pattern to production-flavoured data: instead of combining two plain `Integer`s, the `BiFunction<Stock, Integer, Stock>` combines an immutable `Stock` record with an incoming quantity, producing a **new** `Stock` (since records can't be mutated in place) that carries both the updated quantity and a fresh timestamp — the two-argument shape is exactly what's needed to bring "current state" and "incoming change" together into one combined result.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `inventory` starts with one entry: `"widget" -> Stock(50, "2026-01-01")`. `receiveShipment` is defined as a `BiFunction<Stock, Integer, Stock>`.

The first call, `applyShipment(inventory, "widget", 30, "2026-07-09", receiveShipment)`, enters `applyShipment`. `inventory.getOrDefault("widget", new Stock(0, "never"))` finds the existing entry and returns `Stock(50, "2026-01-01")` as `current` (the default `Stock(0, "never")` is not used, since `"widget"` is present). `combiner.apply(current, incoming)` calls `receiveShipment` with `stock = Stock(50, "2026-01-01")` and `qty = 30`: inside the lambda, `stock.quantity() + qty` computes `50 + 30 = 80`, and a brand-new `Stock(80, "2026-07-09")` is constructed and returned as `updated`. `inventory.put("widget", updated)` replaces the old entry with this new one, and the method prints `"widget -> qty=80 updated=2026-07-09"`.

The second call, `applyShipment(inventory, "sprocket", 15, "2026-07-09", receiveShipment)`, follows the same path, but `"sprocket"` is absent from `inventory`. `getOrDefault` returns the fallback `Stock(0, "never")` as `current`. `combiner.apply(current, incoming)` calls `receiveShipment` with `stock = Stock(0, "never")` and `qty = 15`: `stock.quantity() + qty = 0 + 15 = 15`, producing `Stock(15, "2026-07-09")`. `inventory.put("sprocket", updated)` inserts this as a brand-new entry, and the method prints `"sprocket -> qty=15 updated=2026-07-09"`.

```
applyShipment("widget", 30)   --> current=Stock(50,...) --combiner--> Stock(80, "2026-07-09")
applyShipment("sprocket", 15) --> current=Stock(0,"never") --combiner--> Stock(15, "2026-07-09")
```

Both calls run through the identical `applyShipment` logic and the identical `receiveShipment` `BiFunction` — the only difference is whether `current` came from an existing map entry or the `getOrDefault` fallback, and that alone was enough to produce the correct combined result in both cases.

## 7. Gotchas & takeaways

> `Map.merge`'s `BiFunction` is only invoked when the key is **already present**; passing `null` as the "new value" argument to `merge` is not the same as the key being absent, and has special removal semantics of its own (if the `BiFunction` result is `null`, the entry is removed). Mixing that up with plain `Map.put` behaviour is a common source of confusion — read `Map.merge`'s documentation carefully before relying on it for anything beyond simple accumulation.

- `BiFunction<T, U, R>` represents "two inputs, one output" — its single abstract method is `R apply(T t, U u)`.
- It has an `andThen` `default` method (chaining its result into a following `Function`) but no `compose`, unlike `Function<T, R>`.
- `Map.merge(key, value, BiFunction<V, V, V>)` is one of the most common places `BiFunction` appears — combining an existing value with an incoming one only when the key already exists.
- When the two inputs represent "current state" and "an incoming change," a `BiFunction` returning a brand-new combined result (especially with immutable types like records) is a clean, reusable pattern.
- If you find yourself needing a three-or-more-argument function, there's no built-in `TriFunction` in the JDK — at that point, consider bundling the extra arguments into a small record or defining your own functional interface instead.
