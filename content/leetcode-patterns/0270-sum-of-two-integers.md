---
card: leetcode-patterns
gi: 270
slug: sum-of-two-integers
title: Sum of Two Integers
---

## 1. What it is

Given two integers `a` and `b`, return their sum WITHOUT using the `+` or `-` operators. Example: `a = 2`, `b = 3` → `5`.

## 2. Why & when

This problem forces you to think about how addition actually works at the hardware level: bit by bit, with carries. `XOR` computes the sum of two bits IGNORING any carry, and `AND` (shifted left by one) computes exactly the carry that XOR ignored. Use this shape whenever a problem restricts you from using arithmetic operators directly and asks you to simulate them using only bitwise operations.

## 3. Core concept

**Key idea:** for two bits, `XOR` gives the sum without carry (`1^1=0`, `1^0=1`, `0^0=0` — matches addition except it drops the carry-out from `1+1=10`). `AND` gives exactly the positions where a carry is generated (`1&1=1` means a carry into the next position). Shift that carry left by one (since a carry moves to the NEXT bit position), then repeat: XOR the running sum with the shifted carry, AND them again for a new carry, until there is no carry left.

**Steps:**
1. While `b != 0` (there is still a carry to add in):
2. Compute `carry = (a & b) << 1` (the carry bits, shifted to their correct next position).
3. Compute `a = a ^ b` (the sum so far, without any carry).
4. Set `b = carry` (the carry becomes the new "second number" to add in on the next iteration).
5. When `b` reaches `0`, `a` holds the final sum.

**Why it is correct:** this is exactly how binary addition works by hand: XOR gives each bit's sum ignoring carry-out, AND-then-shift gives the carry-out that needs to be added into the NEXT bit position. Repeating "XOR for the sum, AND-shift for the new carry" simulates the ripple-carry addition process, one full pass of "no carry left" at a time — it always terminates because each iteration either produces a smaller carry or zero, and a fixed-width integer has finitely many bits to carry through.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a=2 (010), b=3 (011), XOR gives 001, carry AND-shift gives 100, repeat until carry is zero, result 101=5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">a = 2 (010), b = 3 (011)</text>
    <text x="10" y="45">a^b = 001 (sum without carry)</text>
    <text x="10" y="65">(a&amp;b)&lt;&lt;1 = 010&lt;&lt;1 = 100 (carry, shifted)</text>
    <text x="10" y="90">new a=001, new b=100; repeat: a^b=101, (a&amp;b)&lt;&lt;1=0</text>
    <rect x="10" y="100" width="30" height="24" fill="#3fb950"/><text x="25" y="117" fill="#0d1117" text-anchor="middle" font-size="9">5</text>
    <text x="45" y="117">b reaches 0, a = 101 = 5</text>
  </g>
</svg>

Each round separates "sum ignoring carry" from "carry to add next," repeating until no carry remains.

## 5. Runnable example

```java
// SumOfTwoIntegers.java
public class SumOfTwoIntegers {

    // Level 1 -- Brute force: repeatedly increment a by 1, b times (or
    // decrement if b is negative), using only ++ and --. Technically
    // avoids `+` and `-` directly, but is O(|b|) time -- extremely
    // slow for large values, and arguably sidesteps the spirit of the
    // question rather than truly simulating addition.

    // KEY INSIGHT: XOR computes each bit's sum ignoring carry; AND
    // (shifted left by one) computes exactly the carry that XOR
    // dropped. Repeating this process simulates ripple-carry addition
    // directly, in a number of iterations bounded by the bit width.

    // Level 2 -- Optimal: iterative XOR/AND carry simulation.
    static int getSum(int a, int b) {
        while (b != 0) {
            int carry = (a & b) << 1;
            a = a ^ b;
            b = carry;
        }
        return a;
    }

    // Level 3 -- Hardened: works unchanged for negative numbers, since
    // Java's bitwise operators act on the raw two's-complement bit
    // pattern regardless of sign, and the carry-simulation logic is
    // agnostic to whether the final result is positive or negative.

    public static void main(String[] args) {
        System.out.println(getSum(2, 3));
        // 5
        System.out.println(getSum(-2, 3));
        // 1
    }
}
```

**How to run:** `java SumOfTwoIntegers.java`

## 6. Walkthrough

Trace `getSum(2, 3)`, `a = 010`, `b = 011`:

| iteration | a (binary) | b (binary) | carry = (a&b)<<1 | new a = a^b | new b = carry |
|---|---|---|---|---|---|
| 1 | 010 | 011 | (010&011)<<1 = 010<<1 = 100 | 010^011 = 001 | 100 |
| 2 | 001 | 100 | (001&100)<<1 = 000<<1 = 000 | 001^100 = 101 | 000 |

Loop ends since `b = 0`. Final `a = 101 = 5`, the correct sum. Time complexity is O(1), since the loop runs at most 32 times (bounded by the fixed integer width) regardless of the input values. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this technique works identically for negative numbers in Java because `int` uses two's-complement representation and the bitwise operators (`&`, `^`, `<<`) operate on that raw bit pattern — no special-casing for sign is needed, unlike some other bit tricks.

- This problem is the clearest demonstration of "arithmetic IS bit manipulation under the hood" — every `+` operator you've ever used compiles down to exactly this kind of carry-propagation logic in hardware.
- The loop is guaranteed to terminate because the carry can only be nonzero for a bounded number of iterations (at most the bit width of the integer type), since each round either resolves the addition or shifts the carry one position further left, eventually shifting out of range.
- Related problems: Divide Two Integers (another "implement arithmetic using only bit operations" problem, using shifts to simulate division), Reverse Bits (a different fixed-width bit manipulation exercise).
