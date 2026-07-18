---
card: leetcode-patterns
gi: 83
slug: cyclic-sort-template-place-each-number-at-its-index-by-swapp
title: Cyclic Sort — template: place each number at its index by swapping
---

## 1. What it is

This page gives the reusable code template for cyclic sort: a `while` loop with an index pointer that only advances when the current position holds its correct value, and a swap that sends misplaced values directly to their target index.

## 2. Why & when

Instead of re-deriving the placement loop for every problem, use one template and change only the "correct index" formula and what you do with leftover mismatches after sorting. The core loop shape — check, swap-or-advance — stays the same whether the range is `[1,n]`, `[0,n-1]`, or a range with intentional duplicates.

## 3. Core concept

**Key idea:** the template has three interchangeable parts — the formula mapping a value to its correct index, the condition that decides whether a swap is needed, and what you scan for after the main placement loop finishes (missing values, duplicates, or mismatches).

**General steps:**
1. Define `correctIndex(value)` — usually `value - 1` for range `[1,n]`, or `value` for range `[0,n-1]`.
2. Loop `i` from `0` to `n - 1`, but only advance `i` when `nums[i]` is already at `correctIndex(nums[i])`, or when `nums[i]` is out of range / a duplicate that can never be placed.
3. Otherwise, swap `nums[i]` with `nums[correctIndex(nums[i])]`.
4. After the loop, do a second pass: any index `i` where `nums[i] != correctIndex⁻¹(i)` reveals a missing number (that index's "correct" value never arrived) or, depending on the problem, a duplicate.

**Why it works:** every swap places exactly one number into a spot where it will never need to move again, since a value is only swapped away from index `i` if a *different, still out-of-place* value belongs there instead. That guarantees the total swap count is bounded by `n`, keeping the whole placement loop O(n).

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort template loop shape">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="660" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="30" y="40" fill="#e6edf3">while (i &lt; n) { if (nums[i] belongs elsewhere) swap; else i++; }</text>
    <text x="20" y="80" fill="#79c0ff">swap sends nums[i] to its correct index -- may need several swaps at the same i</text>
    <text x="20" y="105" fill="#79c0ff">advance i only when nums[i] is correctly placed, or cannot ever be placed</text>
    <text x="20" y="135" fill="#8b949e">second pass after the loop scans for indices where the "expected" value never arrived</text>
  </g>
</svg>

The same loop shape adapts to many problems by swapping only the correct-index formula and the post-loop scan for what counts as "missing" or "duplicate."

## 5. Runnable example

```java
// CyclicSortTemplate.java
import java.util.*;

public class CyclicSortTemplate {

    // The reusable placement loop: values in range [1, n].
    static void place(int[] nums) {
        int i = 0;
        while (i < nums.length) {
            int correct = nums[i] - 1;
            if (nums[i] >= 1 && nums[i] <= nums.length && nums[i] != nums[correct]) {
                int temp = nums[i];
                nums[i] = nums[correct];
                nums[correct] = temp;
            } else {
                i++;
            }
        }
    }

    // The reusable post-loop scan: find every index whose "expected"
    // value (i + 1) never arrived -- these are the missing numbers.
    static List<Integer> findMissing(int[] nums) {
        List<Integer> missing = new ArrayList<>();
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] != i + 1) missing.add(i + 1);
        }
        return missing;
    }

    public static void main(String[] args) {
        int[] nums = {4, 2, 1, 2};
        place(nums);
        System.out.println("after placement: " + Arrays.toString(nums));
        System.out.println("missing numbers: " + findMissing(nums));
    }
}
```

How to run: save as `CyclicSortTemplate.java`, then run `java CyclicSortTemplate.java`.

## 6. Walkthrough

Trace `place` on `{4, 2, 1, 2}` (note `2` is duplicated and `3` is missing):

1. `i = 0`: `nums[0] = 4`, belongs at index `3`. `nums[3] = 2 != 4`, swap: `[2, 2, 1, 4]`.
2. `i = 0`: `nums[0] = 2`, belongs at index `1`. `nums[1] = 2 == 2` already — cannot place (duplicate), advance `i = 1`.
3. `i = 1`: `nums[1] = 2`, belongs at index `1`. Already correct — advance `i = 2`.
4. `i = 2`: `nums[2] = 1`, belongs at index `0`. `nums[0] = 2 != 1`, swap: `[1, 2, 2, 4]`.
5. `i = 2`: `nums[2] = 2`, belongs at index `1`. `nums[1] = 2 == 2` already — cannot place, advance `i = 3`.
6. `i = 3`: `nums[3] = 4`, belongs at index `3`. Already correct — advance `i = 4`. Loop ends.

`findMissing` then scans: index `2` holds `2`, but expects `3` — so `3` is reported missing.

## 7. Gotchas & takeaways

> Gotcha: the `nums[i] != nums[correct]` check (not just checking whether `i == correct`) is what prevents an infinite loop when a duplicate value is already sitting at its own target index — without it, the algorithm would keep trying to swap a value with itself forever.

- Memorize the loop shape once: check-swap-or-advance during placement, then a second linear scan for whatever the problem asks about (missing, duplicate, or mismatched values).
- The post-loop scan is always O(n) and runs after the O(n) placement loop, keeping the whole template O(n) total.
