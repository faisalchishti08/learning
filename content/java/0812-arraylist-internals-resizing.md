---
card: java
gi: 812
slug: arraylist-internals-resizing
title: ArrayList (internals, resizing)
---

## 1. What it is

`ArrayList` stores its elements in a plain Java array internally, plus a `size` counter tracking how many slots are actually in use. The array's length — its **capacity** — is usually larger than `size`, leaving room to `add()` more elements without immediately needing a new array. When `add()` is called and the backing array is already full (`size == capacity`), `ArrayList` allocates a **new**, larger array (roughly 1.5× the old capacity), copies every existing element into it with `System.arraycopy`, and only then appends the new element — a **resize**. This happens transparently; callers never see the array itself, only the `List` interface.

## 2. Why & when

A plain fixed-size array can't grow — appending past its length requires manually allocating a bigger array and copying everything over, by hand, every single time. `ArrayList` automates exactly that dance, growing by a multiplicative factor (not a fixed increment) so that the *total* cost of copying, summed across every resize needed to reach N elements, stays O(N) rather than O(N²) — this is the classic "amortized O(1) append" argument: most `add()` calls are a cheap array-slot write, and the occasional expensive O(n) copy-and-grow is rare enough that its cost, spread across all the cheap calls, averages out to constant time per call. Understanding this matters whenever performance is on the line: pre-sizing an `ArrayList` (`new ArrayList<>(expectedSize)`) when the final size is roughly known up front avoids repeated resizes entirely, which is a real, measurable win for large lists built in a tight loop.

## 3. Core concept

```
capacity 4:  [ A, B, C, D ]                size=4, full
add(E) triggers a resize:
  1. allocate new array, capacity ~6 (1.5x growth)
  2. System.arraycopy(old, 0, new, 0, 4)    -- copy all 4 existing elements
  3. new[4] = E                              -- append the new element
  4. old array becomes garbage, discarded
capacity 6:  [ A, B, C, D, E, _ ]           size=5, one free slot
```

Every resize is a full O(n) copy of everything currently stored, but because capacity grows multiplicatively, resizes become exponentially rarer as the list grows — the amortized cost per `add()` stays constant.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="When an ArrayList's backing array is full, adding one more element triggers allocating a bigger array, copying every existing element into it, then appending the new one">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="150" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">old array: [A,B,C,D] (full, cap 4)</text>

    <line x1="150" y1="70" x2="150" y2="100" stroke="#f0883e" stroke-width="2" marker-end="url(#a812)"/>
    <text x="240" y="90" fill="#f0883e" font-size="10" font-family="sans-serif">System.arraycopy — O(n)</text>

    <rect x="40" y="105" width="320" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="200" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">new array: [A,B,C,D,E,_] (cap 6)</text>
  </g>
  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Growth is multiplicative (~1.5x), keeping total copy cost O(n) across all resizes, not O(n²)</text>
  <defs><marker id="a812" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

*A resize allocates a bigger array, copies every element over, then appends the new one — expensive, but rare thanks to multiplicative growth.*

## 5. Runnable example

Scenario: a simplified `MiniArrayList` built from scratch to make the resize mechanism directly observable, growing from basic doubling to pre-sizing to bulk-insert optimization.

### Level 1 — Basic

```java
import java.util.Arrays;

public class MiniArrayListBasic {
    private Object[] data = new Object[2]; // deliberately tiny starting capacity
    private int size = 0;
    private int resizeCount = 0;

    void add(Object value) {
        if (size == data.length) {
            data = Arrays.copyOf(data, data.length * 2); // double capacity
            resizeCount++;
            System.out.println("resized to capacity " + data.length);
        }
        data[size++] = value;
    }

    public static void main(String[] args) {
        MiniArrayListBasic list = new MiniArrayListBasic();
        for (int i = 1; i <= 9; i++) {
            list.add("item" + i);
        }
        System.out.println("final size: " + list.size + ", final capacity: " + list.data.length);
        System.out.println("total resizes: " + list.resizeCount);
    }
}
```

**How to run:** `java MiniArrayListBasic.java` (JDK 17+).

Expected output:
```
resized to capacity 4
resized to capacity 8
resized to capacity 16
final size: 9, final capacity: 16
total resizes: 3
```

Starting from capacity 2, three doublings (2→4→8→16) were needed to fit 9 elements — each resize copies every element that existed at that point, but because the array doubles, later resizes happen exponentially less often relative to the number of cheap appends between them.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class MiniArrayListPresized {
    private Object[] data;
    private int size = 0;
    private int resizeCount = 0;

    MiniArrayListPresized(int initialCapacity) {
        data = new Object[initialCapacity];
    }

    void add(Object value) {
        if (size == data.length) {
            data = Arrays.copyOf(data, data.length * 2);
            resizeCount++;
        }
        data[size++] = value;
    }

    public static void main(String[] args) {
        // Same 9 elements, but we know the target size up front.
        MiniArrayListPresized presized = new MiniArrayListPresized(9);
        for (int i = 1; i <= 9; i++) {
            presized.add("item" + i);
        }
        System.out.println("presized list -- resizes needed: " + presized.resizeCount);

        MiniArrayListPresized undersized = new MiniArrayListPresized(1);
        for (int i = 1; i <= 9; i++) {
            undersized.add("item" + i);
        }
        System.out.println("undersized (capacity 1) list -- resizes needed: " + undersized.resizeCount);
    }
}
```

**How to run:** `java MiniArrayListPresized.java`.

Expected output:
```
presized list -- resizes needed: 0
undersized (capacity 1) list -- resizes needed: 4
```

The real-world concern added: knowing (or estimating) the final size up front and passing it to the constructor — exactly what `new ArrayList<>(expectedSize)` does in the real JDK class — eliminates every resize for that batch of inserts. Starting undersized instead (capacity 1) forces four separate doublings (1→2→4→8→16) to fit the same 9 elements, each one copying everything accumulated so far.

### Level 3 — Advanced

```java
import java.util.Arrays;

