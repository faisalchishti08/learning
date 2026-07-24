---
card: leetcode-patterns
gi: 320
slug: permutation-sequence
title: Permutation Sequence
---

## 1. What it is

The set `[1, 2, ..., n]` has `n!` distinct permutations. Listing them in ascending lexicographic order, return the `k`-th permutation, as a string. Example: `n = 3`, `k = 3` → `"213"` (the ordered list is `"123","132","213","231","312","321"`; the 3rd is `"213"`).

## 2. Why & when

This problem LOOKS like it needs backtracking (generate all permutations, then index into them), but that wastes time generating `n! - 1` permutations you never need — it teaches you to recognize when a MATH-based direct construction replaces a full backtracking search. Use this shape whenever a problem asks for the `k`-th item in an ORDERED sequence of combinatorial objects (permutations, combinations), since the count of items with a given prefix is often computable directly via factorials.

## 3. Core concept

**Key idea:** the first digit of the `k`-th permutation can be determined directly: there are `(n-1)!` permutations starting with each possible first digit, so `k` divided by `(n-1)!` tells you WHICH first digit to pick, without generating any permutations at all. Repeat this reasoning for each subsequent digit, using the remaining, unused digits.

**Steps:**
1. Precompute `factorial[i]` for `i` from `0` to `n`. Convert `k` to 0-indexed: `k -= 1`.
2. Build a list of available digits `[1, 2, ..., n]`.
3. For each position, from the most significant digit down: compute `blockSize = factorial[remainingDigits - 1]` (how many permutations share the same prefix). Compute `index = k / blockSize` — this is WHICH of the remaining digits goes here. Append `availableDigits[index]` to the result, then REMOVE it from `availableDigits`.
4. Update `k = k % blockSize` (the position WITHIN the chosen block), and repeat for the next position with one fewer digit.
5. Return the built string once every position is filled.

**Why it is correct:** fixing the first digit splits all `n!` permutations into `n` equal-sized blocks of `(n-1)!` permutations each, in sorted order — so `k / (n-1)!` directly identifies which block (and therefore which first digit) contains the `k`-th permutation, and `k % (n-1)!` gives the target's RANK WITHIN that block, ready to repeat the same reasoning one digit shorter. This recursive halving-by-factorial avoids ever constructing a permutation that is not part of the final answer.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dividing k=2 zero-indexed by blocks of size 2! to find the first digit directly, without generating any permutations">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=3, k=3 -&gt; 0-indexed k=2, factorial(2)=2</text>
    <text x="10" y="45">available = [1,2,3], blockSize = 2! = 2</text>
    <text x="10" y="65">index = 2 / 2 = 1 -&gt; pick available[1] = 2 -&gt; result="2", available=[1,3]</text>
    <text x="10" y="85">k = 2 % 2 = 0, blockSize = 1! = 1, index = 0/1=0 -&gt; pick available[0]=1 -&gt; result="21"</text>
    <text x="10" y="105">k=0, blockSize=0!=1, index=0 -&gt; pick available[0]=3 -&gt; result="213"</text>
    <rect x="10" y="115" width="120" height="24" fill="#3fb950"/><text x="70" y="132" fill="#0d1117" text-anchor="middle" font-size="10">"213"</text>
  </g>
</svg>

Each digit is picked by dividing the remaining rank by the block size of the remaining factorial, with no permutations ever generated.

## 5. Runnable example

```java
// PermutationSequence.java
import java.util.*;

public class PermutationSequence {

    // KEY INSIGHT: fixing the first digit splits all n! permutations
    // into n equal blocks of (n-1)! permutations; dividing k by that
    // block size picks the right digit directly, with no need to
    // generate any permutation that is not the answer.

    static String getPermutation(int n, int k) {
        int[] factorial = new int[n + 1];
        factorial[0] = 1;
        for (int i = 1; i <= n; i++) factorial[i] = factorial[i - 1] * i;

        List<Integer> available = new ArrayList<>();
        for (int i = 1; i <= n; i++) available.add(i);

        k -= 1; // convert to 0-indexed
        StringBuilder result = new StringBuilder();

        for (int position = n; position >= 1; position--) {
            int blockSize = factorial[position - 1];
            int index = k / blockSize;
            result.append(available.remove(index));
            k %= blockSize;
        }
        return result.toString();
    }

    public static void main(String[] args) {
        System.out.println(getPermutation(3, 3));
        // 213
        System.out.println(getPermutation(4, 9));
        // 2314
    }
}
```

**How to run:** `java PermutationSequence.java`

## 6. Walkthrough

Trace `getPermutation(3, 3)`, 0-indexed `k = 2`:

| position | blockSize | index = k/blockSize | picked digit | available after | k = k % blockSize |
|---|---|---|---|---|---|
| 3 | 2! = 2 | 2/2 = 1 | available[1] = 2 | [1,3] | 2 % 2 = 0 |
| 2 | 1! = 1 | 0/1 = 0 | available[0] = 1 | [3] | 0 % 1 = 0 |
| 1 | 0! = 1 | 0/1 = 0 | available[0] = 3 | [] | 0 |

Result: `"2" + "1" + "3" = "213"`. Time complexity is O(n²), since removing from an `ArrayList` at an arbitrary index costs O(n), done `n` times. Space is O(n), for the `available` list and the factorial table.

## 7. Gotchas & takeaways

> Gotcha: forgetting to convert `k` to 0-indexed (`k -= 1`) before starting the division logic shifts every computed block index by one, since the problem states `k` as 1-indexed but the block-division math is naturally 0-indexed.

- Recognizing "generate the k-th combinatorial object directly via factorials" instead of "generate everything and index in" is a reusable trick whenever a problem's search space is a well-understood combinatorial structure (permutations here) with a known counting formula.
- `ArrayList.remove(index)` is used here for simplicity; a Fenwick tree (binary indexed tree) or a manually managed array could reduce the removal cost to O(log n) per step for very large `n`.
- Related problems: Permutations (full backtracking generation of every permutation, when you need them ALL, not just the k-th), Combination Sum III (a different combinatorial counting problem, but one that still benefits from early pruning rather than a closed-form shortcut).
