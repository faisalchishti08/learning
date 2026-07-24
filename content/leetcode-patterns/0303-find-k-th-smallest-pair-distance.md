---
card: leetcode-patterns
gi: 303
slug: find-k-th-smallest-pair-distance
title: Find K-th Smallest Pair Distance
---

## 1. What it is

The "distance" of a pair of integers is the absolute difference between them. Given an integer array `nums` and an integer `k`, return the `k`-th smallest distance among all pairs `nums[i], nums[j]` with `i < j`. Example: `nums = [1,3,1]`, `k = 1` → `0` (the pair `(1,1)` has distance `0`, the smallest possible).

## 2. Why & when

At first glance this looks like a K-way Merge, since sorting `nums` creates, for each starting index `i`, a sequence of distances to later elements that grows as the second index increases. In practice, though, the number of pairs is O(n²), too many to merge with a heap efficiently — this problem is included here to teach you to RECOGNIZE when a superficial K-way-Merge shape is better solved with BINARY SEARCH ON THE ANSWER instead. Use this shape whenever a problem asks for the `k`-th smallest of a value that is expensive to enumerate directly, but easy to COUNT how many are less than or equal to a guess.

## 3. Core concept

**Key idea:** binary-search over the possible DISTANCE VALUE (from `0` to `max(nums) - min(nums)`). For a candidate distance `mid`, count how many pairs have distance `<= mid` using a two-pointer sweep over the SORTED array; if that count is `>= k`, the answer is `<= mid`, so search lower; otherwise search higher.

**Steps:**
1. Sort `nums` ascending.
2. Binary search `lo = 0`, `hi = nums[n-1] - nums[0]` (the largest possible distance).
3. For each `mid = (lo + hi) / 2`, count pairs with distance `<= mid`: use a sliding window with two pointers `left` and `right`; for each `right`, advance `left` while `nums[right] - nums[left] > mid`; add `right - left` to the count (every index between `left` and `right` forms a valid pair with `right`).
4. If `count >= k`, set `hi = mid` (the answer might be this small or smaller). Otherwise, set `lo = mid + 1`.
5. When `lo == hi`, that value is the `k`-th smallest pair distance.

**Why it is correct:** the count of pairs with distance `<= x` is a MONOTONIC function of `x` — as `x` grows, the count can only stay the same or increase, never decrease. That monotonicity is exactly what makes binary search valid: you are searching for the smallest `x` where "count of pairs `<= x`" first reaches `k`, which is precisely the `k`-th smallest distance. The two-pointer count works because, on a sorted array, once `nums[right] - nums[left] > mid`, every index before `left` would only make the difference bigger, so `left` only ever needs to move forward, never backward.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary search over candidate distance values, counting pairs within each guess with a two-pointer sweep on the sorted array">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums sorted = [1,1,3], k = 1</text>
    <text x="10" y="45">binary search distance in [0, 3-1=2]</text>
    <text x="10" y="65">try mid=1: count pairs with distance &lt;=1 -&gt; (1,1) dist 0 -&gt; count=1</text>
    <text x="10" y="85">count(1) &gt;= k(1) -&gt; answer &lt;= 1, search lower half</text>
    <text x="10" y="105">try mid=0: count pairs with distance &lt;=0 -&gt; (1,1) dist 0 -&gt; count=1 &gt;= 1</text>
    <rect x="10" y="120" width="150" height="24" fill="#3fb950"/><text x="85" y="137" fill="#0d1117" text-anchor="middle" font-size="10">answer = 0</text>
  </g>
</svg>

Binary search narrows in on the smallest distance value whose pair-count first reaches `k`.

## 5. Runnable example

```java
// KthSmallestPairDistance.java
import java.util.Arrays;

public class KthSmallestPairDistance {

    // Level 1 -- Brute force: compute all O(n^2) pair distances, sort
    // them, return the k-th smallest. Correct, but O(n^2 log(n^2)),
    // and O(n^2) memory for storing every distance.

    // KEY INSIGHT: "count of pairs with distance <= x" is monotonic in
    // x, so binary search the ANSWER (the distance value), using a
    // fast two-pointer count instead of enumerating every pair.

    // Level 2 -- Optimal: binary search + two-pointer count, O(n log n
    // + n log(maxDistance)).
    static int smallestDistancePair(int[] nums, int k) {
        Arrays.sort(nums);
        int lo = 0, hi = nums[nums.length - 1] - nums[0];

        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (countPairsWithinDistance(nums, mid) >= k) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        return lo;
    }

    static int countPairsWithinDistance(int[] nums, int maxDist) {
        int count = 0, left = 0;
        for (int right = 0; right < nums.length; right++) {
            while (nums[right] - nums[left] > maxDist) {
                left++;
            }
            count += right - left;
        }
        return count;
    }

    // Level 3 -- Hardened: works when all elements are equal (every
    // pair has distance 0, and any k up to the total pair count
    // correctly returns 0) and when k equals the total number of
    // pairs (returns the maximum possible distance).

    public static void main(String[] args) {
        System.out.println(smallestDistancePair(new int[]{1, 3, 1}, 1));
        // 0
        System.out.println(smallestDistancePair(new int[]{1, 1, 1}, 2));
        // 0
    }
}
```

**How to run:** `java KthSmallestPairDistance.java`

## 6. Walkthrough

Trace `smallestDistancePair([1,3,1], 1)`, after sorting to `[1,1,3]`:

| lo | hi | mid | countPairsWithinDistance(mid) | count &gt;= k(1)? | next |
|---|---|---|---|---|---|
| 0 | 2 | 1 | pairs: (1,1) dist 0 -&gt; count=1 | yes | hi = 1 |
| 0 | 1 | 0 | pairs: (1,1) dist 0 -&gt; count=1 | yes | hi = 0 |
| 0 | 0 | — | loop ends, lo == hi == 0 | — | return 0 |

Final answer: `0`. Time complexity is O(n log n) to sort, plus O(n log D) for the binary search, where `D` is the maximum possible distance and each of its O(log D) iterations does an O(n) two-pointer count. Space is O(1) extra, beyond the sort.

## 7. Gotchas & takeaways

> Gotcha: this problem LOOKS like it belongs to K-way Merge (sorted array, generate distances by index pairs, sounds mergeable), but the number of implicit "sequences" is O(n), each up to O(n) long, making a heap-based merge cost O(n² log n) in the worst case — recognizing that the ANSWER RANGE is small and the count function is monotonic is what unlocks the much faster binary-search approach.

- The general technique — "binary search the answer, count how many candidates satisfy `<= mid`" — applies whenever a `k`-th smallest/largest value is hard to enumerate directly but easy to COUNT against a guess.
- The two-pointer count only works because `nums` is sorted first; without sorting, `nums[right] - nums[left]` would not shrink monotonically as `left` advances.
- Related problems: Kth Smallest Element in a Sorted Matrix (also has a binary-search-on-value alternative to its heap solution), Median of Two Sorted Arrays (another binary-search-on-answer problem hiding behind a merge-like setup).
