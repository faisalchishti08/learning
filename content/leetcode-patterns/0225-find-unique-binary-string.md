---
card: leetcode-patterns
gi: 225
slug: find-unique-binary-string
title: Find Unique Binary String
---

## 1. What it is

Given an array `nums` of `n` distinct binary strings, each of length `n`, return any binary string of length `n` that does NOT appear in `nums`. Example: `nums = ["01","10"]` → `"11"` is a valid answer (also `"00"` would work).

## 2. Why & when

This problem looks like a search problem but is really a counting argument in disguise: there are `2^n` possible binary strings of length `n`, but only `n` of them are given, so at least one is always missing. Use the "flip the diagonal bit" trick whenever you must produce ONE item guaranteed to be outside a given list, and the list size is smaller than the total possible items.

## 3. Core concept

**Key idea:** build a new string `result` of length `n`. For each index `i`, look at `nums[i]`'s `i`-th character and flip it (`0` becomes `1`, `1` becomes `0`). This is Cantor's diagonalization argument: the result differs from `nums[i]` at position `i`, for every `i`, so it cannot equal any string in `nums`.

**Steps:**
1. Let `n = nums.length`.
2. Create a character array `result` of length `n`.
3. For each index `i` from `0` to `n - 1`: read `nums[i].charAt(i)`. If it is `'0'`, set `result[i] = '1'`. Otherwise set `result[i] = '0'`.
4. Return `result` joined as a string.

**Why it is correct:** for any index `i`, `result` differs from `nums[i]` at position `i` by construction. Two strings that differ at even one position are not equal. So `result` differs from `nums[0]`, from `nums[1]`, and so on, from every single string in `nums` — it cannot be any of them, regardless of what the other characters look like.

## 4. Diagram

<svg viewBox="0 0 420 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagonal of nums flipped bit by bit to build a string absent from nums">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums[0] = 0 1</text>
    <text x="10" y="40">nums[1] = 1 0</text>
    <rect x="10" y="55" width="18" height="20" fill="#f85149"/><text x="19" y="70" fill="#0d1117" text-anchor="middle">0</text>
    <text x="35" y="70">diagonal bit at i=0 from nums[0]: '0'</text>
    <rect x="28" y="55" width="18" height="20" fill="#161b22" stroke="#f85149"/>
    <rect x="10" y="90" width="18" height="20" fill="#161b22" stroke="#f85149"/>
    <rect x="28" y="90" width="18" height="20" fill="#f85149"/><text x="37" y="105" fill="#0d1117" text-anchor="middle">0</text>
    <text x="55" y="105">diagonal bit at i=1 from nums[1]: '0'</text>
    <text x="10" y="135">flip each diagonal bit: 0-&gt;1, 0-&gt;1</text>
    <text x="10" y="155">result = "11", differs from both nums[0] and nums[1]</text>
  </g>
</svg>

The result string reads one character from a different row at each position, then flips it, guaranteeing a mismatch against every row.

## 5. Runnable example

```java
// FindUniqueBinaryString.java
public class FindUniqueBinaryString {

    // Level 1 -- Brute force: try every binary string of length n in
    // numeric order (0, 1, 2, ... as n-bit binary), checking each
    // candidate against every string in nums with a linear scan, until
    // one is not found. Correct, but O(2^n * n^2) in the worst case.

    // KEY INSIGHT: you do not need to search at all. Building a string
    // that differs from nums[i] at position i, for every i, guarantees
    // a string outside nums directly, with no comparisons needed.

    // Level 2 -- Optimal: flip the diagonal bit of each row.
    static String findDifferentBinaryString(String[] nums) {
        int n = nums.length;
        char[] result = new char[n];
        for (int i = 0; i < n; i++) {
            result[i] = (nums[i].charAt(i) == '0') ? '1' : '0';
        }
        return new String(result);
    }

    // Level 3 -- Hardened: works unchanged for n = 1 (single string of
    // length 1, e.g. nums = ["0"] -> result = "1"), since the loop
    // still runs exactly once and flips the only diagonal bit.

    public static void main(String[] args) {
        System.out.println(findDifferentBinaryString(new String[]{"01", "10"}));
        // 11
    }
}
```

**How to run:** `java FindUniqueBinaryString.java`

## 6. Walkthrough

Trace on `nums = ["01", "10"]`, `n = 2`:

| i | nums[i] | nums[i].charAt(i) | flipped bit | result so far |
|---|---|---|---|---|
| 0 | "01" | '0' (index 0) | '1' | "1_" |
| 1 | "10" | '0' (index 1) | '1' | "11" |

The final `result` is `"11"`. Check: `"11"` differs from `"01"` at index 0, and differs from `"10"` at index 1, so it matches neither string in `nums`. Time complexity is O(n) — one pass building the result, one character read and flip per index. Space is O(n) for the result string.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to loop over ALL `2^n` candidate strings and check each against `nums`, but that ignores the guarantee the problem hands you: `nums` has only `n` strings while there are `2^n` possible strings, so the diagonal trick always succeeds in a single O(n) pass, no search needed.

- This is a constructive proof turned into code: instead of searching for a missing item, you build one directly from a property that guarantees it cannot collide with any input row.
- The trick only needs `nums[i]` at position `i` for each `i`, since `nums` has exactly `n` strings and each string has exactly `n` characters, so the diagonal is always in bounds.
- Related idea: Cantor's diagonal argument, the same technique used to prove that the real numbers are uncountable.
