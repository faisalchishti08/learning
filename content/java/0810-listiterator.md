---
card: java
gi: 810
slug: listiterator
title: ListIterator
---

## 1. What it is

`ListIterator<T>` is the [`List`](0802-list.md)-specific extension of [`Iterator`](0809-iterator.md), obtained via `list.listIterator()`. It adds three capabilities plain `Iterator` doesn't have: **bidirectional traversal** (`hasPrevious()`/`previous()` alongside `hasNext()`/`next()`), **in-place replacement** (`set(value)`, replacing the element most recently returned by `next()`/`previous()`), and **mid-traversal insertion** (`add(value)`, inserting immediately before the position `next()` would return). It also exposes `nextIndex()`/`previousIndex()` to check position without moving. `listIterator(int index)` starts traversal from an arbitrary position instead of the beginning.

## 2. Why & when

A plain `Iterator` can only look forward and can only remove — it has no way to *change* an element in place or *insert* a new one at the current position without either restarting the loop or dropping down to error-prone index arithmetic on the list directly. `ListIterator` exists for exactly the class of operation that needs to walk a list once while both reading and rewriting it — applying a discount to every price in place, inserting a separator after items matching a condition, or walking backward to undo a forward pass. Reach for it whenever a single traversal needs to mutate elements (not just remove them) or needs to move in both directions; for read-only or removal-only traversal, plain `Iterator` (or a for-each loop) remains simpler.

## 3. Core concept

```java
List<Integer> prices = new ArrayList<>(List.of(10, 20, 30));
ListIterator<Integer> it = prices.listIterator();

while (it.hasNext()) {
    int price = it.next();
    it.set(price - 5); // replace the element just returned by next()
}
// prices is now [5, 15, 25]

while (it.hasPrevious()) {
    int price = it.previous(); // walk backward over the same list
    System.out.println(price);
}
// prints 25, 15, 5 — reverse order, using the SAME iterator that just walked forward
```

Because the same `ListIterator` instance tracks a single cursor position, walking forward to the end and then calling `hasPrevious()`/`previous()` repeatedly retraces the list in reverse without creating a new iterator.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ListIterator's cursor sits between elements and can move forward with next or backward with previous, plus set and add at the current position">
  <g font-family="sans-serif">
    <rect x="60" y="70" width="80" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="100" y="97" fill="#e6edf3" font-size="11" text-anchor="middle">10</text>
    <rect x="160" y="70" width="80" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="200" y="97" fill="#e6edf3" font-size="11" text-anchor="middle">20</text>
    <rect x="260" y="70" width="80" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="300" y="97" fill="#e6edf3" font-size="11" text-anchor="middle">30</text>
  </g>

  <line x1="200" y1="60" x2="200" y2="140" stroke="#79c0ff" stroke-width="2"/>
  <text x="200" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">cursor</text>

  <text x="140" y="155" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">previous() ←</text>
  <text x="260" y="155" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">→ next()</text>

  <text x="470" y="90" fill="#e6edf3" font-size="10" font-family="sans-serif">set(v)  — replace last returned element</text>
  <text x="470" y="110" fill="#e6edf3" font-size="10" font-family="sans-serif">add(v)  — insert right at the cursor</text>
</svg>

*The cursor sits between elements; `next()`/`previous()` move it, while `set()`/`add()` act at its current position.*

## 5. Runnable example

Scenario: applying a store-wide price adjustment, growing from a basic forward pass with in-place edits to a bidirectional discount-then-verify pass to inserting sale markers mid-traversal.

### Level 1 — Basic

```java
import java.util.*;

public class PriceEditBasic {
    public static void main(String[] args) {
        List<Integer> prices = new ArrayList<>(List.of(10, 20, 30, 40));

        ListIterator<Integer> it = prices.listIterator();
        while (it.hasNext()) {
            int price = it.next();
            it.set(price - 5); // flat $5 discount, applied in place
        }

        System.out.println("discounted prices: " + prices);
    }
}
```

**How to run:** `java PriceEditBasic.java` (JDK 17+).

Expected output:
```
discounted prices: [5, 15, 25, 35]
```

`it.set(price - 5)` replaces the element `next()` just returned, directly in the backing list — no separate `prices.set(index, value)` call or manual index tracking needed.

### Level 2 — Intermediate

