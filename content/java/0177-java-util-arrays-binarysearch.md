---
card: java
gi: 177
slug: java-util-arrays-binarysearch
title: java.util.Arrays.binarySearch()
---

## 1. What it is

`java.util.Arrays.binarySearch()` looks up a value in an array using the **binary search** algorithm, which repeatedly halves the search range by comparing the target against the middle element. It runs in **O(log n)** time — far faster than scanning element by element (`O(n)`) — but it has one hard requirement: **the array must already be sorted in ascending order**, since the algorithm's halving logic depends entirely on that order.

```java
int[] sorted = { 1, 3, 5, 7, 9, 11 };
int index = java.util.Arrays.binarySearch(sorted, 7);
System.out.println(index); // 3 — 7 is at index 3

int missing = java.util.Arrays.binarySearch(sorted, 8);
System.out.println(missing); // negative — 8 is not present
```

If the value is found, `binarySearch` returns its index; if not found, it returns a **negative number** encoding where the value *would* be inserted to keep the array sorted — never a plain `-1` the way some other "not found" conventions use.

## 2. Why & when

Binary search is the standard way to look up values in large sorted collections efficiently:

- **Fast lookups in sorted data** — checking whether a sorted array of a million elements contains a value takes at most about 20 comparisons (`log₂(1,000,000) ≈ 20`), versus up to a million comparisons for a linear scan.
- **It requires sorting first** — if the array isn't already sorted, `Arrays.sort()` must be called before `binarySearch`; searching an unsorted array with `binarySearch` gives **undefined, incorrect results** without throwing any error to warn you.
- **Insertion point discovery** — the negative return value, once decoded, tells you exactly where to insert a new value to keep the array in sorted order, which is useful for maintaining a sorted collection incrementally.

Use `binarySearch` when the array is sorted (or you can afford to sort it once) and you'll be searching it many times; for a single one-off search on unsorted data, a simple linear scan is simpler and doesn't require sorting first.

## 3. Core concept

```java
public class BinarySearchDemo {
    public static void main(String[] args) {
        int[] sorted = { 10, 20, 30, 40, 50 };

        int found = java.util.Arrays.binarySearch(sorted, 30);
        System.out.println("Found 30 at index: " + found); // 2

        int notFound = java.util.Arrays.binarySearch(sorted, 35);
        System.out.println("Raw result for 35: " + notFound); // negative

        int insertionPoint = -(notFound) - 1; // decode the negative result
        System.out.println("35 would insert at index: " + insertionPoint); // 3
    }
}
```

The formula `-(result) - 1` converts the negative "not found" encoding back into a usable **insertion index** — this specific formula (rather than a simpler negation) is what `Arrays.binarySearch`'s documentation specifies, and it's the standard way to interpret a negative result.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary search narrowing a sorted array from a full range down to the target by repeatedly checking the middle element and discarding half the remaining range each time">
  <rect x="8" y="8" width="584" height="164" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binarySearch([10,20,30,40,50], 30) — target 30</text>

  <text x="30" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">step 1: lo=0 hi=4</text>
  <rect x="150" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="170" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">10</text>
  <rect x="190" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="210" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">20</text>
  <rect x="230" y="40" width="40" height="28" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="250" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">30</text>
  <rect x="270" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="290" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">40</text>
  <rect x="310" y="40" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="330" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">50</text>
  <text x="400" y="59" fill="#79c0ff" font-size="10" font-family="sans-serif">mid=index 2 -&gt; 30 == 30 -&gt; FOUND</text>

  <text x="30" y="110" fill="#8b949e" font-size="10" font-family="sans-serif">searching for 45 instead:</text>
  <text x="30" y="130" fill="#8b949e" font-size="9" font-family="sans-serif">mid=index2(30): 45&gt;30, search right half [40,50]</text>
  <text x="30" y="148" fill="#8b949e" font-size="9" font-family="sans-serif">mid=index4(50): 45&lt;50, search left of it -&gt; empty range</text>
  <text x="30" y="166" fill="#79c0ff" font-size="9" font-family="sans-serif">not found -&gt; returns negative, decodes to insertion index 4</text>
</svg>

Each comparison against the middle element eliminates half of the remaining search range.

## 5. Runnable example

Scenario: looking up product prices in a sorted price list — starting with a basic found/not-found search, then extending to decode the insertion point for a missing price, then hardening into a method that inserts a new price into the correct sorted position using the decoded index.

### Level 1 — Basic

```java
public class PriceLookupBasic {
    public static void main(String[] args) {
        int[] prices = { 5, 10, 15, 20, 25 }; // already sorted ascending

        int index = java.util.Arrays.binarySearch(prices, 15);
        System.out.println("Index of 15: " + index);

        int missing = java.util.Arrays.binarySearch(prices, 12);
        System.out.println("Result for missing 12: " + missing);
    }
}
```

**How to run:** `java PriceLookupBasic.java`

`binarySearch(prices, 15)` returns `2` (its actual index); `binarySearch(prices, 12)` returns a negative number since `12` isn't in `prices` — the exact negative value encodes where `12` would need to go to keep the array sorted.

