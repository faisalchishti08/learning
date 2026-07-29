---
card: data-structures
gi: 9
slug: in-place-vs-auxiliary-space-algorithms
title: In-place vs auxiliary-space algorithms
---

## 1. What it is

An **in-place** algorithm transforms its input using only O(1) (or sometimes O(log n), depending on convention) extra memory, beyond the input itself — it modifies the input directly rather than building a new structure. An algorithm using **auxiliary space** allocates additional memory proportional to the input size (or more) to do its work, typically making the algorithm simpler or sometimes faster, at the cost of that extra memory.

## 2. Why & when

Recognize this signal whenever a problem explicitly says "in place," "without extra space," or "O(1) extra memory" — this is a direct constraint ruling out the simplest approach (allocate a new array or structure) and requiring you to reuse the input's own storage instead. Even without an explicit constraint, this tradeoff matters whenever memory is scarce (embedded systems, very large datasets that barely fit in memory) or when minimizing garbage-collection pressure matters for performance.

## 3. Core concept

**Decision criteria:** ask whether the input can be safely overwritten (is the original order/values needed again after this operation, by this code or any caller?), and whether the transformation can be expressed using only a constant number of extra variables (indices, temporary swap variables) rather than a second full-size structure.

**Common in-place techniques:**
- **Two-pointer swapping:** reversing an array, or partitioning it (as in quicksort), using a `left` and `right` index that swap elements and move toward each other — no second array needed.
- **Using the input itself as scratch space:** marking visited cells, as in the "Set Matrix Zeroes" technique of reusing a matrix's own first row/column as marker storage, instead of separate boolean arrays.
- **Cyclic sort / index-as-hash:** placing each value at its "correct" index directly within the array (used in problems like finding a missing number in `1..n`), avoiding a separate hash set.

**Why auxiliary-space solutions are often simpler, and when that simplicity is worth the memory cost:** allocating a second array, a hash set, or a separate result list often makes an algorithm's logic much easier to write and reason about correctly — there is no risk of accidentally overwriting data you still need. For most everyday code (where memory is not tightly constrained), this simplicity is usually the right tradeoff; the effort of writing a correct in-place version is only worth it when memory truly is the bottleneck, or when a problem's constraints explicitly demand it.

**Why in-place transformations must be more careful about *order* of operations:** because the input is being modified while still being read, an in-place algorithm must ensure it never overwrites a value before that value has already been read and used — this is precisely why techniques like two-pointer swapping (never touching the same index twice from opposite directions) or processing in a specific safe order (like a last-to-first digit walk when propagating a carry) are the reliable patterns for correctness, rather than ad hoc index manipulation.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="In-place array reversal using two pointers swapping toward the center, versus an auxiliary-space approach copying into a new reversed array">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">in-place: two pointers swap, O(1) extra</text>
    <rect x="30" y="30" width="240" height="35" fill="#161b22" stroke="#3fb950"/><text x="150" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">left &lt;-&gt; right, swap, move inward</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">auxiliary: new array, O(n) extra</text>
    <rect x="410" y="30" width="240" height="35" fill="#161b22" stroke="#f0883e"/><text x="530" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">copy into new[n-1-i] = old[i]</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">same result, different memory cost</text>
  </g>
</svg>

Both approaches produce an identical reversed result — the two-pointer version reuses the original array's own storage, while the auxiliary version allocates a completely separate one.

## 5. Runnable example

The artifact below implements array reversal both ways, and measures allocated memory behavior conceptually by comparing what each approach touches.

```java
// InPlaceVsAuxiliarySpace.java
import java.util.*;

public class InPlaceVsAuxiliarySpace {

    // In-place: O(1) extra space, modifies the input array directly.
    static void reverseInPlace(int[] arr) {
        int left = 0, right = arr.length - 1;
        while (left < right) {
            int tmp = arr[left];
            arr[left] = arr[right];
            arr[right] = tmp;
            left++;
            right--;
        }
    }

    // Auxiliary space: O(n) extra space, allocates a new array.
    static int[] reverseWithAuxiliarySpace(int[] arr) {
        int n = arr.length;
        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            result[n - 1 - i] = arr[i];
        }
        return result;
    }

    public static void main(String[] args) {
        int[] original = {1, 2, 3, 4, 5};

        int[] auxResult = reverseWithAuxiliarySpace(original);
        System.out.println("auxiliary-space result: " + Arrays.toString(auxResult));
        System.out.println("original array unchanged: " + Arrays.toString(original));

        reverseInPlace(original);
        System.out.println("in-place result: " + Arrays.toString(original));
        System.out.println("original array was modified directly (no separate array returned)");
    }
}
```

**How to run:** save as `InPlaceVsAuxiliarySpace.java`, then run `java InPlaceVsAuxiliarySpace.java`.

## 6. Walkthrough

1. `reverseWithAuxiliarySpace(original)` allocates a brand-new array, `result`, and copies each element from `original` into its mirrored position. `original` itself remains completely untouched — printing it afterward shows `[1, 2, 3, 4, 5]`, unchanged.
2. `reverseInPlace(original)` instead swaps elements directly within `original`, using only two index variables (`left`, `right`) and one temporary swap variable — no second array is ever allocated.
3. Both approaches produce the same logical result (`[5, 4, 3, 2, 1]`), but `reverseWithAuxiliarySpace` returns it as a new array while leaving the input safe to reuse, whereas `reverseInPlace` returns nothing (`void`) and the caller must recognize that `original` itself has now changed.
4. This distinction matters for callers: code that still needs the *original* order after calling a reversal function must use the auxiliary-space version (or make a defensive copy first) — calling the in-place version destroys the original ordering permanently.

## 7. Gotchas & takeaways

> Gotcha: calling an in-place function on data that a caller elsewhere still expects to be unmodified is a common source of subtle bugs — always check (or clearly document) whether a function mutates its input in place versus returning a new structure, especially when refactoring code from an auxiliary-space style to an in-place one for a performance or memory optimization.

- In-place: O(1) extra memory, modifies the input directly; auxiliary space: allocates new memory proportional to input size, leaves the input untouched.
- In-place techniques (two-pointer swapping, using the input as scratch space) require careful ordering to avoid overwriting data before it has been read.
- Related concepts: [Time vs space tradeoffs](0005-time-vs-space-tradeoffs.md) (the broader framing this is a specific instance of), [Recursive vs iterative tradeoffs](0008-recursive-vs-iterative-tradeoffs.md) (an explicit stack used for an iterative rewrite is itself a form of auxiliary space, distinct from true O(1) in-place).
