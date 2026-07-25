---
card: leetcode-patterns
gi: 363
slug: count-vowels-permutation
title: Count Vowels Permutation
---

## 1. What it is

Given `n`, count strings of length `n` using only vowels (`a, e, i, o, u`) that follow these rules: `'a'` can only be followed by `'e'`; `'e'` can only be followed by `'a'` or `'i'`; `'i'` can be followed by anything EXCEPT `'i'`; `'o'` can only be followed by `'i'` or `'u'`; `'u'` can only be followed by `'a'`. Return the count modulo `10^9 + 7`. Example: `n = 2` → `10`.

## 2. Why & when

This is a Fibonacci-style recurrence with FIVE parallel states instead of one — the count of strings ending in each specific vowel depends on the counts of strings ending in whichever vowels are ALLOWED to precede it, at the previous length. Use this shape whenever a problem builds strings (or sequences) one character at a time under a fixed TRANSITION RULE between a small alphabet of states.

## 3. Core concept

**Key idea:** track five rolling counts, one per vowel: `countA[i]`, `countE[i]`, `countI[i]`, `countO[i]`, `countU[i]` = the number of valid length-`i` strings ENDING in that vowel. Each count is built from whichever vowels are allowed to come right before it.

**Steps:**
1. First, invert the "followed by" rules into "preceded by" rules: `a` can follow `e, i, u`; `e` can follow `a, i`; `i` can follow `e, o`; `o` can follow `i`; `u` can follow `i, o`.
2. Base case: at length `1`, every vowel has exactly one valid string (itself): all five counts start at `1`.
3. For `i` from `2` to `n`: `countA = countE_prev + countI_prev + countU_prev`; `countE = countA_prev + countI_prev`; `countI = countE_prev + countO_prev`; `countO = countI_prev`; `countU = countI_prev + countO_prev`.
4. Return the sum of all five counts at length `n`, modulo `10^9 + 7`.

**Why it is correct:** a valid length-`i` string ending in vowel `v` is exactly a valid length-`(i-1)` string ending in some ALLOWED predecessor of `v`, with `v` appended. Summing over every allowed predecessor's count from the previous length counts every valid extension exactly once, since each string's second-to-last character is one specific, well-defined vowel.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="five parallel rolling counts for each vowel updated from allowed predecessor vowels at the previous length">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">length i-1: a=1,e=1,i=1,o=1,u=1</text>
    <text x="10" y="45">countA[i] = e+i+u = 1+1+1 = 3 (a follows e, i, or u)</text>
    <text x="10" y="65">countE[i] = a+i = 1+1 = 2 (e follows a or i)</text>
    <text x="10" y="85">countI[i] = e+o = 1+1 = 2 (i follows e or o)</text>
    <text x="10" y="105">countO[i] = i = 1 (o follows i only)</text>
    <text x="10" y="125">countU[i] = i+o = 1+1 = 2 (u follows i or o)</text>
    <rect x="10" y="145" width="220" height="24" fill="#3fb950"/><text x="120" y="162" fill="#0d1117" text-anchor="middle" font-size="10">sum = 3+2+2+1+2 = 10</text>
  </g>
</svg>

Each vowel's count at length `i` sums the counts of exactly the vowels ALLOWED to precede it.

## 5. Runnable example

```java
// CountVowelsPermutation.java
public class CountVowelsPermutation {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: invert "X followed by Y" rules into "Y preceded by
    // X" rules, then track 5 parallel rolling counts, one per vowel.

    static int countVowelPermutation(int n) {
        long a = 1, e = 1, i = 1, o = 1, u = 1;

        for (int len = 2; len <= n; len++) {
            long newA = (e + i + u) % MOD;
            long newE = (a + i) % MOD;
            long newI = (e + o) % MOD;
            long newO = i;
            long newU = (i + o) % MOD;
            a = newA; e = newE; i = newI; o = newO; u = newU;
        }
        return (int) ((a + e + i + o + u) % MOD);
    }

    public static void main(String[] args) {
        System.out.println(countVowelPermutation(2));
        // 10
        System.out.println(countVowelPermutation(1));
        // 5
    }
}
```

**How to run:** `java CountVowelsPermutation.java`

## 6. Walkthrough

Trace `countVowelPermutation(2)`:

| vowel | length-1 count | length-2 formula | length-2 count |
|---|---|---|---|
| a | 1 | e+i+u = 1+1+1 | 3 |
| e | 1 | a+i = 1+1 | 2 |
| i | 1 | e+o = 1+1 | 2 |
| o | 1 | i = 1 | 1 |
| u | 1 | i+o = 1+1 | 2 |

Sum: `3+2+2+1+2 = 10`, matching the expected answer. Time complexity is O(n), since each length does O(1) work across the five fixed states. Space is O(1) with rolling variables.

## 7. Gotchas & takeaways

> Gotcha: writing the transitions using the ORIGINAL "followed by" direction instead of inverting to "preceded by" is a common mistake — you must compute each vowel's NEW count from OLD counts of its ALLOWED PREDECESSORS, not its allowed successors.

- Five parallel rolling counts, updated simultaneously from OLD values (never read a just-updated new value while computing another), is the general template for small-alphabet transition-rule DP.
- Compute all NEW values from the OLD ones before overwriting any of them — updating in place one at a time would corrupt later calculations within the same length.
- Related problems: Knight Dialer (the same "small alphabet, fixed transition rule" DP, but over 10 phone-keypad digits instead of 5 vowels), Climbing Stairs (a single-state version of this same rolling-count idea).