```java
import java.util.*;

public class PriceEditBidirectional {
    public static void main(String[] args) {
        List<Integer> prices = new ArrayList<>(List.of(10, 20, 30, 40));

        ListIterator<Integer> it = prices.listIterator();
        while (it.hasNext()) {
            int price = it.next();
            it.set(price - 5);
        }
        System.out.println("after forward discount pass: " + prices);

        // Walk backward with the SAME iterator to verify no price went negative.
        boolean anyNegative = false;
        while (it.hasPrevious()) {
            int price = it.previous();
            if (price < 0) {
                anyNegative = true;
                it.set(0); // clamp to zero in place, during the backward pass
            }
        }
        System.out.println("after backward verification pass: " + prices);
        System.out.println("any price had to be clamped: " + anyNegative);
    }
}
```

**How to run:** `java PriceEditBidirectional.java`.

Expected output:
```
after forward discount pass: [5, 15, 25, 35]
after backward verification pass: [5, 15, 25, 35]
any price had to be clamped: false
```

The real-world concern added: reusing the **same** `ListIterator` for a return pass, walking backward from wherever the forward pass left the cursor (at the end, after the last `next()`), verifying and — had any price gone negative — correcting it with `set()` during the backward walk too. `set()` works identically regardless of which direction most recently moved the cursor, since it always targets "the last element returned by either `next()` or `previous()`."

### Level 3 — Advanced

```java
import java.util.*;

public class PriceEditWithMarkers {
    public static void main(String[] args) {
        List<String> priceLabels = new ArrayList<>(List.of("$5", "$45", "$15", "$60", "$25"));

        ListIterator<String> it = priceLabels.listIterator();
        while (it.hasNext()) {
            String label = it.next();
            int value = Integer.parseInt(label.substring(1));
            if (value >= 40) {
                it.add("** SALE **"); // insert right after the current position, before continuing
            }
        }

        System.out.println("labels with sale markers inserted: " + priceLabels);
    }
}
```

**How to run:** `java PriceEditWithMarkers.java`.

Expected output:
```
labels with sale markers inserted: [$5, $45, ** SALE **, $15, $60, ** SALE **, $25]
```

This adds the production-flavored hard case: **inserting new elements mid-traversal** with `add()`, which places the new element immediately before the position the next `next()` call would return — so the cursor ends up positioned right after the newly inserted element, and the loop naturally continues past it without re-visiting it or the element that triggered the insertion. This is something a plain `Iterator` (or a for-each loop) simply cannot do: neither supports adding elements during traversal at all.

## 6. Walkthrough

Tracing `PriceEditWithMarkers.main`:

1. `it = priceLabels.listIterator()` starts a cursor positioned before index 0, over `["$5", "$45", "$15", "$60", "$25"]`.
2. First iteration: `it.next()` returns `"$5"`, advancing the cursor to sit between index 0 and 1. Parsed value `5` is less than `40`, so no insertion happens.
3. Second iteration: `it.next()` returns `"$45"`, advancing the cursor between index 1 and 2. Parsed value `45` is `>= 40`, so `it.add("** SALE **")` inserts the marker string **at the cursor's current position** — right after `"$45"` — and advances the cursor past the newly inserted element. The list is now `["$5", "$45", "** SALE **", "$15", "$60", "$25"]`, and the cursor sits between the new `"** SALE **"` entry and `"$15"`.
4. Third iteration: `it.next()` returns `"$15"` (the loop correctly resumes from where it left off, not re-processing the marker it just inserted) — value `15` is below `40`, no insertion.
5. Fourth iteration: `it.next()` returns `"$60"`, value `60` triggers another `it.add("** SALE **")`, inserted right after `"$60"`.
6. Fifth iteration: `it.next()` returns `"$25"`, below `40`, no insertion; `hasNext()` then returns `false` and the loop ends, leaving the final list with two sale markers inserted exactly after the two prices that triggered them.

## 7. Gotchas & takeaways

> **Gotcha:** after calling `add()`, the newly inserted element sits **behind** the cursor — the very next `next()` call returns whatever came after it, not the element just added. If the loop needs to re-examine the inserted element itself, that requires an explicit `previous()` call right after `add()`, since `add()` does not "revisit" what it just inserted.

- `ListIterator<T>` extends [`Iterator<T>`](0809-iterator.md) with `hasPrevious()`/`previous()` for backward traversal, `set()` for in-place replacement, and `add()` for mid-traversal insertion.
- `set()` always targets "the element most recently returned by `next()` or `previous()`" — it works after moving in either direction.
- `add()` inserts immediately before the position the next `next()` call would return, leaving the cursor positioned just past the new element.
- Only [`List`](0802-list.md) implementations expose `listIterator()` — [`Set`](0803-set.md) and [`Map`](0807-map.md) views don't, since bidirectional positional traversal requires the underlying indexed structure a list has and a set/map does not.
- Use plain `Iterator` when only forward traversal and removal are needed; reach for `ListIterator` specifically when in-place mutation or backward traversal is required.
