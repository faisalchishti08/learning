---
card: leetcode-patterns
gi: 272
slug: maximum-xor-of-two-numbers-in-an-array
title: Maximum XOR of Two Numbers in an Array
---

## 1. What it is

Given an integer array `nums`, find the maximum possible value of `nums[i] XOR nums[j]` over all pairs, in O(n) time. Example: `nums = [3,10,5,25,2,8]` → `28` (achieved by `5 XOR 25 = 28`).

## 2. Why & when

Checking every pair directly is O(n²). Instead, build the answer bit by bit from the HIGHEST bit down, greedily trying to set each bit of the answer to `1` and checking (using a hash set of number PREFIXES) whether some pair in the array can actually achieve that bit pattern. Use this shape whenever a problem asks for a maximum XOR over pairs, since greedy bit-by-bit construction with a prefix-membership check beats brute force.

## 3. Core concept

**Key idea:** build the answer bit by bit, from the most significant bit (bit 31 or lower, depending on the value range) down to bit 0. At each step, assume the best answer so far (`currentAnswer`) can have its next bit set to `1` (`candidate = currentAnswer | (1 << bit)`), and check if any TWO prefixes in the array (their bits truncated to the current bit level) XOR together to produce exactly `candidate`. If such a pair of prefixes exists, keep the bit set; otherwise, leave it as `0`.

**Steps:**
1. Find `maxBit`, the highest bit position that could be set in any number (for a 32-bit `int`, this is bit 31, or you can compute it from the maximum value in `nums`).
2. Initialize `answer = 0`.
3. For `bit` from `maxBit` down to `0`: build `candidate = answer | (1 << bit)`.
4. Build a `HashSet` of all numbers in `nums`, each truncated to just its top `(maxBit - bit + 1)` bits (using a mask).
5. For each prefix `p` in the set, check if `(p ^ candidate)` is also in the set — if so, some pair of prefixes XORs to `candidate`, so keep `answer = candidate`.
6. If no such pair exists, leave `answer` unchanged (that bit stays `0`).
7. Return `answer` after processing all bit positions.

**Why it is correct:** the maximum XOR is built greedily from the top bit down, because a `1` in a higher bit position always contributes more to the final value than any combination of lower bits ever could — exactly like greedy digit selection when maximizing a number. At each step, checking "does some pair of truncated prefixes XOR to give me this candidate" correctly determines feasibility, since XOR of two full numbers' prefixes at bit level `k` only depends on their top `k` bits — lower bits cannot interfere with a check restricted to the current prefix length.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building answer bit by bit, greedily testing if a 1 at each position is achievable by some pair of prefixes">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [3,10,5,25,2,8], building answer top-down</text>
    <text x="10" y="45">bit 4: try answer=10000; check prefixes -&gt; achievable, keep it</text>
    <text x="10" y="65">bit 3: try answer=11000; check prefixes -&gt; achievable, keep it</text>
    <text x="10" y="85">bit 2: try answer=11100; check prefixes -&gt; achievable, keep it</text>
    <rect x="10" y="95" width="60" height="24" fill="#3fb950"/><text x="40" y="112" fill="#0d1117" text-anchor="middle" font-size="9">11100=28</text>
    <text x="80" y="112">final answer after all bits: 28</text>
  </g>
</svg>

Each bit position is greedily tested against feasibility, building the largest achievable XOR value from the top down.

## 5. Runnable example

```java
// MaximumXOROfTwoNumbersInAnArray.java
import java.util.*;

public class MaximumXOROfTwoNumbersInAnArray {

    // Level 1 -- Brute force: check every pair (i, j), computing
    // nums[i] ^ nums[j] and tracking the maximum. Correct, but O(n^2)
    // -- too slow for large arrays.

    // KEY INSIGHT: build the answer bit by bit from the top down,
    // greedily assuming each new bit can be 1, and verifying with a
    // hash set of number PREFIXES whether some pair actually achieves
    // that candidate value -- O(n) work per bit, O(32n) total.

    // Level 2 -- Optimal: greedy bit construction with prefix checks.
    static int findMaximumXOR(int[] nums) {
        int maxBit = 0;
        for (int num : nums) maxBit = Math.max(maxBit, 31 - Integer.numberOfLeadingZeros(Math.max(num, 1)));

        int answer = 0;
        int mask = 0;
        for (int bit = maxBit; bit >= 0; bit--) {
            mask |= (1 << bit);
            Set<Integer> prefixes = new HashSet<>();
            for (int num : nums) prefixes.add(num & mask);

            int candidate = answer | (1 << bit);
            for (int p : prefixes) {
                if (prefixes.contains(p ^ candidate)) {
                    answer = candidate;
                    break;
                }
            }
        }
        return answer;
    }

    // Level 3 -- Hardened: computes maxBit dynamically from the actual
    // input values (using Integer.numberOfLeadingZeros), instead of
    // hardcoding 31, so smaller inputs don't waste iterations on
    // always-zero high bits.

    public static void main(String[] args) {
        System.out.println(findMaximumXOR(new int[]{3, 10, 5, 25, 2, 8}));
        // 28
    }
}
```

**How to run:** `java MaximumXOROfTwoNumbersInAnArray.java`

## 6. Walkthrough

For `nums = [3,10,5,25,2,8]`, `maxBit = 4` (since `25 = 11001` needs 5 bits, indices 0-4):

| bit | candidate | prefixes at this mask | matching pair found? | new answer |
|---|---|---|---|---|
| 4 | 16 | {0, 16} | yes (0 ^ 16 = 16) | 16 |
| 3 | 24 | {0, 8, 24} | yes (0 ^ 24 = 24) | 24 |
| 2 | 28 | {0, 4, 8, 24} | yes (4 ^ 24 = 28) | 28 |
| 1 | 30 | {2, 4, 8, 10, 24} | no | 28 (unchanged) |
| 0 | 29 | {2, 3, 5, 8, 10, 25} | no | 28 (unchanged) |

The final answer is `28`, achieved by the pair `5 (00101) ^ 25 (11001) = 11100 = 28`. Time complexity is O(32n) = O(n), since there are at most 32 bit positions, each requiring one O(n) pass to build and check prefixes. Space is O(n) for the prefix set.

## 7. Gotchas & takeaways

> Gotcha: the prefix set must be rebuilt (or the mask widened) at EVERY bit level, since a "prefix" at bit level `k` is a different truncation than at bit level `k+1` — reusing a stale prefix set from a previous iteration gives incorrect feasibility checks.

- This greedy, bit-by-bit construction with a feasibility check is a reusable technique whenever you need to maximize (or minimize) a bitwise combination across many candidates, without checking every pair explicitly.
- A Trie-based approach (inserting each number's bits into a binary trie, then greedily walking for the opposite bit at each level) solves this same problem with the same O(32n) complexity and is a common alternative worth mentioning.
- Related problems: Single Number III (another problem using a "find a distinguishing bit" idea), Bitwise AND of Numbers Range (a different range/prefix reasoning problem).
