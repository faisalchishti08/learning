---
card: leetcode-patterns
gi: 504
slug: count-number-of-homogenous-substrings
title: Count Number of Homogenous Substrings
---

## 1. What it is

A string is "homogenous" if all its characters are the same (e.g. `"aaa"` or `"b"`). Given a string `s`, count the number of homogenous substrings (contiguous pieces of `s`), modulo `10^9 + 7`. Example: `s = "abbcccaa"` → `13`.

## 2. Why & when

Break `s` into maximal runs of the same repeated character (e.g. `"abbcccaa"` → runs `"a", "bb", "ccc", "aa"`). Every homogenous substring lives entirely inside exactly one run, so the total count is a running sum accumulated run by run — the same accumulate-as-you-scan idea as the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family, applied to counting substrings within streaks instead of summing array values. Constraints: up to 100,000 characters.

## 3. Core concept

**Key idea:** for a run of length `L` (all the same character), the number of homogenous substrings inside it is `L * (L + 1) / 2` (every contiguous choice of start and end within the run, which is always homogenous since every character in the run is identical). Scan the string once, tracking the current run's length; whenever the run breaks (a different character appears), add that run's contribution to a running total and start a new run.

**Steps:**
1. Initialize `total = 0`, `runLength = 1` (the first character starts a run of length 1).
2. Scan `s` from index `1`: if the current character equals the previous one, increment `runLength`; otherwise, add `runLength` to `total` (adding one character at a time to the running total is equivalent to accumulating `1 + 2 + ... + L` across the run — see the walkthrough), and reset `runLength = 1`.
3. A cleaner equivalent (used in the code below): at every index, whether the run continues or resets, add the *current* `runLength` to `total` — this naturally accumulates `1 + 2 + ... + L` for a run of length `L`, without needing the closed-form formula or a separate "run just ended" step.
4. Return `total mod (10^9 + 7)`.

**Why adding `runLength` at every step (not just at the end of a run) gives the right total:** the number of homogenous substrings *ending* at the current character, within its run, equals the run's length so far — a run of length `L` contributes `1 + 2 + ... + L = L(L+1)/2` in total by adding the growing `runLength` value once per character, which is exactly the definition of a running (prefix) sum over the run lengths.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each character adds its current run length to a running total of homogenous substrings">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">s = "abbcccaa"</text>
    <text x="20" y="45" fill="#8b949e">'a': runLength=1, total+=1 -&gt; total=1</text>
    <text x="20" y="65" fill="#8b949e">'b': new run, runLength=1, total+=1 -&gt; total=2</text>
    <text x="20" y="85" fill="#8b949e">'b': same run, runLength=2, total+=2 -&gt; total=4</text>
    <text x="20" y="105" fill="#8b949e">'c','c','c': runLength=1,2,3, total+=1+2+3=6 -&gt; total=10</text>
    <text x="20" y="130" fill="#8b949e">'a': new run, runLength=1, total+=1 -&gt; total=11</text>
    <text x="20" y="155" fill="#3fb950">'a': same run, runLength=2, total+=2 -&gt; total=13 (final answer)</text>
  </g>
</svg>

Each character contributes its run length so far, so a run's total contribution accumulates as `1 + 2 + ... + L`.

## 5. Runnable example

**Level 1 — Brute force.** Check every substring directly for homogeneity. O(n²).

**KEY INSIGHT:** every homogenous substring lives entirely within one maximal run of repeated characters, and a run of length `L` contains exactly `1+2+...+L` such substrings — accumulated one character at a time as a running total.

**Level 2 — Optimal.** Single pass tracking the current run length, adding it to a running total each step, O(n).

**Level 3 — Hardened.** Handles a single-character string, an already-homogenous whole string, and the required modulo arithmetic.

```java
// CountHomogenousSubstrings.java
public class CountHomogenousSubstrings {

    static final int MOD = 1_000_000_007;

    // Level 1: brute force, O(n^2)
    static int bruteForce(String s) {
        int count = 0;
        for (int i = 0; i < s.length(); i++) {
            for (int j = i; j < s.length(); j++) {
                boolean homogenous = true;
                for (int k = i + 1; k <= j; k++) {
                    if (s.charAt(k) != s.charAt(i)) { homogenous = false; break; }
                }
                if (homogenous) count++;
            }
        }
        return count % MOD;
    }

    // Level 2 & 3: running run-length total, O(n)
    static int countHomogenous(String s) {
        long total = 0;
        long runLength = 0;
        char previous = '\0';

        for (int i = 0; i < s.length(); i++) {
            char current = s.charAt(i);
            runLength = (current == previous) ? runLength + 1 : 1;
            total = (total + runLength) % MOD;
            previous = current;
        }
        return (int) total;
    }

    public static void main(String[] args) {
        System.out.println(bruteForce("abbcccaa"));   // 13
        System.out.println(countHomogenous("abbcccaa")); // 13

        System.out.println(countHomogenous("xy"));    // 2 (each single char)
        System.out.println(countHomogenous("zzzzz")); // 15 (5*6/2)
    }
}
```

**How to run:** save as `CountHomogenousSubstrings.java`, then run `java CountHomogenousSubstrings.java`.

## 6. Walkthrough

Trace `countHomogenous("abbcccaa")`:

| i | char | previous | runLength | total after |
|---|---|---|---|---|
| 0 | a | \0 | 1 | 1 |
| 1 | b | a | 1 | 2 |
| 2 | b | b | 2 | 4 |
| 3 | c | b | 1 | 5 |
| 4 | c | c | 2 | 7 |
| 5 | c | c | 3 | 10 |
| 6 | a | c | 1 | 11 |
| 7 | a | a | 2 | 13 |

Final `total = 13`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting the modulo on every addition (only applying it at the very end) can overflow `long` on very long homogenous strings — apply `% MOD` at each step, as shown in the code, to keep the running total bounded.

- Every homogenous substring lives inside exactly one maximal run; a run of length `L` contributes `1+2+...+L` substrings, accumulated naturally by adding the growing run length once per character.
- This is a running-total (prefix-sum-style) accumulation over run lengths, not over the original array values — the same "accumulate as you scan" idea applied to a different quantity.
- Time: O(n) — a single pass, O(1) work per character.
