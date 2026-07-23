---
card: leetcode-patterns
gi: 275
slug: xor-queries-of-a-subarray
title: XOR Queries of a Subarray
---

## 1. What it is

Given an array `arr` and a list of `queries`, where each query is `[left, right]`, return an array where each entry is the XOR of all elements in `arr[left..right]` inclusive, for the corresponding query. Example: `arr = [1,3,4,8]`, `queries = [[0,1],[1,2],[0,3],[3,3]]` → `[2,7,14,8]`.

## 2. Why & when

XOR-ing a subarray range directly for every query is O(range length) per query, or O(n · q) overall. Building a PREFIX XOR array once, up front, answers every query in O(1), the same idea as a prefix sum array but using XOR instead of addition. Use this shape whenever a problem asks for many range-based XOR (or sum) queries over a fixed array — precompute a running combination once, then answer each query with a simple lookup.

## 3. Core concept

**Key idea:** build `prefixXor[i] = arr[0] ^ arr[1] ^ ... ^ arr[i-1]` (the XOR of everything BEFORE index `i`), with `prefixXor[0] = 0`. The XOR of any range `arr[left..right]` is then `prefixXor[right + 1] ^ prefixXor[left]`, because everything before index `left` appears in BOTH prefix values and cancels out under XOR, leaving only the range `[left, right]`.

**Steps:**
1. Build `prefixXor` of length `n + 1`. Set `prefixXor[0] = 0`.
2. For `i` from `0` to `n - 1`: `prefixXor[i + 1] = prefixXor[i] ^ arr[i]`.
3. For each query `[left, right]`: compute `prefixXor[right + 1] ^ prefixXor[left]` and add it to the results.
4. Return the results array.

**Why it is correct:** `prefixXor[right + 1] = arr[0] ^ ... ^ arr[right]` and `prefixXor[left] = arr[0] ^ ... ^ arr[left-1]`. XOR-ing these two together, the shared prefix `arr[0] ^ ... ^ arr[left-1]` appears in BOTH terms and cancels to `0` (since `a ^ a = 0`), leaving exactly `arr[left] ^ ... ^ arr[right]` — the XOR of just the queried range. This is the same telescoping cancellation idea as a prefix-sum range-sum query, adapted to XOR.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="prefixXor array built from arr, query left=1 right=2 computed as prefixXor 3 xor prefixXor 1">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr = [1,3,4,8], prefixXor = [0,1,2,6,14]</text>
    <text x="10" y="45">query [1,2]: arr[1]^arr[2] = 3^4 = 7</text>
    <text x="10" y="65">prefixXor[3] ^ prefixXor[1] = 6 ^ 1 = 7</text>
    <rect x="10" y="75" width="30" height="24" fill="#3fb950"/><text x="25" y="92" fill="#0d1117" text-anchor="middle" font-size="9">7</text>
    <text x="45" y="92">matches directly, no need to re-scan arr[1..2]</text>
  </g>
</svg>

Two overlapping prefix XORs cancel their shared portion automatically, leaving exactly the queried range.

## 5. Runnable example

```java
// XORQueriesOfASubarray.java
public class XORQueriesOfASubarray {

    // Level 1 -- Brute force: for each query, loop from left to right,
    // XOR-ing every element in that range directly. Correct, but
    // O(n * q) overall -- slow when there are many queries over a
    // large array.

    // KEY INSIGHT: a prefix XOR array, built once in O(n), lets any
    // range XOR be answered in O(1) via prefixXor[right+1] ^
    // prefixXor[left] -- the same telescoping idea as prefix sums.

    // Level 2 -- Optimal: prefix XOR array, O(1) per query.
    static int[] xorQueries(int[] arr, int[][] queries) {
        int n = arr.length;
        int[] prefixXor = new int[n + 1];
        for (int i = 0; i < n; i++) {
            prefixXor[i + 1] = prefixXor[i] ^ arr[i];
        }

        int[] result = new int[queries.length];
        for (int i = 0; i < queries.length; i++) {
            int left = queries[i][0], right = queries[i][1];
            result[i] = prefixXor[right + 1] ^ prefixXor[left];
        }
        return result;
    }

    // Level 3 -- Hardened: works unchanged for a single-element query
    // range (left == right), since prefixXor[right+1] ^ prefixXor[left]
    // correctly isolates just that one element in that case too.

    public static void main(String[] args) {
        int[] arr = {1, 3, 4, 8};
        int[][] queries = {{0,1},{1,2},{0,3},{3,3}};
        System.out.println(java.util.Arrays.toString(xorQueries(arr, queries)));
        // [2, 7, 14, 8]
    }
}
```

**How to run:** `java XORQueriesOfASubarray.java`

## 6. Walkthrough

Building `prefixXor` for `arr = [1,3,4,8]`:

| i | arr[i] | prefixXor[i+1] = prefixXor[i]^arr[i] |
|---|---|---|
| 0 | 1 | 0^1 = 1 |
| 1 | 3 | 1^3 = 2 |
| 2 | 4 | 2^4 = 6 |
| 3 | 8 | 6^8 = 14 |

`prefixXor = [0,1,2,6,14]`. Answering `queries = [[0,1],[1,2],[0,3],[3,3]]`:

| query | prefixXor[right+1] ^ prefixXor[left] | result |
|---|---|---|
| [0,1] | prefixXor[2]^prefixXor[0] = 2^0 | 2 |
| [1,2] | prefixXor[3]^prefixXor[1] = 6^1 | 7 |
| [0,3] | prefixXor[4]^prefixXor[0] = 14^0 | 14 |
| [3,3] | prefixXor[4]^prefixXor[3] = 14^6 | 8 |

Result `[2,7,14,8]` matches the expected output. Time complexity is O(n + q), building the prefix array once in O(n) and answering each of `q` queries in O(1). Space is O(n) for the prefix array.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `+1` offset (using `prefixXor[right]` instead of `prefixXor[right + 1]`) excludes the element AT index `right` from the range — always double-check the off-by-one indexing convention, exactly as with prefix-sum arrays.

- This is the XOR analogue of the classic prefix-sum range-query technique — recognize that XOR shares the same telescoping/cancellation property that makes prefix sums work (an invertible, associative operation with an identity element).
- Precomputing once and answering each query in O(1) is a major improvement whenever the number of queries is large relative to the array size — always consider this tradeoff when many range queries are expected.
- Related problems: Decode XORed Array (a related XOR-chain idea, reconstructing values instead of answering range queries), Single Number (uses the same core `a ^ a = 0` cancellation property).
