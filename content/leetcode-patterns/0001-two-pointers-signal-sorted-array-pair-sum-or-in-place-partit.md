---
card: leetcode-patterns
gi: 1
slug: two-pointers-signal-sorted-array-pair-sum-or-in-place-partit
title: Two Pointers — signal: sorted array, pair-sum, or in-place partitioning
---

## 1. What it is

Two pointers is a technique where you walk two index variables across a sequence at the same time, instead of using one index and a nested loop. Each pointer moves based on a rule, and together they narrow down the part of the array or string that still matters. Think of it like two people searching a sorted bookshelf from opposite ends, meeting in the middle instead of each scanning the whole shelf alone.

## 2. Why & when

You reach for two pointers when a brute-force solution uses a nested loop to compare every pair of elements, giving O(n²) time. Two pointers often cuts this to O(n) by using structure in the input — usually sortedness — to skip work instead of checking every pair.

Learn to recognize these signals in a problem statement:

- **"The array is sorted"** (or you can sort it yourself without breaking the problem). Sorted order lets you reason about which pointer to move: if a pair sums too high, the larger value must shrink, so you move the right pointer left.
- **"Find a pair (or triplet) that sums to a target."** Pair-sum problems on sorted arrays are the classic use case: two pointers scan from both ends and adjust based on the comparison.
- **"Rearrange the array in place"** or **"remove elements without extra space."** Problems like removing duplicates, moving zeroes, or partitioning by a condition use two pointers moving in the *same* direction: one pointer reads, the other writes the next valid position.
- **"O(1) extra space" is a stated constraint.** Two pointers uses no auxiliary array, so it is the pattern interviewers expect when they explicitly rule out extra memory.

The alternative is a hash set (O(n) space) or a nested loop (O(n²) time). Two pointers is the answer when the input is sorted (or sortable) and the interviewer wants O(n) time with O(1) space.

## 3. Core concept

There are two distinct pointer layouts, and the signal in the problem tells you which one to use:

**Opposite-ends pointers.** One pointer `left` starts at index 0, the other `right` starts at the last index. Each step compares `arr[left]` and `arr[right]` against a goal (usually a target sum), then moves exactly one pointer inward based on that comparison. This layout needs a sorted array, because the comparison result must translate directly into "move left forward" or "move right backward."

**Same-direction pointers.** Both pointers start at index 0. One pointer (`slow`) marks the next position to write a valid element; the other (`fast`) scans ahead looking for elements that pass a condition. When `fast` finds one, it copies it to `slow` and both advance; otherwise only `fast` advances. This layout does not require sorted input — it is used for in-place filtering and deduplication.

The key insight in both layouts: each pointer only ever moves forward (or inward). Neither pointer revisits a position, so the total work across the whole run is bounded by the array length, not its square.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointer layouts: opposite-ends and same-direction">
  <text x="20" y="24" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Opposite-ends (pair-sum on sorted array)</text>
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="95" y="63" fill="#e6edf3" text-anchor="middle">7</text>
    <text x="145" y="63" fill="#e6edf3" text-anchor="middle">11</text>
    <text x="195" y="63" fill="#e6edf3" text-anchor="middle">15</text>
    <text x="245" y="63" fill="#e6edf3" text-anchor="middle">20</text>
    <text x="45" y="95" fill="#79c0ff" text-anchor="middle">left</text>
    <text x="245" y="95" fill="#f0883e" text-anchor="middle">right</text>
    <line x1="45" y1="80" x2="45" y2="84" stroke="#79c0ff"/>
    <line x1="245" y1="80" x2="245" y2="84" stroke="#f0883e"/>
  </g>
  <text x="20" y="130" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Same-direction (in-place filter/dedupe)</text>
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="146" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="146" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="146" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="146" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="146" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="169" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="95" y="169" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="145" y="169" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="195" y="169" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="245" y="169" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="95" y="200" fill="#79c0ff" text-anchor="middle">slow</text>
    <text x="195" y="200" fill="#f0883e" text-anchor="middle">fast</text>
  </g>
</svg>

Opposite-ends pointers close in from both sides of a sorted array. Same-direction pointers have `fast` scan ahead while `slow` marks the next write position.

## 5. Runnable example

The artifact below is not a single problem's solution — it is a tiny probe you can run to confirm which layout a given input calls for, by checking the two signals: "is it sorted" and "does it need in-place output."

### Signal-checker

```java
// PointerSignal.java
import java.util.Arrays;

public class PointerSignal {
    static boolean isSorted(int[] a) {
        for (int i = 1; i < a.length; i++) {
            if (a[i - 1] > a[i]) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        int[] pairSumInput = {2, 7, 11, 15, 20};
        int[] dedupeInput = {1, 1, 2, 2, 3};

        System.out.println("pairSumInput sorted? " + isSorted(pairSumInput)
            + " -> use opposite-ends pointers");
        System.out.println("dedupeInput sorted?   " + isSorted(dedupeInput)
            + " -> in-place task, use same-direction pointers");
    }
}
```

How to run: save as `PointerSignal.java`, then run `java PointerSignal.java` (JDK 11+ runs single-file source directly).

## 6. Walkthrough

1. You read the problem statement. Two facts jump out: the array is already sorted, and you need to find a pair that sums to a target.
2. The "sorted" signal tells you a comparison between `arr[left] + arr[right]` and the target has a predictable direction: too small means move `left` right (to increase the sum); too large means move `right` left (to decrease it).
3. You set `left = 0` and `right = arr.length - 1`, matching the opposite-ends layout.
4. Running the checker above on `{2, 7, 11, 15, 20}` prints `sorted? true`, confirming the opposite-ends approach is safe to use.
5. For the dedupe input, no target sum exists — instead the task is "remove duplicates in place." That phrasing signals the same-direction layout, even though this input also happens to be sorted.

## 7. Gotchas & takeaways

> Gotcha: two pointers on an **unsorted** array for a pair-sum problem gives wrong answers, because moving a pointer no longer has a predictable effect on the sum. Sort first (O(n log n)), or use a hash set instead if you must preserve original order.

- Opposite-ends pointers need sorted (or sortable) input and a monotonic comparison rule.
- Same-direction pointers need an in-place, single-pass transformation, sorted or not.
- If you see "O(1) extra space" plus "array," it is almost always two pointers, not a hash set.
