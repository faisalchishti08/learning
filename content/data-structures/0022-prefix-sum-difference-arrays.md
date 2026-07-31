---
card: data-structures
gi: 22
slug: prefix-sum-difference-arrays
title: Prefix-sum & difference arrays
---

## 1. What it is

A **prefix-sum array** stores, at each index `i`, the running total of all elements from the start of the array up to `i`. Once built, it answers "what is the sum of any range `[l, r]`?" in O(1), instead of re-adding elements every time. A **difference array** is its mirror image: it stores the *change between* consecutive elements, letting you apply the same update to an entire range in O(1) instead of updating every element in that range one by one.

## 2. Why & when

Use a prefix-sum array when you need to answer many range-sum queries on data that does not change — building it once costs O(n), and each query after that costs O(1), instead of O(n) per query with a naive loop. Use a difference array when you need to apply many range updates (like "add 5 to every element from index 2 to 6") to data you will only read once at the end.

## 3. Core concept

**How prefix sum works.** Define `prefix[i] = arr[0] + arr[1] + ... + arr[i-1]`, with `prefix[0] = 0`. The sum of any range `[l, r]` (inclusive) is then `prefix[r+1] - prefix[l]` — one subtraction, because `prefix[r+1]` already includes everything up to `r`, and subtracting `prefix[l]` removes everything before `l`.

**Why this is correct.** `prefix[r+1] - prefix[l]` equals `(arr[0]+...+arr[r]) - (arr[0]+...+arr[l-1])`, and the shared `arr[0]+...+arr[l-1]` terms cancel out, leaving exactly `arr[l] + ... + arr[r]`.

**How a difference array works.** Define `diff[i] = arr[i] - arr[i-1]` (with `diff[0] = arr[0]`). To add a value `v` to every element in range `[l, r]`, you only touch two positions: `diff[l] += v` and `diff[r+1] -= v`. Reconstructing the final array by taking the prefix sum of `diff` applies that `+v` to every position from `l` onward, and the `-v` at `r+1` cancels it out exactly where the range ends.

**The pattern behind both: trade an O(n) per-operation cost for an O(n) one-time setup.** Prefix sum front-loads the cost of summing so queries are free. A difference array defers the cost of applying updates so each update is free, paying the full O(n) cost only once, when you reconstruct the array at the end.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A prefix-sum array below the original array, and a range sum computed as one subtraction between two prefix values">
  <g font-family="sans-serif" font-size="12">
    <text x="320" y="18" fill="#8b949e" text-anchor="middle">arr:      3    1    4    1    5</text>
    <text x="320" y="42" fill="#8b949e" text-anchor="middle">prefix: 0    3    4    8    9    14</text>
    <rect x="230" y="55" width="55" height="26" fill="#161b22" stroke="#3fb950"/><text x="257" y="73" fill="#e6edf3" text-anchor="middle" font-size="10">prefix[1]=3</text>
    <rect x="400" y="55" width="55" height="26" fill="#161b22" stroke="#3fb950"/><text x="427" y="73" fill="#e6edf3" text-anchor="middle" font-size="10">prefix[4]=9</text>
    <text x="320" y="110" fill="#79c0ff" text-anchor="middle">sum(arr[1..3]) = prefix[4] - prefix[1] = 9 - 3 = 6</text>
    <text x="320" y="135" fill="#8b949e" text-anchor="middle" font-size="10">(check: arr[1]+arr[2]+arr[3] = 1+4+1 = 6, matches)</text>
  </g>
</svg>

`prefix[4] - prefix[1]` gives the sum of `arr[1..3]` directly, with no need to re-add those elements one by one.

## 5. Runnable example

