---
card: leetcode-patterns
gi: 229
slug: modified-binary-search-complexity-o-log-n-time
title: Modified Binary Search — complexity: O(log n) time
---

## 1. What it is

This page explains why binary search runs in O(log n) time no matter which shape (index or answer) you use, why that is the best possible complexity for this family, and lists the named problems that use this pattern.

## 2. Why & when

Interviewers expect you to justify the O(log n) bound, not just state it. Explaining "each comparison discards half the remaining candidates, so after k comparisons only n / 2^k candidates remain, and that shrinks to 1 after about log2(n) steps" shows you understand WHY halving produces a logarithm, not just that binary search is "fast."

## 3. Core concept

**Time: O(log n).** Start with `n` candidates. Each comparison at `mid` eliminates half of them. After one comparison, `n / 2` remain. After two, `n / 4`. After `k` comparisons, `n / 2^k` remain. The loop ends when only one candidate is left, which happens when `n / 2^k = 1`, i.e. `k = log2(n)`. So the number of comparisons — and therefore the time — grows proportionally to `log2(n)`.

**Space: O(1) iterative, O(log n) if written recursively.** The iterative template (the one used throughout this section) only tracks `lo`, `hi`, and `mid` — three variables, regardless of `n`. A recursive version would use O(log n) stack frames, one per halving step, which is why the iterative form is preferred in practice.

**Why this is optimal.** Any correct search algorithm that only compares the target against elements (a "comparison-based" search) must make at least log2(n) comparisons in the worst case, because each comparison has only two useful outcomes (go left or go right), and you need enough comparisons to distinguish between all `n` possible positions. Binary search achieves this lower bound exactly, so it cannot be asymptotically improved for a general sorted array.

**Cost of rotation or an answer-range does not change the bound.** Adding the "which half is sorted" check for rotated arrays, or swapping the target comparison for a `check(mid)` predicate, is still O(1) extra work per iteration — the number of iterations is still O(log n).

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Search space of 16 items shrinks by half each comparison, reaching 1 after 4 steps">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=16 candidates</text>
    <rect x="10" y="30" width="160" height="18" fill="#3fb950"/><text x="180" y="44">16 -&gt; after 1 compare: 8</text>
    <rect x="10" y="55" width="80" height="18" fill="#3fb950"/><text x="180" y="69">8 -&gt; after 2 compares: 4</text>
    <rect x="10" y="80" width="40" height="18" fill="#3fb950"/><text x="180" y="94">4 -&gt; after 3 compares: 2</text>
    <rect x="10" y="105" width="20" height="18" fill="#3fb950"/><text x="180" y="119">2 -&gt; after 4 compares: 1</text>
    <text x="10" y="150">4 compares = log2(16); doubling n only adds ONE more compare</text>
  </g>
</svg>

Every comparison halves the remaining candidates, so the number of comparisons needed grows as the logarithm of the input size, not linearly with it.

## 5. Runnable example

```java
// ComplexityCheck.java
public class ComplexityCheck {

    static int searchIndexCounted(int[] nums, int target, int[] comparisons) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            comparisons[0]++;
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    public static void main(String[] args) {
        int n = 1_000_000;
        int[] nums = new int[n];
        for (int i = 0; i < n; i++) nums[i] = i;

        int[] comparisons = {0};
        searchIndexCounted(nums, n - 1, comparisons);

        double expected = Math.log(n) / Math.log(2);
        System.out.println("n=" + n);
        System.out.println("comparisons used: " + comparisons[0]);
        System.out.println("log2(n) ~= " + expected);
        // comparisons used should land close to ceil(log2(n)) = 20
    }
}
```

**How to run:** `java ComplexityCheck.java`

## 6. Walkthrough

1. `nums` has 1,000,000 sorted elements.
2. Searching for the last element (`n - 1`) forces the algorithm through nearly the worst-case number of comparisons.
3. `log2(1,000,000)` is approximately `19.93`, so the algorithm should need about 20 comparisons.
4. Running the code confirms the actual comparison count matches this bound closely, not the 1,000,000 a linear scan would need in the worst case.
5. This confirms the practical benefit: doubling the input size from 1,000,000 to 2,000,000 would only add ONE more comparison, not double the work — the defining property of logarithmic growth.

## 7. Gotchas & takeaways

> Gotcha: assuming binary search is always faster in absolute terms for small inputs is wrong — for very small arrays, a linear scan can be faster in practice due to lower constant overhead per step, even though binary search wins asymptotically as `n` grows.

- Time: O(log n) for both the search-on-index and search-on-answer shapes, since both halve the remaining range every iteration.
- Space: O(1) for the iterative template used throughout this section; avoid the recursive form in an interview unless asked, since it costs O(log n) stack space for no benefit.
- Reference problems that use this pattern: Binary Search, Search Insert Position, First Bad Version, Sqrt(x), Guess Number Higher or Lower, Arranging Coins, Search in Rotated Sorted Array, Find Minimum in Rotated Sorted Array, Find First and Last Position of Element in Sorted Array.
