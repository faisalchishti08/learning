---
card: leetcode-patterns
gi: 3
slug: two-pointers-complexity-o-n-time-o-1-space
title: Two Pointers — complexity: O(n) time, O(1) space
---

## 1. What it is

This page explains *why* two pointers runs in O(n) time and O(1) extra space, and lists the named problems that use the pattern, so you have both the proof and a reference set.

## 2. Why & when

Interviewers often ask you to state and justify the complexity of your solution, not just produce working code. "It's O(n) because we use two pointers" is not a justification — you need to explain why the total number of steps is bounded by n, not n². This matters most when your brute-force instinct is a nested loop (O(n²)); showing the tighter bound is often the difference between a partial and a full score.

## 3. Core concept

**Time — O(n).** In the opposite-ends layout, `left` only ever increases and `right` only ever decreases. Each is bounded between 0 and n−1, so `left` can move at most n times across the whole run, and `right` can move at most n times. The loop condition `left < right` stops them from crossing, so the loop body executes at most n times total, not once per pair. That is what separates it from the nested-loop brute force, which compares every pair — O(n²) comparisons — by not remembering what earlier comparisons already ruled out.

In the same-direction layout, `fast` visits each index exactly once, and `slow` never moves past `fast`. One full left-to-right scan means the loop body runs exactly n times.

**Space — O(1).** Both layouts use a fixed number of extra variables (`left`, `right`, or `slow`, `fast`) regardless of input size. No auxiliary array, hash set, or recursion stack grows with n. Compare this to a hash-set approach for pair-sum, which is also O(n) time but O(n) space, because it stores up to n elements in the set.

**Amortized reasoning.** The key proof technique here is a potential/amortized argument: define "work remaining" as `right - left` (or `n - fast`). Each step reduces that quantity by at least 1. Since it starts at n and cannot go below 0, the loop runs at most n times. This is the same style of argument used to prove sliding-window and fast/slow-pointer algorithms are linear.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of nested loop O(n squared) versus two pointers O(n)">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Nested loop: every (i, j) pair checked</text>
    <g stroke="#f0883e" stroke-width="1">
      <line x1="20" y1="40" x2="20" y2="140"/>
      <line x1="20" y1="40" x2="220" y2="40"/>
    </g>
    <!-- grid of dots representing O(n^2) comparisons -->
    <g fill="#f0883e">
      <circle cx="40" cy="60" r="2"/><circle cx="60" cy="60" r="2"/><circle cx="80" cy="60" r="2"/><circle cx="100" cy="60" r="2"/>
      <circle cx="40" cy="80" r="2"/><circle cx="60" cy="80" r="2"/><circle cx="80" cy="80" r="2"/><circle cx="100" cy="80" r="2"/>
      <circle cx="40" cy="100" r="2"/><circle cx="60" cy="100" r="2"/><circle cx="80" cy="100" r="2"/><circle cx="100" cy="100" r="2"/>
      <circle cx="40" cy="120" r="2"/><circle cx="60" cy="120" r="2"/><circle cx="80" cy="120" r="2"/><circle cx="100" cy="120" r="2"/>
    </g>
    <text x="20" y="170" fill="#8b949e">n=4 -> 16 comparisons -> O(n^2)</text>

    <text x="400" y="20" fill="#e6edf3" font-weight="bold">Two pointers: one diagonal pass</text>
    <g fill="#79c0ff">
      <circle cx="420" cy="60" r="2"/>
      <circle cx="440" cy="80" r="2"/>
      <circle cx="460" cy="100" r="2"/>
      <circle cx="480" cy="120" r="2"/>
    </g>
    <line x1="410" y1="50" x2="490" y2="130" stroke="#79c0ff" stroke-dasharray="3,3"/>
    <text x="400" y="170" fill="#8b949e">n=4 -> at most 4 steps -> O(n)</text>
  </g>
</svg>

The nested loop checks every cell of an n×n grid of pairs. Two pointers only ever walks one diagonal-ish path through it, touching each index once.

## 5. Runnable example

A tiny instrumented version of the opposite-ends template that counts how many comparisons it actually performs, so you can see the O(n) bound hold on real input rather than just take it on faith.

```java
// ComplexityCheck.java
public class ComplexityCheck {

    static int countTwoPointerSteps(int[] arr, int target) {
        int left = 0, right = arr.length - 1, steps = 0;
        while (left < right) {
            steps++;
            int sum = arr[left] + arr[right];
            if (sum == target) break;
            else if (sum < target) left++;
            else right--;
        }
        return steps;
    }

    static int countNestedLoopSteps(int[] arr, int target) {
        int steps = 0;
        for (int i = 0; i < arr.length; i++) {
            for (int j = i + 1; j < arr.length; j++) {
                steps++;
                if (arr[i] + arr[j] == target) return steps;
            }
        }
        return steps;
    }

    public static void main(String[] args) {
        int[] arr = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
        int target = 5 + 19; // forces a near-worst-case scan

        System.out.println("n = " + arr.length);
        System.out.println("two-pointer steps: " + countTwoPointerSteps(arr, target));
        System.out.println("nested-loop steps: " + countNestedLoopSteps(arr, target));
    }
}
```

How to run: save as `ComplexityCheck.java`, then run `java ComplexityCheck.java`. The two-pointer step count stays at or below n; the nested-loop count grows toward n²/2.

## 6. Walkthrough

1. `arr` has 10 elements. `target = 24` (5 + 19), a pair near the middle of the array.
2. `countTwoPointerSteps` starts with `left = 0, right = 9`. Each step moves exactly one pointer, so `right - left` shrinks by 1 every step. It finds the pair within at most 9 steps — bounded by n.
3. `countNestedLoopSteps` starts `i = 0, j = 1` and increments `j` before `i`, checking every pair in order. It has to walk through many irrelevant pairs before reaching `(2, 8)` — the pair for 5 and 19 — costing far more than n steps.
4. Printing both counts side by side shows the two-pointer count is linear in n, while the nested-loop count trends toward n²/2 for a target found late in the scan.
5. Neither method allocates an array or set proportional to n — both use only a handful of `int` variables — so both are O(1) space; the difference is purely in step count (time).

## 7. Gotchas & takeaways

> Gotcha: two pointers being O(n) time depends on each pointer moving **monotonically** (never backward). If your problem needs a pointer to jump backward and re-scan, you no longer have this pattern — you likely need a different technique, such as dynamic programming or a stack.

- Time: O(n) because `left` and `right` (or `slow` and `fast`) together traverse the array once, not once-per-pair.
- Space: O(1) because the pointers are the only extra state, independent of input size.
- Reference problems that use this pattern: Two Sum II, Valid Palindrome, Remove Duplicates from Sorted Array, Merge Sorted Array, Squares of a Sorted Array, Move Zeroes, Reverse String, Intersection of Two Arrays II, Backspace String Compare, 3Sum, Container With Most Water, Trapping Rain Water.