### Level 2 — Intermediate

Same price list, now decoding the negative result into an actual insertion index using the standard formula.

```java
public class PriceLookupIntermediate {
    public static void main(String[] args) {
        int[] prices = { 5, 10, 15, 20, 25 };

        int result = java.util.Arrays.binarySearch(prices, 12);
        if (result >= 0) {
            System.out.println("Found at index " + result);
        } else {
            int insertionPoint = -(result) - 1;
            System.out.println("Not found; would insert at index " + insertionPoint);
        }
    }
}
```

**How to run:** `java PriceLookupIntermediate.java`

`result >= 0` distinguishes "found" from "not found" — a non-negative result is always a valid index, while any negative result must be decoded with `-(result) - 1` to get the insertion point (here, `12` would insert at index `2`, between `10` and `15`).

### Level 3 — Advanced

Same price list, now with a method that inserts a new price into a correctly-sized, still-sorted array using the decoded insertion point — building a new array since plain arrays can't grow in place.

```java
import java.util.Arrays;

public class PriceLookupAdvanced {

    static int[] insertSorted(int[] sortedPrices, int newPrice) {
        int result = Arrays.binarySearch(sortedPrices, newPrice);
        if (result >= 0) {
            return sortedPrices; // already present, nothing to insert
        }
        int insertionPoint = -(result) - 1;

        int[] expanded = new int[sortedPrices.length + 1];
        System.arraycopy(sortedPrices, 0, expanded, 0, insertionPoint);              // copy elements before the gap
        expanded[insertionPoint] = newPrice;                                        // drop the new value into the gap
        System.arraycopy(sortedPrices, insertionPoint, expanded, insertionPoint + 1, // copy elements after the gap
                          sortedPrices.length - insertionPoint);
        return expanded;
    }

    public static void main(String[] args) {
        int[] prices = { 5, 10, 15, 20, 25 };

        int[] updated = insertSorted(prices, 12);
        System.out.println(Arrays.toString(updated)); // stays sorted, 12 inserted correctly

        int[] duplicate = insertSorted(updated, 12);
        System.out.println(Arrays.toString(duplicate)); // unchanged: 12 already present
    }
}
```

**How to run:** `java PriceLookupAdvanced.java`

`System.arraycopy` is called twice: once to copy everything *before* the insertion point into the new array unchanged, and once to copy everything from the insertion point *onward* shifted one slot to the right — leaving exactly one open slot at `insertionPoint` for `newPrice`, and preserving sorted order throughout.

## 6. Walkthrough

Trace `insertSorted({5, 10, 15, 20, 25}, 12)`:

**Search.** `Arrays.binarySearch(prices, 12)` doesn't find `12` (it's not in the array), returning some negative encoded value. Decoding: `insertionPoint = 2` (between `10` at index 1 and `15` at index 2).

**Allocate.** `expanded = new int[6]` (one longer than the original 5).

**First copy.** `System.arraycopy(prices, 0, expanded, 0, 2)` copies indices `0` and `1` (`5`, `10`) into `expanded[0]` and `expanded[1]`, unchanged.

**Insert.** `expanded[2] = 12` drops the new value into the gap.

**Second copy.** `System.arraycopy(prices, 2, expanded, 3, 3)` copies the remaining 3 original elements (`15, 20, 25`, starting from index 2) into `expanded[3..5]`, shifted one slot right to make room.

```
prices:      [ 5, 10, 15, 20, 25]
insertionPoint = 2

expanded before insert: [ 5, 10,  _,  _,  _,  _]
copy prices[0..1] -> expanded[0..1]: [ 5, 10,  _,  _,  _,  _]
expanded[2] = 12:                    [ 5, 10, 12,  _,  _,  _]
copy prices[2..4] -> expanded[3..5]: [ 5, 10, 12, 15, 20, 25]
```

**Second call.** `insertSorted(updated, 12)` searches the now-6-element array and *finds* `12` at index `2` (`result >= 0`), so the method returns the array unchanged — printing the same array again with no duplicate inserted.

## 7. Gotchas & takeaways

> **`binarySearch` on an unsorted array gives undefined results — it does not throw an exception or detect the mistake.** The algorithm assumes sortedness and will confidently return a wrong index (or a wrong "not found") without any warning; always sort first.

> **A "not found" result is never a simple `-1` — it's a specific negative number that must be decoded with `-(result) - 1` to get the insertion point.** Comparing the raw result to `-1` directly, instead of checking `result < 0`, is a common mistake that silently misclassifies most "not found" cases.

- `binarySearch` requires the array to already be sorted ascending; sort with `Arrays.sort()` first if it isn't.
- A non-negative result is the found index; a negative result must be decoded (`-(result) - 1`) to get the insertion point.
- Binary search runs in `O(log n)` time, dramatically faster than a linear scan for large sorted arrays.
- Use the decoded insertion point together with `System.arraycopy` to insert a new element while keeping an array sorted.
