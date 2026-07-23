---
card: leetcode-patterns
gi: 267
slug: decode-xored-array
title: Decode XORed Array
---

## 1. What it is

An integer array `arr` of length `n` was encoded into `encoded` of length `n - 1`, where `encoded[i] = arr[i] XOR arr[i + 1]`. Given `encoded` and `first` (the value of `arr[0]`), reconstruct the original `arr`. Example: `encoded = [1,2,3]`, `first = 1` → `arr = [1,0,2,1]`.

## 2. Why & when

XOR has a self-inverse property: if `encoded[i] = arr[i] ^ arr[i+1]`, then `arr[i+1] = encoded[i] ^ arr[i]`, since XOR-ing the same value twice cancels it out. Use this shape whenever a sequence is defined by consecutive XOR differences, and you are given one anchor value to unwind the whole chain — the same idea as reconstructing a sequence from consecutive differences in arithmetic, but with XOR instead of subtraction.

## 3. Core concept

**Key idea:** `arr[i+1] = encoded[i] ^ arr[i]`. Starting from the known `arr[0] = first`, walk forward through `encoded`, computing each next value of `arr` from the previous one.

**Steps:**
1. Create `arr` of length `encoded.length + 1`. Set `arr[0] = first`.
2. For `i` from `0` to `encoded.length - 1`: compute `arr[i + 1] = encoded[i] ^ arr[i]`.
3. Return `arr`.

**Why it is correct:** from the definition `encoded[i] = arr[i] ^ arr[i+1]`, XOR-ing both sides with `arr[i]` gives `encoded[i] ^ arr[i] = arr[i] ^ arr[i+1] ^ arr[i] = (arr[i] ^ arr[i]) ^ arr[i+1] = 0 ^ arr[i+1] = arr[i+1]`. This algebraic identity holds for every position, so walking forward from the known `arr[0]`, applying this formula once per step, correctly reconstructs every subsequent value.

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="encoded 1 2 3, first=1, unwinding arr[1]=1^1=0, arr[2]=2^0=2, arr[3]=3^2=1">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">encoded = [1,2,3], first = 1</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <text x="45" y="47">arr[0] = first = 1</text>
    <text x="10" y="75">arr[1] = encoded[0]^arr[0] = 1^1 = 0</text>
    <text x="10" y="95">arr[2] = encoded[1]^arr[1] = 2^0 = 2</text>
    <text x="10" y="115">arr[3] = encoded[2]^arr[2] = 3^2 = 1</text>
  </g>
</svg>

Each new value is unwound directly from the previous value and the corresponding encoded entry, one step at a time.

## 5. Runnable example

```java
// DecodeXORedArray.java
public class DecodeXORedArray {

    // Level 1 -- Brute force: there is no meaningfully "slower"
    // alternative here -- the XOR-inversion formula IS the direct,
    // correct approach, and any other method would need to somehow
    // guess or search for values, which the XOR identity makes
    // entirely unnecessary.

    // KEY INSIGHT: encoded[i] ^ arr[i] = arr[i+1], directly from the
    // definition encoded[i] = arr[i] ^ arr[i+1] and the fact that
    // a ^ a = 0. This unwinds the whole array in a single forward pass.

    // Level 2 -- Optimal: forward reconstruction using XOR inversion.
    static int[] decode(int[] encoded, int first) {
        int[] arr = new int[encoded.length + 1];
        arr[0] = first;
        for (int i = 0; i < encoded.length; i++) {
            arr[i + 1] = encoded[i] ^ arr[i];
        }
        return arr;
    }

    // Level 3 -- Hardened: works unchanged for encoded.length == 1
    // (the shortest possible input, producing a 2-element arr) and
    // for all-zero encoded values (arr becomes constant, since each
    // step's XOR with 0 leaves the value unchanged).

    public static void main(String[] args) {
        System.out.println(java.util.Arrays.toString(decode(new int[]{1, 2, 3}, 1)));
        // [1, 0, 2, 1]
    }
}
```

**How to run:** `java DecodeXORedArray.java`

## 6. Walkthrough

Trace `decode([1,2,3], 1)`:

| i | encoded[i] | arr[i] | arr[i+1] = encoded[i]^arr[i] |
|---|---|---|---|
| 0 | 1 | 1 | 1^1 = 0 |
| 1 | 2 | 0 | 2^0 = 2 |
| 2 | 3 | 2 | 3^2 = 1 |

Final `arr = [1,0,2,1]`, matching the expected output. Time complexity is O(n), a single forward pass. Space is O(n) for the output array (required by the problem).

## 7. Gotchas & takeaways

> Gotcha: it is tempting to think you need `arr[i+1]`'s value BEFORE computing `encoded[i]`, but the algebra flips this exactly around — `encoded[i] ^ arr[i]` directly cancels the known `arr[i]` term, leaving `arr[i+1]` isolated, with no guessing or searching required.

- This is the simplest possible "unwind a XOR chain" problem: a direct one-line recurrence, no search or backtracking needed.
- The technique generalizes to any sequence defined by consecutive differences under an invertible operation (subtraction for arithmetic sequences, XOR here) — always look for the inverse operation to walk the chain forward or backward.
- Related problems: Single Number (uses XOR cancellation in a different structural context), XOR Queries of a Subarray (uses a related prefix-XOR idea to answer range queries).
