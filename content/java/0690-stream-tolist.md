---
card: java
gi: 690
slug: stream-tolist
title: Stream.toList()
---

## 1. What it is

**Java 16** added a new default method, **`Stream.toList()`** (JEP-less small enhancement, delivered via the JDK's regular API evolution), as a concise shorthand for collecting a stream into an unmodifiable `List`. Before this, the idiomatic way to materialize a stream into a list was `stream.collect(Collectors.toList())` — correct, but verbose for something so common, and — a subtlety many developers didn't realize — `Collectors.toList()` never actually guaranteed an *unmodifiable* list (it happened to return a mutable `ArrayList` in practice). `stream.toList()` is shorter to write and returns a list that is explicitly, guaranteed **unmodifiable**.

## 2. Why & when

Collecting a stream's results into a `List` is one of the single most common terminal operations in everyday Java code — filtering, mapping, and gathering results happens constantly, and `.collect(Collectors.toList())` was a long, slightly awkward incantation for something so routine. Beyond brevity, the switch to an explicitly unmodifiable result addresses a real, if subtle, correctness gap: code that called `Collectors.toList()` and then, based on that success, assumed it could safely mutate the result (add, remove, or sort in place) was relying on undocumented, implementation-specific behavior rather than a real API contract. `Stream.toList()` makes the contract explicit — attempting to mutate the returned list always throws `UnsupportedOperationException`, so any accidental mutation is caught immediately and loudly rather than silently working "by accident." Reach for `.toList()` any time you just need a materialized list from a stream pipeline and don't need a specific mutable list implementation, a `Collector` downstream combinator, or a list you intend to modify afterward.

## 3. Core concept

```java
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

// Before Java 16: verbose, and the mutability of the result was never actually guaranteed
List<Integer> old = Stream.of(1, 2, 3).collect(Collectors.toList());

// Java 16+: concise, and explicitly, guaranteed unmodifiable
List<Integer> modern = Stream.of(1, 2, 3).toList();

modern.add(4); // throws UnsupportedOperationException — the guarantee, enforced
```

`.toList()` is a plain instance method on `Stream<T>` itself — no `Collectors` import, no `.collect(...)` wrapper needed.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.collect(Collectors.toList()) produces a mutable list by accident of implementation; Stream.toList() produces a guaranteed unmodifiable list">
  <rect x="20" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="45" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">.collect(Collectors.toList())</text>
  <text x="155" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">happens to return ArrayList</text>
  <text x="155" y="95" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">mutability NOT part of the contract</text>

  <rect x="330" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">.toList()</text>
  <text x="465" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">returns unmodifiable List</text>
  <text x="465" y="95" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">immutability IS the guarantee</text>
</svg>

Both produce a `List<T>` with the same elements, but only one makes the immutability an explicit, enforced part of the API contract.

## 5. Runnable example

Scenario: processing a list of order totals — first the basic filter-map-toList pipeline, then discovering (via a caught exception) that the result really is unmodifiable, then a slightly larger reporting pipeline that uses `.toList()` at each stage of a multi-step transformation to keep intermediate results safely immutable.

### Level 1 — Basic

```java
// File: ToListBasic.java
import java.util.List;

public class ToListBasic {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6);

        List<Integer> evenSquares = numbers.stream()
                .filter(n -> n % 2 == 0)
                .map(n -> n * n)
                .toList();

        System.out.println(evenSquares);
    }
}
```

**How to run:** `java ToListBasic.java`

Expected output:
```
[4, 16, 36]
```

### Level 2 — Intermediate

```java
// File: ToListImmutability.java
import java.util.List;

public class ToListImmutability {
    public static void main(String[] args) {
        List<String> names = List.of("Ada", "Grace", "Alan").stream()
                .map(String::toUpperCase)
                .toList();

        System.out.println("Result: " + names);

        try {
            names.add("Linus");
        } catch (UnsupportedOperationException e) {
            System.out.println("Mutation rejected: " + e.getClass().getSimpleName());
        }

        try {
            names.set(0, "REPLACED");
        } catch (UnsupportedOperationException e) {
            System.out.println("In-place replace rejected: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java ToListImmutability.java`

Expected output:
```
Result: [ADA, GRACE, ALAN]
Mutation rejected: UnsupportedOperationException
In-place replace rejected: UnsupportedOperationException
```

This demonstrates the guaranteed contract directly: both `add` and `set` — two entirely different mutation methods — are rejected, confirming `.toList()`'s result is unmodifiable in every sense, not just "happens not to support the one method you tried."

### Level 3 — Advanced

```java
// File: OrderReport.java
import java.util.List;

public class OrderReport {
    record Order(String customer, double total, boolean paid) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("Alice", 120.50, true),
                new Order("Bob", 45.00, false),
                new Order("Carol", 300.00, true),
                new Order("Dave", 15.75, false)
        );

        List<Order> paidOrders = orders.stream()
                .filter(Order::paid)
                .toList();

        List<String> paidCustomerNames = paidOrders.stream()
                .map(Order::customer)
                .toList();

        double totalPaid = paidOrders.stream()
                .mapToDouble(Order::total)
                .sum();

        System.out.println("Paid orders: " + paidOrders.size());
        System.out.println("Paid customers: " + paidCustomerNames);
        System.out.printf("Total paid amount: $%.2f%n", totalPaid);

        try {
            paidOrders.clear();
        } catch (UnsupportedOperationException e) {
            System.out.println("paidOrders is immutable, as expected: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java OrderReport.java`

Expected output:
```
Paid orders: 2
Paid customers: [Alice, Carol]
Total paid amount: $420.50
paidOrders is immutable, as expected: UnsupportedOperationException
```

Level 3 chains `.toList()` across a small multi-stage report: filtering to `paidOrders`, deriving `paidCustomerNames` from that already-immutable list, and summing totals — each intermediate result is safely shareable across the rest of the method (or handed off to other code) without any risk that some other part of the pipeline accidentally mutates a shared list in place.

## 6. Walkthrough

1. `main` builds an immutable `List<Order>` of four orders via `List.of(...)`, mixing paid and unpaid orders with varying totals.
2. `orders.stream().filter(Order::paid).toList()` creates a stream, filters it down to only orders where the record's `paid()` accessor returns `true` (Alice and Carol), and immediately materializes the filtered results into a new, unmodifiable `List<Order>` assigned to `paidOrders`.
3. `paidOrders.stream().map(Order::customer).toList()` starts a **second**, independent stream pipeline over `paidOrders` (the already-materialized, filtered list from step 2), extracts each order's `customer()` name, and again collects the results via `.toList()` into `paidCustomerNames` — demonstrating that `.toList()`'s output is a perfectly normal `List<T>` you can immediately re-stream, just one that rejects mutation.
4. `paidOrders.stream().mapToDouble(Order::total).sum()` runs a third pipeline, this time using the primitive-specialized `mapToDouble` (avoiding boxing overhead) to extract each paid order's `total()` and sum them via the terminal `.sum()` operation, producing `120.50 + 300.00 = 420.50`.
5. The three derived values (`paidOrders.size()`, `paidCustomerNames`, `totalPaid`) are printed in turn, giving a small report: 2 paid orders, from Alice and Carol, totaling $420.50.
6. Finally, `paidOrders.clear()` is attempted inside a `try` block — since `paidOrders` came from `.toList()`, this immediately throws `UnsupportedOperationException` rather than silently emptying the list (which would be a serious bug if `paidOrders` were still needed elsewhere after this line), and the `catch` block confirms the expected exception type was thrown.

```
orders (List<Order>, 4 entries)
      │ .stream().filter(Order::paid).toList()
      ▼
paidOrders (unmodifiable List<Order>, 2 entries: Alice, Carol)
      │ .stream().map(Order::customer).toList()      │ .stream().mapToDouble(Order::total).sum()
      ▼                                                ▼
paidCustomerNames = [Alice, Carol]              totalPaid = 420.50
```

## 7. Gotchas & takeaways

> `Stream.toList()`'s unmodifiable guarantee is a **behavioral change**, not just a convenience — code migrating from `.collect(Collectors.toList())` to `.toList()` that previously relied (even accidentally) on being able to mutate the result will now fail fast with `UnsupportedOperationException` at the first mutation attempt. This is almost always a good thing to discover immediately rather than later, but it does mean a mechanical find-and-replace migration isn't always safe without checking each call site.

- `.toList()` is a plain `Stream<T>` instance method — no `import java.util.stream.Collectors;` needed, unlike the older idiom.
- The returned list explicitly forbids `null` elements in some collector-based paths but `.toList()` itself does permit `null` elements (unlike `List.of(...)`, which forbids them) — don't conflate the two "immutable list" APIs; they have subtly different null-handling rules.
- If you specifically need a **mutable** list from a stream, `.collect(Collectors.toCollection(ArrayList::new))` (or continuing to use `.collect(Collectors.toList())`, understanding its mutability was never actually guaranteed) remains the way to get one.
- `.toList()`'s brevity makes it easy to chain multiple stream stages cleanly, as shown in Level 3 — each stage's output is immediately safe to re-stream, pass to other methods, or store, without needing to worry about accidental downstream mutation.
- Because the result is unmodifiable, don't attempt in-place operations like `Collections.sort(result)` on it — sort via the stream pipeline itself (`.sorted(...)` before `.toList()`) or copy into a mutable collection first if in-place sorting is truly needed.
