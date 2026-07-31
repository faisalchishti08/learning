---
card: data-structures
gi: 19
slug: insert-delete-shifting-cost
title: Insert / delete shifting cost
---

## 1. What it is

Inserting or deleting an element in the **middle** of an array is not a single-step operation. Because array elements must stay contiguous with no gaps, every element after the insertion or deletion point has to **shift** one slot to make (or close) the space. Inserting at index 2 of a 10-element array means moving 8 elements over by one position.

## 2. Why & when

This matters when you choose between an array-backed list (`ArrayList`) and a node-based list (`LinkedList`) for code that frequently inserts or removes elements away from the end. If most changes happen at the end (`add`/`removeLast`), arrays are fine — no shifting needed there. If changes happen often in the middle or the front, the O(n) shifting cost of an array can dominate your runtime.

## 3. Core concept

**Why contiguity forces shifting.** The array invariant — no gaps between elements — must hold after every operation. Deleting `arr[2]` and leaving a hole would break every later index's O(1) address formula, so every element after index 2 must move left by one slot to close the gap.

**Insert cost = number of elements after the insertion point.** Inserting at the very end costs 0 shifts (nothing is after it). Inserting at the very front costs `n` shifts (everything moves). On average, inserting at a random position shifts about `n/2` elements — still O(n).

**Delete follows the same rule in reverse.** Removing `arr[i]` shifts every element after index `i` one slot to the left. Removing the last element costs 0 shifts; removing the first costs `n - 1` shifts.

**Contrast with a linked list.** A `LinkedList` node insertion or deletion, given a reference to the right spot, is O(1) — it just relinks a couple of pointers, no shifting of unrelated elements. The tradeoff is that a linked list lacks O(1) random access to *find* that spot in the first place.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deleting index 2 from a 6-element array shifts every later element one slot to the left to close the gap">
  <g font-family="sans-serif" font-size="12">
    <text x="320" y="20" fill="#8b949e" text-anchor="middle">before: delete index 2 (value 30)</text>
    <rect x="30" y="35" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="60" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">10</text>
    <rect x="90" y="35" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="120" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">20</text>
    <rect x="150" y="35" width="60" height="30" fill="#21262d" stroke="#f85149"/><text x="180" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">30 x</text>
    <rect x="210" y="35" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="240" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">40</text>
    <rect x="270" y="35" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="300" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">50</text>
    <rect x="330" y="35" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="360" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">60</text>

    <text x="320" y="100" fill="#8b949e" text-anchor="middle">after: three elements shifted left by one</text>
    <rect x="30" y="115" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="60" y="135" fill="#e6edf3" text-anchor="middle" font-size="10">10</text>
    <rect x="90" y="115" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="120" y="135" fill="#e6edf3" text-anchor="middle" font-size="10">20</text>
    <rect x="150" y="115" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="180" y="135" fill="#e6edf3" text-anchor="middle" font-size="10">40</text>
    <rect x="210" y="115" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="240" y="135" fill="#e6edf3" text-anchor="middle" font-size="10">50</text>
    <rect x="270" y="115" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="300" y="135" fill="#e6edf3" text-anchor="middle" font-size="10">60</text>
    <rect x="330" y="115" width="60" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/><text x="360" y="135" fill="#8b949e" text-anchor="middle" font-size="10">unused</text>

    <text x="320" y="175" fill="#79c0ff" text-anchor="middle">deleting near the front shifts many elements — O(n) in the worst case</text>
  </g>
</svg>

Deleting index 2 leaves a gap. Every element after it (40, 50, 60) must move one slot left to close that gap and keep the array contiguous.

## 5. Runnable example

```java
// InsertDeleteShiftingCost.java
import java.util.Arrays;

public class InsertDeleteShiftingCost {

    // Basic: manual insert at an arbitrary index, showing the explicit shift.
    static int[] insertAt(int[] arr, int index, int value) {
        int[] result = new int[arr.length + 1];
        System.arraycopy(arr, 0, result, 0, index);            // copy elements before index, unchanged
        result[index] = value;                                  // place the new value
        System.arraycopy(arr, index, result, index + 1, arr.length - index); // shift the rest right by one
        return result;
    }

    static void basicLevel() {
        int[] arr = {10, 20, 40, 50};
        int[] afterInsert = insertAt(arr, 2, 30); // insert 30 at index 2
        System.out.println("basic: after insert -> " + Arrays.toString(afterInsert));
    }

    // Intermediate: manual delete at an arbitrary index, showing the explicit shift left.
    static int[] deleteAt(int[] arr, int index) {
        int[] result = new int[arr.length - 1];
        System.arraycopy(arr, 0, result, 0, index);                       // elements before index, unchanged
        System.arraycopy(arr, index + 1, result, index, arr.length - index - 1); // shift the rest left by one
        return result;
    }

    static void intermediateLevel() {
        int[] arr = {10, 20, 30, 40, 50, 60};
        int[] afterDelete = deleteAt(arr, 2); // delete the element at index 2 (value 30)
        System.out.println("intermediate: after delete -> " + Arrays.toString(afterDelete));
    }

    // Advanced: measuring the cost difference between front-inserts and end-inserts on ArrayList.
    static void advancedLevel() {
        java.util.List<Integer> list = new java.util.ArrayList<>();
        for (int i = 0; i < 50_000; i++) list.add(i); // fill with 50,000 elements first

        long t1 = System.nanoTime();
        list.add(list.size(), -1); // insert at the END: no shifting needed
        long endTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        list.add(0, -2); // insert at the FRONT: shifts all 50,001 elements right
        long frontTime = System.nanoTime() - t2;

        System.out.println("advanced: end-insert time(ns) -> " + endTime);
        System.out.println("advanced: front-insert time(ns) -> " + frontTime + " (shifts every element)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `InsertDeleteShiftingCost.java`, then run `java InsertDeleteShiftingCost.java`.

## 6. Walkthrough

1. `basicLevel()` calls `insertAt(arr, 2, 30)` on `{10, 20, 40, 50}`. It copies indexes `0..1` unchanged, places `30` at index 2, then copies the remaining old elements (`40, 50`) one slot to the right — the result is `{10, 20, 30, 40, 50}`.
2. `intermediateLevel()` calls `deleteAt(arr, 2)` on `{10, 20, 30, 40, 50, 60}`. It keeps indexes `0..1`, then shifts every element after index 2 (`40, 50, 60`) one slot left, closing the gap left by the removed `30`.
3. `advancedLevel()` fills an `ArrayList` with 50,000 elements, then times two single insertions: one at the end, one at the front.
4. The end-insert should be fast (close to O(1) amortized) since nothing needs to move. The front-insert should be visibly slower, since `ArrayList` internally shifts all 50,001 existing elements one slot right to make room at index 0.

## 7. Gotchas & takeaways

> Gotcha: `ArrayList.add(0, value)` and `ArrayList.remove(0)` are both O(n), not O(1) — a loop that repeatedly inserts or removes at the front of an `ArrayList` silently becomes O(n²). If front operations are frequent, use a `LinkedList` or `ArrayDeque` instead.

- Inserting or deleting in the middle of an array costs O(n), because every later element must shift to preserve contiguity.
- Operations at the very end of an array cost O(1) (no shifting); operations at the front cost O(n) (maximum shifting).
- A linked list avoids shifting entirely for insert/delete, at the cost of losing O(1) random access.
- Related concepts: [Static (fixed-size) arrays](0015-static-fixed-size-arrays.md), [Array resizing & amortized append](0020-array-resizing-amortized-append.md).
