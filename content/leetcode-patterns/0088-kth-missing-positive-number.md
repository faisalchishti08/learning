---
card: leetcode-patterns
gi: 88
slug: kth-missing-positive-number
title: Kth Missing Positive Number
---

## 1. What it is

Given a strictly increasing array of positive integers `arr` and an integer `k`, find the `k`th positive integer that is missing from `arr`. Example: `arr = [2,3,4,7,11]`, `k = 5` → `9` (missing positives in order are `1, 5, 6, 8, 9, ...`; the 5th one is `9`).

## 2. Why & when

This problem sits in the Cyclic Sort section because it shares the same "value versus position" reasoning: since `arr` is sorted and strictly increasing, the number of missing positives *before* any given array position can be computed directly by comparing the value at that position to what a "no gaps" array would hold there. That direct index-to-value relationship is the same core idea cyclic sort exploits, applied here to counting instead of swapping.

## 3. Core concept

**Key idea:** if there were no missing numbers, `arr[i]` would equal `i + 1`. The actual number of missing positives *up to and including index `i`* equals `arr[i] - (i + 1)`. Because `arr` is strictly increasing, this "missing count so far" only ever increases or stays flat as `i` grows — so binary search can find the exact index where the missing count first reaches `k`.

**Steps:**
1. Binary search over indices `0` to `n - 1` (or `n`, to allow "past the end").
2. At each midpoint `mid`, compute `missingBefore = arr[mid] - (mid + 1)`.
3. If `missingBefore < k`, not enough missing numbers appear before this index — search the right half.
4. Otherwise, search the left half (including `mid`).
5. After binary search converges on the smallest index where `missingBefore >= k`, the answer is `k + left`, where `left` is that index (equivalently, the count of missing numbers found at the last position that had fewer than `k` missing).

**Why it is correct:** the formula `arr[i] - (i + 1)` counts exactly how many positive integers are missing among the values `1` through `arr[i]`. This count is non-decreasing as `i` increases (since `arr` is strictly increasing), which is exactly the monotonic condition binary search needs to find the boundary where the count first reaches `k`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Missing count growing monotonically across a sorted array">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">arr = [2, 3, 4, 7, 11], missing before each index:</text>
    <text x="20" y="45" fill="#8b949e">i=0: arr[0]-1 = 2-1 = 1</text>
    <text x="20" y="65" fill="#8b949e">i=1: arr[1]-2 = 3-2 = 1</text>
    <text x="20" y="85" fill="#8b949e">i=2: arr[2]-3 = 4-3 = 1</text>
    <text x="20" y="105" fill="#f0883e">i=3: arr[3]-4 = 7-4 = 3 (5,6 became missing between arr[2] and arr[3])</text>
    <text x="20" y="125" fill="#8b949e">i=4: arr[4]-5 = 11-5 = 6</text>
    <text x="20" y="150" fill="#3fb950">k=5 first reached between index 3 (count 3) and index 4 (count 6) -&gt; answer is 9</text>
  </g>
</svg>

The "missing count so far" only increases as the index grows — exactly the monotonic structure binary search needs to zero in on the position where the `k`th missing number appears.

## 5. Runnable example

```java
// KthMissingPositiveNumber.java
public class KthMissingPositiveNumber {

    // Level 1 -- Brute force: walk through positive integers one at a
    // time, checking membership in arr, counting misses until the kth
    // is found. O(n) time (using a pointer into arr) but conceptually a
    // full linear scan -- wastes the sorted structure's binary-searchable
    // monotonic property.
    static int bruteForce(int[] arr, int k) {
        int arrIndex = 0, missingCount = 0, candidate = 1;
        while (true) {
            if (arrIndex < arr.length && arr[arrIndex] == candidate) {
                arrIndex++;
            } else {
                missingCount++;
                if (missingCount == k) return candidate;
            }
            candidate++;
        }
    }

    // KEY INSIGHT: arr[i] - (i + 1) counts exactly how many positive
    // integers are missing up to arr[i], and this count is monotonically
    // non-decreasing -- so binary search finds the kth missing number in
    // O(log n) instead of a full linear scan.

    // Level 2 -- Optimal: binary search on the monotonic missing-count
    // function. O(log n) time, O(1) space.
    public static int findKthPositive(int[] arr, int k) {
        int left = 0, right = arr.length;
        while (left < right) {
            int mid = left + (right - left) / 2;
            int missingBefore = arr[mid] - (mid + 1);
            if (missingBefore < k) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        return left + k;
    }

    // Level 3 -- Hardened: the missing number falls entirely beyond the
    // end of the array (e.g. k is larger than any gap inside arr).
    static int hardened(int[] arr, int k) {
        return findKthPositive(arr, k);
    }

    public static void main(String[] args) {
        int[] arr = {2, 3, 4, 7, 11};
        System.out.println("brute force: " + bruteForce(arr, 5));
        System.out.println("optimal:     " + findKthPositive(arr, 5));

        int[] noGapsUntilEnd = {1, 2, 3, 4};
        System.out.println("past the end (expect 8): " + hardened(noGapsUntilEnd, 4));
    }
}
```

How to run: save as `KthMissingPositiveNumber.java`, then run `java KthMissingPositiveNumber.java`.

## 6. Walkthrough

Dry run of `findKthPositive({2,3,4,7,11}, 5)`:

| step | left | right | mid | arr[mid] | missingBefore | missingBefore &lt; k? | action |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 5 | 2 | 4 | 4-3=1 | 1<5 yes | left=3 |
| 2 | 3 | 5 | 4 | 11 | 11-5=6 | 6<5 no | right=4 |
| 3 | 3 | 4 | 3 | 7 | 7-4=3 | 3<5 yes | left=4 |

`left == right == 4`, loop ends. Return `left + k = 4 + 5 = 9`. Matches the expected answer. Time complexity: O(log n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: the final answer formula is `left + k`, not `arr[left] + something` — it is easy to reach for the array value at the converged index, but the correct answer is derived purely from the index and `k`, since `left` represents how many array elements come before the answer.

- Although grouped with cyclic sort, this problem's real technique is binary search over a derived monotonic function — recognizing "count of missing so far" as monotonic is the key transferable idea.
- Related problems: Missing Number (a direct sum/XOR approach for a single missing value), Find All Numbers Disappeared in an Array (lists every missing value instead of finding just the kth).
