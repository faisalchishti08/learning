---
card: leetcode-patterns
gi: 495
slug: product-of-array-except-self
title: Product of Array Except Self
---

## 1. What it is

Given an array `nums`, return an array `answer` where `answer[i]` is the product of every element in `nums` except `nums[i]`. You must solve it in O(n) time without using division, and the output array does not count as extra space. Example: `nums = [1, 2, 3, 4]` → `[24, 12, 8, 6]`.

## 2. Why & when

"Product of everything except this element" is the multiplicative twin of the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md): instead of prefix *sums*, build prefix *products* from the left and from the right, then multiply the two at each index. Constraints: up to 100,000 elements; no division allowed (which rules out the simpler "compute total product, then divide by `nums[i]`" approach, which also breaks when `nums` contains zeros).

## 3. Core concept

**Key idea:** `answer[i]` equals `(product of everything left of i) * (product of everything right of i)`. Compute the left-products in one left-to-right pass, storing them directly into `answer`. Then compute the right-products in one right-to-left pass, multiplying them into `answer` on the fly (using a single running variable instead of a second array, to meet the "no extra space" constraint).

**Steps:**
1. Initialize `answer[0] = 1` (nothing to the left of index 0).
2. Left-to-right pass: for `i` from `1` to `n-1`, set `answer[i] = answer[i-1] * nums[i-1]` (the running product of everything before index `i`).
3. Initialize a running variable `rightProduct = 1`.
4. Right-to-left pass: for `i` from `n-1` down to `0`, multiply `answer[i] *= rightProduct`, then update `rightProduct *= nums[i]`.
5. Return `answer`.

**Why avoiding division matters, beyond the stated constraint:** dividing the total product by `nums[i]` fails outright when any element is `0` (division by zero), and gives wrong results when more than one element is `0` (every other position should be `0` too, but the total product is already `0`, making the division ill-defined). The two-pass product approach handles zeros correctly without any special case.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Left-to-right prefix products combined with a right-to-left running product">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 2, 3, 4]</text>
    <text x="20" y="45" fill="#79c0ff">left pass:  answer = [1, 1, 2, 6] (product of everything before i)</text>
    <text x="20" y="70" fill="#f0883e">right pass: rightProduct rolls 1 -&gt; 4 -&gt; 12 -&gt; 24 as i goes 3 -&gt; 0</text>
    <text x="20" y="95" fill="#8b949e">i=3: answer[3] = 6 * 1 = 6.  rightProduct becomes 4</text>
    <text x="20" y="115" fill="#8b949e">i=2: answer[2] = 2 * 4 = 8.  rightProduct becomes 12</text>
    <text x="20" y="135" fill="#8b949e">i=1: answer[1] = 1 * 12 = 12. rightProduct becomes 24</text>
    <text x="20" y="155" fill="#3fb950">i=0: answer[0] = 1 * 24 = 24. final: [24, 12, 8, 6]</text>
  </g>
</svg>

Left products are built first; a single running variable then folds in the right products in reverse.

## 5. Runnable example

**Level 1 — Brute force.** For each index, multiply every other element directly. O(n²), or O(n) with a division shortcut that breaks on zeros.

**KEY INSIGHT:** the answer at each index splits cleanly into a left product and a right product; computing both with running variables (one array pass each) avoids both the O(n²) cost and the division-by-zero problem.

**Level 2 — Optimal.** Two passes: left products stored in the answer array, right products folded in with one running variable, O(n) time, O(1) extra space.

**Level 3 — Hardened.** Handles a single zero in the array (all other positions become `0`) and multiple zeros (every position becomes `0`).

```java
// ProductExceptSelf.java
import java.util.Arrays;

public class ProductExceptSelf {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            int product = 1;
            for (int j = 0; j < n; j++) {
                if (j != i) product *= nums[j];
            }
            result[i] = product;
        }
        return result;
    }

    // Level 2 & 3: two passes, O(n) time, O(1) extra space
    static int[] productExceptSelf(int[] nums) {
        int n = nums.length;
        int[] answer = new int[n];

        answer[0] = 1;
        for (int i = 1; i < n; i++) {
            answer[i] = answer[i - 1] * nums[i - 1];
        }

        int rightProduct = 1;
        for (int i = n - 1; i >= 0; i--) {
            answer[i] *= rightProduct;
            rightProduct *= nums[i];
        }
        return answer;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 4};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(productExceptSelf(nums)));

        System.out.println("one zero:    " + Arrays.toString(productExceptSelf(new int[]{1, 2, 0, 4})));
        System.out.println("two zeros:   " + Arrays.toString(productExceptSelf(new int[]{0, 2, 0, 4})));
    }
}
```

**How to run:** save as `ProductExceptSelf.java`, then run `java ProductExceptSelf.java`.

## 6. Walkthrough

Trace `productExceptSelf({1, 2, 3, 4})`. Left pass fills `answer = [1, 1, 2, 6]` (`answer[1]=1*1`, `answer[2]=1*2`, `answer[3]=2*3`).

| i (right pass) | answer[i] before | rightProduct before | answer[i] after | rightProduct after |
|---|---|---|---|---|
| 3 | 6 | 1 | 6*1=6 | 1*4=4 |
| 2 | 2 | 4 | 2*4=8 | 4*3=12 |
| 1 | 1 | 12 | 1*12=12 | 12*2=24 |
| 0 | 1 | 24 | 1*24=24 | 24*1=24 |

Final `answer = [24, 12, 8, 6]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: computing the total product and dividing by `nums[i]` looks simpler, but fails the "no division" constraint and breaks entirely when `nums` contains a `0` — the two-pass product approach handles every case, including multiple zeros, with no special casing.

- The answer at each index is a left product times a right product — compute each with a single running variable, not a second full array.
- The output array itself is not counted as "extra space," but the running `rightProduct` variable is what keeps the *auxiliary* space at O(1).
- Time: O(n) — exactly two passes over the array.
