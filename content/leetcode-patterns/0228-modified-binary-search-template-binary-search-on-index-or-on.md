---
card: leetcode-patterns
gi: 228
slug: modified-binary-search-template-binary-search-on-index-or-on
title: Modified Binary Search — template: binary search on index or on the answer
---

## 1. What it is

Two reusable loop skeletons cover almost every problem in this family: the **search-on-index template** (find a target value inside a sorted, possibly rotated, array) and the **search-on-answer template** (find the boundary where a monotonic condition flips, over a numeric range).

## 2. Why & when

Memorizing these templates means you spend your problem-solving time on the CONDITION (what makes `mid` too small, too big, or a match) instead of re-deriving the loop bounds and off-by-one details from scratch every time. Off-by-one mistakes (`<` versus `<=`, `mid` versus `mid + 1`) are the most common bug source in binary search, so a fixed, memorized shape avoids them.

Use the index template whenever you have an actual sorted array (rotated or not) and are looking for a target value or an insertion point. Use the answer template whenever there is no array — only a range of candidate values and a yes/no predicate that is monotonic across that range.

## 3. Core concept

**Search-on-index template.**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2` (avoids integer overflow).
3. If `nums[mid] == target`, return `mid`.
4. If the array is rotated, first decide which half (`lo..mid` or `mid..hi`) is properly sorted, then check whether `target` falls within that sorted half's range; move `lo` or `hi` accordingly.
5. If not rotated, simply compare `target` to `nums[mid]`: move `hi = mid - 1` if `target < nums[mid]`, else `lo = mid + 1`.
6. If the loop ends without a match, the target is not present (return `-1`, or `lo` if you need the insertion point).

**Search-on-answer template.**
1. Set `lo` and `hi` to the smallest and largest possible answer values.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `check(mid)` is true (the condition you want holds), the answer could be `mid` or smaller: set `hi = mid`.
4. Otherwise, the answer must be larger: set `lo = mid + 1`.
5. When the loop ends, `lo == hi` is the boundary — the smallest value where `check` is true.

The key insight shared by both templates: every iteration must strictly shrink the range (`lo` or `hi` always moves past `mid`, never staying put), or the loop can run forever or skip the correct answer.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Search on index narrows lo and hi around array positions; search on answer narrows lo and hi around a boundary value">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Search on index: lo &lt;= hi, return mid on match</text>
    <rect x="20" y="35" width="200" height="24" fill="#161b22" stroke="#30363d"/>
    <rect x="90" y="35" width="30" height="24" fill="#3fb950"/><text x="105" y="52" fill="#0d1117" text-anchor="middle" font-size="10">mid</text>
    <text x="20" y="80" fill="#8b949e">nums[mid] &lt; target -&gt; lo = mid + 1 (drop left half)</text>

    <text x="20" y="120" fill="#e6edf3" font-weight="bold">Search on answer: lo &lt; hi, converge to boundary</text>
    <rect x="20" y="135" width="24" height="24" fill="#161b22" stroke="#f85149"/><rect x="46" y="135" width="24" height="24" fill="#161b22" stroke="#f85149"/>
    <rect x="72" y="135" width="24" height="24" fill="#3fb950"/><text x="84" y="152" fill="#0d1117" text-anchor="middle" font-size="9">mid</text>
    <rect x="98" y="135" width="24" height="24" fill="#3fb950"/>
    <text x="20" y="180" fill="#8b949e">check(mid) true -&gt; hi = mid (boundary is here or earlier)</text>
  </g>
</svg>

The index template ends when `lo` passes `hi` (a match was found earlier, or it never existed). The answer template ends when `lo` and `hi` meet exactly at the boundary.

## 5. Runnable example

```java
// BinarySearchTemplates.java
public class BinarySearchTemplates {

    // Search-on-index: plain sorted array.
    static int searchIndex(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    // Search-on-answer: smallest x in [lo, hi] where check(x) is true.
    interface Check { boolean test(int x); }

    static int searchAnswer(int lo, int hi, Check check) {
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (check.test(mid)) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    public static void main(String[] args) {
        int[] nums = {2, 5, 8, 12, 16, 23, 38, 56, 72, 91};
        System.out.println("searchIndex(38): " + searchIndex(nums, 38));
        // 6

        int n = 30;
        int smallestSquareAtLeastN = searchAnswer(0, n, x -> (long) x * x >= n);
        System.out.println("smallest x with x*x >= 30: " + smallestSquareAtLeastN);
        // 6
    }
}
```

**How to run:** `java BinarySearchTemplates.java`

## 6. Walkthrough

1. `searchIndex(nums, 38)`: `lo=0, hi=9`. `mid=4`, `nums[4]=16 < 38`, so `lo=5`.
2. `mid=7`, `nums[7]=56 > 38`, so `hi=6`.
3. `mid=5`, `nums[5]=23 < 38`, so `lo=6`.
4. `mid=6`, `nums[6]=38 == 38`, return `6`. Found in 3 comparisons instead of scanning 7 elements.
5. `searchAnswer(0, 30, check)`: `lo=0, hi=30`. Each step halves the range, checking `mid*mid >= 30`, converging until `lo == hi == 6`, the smallest value satisfying the condition.

## 7. Gotchas & takeaways

> Gotcha: using `mid = (lo + hi) / 2` instead of `mid = lo + (hi - lo) / 2` can overflow `int` when `lo` and `hi` are both large, silently producing a negative `mid` and an incorrect search — always use the overflow-safe form.

- Index template: loop condition is `lo <= hi` (both bounds are still valid candidates); update `lo`/`hi` to `mid ± 1` (exclude `mid` once checked).
- Answer template: loop condition is `lo < hi` (searching for a boundary, not a specific index); update `hi = mid` (include `mid`, since it might BE the answer) or `lo = mid + 1`.
- This exact pair of templates, with the array-vs-rotated comparison or the `check` predicate swapped in, is the direct basis for every named problem in this section.
