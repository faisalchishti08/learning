---
card: leetcode-patterns
gi: 273
slug: gray-code
title: Gray Code
---

## 1. What it is

An `n`-bit Gray code sequence is an ordering of all `2^n` integers from `0` to `2^n - 1` such that every consecutive pair (including the last value back to the first) differs in EXACTLY ONE bit. Given `n`, return any valid Gray code sequence. Example: `n = 2` → `[0,1,3,2]` (binary `00, 01, 11, 10` — each step flips exactly one bit).

## 2. Why & when

Instead of searching or backtracking to build a sequence where consecutive values differ by one bit, there is a direct closed-form formula: `i XOR (i >> 1)`, applied to every `i` from `0` to `2^n - 1`, always produces a valid Gray code sequence. Use this shape whenever a problem asks for a specific bit-adjacent ordering, since a known formula often replaces what looks like a search problem.

## 3. Core concept

**Key idea:** the formula `gray(i) = i ^ (i >> 1)` converts a normal binary count into Gray code directly. As `i` increments by 1 in normal binary, exactly one bit of `i` flips at the LOWEST differing position, but this formula's XOR with `i`'s own right-shift guarantees each consecutive Gray-coded value differs by exactly one bit, by construction of how binary counting overflows propagate.

**Steps:**
1. Compute the total count: `total = 1 << n` (which is `2^n`).
2. Create a result list of size `total`.
3. For `i` from `0` to `total - 1`: compute `result[i] = i ^ (i >> 1)`.
4. Return the result list.

**Why it is correct:** this is a well-known bijection between standard binary and Gray code (reflected binary code). The right-shift-then-XOR construction ensures that between `gray(i)` and `gray(i+1)`, exactly one bit differs, because incrementing `i` by 1 changes its lowest set of trailing bits in a pattern that this XOR transformation always reduces to a single bit flip in the output. This is a mathematically proven identity, not something that needs re-derivation per input — applying the formula directly is both correct and O(1) per value.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="i values 0 1 2 3 converted via i xor i shift right 1 to gray codes 0 1 3 2, each differing by one bit from the previous">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 2, computing gray(i) = i ^ (i &gt;&gt; 1)</text>
    <text x="10" y="45">i=0 (00): 00^00=00=0</text>
    <text x="10" y="65">i=1 (01): 01^00=01=1</text>
    <text x="10" y="85">i=2 (10): 10^01=11=3</text>
    <text x="10" y="105">i=3 (11): 11^01=10=2</text>
    <rect x="10" y="115" width="150" height="24" fill="#3fb950"/><text x="85" y="132" fill="#0d1117" text-anchor="middle" font-size="9">[0, 1, 3, 2]</text>
  </g>
</svg>

Each output value differs from its predecessor by exactly one bit, confirmed by comparing consecutive binary forms `00, 01, 11, 10`.

## 5. Runnable example

```java
// GrayCode.java
import java.util.*;

public class GrayCode {

    // Level 1 -- Brute force: backtrack, building the sequence one
    // value at a time, checking at each step that the next candidate
    // differs from the last by exactly one bit and hasn't been used
    // yet. Correct, but far more complex than needed, and slower due
    // to the search and duplicate-checking overhead.

    // KEY INSIGHT: the direct formula i ^ (i >> 1) is a well-known,
    // proven bijection that always produces a valid Gray code
    // ordering -- no search or backtracking is needed at all.

    // Level 2 -- Optimal: apply the closed-form formula directly.
    static List<Integer> grayCode(int n) {
        int total = 1 << n;
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < total; i++) {
            result.add(i ^ (i >> 1));
        }
        return result;
    }

    // Level 3 -- Hardened: works unchanged for n=0 (total=1, returns
    // just [0], a trivially valid single-element Gray code sequence).

    public static void main(String[] args) {
        System.out.println(grayCode(2));
        // [0, 1, 3, 2]
    }
}
```

**How to run:** `java GrayCode.java`

## 6. Walkthrough

Trace `grayCode(2)`, `total = 4`:

| i (binary) | i >> 1 (binary) | i ^ (i >> 1) | decimal |
|---|---|---|---|
| 00 | 00 | 00 | 0 |
| 01 | 00 | 01 | 1 |
| 10 | 01 | 11 | 3 |
| 11 | 01 | 10 | 2 |

Result `[0, 1, 3, 2]`. Checking consecutive pairs: `0(00)` to `1(01)` differs in bit 0 only; `1(01)` to `3(11)` differs in bit 1 only; `3(11)` to `2(10)` differs in bit 0 only; and wrapping around, `2(10)` to `0(00)` differs in bit 1 only. Every consecutive pair, including the wraparound, differs by exactly one bit. Time complexity is O(2^n), since the output itself has `2^n` elements. Space is O(2^n) for the output.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to try to construct the sequence by simulating "flip one bit at a time" with an explicit search, but this reinvents a well-established closed-form identity — recognizing `i ^ (i >> 1)` as a known formula (like recognizing the triangular number formula in Arranging Coins) saves significant implementation complexity.

- The output size is always exactly `2^n`, matching the requirement that the sequence covers every integer from `0` to `2^n - 1` exactly once.
- This is one of the few problems in this section where the answer is a KNOWN MATHEMATICAL FORMULA rather than a technique you derive from first principles — worth memorizing directly.
- Related problems: Single Number III (uses bit manipulation to split values, a different kind of bit-level reasoning), Complement of Base 10 Integer (another problem involving a fixed transformation over a number's bit pattern).
