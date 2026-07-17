---
card: leetcode-patterns
gi: 48
slug: minimum-window-substring
title: Minimum Window Substring
---

## 1. What it is

Given two strings `s` and `t`, return the shortest substring of `s` that contains every character of `t`, including duplicates (if `t` has two `'a'`s, the substring must have at least two `'a'`s). Return an empty string if no such substring exists. Example: `s = "ADOBECODEBANC"`, `t = "ABC"` → answer `"BANC"`.

## 2. Why & when

"Shortest substring containing all characters (with duplicate counts) of another string" is the shortest-window sliding-window template, using a frequency map for the "need" condition — the hardest and most general version of the "shortest window" problems in this section, combining the counting-based validity check from Permutation in String with the shrink-while-valid mechanics of Minimum Size Subarray Sum.

## 3. Core concept

**Key idea:** track how many characters of `t` are still "missing" from the current window. Expand `right` until nothing is missing (the window is valid); then shrink `left` as much as possible while it stays valid, recording the shortest length found.

**Steps:**
1. Build a frequency map `need` for `t`. Set `missing = t.length()` (how many more characters, counting duplicates, the window still needs).
2. Set `left = 0`, `bestStart = -1`, `bestLen = Integer.MAX_VALUE`.
3. For each index `right` from 0 to `s.length() - 1`:
   - Let `c = s.charAt(right)`. If `need.get(c) > 0` (still needed), decrement `missing`. Decrement `need.get(c)` regardless (it can go negative, tracking a surplus).
   - While `missing == 0` (window is valid): if `right - left + 1 < bestLen`, update `bestStart` and `bestLen`. Then try to shrink: let `d = s.charAt(left)`; increment `need.get(d)`; if that brings `need.get(d)` above `0`, it means `d` was actually needed, so increment `missing` (the window is about to become invalid); `left++`.
4. Return the substring `[bestStart, bestStart + bestLen)`, or `""` if `bestStart` stayed `-1`.

**Why it is correct:** `missing` tracks exactly how many more required characters (with multiplicity) the window still lacks; it reaches `0` exactly when the window is a valid superset of `t`'s multiset of characters. The `need` map going negative for characters beyond what `t` requires (a "surplus") correctly distinguishes removing a surplus character (harmless) from removing a character the window still needs (which must increment `missing` back up, since removing it would make the window invalid).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Minimum window substring tracking missing character count">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "ADOBECODEBANC", t = "ABC" (need: A=1,B=1,C=1)</text>
    <text x="20" y="55" fill="#8b949e">expand right until missing==0: window "ADOBEC" contains A,B,C -&gt; valid, length 6</text>
    <text x="20" y="80" fill="#79c0ff">shrink left: drop 'A' (needed) -&gt; missing becomes 1, window invalid, stop shrink</text>
    <text x="20" y="105" fill="#8b949e">continue expanding right; eventually window "BANC" is found, length 4, better</text>
  </g>
</svg>

`missing` counts required characters not yet covered; the window is valid exactly when it reaches zero, and the shrink loop finds the tightest valid boundary.

## 5. Runnable example

