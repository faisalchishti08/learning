---
card: leetcode-patterns
gi: 29
slug: sliding-window-template-expand-right-shrink-left-while-a-win
title: Sliding Window — template: expand right, shrink left while a window condition holds
---

## 1. What it is

The sliding window template is the reusable loop skeleton: one `for` loop advancing `right`, and one inner `while` loop that shrinks `left` whenever the window becomes invalid. Every sliding-window problem reuses this exact skeleton — only the "what makes the window valid" check changes.

## 2. Why & when

Memorizing this one skeleton means you spend your problem-solving time deciding what state to track (a sum, a `HashMap` of counts, a distinct-element count) and what the validity condition is — not re-deriving the loop structure. Use it whenever the signal page identifies the problem as sliding window: a contiguous subarray/substring with an incrementally checkable condition.

## 3. Core concept

**Key idea:** `right` always advances by exactly one per outer iteration; `left` advances zero or more times per iteration, only to restore validity. Because both pointers only move forward, the whole scan is O(n) even though it "looks" like a nested loop.

**The template:**
```text
left = 0
state = <empty tracker: sum, count map, distinct count, etc.>
for right in 0..n-1:
    add arr[right] to state
    while state is invalid:
        remove arr[left] from state
        left += 1
    # window [left, right] is now valid (or you're tracking a different condition)
    update answer using (right - left + 1)
```

**Two variants of "update answer":**
- **Longest valid window:** update the answer *after* the shrink loop, once the window is guaranteed valid — you want the longest length among all valid windows.
- **Shortest window containing something:** update the answer *inside* the shrink loop, every time the window is still valid after removing an element — you want the shortest length among all valid windows, so you record before shrinking further, then keep trying to shrink more.

**Why it is correct:** the shrink loop's job is to restore the invariant "the window is valid" (or, for the shortest variant, "the window is exactly one element more than the minimal invalid state"). Because `left` never resets backward, every element is added to `state` once and removed from `state` at most once across the entire scan — that bounds the total work to O(n).

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sliding window template control flow">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="220" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="130" y="45" fill="#e6edf3" text-anchor="middle">for right in 0..n-1</text>
    <rect x="20" y="80" width="220" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="130" y="105" fill="#e6edf3" text-anchor="middle">add arr[right] to state</text>
    <rect x="20" y="140" width="220" height="40" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="130" y="165" fill="#e6edf3" text-anchor="middle">while invalid: remove arr[left], left++</text>
    <line x1="130" y1="60" x2="130" y2="80" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="130" y1="120" x2="130" y2="140" stroke="#8b949e" marker-end="url(#a3)"/>
  </g>
  <defs>
    <marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`right` drives the outer loop; the inner `while` restores validity before the answer is updated.

## 5. Runnable example

Two ready-to-adapt templates: longest-valid-window and shortest-window-containing.

```java
// SlidingWindowTemplates.java
import java.util.HashMap;
import java.util.Map;

public class SlidingWindowTemplates {

    // Longest valid window template, using "at most k distinct characters"
    // as the concrete validity condition.
    static int longestWithAtMostKDistinct(String s, int k) {
        Map<Character, Integer> counts = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            counts.merge(c, 1, Integer::sum);
            while (counts.size() > k) {
                char toRemove = s.charAt(left);
                counts.merge(toRemove, -1, Integer::sum);
                if (counts.get(toRemove) == 0) counts.remove(toRemove);
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Shortest window template, using "sum >= target" as the condition.
    static int shortestWithSumAtLeast(int[] arr, int target) {
        int left = 0, sum = 0;
        int best = Integer.MAX_VALUE;
        for (int right = 0; right < arr.length; right++) {
            sum += arr[right];
            while (sum >= target) {
                best = Math.min(best, right - left + 1);
                sum -= arr[left];
                left++;
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best;
    }

    public static void main(String[] args) {
        System.out.println("longest with <=2 distinct: "
            + longestWithAtMostKDistinct("eceba", 2));
        System.out.println("shortest with sum >= 7: "
            + shortestWithSumAtLeast(new int[] {2, 1, 5, 2, 3, 2}, 7));
    }
}
```

How to run: save as `SlidingWindowTemplates.java`, then run `java SlidingWindowTemplates.java`.

## 6. Walkthrough

Dry run of `longestWithAtMostKDistinct("eceba", k = 2)`:

1. `right=0` ('e'): counts `{e:1}`. Size 1 <= 2, valid. Best: 1.
2. `right=1` ('c'): counts `{e:1, c:1}`. Size 2 <= 2, valid. Best: 2.
3. `right=2` ('e'): counts `{e:2, c:1}`. Size 2 <= 2, valid. Best: 3.
4. `right=3` ('b'): counts `{e:2, c:1, b:1}`. Size 3 > 2, invalid. Shrink: remove `s[0]='e'`, counts `{e:1, c:1, b:1}`, still size 3, `left=1`. Remove `s[1]='c'`, counts `{e:1, b:1}`, size 2, `left=2`. Now valid. Best stays 3 (window length `right-left+1 = 3-2+1=2`).
5. `right=4` ('a'): counts `{e:1, b:1, a:1}`. Size 3 > 2, invalid. Shrink similarly until valid.

Final best: `3`, from the window `"ece"`. Time complexity: O(n). Space complexity: O(k) for the counts map.

## 7. Gotchas & takeaways

> Gotcha: updating the answer in the wrong place — before the shrink loop instead of after, for the longest-window variant — records the length of a window that might still be invalid.

- One skeleton, two update points: after the shrink loop for "longest," inside the shrink loop for "shortest."
- The `state` tracker's shape depends on the condition: an `int` for a running sum, a `HashMap<Character, Integer>` for character counts, an `int` for a distinct-count derived from that map.
