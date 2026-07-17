---
card: leetcode-patterns
gi: 11
slug: intersection-of-two-arrays-ii
title: Intersection of Two Arrays II
---

## 1. What it is

Given two integer arrays `nums1` and `nums2`, return an array of their intersection. Each element in the result should appear as many times as it shows in both arrays (respecting the minimum count), and the result can be in any order. Example: `nums1 = [1, 2, 2, 1]`, `nums2 = [2, 2]` → result `[2, 2]`.

## 2. Why & when

This problem is usually solved with a hash map counting frequencies — that works on unsorted input in O(n + m) time and O(n) space. But if the arrays are **sorted** (or you sort them first), two pointers solves it in O(1) extra space (beyond the output and beyond the sort itself), which is the version worth knowing because interviewers often ask the follow-up: "what if the arrays are already sorted?" or "what if `nums1`'s size is small compared to `nums2`, which is stored on disk?" — both point to the two-pointers approach over the hash map.

## 3. Core concept

**Key idea:** with both arrays sorted, walking one pointer through each array at the same time lets you find matches without a hash map, because a mismatch tells you exactly which pointer to advance.

**Steps:**
1. Sort `nums1` and `nums2` if they are not already sorted.
2. Set `i = 0`, `j = 0`, and an empty result list.
3. While `i < nums1.length` and `j < nums2.length`:
   - If `nums1[i] == nums2[j]`, it is a match — add it to the result, then `i++`, `j++`.
   - If `nums1[i] < nums2[j]`, `nums1[i]` cannot match anything in `nums2` from `j` onward (since `nums2` is sorted and everything from `j` on is `>= nums2[j] > nums1[i]`) — advance `i`.
   - Otherwise, symmetric reasoning says advance `j`.
4. Return the result list as an array.

**Why it is correct:** unlike the opposite-ends layout, here both pointers move in the *same* direction (left to right) but through two *different* arrays — this is a same-direction, two-array variant of the pattern, sometimes called the "merge" pattern because it mirrors merge sort's merge step. Each comparison rules out one element from one array for good, so the total number of steps is bounded by `nums1.length + nums2.length`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Intersection of two sorted arrays with independent pointers">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums1 = [1, 2, 2, 1] -&gt; sorted [1, 1, 2, 2]</text>
    <text x="20" y="44" fill="#e6edf3">nums2 = [2, 2]      -&gt; sorted [2, 2]</text>
    <rect x="20" y="60" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="60" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="60" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="60" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="40" y="80" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="80" y="80" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="120" y="80" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="160" y="80" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="20" y="100" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="60" y="100" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="40" y="120" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="80" y="120" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="150" fill="#8b949e">nums1[i]=1 &lt; nums2[j]=2 -&gt; i++ (1 can't match anything left in nums2)</text>
  </g>
</svg>

Two independent pointers walk two different sorted arrays; a mismatch always tells you exactly which one to advance.

## 5. Runnable example

```java
// IntersectionII.java
import java.util.*;

public class IntersectionII {

    // Level 1 -- Brute force: hash map counts frequencies of nums1, then
    // scan nums2 decrementing counts. O(n + m) time, O(n) space -- works on
    // unsorted input but does not exploit sortedness at all.
    static int[] bruteForce(int[] nums1, int[] nums2) {
        Map<Integer, Integer> count = new HashMap<>();
        for (int v : nums1) count.merge(v, 1, Integer::sum);
        List<Integer> result = new ArrayList<>();
        for (int v : nums2) {
            int c = count.getOrDefault(v, 0);
            if (c > 0) {
                result.add(v);
                count.put(v, c - 1);
            }
        }
        return result.stream().mapToInt(Integer::intValue).toArray();
    }

    // KEY INSIGHT: once both arrays are sorted, a mismatch between
    // nums1[i] and nums2[j] proves one of them can never match anything
    // remaining in the other array -- so two independent pointers replace
    // the hash map entirely.

    // Level 2 -- Optimal: two pointers over sorted arrays. O(n log n + m log m)
    // for the sort (O(n + m) if already sorted), O(1) extra space beyond output.
    public static int[] intersect(int[] nums1, int[] nums2) {
        Arrays.sort(nums1);
        Arrays.sort(nums2);
        List<Integer> result = new ArrayList<>();
        int i = 0, j = 0;
        while (i < nums1.length && j < nums2.length) {
            if (nums1[i] == nums2[j]) {
                result.add(nums1[i]);
                i++;
                j++;
            } else if (nums1[i] < nums2[j]) {
                i++;
            } else {
                j++;
            }
        }
        return result.stream().mapToInt(Integer::intValue).toArray();
    }

    // Level 3 -- Hardened: one array empty, or no overlap at all, both
    // terminate the while loop immediately with an empty result -- no
    // extra branch needed.
    static int[] hardened(int[] nums1, int[] nums2) {
        if (nums1 == null || nums2 == null) {
            throw new IllegalArgumentException("inputs must not be null");
        }
        return intersect(nums1, nums2);
    }

    public static void main(String[] args) {
        int[] nums1 = {1, 2, 2, 1};
        int[] nums2 = {2, 2};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums1, nums2)));
        System.out.println("optimal:     " + Arrays.toString(intersect(nums1, nums2)));

        int[] noOverlap = {8, 9};
        System.out.println("no overlap: " + Arrays.toString(hardened(noOverlap, new int[] {1, 2})));
    }
}
```

How to run: save as `IntersectionII.java`, then run `java IntersectionII.java`.

## 6. Walkthrough

Dry run of `intersect` on sorted `nums1 = [1, 1, 2, 2]`, `nums2 = [2, 2]`:

| step | i | j | nums1[i] | nums2[j] | action |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 2 | 1 < 2, i++ |
| 2 | 1 | 0 | 1 | 2 | 1 < 2, i++ |
| 3 | 2 | 0 | 2 | 2 | match, add 2, i++, j++ |
| 4 | 3 | 1 | 2 | 2 | match, add 2, i++, j++ |
| 5 | 4 | 2 | — | — | j out of bounds, loop ends |

Result: `[2, 2]`. Time complexity: O(n log n + m log m) if a sort is needed, O(n + m) for the merge scan itself. Space complexity: O(1) extra, beyond the output list and the in-place sort.

## 7. Gotchas & takeaways

> Gotcha: this is a **two-array** variant of two pointers, not the single-array opposite-ends or same-direction shapes — both pointers move left to right, but each walks a *different* array. Do not confuse it with the pair-sum pattern, which uses one array and two pointers converging inward.

- If the arrays are already sorted, skip the sort and this becomes a straight O(n + m) merge-style scan.
- The hash-map approach is still correct on unsorted data and is simpler to write; use two pointers when the interviewer specifically asks about sorted input or memory constraints.
- Related problems: Intersection of Two Arrays (unique elements only, no duplicate counts), Merge Sorted Array, Find the Difference of Two Arrays.
