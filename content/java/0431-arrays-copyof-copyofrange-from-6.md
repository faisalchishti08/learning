---
card: java
gi: 431
slug: arrays-copyof-copyofrange-from-6
title: Arrays.copyOf / copyOfRange (from 6)
---

## 1. What it is

`Arrays.copyOf(original, newLength)` and `Arrays.copyOfRange(original, from, to)`, added in Java 6, create a **new** array by copying elements out of an existing one. `copyOf` copies from the start, either truncating (if `newLength` is smaller than the original) or padding with default values (`0`, `false`, `null`) if `newLength` is larger. `copyOfRange` copies a specific slice, from index `from` (inclusive) to `to` (**exclusive**), and — just like `copyOf` — pads with default values if `to` extends past the original array's actual length.

## 2. Why & when

Java arrays have a **fixed length** once created — there's no way to resize one in place. Before `Arrays.copyOf`, "resizing" an array meant manually writing the boilerplate every time: allocate a new array of the desired length, then loop (or use `System.arraycopy`) to copy the old contents across. `Arrays.copyOf`/`copyOfRange` package this common pattern into a single, readable call, handling the copy-and-pad or copy-and-truncate logic correctly every time.

This is precisely the technique behind array-backed growable structures — `ArrayList` internally grows its backing array by allocating a new, larger one and copying the old contents across, exactly as you'll build by hand below. You reach for `copyOf`/`copyOfRange` any time you need to resize an array, extract a sub-section of one, or need a genuinely independent copy (mutating the copy won't affect the original, unlike just assigning the same array reference to a new variable).

## 3. Core concept

```java
import java.util.Arrays;

int[] original = {10, 20, 30};

int[] grown = Arrays.copyOf(original, 5);       // [10, 20, 30, 0, 0]   -- padded with default int value 0
int[] shrunk = Arrays.copyOf(original, 2);       // [10, 20]             -- truncated

int[] middle = Arrays.copyOfRange(original, 1, 3);  // [20, 30]         -- "to" index is EXCLUSIVE
int[] pastEnd = Arrays.copyOfRange(original, 2, 5); // [30, 0, 0]       -- padded past the actual length
```

Both methods always return a **brand-new array** — the original is never modified, and the new array shares no mutable state with it (for primitive arrays; for object arrays, the *references* are copied, but the array itself is still a distinct object).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="copyOf grows or shrinks from the start of the array, padding with defaults if larger; copyOfRange extracts a specific slice, also padding with defaults if the requested end goes past the original length">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">original: [10, 20, 30]</text>

  <rect x="30" y="38" width="260" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="160" y="56" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">copyOf(original, 5) -&gt; [10, 20, 30, 0, 0]</text>

  <rect x="30" y="76" width="260" height="28" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="160" y="94" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">copyOf(original, 2) -&gt; [10, 20]</text>

  <rect x="330" y="38" width="280" height="28" rx="4" fill="#1c2430" stroke="#e6edf3"/><text x="470" y="56" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">copyOfRange(original, 1, 3) -&gt; [20, 30]</text>

  <rect x="330" y="76" width="280" height="28" rx="4" fill="#1c2430" stroke="#f85149"/><text x="470" y="94" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">copyOfRange(original, 2, 5) -&gt; [30, 0, 0]</text>

  <text x="320" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Every call returns a NEW array; the original is untouched in every case.</text>
</svg>

Both methods always produce a fresh array, padding with default values whenever the requested range extends beyond the original's actual data.

## 5. Runnable example

Scenario: building a small growable integer array from scratch (the same technique `ArrayList` uses internally) — the same array, evolved from basic `copyOf` resizing, through `copyOfRange` slicing, to a working mini growable-array class that doubles its capacity as needed and trims itself back to the exact used size on demand.

### Level 1 — Basic

```java
import java.util.Arrays;

public class DynamicArrayCopyOfBasic {
    public static void main(String[] args) {
        int[] scores = {10, 20, 30};
        System.out.println("Original: " + Arrays.toString(scores));

        int[] grown = Arrays.copyOf(scores, 5); // new array, length 5, extra slots default to 0
        System.out.println("Grown to 5: " + Arrays.toString(grown));

        int[] shrunk = Arrays.copyOf(scores, 2); // new array, length 2, truncates the rest
        System.out.println("Shrunk to 2: " + Arrays.toString(shrunk));
    }
}
```

**How to run:** `java DynamicArrayCopyOfBasic.java`

`Arrays.copyOf(scores, 5)` allocates a new 5-element array, copies `scores`' 3 existing values into the first 3 slots, and leaves the last 2 as the default `int` value, `0`. `Arrays.copyOf(scores, 2)` allocates a new 2-element array and copies only the first 2 values, silently dropping the third — `scores` itself is never modified by either call.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class DynamicArrayCopyOfRange {
    public static void main(String[] args) {
        int[] scores = {10, 20, 30, 40, 50};
        System.out.println("Original: " + Arrays.toString(scores));

        int[] middle = Arrays.copyOfRange(scores, 1, 4); // indices 1,2,3 -- "to" index is EXCLUSIVE
        System.out.println("copyOfRange(1, 4): " + Arrays.toString(middle));

        int[] pastEnd = Arrays.copyOfRange(scores, 3, 8); // requesting past the array's actual length
        System.out.println("copyOfRange(3, 8) (past end, zero-padded): " + Arrays.toString(pastEnd));
    }
}
```

**How to run:** `java DynamicArrayCopyOfRange.java`

`copyOfRange(scores, 1, 4)` extracts indices 1, 2, and 3 (index 4, the `to` boundary, is excluded) — a clean way to grab a sub-section without a manual loop. `copyOfRange(scores, 3, 8)` requests indices 3 through 7, but `scores` only has indices up to 4 — the missing indices (5, 6, 7) are filled with the default value `0`, exactly like `copyOf` does when growing.

### Level 3 — Advanced

```java
import java.util.Arrays;

