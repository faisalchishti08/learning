---
card: java
gi: 842
slug: collections-sort-reverse-shuffle-binarysearch
title: Collections.sort / reverse / shuffle / binarySearch
---

## 1. What it is

`Collections` (note: singular `Collection` is the interface; `Collections`, plural, is a utility class) provides static algorithm methods that operate on `List`s: `Collections.sort(list)`/`sort(list, comparator)` (equivalent to, and largely superseded in practice by, the instance method `list.sort(...)` added in Java 8, but still common in older code), `Collections.reverse(list)` (reverses element order in place), `Collections.shuffle(list)`/`shuffle(list, random)` (randomly permutes elements, using a supplied `Random` for reproducible shuffles), and `Collections.binarySearch(list, key)`/`binarySearch(list, key, comparator)` (performs binary search — **only valid on an already-sorted list**, and returns the negative insertion point encoded as `-(insertionPoint) - 1` when the key isn't found).

## 2. Why & when

These methods exist to avoid hand-writing common list algorithms — reversing, shuffling, and binary-searching are each a few lines of easy-to-get-subtly-wrong code (off-by-one errors in a hand-rolled binary search are a classic bug source) that the JDK provides correctly and efficiently once, for any `List`. `Collections.shuffle(list, seededRandom)` in particular matters for testing and reproducibility — an unseeded shuffle can't be replayed identically across runs, while a seeded one produces the exact same permutation every time, useful for deterministic tests or reproducible bug reports. `Collections.binarySearch` matters purely for performance: on a large sorted list, it finds an element in O(log n) instead of the O(n) a linear scan (`list.indexOf` or `list.contains`) would cost — but only if its precondition (the list must already be sorted according to the same ordering used for the search) is actually met.

## 3. Core concept

```java
List<Integer> numbers = new ArrayList<>(List.of(5, 2, 8, 1, 9));

Collections.sort(numbers);              // [1, 2, 5, 8, 9] -- required before binarySearch
Collections.reverse(numbers);           // [9, 8, 5, 2, 1] -- simple in-place reversal
Collections.shuffle(numbers, new Random(42)); // a reproducible random permutation, given the same seed

Collections.sort(numbers);              // must re-sort before binarySearch is valid again
int index = Collections.binarySearch(numbers, 8); // 3 -- found at index 3

int missing = Collections.binarySearch(numbers, 6); // NOT found
// missing is negative: -(insertionPoint) - 1, telling you WHERE 6 WOULD belong if inserted
```

The negative return value from a failed `binarySearch` isn't just "not found" — it encodes the exact position the missing key would need to be inserted at to keep the list sorted, recoverable via `-(missing) - 1`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collections.binarySearch requires the list to already be sorted; searching an unsorted list produces an unreliable, meaningless result">
  <rect x="40" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="170" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">sorted list + binarySearch</text>
  <text x="170" y="72" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">correct, O(log n)</text>

  <rect x="340" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="470" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">UNSORTED list + binarySearch</text>
  <text x="470" y="72" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">result is UNDEFINED, may be wrong</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binarySearch has NO way to detect an unsorted list — it silently trusts the precondition</text>
</svg>

*`binarySearch` never checks whether the list is actually sorted — violating that precondition produces silently wrong results, not an exception.*

## 5. Runnable example

Scenario: managing a leaderboard's underlying score list, growing from basic sort/reverse/shuffle usage, to correct binary-search lookups, to demonstrating (and avoiding) the classic bug of searching an unsorted list.

### Level 1 — Basic

```java
import java.util.*;

public class ListAlgorithmsBasic {
    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>(List.of(72, 91, 60, 85, 78));

        Collections.sort(scores);
        System.out.println("sorted: " + scores);

        Collections.reverse(scores);
        System.out.println("reversed: " + scores);
    }
}
```

**How to run:** `java ListAlgorithmsBasic.java` (JDK 17+).

Expected output:
```
sorted: [60, 72, 78, 85, 91]
reversed: [91, 85, 78, 72, 60]
```

`Collections.reverse` simply flips the current order in place — it doesn't re-sort or re-derive anything, just reverses whatever order the list already had.

### Level 2 — Intermediate

```java
import java.util.*;

public class ReproducibleShuffleAndSearch {
    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>(List.of(72, 91, 60, 85, 78));

        // A SEEDED shuffle -- the exact same permutation every time this program runs.
        Collections.shuffle(scores, new Random(42));
        System.out.println("shuffled (reproducible with seed 42): " + scores);

        // binarySearch REQUIRES sorted input -- always sort immediately before searching.
        Collections.sort(scores);
        System.out.println("re-sorted before searching: " + scores);

        int foundIndex = Collections.binarySearch(scores, 85);
        System.out.println("index of 85: " + foundIndex);

        int notFoundResult = Collections.binarySearch(scores, 80);
        int insertionPoint = -(notFoundResult) - 1;
        System.out.println("80 not found, raw result: " + notFoundResult + ", would insert at index: " + insertionPoint);
    }
}
```

**How to run:** `java ReproducibleShuffleAndSearch.java`. With the same seed (`42`), the shuffled order is identical on every run and every machine.

Expected output:
```
shuffled (reproducible with seed 42): [78, 60, 91, 85, 72]
re-sorted before searching: [60, 72, 78, 85, 91]
index of 85: 3
80 not found, raw result: -4, would insert at index: 3
```

The real-world concern added: a **seeded** shuffle for reproducibility (essential for deterministic tests), and correctly decoding `binarySearch`'s negative "not found" result into the actual insertion point — `-(-4) - 1 = 3`, meaning `80` would need to go at index 3 (between `78` and `85`) to keep the list sorted.

### Level 3 — Advanced

```java
import java.util.*;

public class UnsortedSearchBug {
    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>(List.of(72, 91, 60, 85, 78));

        // BUG: searching WITHOUT sorting first. binarySearch has no way to detect this.
        int buggyResult = Collections.binarySearch(scores, 85);
        System.out.println("searching UNSORTED list for 85: " + buggyResult + " (unreliable -- may be wrong!)");
        System.out.println("(85 IS actually present, at unsorted index " + scores.indexOf(85) + ", but binarySearch can't tell)");

        // THE FIX: always sort immediately before searching, on a list you control the mutation of.
        Collections.sort(scores);
        int correctResult = Collections.binarySearch(scores, 85);
        System.out.println("searching SORTED list for 85: " + correctResult + " (correct)");

        // A SECOND bug: mutating the list (e.g. adding an element) INVALIDATES sortedness for future searches.
        scores.add(50); // now unsorted again -- 50 was appended at the end, not inserted in order
        int staleResult = Collections.binarySearch(scores, 50);
        System.out.println("searching again after an unsorted append: " + staleResult + " (unreliable again!)");
    }
}
```

**How to run:** `java UnsortedSearchBug.java`. The exact "unreliable" values shown may vary depending on `binarySearch`'s internal probing sequence for this specific unsorted data, but the key point — the result cannot be trusted — holds regardless of what specific wrong (or coincidentally right) answer appears.

Expected output shape (exact "unreliable" numbers may differ from this specific example):
```
searching UNSORTED list for 85: -3 (unreliable -- may be wrong!)
(85 IS actually present, at unsorted index 3, but binarySearch can't tell)
searching SORTED list for 85: 3 (correct)
searching again after an unsorted append: -6 (unreliable again!)
```

This adds the production-flavored hard case: `Collections.binarySearch` never validates its precondition — it has no way to check whether the list is actually sorted, and calling it on an unsorted list simply produces a meaningless result (possibly "not found" for an element that's actually present, as shown here) rather than an exception. Just as dangerously, mutating a previously-sorted list (even by simple appending, as with `scores.add(50)`) silently invalidates its sortedness for any *future* `binarySearch` call — the list doesn't "remember" it was sorted once; every mutation is the caller's responsibility to account for before searching again.

## 6. Walkthrough

Tracing `UnsortedSearchBug.main`:

1. `scores` starts as `[72, 91, 60, 85, 78]` — in its original, unsorted insertion order.
2. `Collections.binarySearch(scores, 85)` is called directly on this unsorted list. Internally, binary search repeatedly checks the middle element of the current search range and decides whether to search the left or right half based on whether that middle element is greater or less than the target — a decision that only makes sense if the list is actually sorted. Applied to unsorted data, the algorithm still runs to completion and returns *some* result, but that result bears no reliable relationship to whether or where the target actually appears — in this specific run, it happens to report "not found" (`-3`) even though `85` genuinely is present at (unsorted) index 3, purely because the search's left/right decisions, driven by comparisons against an unsorted arrangement, happened to skip over it.
3. `Collections.sort(scores)` reorders `scores` into `[60, 72, 78, 85, 91]`. Now `Collections.binarySearch(scores, 85)` correctly returns `3`, since the precondition is finally satisfied.
4. `scores.add(50)` appends `50` to the **end** of the list, producing `[60, 72, 78, 85, 91, 50]` — this is no longer sorted, since `50` belongs at the front, not the back.
5. `Collections.binarySearch(scores, 50)` is called on this now-unsorted list. Exactly as in step 2, the search proceeds as if the list were sorted, comparing against the middle element and following a left/right decision path that assumes correctness it doesn't have — the result is unreliable, demonstrating that sortedness isn't a one-time property to establish and forget, but an invariant that must be maintained (or re-established via another `sort` call) before every single `binarySearch` call.

## 7. Gotchas & takeaways

> **Gotcha:** `Collections.binarySearch` has **no way to detect** that its precondition (the list must be sorted, according to the same ordering used for the search) has been violated — it will run to completion and return a value regardless, and that value carries no reliability guarantee once the precondition is broken. There is no exception, no warning — just a silently wrong answer that might occasionally coincide with the right one by chance.

- `Collections.sort`, `.reverse`, and `.shuffle` mutate a `List` in place; `Collections.shuffle(list, seededRandom)` produces a reproducible permutation given the same seed.
- `Collections.binarySearch` requires the list to already be sorted according to the same ordering (natural or a supplied comparator) used for the search — violating this precondition produces an undefined, unreliable result rather than an exception.
- A failed `binarySearch` returns a negative value encoding the correct insertion point: `-(insertionPoint) - 1`, recoverable via `-(result) - 1`.
- Any mutation to a sorted list (even simple appending) can invalidate its sortedness for future `binarySearch` calls — sortedness must be actively maintained, not assumed to persist automatically.
- For lists that are searched far more often than mutated, consider a genuinely self-sorting structure like [`TreeSet`](0819-treeset.md)/[`TreeMap`](0825-treemap-red-black-tree.md) instead, which maintains its sortedness invariant automatically through every mutation.
