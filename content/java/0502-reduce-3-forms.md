---
card: java
gi: 502
slug: reduce-3-forms
title: reduce() (3 forms)
---

## 1. What it is

`Stream.reduce(...)` combines all of a stream's elements into a single result by repeatedly applying a combining function. It comes in three overloads: `reduce(BinaryOperator<T> accumulator)` returns `Optional<T>` (no starting value, so an empty stream has nothing to return); `reduce(T identity, BinaryOperator<T> accumulator)` takes a starting value and returns `T` directly (an empty stream just returns the identity); `reduce(U identity, BiFunction<U,T,U> accumulator, BinaryOperator<U> combiner)` allows the accumulated type `U` to differ from the element type `T`, with the extra `combiner` needed to merge partial results when the stream is processed in parallel.

## 2. Why & when

`reduce` is the general-purpose "fold everything into one value" operation — summing numbers, concatenating strings, finding a maximum, building up any single aggregate result from a sequence of elements, one combination step at a time. Many common reductions already have dedicated, more readable methods (`sum()`, `max()`, `count()`), so `reduce` is typically reached for when the combination logic is custom and doesn't match one of those built-ins.

The two-argument form (with an identity) is the most common: it guarantees a non-`Optional` result and clearly states what an empty stream should produce. The one-argument form is used when there's no sensible identity value, and the caller is prepared to handle the `Optional` for the empty-stream case. The three-argument form only matters when reducing into a different accumulated type than the stream's element type — most everyday reductions never need it.

## 3. Core concept

```java
import java.util.stream.*;

// One-arg: no identity, returns Optional<T>
Optional<Integer> maybeSum = Stream.of(1, 2, 3).reduce((a, b) -> a + b);

// Two-arg: identity supplied, returns T directly
int sum = Stream.of(1, 2, 3).reduce(0, (a, b) -> a + b); // 6

// Three-arg: accumulated type (Integer) differs from element type (String)
int totalLength = Stream.of("a", "bb", "ccc")
        .reduce(0, (partialLen, s) -> partialLen + s.length(), Integer::sum);
```

Each form folds the stream down to one value by repeatedly combining an accumulated result with the next element — they differ in whether a starting value is required and whether the accumulated type can differ from the element type.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="reduce folds a stream into one value by repeatedly combining elements">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="40" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="45" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">0</text>
  <text x="90" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">+</text>
  <rect x="105" y="40" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="127" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <text x="160" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">=</text>
  <rect x="175" y="40" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="197" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <text x="230" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">+</text>
  <rect x="245" y="40" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="267" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">2</text>
  <text x="300" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">=</text>
  <rect x="315" y="40" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="337" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">3</text>
  <text x="370" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">+</text>
  <rect x="385" y="40" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="407" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">3</text>
  <text x="440" y="60" fill="#8b949e" font-size="12" font-family="sans-serif">=</text>
  <rect x="455" y="40" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="477" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">6</text>
  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">reduce(0, (acc, n) -&gt; acc + n): the accumulator carries forward through each element.</text>
</svg>

Each step combines the running accumulated value with the next element, carrying the result forward until only one final value remains.

## 5. Runnable example

Scenario: computing an order total from a shopping cart — evolved from a basic sum with the two-argument form, through finding the most expensive item with the one-argument form, to a version that aggregates into a different, richer accumulated type using the three-argument form.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ReduceBasic {
    record Item(String name, double price) {}

    public static void main(String[] args) {
        List<Item> cart = List.of(
                new Item("Book", 12.99),
                new Item("Pen", 1.50),
                new Item("Laptop", 999.00)
        );

        double total = cart.stream()
                .map(Item::price)
                .reduce(0.0, Double::sum); // identity 0.0, combine with Double::sum

        System.out.printf("Total: $%.2f%n", total);
    }
}
```

**How to run:** `java ReduceBasic.java`

Expected output:
```
Total: $1013.49
```

`.reduce(0.0, Double::sum)` starts with an identity of `0.0` and repeatedly combines it with each price: `0.0 + 12.99 = 12.99`, then `12.99 + 1.50 = 14.49`, then `14.49 + 999.00 = 1013.49`. The two-argument form guarantees a plain `double` result — no `Optional` unwrapping needed, and an empty cart would correctly total `$0.00`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ReduceOneArg {
    record Item(String name, double price) {}

    public static void main(String[] args) {
        List<Item> cart = List.of(
                new Item("Book", 12.99),
                new Item("Pen", 1.50),
                new Item("Laptop", 999.00)
        );

        // No sensible "identity" Item exists -- use the one-arg form and handle the empty case explicitly.
        Optional<Item> mostExpensive = cart.stream()
                .reduce((a, b) -> a.price() >= b.price() ? a : b);

        mostExpensive.ifPresentOrElse(
                item -> System.out.println("Most expensive: " + item.name() + " ($" + item.price() + ")"),
                () -> System.out.println("Cart is empty")
        );
    }
}
```

**How to run:** `java ReduceOneArg.java`

Expected output:
```
Most expensive: Laptop ($999.0)
```

