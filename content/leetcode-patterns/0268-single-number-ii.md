---
card: leetcode-patterns
gi: 268
slug: single-number-ii
title: Single Number II
---

## 1. What it is

Given an integer array where every element appears exactly THREE times, except for one element that appears exactly once, find that single element, in O(n) time and O(1) space. Example: `nums = [2,2,3,2]` → `3`.

## 2. Why & when

Plain XOR-cancellation (Single Number) only works when unwanted values appear an EVEN number of times — three copies of a value do NOT cancel under XOR. Use this shape whenever a problem changes the "appears twice" signal to "appears three times" (or any fixed count greater than two), since it requires tracking bit counts modulo that count, not simple XOR.

## 3. Core concept

**Key idea:** for each of the 32 bit positions, sum up how many numbers in the array have that bit set. If every unwanted value appears exactly 3 times, the total count at any bit position contributed by unwanted values is always a MULTIPLE OF 3. So `(total count at bit i) % 3` tells you whether the single element has that bit set: nonzero remainder means yes, zero means no.

**Steps:**
1. Initialize `result = 0`.
2. For each bit position `i` from `0` to `31`: count how many numbers in `nums` have bit `i` set, by summing `(num >> i) & 1` across all numbers.
3. Compute `bitCount % 3`. If the remainder is nonzero (must be `1`, since only the single element contributes an unpaired copy), set bit `i` in `result`.
4. After checking all 32 bits, return `result`.

**Why it is correct:** every unwanted value appears exactly 3 times, so it contributes exactly 3 to the count at every bit position where it has a `1` — always a multiple of 3, contributing `0` after taking `% 3`. The single element appears once, contributing exactly `1` to the count at every bit position where IT has a `1`. Summing across all numbers and taking `% 3` per bit position isolates exactly the single element's bit pattern.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="nums 2 2 3 2, bit 0 count is 1 (from the single 3), bit 1 count is 3 (from three 2s), mod 3 gives bit pattern of 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [2,2,3,2]  (2=010, 3=011)</text>
    <text x="10" y="45">bit 0: 2 has 0, 2 has 0, 3 has 1, 2 has 0 -&gt; count=1, 1%3=1 -&gt; bit 0 set</text>
    <text x="10" y="65">bit 1: 2 has 1, 2 has 1, 3 has 1, 2 has 1 -&gt; count=4... wait, recompute per value</text>
    <text x="10" y="90">bit 1: three 2s contribute 3, one 3 contributes 1 -&gt; count=4, 4%3=1 -&gt; bit 1 set</text>
    <rect x="10" y="100" width="30" height="24" fill="#3fb950"/><text x="25" y="117" fill="#0d1117" text-anchor="middle" font-size="9">3</text>
    <text x="50" y="117">result = binary 011 = 3</text>
  </g>
</svg>

Summing bit counts across all numbers and reducing modulo 3 strips away every triple-counted bit, leaving only the single element's pattern.

## 5. Runnable example

```java
// SingleNumberII.java
public class SingleNumberII {

    // Level 1 -- Brute force: use a HashMap<Integer, Integer> to count
    // occurrences of every value, then scan for the one with count 1.
    // Correct, but O(n) SPACE for the map, violating the O(1) space
    // requirement.

    // KEY INSIGHT: summing set-bit counts across all numbers, per bit
    // position, and reducing modulo 3 cancels every value that
    // appears exactly 3 times, leaving only the single element's bits.

    // Level 2 -- Optimal: per-bit counting modulo 3.
    static int singleNumber(int[] nums) {
        int result = 0;
        for (int i = 0; i < 32; i++) {
            int bitSum = 0;
            for (int num : nums) {
                bitSum += (num >> i) & 1;
            }
            if (bitSum % 3 != 0) {
                result |= (1 << i);
            }
        }
        return result;
    }

    // Level 3 -- Hardened: works unchanged for negative numbers, since
    // Java's `>>` on a negative int sign-extends, but each bit
    // position is still checked independently and correctly via `& 1`
    // regardless of the number's sign.

    public static void main(String[] args) {
        System.out.println(singleNumber(new int[]{2, 2, 3, 2}));
        // 3
        System.out.println(singleNumber(new int[]{0, 1, 0, 1, 0, 1, 99}));
        // 99
    }
}
```

**How to run:** `java SingleNumberII.java`

## 6. Walkthrough

Trace `singleNumber([2,2,3,2])` for the low 2 bit positions (`2 = 010`, `3 = 011`):

| bit i | contributions from [2,2,3,2] | bitSum | bitSum % 3 | result bit i |
|---|---|---|---|---|
| 0 | 0,0,1,0 | 1 | 1 | set |
| 1 | 1,1,1,1 | 4 | 1 | set |
| 2 | 0,0,0,0 | 0 | 0 | clear |

Result accumulates bit 0 and bit 1 set: `binary 011 = 3`, matching the expected single element. Time complexity is O(32n) = O(n), since the outer loop over 32 bit positions is a constant factor. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this technique generalizes to "appears k times except one" for any fixed `k`, by replacing `% 3` with `% k` — always confirm the exact repeat count from the problem statement, since the modulus must match exactly.

- This is a strict generalization of Single Number: plain XOR-cancellation is the special case where you reduce bit counts modulo 2 instead of modulo 3.
- The HashMap approach (Level 1) is simpler to write correctly under interview time pressure and worth mentioning first, even though it doesn't meet the O(1) space bar the problem sets.
- Related problems: Single Number (the modulo-2 special case), Single Number III (a different twist: two single elements instead of one, solved with a different XOR-splitting technique).
