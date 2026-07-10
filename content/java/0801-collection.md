---
card: java
gi: 801
slug: collection
title: Collection
---

## 1. What it is

`Collection<T>` is the second-level root interface in the framework: it extends [`Iterable`](0800-iterable.md) and adds the operations every general-purpose group of elements should support — `add`, `remove`, `contains`, `size`, `isEmpty`, `clear`, plus bulk operations like `addAll`, `removeAll`, `retainAll`, and `stream()`. It is not implemented directly; instead `List`, `Set`, and `Queue` all extend it, each adding their own ordering and duplicate-handling rules on top. Writing code against `Collection<T>` rather than a specific type like `ArrayList<T>` means the code works unchanged whether the caller passes a list, a set, or a queue.

## 2. Why & when

Without a shared `Collection` interface, a utility method that wanted to "sum the elements" or "check if any element matches X" would need one overload per concrete type — one for `ArrayList`, one for `HashSet`, one for `LinkedList`. `Collection` exists so that code can be written once against the *behavior* every group-of-elements shares (you can add to it, ask its size, iterate it) and remain agnostic to whether duplicates are allowed or whether order is preserved. You reach for `Collection<T>` as a parameter or return type whenever a method genuinely doesn't care about order or uniqueness — only `List` or `Set` when those specific guarantees matter to the logic. The tradeoff is that `Collection` itself gives you no `get(index)` and no guaranteed uniqueness — those are exactly the guarantees `List` and `Set` add back in, respectively.

## 3. Core concept

```java
public interface Collection<T> extends Iterable<T> {
    boolean add(T t);
    boolean remove(Object o);
    boolean contains(Object o);
    int size();
    boolean isEmpty();
    void clear();
    boolean addAll(Collection<? extends T> c);
    boolean removeAll(Collection<?> c);
    boolean retainAll(Collection<?> c);
    boolean removeIf(Predicate<? super T> filter);
    Stream<T> stream();
    // ...and more
}
```

Both `ArrayList<Integer>` (a `List`) and `HashSet<Integer>` (a `Set`) satisfy this same interface, even though one allows duplicates and preserves insertion order while the other rejects duplicates and has no defined order. A method written as `void printSize(Collection<?> c)` works identically on either.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collection extends Iterable and is itself extended by List, Set, and Queue">
  <rect x="250" y="15" width="140" height="40" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="320" y="40" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Iterable&lt;T&gt;</text>

  <line x1="320" y1="55" x2="320" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#a801)"/>
  <defs><marker id="a801" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="240" y="90" width="160" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Collection&lt;T&gt;</text>

  <line x1="270" y1="130" x2="130" y2="165" stroke="#79c0ff" stroke-width="2" marker-end="url(#a801)"/>
  <line x1="320" y1="130" x2="320" y2="165" stroke="#79c0ff" stroke-width="2" marker-end="url(#a801)"/>
  <line x1="370" y1="130" x2="510" y2="165" stroke="#79c0ff" stroke-width="2" marker-end="url(#a801)"/>

  <rect x="50" y="170" width="120" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="195" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">List&lt;T&gt;</text>

  <rect x="260" y="170" width="120" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="195" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Set&lt;T&gt;</text>

  <rect x="460" y="170" width="120" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="195" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Queue&lt;T&gt;</text>
</svg>

*`Collection` is the shared parent of `List`, `Set`, and `Queue` — code against it, and any of the three works unchanged.*

## 5. Runnable example

Scenario: a small inventory audit utility that computes totals and filters items — written once against `Collection<String>`, then run unchanged against both a `List` (duplicates allowed, arrival order matters) and a `Set` (only distinct SKUs matter).

### Level 1 — Basic

```java
import java.util.*;

public class InventoryAuditBasic {

    static void printSummary(Collection<String> skus) {
        System.out.println("count: " + skus.size());
        System.out.println("contains SKU-42: " + skus.contains("SKU-42"));
    }

    public static void main(String[] args) {
        List<String> arrivals = new ArrayList<>(List.of("SKU-42", "SKU-7", "SKU-42"));
        Set<String> distinctSkus = new HashSet<>(arrivals);

        System.out.println("-- arrivals (List) --");
        printSummary(arrivals);

        System.out.println("-- distinct SKUs (Set) --");
        printSummary(distinctSkus);
    }
}
```

**How to run:** `java InventoryAuditBasic.java` (JDK 17+).

Expected output:
```
-- arrivals (List) --
count: 3
contains SKU-42: true
-- distinct SKUs (Set) --
count: 2
contains SKU-42: true
```

`printSummary` takes a `Collection<String>` parameter, so it accepts the `ArrayList` and the `HashSet` without any change or overload. The `List` reports `count: 3` because it kept the duplicate `SKU-42`; the `Set` reports `count: 2` because building it from the list silently dropped the duplicate.

### Level 2 — Intermediate

```java
import java.util.*;

public class InventoryAuditFiltered {

    static Collection<String> withoutDiscontinued(Collection<String> skus, Set<String> discontinued) {
        Collection<String> active = new ArrayList<>(skus); // defensive copy: don't mutate the caller's collection
        active.removeIf(discontinued::contains);
        return active;
    }

    public static void main(String[] args) {
        List<String> arrivals = new ArrayList<>(List.of("SKU-42", "SKU-7", "SKU-99", "SKU-42"));
        Set<String> discontinued = Set.of("SKU-99");

        Collection<String> active = withoutDiscontinued(arrivals, discontinued);
        System.out.println("active items: " + active);
        System.out.println("original arrivals untouched: " + arrivals);
    }
}
```

