---
card: leetcode-patterns
gi: 264
slug: complement-of-base-10-integer
title: Complement of Base 10 Integer
---

## 1. What it is

The complement of an integer is formed by flipping every `0` to `1` and every `1` to `0` in its binary representation, using only as many bits as the number actually needs (no leading zero padding). Given a non-negative integer `n`, return its complement. Example: `n = 5` (binary `101`) → `2` (binary `010`).

## 2. Why & when

Flipping every bit sounds like a job for `~n` (bitwise NOT), but `~n` flips ALL 32 bits of a Java `int`, including a huge run of leading zeros that are not conceptually part of `n`'s "true" bit width — giving a wrong (and negative) result. Use this shape whenever a problem needs to flip bits within the SIGNIFICANT bit width of a number, not its full fixed-width representation.

## 3. Core concept

**Key idea:** build a mask of all `1`s that is exactly as wide as `n`'s binary representation (no wider). XOR-ing `n` with that mask flips exactly the bits that matter: any bit that was `1` becomes `0`, and any bit that was `0` (within the mask's width) becomes `1`. Bits outside the mask's width (which would be `0` in both `n` and the mask) stay `0` under XOR.

**Steps:**
1. If `n == 0`, return `1` immediately (0's complement, using its own 1-bit width, is `1`).
2. Build `mask` by starting at `1` and repeatedly shifting left and OR-ing in `1`, until `mask >= n` (this creates a run of 1s exactly as wide as `n`'s bits — for example, `n=5` needs `mask=7`, i.e. `111`).
3. Return `n ^ mask`.

**Why it is correct:** XOR-ing `n` with a same-width all-1s mask flips every bit within that width: a `1` XOR `1` becomes `0`, and a `0` XOR `1` becomes `1`. Building the mask by repeatedly shifting and OR-ing until it is at least as large as `n` guarantees the mask has exactly as many `1` bits as `n`'s own bit width, so no extra high bits are touched (they stay `0` on both sides).

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="n=101, mask built as 111 (same width), XOR gives 010, the complement">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 5 (binary 101)</text>
    <text x="10" y="45" font-family="monospace">n     = 101</text>
    <text x="10" y="65" font-family="monospace">mask  = 111  (same width as n, built bit by bit)</text>
    <text x="10" y="85" fill="#3fb950" font-family="monospace">n^mask= 010  (= 2, the complement)</text>
    <text x="10" y="110">using ~n instead would flip all 32 bits, giving a wrong, negative result</text>
  </g>
</svg>

The mask must match `n`'s exact bit width, or the XOR flips bits that were never part of the original number's significant range.

## 5. Runnable example

```java
// ComplementOfBase10Integer.java
public class ComplementOfBase10Integer {

    // Level 1 -- Brute force: convert n to a binary string, flip each
    // character ('0' to '1' and vice versa), then parse the flipped
    // string back into an integer. Correct, but wastes time and
    // memory on string conversion for a fixed-width bit operation.

    // KEY INSIGHT: build a same-width all-1s mask, then XOR it with n
    // -- flipping every significant bit directly, without touching
    // any bits beyond n's own width.

    // Level 2 -- Optimal: build a matching-width mask, then XOR.
    static int bitwiseComplement(int n) {
        if (n == 0) return 1;

        int mask = 0;
        int temp = n;
        while (temp > 0) {
            mask = (mask << 1) | 1;
            temp >>= 1;
        }
        return n ^ mask;
    }

    // Level 3 -- Hardened: explicitly handles n == 0 as a special
    // case, since the mask-building loop would never run for n=0,
    // leaving mask=0 and producing an incorrect complement of 0
    // instead of the expected 1.

    public static void main(String[] args) {
        System.out.println(bitwiseComplement(5));
        // 2
        System.out.println(bitwiseComplement(7));
        // 0
        System.out.println(bitwiseComplement(10));
        // 5
    }
}
```

**How to run:** `java ComplementOfBase10Integer.java`

## 6. Walkthrough

Trace `bitwiseComplement(5)`, `n = 5` (binary `101`):

| temp | mask before | mask after (mask<<1 \| 1) | temp after (temp >> 1) |
|---|---|---|---|
| 5 | 0 (0) | 1 (1) | 2 |
| 2 | 1 (1) | 3 (11) | 1 |
| 1 | 3 (11) | 7 (111) | 0 |

Loop ends when `temp` reaches `0`. `mask = 7` (binary `111`), matching `n`'s 3-bit width. `n ^ mask = 101 ^ 111 = 010 = 2`, the correct complement. Time complexity is O(log n), since the mask-building loop runs once per bit of `n`. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: using Java's built-in `~n` (bitwise NOT) instead of a same-width mask gives a completely wrong answer, since `~n` flips all 32 bits of the `int`, including the leading zeros that are not part of `n`'s "real" binary representation — always build a width-matched mask first.

- This problem's core insight — build a mask matching the exact significant bit width, then XOR — is a reusable technique any time "flip only the meaningful bits" is required, distinct from flipping every bit of the fixed-width representation.
- The special case for `n == 0` is easy to forget, since the mask-building loop naturally produces `mask = 0` for `temp = 0`, which would incorrectly return `0 ^ 0 = 0` instead of the correct answer, `1`.
- Related problems: Reverse Bits (another bit-rearranging operation, using a fixed 32-bit loop instead of a variable-width mask), Number of 1 Bits (uses the same "how many bits matter" reasoning, applied to counting instead of flipping).
