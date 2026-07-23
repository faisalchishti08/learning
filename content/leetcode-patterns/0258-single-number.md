---
card: leetcode-patterns
gi: 258
slug: single-number
title: Single Number
---

## 1. What it is

Given a non-empty array `nums` where every element appears exactly twice, except for one, find that single element. You must do it in O(n) time and O(1) extra space. Example: `nums = [4,1,2,1,2]` → `4`.

## 2. Why & when

This is the foundational XOR-cancellation problem: the O(1) space requirement rules out a `HashSet`, and the "appears twice except one" structure is the exact signal that XOR was built to exploit. Use this shape whenever a problem promises every unwanted value appears an EVEN number of times, and one value appears an odd number of times.

## 3. Core concept

**Key idea:** XOR-ing a value with itself gives `0` (`a ^ a = 0`), and XOR-ing anything with `0` gives that thing back unchanged (`a ^ 0 = a`). XOR-ing the entire array together, in any order, cancels every pair to `0`, leaving only the single unpaired value.

**Steps:**
1. Initialize `result = 0`.
2. For each `num` in `nums`: `result ^= num`.
3. After the loop, `result` holds the single element.

**Why it is correct:** XOR is commutative and associative, so the order elements are XOR-ed in does not matter — you can freely regroup `4^1^2^1^2` as `4 ^ (1^1) ^ (2^2) = 4 ^ 0 ^ 0 = 4`. Every value that appears exactly twice contributes a `pair ^ pair = 0` term that vanishes entirely, leaving only the value that appears an odd number of times (exactly once, per the problem's guarantee).

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XOR of 4 1 2 1 2 regrouped as 4 xor (1 xor 1) xor (2 xor 2) equals 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [4, 1, 2, 1, 2]</text>
    <text x="10" y="45">4 ^ 1 ^ 2 ^ 1 ^ 2</text>
    <text x="10" y="65">= 4 ^ (1^1) ^ (2^2)  (XOR is commutative and associative)</text>
    <text x="10" y="85">= 4 ^ 0 ^ 0</text>
    <rect x="10" y="95" width="30" height="24" fill="#3fb950"/><text x="25" y="112" fill="#0d1117" text-anchor="middle" font-size="9">4</text>
  </g>
</svg>

Regrouping the XOR chain shows every pair cancels to zero, leaving only the single unpaired value.

## 5. Runnable example

```java
// SingleNumber.java
public class SingleNumber {

    // Level 1 -- Brute force: use a HashSet; for each number, remove
    // it if already present (meaning its pair was seen), otherwise
    // add it. The one value left in the set at the end is the answer.
    // Correct, but O(n) SPACE for the set, violating the O(1) space
    // requirement.

    // KEY INSIGHT: a ^ a = 0 and a ^ 0 = a. XOR-ing the whole array
    // together cancels every pair automatically, needing only one
    // accumulator variable instead of a data structure.

    // Level 2 -- Optimal: XOR-cancellation in a single pass.
    static int singleNumber(int[] nums) {
        int result = 0;
        for (int num : nums) {
            result ^= num;
        }
        return result;
    }

    // Level 3 -- Hardened: works unchanged for negative numbers (XOR
    // operates on the two's-complement bit pattern directly, and
    // pairs of equal negative numbers still cancel to 0) and for a
    // single-element array (the loop runs once, returning that value).

    public static void main(String[] args) {
        System.out.println(singleNumber(new int[]{4, 1, 2, 1, 2}));
        // 4
        System.out.println(singleNumber(new int[]{-3, -3, 7}));
        // 7
    }
}
```

**How to run:** `java SingleNumber.java`

## 6. Walkthrough

Trace `singleNumber(nums)` on `nums = [4,1,2,1,2]`:

| num | result before | result = result ^ num |
|---|---|---|
| 4 | 0 | 0^4 = 4 |
| 1 | 4 | 4^1 = 5 |
| 2 | 5 | 5^2 = 7 |
| 1 | 7 | 7^1 = 6 |
| 2 | 6 | 6^2 = 4 |

Final `result = 4`, the single unpaired value. Time complexity is O(n), one XOR per element. Space is O(1), a single accumulator regardless of array size.

## 7. Gotchas & takeaways

> Gotcha: this exact technique only works when the unwanted values appear an EVEN number of times — if the problem instead says "every element appears THREE times except one" (Single Number II), plain XOR-cancellation gives a wrong answer, since three copies do not cancel to `0` under XOR.

- This is the canonical example of trading a `HashSet` (O(n) space) for a single accumulator variable (O(1) space), using a mathematical property (`a ^ a = 0`) instead of an explicit "have I seen this" data structure.
- The order of the input array does not matter at all, since XOR is commutative and associative — shuffling `nums` gives the identical final `result`.
- Related problems: Find the Difference (the same XOR-cancellation idea, applied to characters instead of integers), Missing Number (a related XOR trick, cancelling indices against values instead of pairs).