The real-world concern this adds: there's no meaningful "identity `Item`" to start from (unlike `0.0` for a sum), so the one-argument form is used instead — it compares pairs of items, always keeping the pricier one, and folds down to a single `Item`. Because this form can't guarantee a result for an empty stream, it returns `Optional<Item>`, handled here with `.ifPresentOrElse(...)` rather than assuming a value is always present.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ReduceThreeArg {
    record Item(String name, double price, int quantity) {}
    record CartSummary(int totalItems, double totalCost) {
        CartSummary combine(CartSummary other) {
            return new CartSummary(this.totalItems + other.totalItems, this.totalCost + other.totalCost);
        }
    }

    public static void main(String[] args) {
        List<Item> cart = List.of(
                new Item("Book", 12.99, 2),
                new Item("Pen", 1.50, 5),
                new Item("Laptop", 999.00, 1)
        );

        // Accumulated type (CartSummary) differs from element type (Item) -- needs the 3-arg form.
        CartSummary summary = cart.stream()
                .reduce(
                        new CartSummary(0, 0.0),
                        (partial, item) -> new CartSummary(
                                partial.totalItems() + item.quantity(),
                                partial.totalCost() + item.price() * item.quantity()),
                        CartSummary::combine // only used if this stream ran in parallel
                );

        System.out.println("Items: " + summary.totalItems());
        System.out.printf("Total cost: $%.2f%n", summary.totalCost());
    }
}
```

**How to run:** `java ReduceThreeArg.java`

Expected output:
```
Items: 8
Total cost: $1032.48
```

This uses the three-argument form because the accumulated result (`CartSummary`, tracking both a running item count and a running cost) is a *different type* from the stream's elements (`Item`). The second argument (`(partial, item) -> ...`) folds one `Item` into the running `CartSummary`; the third argument (`CartSummary::combine`) would merge two partial `CartSummary` results together if the stream were processed in parallel — for this sequential stream it's never actually invoked, but the compiler requires it as part of the three-argument form's contract.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `cart` holds three items: `Book` (price `12.99`, quantity `2`), `Pen` (price `1.50`, quantity `5`), `Laptop` (price `999.00`, quantity `1`).

`cart.stream().reduce(new CartSummary(0, 0.0), (partial, item) -> ..., CartSummary::combine)` begins with the identity `CartSummary(0, 0)`. Processing `Book` first: the accumulator function computes `partial.totalItems() + item.quantity() = 0 + 2 = 2` and `partial.totalCost() + item.price() * item.quantity() = 0.0 + 12.99 * 2 = 25.98`, producing `CartSummary(2, 25.98)`.

Processing `Pen` next, with the running `CartSummary(2, 25.98)`: `totalItems = 2 + 5 = 7`, `totalCost = 25.98 + 1.50 * 5 = 25.98 + 7.50 = 33.48`, producing `CartSummary(7, 33.48)`.

Processing `Laptop` last, with the running `CartSummary(7, 33.48)`: `totalItems = 7 + 1 = 8`, `totalCost = 33.48 + 999.00 * 1 = 33.48 + 999.00 = 1032.48`.

```
start: CartSummary(0, 0.0)
+ Book  (12.99 x 2): items 0+2=2,  cost 0.0+25.98=25.98   -> CartSummary(2, 25.98)
+ Pen   (1.50 x 5):  items 2+5=7,  cost 25.98+7.50=33.48  -> CartSummary(7, 33.48)
+ Laptop(999.00 x 1):items 7+1=8,  cost 33.48+999.00=1032.48 -> CartSummary(8, 1032.48)
```

Since this stream is sequential (not parallel), `CartSummary::combine` (the third argument) is never actually invoked — there are no partial results from separate threads to merge. The final `summary` is `CartSummary(8, 1032.48)`, printed as `"Items: 8"` and `"Total cost: $1032.48"`.

## 7. Gotchas & takeaways

> The `combiner` function in the three-argument `reduce` form is **only** invoked when the stream is processed in parallel — on a sequential stream, it's part of the method signature but never actually called. It's easy to write a combiner that quietly does the wrong thing and never notice, since sequential testing won't exercise it; make sure the combiner performs a logically correct merge of two partial results before ever running the same reduction on a parallel stream.

- The one-argument `reduce(accumulator)` returns `Optional<T>` and requires no identity — used when there's no sensible starting value.
- The two-argument `reduce(identity, accumulator)` returns `T` directly and is the most common form, since the identity clearly defines the empty-stream result.
- The three-argument `reduce(identity, accumulator, combiner)` is needed only when the accumulated type differs from the element type; the `combiner` merges partial results and matters only for parallel execution.
- Many common reductions already have dedicated, clearer methods (`sum()`, `max()`, `count()`, `Collectors.joining()`) — prefer those over `reduce` when they exist, since they communicate intent more directly.
- The accumulator function passed to `reduce` should be associative and side-effect-free, since the order and grouping of combination steps aren't guaranteed to match simple left-to-right folding once parallelism is involved.
