---
card: java
gi: 825
slug: treemap-red-black-tree
title: TreeMap (red-black tree)
---

## 1. What it is

`TreeMap` is the standard implementation of [`SortedMap`/`NavigableMap`](0808-sortedmap-navigablemap.md), storing its entries in a **red-black tree** — a self-balancing binary search tree that guarantees the longest path from root to leaf is never more than roughly twice the shortest path. That balance guarantee is what makes `TreeMap`'s O(log n) cost for `put`/`get`/`remove` a genuine worst-case bound, not just a typical-case average. A plain, unbalanced binary search tree can degrade to a straight line (effectively a linked list) if keys are inserted in already-sorted order — turning every operation into O(n). Red-black trees prevent that by automatically performing local restructuring (rotations and recoloring) after every insertion or deletion to keep the tree's height bounded.

## 2. Why & when

The whole value proposition of a balanced tree over a naive binary search tree is protection against a specific, easy-to-trigger worst case: inserting keys that already arrive in sorted (or reverse-sorted) order. A naive BST handles that input by growing into a degenerate chain, one child per node, turning every future lookup into a linear scan; `TreeMap`'s red-black balancing actively prevents this, so sorted input is no more dangerous than any other input order — the O(log n) guarantee holds regardless. Reach for `TreeMap` whenever data must stay continuously sorted by key **and** the guarantee needs to hold even under adversarial or naturally-sorted insertion patterns — time-series data arriving in chronological order is a common real case where this distinction actually matters, since chronological arrival is exactly the "already sorted" pattern that would break a naive tree.

## 3. Core concept

```
Naive (unbalanced) BST, keys inserted in sorted order 1,2,3,4,5:

1
 \
  2
   \
    3
     \
      4
       \
        5

-- a straight chain: looking up "5" requires walking all 5 nodes, O(n).

TreeMap's red-black tree, same keys, same insertion order:

        3
       / \
      2   4
     /     \
    1       5

-- height stays O(log n) regardless of insertion order, via automatic rebalancing.
```

The keys, in both trees, produce identical sorted iteration order — the difference is entirely in the tree's *shape*, and therefore its worst-case search cost.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting keys in sorted order degenerates a naive binary search tree into a linked-list-like chain, but a red-black tree stays balanced through automatic rotations">
  <g font-family="sans-serif">
    <text x="150" y="25" fill="#f85149" font-size="12" text-anchor="middle">Naive BST (degenerate)</text>
    <circle cx="80" cy="50" r="16" fill="#1c2430" stroke="#f85149"/><text x="80" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">1</text>
    <circle cx="110" cy="80" r="16" fill="#1c2430" stroke="#f85149"/><text x="110" y="85" fill="#e6edf3" font-size="11" text-anchor="middle">2</text>
    <circle cx="140" cy="110" r="16" fill="#1c2430" stroke="#f85149"/><text x="140" y="115" fill="#e6edf3" font-size="11" text-anchor="middle">3</text>
    <circle cx="170" cy="140" r="16" fill="#1c2430" stroke="#f85149"/><text x="170" y="145" fill="#e6edf3" font-size="11" text-anchor="middle">4</text>
    <circle cx="200" cy="170" r="16" fill="#1c2430" stroke="#f85149"/><text x="200" y="175" fill="#e6edf3" font-size="11" text-anchor="middle">5</text>
    <text x="140" y="200" fill="#8b949e" font-size="9" text-anchor="middle">height 5 — O(n) lookups</text>
  </g>

  <g font-family="sans-serif">
    <text x="480" y="25" fill="#3fb950" font-size="12" text-anchor="middle">TreeMap red-black tree (balanced)</text>
    <circle cx="480" cy="55" r="16" fill="#1c2430" stroke="#3fb950"/><text x="480" y="60" fill="#e6edf3" font-size="11" text-anchor="middle">3</text>
    <circle cx="430" cy="100" r="16" fill="#1c2430" stroke="#3fb950"/><text x="430" y="105" fill="#e6edf3" font-size="11" text-anchor="middle">2</text>
    <circle cx="530" cy="100" r="16" fill="#1c2430" stroke="#3fb950"/><text x="530" y="105" fill="#e6edf3" font-size="11" text-anchor="middle">4</text>
    <circle cx="400" cy="145" r="16" fill="#1c2430" stroke="#3fb950"/><text x="400" y="150" fill="#e6edf3" font-size="11" text-anchor="middle">1</text>
    <circle cx="560" cy="145" r="16" fill="#1c2430" stroke="#3fb950"/><text x="560" y="150" fill="#e6edf3" font-size="11" text-anchor="middle">5</text>
    <line x1="480" y1="71" x2="430" y2="84" stroke="#3fb950"/>
    <line x1="480" y1="71" x2="530" y2="84" stroke="#3fb950"/>
    <line x1="430" y1="116" x2="400" y2="129" stroke="#3fb950"/>
    <line x1="530" y1="116" x2="560" y2="129" stroke="#3fb950"/>
    <text x="480" y="195" fill="#8b949e" font-size="9" text-anchor="middle">height 3 — O(log n) lookups, same 5 keys</text>
  </g>