**How to run:** `java InventoryAuditFiltered.java`.

Expected output:
```
active items: [SKU-42, SKU-7, SKU-42]
original arrivals untouched: [SKU-42, SKU-7, SKU-99, SKU-42]
```

The real-world concern added: bulk filtering with `removeIf`, and doing it on a **defensive copy** rather than the caller's own collection — a method that silently mutates a `Collection` passed in by a caller is a classic source of hard-to-trace bugs, so `withoutDiscontinued` copies first and only ever mutates the copy.

### Level 3 — Advanced

```java
import java.util.*;

public class InventoryAuditImmutable {

    static Collection<String> withoutDiscontinued(Collection<String> skus, Set<String> discontinued) {
        Collection<String> active = new ArrayList<>(skus);
        active.removeIf(discontinued::contains);
        return active;
    }

    public static void main(String[] args) {
        // List.of(...) returns an IMMUTABLE Collection — a common production trap.
        Collection<String> arrivals = List.of("SKU-42", "SKU-7", "SKU-99");
        Set<String> discontinued = Set.of("SKU-99");

        try {
            arrivals.removeIf(discontinued::contains); // fails: List.of(...) doesn't support mutation
        } catch (UnsupportedOperationException e) {
            System.out.println("caught: cannot mutate an immutable Collection directly");
        }

        // The safe pattern: always copy an unknown Collection before mutating.
        Collection<String> active = withoutDiscontinued(arrivals, discontinued);
        System.out.println("active items: " + active);

        // retainAll performs set-style intersection on any two Collections, regardless of type.
        Collection<String> intersection = new ArrayList<>(arrivals);
        intersection.retainAll(discontinued);
        System.out.println("intersection with discontinued: " + intersection);
    }
}
```

**How to run:** `java InventoryAuditImmutable.java`.

Expected output:
```
caught: cannot mutate an immutable Collection directly
active items: [SKU-42, SKU-7]
intersection with discontinued: [SKU-99]
```

This adds the production-flavored hard case: many `Collection`-returning factory methods (`List.of`, `Set.of`, `Collections.unmodifiableList`) return objects that satisfy the `Collection` interface's *type* but throw `UnsupportedOperationException` on any mutating call. Code that accepts a generic `Collection<T>` parameter must never assume it's safe to mutate directly — the copy-then-mutate pattern from Level 2 is exactly what protects against this, and `retainAll` demonstrates that even set-style intersection logic works uniformly across `Collection`, independent of whether the concrete type underneath is a list or a set.

## 6. Walkthrough

Tracing `InventoryAuditImmutable.main`:

1. `arrivals` is created via `List.of(...)`, which returns an **immutable** `Collection<String>` — it satisfies every method signature in the interface, but several of them (`add`, `remove`, `removeIf`) throw at runtime instead of succeeding.
2. The first `try` block calls `arrivals.removeIf(...)` directly on that immutable collection; this throws `UnsupportedOperationException`, caught and reported — demonstrating that "is a `Collection`" does not imply "is mutable."
3. `withoutDiscontinued(arrivals, discontinued)` is called next. Inside it, `new ArrayList<>(skus)` copies every element of `arrivals` into a fresh, mutable `ArrayList`; `removeIf(discontinued::contains)` then safely removes `SKU-99` from that **copy**, leaving the original `arrivals` collection completely untouched.
4. The result, `active`, is printed: `[SKU-42, SKU-7]` — the discontinued SKU is gone, and no exception occurred, because the mutation happened on a private copy.
5. `intersection` is built the same defensive-copy way, then `retainAll(discontinued)` keeps only elements also present in `discontinued`, computing a set-style intersection (`[SKU-99]`) purely through the `Collection` interface — no cast to `List` or `Set` needed anywhere in this method.

## 7. Gotchas & takeaways

> **Gotcha:** many factory methods return objects typed as `Collection<T>` (or `List<T>`/`Set<T>`) that are **immutable** at runtime — `List.of(...)`, `Set.of(...)`, `Collections.unmodifiableList(...)`. The compiler will happily let you call `add`/`remove`/`removeIf` on them; only at runtime does `UnsupportedOperationException` reveal the mistake. Never assume a `Collection` parameter is safe to mutate without checking its origin or defensively copying first.

- `Collection<T>` extends [`Iterable<T>`](0800-iterable.md) and adds `add`, `remove`, `contains`, `size`, and bulk operations like `addAll`/`removeAll`/`retainAll`/`removeIf`.
- It is the shared parent of `List`, `Set`, and `Queue` — write against `Collection<T>` when a method genuinely doesn't care about ordering or duplicate rules.
- `retainAll` performs intersection, `removeAll` performs difference, and `addAll` performs union-like merging — all work identically regardless of the concrete `Collection` type underneath.
- Defensive-copy a `Collection` parameter before mutating it, since callers may pass an immutable one.
- Reach for the more specific `List` or `Set` interfaces instead when order or uniqueness guarantees actually matter to your logic.
