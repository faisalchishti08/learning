---
card: leetcode-patterns
gi: 255
slug: bitwise-xor-bit-manipulation-signal-pairing-toggling-or-coun
title: Bitwise XOR / Bit Manipulation — signal: pairing, toggling, or counting bits
---

## 1. What it is

Bit Manipulation problems work directly on the binary representation of numbers, using operators like `XOR` (`^`), `AND` (`&`), `OR` (`|`), and shifts (`<<`, `>>`) instead of arithmetic or comparisons. Think of every integer as a fixed-width row of 0s and 1s, where each bit can be inspected, flipped, or counted independently and extremely fast.

## 2. Why & when

Reach for this pattern whenever a problem can be reframed in terms of "which bits are set," "how many times does a value cancel out," or "toggle this on/off," since bit operations run in O(1) per operation and often turn an O(n) or O(n log n) problem into O(n) with a much smaller constant, or even O(1).

Learn to recognize these signals in a problem statement:

- **"Every element appears twice except one"** (or similar pairing language) — XOR cancellation: `a ^ a = 0`, so pairs vanish and the single element remains.
- **"Count the number of 1 bits," "hamming weight," "hamming distance"** — direct bit-counting, usually with `n & (n - 1)` to strip the lowest set bit.
- **"Is this a power of two," "is this a power of four"** — a single set bit has a very specific pattern (`n & (n - 1) == 0`).
- **"Reverse the bits," "find the complement," "toggle bits"** — direct bit manipulation via shifts and masks.
- **"Missing number," "duplicate number," "single number"** — often solvable by XOR-ing everything together, since duplicates cancel.

The alternative — using a `HashSet` or sorting to find duplicates/missing values — works but uses O(n) extra space or O(n log n) time; bit manipulation frequently achieves the same result in O(n) time and O(1) space.

## 3. Core concept

Every bit-manipulation problem boils down to one of a small number of building-block operations, applied bit by bit or across a whole array:

**XOR cancellation.** `a ^ a = 0` and `a ^ 0 = a`. XOR-ing a list where every value appears an even number of times except one leaves only that one value, because every pair cancels to `0`, and XOR-ing with `0` changes nothing.

**Masking.** `n & mask` isolates specific bits (for example, `n & 1` checks the lowest bit; `n & (1 << i)` checks bit `i`). `n | mask` sets specific bits. `n & ~mask` clears specific bits.

**Shifting.** `n << k` multiplies by `2^k` (and moves bits left, filling with 0s). `n >> k` divides by `2^k` (moves bits right). Shifting is how you visit each bit position one at a time in a loop.

**The lowest-set-bit trick.** `n & (n - 1)` clears the LOWEST set bit of `n`. Repeating this until `n` becomes `0` counts the set bits; checking if it makes `n` exactly `0` in ONE step tells you `n` had exactly one set bit (a power of two).

The key insight: bit operations are O(1) per operation and work on the WHOLE number at once, in parallel across all bit positions — which is why they can replace slower array or hash-based techniques for problems that are fundamentally about presence, parity, or counting.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XOR cancellation showing pairs of bits cancelling to zero, leaving the single element">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">XOR cancellation: [4, 1, 2, 1, 2]</text>
    <text x="10" y="45">4 ^ 1 ^ 2 ^ 1 ^ 2</text>
    <text x="10" y="65">= 4 ^ (1^1) ^ (2^2)   (regroup pairs)</text>
    <text x="10" y="85">= 4 ^ 0 ^ 0</text>
    <rect x="10" y="100" width="30" height="24" fill="#3fb950"/><text x="25" y="117" fill="#0d1117" text-anchor="middle" font-size="9">4</text>
    <text x="50" y="117">= 4 (the single element)</text>
    <text x="10" y="150">bit-level: 0100 ^ 0001 ^ 0010 ^ 0001 ^ 0010 = 0100</text>
  </g>
</svg>

Every duplicated value cancels itself out under XOR, leaving only the value that appears an odd number of times.

## 5. Runnable example

```java
// BitManipulationSignal.java
public class BitManipulationSignal {

    // Signal check 1: pairing/cancellation via XOR.
    static int findSingle(int[] nums) {
        int result = 0;
        for (int num : nums) result ^= num;
        return result;
    }

    // Signal check 2: counting set bits via the lowest-set-bit trick.
    static int countSetBits(int n) {
        int count = 0;
        while (n != 0) {
            n &= (n - 1); // clears the lowest set bit
            count++;
        }
        return count;
    }

    // Signal check 3: power-of-two check, reusing the same trick.
    static boolean isPowerOfTwo(int n) {
        return n > 0 && (n & (n - 1)) == 0;
    }

    public static void main(String[] args) {
        System.out.println(findSingle(new int[]{4, 1, 2, 1, 2}));
        // 4 (pairing signal)

        System.out.println(countSetBits(11)); // binary 1011
        // 3 (counting signal)

        System.out.println(isPowerOfTwo(16));
        // true (single-bit signal)
    }
}
```

**How to run:** `java BitManipulationSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Every element appears twice except one" is the pairing/cancellation signal — XOR everything together.
2. Running `findSingle` on `[4,1,2,1,2]` confirms the pairs `1^1` and `2^2` cancel, leaving `4`.
3. If instead the problem says "count the number of set bits," that is the counting signal — use `n & (n - 1)` in a loop, confirmed by `countSetBits(11) == 3` (binary `1011` has three 1s).
4. If the problem says "is this a power of two," recognize that a power of two has EXACTLY one set bit, so the same `n & (n - 1)` trick, checked in a single step against `0`, answers the question directly.
5. This upfront classification (pairing, counting, or single-bit-check) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: XOR cancellation only works cleanly when every unwanted value appears an EVEN number of times — if a problem allows a value to appear three times (see Single Number II elsewhere), plain XOR no longer isolates the answer, and a different bit-counting technique (tracking bit counts mod 3) is needed instead.

- XOR cancellation (`a ^ a = 0`): the pairing/duplicate-removal signal.
- `n & (n - 1)` (clear lowest set bit): the counting/power-of-two signal.
- Shifts and masks (`<<`, `>>`, `&`, `|`, `~`): the direct bit-inspection/toggling signal, used to visit or modify individual bit positions.