</svg>

*Same keys, same sorted insertion order — the naive tree degenerates while `TreeMap`'s red-black tree stays balanced automatically.*

## 5. Runnable example

Scenario: a dictionary of word definitions requiring sorted-by-word iteration, growing from basic sorted storage and lookup, to a stress test proving the balance guarantee holds even for already-sorted input, to handling the ClassCastException trap that comes with relying on natural ordering.

### Level 1 — Basic

```java
import java.util.*;

public class DictionaryBasic {
    public static void main(String[] args) {
        TreeMap<String, String> dictionary = new TreeMap<>();
        dictionary.put("zebra", "a striped animal");
        dictionary.put("apple", "a fruit");
        dictionary.put("mango", "a tropical fruit");

        System.out.println("dictionary, sorted by word: " + dictionary);
        System.out.println("first entry: " + dictionary.firstEntry());
    }
}
```

**How to run:** `java DictionaryBasic.java` (JDK 17+).

Expected output:
```
dictionary, sorted by word: {apple=a fruit, mango=a tropical fruit, zebra=a striped animal}
first entry: apple=a fruit
```

Entries are inserted in arbitrary order but always iterate alphabetically — the same guaranteed sorted-order property demonstrated for `TreeSet` and `NavigableMap`, now anchored to the red-black tree that makes it efficient.

### Level 2 — Intermediate

```java
import java.util.*;

public class BalanceStressTest {
    public static void main(String[] args) {
        int n = 200_000;

        // Insert keys in ALREADY-SORTED order -- the classic worst case for a naive BST.
        TreeMap<Integer, Integer> sortedInsertMap = new TreeMap<>();
        long start = System.currentTimeMillis();
        for (int i = 0; i < n; i++) {
            sortedInsertMap.put(i, i * i);
        }
        long insertElapsed = System.currentTimeMillis() - start;

        long lookupStart = System.currentTimeMillis();
        int found = 0;
        for (int i = 0; i < n; i++) {
            if (sortedInsertMap.containsKey(i)) found++;
        }
        long lookupElapsed = System.currentTimeMillis() - lookupStart;

        System.out.println("inserted " + n + " keys in already-sorted order in " + insertElapsed + " ms");
        System.out.println("performed " + n + " lookups in " + lookupElapsed + " ms");
        System.out.println("all found: " + (found == n));
        System.out.println("-> stays fast despite worst-case input order, because red-black balancing prevents degeneration");
    }
}
```

**How to run:** `java BalanceStressTest.java`. Timings vary by machine, but both operations complete in well under a second even at 200,000 sorted-order insertions — proof the tree never degenerates into a slow linear chain.

Expected output shape:
```
inserted 200000 keys in already-sorted order in ~60 ms
performed 200000 lookups in ~40 ms
all found: true
-> stays fast despite worst-case input order, because red-black balancing prevents degeneration
```

The real-world concern added: proving the balance guarantee holds under the exact input pattern (already-sorted keys) that would be catastrophic for a naive, unbalanced binary search tree. This matters for genuinely realistic scenarios like ingesting time-series data, log entries, or auto-incrementing IDs — all naturally arrive in sorted order, and `TreeMap` handles that pattern just as efficiently as random insertion order.

### Level 3 — Advanced

