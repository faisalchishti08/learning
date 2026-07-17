---
card: leetcode-patterns
gi: 33
slug: longest-substring-without-repeating-characters
title: Longest Substring Without Repeating Characters
---

## 1. What it is

Given a string `s`, find the length of the longest substring without repeating characters. Example: `s = "abcabcbb"` → the answer is `3`, from the substring `"abc"`.

## 2. Why & when

"Longest substring" plus "without repeating characters" is the textbook variable-size sliding window: the window is valid exactly when it contains no duplicate characters, and that condition can be checked incrementally with a set or a last-seen-index map.

## 3. Core concept

**Key idea:** track the last index at which each character was seen. When you encounter a character already in the current window, jump `left` directly past its previous occurrence — no need to shrink one step at a time.

**Steps:**
1. Create a map `lastSeen` from character to its most recent index.
2. Set `left = 0`, `best = 0`.
3. For each index `right` from 0 to `s.length() - 1`:
   - If `s.charAt(right)` is in `lastSeen` **and** `lastSeen.get(s.charAt(right)) >= left` (its previous occurrence is inside the current window), move `left` to `lastSeen.get(s.charAt(right)) + 1`.
   - Update `lastSeen.put(s.charAt(right), right)`.
   - Update `best = max(best, right - left + 1)`.
4. Return `best`.

**Why it is correct:** the condition `lastSeen.get(c) >= left` checks whether the earlier occurrence is still *inside* the window — if it is outside (before `left`), it is irrelevant and `left` should not move. Jumping `left` directly to `lastSeen.get(c) + 1`, instead of shrinking one character at a time, skips straight past the duplicate without re-checking characters you already know are fine, still giving O(n) time.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Longest substring without repeats jumping left past a duplicate">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "abcabcbb"</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">c</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="20" y="95" fill="#8b949e">right=3 'a': lastSeen['a']=0 &gt;= left(0) -&gt; left jumps to 1</text>
    <text x="20" y="118" fill="#8b949e">window becomes [1,3]="bca", length 3</text>
  </g>
</svg>

Instead of shrinking one step at a time, `left` jumps directly past the duplicate's last known position.

## 5. Runnable example

```java
// LongestSubstringNoRepeat.java
import java.util.HashMap;
import java.util.Map;

public class LongestSubstringNoRepeat {

    // Level 1 -- Brute force: check every substring for repeated
    // characters using a HashSet. O(n^3) time (O(n^2) substrings, O(n) to
    // check each), O(n) space.
    static int bruteForce(String s) {
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            for (int j = i; j < s.length(); j++) {
                if (hasNoRepeats(s, i, j)) {
                    best = Math.max(best, j - i + 1);
                }
            }
        }
        return best;
    }

    private static boolean hasNoRepeats(String s, int i, int j) {
        java.util.Set<Character> seen = new java.util.HashSet<>();
        for (int k = i; k <= j; k++) {
            if (!seen.add(s.charAt(k))) return false;
        }
        return true;
    }

    // KEY INSIGHT: tracking each character's LAST SEEN index lets left
    // jump directly past a duplicate in one step, instead of shrinking the
    // window character by character.

    // Level 2 -- Optimal: sliding window with last-seen-index map. O(n)
    // time, O(min(n, alphabet size)) space.
    public static int lengthOfLongestSubstring(String s) {
        Map<Character, Integer> lastSeen = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (lastSeen.containsKey(c) && lastSeen.get(c) >= left) {
                left = lastSeen.get(c) + 1;
            }
            lastSeen.put(c, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: an empty string returns 0 (the loop never
    // runs); a string with all identical characters correctly returns 1.
    static int hardened(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        return lengthOfLongestSubstring(s);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("abcabcbb"));
        System.out.println("optimal:     " + lengthOfLongestSubstring("abcabcbb"));
        System.out.println("all same:    " + hardened("bbbb"));
    }
}
```

How to run: save as `LongestSubstringNoRepeat.java`, then run `java LongestSubstringNoRepeat.java`.

## 6. Walkthrough

Dry run of `lengthOfLongestSubstring("abcabcbb")`:

| right | char | lastSeen before | left after | window | best |
|---|---|---|---|---|---|
| 0 | a | {} | 0 | "a" | 1 |
| 1 | b | {a:0} | 0 | "ab" | 2 |
| 2 | c | {a:0,b:1} | 0 | "abc" | 3 |
| 3 | a | {a:0,b:1,c:2} | 1 (jump past a@0) | "bca" | 3 |
| 4 | b | {a:3,b:1,c:2} | 2 (jump past b@1) | "cab" | 3 |
| 5 | c | {a:3,b:4,c:2} | 3 (jump past c@2) | "abc" | 3 |
| 6 | b | {a:3,b:4,c:5} | 5 (jump past b@4) | "cb" | 3 |
| 7 | b | {a:3,b:6,c:5} | 7 (jump past b@6) | "b" | 3 |

Final answer: `3`. Time complexity: O(n), each character visited once by `right`, `left` only ever moves forward. Space complexity: O(min(n, alphabet size)).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `lastSeen.get(c) >= left` check — using only `lastSeen.containsKey(c)` — can move `left` *backward*, since a character's last-seen index might be from before the current window even started. Always confirm the stale occurrence is still inside the window before jumping.

- This "jump left directly" optimization is what separates an O(n) solution from an O(n) solution that still shrinks one step at a time (both are technically O(n), but the direct jump avoids redundant work in the common case).
- Related problems: Longest Substring with At Most Two Distinct Characters, Longest Repeating Character Replacement, Find All Anagrams in a String.