```java
// PrefixSumDifferenceArrays.java
import java.util.Arrays;

public class PrefixSumDifferenceArrays {

    // Basic: build a prefix-sum array, then answer range-sum queries in O(1) each.
    static int[] buildPrefixSum(int[] arr) {
        int[] prefix = new int[arr.length + 1]; // prefix[0] = 0 by default
        for (int i = 0; i < arr.length; i++) {
            prefix[i + 1] = prefix[i] + arr[i];
        }
        return prefix;
    }

    static int rangeSum(int[] prefix, int l, int r) { // inclusive [l, r]
        return prefix[r + 1] - prefix[l];
    }

    static void basicLevel() {
        int[] arr = {3, 1, 4, 1, 5};
        int[] prefix = buildPrefixSum(arr);
        System.out.println("basic: prefix array -> " + Arrays.toString(prefix));
        System.out.println("basic: sum(arr[1..3]) -> " + rangeSum(prefix, 1, 3)); // 1+4+1 = 6
        System.out.println("basic: sum(arr[0..4]) -> " + rangeSum(prefix, 0, 4)); // whole array = 14
    }

    // Intermediate: many queries on the same array, each O(1) after the one-time O(n) build.
    static void intermediateLevel() {
        int[] arr = new int[100_000];
        for (int i = 0; i < arr.length; i++) arr[i] = (i % 7) + 1;
        int[] prefix = buildPrefixSum(arr); // O(n) once

        int total = 0;
        for (int q = 0; q < 10_000; q++) { // 10,000 O(1) queries
            int l = q % 50_000, r = l + 100;
            total += rangeSum(prefix, l, r);
        }
        System.out.println("intermediate: sum across 10,000 range queries -> " + total);
    }

    // Advanced: a difference array applying many range updates in O(1) each, reconstructed once at the end.
    static void advancedLevel() {
        int n = 10;
        int[] diff = new int[n + 1]; // one extra slot for the "cancel" position

        // "add 5 to indexes 2..6"
        diff[2] += 5;
        diff[7] -= 5;
        // "add 3 to indexes 0..4"
        diff[0] += 3;
        diff[5] -= 3;

        int[] result = new int[n];
        int running = 0;
        for (int i = 0; i < n; i++) {
            running += diff[i]; // reconstruct via prefix sum of the diff array
            result[i] = running;
        }
        System.out.println("advanced: reconstructed array -> " + Arrays.toString(result));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PrefixSumDifferenceArrays.java`, then run `java PrefixSumDifferenceArrays.java`.

## 6. Walkthrough

1. `basicLevel()` builds `prefix` from `{3,1,4,1,5}`: `prefix = [0,3,4,8,9,14]`. Each `prefix[i+1]` is the previous prefix value plus `arr[i]`.
2. `rangeSum(prefix, 1, 3)` computes `prefix[4] - prefix[1] = 9 - 3 = 6`, matching `arr[1]+arr[2]+arr[3] = 1+4+1 = 6` — one subtraction instead of three additions.
3. `intermediateLevel()` builds the prefix array once (O(n)), then runs 10,000 range queries, each a single subtraction — far cheaper than re-summing each range from scratch, which would cost O(n) per query.
4. `advancedLevel()` applies two range updates to `diff` using only 4 array writes total: `diff[2]+=5, diff[7]-=5` marks "+5 starts at index 2, stops after index 6"; `diff[0]+=3, diff[5]-=3` marks "+3 starts at index 0, stops after index 4".
5. Reconstructing `result` by running a prefix sum over `diff` applies both updates correctly at every index: indexes 0-1 get +3, indexes 2-4 get +3+5=+8, indexes 5-6 get +5, index 7-9 get +0 — each range update only cost O(1) to apply, with the full O(n) cost paid once during reconstruction.

## 7. Gotchas & takeaways

> Gotcha: `prefix[r+1] - prefix[l]`, not `prefix[r] - prefix[l]` — the off-by-one is the most common bug with prefix sums. Because `prefix[i]` is defined as the sum of the first `i` elements (up to but not including index `i`), including index `r` in the range requires `prefix[r+1]`.

- A prefix-sum array turns O(n) range-sum queries into O(1) queries, after a one-time O(n) build.
- A difference array turns O(n) range-update operations into O(1) updates, deferring the full cost to a single O(n) reconstruction pass.
- Both trade an upfront or deferred O(n) cost for making the *repeated* operation (query, or update) O(1).
- Related concepts: [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md) (another incremental-update technique), [In-place rotation & reversal](0023-in-place-rotation-reversal.md).