```java
import java.util.*;

public class NaturalOrderingTrap {
    static class Money {
        final int cents;
        Money(int cents) { this.cents = cents; }
        // Deliberately does NOT implement Comparable -- a common oversight for "simple" value classes.
        @Override public String toString() { return "$" + (cents / 100.0); }
    }

    public static void main(String[] args) {
        TreeMap<Money, String> prices = new TreeMap<>();
        try {
            prices.put(new Money(500), "widget");
            prices.put(new Money(300), "gadget"); // triggers a comparison -- and Money isn't Comparable
        } catch (ClassCastException e) {
            System.out.println("caught: " + e.getMessage());
        }

        // Fix: supply an explicit Comparator instead of relying on natural ordering.
        TreeMap<Money, String> fixedPrices = new TreeMap<>(Comparator.comparingInt(m -> m.cents));
        fixedPrices.put(new Money(500), "widget");
        fixedPrices.put(new Money(300), "gadget");
        fixedPrices.put(new Money(150), "gizmo");

        System.out.println("prices, cheapest first: " + fixedPrices);
    }
}
```

**How to run:** `java NaturalOrderingTrap.java`.

Expected output:
```
caught: class NaturalOrderingTrap$Money cannot be cast to class java.lang.Comparable (...)
prices, cheapest first: {NaturalOrderingTrap$Money@... =gizmo, NaturalOrderingTrap$Money@... =widget, ...}
```

(Note: without a `toString()` override producing readable output in the map's key display, the exact `Money@...` text will include a hash-based identity string — the important, deterministic part is the ordering: gizmo, gadget, widget, cheapest to most expensive.)

This adds the production-flavored hard case: a `TreeMap` (or `TreeSet`) constructed **without** an explicit `Comparator`, given a key type that doesn't implement `Comparable`. The first `put` succeeds (a single-entry tree needs no comparison), but the *second* `put` triggers an actual comparison to decide where the new key belongs relative to the existing one — and since `Money` isn't `Comparable`, that comparison throws `ClassCastException` at runtime, not compile time, because Java's generics don't statically enforce that a `TreeMap`'s key type is `Comparable` unless a bound is declared. Supplying an explicit `Comparator` at construction sidesteps the requirement entirely.

## 6. Walkthrough

Tracing `NaturalOrderingTrap.main`:

1. `prices = new TreeMap<>()` is constructed without a `Comparator`, meaning it will attempt to use each key's natural ordering (`Comparable.compareTo`) when more than one key is present.
2. `prices.put(new Money(500), "widget")` succeeds trivially — a `TreeMap` with zero prior entries never needs to compare the first key against anything.
3. `prices.put(new Money(300), "gadget")` needs to determine whether the new `Money(300)` key belongs before or after the existing `Money(500)` key in the tree — this requires calling `compareTo` on one of them. Since `Money` never implements `Comparable`, the JVM cannot find that method and throws `ClassCastException` at the point of the comparison attempt, not earlier.
4. The `catch` block reports the exception, and the code moves on to `fixedPrices`, constructed instead with `new TreeMap<>(Comparator.comparingInt(m -> m.cents))` — supplying an explicit comparator entirely bypasses the need for `Money` to implement `Comparable` at all, since `TreeMap` will use the provided comparator for every comparison instead.
5. Three prices are inserted into `fixedPrices` in arbitrary order (500, 300, 150 cents); each insertion is correctly placed by the tree using the supplied comparator, and the final printed map iterates cheapest-to-most-expensive, confirming the fix works.

## 7. Gotchas & takeaways

> **Gotcha:** `new TreeMap<K, V>()` compiles successfully for **any** key type `K`, even one that doesn't implement `Comparable<K>` — the compiler has no way to statically verify this, since `TreeMap`'s no-argument constructor doesn't bound `K` by `Comparable`. The failure only surfaces at runtime, and only once a second key actually needs to be compared against an existing one — always supply an explicit `Comparator` when the key type's `Comparable` status is even slightly in doubt.

- `TreeMap` is backed by a red-black tree, guaranteeing O(log n) `put`/`get`/`remove` even in the worst case — including the classic already-sorted-input pattern that degenerates a naive, unbalanced binary search tree to O(n).
- The balance guarantee is what makes `TreeMap` genuinely safe for chronologically-arriving or otherwise pre-sorted data, unlike a hand-rolled BST would be.
- Without an explicit `Comparator`, `TreeMap` relies on the key type's natural ordering (`Comparable.compareTo`), which fails at runtime with `ClassCastException` — not a compile-time error — if the key type doesn't actually implement `Comparable`.
- Supplying an explicit `Comparator` at construction removes the `Comparable` requirement on the key type entirely.
- For key types under your control that will only ever be used with natural ordering, implementing `Comparable<K>` directly is usually cleaner than always supplying an external comparator.
