---
card: leetcode-patterns
gi: 257
slug: bitwise-xor-bit-manipulation-complexity-o-n-time-o-1-space
title: Bitwise XOR / Bit Manipulation — complexity: O(n) time, O(1) space
---

## 1. What it is

This page explains why bit-manipulation solutions typically run in O(n) time and O(1) space, why that beats the O(n) time / O(n) space of a hash-set alternative, and lists the named problems that use this pattern.

## 2. Why & when

Interviewers value bit tricks specifically because they eliminate extra memory: a `HashSet<Integer>` to track duplicates costs O(n) space, while XOR-cancellation achieves the same logical result in O(1) space, using only a single accumulator variable. Explaining this space tradeoff, not just stating "it's fast," is the stronger interview answer.

## 3. Core concept

**XOR-cancellation — O(n) time, O(1) space.** A single pass over `n` elements, XOR-ing each into one accumulator variable, is O(n) time (one O(1) operation per element) and O(1) space (only the accumulator, regardless of input size). Compare this to using a `HashSet` to track "seen" values and remove pairs: also O(n) time, but O(n) space for the set itself.

**Bit-counting (`n & (n - 1)`) — O(k) time per number, where k is the number of set bits.** Since the loop only runs once per SET bit (not once per bit position), counting bits in a sparse number (few 1s) is faster than a naive loop over all 32 bit positions. In the worst case (all bits set), it still costs O(32) = O(1) for a fixed-width integer, so this is effectively O(1) per number, O(n) total across an array of `n` numbers.

**Mask-and-shift over a fixed-width integer — O(1) per operation, O(32) = O(1) total per number.** Since `int` and `long` have a fixed number of bits (32 or 64), any loop that visits "every bit of one number" is a CONSTANT amount of work, not something that grows with the input — it only looks like a loop because you're iterating over bit positions, not over the input size.

**Why this beats hash-based alternatives.** A `HashSet`-based duplicate-finder is O(n) time but O(n) space, and each `HashSet` operation carries real constant-factor overhead (hashing, boxing `int` to `Integer`, bucket traversal). XOR-cancellation and bit-counting avoid all of that: primitive `int` operations, no allocation, no hashing — often 5-10x faster in practice despite matching Big-O time complexity.

## 4. Diagram

<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XOR cancellation uses one variable regardless of n, HashSet approach grows memory with n">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">XOR cancellation: O(1) space</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">acc</text>
    <text x="50" y="47">one variable, regardless of array size n</text>

    <text x="10" y="90" font-weight="bold">HashSet approach: O(n) space</text>
    <rect x="10" y="100" width="16" height="16" fill="#161b22" stroke="#30363d"/>
    <rect x="30" y="100" width="16" height="16" fill="#161b22" stroke="#30363d"/>
    <rect x="50" y="100" width="16" height="16" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="100" width="16" height="16" fill="#161b22" stroke="#30363d"/>
    <text x="95" y="113">set entries grow with n</text>
    <text x="10" y="145">both are O(n) time; only space differs</text>
  </g>
</svg>

Both approaches process each element once, but only XOR-cancellation avoids allocating memory proportional to the input size.

## 5. Runnable example

```java
// ComplexityCheck.java
import java.util.*;

public class ComplexityCheck {

    static int xorCancellation(int[] nums) {
        int result = 0;
        for (int num : nums) result ^= num;
        return result;
    }

    static int hashSetApproach(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int num : nums) {
            if (!seen.add(num)) seen.remove(num);
        }
        return seen.iterator().next();
    }

    public static void main(String[] args) {
        int n = 1_000_001; // odd count so one value is unpaired
        int[] nums = new int[n];
        for (int i = 0; i < n / 2; i++) {
            nums[2 * i] = i;
            nums[2 * i + 1] = i;
        }
        nums[n - 1] = 999_999; // the unpaired value

        long start1 = System.nanoTime();
        int result1 = xorCancellation(nums);
        long time1 = System.nanoTime() - start1;

        long start2 = System.nanoTime();
        int result2 = hashSetApproach(nums);
        long time2 = System.nanoTime() - start2;

        System.out.println("XOR result: " + result1 + ", time: " + time1 + "ns");
        System.out.println("HashSet result: " + result2 + ", time: " + time2 + "ns");
        // both results match; XOR uses O(1) space, HashSet uses O(n) space
    }
}
```

**How to run:** `java ComplexityCheck.java`

## 6. Walkthrough

1. `nums` has just over 1,000,000 elements: pairs `0,0,1,1,...` plus one unpaired value.
2. `xorCancellation` makes one pass, using a single `int` accumulator the entire time — memory usage never grows with `n`.
3. `hashSetApproach` makes one pass too, but the `HashSet` grows to hold up to `n/2` boxed `Integer` entries at its peak, before shrinking back down as pairs cancel.
4. Both report the same correct unpaired value, confirming both are correct; the timing typically shows XOR-cancellation running measurably faster, due to avoiding hashing and object allocation entirely.
5. This confirms the practical benefit: for large `n`, the XOR approach uses a small, constant amount of memory, while the HashSet approach's memory footprint scales with the input.

## 7. Gotchas & takeaways

> Gotcha: Big-O time complexity alone (both are O(n)) does not tell the whole story — always mention the SPACE complexity difference (O(1) vs O(n)) when comparing a bit-manipulation solution to its hash-based alternative, since that is usually the actual reason to prefer it.

- Time: O(n) for processing an array of `n` elements with XOR-cancellation or a bit-counting pass; O(1) per individual number for counting or masking operations, since integers have a fixed bit width.
- Space: O(1) for XOR-cancellation and bit-counting/masking — only a small, fixed number of accumulator variables, regardless of input size.
- Reference problems that use this pattern: Single Number, Number of 1 Bits, Counting Bits, Reverse Bits, Hamming Distance, Power of Two, Complement of Base 10 Integer, Find the Difference, Binary Watch.