```java
// MinimumWindowSubstring.java
import java.util.HashMap;
import java.util.Map;

public class MinimumWindowSubstring {

    // Level 1 -- Brute force: check every substring for containing all
    // of t's characters (with multiplicity) directly. O(n^2 * |t|) time.
    static String bruteForce(String s, String t) {
        int bestStart = -1, bestLen = Integer.MAX_VALUE;
        for (int i = 0; i < s.length(); i++) {
            for (int j = i; j < s.length(); j++) {
                if (contains(s.substring(i, j + 1), t)) {
                    if (j - i + 1 < bestLen) { bestLen = j - i + 1; bestStart = i; }
                    break;
                }
            }
        }
        return bestStart == -1 ? "" : s.substring(bestStart, bestStart + bestLen);
    }

    private static boolean contains(String window, String t) {
        Map<Character, Integer> need = new HashMap<>();
        for (char c : t.toCharArray()) need.merge(c, 1, Integer::sum);
        for (char c : window.toCharArray()) {
            if (need.containsKey(c)) need.merge(c, -1, Integer::sum);
        }
        for (int v : need.values()) if (v > 0) return false;
        return true;
    }

    // KEY INSIGHT: tracking a single "missing" counter (not just the need
    // map) lets you check window validity in O(1), instead of scanning the
    // whole need map after every character -- that is what keeps the
    // shrink-while-valid loop linear overall.

    // Level 2 -- Optimal: sliding window with a missing-count tracker.
    // O(n + m) time, O(m) space (m = distinct characters in t).
    public static String minWindow(String s, String t) {
        Map<Character, Integer> need = new HashMap<>();
        for (char c : t.toCharArray()) need.merge(c, 1, Integer::sum);

        int missing = t.length();
        int left = 0, bestStart = -1, bestLen = Integer.MAX_VALUE;

        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (need.getOrDefault(c, 0) > 0) missing--;
            need.merge(c, -1, Integer::sum);

            while (missing == 0) {
                if (right - left + 1 < bestLen) {
                    bestLen = right - left + 1;
                    bestStart = left;
                }
                char d = s.charAt(left);
                need.merge(d, 1, Integer::sum);
                if (need.get(d) > 0) missing++;
                left++;
            }
        }
        return bestStart == -1 ? "" : s.substring(bestStart, bestStart + bestLen);
    }

    // Level 3 -- Hardened: t longer than s, or t containing a character
    // not present in s at all, both correctly result in missing never
    // reaching 0, so the method returns "".
    static String hardened(String s, String t) {
        if (s == null || t == null) throw new IllegalArgumentException("inputs must not be null");
        return minWindow(s, t);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("ADOBECODEBANC", "ABC"));
        System.out.println("optimal:     " + minWindow("ADOBECODEBANC", "ABC"));
        System.out.println("impossible:  \"" + hardened("a", "aa") + "\"");
    }
}
```

How to run: save as `MinimumWindowSubstring.java`, then run `java MinimumWindowSubstring.java`.

## 6. Walkthrough

Dry run of `minWindow("ADOBECODEBANC", "ABC")` (`need` starts `{A:1, B:1, C:1}`, `missing = 3`):

1. `right` expands through `"ADOBEC"` (indices 0-5): `A`, `B`, `C` are each seen once, decrementing `missing` to `0` by the time `right = 5`. Window `[0, 5]` is valid, length `6`. Record `bestStart=0, bestLen=6`.
2. Shrink: `left=0`, character `'A'`. Its `need` count was exactly `0` (satisfied, no surplus); incrementing it back to `1` means `A` is needed again, so `missing` becomes `1`. `left` moves to `1`, and the shrink loop exits, since the window is now invalid.
3. `right` continues expanding through `"ODEB"` (indices 6-9) without finding all three again yet, since `A` is missing.
4. At `right = 10` (`'A'` in `"BANC"`), `missing` returns to `0`. Window `[1, 10]` = `"DOBECODEBA"` is valid but length `10` — worse than the current best of `6`, so shrinking begins.
5. Shrinking from `left=1` through several non-essential characters eventually reaches `left=9`, window `[9, 12]` = `"BANC"`, length `4` — the new best.
6. No shorter valid window is found afterward. Final answer: `"BANC"`.

Time complexity: O(n + m), where n = `s.length()`, m = `t.length()` — each character of `s` is visited by `right` once and by `left` at most once. Space complexity: O(m), for the `need` map.

## 7. Gotchas & takeaways

> Gotcha: using `need.containsKey(c)` alone (instead of checking `need.getOrDefault(c, 0) > 0`) to decide whether to decrement `missing` double-counts characters that already have a surplus in the window — only decrement `missing` when the character was still genuinely needed at that moment.

- This is the hardest sliding-window shape in this section because it combines a multi-character frequency condition (like Permutation in String) with the shortest-window shrink logic (like Minimum Size Subarray Sum) — recognizing both halves separately makes the combination tractable.
- Related problems: Permutation in String, Find All Anagrams in a String, Substring with Concatenation of All Words.
