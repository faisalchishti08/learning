---
card: leetcode-patterns
gi: 276
slug: minimum-flips-to-make-a-or-b-equal-to-c
title: Minimum Flips to Make a OR b Equal to c
---

## 1. What it is

Given three integers `a`, `b`, and `c`, find the MINIMUM number of bit flips needed in `a` and `b` so that `a OR b` equals `c`. Example: `a = 2` (`010`), `b = 6` (`110`), `c = 5` (`101`) → `3`.

## 2. Why & when

Because OR combines two numbers bit by bit independently, the number of flips needed at EACH bit position can be figured out on its own — the total answer is just the sum of the per-bit costs. Use this shape whenever a problem asks for a minimum number of changes to make a bitwise combination (OR, AND, XOR) equal a target, since bit-independence lets you solve each position separately and add up the results.

## 3. Core concept

**Key idea:** for each bit position `i`, look at the bit of `a`, the bit of `b`, and the bit of `c` at that position. There are only a few cases: if `c`'s bit is `1`, you need AT LEAST ONE of `a` or `b`'s bits to be `1` — if BOTH are currently `0`, flip one of them (cost `1`); otherwise, cost `0` (already satisfied). If `c`'s bit is `0`, BOTH `a` and `b`'s bits must be `0` — flip each one that is currently `1` (cost `0`, `1`, or `2`, depending on how many are set).

**Steps:**
1. Initialize `flips = 0`.
2. For each bit position `i` from `0` to `31` (or until `a`, `b`, and `c` are all exhausted): extract `bitA = (a >> i) & 1`, `bitB = (b >> i) & 1`, `bitC = (c >> i) & 1`.
3. If `bitC == 1`: if `bitA == 0 && bitB == 0`, add `1` to `flips` (need to set at least one of them).
4. If `bitC == 0`: add `bitA + bitB` to `flips` (flip every set bit among `a` and `b`, since both must become `0`).
5. Return `flips` after checking all relevant bit positions.

**Why it is correct:** OR is computed independently at each bit position — the value of bit `i` in `a OR b` depends ONLY on bit `i` of `a` and `b`, never on any other position. So minimizing total flips is equivalent to minimizing flips at EACH position independently, and summing those independent minimums gives the global minimum. The case analysis (target `1` needs at least one source `1`; target `0` needs both sources `0`) covers every possible combination exhaustively.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a=010, b=110, c=101, bit by bit comparison showing which positions need flips">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">a=010, b=110, c=101</text>
    <text x="10" y="45">bit 0: a=0,b=0,c=1 -&gt; need at least one 1, flip one (cost 1)</text>
    <text x="10" y="65">bit 1: a=1,b=1,c=0 -&gt; both must be 0, flip both (cost 2)</text>
    <text x="10" y="85">bit 2: a=0,b=1,c=1 -&gt; already satisfied (cost 0)</text>
    <rect x="10" y="95" width="30" height="24" fill="#3fb950"/><text x="25" y="112" fill="#0d1117" text-anchor="middle" font-size="9">3</text>
    <text x="45" y="112">total flips = 1 + 2 + 0 = 3</text>
  </g>
</svg>

Each bit position is judged independently, and the per-position costs simply add up to the total minimum.

## 5. Runnable example

```java
// MinimumFlipsToMakeAOrBEqualToC.java
public class MinimumFlipsToMakeAOrBEqualToC {

    // Level 1 -- Brute force: there is no meaningfully slower
    // alternative that still respects the bit-independence structure
    // -- any correct solution must eventually reason about each bit
    // position, since OR combines bits independently. A "brute force"
    // here would only be trying every possible modified (a, b) pair,
    // which is exponential and unnecessary given the direct per-bit
    // reasoning below.

    // KEY INSIGHT: OR combines each bit position independently, so the
    // minimum total flips is the SUM of the minimum flips needed at
    // each bit position, computed with a simple case check.

    // Level 2 -- Optimal: per-bit case analysis, summed.
    static int minFlips(int a, int b, int c) {
        int flips = 0;
        for (int i = 0; i < 32; i++) {
            int bitA = (a >> i) & 1;
            int bitB = (b >> i) & 1;
            int bitC = (c >> i) & 1;

            if (bitC == 1) {
                if (bitA == 0 && bitB == 0) flips++;
            } else {
                flips += bitA + bitB;
            }
        }
        return flips;
    }

    // Level 3 -- Hardened: checking all 32 bit positions unconditionally
    // (rather than stopping early) correctly handles cases where a, b,
    // or c have set bits at high positions that the others lack.

    public static void main(String[] args) {
        System.out.println(minFlips(2, 6, 5));
        // 3
        System.out.println(minFlips(4, 2, 7));
        // 1
        System.out.println(minFlips(1, 2, 3));
        // 0
    }
}
```

**How to run:** `java MinimumFlipsToMakeAOrBEqualToC.java`

## 6. Walkthrough

Trace `minFlips(2, 6, 5)`, `a = 010`, `b = 110`, `c = 101`:

| bit i | bitA | bitB | bitC | case | flips added |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 1 | need >=1 one, both are 0 | 1 |
| 1 | 1 | 1 | 0 | both must be 0, both are 1 | 2 |
| 2 | 0 | 1 | 1 | already satisfied | 0 |

Total `flips = 1 + 2 + 0 = 3`, matching the expected answer. Time complexity is O(1), since the loop always runs exactly 32 times for a fixed-width integer. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: when `bitC == 0`, BOTH `a` and `b`'s bits must become `0` if either is currently `1` — this can cost up to `2` flips at a single bit position, unlike the `bitC == 1` case, which never costs more than `1` (since only ONE of `a` or `b` needs to be set, not both).

- This problem's bit-independence property (each output bit of `a OR b` depends only on the same-position bits of `a` and `b`) is what allows a simple, direct per-bit summation instead of any search or optimization technique.
- The same reasoning approach — decompose into independent bit positions, solve each with a small case analysis, sum the results — generalizes to similar "minimum flips for AND/XOR to equal target" problem variants.
- Related problems: Hamming Distance (a related "count differing bit positions" idea, though without a target-satisfying constraint), Sum of Two Integers (another problem reasoning about bits position by position, though for arithmetic instead of a minimization).
