---
card: leetcode-patterns
gi: 261
slug: reverse-bits
title: Reverse Bits
---

## 1. What it is

Given a 32-bit unsigned integer `n`, reverse the order of its bits and return the resulting integer. Example: `n = 00000010100101000001111010011100` (binary) → `00111001011110000010100101000000` (binary), which as an unsigned decimal is `964176192`.

## 2. Why & when

This is the direct application of the mask-and-shift template: read each bit from one end of `n`, and write it into the opposite end of a new result. Use this shape whenever a problem asks you to physically rearrange, mirror, or restructure the bit pattern of a number, rather than just count or check bits.

## 3. Core concept

**Key idea:** build the result one bit at a time. On each of the 32 iterations, take the LOWEST bit of the remaining `n` (using `n & 1`), and place it into the correct position of the result — starting from the result's own highest bit and moving toward its lowest, mirroring the order.

**Steps:**
1. Initialize `result = 0`.
2. For `i` from `0` to `31`: extract the lowest bit of `n` with `bit = n & 1`.
3. Shift `result` left by 1 to make room, then OR in `bit`: `result = (result << 1) | bit`.
4. Shift `n` right by 1 to move to the next bit: `n = n >>> 1` (unsigned right shift, to avoid sign extension).
5. After 32 iterations, `result` holds the bit-reversed value.

**Why it is correct:** each loop iteration peels the LOWEST remaining bit off `n` and appends it as the NEW lowest bit of `result` (after first shifting `result` left to push previously-added bits further up). Since the first bit peeled off `n` (its original lowest bit) ends up shifted furthest to the left in `result` by the end (having been shifted 31 more times), and the last bit peeled off (`n`'s original highest bit) ends up as `result`'s lowest bit, the entire bit order is exactly reversed.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="4-bit example: n=1101, reversed one bit at a time into result=1011">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">4-bit example: n = 1101</text>
    <text x="10" y="45">step 1: bit=1 (lowest of n), result = 0001, n = 0110</text>
    <text x="10" y="65">step 2: bit=0, result = 0010, n = 0011</text>
    <text x="10" y="85">step 3: bit=1, result = 0101, n = 0001</text>
    <text x="10" y="105">step 4: bit=1, result = 1011, n = 0000</text>
    <rect x="10" y="115" width="60" height="24" fill="#3fb950"/><text x="40" y="132" fill="#0d1117" text-anchor="middle" font-size="9">1011</text>
    <text x="80" y="132">1101 reversed is 1011</text>
  </g>
</svg>

Each step moves one bit from the low end of `n` to the growing high end of `result`, reversing the order one position at a time.

## 5. Runnable example

```java
// ReverseBits.java
public class ReverseBits {

    // Level 1 -- Brute force: convert n to a 32-character binary
    // string, reverse the string, then parse it back into an integer.
    // Correct, but wastes time and memory on string allocation and
    // parsing, which is unnecessary for a fixed-width bit operation.

    // KEY INSIGHT: peeling the lowest bit off n and appending it as
    // the new lowest bit of a growing result (after shifting result
    // left) naturally reverses the bit order, one bit per iteration,
    // using only integer operations.

    // Level 2 -- Optimal: bit-by-bit reversal with shifts and masks.
    static int reverseBits(int n) {
        int result = 0;
        for (int i = 0; i < 32; i++) {
            int bit = n & 1;
            result = (result << 1) | bit;
            n = n >>> 1; // unsigned right shift
        }
        return result;
    }

    // Level 3 -- Hardened: uses `>>>` (unsigned right shift), not `>>`
    // (signed right shift), so negative n values (which have their
    // sign bit set) do not get incorrectly sign-extended with 1s
    // during the shift.

    public static void main(String[] args) {
        int n = 0b00000010100101000001111010011100;
        System.out.println(Integer.toBinaryString(reverseBits(n)));
        // 111001011110000010100101000000 (leading zero dropped by toBinaryString)
    }
}
```

**How to run:** `java ReverseBits.java`

## 6. Walkthrough

Trace `reverseBits(n)` on a 4-bit shortened example, `n = 1101` (13):

| i | bit = n & 1 | result before | result after (result<<1 \| bit) | n after (n >>> 1) |
|---|---|---|---|---|
| 0 | 1 | 0000 | 0001 | 0110 |
| 1 | 0 | 0001 | 0010 | 0011 |
| 2 | 1 | 0010 | 0101 | 0001 |
| 3 | 1 | 0101 | 1011 | 0000 |

Final `result = 1011`, the bit-reversal of `1101`. Time complexity is O(1), since the loop always runs exactly 32 times regardless of the input value. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: using `>>` (signed right shift) instead of `>>>` (unsigned right shift) on `n` breaks the algorithm for negative inputs — `>>` fills the vacated high bits with copies of the sign bit, corrupting the remaining bits you still need to process, while `>>>` correctly fills with `0`s.

- The loop always runs exactly 32 times, one per bit of a fixed-width `int` — this is what makes the algorithm O(1), not O(log n) or O(n).
- Building `result` by always shifting left before ORing in the new bit is what places each extracted bit into its correctly mirrored final position.
- Related problems: Number of 1 Bits (a different fixed-width bit loop, counting instead of rearranging), Complement of Base 10 Integer (another bit-flipping operation, using a full mask instead of a per-bit loop).