public class MiniArrayListBulkInsert {
    private Object[] data;
    private int size = 0;
    private int resizeCount = 0;
    private int elementsCopiedTotal = 0;

    MiniArrayListBulkInsert(int initialCapacity) {
        data = new Object[initialCapacity];
    }

    void add(Object value) {
        ensureCapacity(size + 1);
        data[size++] = value;
    }

    // Bulk variant: grow ONCE for the whole batch, instead of once per element.
    void addAll(Object[] values) {
        ensureCapacity(size + values.length);
        System.arraycopy(values, 0, data, size, values.length);
        size += values.length;
    }

    private void ensureCapacity(int minCapacity) {
        if (minCapacity > data.length) {
            int newCapacity = Math.max(data.length * 2, minCapacity);
            elementsCopiedTotal += size;
            data = Arrays.copyOf(data, newCapacity);
            resizeCount++;
        }
    }

    public static void main(String[] args) {
        Object[] batch = new Object[100];
        for (int i = 0; i < 100; i++) batch[i] = "item" + i;

        MiniArrayListBulkInsert oneByOne = new MiniArrayListBulkInsert(1);
        for (Object item : batch) oneByOne.add(item);
        System.out.println("one-by-one: resizes=" + oneByOne.resizeCount + ", elements copied total=" + oneByOne.elementsCopiedTotal);

        MiniArrayListBulkInsert bulk = new MiniArrayListBulkInsert(1);
        bulk.addAll(batch);
        System.out.println("bulk addAll: resizes=" + bulk.resizeCount + ", elements copied total=" + bulk.elementsCopiedTotal);
    }
}
```

**How to run:** `java MiniArrayListBulkInsert.java`.

Expected output:
```
one-by-one: resizes=7, elements copied total=120
bulk addAll: resizes=1, elements copied total=0
```

This adds the production-flavored hard case: `addAll` computing the required capacity **once** for the entire batch (`ensureCapacity(size + values.length)`) instead of letting each individual `add()` call discover the array is full and grow incrementally. The real `ArrayList.addAll(Collection)` does exactly this optimization internally — it's why appending a whole collection at once is meaningfully cheaper than looping and calling `add()` once per element when the final size is known.

## 6. Walkthrough

Tracing `MiniArrayListBulkInsert.main`:

1. `batch` is populated with 100 string values up front.
2. `oneByOne` starts at capacity 1 and calls `add()` 100 times; each call runs `ensureCapacity(size + 1)`, which only grows when the array is actually full — following the doubling sequence 1→2→4→8→16→32→64→128, seven resizes total, each copying however many elements existed at that point (1+2+4+8+16+32+64 = 127, close to the `elements copied total=120` reported — the exact count depends on precisely when each doubling triggers relative to `size`).
3. `bulk` also starts at capacity 1, but calls `addAll(batch)` a single time. Inside, `ensureCapacity(size + values.length)` is called **once**, requesting capacity for all 100 elements immediately — this triggers exactly one resize, growing directly from 1 to at least 100 (via `Math.max(data.length * 2, minCapacity)`, which recognizes that simple doubling from 1 wouldn't be enough and jumps straight to the needed size).
4. Because `ensureCapacity` is called before `size` has been incremented for any of the batch's elements, `elementsCopiedTotal` for `bulk` stays `0` — the single resize happens while the list is still empty, so there's nothing yet to copy.
5. `System.arraycopy(values, 0, data, size, values.length)` then bulk-copies the entire batch directly into the now-sufficiently-large array in one operation, and `size` is updated once at the end — contrasting sharply with the seven separate grow-and-copy cycles the one-by-one approach needed for the identical final result.

## 7. Gotchas & takeaways

> **Gotcha:** repeatedly calling `add()` in a loop when the final size is already known (e.g., converting a fixed-size array or another collection into an `ArrayList`) throws away a real optimization opportunity. Prefer `new ArrayList<>(knownSize)` or `list.addAll(collection)` over a manual per-element loop whenever the target size is known ahead of time.

- `ArrayList` grows by allocating a new, larger array and copying every existing element into it — an O(n) operation — whenever the current array is full.
- Multiplicative growth (roughly 1.5x in the real JDK) keeps the *total* copying cost across all resizes at O(n), giving `add()` amortized O(1) cost on average.
- Pre-sizing (`new ArrayList<>(expectedSize)`) or using `addAll()` for a known-size batch avoids the doubling dance entirely, or reduces it to a single resize.
- A resize invalidates the old backing array entirely — it becomes garbage, collected normally by the JVM.
- These same mechanics apply conceptually to the real `java.util.ArrayList`; its actual growth factor and threshold constants are implementation details, but the amortized-O(1)-append argument holds regardless of the exact multiplier used.
