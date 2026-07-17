---
card: leetcode-patterns
gi: 26
slug: longest-mountain-in-array
title: Longest Mountain in Array
---

## 1. What it is

Given an integer array `arr`, a "mountain" is a contiguous subarray that strictly increases to a peak, then strictly decreases, with at least one element on each side of the peak (so length at least 3). Return the length of the longest mountain, or `0` if none exists. Example: `arr = [2, 1, 4, 7, 3, 2, 5]` → the longest mountain is `[1, 4, 7, 3, 2]`, length `5`.

## 2. Why & when

Finding a mountain means finding a peak, then expanding two pointers outward from it — one walking left while values keep decreasing (going backward), one walking right while values keep decreasing (going forward). This is two pointers moving in *opposite* directions from a shared center, rather than converging inward or scanning the same direction.

## 3. Core concept

**Key idea:** a valid peak is any index that is strictly greater than both of its neighbors. From each peak, expand `left` and `right` outward independently, as far as the strictly-increasing (going left) and strictly-decreasing (going right) conditions hold.

**Steps:**
1. For each index `i` from 1 to `length - 2` (only interior positions can be peaks):
   - Check if `arr[i]` is a peak: `arr[i - 1] < arr[i]` and `arr[i] > arr[i + 1]`.
   - If not a peak, skip to the next `i`.
   - If it is a peak, expand `left` from `i` while `arr[left - 1] < arr[left]` (walking backward through the increasing run).
   - Expand `right` from `i` while `arr[right + 1] < arr[right]` (walking forward through the decreasing run).
   - The mountain length is `right - left + 1`; track the maximum.
2. Return the maximum length found, or `0` if no peak existed.

**Why it is correct:** every mountain has exactly one peak (its unique maximum), so checking every interior index as a potential peak and expanding outward from valid ones finds every mountain. Because each element belongs to at most one maximal increasing run and one maximal decreasing run, the total expansion work across all peaks is bounded by O(n), not O(n²), even though it looks like nested loops.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Longest mountain expanding from a peak">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">arr = [2, 1, 4, 7, 3, 2, 5]</text>
    <polyline points="20,140 60,150 100,80 140,40 180,100 220,130 260,60" fill="none" stroke="#8b949e" stroke-width="2"/>
    <circle cx="140" cy="40" r="5" fill="#f59e0b"/>
    <text x="140" y="28" fill="#f59e0b" text-anchor="middle">peak (7)</text>
    <text x="60" y="165" fill="#79c0ff" text-anchor="middle">left expands here (1&lt;4&lt;7)</text>
    <text x="220" y="150" fill="#f0883e" text-anchor="middle">right expands here (7&gt;3&gt;2)</text>
  </g>
</svg>

Starting from the peak at value 7, `left` walks back through the strictly increasing run, `right` walks forward through the strictly decreasing run.

## 5. Runnable example

```java
// LongestMountain.java
public class LongestMountain {

    // Level 1 -- Brute force: for every pair of start and end indices,
    // check whether the subarray forms a valid mountain. O(n^3) time (or
    // O(n^2) with a smarter check) -- explores far more subarrays than
    // necessary.
    static int bruteForce(int[] arr) {
        int n = arr.length, best = 0;
        for (int start = 0; start < n; start++) {
            for (int end = start + 2; end < n; end++) {
                if (isMountain(arr, start, end)) {
                    best = Math.max(best, end - start + 1);
                }
            }
        }
        return best;
    }

    private static boolean isMountain(int[] arr, int start, int end) {
        int peak = start;
        for (int i = start; i <= end; i++) if (arr[i] > arr[peak]) peak = i;
        if (peak == start || peak == end) return false;
        for (int i = start; i < peak; i++) if (arr[i] >= arr[i + 1]) return false;
        for (int i = peak; i < end; i++) if (arr[i] <= arr[i + 1]) return false;
        return true;
    }

    // KEY INSIGHT: every mountain has exactly one peak, so scanning for
    // peaks directly and expanding two pointers outward from each one
    // finds every mountain in a single amortized linear pass.

    // Level 2 -- Optimal: find peaks, expand two pointers outward. O(n)
    // time, O(1) space.
    public static int longestMountain(int[] arr) {
        int n = arr.length, best = 0;
        for (int i = 1; i < n - 1; i++) {
            boolean isPeak = arr[i - 1] < arr[i] && arr[i] > arr[i + 1];
            if (!isPeak) continue;

            int left = i, right = i;
            while (left > 0 && arr[left - 1] < arr[left]) left--;
            while (right < n - 1 && arr[right + 1] < arr[right]) right++;

            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: a strictly increasing or strictly decreasing
    // array has no interior peak, so the loop never finds one and
    // correctly returns 0.
    static int hardened(int[] arr) {
        if (arr == null || arr.length < 3) return 0;
        return longestMountain(arr);
    }

    public static void main(String[] args) {
        int[] arr = {2, 1, 4, 7, 3, 2, 5};
        System.out.println("brute force: " + bruteForce(arr));
        System.out.println("optimal:     " + longestMountain(arr));
        System.out.println("no mountain: " + hardened(new int[] {1, 2, 3, 4}));
    }
}
```

How to run: save as `LongestMountain.java`, then run `java LongestMountain.java`.

## 6. Walkthrough

Dry run of `longestMountain({2, 1, 4, 7, 3, 2, 5})`:

1. `i = 1` (`arr[1] = 1`): `arr[0] = 2` is not less than `1`, so not a peak.
2. `i = 2` (`arr[2] = 4`): `arr[1] = 1 < 4` and `arr[3] = 7 > 4`, so `arr[2]` is not greater than its right neighbor — not a peak.
3. `i = 3` (`arr[3] = 7`): `arr[2] = 4 < 7` and `arr[4] = 3 < 7` — peak found. Expand `left`: `arr[2]=4 < arr[3]=7` so `left` moves to 2; `arr[1]=1 < arr[2]=4` so `left` moves to 1; `arr[0]=2` is not less than `arr[1]=1`, stop. `left = 1`. Expand `right`: `arr[4]=3 < arr[3]=7` so `right` moves to 4; `arr[5]=2 < arr[4]=3` so `right` moves to 5; `arr[6]=5` is not less than `arr[5]=2`, stop. `right = 5`.
4. Mountain length: `right - left + 1 = 5 - 1 + 1 = 5`.
5. `i = 4, 5` are not peaks (checked and skipped). Final answer: `5`.

Time complexity: O(n), amortized — each element is visited a bounded number of times across all peak expansions. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: using `<=` instead of `<` in the peak or expansion checks breaks the "strictly increasing/decreasing" requirement — a plateau (equal adjacent values) must NOT count as part of a mountain.

- Even though the peak-expansion looks like it could be O(n²) (a loop with an inner while), the total work across all peaks is bounded by O(n), because each array element is consumed by at most one increasing run and one decreasing run.
- Related problems: Peak Index in a Mountain Array (binary search variant, since that array is guaranteed to already be a single mountain), Valid Mountain Array.
