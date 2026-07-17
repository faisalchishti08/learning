---
card: leetcode-patterns
gi: 2
slug: two-pointers-template-opposite-ends-or-same-direction-pointe
title: Two Pointers — template: opposite-ends or same-direction pointers
---

## 1. What it is

A template is the reusable skeleton of code you write first, before filling in problem-specific logic. For two pointers, there are exactly two skeletons: the **opposite-ends** loop and the **same-direction** loop. Once you memorize both, solving a new two-pointers problem becomes "pick the right skeleton, then fill in one comparison or one condition."

## 2. Why & when

Interviewers expect you to produce working code quickly. If you re-derive the loop structure from scratch every time, you waste time and risk off-by-one bugs. Memorizing the two templates below means you spend your thinking time on the problem-specific rule (what to compare, what condition to check), not on the loop mechanics.

Use the opposite-ends template when the array is sorted and you are searching for a pair or shrinking a window from both sides. Use the same-direction template when you are filtering, compacting, or deduplicating a sequence in place, in a single left-to-right pass.

## 3. Core concept

**Opposite-ends template.** Two indices start at the two ends and move toward each other. The loop continues while `left < right`. On each iteration you compare the two pointed-at values against a goal, then move exactly one pointer — never both — based on that comparison. Moving only one pointer per step is what keeps the total work at O(n): across the whole run, `left` can advance at most n times and `right` can retreat at most n times, so the loop body runs at most n times total.

**Same-direction template.** One index, `slow`, tracks the boundary of the "answer so far." The other, `fast`, scans every element once. When `fast` finds an element that belongs in the answer, you write it at `slow` and advance both; otherwise you advance only `fast`. By the end, `slow` marks the new logical length of the array.

Both templates share one rule: never move a pointer backward, and never revisit an index. That single-pass guarantee is what gives you O(n) time.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointer template control flow">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="180" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="110" y="45" fill="#e6edf3" text-anchor="middle">while (left &lt; right)</text>
    <rect x="20" y="80" width="180" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="110" y="105" fill="#e6edf3" text-anchor="middle">compare a[left], a[right]</text>
    <rect x="20" y="140" width="180" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="110" y="165" fill="#e6edf3" text-anchor="middle">move ONE pointer inward</text>
    <line x1="110" y1="60" x2="110" y2="80" stroke="#8b949e" marker-end="url(#a1)"/>
    <line x1="110" y1="120" x2="110" y2="140" stroke="#8b949e" marker-end="url(#a1)"/>
    <path d="M200,160 C260,160 260,40 200,40" stroke="#8b949e" fill="none" marker-end="url(#a1)"/>

    <rect x="400" y="20" width="200" height="40" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="45" fill="#e6edf3" text-anchor="middle">for (fast = 0; fast &lt; n; fast++)</text>
    <rect x="400" y="80" width="200" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="500" y="105" fill="#e6edf3" text-anchor="middle">a[fast] passes condition?</text>
    <rect x="400" y="140" width="200" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="500" y="165" fill="#e6edf3" text-anchor="middle">write at slow, slow++</text>
    <line x1="500" y1="60" x2="500" y2="80" stroke="#8b949e" marker-end="url(#a1)"/>
    <line x1="500" y1="120" x2="500" y2="140" stroke="#8b949e" marker-end="url(#a1)"/>
  </g>
  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Left: the opposite-ends loop shrinks the window by one pointer per step. Right: the same-direction loop scans with `fast` and writes with `slow`.

## 5. Runnable example

Both templates as generic, reusable methods. Fill in the comparison or condition to adapt them to a specific problem.

```java
// TwoPointerTemplates.java
import java.util.Arrays;

public class TwoPointerTemplates {

    // Opposite-ends template: returns indices of a pair summing to target,
    // or null if none exists. Requires arr to be sorted ascending.
    static int[] oppositeEnds(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        while (left < right) {
            int sum = arr[left] + arr[right];
            if (sum == target) {
                return new int[] { left, right };
            } else if (sum < target) {
                left++;   // sum too small -> grow it
            } else {
                right--;  // sum too large -> shrink it
            }
        }
        return null;
    }

    // Same-direction template: compacts arr in place, keeping only elements
    // that satisfy keep(x). Returns the new logical length.
    interface Keep { boolean test(int x); }

    static int sameDirection(int[] arr, Keep keep) {
        int slow = 0;
        for (int fast = 0; fast < arr.length; fast++) {
            if (keep.test(arr[fast])) {
                arr[slow] = arr[fast];
                slow++;
            }
        }
        return slow;
    }

    public static void main(String[] args) {
        int[] sorted = {2, 7, 11, 15};
        System.out.println("pair for target 9: "
            + Arrays.toString(oppositeEnds(sorted, 9)));

        int[] nums = {0, 1, 0, 3, 12};
        int len = sameDirection(nums, x -> x != 0);
        System.out.println("non-zero prefix: "
            + Arrays.toString(Arrays.copyOf(nums, len)));
    }
}
```

How to run: save as `TwoPointerTemplates.java`, then run `java TwoPointerTemplates.java`.

## 6. Walkthrough

1. `oppositeEnds` is called with `sorted = {2, 7, 11, 15}` and `target = 9`. `left = 0`, `right = 3`.
2. `arr[0] + arr[3] = 2 + 15 = 17`, which is greater than 9, so `right--` moves to index 2.
3. `arr[0] + arr[2] = 2 + 11 = 13`, still greater than 9, so `right--` moves to index 1.
4. `arr[0] + arr[1] = 2 + 7 = 9`, equal to target, so the method returns `[0, 1]`.
5. `sameDirection` is called with `nums = {0, 1, 0, 3, 12}` and `keep = x != 0`. `slow = 0`.
6. `fast = 0`: `arr[0] = 0` fails `keep`, so nothing is written; only `fast` advances.
7. `fast = 1`: `arr[1] = 1` passes; `arr[slow] = arr[fast]` writes `1` at index 0, `slow` becomes 1.
8. This continues; by the end `slow = 3` and the first 3 slots hold `{1, 3, 12}`, the non-zero prefix.

## 7. Gotchas & takeaways

> Gotcha: in the opposite-ends template, moving **both** pointers on the same iteration (instead of exactly one) can skip over the correct pair. Always move only the pointer implicated by the comparison.

- Opposite-ends template: sorted input, one comparison, move exactly one pointer per step.
- Same-direction template: any input, one condition, `fast` scans, `slow` writes.
- Both templates are O(n) time and O(1) extra space — no auxiliary array or hash set needed.
