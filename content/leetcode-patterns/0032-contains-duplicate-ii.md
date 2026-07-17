---
card: leetcode-patterns
gi: 32
slug: contains-duplicate-ii
title: Contains Duplicate II
---

## 1. What it is

Given an integer array `nums` and an integer `k`, return `true` if there are two distinct indices `i` and `j` such that `nums[i] == nums[j]` and the absolute difference between `i` and `j` is at most `k`. Example: `nums = [1, 2, 3, 1]`, `k = 3` → `true` (indices 0 and 3, both value `1`, distance `3`).

## 2. Why & when

"Within a window of size `k`" plus "duplicate check" is a fixed-size sliding window over a `HashSet`: maintain a set of the last `k` elements seen, and check membership before inserting each new one.

## 3. Core concept

**Key idea:** a sliding window of size `k + 1` (indices `i` and `j` within distance `k` means at most `k + 1` positions are in play at once) implemented as a `HashSet` gives O(1) duplicate checks, with the window's "shrink" step being a single removal.

**Steps:**
1. Create an empty `HashSet<Integer> window`.
2. For each index `i` from 0 to `length - 1`:
   - If `window.contains(nums[i])`, return `true` — a duplicate within distance `k` was found.
   - Add `nums[i]` to `window`.
   - If `window.size() > k`, remove `nums[i - k]` (the element that has fallen outside the allowed window).
3. If the loop finishes without finding a duplicate, return `false`.

**Why it is correct:** the set always holds exactly the elements from index `max(0, i - k)` to `i`, so checking membership before insertion only ever compares the current element against others within the allowed distance `k`. Removing the element that exits the window keeps the set from growing unbounded and keeps stale, out-of-range matches from causing false positives.

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contains duplicate sliding window hash set">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1, 2, 3, 1], k = 3</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="20" y="95" fill="#8b949e">window = {1,2,3} at i=3, size 3 <= k, no removal needed</text>
    <text x="20" y="118" fill="#8b949e">window.contains(1) -&gt; true -&gt; duplicate found within distance k</text>
  </g>
</svg>

The set always holds exactly the last `k` (or fewer) elements, giving O(1) duplicate detection within the allowed distance.

## 5. Runnable example

```java
// ContainsDuplicateII.java
import java.util.HashSet;
import java.util.Set;

public class ContainsDuplicateII {

    // Level 1 -- Brute force: check every pair of indices within distance
    // k. O(n * k) time, O(1) space.
    static boolean bruteForce(int[] nums, int k) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j <= i + k && j < nums.length; j++) {
                if (nums[i] == nums[j]) return true;
            }
        }
        return false;
    }

    // KEY INSIGHT: a fixed-size sliding window implemented as a HashSet
    // gives O(1) duplicate checks, replacing the O(k) inner scan with a
    // single membership test.

    // Level 2 -- Optimal: sliding window with a HashSet. O(n) time, O(k)
    // space.
    public static boolean containsNearbyDuplicate(int[] nums, int k) {
        Set<Integer> window = new HashSet<>();
        for (int i = 0; i < nums.length; i++) {
            if (window.contains(nums[i])) return true;
            window.add(nums[i]);
            if (window.size() > k) {
                window.remove(nums[i - k]);
            }
        }
        return false;
    }

    // Level 3 -- Hardened: k == 0 means no two distinct indices can ever
    // be within distance 0 of each other, so the method correctly returns
    // false immediately (window.size() > 0 removes every element right
    // after insertion).
    static boolean hardened(int[] nums, int k) {
        if (nums == null || k < 0) throw new IllegalArgumentException("k must be non-negative");
        return containsNearbyDuplicate(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 1};
        System.out.println("brute force: " + bruteForce(nums, 3));
        System.out.println("optimal:     " + containsNearbyDuplicate(nums, 3));
        System.out.println("k == 0:      " + hardened(new int[] {1, 1}, 0));
    }
}
```

How to run: save as `ContainsDuplicateII.java`, then run `java ContainsDuplicateII.java`.

## 6. Walkthrough

Dry run of `containsNearbyDuplicate({1, 2, 3, 1}, k = 3)`:

| i | nums[i] | window before | contains? | window after |
|---|---|---|---|---|
| 0 | 1 | {} | no | {1} |
| 1 | 2 | {1} | no | {1,2} |
| 2 | 3 | {1,2} | no | {1,2,3} |
| 3 | 1 | {1,2,3} | yes! | — |

At `i = 3`, `window` still contains `1` (size is 3, not yet exceeding `k = 3`, so no removal happened), and `nums[3] = 1` is found — return `true`. Time complexity: O(n). Space complexity: O(min(n, k)).

## 7. Gotchas & takeaways

> Gotcha: checking `window.size() >= k` instead of `> k` removes an element one step too early, shrinking the effective window to `k - 1` and potentially missing a valid duplicate at exactly distance `k`.

- This is a sliding-window variant using a `HashSet` as the window's `state`, instead of a running sum or a frequency map — the window size here is fixed at `k + 1` conceptually, capped by removing the (i-k)-th element.
- Related problems: Contains Duplicate, Contains Duplicate III (adds a value-difference constraint, usually solved with a sorted structure like a `TreeMap` or bucketing).
