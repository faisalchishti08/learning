---
card: leetcode-patterns
gi: 359
slug: delete-and-earn
title: Delete and Earn
---

## 1. What it is

Given an array `nums`, repeatedly choose a number `x`, earn `x` points for EVERY occurrence of `x`, then DELETE every occurrence of `x - 1` and `x + 1` from the array (they become unavailable, forever). Return the MAXIMUM total points earnable. Example: `nums = [2,2,3,3,3,4]` → `9` (pick `3` three times, earning `9`, deleting all `2`s and `4`s).

## 2. Why & when

This LOOKS like a graph or greedy problem, but it is House Robber in disguise: picking value `x` forbids picking `x - 1` or `x + 1`, which is exactly the "adjacent forbidden" rule — except "adjacent" now means "consecutive VALUES," not consecutive array positions. Use this shape whenever picking one number blocks its numeric NEIGHBORS (not its array neighbors) from being picked.

## 3. Core concept

**Key idea:** first, convert `nums` into `points[v]` = `v * (count of v in nums)`, for every value `v` from `0` to `max(nums)`. Then run the EXACT House Robber recurrence over `points`, since picking value `v` forbids picking `v-1` and `v+1` — identical to picking house `i` forbidding houses `i-1` and `i+1`.

**Steps:**
1. Count occurrences of each value in `nums`. Build `points[v] = v * count[v]` for `v` from `0` to `maxVal`.
2. Base cases: `dp[0] = points[0]`, `dp[1] = max(points[0], points[1])`.
3. For `v` from `2` to `maxVal`: `dp[v] = max(dp[v-1], dp[v-2] + points[v])`.
4. Return `dp[maxVal]`.

**Why it is correct:** the transformation from "numbers with a value-based adjacency rule" to "an array `points[v]` with an index-based adjacency rule" is EXACT — since all occurrences of the same value must be taken together (there is no benefit to taking only some of them), `points[v]` correctly represents the total gain from picking value `v`, and the value-adjacency rule becomes literal index-adjacency once values are used as array indices.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="conversion from nums with value based adjacency to a points array indexed by value with the same house robber recurrence">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[2,2,3,3,3,4]; counts: 2-&gt;2, 3-&gt;3, 4-&gt;1</text>
    <text x="10" y="45">points = [0,0,4,9,4] (index = value)</text>
    <text x="10" y="65">dp[3] = max(dp[2], dp[1]+points[3]) = max(4, 0+9) = 9</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[4] carries dp[3] = 9 forward</text>
  </g>
</svg>

Once values become array indices with aggregated points, this is exactly House Robber.

## 5. Runnable example

```java
// DeleteAndEarn.java
public class DeleteAndEarn {

    // KEY INSIGHT: picking value v forbids v-1 and v+1 -- convert to
    // points[v] = v * count[v], then run the exact House Robber
    // recurrence over points, indexed by value.

    static int deleteAndEarn(int[] nums) {
        int maxVal = 0;
        for (int num : nums) maxVal = Math.max(maxVal, num);

        long[] points = new long[maxVal + 1];
        for (int num : nums) points[num] += num;

        long prev2 = points[0];
        long prev1 = Math.max(points[0], points.length > 1 ? points[1] : 0);
        for (int v = 2; v <= maxVal; v++) {
            long curr = Math.max(prev1, prev2 + points[v]);
            prev2 = prev1;
            prev1 = curr;
        }
        return (int) prev1;
    }

    public static void main(String[] args) {
        System.out.println(deleteAndEarn(new int[]{2, 2, 3, 3, 3, 4}));
        // 9
        System.out.println(deleteAndEarn(new int[]{3, 4, 2}));
        // 6
    }
}
```

**How to run:** `java DeleteAndEarn.java`

## 6. Walkthrough

Trace `deleteAndEarn([2,2,3,3,3,4])`, `points = [0,0,4,9,4]`:

| v | prev2 | prev1 | curr |
|---|---|---|---|
| start | 0 | 0 | - |
| 2 | 0 | max(0, 0+4)=4 | 4 |
| 3 | 4 | max(4, 0+9)=9 | 9 |
| 4 | 9 | max(9, 4+4)=9 | 9 |

Final `prev1 = 9`, matching the expected answer (pick `3` three times, earning `9`). Time complexity is O(n + maxVal), for counting occurrences plus the DP pass. Space is O(maxVal).

## 7. Gotchas & takeaways

> Gotcha: using `int` instead of `long` for `points` risks overflow if a value like `10^4` appears `10^4` times (`points[v]` up to `10^8`, still fits `int`, but summed contributions across a full run can approach the edge of safe `int` arithmetic) — prefer `long` for the accumulator when constraints are not tightly known.

- The transformation "aggregate by value, then run House Robber over the aggregated array" is the general technique for turning a VALUE-adjacency constraint into an INDEX-adjacency one.
- All occurrences of a chosen value must be taken together — there is never a reason to only partially take a value's occurrences, since the deletion penalty (losing `v-1` and `v+1`) is paid regardless of how many times `v` is picked.
- Related problems: House Robber (the exact recurrence this problem reduces to), House Robber II (a circular-array variant of the same base recurrence, not directly related to this problem's value-based twist).
