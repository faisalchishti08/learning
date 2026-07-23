---
card: leetcode-patterns
gi: 256
slug: bitwise-xor-bit-manipulation-template-xor-cancellation-masks
title: Bitwise XOR / Bit Manipulation — template: XOR cancellation, masks, and shifts
---

## 1. What it is

Three reusable snippets cover almost every problem in this family: the **XOR-cancellation template** (find an unpaired value), the **bit-counting template** (count or inspect set bits), and the **mask-and-shift template** (build, read, or modify specific bits directly).

## 2. Why & when

Memorizing these tiny templates means you spend your time on WHICH bits matter for a given problem, not on re-deriving how to loop over bits or clear a specific bit from scratch. Bit manipulation bugs are often invisible until tested on specific edge values (0, negative numbers, the maximum `int`), so a fixed, well-tested shape avoids repeating the same mistakes.

Use XOR cancellation whenever duplicates should vanish and a lone value should remain. Use bit-counting whenever the problem is about "how many bits are set" or "which power of two." Use mask-and-shift whenever you need to read, set, clear, or toggle SPECIFIC bit positions (not just count them).

## 3. Core concept

**XOR-cancellation template.**
1. Initialize `result = 0`.
2. XOR every relevant value into `result`, in a single pass: `result ^= value`.
3. Everything that appears an even number of times cancels to `0`; what remains is the answer.

**Bit-counting template (lowest-set-bit trick).**
1. Initialize `count = 0`.
2. While `n != 0`: do `n &= (n - 1)` (this clears the lowest set bit), then `count++`.
3. `count` is the total number of set bits (the "population count" or "Hamming weight").

**Mask-and-shift template.**
1. To CHECK bit `i` of `n`: `(n >> i) & 1` (shift bit `i` down to position 0, then mask everything else off), or equivalently `(n & (1 << i)) != 0`.
2. To SET bit `i`: `n | (1 << i)`.
3. To CLEAR bit `i`: `n & ~(1 << i)`.
4. To TOGGLE bit `i`: `n ^ (1 << i)`.
5. To loop over all 32 bits of an `int`: `for (int i = 0; i < 32; i++) { ... (n >> i) & 1 ... }`.

The key insight shared by all three: bit operations are constant-time per bit and per operation, so a loop over 32 bits (for a standard `int`) is effectively O(1) work, not something to worry about asymptotically — the real cost is almost always the outer loop over the input array or string.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XOR cancellation reduces pairs to zero, lowest-set-bit trick clears one bit at a time, mask isolates one bit position">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">n &amp; (n-1) clears the lowest set bit</text>
    <text x="20" y="45" fill="#e6edf3" font-family="monospace">n     = 1011 0</text>
    <text x="20" y="65" fill="#e6edf3" font-family="monospace">n-1   = 1010 1</text>
    <text x="20" y="85" fill="#3fb950" font-family="monospace">n&amp;(n-1)= 1010 0  (lowest 1 cleared)</text>

    <text x="380" y="20" fill="#e6edf3" font-weight="bold">Mask isolates one bit position</text>
    <text x="380" y="45" fill="#e6edf3" font-family="monospace">n        = 0110 1</text>
    <text x="380" y="65" fill="#e6edf3" font-family="monospace">1 &lt;&lt; 2   = 0010 0</text>
    <text x="380" y="85" fill="#3fb950" font-family="monospace">n &amp; mask = 0010 0  (bit 2 is set)</text>
  </g>
</svg>

Each template isolates or removes exactly one piece of bit-level information per step, using a fixed, reusable expression.

## 5. Runnable example

```java
// BitManipulationTemplates.java
public class BitManipulationTemplates {

    static int xorCancellation(int[] nums) {
        int result = 0;
        for (int num : nums) result ^= num;
        return result;
    }

    static int countSetBits(int n) {
        int count = 0;
        while (n != 0) {
            n &= (n - 1);
            count++;
        }
        return count;
    }

    static int setBit(int n, int i) { return n | (1 << i); }
    static int clearBit(int n, int i) { return n & ~(1 << i); }
    static int toggleBit(int n, int i) { return n ^ (1 << i); }
    static boolean checkBit(int n, int i) { return (n & (1 << i)) != 0; }

    public static void main(String[] args) {
        System.out.println(xorCancellation(new int[]{4, 1, 2, 1, 2}));
        // 4

        System.out.println(countSetBits(11));
        // 3

        int n = 0b0101; // 5
        System.out.println(checkBit(n, 0)); // true (bit 0 is set)
        System.out.println(checkBit(n, 1)); // false
        System.out.println(setBit(n, 1));   // 0111 = 7
        System.out.println(clearBit(n, 0)); // 0100 = 4
        System.out.println(toggleBit(n, 2));// 0001 = 1
    }
}
```

**How to run:** `java BitManipulationTemplates.java`

## 6. Walkthrough

1. `xorCancellation([4,1,2,1,2])`: XOR-ing left to right, `4^1=5`, `5^2=7`, `7^1=6`, `6^2=4`. Result `4`, the unpaired value.
2. `countSetBits(11)`: `11` is binary `1011`. First iteration: `1011 & 1010 = 1010`, count=1. Second: `1010 & 1001 = 1000`, count=2. Third: `1000 & 0111 = 0000`, count=3. Loop ends, `count=3`.
3. `checkBit(5, 0)`: `5` is binary `0101`. `(0101 >> 0) & 1 = 1`, so bit 0 is set — `true`.
4. `setBit(5, 1)`: `0101 | 0010 = 0111 = 7`.
5. `clearBit(5, 0)`: `0101 & ~0001 = 0101 & 1110 = 0100 = 4`.

## 7. Gotchas & takeaways

> Gotcha: `n & (n - 1)` on `n = 0` would loop forever if the `while` condition were wrong, but the correct condition `while (n != 0)` naturally stops, since `0 & (0 - 1)` is never reached — always double check the loop condition matches the trick's stopping case.

- XOR-cancellation needs O(1) space and a single pass — always prefer it over a `HashSet` when the "appears twice except one" signal is present.
- `n & (n - 1)` runs its loop only as many times as there are SET bits, not 32 times always — it is faster in practice than checking every bit position one by one for sparse numbers.
- These three templates, combined or applied to individual characters/digits instead of whole numbers, are the direct basis for every named problem in this section — Single Number uses XOR-cancellation, Number of 1 Bits uses bit-counting, Reverse Bits uses mask-and-shift.