public class MiniGrowableIntArray {
    static class GrowableIntArray {
        private int[] data = new int[2]; // start tiny, to force growth quickly in this demo
        private int size = 0;

        void add(int value) {
            if (size == data.length) {
                data = Arrays.copyOf(data, data.length * 2); // double capacity, keep existing values
                System.out.println("  (grew capacity to " + data.length + ")");
            }
            data[size++] = value;
        }

        int[] toTrimmedArray() {
            return Arrays.copyOfRange(data, 0, size); // drop the unused trailing capacity
        }

        @Override public String toString() {
            return Arrays.toString(toTrimmedArray()) + " (capacity=" + data.length + ", size=" + size + ")";
        }
    }

    public static void main(String[] args) {
        GrowableIntArray list = new GrowableIntArray();
        for (int i = 1; i <= 6; i++) {
            list.add(i * 10);
            System.out.println("After add(" + (i * 10) + "): " + list);
        }

        int[] trimmed = list.toTrimmedArray();
        System.out.println("\nFinal trimmed array (no wasted capacity): " + Arrays.toString(trimmed));
    }
}
```

**How to run:** `java MiniGrowableIntArray.java`

`GrowableIntArray` tracks a backing array (`data`) with spare capacity separately from its logical `size`. `add()` uses `Arrays.copyOf` to **double** the capacity only when the backing array is completely full — this doubling strategy (rather than growing by a fixed small amount each time) is exactly what `ArrayList` does internally, and it keeps the *amortized* cost of adding elements low. `toTrimmedArray()` uses `Arrays.copyOfRange` to return only the logically-used portion, hiding the unused capacity from callers.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `list` is created with `data = new int[2]` (capacity 2) and `size = 0`.

`list.add(10)`: `size == data.length` is `0 == 2`, `false` — no growth needed. `data[0] = 10`, `size` becomes `1`. Printing shows `[10] (capacity=2, size=1)`.

`list.add(20)`: `size == data.length` is `1 == 2`, still `false`. `data[1] = 20`, `size` becomes `2`. Printing shows `[10, 20] (capacity=2, size=2)`.

`list.add(30)`: now `size == data.length` is `2 == 2`, `true` — the backing array is full. `data = Arrays.copyOf(data, data.length * 2)` creates a new 4-element array, copying `[10, 20]` into the first two slots (the other two default to `0`), and reassigns `data` to point at it; `"(grew capacity to 4)"` is printed. Then `data[2] = 30`, `size` becomes `3`. `toTrimmedArray()` (used inside `toString()`) calls `Arrays.copyOfRange(data, 0, 3)`, correctly returning just `[10, 20, 30]` — the unused 4th slot (still `0`) is never exposed to the caller.

`list.add(40)`: `size == data.length` is `3 == 4`, `false` — still room. `data[3] = 40`, `size` becomes `4`. Shows `[10, 20, 30, 40] (capacity=4, size=4)`.

`list.add(50)`: `size == data.length` is `4 == 4`, `true` — grows again, doubling from 4 to 8: `"(grew capacity to 8)"` prints, `data[4] = 50`, `size` becomes `5`.

`list.add(60)`: `size == data.length` is `5 == 8`, `false` — no growth. `data[5] = 60`, `size` becomes `6`.

After the loop, `list.toTrimmedArray()` is called directly: `Arrays.copyOfRange(data, 0, 6)` returns exactly `[10, 20, 30, 40, 50, 60]`, with none of the two remaining unused capacity slots leaking into the result.

Expected output:
```
After add(10): [10] (capacity=2, size=1)
After add(20): [10, 20] (capacity=2, size=2)
  (grew capacity to 4)
After add(30): [10, 20, 30] (capacity=4, size=3)
After add(40): [10, 20, 30, 40] (capacity=4, size=4)
  (grew capacity to 8)
After add(50): [10, 20, 30, 40, 50] (capacity=8, size=5)
After add(60): [10, 20, 30, 40, 50, 60] (capacity=8, size=6)

Final trimmed array (no wasted capacity): [10, 20, 30, 40, 50, 60]
```

## 7. Gotchas & takeaways

> `copyOfRange`'s `to` index is **exclusive**, and if it extends past the original array's length, the result is **silently padded** with default values (`0`, `null`, etc.) rather than throwing an exception — only a *negative* `from` or a `from` greater than `to` throws. Requesting `copyOfRange(arr, 3, 8)` on a 5-element array doesn't fail; it quietly returns a longer array than you might expect, with trailing zeros/nulls, which can hide a bug where you meant to bound the range at the array's actual length.

- `copyOf(original, newLength)` copies from the start, truncating or zero/null-padding to reach the requested length.
- `copyOfRange(original, from, to)` copies a specific slice, with `from` inclusive and `to` **exclusive**, also padding if `to` exceeds the original's length.
- Both methods always return a brand-new array — the original is never mutated, making them safe for creating independent copies or snapshots.
- This copy-and-grow pattern (usually doubling capacity) is exactly what `ArrayList` and similar growable structures do internally to amortize the cost of repeated additions.
- When trimming a working buffer back down to its logically-used size (as `toTrimmedArray()` does above), `copyOfRange(data, 0, size)` is the idiomatic way to hide unused backing capacity from callers.
