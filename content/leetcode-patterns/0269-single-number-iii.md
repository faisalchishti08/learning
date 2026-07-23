---
card: leetcode-patterns
gi: 269
slug: single-number-iii
title: Single Number III
---

## 1. What it is

Given an integer array where exactly TWO elements appear once and every other element appears exactly twice, return the two single elements (in any order). Example: `nums = [1,2,1,3,2,5]` → `[3,5]`.

## 2. Why & when

Plain XOR-cancellation (Single Number) finds ONE unpaired value, but here there are two, and XOR-ing everything together only gives their COMBINED XOR — you need one more trick to SEPARATE them into two groups. Use this shape whenever a problem has exactly two unpaired values mixed into an otherwise-paired array; the key extra step is finding a bit that distinguishes the two unknowns.

## 3. Core concept

**Key idea:** XOR the whole array together first. Every properly paired value cancels out, leaving `xorAll = single1 ^ single2`. Since `single1 != single2`, `xorAll` is nonzero, and at least one bit is set in it — pick any such bit, say the LOWEST set bit. That bit must differ between `single1` and `single2` (since a bit position where `xorAll` is `1` means the two singles disagree there). Split the entire array into two groups based on whether each number has that bit set, and XOR each group separately — each group contains exactly one of the two singles, plus fully-paired values that still cancel.

**Steps:**
1. Compute `xorAll` by XOR-ing every element in `nums`.
2. Find the lowest set bit of `xorAll`: `diffBit = xorAll & (-xorAll)` (isolates the lowest set bit using two's complement negation).
3. Initialize `group1 = 0`, `group2 = 0`.
4. For each `num` in `nums`: if `(num & diffBit) != 0`, XOR it into `group1`; otherwise XOR it into `group2`.
5. Return `[group1, group2]`.

**Why it is correct:** `diffBit` is guaranteed to be a bit where `single1` and `single2` differ, so they land in DIFFERENT groups. Every other value, appearing exactly twice, has both copies land in the SAME group (since a value's bits don't change between its two occurrences), so both copies still cancel within that group. Each group therefore reduces to exactly one of the two single elements.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="nums 1 2 1 3 2 5, xorAll=3^5=6, lowest set bit=2, split into groups by bit 2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1,2,1,3,2,5], singles are 3 and 5</text>
    <text x="10" y="45">xorAll = 1^2^1^3^2^5 = 3^5 = 6 (binary 110)</text>
    <text x="10" y="65">diffBit = lowest set bit of 6 = 2 (binary 010)</text>
    <rect x="10" y="80" width="30" height="24" fill="#3fb950"/><text x="25" y="97" fill="#0d1117" text-anchor="middle" font-size="9">3</text>
    <text x="45" y="97">bit 1 set (011 &amp; 010 != 0) -&gt; group1</text>
    <rect x="10" y="110" width="30" height="24" fill="#e3b341"/><text x="25" y="127" fill="#0d1117" text-anchor="middle" font-size="9">5</text>
    <text x="45" y="127">bit 1 clear (101 &amp; 010 == 0) -&gt; group2</text>
  </g>
</svg>

The distinguishing bit sends the two singles into separate groups, while every paired value's two identical copies always land together.

## 5. Runnable example

```java
// SingleNumberIII.java
public class SingleNumberIII {

    // Level 1 -- Brute force: use a HashMap<Integer, Integer> to count
    // occurrences, then collect every value with count 1. Correct, but
    // O(n) SPACE for the map, violating the O(1) space bar this
    // problem's follow-up typically asks for.

    // KEY INSIGHT: XOR-ing everything gives single1 ^ single2. Any bit
    // set in that combined XOR must differ between the two singles,
    // so splitting the array by that bit separates them into two
    // independent Single-Number subproblems.

    // Level 2 -- Optimal: XOR-all, split by the lowest differing bit.
    static int[] singleNumber(int[] nums) {
        int xorAll = 0;
        for (int num : nums) xorAll ^= num;

        int diffBit = xorAll & (-xorAll); // isolate lowest set bit

        int group1 = 0, group2 = 0;
        for (int num : nums) {
            if ((num & diffBit) != 0) group1 ^= num;
            else group2 ^= num;
        }
        return new int[]{group1, group2};
    }

    // Level 3 -- Hardened: `xorAll & (-xorAll)` correctly isolates the
    // lowest set bit using two's-complement negation, working for any
    // nonzero xorAll, including negative values.

    public static void main(String[] args) {
        System.out.println(java.util.Arrays.toString(singleNumber(new int[]{1, 2, 1, 3, 2, 5})));
        // [3, 5] (order may vary)
    }
}
```

**How to run:** `java SingleNumberIII.java`

## 6. Walkthrough

Trace `singleNumber([1,2,1,3,2,5])`:

1. `xorAll = 1^2^1^3^2^5`. Pairs `1^1` and `2^2` cancel, leaving `xorAll = 3^5 = 6` (binary `110`).
2. `diffBit = 6 & (-6)`. In two's complement, `-6` is `...11111010`, so `6 & -6 = 010 = 2` (the lowest set bit of `6`).
3. Splitting `nums` by bit `1` (value `2`): `1` (binary `001`, bit clear) → group2; `2` (binary `010`, bit set) → group1; `1` again → group2; `3` (binary `011`, bit set) → group1; `2` again → group1; `5` (binary `101`, bit clear) → group2.
4. `group1 = 2^3^2 = 3` (the two `2`s cancel, leaving `3`). `group2 = 1^1^5 = 5` (the two `1`s cancel, leaving `5`).

Result `[3, 5]` matches the expected singles. Time complexity is O(n), three passes over the array. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: using `xorAll & (xorAll - 1)` (the "clear lowest bit" trick) instead of `xorAll & (-xorAll)` (the "isolate lowest bit" trick) computes the WRONG mask — always double check which of these two similar-looking expressions you need, since they answer different questions.

- This problem's key extra insight beyond plain Single Number is realizing that ANY bit set in `single1 ^ single2` can be used to split the array — the lowest set bit is just a convenient, simple choice, not the only valid one.
- Every fully-paired value's two copies always share the exact same bit pattern, so splitting by any fixed bit always sends both copies to the same group — this is what keeps the two subproblems independent and correct.
- Related problems: Single Number (the one-single-element base case), Single Number II (a different generalization, three copies instead of two, using modulo-3 bit counting instead of a XOR split).
