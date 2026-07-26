---
card: leetcode-patterns
gi: 455
slug: non-decreasing-array
title: Non-decreasing Array
---

## 1. What it is

Given an array, determine whether it can become non-decreasing by modifying AT MOST ONE element. Example: `nums = [4,2,3]` → `true` (change the `4` to `2` or less). Example: `nums = [4,2,1]` → `false` (needs at least two changes).

## 2. Why & when

Use this shape whenever a problem asks whether a SINGLE fix can restore a property (here, non-decreasing order) across an entire array. The greedy rule: scan once, and whenever a violation (`nums[i] > nums[i+1]`) is found, decide GREEDILY which of the two values to lower or raise, based only on the ONE neighbor just outside the violation.

## 3. Core concept

**Key idea:** count violations (`nums[i] > nums[i+1]`) while scanning. If more than ONE violation occurs, immediately return `false`. On the FIRST violation, choose which side to fix using a LOCAL rule: prefer lowering `nums[i]` to `nums[i+1]`, unless that would break the relationship with `nums[i-1]`, in which case raise `nums[i+1]` to `nums[i]` instead.

**Steps:**
1. Track a violation `count = 0`.
2. For each `i` where `nums[i] > nums[i+1]`: increment `count`; if `count > 1`, return `false`.
3. Decide the fix: if `i == 0` OR `nums[i-1] <= nums[i+1]`, set `nums[i] = nums[i+1]` (lowering `nums[i]` is safe — it does not break the relationship with what comes before it). Otherwise, set `nums[i+1] = nums[i]` (lowering `nums[i]` WOULD break the earlier relationship, so raise `nums[i+1]` instead).
4. If the scan finishes with at most one violation (and it was successfully patched), return `true`.

**Why checking `nums[i-1]` decides which side to fix (the exchange argument):** lowering `nums[i]` to `nums[i+1]` is the "cheaper" fix (it does not raise any value), but it is only SAFE if `nums[i-1] <= nums[i+1]` — otherwise, the newly lowered `nums[i]` would now be SMALLER than `nums[i-1]`, creating a brand-new violation. In that specific case, the only safe option left is to raise `nums[i+1]` up to `nums[i]` instead, which cannot break anything to its right (since `nums[i+1]` is only increasing, and any subsequent check only compares it against later values).

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a single violation checked against the element two positions back to decide whether lowering or raising is the safe fix">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">violation at (i, i+1): nums[i] &gt; nums[i+1]</text>
    <text x="10" y="45">if nums[i-1] &lt;= nums[i+1]: lower nums[i] to nums[i+1] (safe)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">else: raise nums[i+1] to nums[i] instead (the only safe option left)</text>
  </g>
</svg>

Checking the element just before the violation decides which side of the violation is safe to adjust.

## 5. Runnable example

```java
// NonDecreasingArray.java
public class NonDecreasingArray {

    // KEY INSIGHT: on a violation, check nums[i-1] to decide the safe
    // fix -- lowering nums[i] is cheaper, but only safe if it doesn't
    // create a NEW violation with what came before it.

    static boolean checkPossibility(int[] nums) {
        int count = 0;
        for (int i = 0; i < nums.length - 1; i++) {
            if (nums[i] > nums[i + 1]) {
                count++;
                if (count > 1) return false;
                if (i == 0 || nums[i - 1] <= nums[i + 1]) {
                    nums[i] = nums[i + 1];
                } else {
                    nums[i + 1] = nums[i];
                }
            }
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(checkPossibility(new int[]{4, 2, 3}));
        // true
        System.out.println(checkPossibility(new int[]{4, 2, 1}));
        // false
    }
}
```

**How to run:** `java NonDecreasingArray.java`

## 6. Walkthrough

Trace `checkPossibility([4,2,3])`:

| i | nums[i] > nums[i+1]? | check nums[i-1] | fix | array after |
|---|---|---|---|---|
| 0 | 4 > 2? yes | i==0, no check needed | nums[0] = nums[1] = 2 | [2,2,3] |
| 1 | 2 > 3? no | — | — | [2,2,3] |

Only one violation occurred and was fixed, so the function returns `true`, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: always lowering `nums[i]` on every violation (without checking `nums[i-1]`) is a common but INCORRECT simplification — it fails on inputs like `[3,4,2,3]`, where lowering the `4` to `2` would create a new violation against the `3` before it; raising the `2` to `4` instead is the only valid fix there.

- A SINGLE violation is allowed; a SECOND violation anywhere means the answer is `false` — the moment `count > 1`, no fix can save the array.
- The `nums[i-1]` check is the entire "trickiness" of this problem: without it, the greedy fix looks correct on simple examples but silently fails on others.
- Related problems: Candy (also a two-directional greedy check, but accumulating a count instead of making a single yes/no repair decision), Wiggle Subsequence (a different kind of single-pass property check, counting direction changes instead of violations).
