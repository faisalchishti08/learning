---
card: leetcode-patterns
gi: 84
slug: cyclic-sort-complexity-o-n-time-o-1-space
title: Cyclic Sort — complexity: O(n) time, O(1) space
---

## 1. What it is

This page states and proves the time and space cost of cyclic sort: O(n) time, and O(1) extra space, because every operation is either an index computation, a comparison, or an in-place swap.

## 2. Why & when

Cyclic sort beats a general-purpose sort's O(n log n) precisely because it exploits extra information — the values are known to lie in a bounded range matching the array's length. Knowing the O(n) bound in advance tells you cyclic sort is worth reaching for whenever that range condition holds, rather than defaulting to `Arrays.sort` or a hash set.

## 3. Core concept

**Time — O(n):** although the placement loop's index `i` does not always advance (a swap can leave `i` unchanged so the newly-arrived value can be checked too), every swap places at least one value into its permanently correct position. Since there are only `n` values, at most `n` swaps can ever happen across the entire run. Combined with at most `n` advances of `i`, the total work is bounded by `2n`, which is O(n).

**Space — O(1):** the algorithm sorts in place using only the input array and a constant number of index variables (`i`, `correctIndex`, and a temporary swap variable) — no auxiliary array or hash set is allocated, regardless of `n`.

**Comparison:**

| Approach | Time | Space |
|---|---|---|
| Comparison-based sort (e.g. quicksort) | O(n log n) | O(log n) to O(n) |
| Hash set to track seen values | O(n) | O(n) |
| Cyclic sort | O(n) | O(1) |

Only cyclic sort achieves both O(n) time and O(1) space — but only when the value range matches the array length.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bounding total swaps by array length">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">each swap permanently places one value -- at most n swaps possible</text>
    <rect x="20" y="40" width="500" height="20" fill="#161b22" stroke="#30363d"/>
    <rect x="20" y="40" width="500" height="20" fill="#3fb950" opacity="0.3"/>
    <text x="270" y="55" fill="#e6edf3" text-anchor="middle" font-size="11">at most n total swaps across the whole array</text>
    <text x="20" y="90" fill="#8b949e">i advances at most n times too -- total work bounded by 2n -&gt; O(n)</text>
  </g>
</svg>

Every swap fixes a value permanently, so the running total of swaps can never exceed the array's length — the loop cannot do unbounded work at any single index.

## 5. Runnable example

```java
// CyclicSortComplexity.java
import java.util.*;

public class CyclicSortComplexity {

    static int swapCount = 0;
    static int advanceCount = 0;

    static void cyclicSort(int[] nums) {
        int i = 0;
        while (i < nums.length) {
            int correct = nums[i] - 1;
            if (nums[i] >= 1 && nums[i] <= nums.length && nums[i] != nums[correct]) {
                int temp = nums[i];
                nums[i] = nums[correct];
                nums[correct] = temp;
                swapCount++;
            } else {
                i++;
                advanceCount++;
            }
        }
    }

    public static void main(String[] args) {
        int[] nums = {5, 4, 3, 2, 1};
        cyclicSort(nums);
        System.out.println("sorted: " + Arrays.toString(nums));
        System.out.println("swaps performed:    " + swapCount + " (bounded by n=" + nums.length + ")");
        System.out.println("advances performed:  " + advanceCount + " (bounded by n=" + nums.length + ")");
        System.out.println("extra space used: just i, correct, temp -- O(1), independent of n");
    }
}
```

How to run: save as `CyclicSortComplexity.java`, then run `java CyclicSortComplexity.java`.

## 6. Walkthrough

1. `nums = {5,4,3,2,1}` is the worst case for swap count — every element starts in exactly the wrong place.
2. Each swap during the run moves one value into its final position, never to be touched again — so the running `swapCount` climbs but is capped once every value is placed.
3. After the sort finishes, `swapCount + advanceCount` together equal the total loop iterations, and both counts are bounded by `n = 5`.
4. The array becomes `{1,2,3,4,5}`, and the program prints exact counts confirming the O(n) bound empirically for this input.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to assume the loop is O(n²) because `i` sometimes does not advance after a swap — but the key insight is that **swaps**, not iterations of `i`, are the thing that could repeat, and swaps are strictly capped at `n` because each one is a one-way, permanent placement.

- Reach for cyclic sort whenever a problem's constraints say "array of `n` numbers in range `[1,n]`" (or `[0,n-1]`) and asks for O(n) time, O(1) space.
- The O(1) space guarantee is what makes cyclic sort preferable to a hash-set approach in memory-constrained or large-`n` scenarios.
