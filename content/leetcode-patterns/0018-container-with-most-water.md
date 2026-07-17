---
card: leetcode-patterns
gi: 18
slug: container-with-most-water
title: Container With Most Water
---

## 1. What it is

Given an array `height` where `height[i]` is the height of a vertical line at position `i`, find two lines that, together with the x-axis, form a container holding the most water. Return the maximum area. Example: `height = [1,8,6,2,5,4,8,3,7]` → the answer is `49`, from the lines at index 1 (height 8) and index 8 (height 7): width `7`, height `min(8,7) = 7`, area `49`.

## 2. Why & when

The array is not necessarily sorted, but the *positions* are fixed and ordered by index, and the area formula (`width * min(height)`) shrinks predictably as the width shrinks — that structure is what two pointers exploits, starting from the widest possible container and narrowing.

## 3. Core concept

**Key idea:** start with the widest container (both ends), and always move the pointer at the **shorter** line, because that is the only move that could possibly increase the area.

**Steps:**
1. Set `left = 0`, `right = height.length - 1`, `best = 0`.
2. While `left < right`:
   - Compute `width = right - left`, `h = min(height[left], height[right])`, `area = width * h`.
   - Update `best = max(best, area)`.
   - Move the pointer at the shorter line inward: if `height[left] < height[right]`, `left++`; else `right--`.
3. Return `best`.

**Why it is correct:** the area is capped by the shorter of the two lines. If you move the pointer at the *taller* line inward, the width shrinks and the height cap stays the same or gets worse (limited by the still-shorter line) — that move can never improve the area, so it is always safe to discard. Moving the *shorter* line's pointer is the only move that has a chance of finding a taller line, which could compensate for the smaller width.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Container with most water narrowing from the shorter side">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">height = [1, 8, 6, 2, 5, 4, 8, 3, 7]</text>
    <line x1="20" y1="140" x2="20" y2="30" stroke="#79c0ff" stroke-width="3"/>
    <line x1="280" y1="140" x2="280" y2="50" stroke="#f0883e" stroke-width="3"/>
    <line x1="20" y1="140" x2="280" y2="140" stroke="#30363d" stroke-dasharray="3,3"/>
    <text x="20" y="155" fill="#79c0ff" text-anchor="middle">left=0 (h=1)</text>
    <text x="280" y="155" fill="#f0883e" text-anchor="middle">right=8 (h=7)</text>
    <text x="20" y="20" fill="#8b949e">area = width(8) * min(1,7) = 8 -&gt; best=8</text>
    <text x="330" y="60" fill="#8b949e">left is shorter -&gt; move left inward</text>
  </g>
</svg>

The container's height is capped by the shorter line, so only moving the shorter pointer can possibly find a bigger area.

## 5. Runnable example

```java
// ContainerWithMostWater.java
public class ContainerWithMostWater {

    // Level 1 -- Brute force: check every pair of lines. O(n^2) time,
    // O(1) space -- ignores that moving the taller line's pointer can
    // never help.
    static int bruteForce(int[] height) {
        int best = 0;
        for (int i = 0; i < height.length; i++) {
            for (int j = i + 1; j < height.length; j++) {
                int area = (j - i) * Math.min(height[i], height[j]);
                best = Math.max(best, area);
            }
        }
        return best;
    }

    // KEY INSIGHT: the container's height is bounded by its shorter line,
    // so moving the taller line's pointer can only shrink the width without
    // ever raising the height cap -- only the shorter side is worth moving.

    // Level 2 -- Optimal: two pointers, always move the shorter side.
    // O(n) time, O(1) space.
    public static int maxArea(int[] height) {
        int left = 0, right = height.length - 1, best = 0;
        while (left < right) {
            int width = right - left;
            int h = Math.min(height[left], height[right]);
            best = Math.max(best, width * h);
            if (height[left] < height[right]) {
                left++;
            } else {
                right--;
            }
        }
        return best;
    }

    // Level 3 -- Hardened: an array of length 2 returns exactly that one
    // container's area, since the loop body runs once before left meets right.
    static int hardened(int[] height) {
        if (height == null || height.length < 2) {
            throw new IllegalArgumentException("need at least two lines");
        }
        return maxArea(height);
    }

    public static void main(String[] args) {
        int[] height = {1, 8, 6, 2, 5, 4, 8, 3, 7};
        System.out.println("brute force: " + bruteForce(height));
        System.out.println("optimal:     " + maxArea(height));
        System.out.println("two lines:   " + hardened(new int[] {4, 9}));
    }
}
```

How to run: save as `ContainerWithMostWater.java`, then run `java ContainerWithMostWater.java`.

## 6. Walkthrough

Dry run of `maxArea({1, 8, 6, 2, 5, 4, 8, 3, 7})`:

| step | left (h) | right (h) | width | min height | area | best | move |
|---|---|---|---|---|---|---|---|
| 1 | 0 (1) | 8 (7) | 8 | 1 | 8 | 8 | left shorter, left++ |
| 2 | 1 (8) | 8 (7) | 7 | 7 | 49 | 49 | right shorter, right-- |
| 3 | 1 (8) | 7 (3) | 6 | 3 | 18 | 49 | right shorter, right-- |
| 4 | 1 (8) | 6 (8) | 5 | 8 | 40 | 49 | tie, right-- |

The scan continues narrowing; no later step beats `49`. Final answer: `49`. Time complexity: O(n), one inward pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: moving the *taller* line's pointer (instead of the shorter one) is the classic mistake — it feels arbitrary which side to move, but only moving the shorter side is provably safe; moving the taller side can silently skip over the true best answer.

- The "shorter side moves" rule is the entire trick — once you see it, the rest is a standard opposite-ends scan.
- Related problems: Trapping Rain Water (a related but distinct pattern — needs max-so-far on both sides, not just the current pointers), 3Sum, Largest Rectangle in Histogram.
