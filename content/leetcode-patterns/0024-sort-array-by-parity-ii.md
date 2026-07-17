---
card: leetcode-patterns
gi: 24
slug: sort-array-by-parity-ii
title: Sort Array By Parity II
---

## 1. What it is

Given an integer array `nums` of even length, where exactly half its values are even and half are odd, rearrange it so that `nums[i]` is even whenever `i` is even, and odd whenever `i` is odd. Any valid arrangement is accepted. Example: `nums = [4, 2, 5, 7]` → a valid answer is `[4, 5, 2, 7]`.

## 2. Why & when

Every position has a required parity (even index needs an even value, odd index needs an odd value). Two pointers, each scanning only the positions with one parity, can find and swap mismatches in place. This is a different two-pointer shape from Sort Colors: instead of three regions, you track two interleaved pointers, one for even slots and one for odd slots.

## 3. Core concept

**Key idea:** an even index holding an odd value is exactly wrong when paired with an odd index holding an even value — swapping those two fixes both mismatches in a single operation.

**Steps:**
1. Set `even = 0` (walks only even indices: 0, 2, 4, …) and `odd = 1` (walks only odd indices: 1, 3, 5, …).
2. While `even < nums.length` and `odd < nums.length`:
   - Advance `even` by 2 while `nums[even]` is already even (that slot is already correct).
   - Advance `odd` by 2 while `nums[odd]` is already odd (that slot is already correct).
   - If both pointers are still in bounds, swap `nums[even]` and `nums[odd]` — this places a valid value at both positions.
3. Return `nums`.

**Why it is correct:** the array has exactly as many even values as even slots (given the problem's 50/50 guarantee), so every misplaced odd value at an even index has a matching misplaced even value somewhere at an odd index. The two pointers only ever need to find those two misplaced values and swap them — no third scan or extra storage required.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sort array by parity two pointers on even and odd slots">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [4, 2, 5, 7]  (index 0,2 need even; 1,3 need odd)</text>
    <rect x="20" y="40" width="44" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="64" y="40" width="44" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="108" y="40" width="44" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="40" width="44" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="42" y="60" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="86" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="130" y="60" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="174" y="60" fill="#e6edf3" text-anchor="middle">7</text>
    <text x="42" y="90" fill="#79c0ff" text-anchor="middle">even=0 (ok, skip to 2)</text>
    <text x="86" y="90" fill="#f0883e" text-anchor="middle">odd=1 (2 is even, wrong!)</text>
    <text x="20" y="125" fill="#8b949e">even advances to index 2 (value 5, odd -&gt; wrong); swap with odd=1 (value 2)</text>
  </g>
</svg>

`even` and `odd` each skip over already-correct slots, then swap the first pair of mismatches they find.

## 5. Runnable example

```java
// SortArrayByParityII.java
import java.util.Arrays;

public class SortArrayByParityII {

    // Level 1 -- Brute force: split into two lists (evens, odds), then
    // interleave them into a new array. O(n) time, O(n) extra space for
    // the two lists.
    static int[] bruteForce(int[] nums) {
        java.util.List<Integer> evens = new java.util.ArrayList<>();
        java.util.List<Integer> odds = new java.util.ArrayList<>();
        for (int v : nums) {
            if (v % 2 == 0) evens.add(v); else odds.add(v);
        }
        int[] result = new int[nums.length];
        for (int i = 0; i < evens.size(); i++) result[2 * i] = evens.get(i);
        for (int i = 0; i < odds.size(); i++) result[2 * i + 1] = odds.get(i);
        return result;
    }

    // KEY INSIGHT: every misplaced odd value at an even slot has a matching
    // misplaced even value at an odd slot (the array is guaranteed 50/50),
    // so a single swap between two mismatched pointers fixes both at once.

    // Level 2 -- Optimal: two interleaved pointers, in-place swap. O(n)
    // time, O(1) space.
    public static int[] sortArrayByParityII(int[] nums) {
        int even = 0, odd = 1;
        int n = nums.length;
        while (even < n && odd < n) {
            if (nums[even] % 2 == 0) {
                even += 2;
            } else if (nums[odd] % 2 == 1) {
                odd += 2;
            } else {
                int tmp = nums[even];
                nums[even] = nums[odd];
                nums[odd] = tmp;
            }
        }
        return nums;
    }

    // Level 3 -- Hardened: an array already correctly arranged runs the
    // loop with only the two "already correct" branches firing, never the
    // swap branch, and terminates once both pointers exceed n.
    static int[] hardened(int[] nums) {
        if (nums == null || nums.length % 2 != 0) {
            throw new IllegalArgumentException("nums must have even length");
        }
        return sortArrayByParityII(nums);
    }

    public static void main(String[] args) {
        int[] nums = {4, 2, 5, 7};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(sortArrayByParityII(nums)));

        int[] alreadySorted = {2, 3, 4, 5};
        System.out.println("already correct: " + Arrays.toString(hardened(alreadySorted)));
    }
}
```

How to run: save as `SortArrayByParityII.java`, then run `java SortArrayByParityII.java`.

## 6. Walkthrough

Dry run of `sortArrayByParityII({4, 2, 5, 7})`:

| step | even | odd | nums[even] | nums[odd] | action | array after |
|---|---|---|---|---|---|---|
| 1 | 0 | 1 | 4 (even, ok) | — | even += 2 | [4,2,5,7] |
| 2 | 2 | 1 | 5 (odd, wrong) | 2 (even, wrong) | swap | [4,5,2,7] |
| 3 | 2 | 1 | 2 (even, ok) | — | even += 2 | [4,5,2,7] |
| 4 | 4 | 1 | — | — | even (4) >= n (4), loop ends | [4,5,2,7] |

Final array: `[4, 5, 2, 7]` — every even index holds an even value, every odd index holds an odd value. Time complexity: O(n), each pointer visits at most n/2 positions. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: using `if / else if / else` incorrectly (for example, checking `nums[odd] % 2 == 1` before confirming `even` is still in range) can read past the array — always check both pointer bounds in the `while` condition before touching `nums[even]` or `nums[odd]`.

- Recognize this as a "two independent skip-and-swap pointers" shape, distinct from opposite-ends (converging) and same-direction single-pointer-writes (Move Zeroes) — both pointers here move forward, but each skips over a *different* condition.
- Related problems: Sort Colors, Segregate Even and Odd Numbers, Wiggle Sort.
