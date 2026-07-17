---
card: leetcode-patterns
gi: 34
slug: longest-repeating-character-replacement
title: Longest Repeating Character Replacement
---

## 1. What it is

Given a string `s` of uppercase letters and an integer `k`, you may replace at most `k` characters in the string with any other uppercase letter. Return the length of the longest substring you can make consist of a single repeated letter. Example: `s = "ABAB"`, `k = 2` → answer `4` (replace both `B`s with `A`, or both `A`s with `B`).

## 2. Why & when

A window is "achievable" (turnable into all-one-letter with at most `k` replacements) exactly when `windowLength - countOfMostFrequentLetterInWindow <= k` — the characters that are *not* the majority letter are the ones you would need to replace. That is an incrementally checkable condition, which makes this a sliding window problem, tracking a frequency count per letter.

## 3. Core concept

**Key idea:** for a window to need at most `k` replacements, the count of its most frequent character must cover all but `k` of the window's length. Track the max frequency seen in any window state; if the window's length minus that max frequency exceeds `k`, shrink.

**Steps:**
1. Create a 26-slot frequency array (or map) for the window's characters. Set `left = 0`, `maxFreq = 0`, `best = 0`.
2. For each index `right` from 0 to `s.length() - 1`:
   - Increment the count for `s.charAt(right)`; update `maxFreq = max(maxFreq, count of that character)`.
   - While `(right - left + 1) - maxFreq > k`: decrement the count for `s.charAt(left)`, then `left++`.
   - Update `best = max(best, right - left + 1)`.
3. Return `best`.

**Why it is correct:** `maxFreq` is allowed to be a slight overestimate of the *current* window's true max frequency (it is never recalculated downward when the window shrinks) — but this does not cause incorrect answers, because the window only needs to shrink when it can no longer support *any* valid single-letter target of that size; once a window of a given length was found valid, the algorithm never needs to consider a strictly shorter valid window as the new best, so `best` never accidentally shrinks from a stale `maxFreq`.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Longest repeating character replacement window with max frequency tracking">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "ABAB", k = 2</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">A</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">B</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">A</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">B</text>
    <text x="20" y="95" fill="#8b949e">window "ABAB": counts A=2,B=2, maxFreq=2, length=4</text>
    <text x="20" y="118" fill="#8b949e">4 - 2 = 2 &lt;= k(2) -&gt; valid, best=4 (replace both B's, or both A's)</text>
  </g>
</svg>

The window is valid whenever the "non-majority" character count (length minus max frequency) fits within the replacement budget `k`.

## 5. Runnable example

```java
// CharacterReplacement.java
public class CharacterReplacement {

    // Level 1 -- Brute force: for every substring, count each letter's
    // frequency and check if replacements needed fit within k. O(n^2 * 26)
    // time, O(1) space -- rechecks every substring from scratch.
    static int bruteForce(String s, int k) {
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            int[] count = new int[26];
            int maxFreq = 0;
            for (int j = i; j < s.length(); j++) {
                count[s.charAt(j) - 'A']++;
                maxFreq = Math.max(maxFreq, count[s.charAt(j) - 'A']);
                int len = j - i + 1;
                if (len - maxFreq <= k) best = Math.max(best, len);
            }
        }
        return best;
    }

    // KEY INSIGHT: a window is achievable exactly when its length minus
    // its most frequent character's count fits within k -- tracking a
    // running maxFreq (even a slightly stale one) lets a single sliding
    // window find the answer without recomputing frequencies per substring.

    // Level 2 -- Optimal: sliding window with frequency array. O(n) time,
    // O(1) space (26-slot array is constant size).
    public static int characterReplacement(String s, int k) {
        int[] count = new int[26];
        int left = 0, maxFreq = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            count[s.charAt(right) - 'A']++;
            maxFreq = Math.max(maxFreq, count[s.charAt(right) - 'A']);
            while ((right - left + 1) - maxFreq > k) {
                count[s.charAt(left) - 'A']--;
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: k equal to or greater than the string's length
    // means the whole string is always achievable, since the shrink
    // condition can never trigger.
    static int hardened(String s, int k) {
        if (s == null || k < 0) throw new IllegalArgumentException("invalid input");
        return characterReplacement(s, k);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("ABAB", 2));
        System.out.println("optimal:     " + characterReplacement("ABAB", 2));
        System.out.println("large k:     " + hardened("XYZ", 10));
    }
}
```

How to run: save as `CharacterReplacement.java`, then run `java CharacterReplacement.java`.

## 6. Walkthrough

Dry run of `characterReplacement("ABAB", k = 2)`:

| right | char | count[char] | maxFreq | window length | length-maxFreq | valid? | best |
|---|---|---|---|---|---|---|---|
| 0 | A | 1 | 1 | 1 | 0 | yes (0<=2) | 1 |
| 1 | B | 1 | 1 | 2 | 1 | yes (1<=2) | 2 |
| 2 | A | 2 | 2 | 3 | 1 | yes (1<=2) | 3 |
| 3 | B | 2 | 2 | 4 | 2 | yes (2<=2) | 4 |

No shrinking was ever needed. Final answer: `4`. Time complexity: O(n). Space complexity: O(1) — the frequency array has a fixed size of 26.

## 7. Gotchas & takeaways

> Gotcha: recalculating `maxFreq` exactly (scanning the whole `count` array) every time the window shrinks would still be correct, but is unnecessary — leaving `maxFreq` as a "high-water mark" is safe and keeps the algorithm O(n) instead of O(26n).

- The formula `windowLength - maxFreq <= k` is the reusable idea: "how many characters would need to change" always equals "window size minus the size of the largest group that can stay."
- Related problems: Max Consecutive Ones III (the same formula, with the "majority" fixed as the value `1`), Fruit Into Baskets, Longest Substring with At Most K Distinct Characters.
