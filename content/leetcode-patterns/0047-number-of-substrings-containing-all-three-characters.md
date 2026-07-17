---
card: leetcode-patterns
gi: 47
slug: number-of-substrings-containing-all-three-characters
title: Number of Substrings Containing All Three Characters
---

## 1. What it is

Given a string `s` consisting only of characters `'a'`, `'b'`, and `'c'`, return the number of substrings that contain at least one occurrence of all three characters. Example: `s = "abcabc"` → answer `10`.

## 2. Why & when

"At least one of each" is a **minimum-window-style** condition — once a window contains all three characters, every longer extension to the right (with the same or later left boundary) also contains all three. That monotonic "once valid, stays valid as it grows" property, combined with counting rather than just finding the shortest, is what makes this a sliding-window counting problem, similar in spirit to Minimum Size Subarray Sum but adapted to count rather than minimize.

## 3. Core concept

**Key idea:** for a fixed `right`, find the largest possible `left` such that the window `[left, right]` still contains all three characters. Every smaller `left` (moving further left) also keeps the window valid, so every starting position from `0` to that boundary contributes a valid substring ending at `right`.

**Steps:**
1. Track the last-seen index of each of `'a'`, `'b'`, `'c'` (initialize to `-1`).
2. Set `count = 0`.
3. For each index `right` from 0 to `length - 1`:
   - Update the last-seen index for `s.charAt(right)`.
   - If all three last-seen indices are `>= 0` (all three characters have appeared at least once so far), the number of valid substrings ending at `right` is `min(lastA, lastB, lastC) + 1` — every start from `0` up to that minimum last-seen index keeps all three characters in range.
   - Add that amount to `count`.
4. Return `count`.

**Why it is correct:** a substring `[start, right]` contains all three characters exactly when `start` is at or before every character's most recent occurrence — equivalently, `start <= min(lastA, lastB, lastC)`. There are exactly `min(lastA, lastB, lastC) + 1` such valid starting positions (from `0` through that minimum, inclusive), so summing this count for every `right` gives the total number of valid substrings, without enumerating them individually.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Number of substrings with all three characters using last seen indices">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "abcabc"</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">c</text>
    <text x="20" y="95" fill="#8b949e">right=2 'c': lastA=0, lastB=1, lastC=2 -&gt; min=0</text>
    <text x="20" y="118" fill="#8b949e">valid starts: only index 0 -&gt; count += 1 ("abc")</text>
  </g>
</svg>

Once all three characters have appeared, `min(lastA, lastB, lastC) + 1` counts every valid starting position for the current `right`, all at once.

## 5. Runnable example

```java
// SubstringsAllThreeChars.java
public class SubstringsAllThreeChars {

    // Level 1 -- Brute force: check every substring for containing all
    // three characters directly. O(n^2) time, O(1) space.
    static int bruteForce(String s) {
        int count = 0;
        for (int i = 0; i < s.length(); i++) {
            boolean[] seen = new boolean[3];
            for (int j = i; j < s.length(); j++) {
                seen[s.charAt(j) - 'a'] = true;
                if (seen[0] && seen[1] && seen[2]) count++;
            }
        }
        return count;
    }

    // KEY INSIGHT: tracking the LAST SEEN index of each character lets you
    // count every valid starting position for the current right endpoint
    // in O(1), instead of checking each candidate start individually.

    // Level 2 -- Optimal: last-seen-index tracking. O(n) time, O(1) space.
    public static int numberOfSubstrings(String s) {
        int[] lastSeen = { -1, -1, -1 };
        int count = 0;
        for (int right = 0; right < s.length(); right++) {
            lastSeen[s.charAt(right) - 'a'] = right;
            if (lastSeen[0] >= 0 && lastSeen[1] >= 0 && lastSeen[2] >= 0) {
                count += Math.min(lastSeen[0], Math.min(lastSeen[1], lastSeen[2])) + 1;
            }
        }
        return count;
    }

    // Level 3 -- Hardened: a string missing one of the three characters
    // entirely returns 0, since the "all three seen" condition never
    // becomes true.
    static int hardened(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        return numberOfSubstrings(s);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("abcabc"));
        System.out.println("optimal:     " + numberOfSubstrings("abcabc"));
        System.out.println("missing 'c': " + hardened("aabb"));
    }
}
```

How to run: save as `SubstringsAllThreeChars.java`, then run `java SubstringsAllThreeChars.java`.

## 6. Walkthrough

Dry run of `numberOfSubstrings("abcabc")`:

| right | char | lastA | lastB | lastC | all seen? | min+1 | count |
|---|---|---|---|---|---|---|---|
| 0 | a | 0 | -1 | -1 | no | — | 0 |
| 1 | b | 0 | 1 | -1 | no | — | 0 |
| 2 | c | 0 | 1 | 2 | yes | 0+1=1 | 1 |
| 3 | a | 3 | 1 | 2 | yes | 1+1=2 | 3 |
| 4 | b | 3 | 4 | 2 | yes | 2+1=3 | 6 |
| 5 | c | 3 | 4 | 5 | yes | 3+1=4 | 10 |

Final answer: `10`. Time complexity: O(n). Space complexity: O(1) — only 3 last-seen indices tracked.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `+ 1` when computing valid starts (using `min(...)` alone instead of `min(...) + 1`) undercounts by one for every valid `right`, since indices are 0-based and the minimum last-seen index itself is a valid starting position.

- The "last seen index" state is the same idea used in Longest Substring Without Repeating Characters — tracking just enough per-character metadata to answer a positional question in O(1), rather than rescanning.
- Related problems: Longest Substring Without Repeating Characters, Minimum Window Substring, Count Number of Nice Subarrays.
