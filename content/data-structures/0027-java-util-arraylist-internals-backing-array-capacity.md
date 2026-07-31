---
card: data-structures
gi: 27
slug: java-util-arraylist-internals-backing-array-capacity
title: java.util.ArrayList internals (backing array, capacity)
---

## 1. What it is

`java.util.ArrayList` is a dynamic array class: internally it wraps a plain `Object[]` array (its **backing array**) and manages the bookkeeping of size and growth for you. **Capacity** is the length of that hidden backing array — how many elements it can currently hold before a resize is needed. **Size** is how many elements you have actually added; capacity is always `>= size`.

## 2. Why & when

Understanding the backing array explains `ArrayList`'s real performance characteristics: fast indexed `get`/`set` (O(1), since it is just array indexing under the hood), amortized O(1) `add` at the end, but O(n) `add`/`remove` in the middle (because of shifting). It also explains why `new ArrayList<>(expectedSize)` is worth using when you know roughly how many elements you will add — it avoids repeated backing-array resizes.

## 3. Core concept

**Capacity vs size are different numbers.** `list.size()` is the count of actual elements; the backing array's length (its capacity) is usually larger, to leave room for future `add()` calls without an immediate resize. There is no public `list.capacity()` method — capacity is an internal implementation detail.

**Default and growth behavior.** A no-argument `new ArrayList<>()` starts with an empty backing array and allocates a small backing array (historically capacity 10) on the *first* `add()`. When the backing array fills up, `ArrayList` allocates a new array at roughly 1.5x the old capacity and copies every element over — the same doubling-style growth covered in [Array resizing & amortized append](0020-array-resizing-amortized-append.md), applied inside a standard library class instead of hand-rolled.

**Why `get`/`set` stay O(1) but structural changes do not.** `get(i)` and `set(i, v)` translate directly to `backingArray[i]`, so they inherit the array's O(1) random access. `add(i, v)` and `remove(i)` in the middle still have to shift every later element in the backing array, so they remain O(n) — `ArrayList` does not remove this cost, it just hides the resizing logic.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An ArrayList object holding a reference to a backing Object array, with size smaller than the array's total capacity">
  <g font-family="sans-serif" font-size="12">
    <text x="130" y="18" fill="#8b949e" text-anchor="middle">ArrayList&lt;String&gt; (size=3)</text>
    <rect x="50" y="30" width="160" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="130" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">elementData -&gt; (reference)</text>
    <line x1="130" y1="60" x2="130" y2="90" stroke="#79c0ff" marker-end="url(#a4)"/>
    <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="400" y="18" fill="#8b949e" text-anchor="middle">backing Object[] (capacity=10)</text>
    <rect x="40" y="95" width="45" height="26" fill="#0d1117" stroke="#3fb950"/><text x="62" y="112" fill="#e6edf3" text-anchor="middle" font-size="9">"a"</text>
    <rect x="85" y="95" width="45" height="26" fill="#0d1117" stroke="#3fb950"/><text x="107" y="112" fill="#e6edf3" text-anchor="middle" font-size="9">"b"</text>
    <rect x="130" y="95" width="45" height="26" fill="#0d1117" stroke="#3fb950"/><text x="152" y="112" fill="#e6edf3" text-anchor="middle" font-size="9">"c"</text>
    <rect x="175" y="95" width="45" height="26" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <rect x="220" y="95" width="45" height="26" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <text x="150" y="150" fill="#8b949e" font-size="10">size=3 (elements used)</text>
    <text x="380" y="150" fill="#8b949e" font-size="10">capacity=10 (backing array length, 7 unused slots)</text>
  </g>
</svg>

The `ArrayList` object itself is small — it just holds a reference to the real data, a separate `Object[]` array whose length (capacity) is usually bigger than the reported `size()`.

## 5. Runnable example

```java
// ArrayListInternals.java
import java.util.ArrayList;
import java.util.List;

public class ArrayListInternals {

    // Basic: size vs capacity -- size() only reports elements actually added.
    static void basicLevel() {
        List<String> list = new ArrayList<>();
        System.out.println("basic: empty list size -> " + list.size());
        list.add("a"); list.add("b"); list.add("c");
        System.out.println("basic: after 3 adds, size -> " + list.size());
        // capacity is internal and not exposed publicly -- size() is the only supported way to ask "how many?"
    }

    // Intermediate: get/set are O(1) (direct array indexing); add/remove in the middle are O(n) (shifting).
    static void intermediateLevel() {
        List<Integer> list = new ArrayList<>();
        for (int i = 0; i < 10; i++) list.add(i);

        long t1 = System.nanoTime();
        int value = list.get(5); // O(1): backingArray[5]
        long getTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        list.add(0, -1); // O(n): shifts every existing element right by one
        long insertTime = System.nanoTime() - t2;

        System.out.println("intermediate: get(5) -> " + value + " time(ns) -> " + getTime);
        System.out.println("intermediate: add(0, -1) list now -> " + list + " time(ns) -> " + insertTime);
    }

    // Advanced: pre-sizing with the capacity constructor avoids repeated backing-array resizes.
    static void advancedLevel() {
        int n = 300_000;

        long t1 = System.nanoTime();
        List<Integer> defaultGrowth = new ArrayList<>(); // starts small, resizes repeatedly
        for (int i = 0; i < n; i++) defaultGrowth.add(i);
        long defaultTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        List<Integer> preSized = new ArrayList<>(n); // backing array allocated at full size up front
        for (int i = 0; i < n; i++) preSized.add(i);
        long preSizedTime = System.nanoTime() - t2;

        System.out.println("advanced: default-growth add loop time(ns) -> " + defaultTime);
        System.out.println("advanced: pre-sized add loop time(ns) -> " + preSizedTime);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArrayListInternals.java`, then run `java ArrayListInternals.java`.

## 6. Walkthrough

1. `basicLevel()` creates an empty `ArrayList`. Internally its backing array starts empty (or unallocated); `size()` correctly reports `0` regardless of what capacity the backing array actually has reserved.
2. After three `add()` calls, `size()` reports `3` — but the hidden backing array's length is very likely larger than 3, since `ArrayList` over-allocates to avoid resizing on every single `add()`.
3. `intermediateLevel()` calls `get(5)`, which resolves directly to an array index lookup on the backing array — fast and O(1), regardless of list size.
4. `add(0, -1)` inserts at the front, forcing `ArrayList` to shift all 10 existing elements one slot right inside the backing array before placing `-1` at index 0 — this is visibly more expensive than the `get` call.
5. `advancedLevel()` compares default growth (many backing-array resizes as the list grows from empty to 300,000 elements) against `new ArrayList<>(n)`, which allocates the backing array at its final capacity immediately, needing zero resize-and-copy operations along the way.

## 7. Gotchas & takeaways

> Gotcha: `ArrayList` has no public `capacity()` method — you can only observe `size()`. Relying on undocumented internal capacity behavior (e.g. assuming it always starts at exactly 10) is fragile across Java versions; treat capacity as an implementation detail, and only use `new ArrayList<>(expectedSize)` as a performance hint, not a guarantee.

- `ArrayList` wraps a plain array internally; `size()` is the element count, capacity is the (larger, hidden) backing array length.
- `get`/`set` are O(1) because they are direct array indexing; `add`/`remove` away from the end are O(n) because of shifting.
- Pre-sizing with `new ArrayList<>(expectedSize)` avoids repeated resize-and-copy work when the approximate final size is known.
- Related concepts: [Array resizing & amortized append](0020-array-resizing-amortized-append.md), [Insert / delete shifting cost](0019-insert-delete-shifting-cost.md).
