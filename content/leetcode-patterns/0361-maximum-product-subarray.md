---
card: leetcode-patterns
gi: 361
slug: maximum-product-subarray
title: Maximum Product Subarray
---

## 1. What it is

Given an integer array `nums`, find the CONTIGUOUS subarray (containing at least one number) with the LARGEST product, and return that product. Example: `nums = [2,3,-2,4]` → `6` (subarray `[2,3]`).

## 2. Why & when

This looks like a simple "extend or restart" DP, but a NEGATIVE number can flip the sign of a running product, turning the smallest (most negative) running product into the LARGEST once multiplied by another negative. Use this shape whenever a problem tracks a running product (not sum) ending at each position, since products need to track BOTH the running maximum AND the running minimum.

## 3. Core concept

**Key idea:** track two rolling values at each position: `maxEndingHere` (the largest product of a subarray ending at `i`) and `minEndingHere` (the smallest, most negative). A negative `nums[i]` SWAPS the roles of these two before combining, since multiplying a negative number flips which one becomes the new maximum.

**Steps:**
1. Initialize `maxEndingHere = minEndingHere = result = nums[0]`.
2. For `i` from `1` to `n-1`: if `nums[i] < 0`, swap `maxEndingHere` and `minEndingHere` (multiplying by a negative flips their order).
3. Update `maxEndingHere = max(nums[i], maxEndingHere * nums[i])` and `minEndingHere = min(nums[i], minEndingHere * nums[i])` (either start fresh at `i`, or extend the previous subarray).
4. Update `result = max(result, maxEndingHere)` after each step. Return `result`.

**Why it is correct:** the maximum product ending at `i` either EXTENDS the best (or worst) product ending at `i-1` by multiplying in `nums[i]`, or STARTS FRESH at `nums[i]` alone. Because a negative `nums[i]` turns the previous MINIMUM into a candidate MAXIMUM (two negatives multiply to a positive), tracking only the running maximum would silently lose this possibility — the running minimum must be carried forward too.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="running max and min product swapping roles when a negative number is multiplied in">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[2,3,-2,4]; at i=2 (value -2)</text>
    <text x="10" y="45">before: maxEndingHere=6, minEndingHere=2</text>
    <text x="10" y="65">nums[i] &lt; 0 -&gt; swap first: max=2, min=6</text>
    <text x="10" y="85">then: maxEndingHere=max(-2,2*-2)=-2, minEndingHere=min(-2,6*-2)=-12</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">swap catches sign flips from negatives</text>
  </g>
</svg>

Swapping before multiplying ensures the negative's sign-flipping effect is correctly tracked on both running extremes.

## 5. Runnable example

```java
// MaximumProductSubarray.java
public class MaximumProductSubarray {

    // KEY INSIGHT: track BOTH running max and running min product,
    // since a negative number can turn the smallest running product
    // into the largest by flipping its sign.

    static int maxProduct(int[] nums) {
        int maxEndingHere = nums[0];
        int minEndingHere = nums[0];
        int result = nums[0];

        for (int i = 1; i < nums.length; i++) {
            int curr = nums[i];
            if (curr < 0) {
                int temp = maxEndingHere;
                maxEndingHere = minEndingHere;
                minEndingHere = temp;
            }
            maxEndingHere = Math.max(curr, maxEndingHere * curr);
            minEndingHere = Math.min(curr, minEndingHere * curr);
            result = Math.max(result, maxEndingHere);
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(maxProduct(new int[]{2, 3, -2, 4}));
        // 6
        System.out.println(maxProduct(new int[]{-2, 3, -4}));
        // 24
    }
}
```

**How to run:** `java MaximumProductSubarray.java`

## 6. Walkthrough

Trace `maxProduct([2,3,-2,4])`:

| i | nums[i] | maxEndingHere | minEndingHere | result |
|---|---|---|---|---|
| 0 | 2 | 2 | 2 | 2 |
| 1 | 3 | 6 | 3 | 6 |
| 2 | -2 | -2 (after swap+mult) | -12 | 6 |
| 3 | 4 | 4 | -48 | 6 |

Final `result = 6`, matching the expected `6` from subarray `[2,3]`. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the swap step before updating `maxEndingHere` and `minEndingHere` silently drops the case where two negatives combine into a large positive product — always swap first when `nums[i] < 0`, then apply the same `max`/`min` update formulas used for positive numbers.

- Tracking two rolling values (max AND min) instead of one is the specific twist that separates this from a plain running-sum "extend or restart" DP (like Kadane's algorithm for Maximum Subarray).
- A `0` in the array resets both running values naturally, since `max(0, anything * 0) = max(0, 0) = 0` at worst, breaking any subarray that would otherwise cross it.
- Related problems: Maximum Subarray (the additive version of this exact shape, needing only a running max since addition has no sign-flipping quirk), Climbing Stairs (a simpler two-variable rolling DP, without the swap complication).
