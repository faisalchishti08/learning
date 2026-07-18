---
card: leetcode-patterns
gi: 62
slug: find-the-duplicate-number
title: Find the Duplicate Number
---

## 1. What it is

Given an array `nums` of `n + 1` integers where each integer is in the range `[1, n]`, there is exactly one repeated number (it may repeat more than once). Find that duplicate, without modifying the array and using only O(1) extra space. Example: `nums = [1,3,4,2,2]` → answer `2`.

## 2. Why & when

Sorting the array or using a hash set both find the duplicate easily, but sorting costs O(n log n) time (and modifies the array), and a hash set costs O(n) extra space. The constraint "O(1) space, do not modify the array" rules both out — and is a strong hint that this is really a hidden linked-list-cycle problem.

## 3. Core concept

**Key idea:** treat each index `i` as a "node" and the value `nums[i]` as the "next pointer" — that is, "node `i` points to node `nums[i]`". Because two different indices share the same duplicate value, two different "nodes" point to the same "next node", which forces a cycle to exist in this implicit linked list. Finding the duplicate becomes finding the start of that cycle — the exact problem solved in Linked List Cycle II.

**Steps:**
1. Define the implicit "next" function: `next(i) = nums[i]`.
2. Run Phase 1 of fast & slow pointers starting from index `0`: `slow = nums[slow]`, `fast = nums[nums[fast]]`, until `slow == fast`.
3. Run Phase 2: reset `slow2 = 0`. Move `slow2` and `slow` (formerly `fast`'s partner) one step at a time until they meet.
4. Return the meeting value — it is the cycle's entrance, which is exactly the duplicate number.

**Why it is correct:** the pigeonhole principle guarantees a duplicate exists, since there are `n + 1` values crammed into the range `[1, n]`. That duplicate value is pointed to by at least two different indices, which means the implicit linked list of "index points to value" must loop back on itself — the exact structure that Linked List Cycle II is built to solve, and its algebraic proof (distance from start to cycle entrance) applies unchanged.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array treated as an implicit linked list via index-to-value pointers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [1, 3, 4, 2, 2], indices 0..4, "next" of i is nums[i]</text>
    <circle cx="60" cy="90" r="20" fill="#161b22" stroke="#79c0ff"/><text x="60" y="95" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="140" cy="90" r="20" fill="#161b22" stroke="#79c0ff"/><text x="140" y="95" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="220" cy="90" r="20" fill="#161b22" stroke="#f0883e"/><text x="220" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="300" cy="90" r="20" fill="#161b22" stroke="#f0883e"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="380" cy="90" r="20" fill="#161b22" stroke="#f0883e"/><text x="380" y="95" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="80" y1="90" x2="120" y2="90" stroke="#8b949e" marker-end="url(#f)"/>
    <line x1="160" y1="90" x2="200" y2="90" stroke="#8b949e" marker-end="url(#f)"/>
    <line x1="240" y1="90" x2="280" y2="90" stroke="#8b949e" marker-end="url(#f)"/>
    <line x1="320" y1="90" x2="360" y2="90" stroke="#8b949e" marker-end="url(#f)"/>
    <path d="M380,110 C380,150 220,150 220,110" fill="none" stroke="#8b949e" marker-end="url(#f)"/>
    <defs><marker id="f" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="180" fill="#8b949e">index 0 -&gt; value 1 -&gt; index 1 -&gt; value 3 -&gt; index 3 -&gt; value 2 -&gt; index 2 -&gt; value 4 -&gt; index 4 -&gt; value 2 (cycle back to index 2)</text>
  </g>
</svg>

Two different indices (`3` and `4`) both point to value `2`, so the implicit chain of "index points to value" loops back on itself at `2` — the cycle's entrance is the duplicate.

## 5. Runnable example

```java
// FindTheDuplicateNumber.java
public class FindTheDuplicateNumber {

    // Level 1 -- Brute force: hash set of seen values. O(n) time, O(n)
    // space -- wastes memory and technically counts as "extra space".
    static int bruteForce(int[] nums) {
        java.util.Set<Integer> seen = new java.util.HashSet<>();
        for (int num : nums) {
            if (!seen.add(num)) return num;
        }
        throw new IllegalArgumentException("no duplicate found");
    }

    // KEY INSIGHT: treating index i as a node and nums[i] as its "next
    // pointer" turns "find the duplicate" into "find where the implicit
    // linked list's cycle begins" -- reusing Linked List Cycle II exactly.

    // Level 2 -- Optimal: fast &amp; slow pointers over index-to-value
    // "pointers". O(n) time, O(1) space, array untouched.
    public static int findDuplicate(int[] nums) {
        int slow = nums[0], fast = nums[0];
        do {
            slow = nums[slow];
            fast = nums[nums[fast]];
        } while (slow != fast);

        int ptr = nums[0];
        while (ptr != slow) {
            ptr = nums[ptr];
            slow = nums[slow];
        }
        return ptr;
    }

    // Level 3 -- Hardened: the duplicate value appears more than twice
    // (e.g. [2,2,2,2,2]) -- the same cycle logic still applies, since
    // it only depends on SOME value being pointed to by two indices.
    static int hardened(int[] nums) {
        return findDuplicate(nums);
    }

    public static void main(String[] args) {
        int[] nums1 = {1, 3, 4, 2, 2};
        System.out.println("brute force: " + bruteForce(nums1));
        System.out.println("optimal:     " + findDuplicate(nums1));

        int[] nums2 = {2, 2, 2, 2, 2};
        System.out.println("all duplicates: " + hardened(nums2));
    }
}
```

How to run: save as `FindTheDuplicateNumber.java`, then run `java FindTheDuplicateNumber.java`.

## 6. Walkthrough

Dry run of `findDuplicate({1,3,4,2,2})`:

**Phase 1** (find a meeting point), starting `slow = fast = nums[0] = 1`:

| step | slow = nums[slow] | fast = nums[nums[fast]] |
|---|---|---|
| 1 | nums[1]=3 | nums[nums[1]]=nums[3]=2 |
| 2 | nums[3]=2 | nums[nums[2]]=nums[4]=2 |
| — | slow == fast == 2, stop | |

**Phase 2** (find the entrance), `ptr = nums[0] = 1`, `slow` stays at `2`:

| step | ptr = nums[ptr] | slow = nums[slow] |
|---|---|---|
| 1 | nums[1]=3 | nums[2]=4 |
| 2 | nums[3]=2 | nums[4]=2 |
| — | ptr == slow == 2, stop -> return 2 | |

Time complexity: O(n) — both phases together bounded by the array length. Space complexity: O(1), and the array is never modified.

## 7. Gotchas & takeaways

> Gotcha: starting `slow` and `fast` at index `0` itself (rather than `nums[0]`) works too in most write-ups, but be consistent — mixing "start at index 0" with "start at value nums[0]" mid-algorithm produces an off-by-one error in the meeting point.

- Recognizing "values in `[1, n]` over an array of `n + 1` elements, no modification, O(1) space" as a disguised linked-list-cycle problem is the single hardest step — the code itself is nearly identical to Linked List Cycle II.
- Related problems: Linked List Cycle II (the direct template this borrows), Circular Array Loop (another array-as-implicit-graph cycle problem).
