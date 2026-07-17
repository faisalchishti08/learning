---
card: leetcode-patterns
gi: 27
slug: trapping-rain-water
title: Trapping Rain Water
---

## 1. What it is

Given `n` non-negative integers `height`, representing an elevation map where each bar has width 1, compute how much water it can trap after raining. Example: `height = [0,1,0,2,1,0,1,3,2,1,2,1]` → answer `6` units of trapped water.

## 2. Why & when

The water trapped above any bar `i` equals `min(maxLeft(i), maxRight(i)) - height[i]`, where `maxLeft` and `maxRight` are the tallest bars to the left and right of `i` (inclusive of `i`). Computing `maxLeft` and `maxRight` for every index with two separate passes works, but two pointers converging from both ends solves it in one pass, because at any moment you can always safely resolve the side with the smaller running maximum.

## 3. Core concept

**Key idea:** at each step, whichever side has the smaller "max so far" is the side whose current bar's trapped water is fully determined — the other side's wall is guaranteed to be at least as tall, so it cannot be the limiting factor.

**Steps:**
1. Set `left = 0`, `right = n - 1`, `leftMax = 0`, `rightMax = 0`, `water = 0`.
2. While `left < right`:
   - If `height[left] < height[right]`:
     - Update `leftMax = max(leftMax, height[left])`.
     - Add `leftMax - height[left]` to `water` (this bar's trapped water — safe because `rightMax >= leftMax` is guaranteed by the comparison).
     - `left++`.
   - Else (symmetric): update `rightMax`, add `rightMax - height[right]` to `water`, `right--`.
3. Return `water`.

**Why it is correct:** if `height[left] < height[right]`, then the true `rightMax` (over the whole remaining range) must be at least `height[right]`, which is greater than `height[left]`. Since `leftMax` is already known exactly (it is the max of everything scanned from the left so far), the water above `height[left]` is capped by `leftMax` — the true, but still unknown, `rightMax` cannot be smaller, so it is never the binding constraint. That lets you resolve `left`'s water immediately, without knowing the exact `rightMax`.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Trapping rain water two pointers with running max">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">height = [0,1,0,2,1,0,1,3,2,1,2,1]</text>
    <polyline points="20,160 40,160 60,140 80,160 100,100 120,140 140,160 160,140 180,60 200,100 220,140 240,100 260,140" fill="none" stroke="#8b949e" stroke-width="2"/>
    <rect x="180" y="60" width="16" height="6" fill="#f59e0b"/>
    <text x="188" y="50" fill="#f59e0b" text-anchor="middle" font-size="10">tall right wall (3)</text>
    <text x="20" y="185" fill="#8b949e">leftMax and rightMax grow as pointers converge; smaller side resolves its water each step</text>
  </g>
</svg>

The pointer on the side with the smaller running max always has a fully determined amount of trapped water, because the opposite wall is guaranteed at least as tall.

## 5. Runnable example

```java
// TrappingRainWater.java
public class TrappingRainWater {

    // Level 1 -- Brute force: for each bar, scan left and right separately
    // to find maxLeft and maxRight. O(n^2) time, O(1) space -- rescans the
    // whole array for every single bar.
    static int bruteForce(int[] height) {
        int n = height.length, water = 0;
        for (int i = 0; i < n; i++) {
            int maxLeft = 0, maxRight = 0;
            for (int l = 0; l <= i; l++) maxLeft = Math.max(maxLeft, height[l]);
            for (int r = i; r < n; r++) maxRight = Math.max(maxRight, height[r]);
            water += Math.min(maxLeft, maxRight) - height[i];
        }
        return water;
    }

    // KEY INSIGHT: the side with the smaller running max always has its
    // trapped water fully determined, because the true max on the other
    // side is guaranteed to be at least as large -- so two pointers can
    // resolve one bar per step without precomputing full max arrays.

    // Level 2 -- Optimal: two pointers with running maxes. O(n) time,
    // O(1) space.
    public static int trap(int[] height) {
        int left = 0, right = height.length - 1;
        int leftMax = 0, rightMax = 0, water = 0;
        while (left < right) {
            if (height[left] < height[right]) {
                leftMax = Math.max(leftMax, height[left]);
                water += leftMax - height[left];
                left++;
            } else {
                rightMax = Math.max(rightMax, height[right]);
                water += rightMax - height[right];
                right--;
            }
        }
        return water;
    }

    // Level 3 -- Hardened: a strictly increasing or strictly decreasing
    // elevation map traps no water at all -- the running max always equals
    // the current bar's height on the resolving side, so each step adds 0.
    static int hardened(int[] height) {
        if (height == null || height.length < 3) return 0;
        return trap(height);
    }

    public static void main(String[] args) {
        int[] height = {0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1};
        System.out.println("brute force: " + bruteForce(height));
        System.out.println("optimal:     " + trap(height));
        System.out.println("no trapping: " + hardened(new int[] {1, 2, 3, 4}));
    }
}
```

How to run: save as `TrappingRainWater.java`, then run `java TrappingRainWater.java`.

## 6. Walkthrough

Dry run of the first few steps of `trap({0,1,0,2,1,0,1,3,2,1,2,1})`:

| step | left (h) | right (h) | leftMax | rightMax | comparison | water added | water total |
|---|---|---|---|---|---|---|---|
| 1 | 0 (0) | 11 (1) | 0 | 0 | 0 < 1 | leftMax=0, add 0-0=0 | 0 |
| 2 | 1 (1) | 11 (1) | 1 | 0 | 1 is not < 1 (else branch) | rightMax=1, add 1-1=0 | 0 |
| 3 | 1 (1) | 10 (2) | 1 | 1 | 1 < 2 | leftMax=1, add 1-1=0 | 0 |
| 4 | 2 (0) | 10 (2) | 1 | 1 | 0 < 2 | leftMax=1, add 1-0=1 | 1 |
| 5 | 3 (2) | 10 (2) | 1 | 1 | 2 not < 2 (else) | rightMax=2, add 2-2=0 | 1 |

The scan continues converging, accumulating water at each locally-resolved bar; the full run reaches a final total of `6`. Time complexity: O(n), one pass. Space complexity: O(1) — no precomputed max arrays needed.

## 7. Gotchas & takeaways

> Gotcha: using `<=` instead of `<` in the comparison (`height[left] <= height[right]`) still works correctly here (ties can resolve either side), but mixing up which running max you update — updating `rightMax` while resolving the `left` pointer, for example — silently produces wrong totals. Keep `leftMax` paired with `left`, `rightMax` paired with `right`.

- This is the same "shorter side is the safe one to resolve" reasoning as Container With Most Water, but Trapping Rain Water needs the *running max*, not just the current bar, because it sums water above every bar, not just the max area of one container.
- Related problems: Container With Most Water, Trapping Rain Water II (2D version, needs a priority queue instead of two pointers), Product of Array Except Self.
