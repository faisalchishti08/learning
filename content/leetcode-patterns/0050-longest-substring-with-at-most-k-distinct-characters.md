---
card: leetcode-patterns
gi: 50
slug: longest-substring-with-at-most-k-distinct-characters
title: Longest Substring with At Most K Distinct Characters
---

## 1. What it is

Given a string `s` and an integer `k`, return the length of the longest substring that contains at most `k` distinct characters. Example: `s = "eceba"`, `k = 2` → answer `3`, from the substring `"ece"`.

## 2. Why & when

This is the general-purpose version of the "at most k distinct" sliding window — Fruit Into Baskets is this exact problem with `k` fixed at `2` and fruit types standing in for characters. Recognizing the reduction means you can solve either problem with the same code.

## 3. Core concept

**Key idea:** track a frequency map of characters in the current window; the map's key count is exactly the number of distinct characters. Expand `right`; whenever the distinct count exceeds `k`, shrink `left` until it no longer does.

**Steps:**
1. Create an empty map `count`. Set `left = 0`, `best = 0`.
2. For each index `right` from 0 to `s.length() - 1`:
   - Increment `count[s.charAt(right)]`.
   - While `count.size() > k`: decrement `count[s.charAt(left)]`; if it reaches `0`, remove the key; then `left++`.
   - Update `best = max(best, right - left + 1)`.
3. Return `best`.

**Why it is correct:** `count.size()` always equals the number of distinct characters currently in the window, since every character present has a positive count and every absent character has been fully removed. Shrinking exactly when that size exceeds `k` maintains the invariant "the window has at most `k` distinct characters" at every point where `best` is updated.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Longest substring at most k distinct characters">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "eceba", k = 2</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">e</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">c</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">e</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="20" y="95" fill="#8b949e">window "ece": count={e:2,c:1}, size 2 &lt;= k -&gt; valid, length 3</text>
    <text x="20" y="118" fill="#8b949e">adding 'b' makes size 3 &gt; k -&gt; shrink until back to 2 distinct</text>
  </g>
</svg>

The map's size directly tracks the window's distinct-character count against the budget `k`.

## 5. Runnable example

```java
// LongestSubstringKDistinct.java
import java.util.HashMap;
import java.util.Map;

public class LongestSubstringKDistinct {

    // Level 1 -- Brute force: for every window start, expand right while
    // counting distinct characters with a HashSet, stopping once it
    // exceeds k. O(n^2) time, O(1) space.
    static int bruteForce(String s, int k) {
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            java.util.Set<Character> seen = new java.util.HashSet<>();
            int j = i;
            while (j < s.length()) {
                seen.add(s.charAt(j));
                if (seen.size() > k) break;
                j++;
            }
            best = Math.max(best, j - i);
        }
        return best;
    }

    // KEY INSIGHT: this is the general "at most k distinct" sliding window
    // -- the same shape as Fruit Into Baskets with k=2, generalized to any
    // k, tracked with a frequency map's key count.

    // Level 2 -- Optimal: sliding window with a frequency map. O(n) time,
    // O(k) space.
    public static int lengthOfLongestSubstringKDistinct(String s, int k) {
        Map<Character, Integer> count = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            count.merge(s.charAt(right), 1, Integer::sum);
            while (count.size() > k) {
                char c = s.charAt(left);
                count.merge(c, -1, Integer::sum);
                if (count.get(c) == 0) count.remove(c);
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: k == 0 correctly returns 0 -- the moment any
    // character is added, count.size() becomes 1, which is already > 0,
    // so the shrink loop empties the window right back down before best
    // is ever updated with a positive length.
    static int hardened(String s, int k) {
        if (s == null || k < 0) throw new IllegalArgumentException("invalid input");
        return lengthOfLongestSubstringKDistinct(s, k);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("eceba", 2));
        System.out.println("optimal:     " + lengthOfLongestSubstringKDistinct("eceba", 2));
        System.out.println("k == 0:      " + hardened("abc", 0));
    }
}
```

How to run: save as `LongestSubstringKDistinct.java`, then run `java LongestSubstringKDistinct.java`.

## 6. Walkthrough

Dry run of `lengthOfLongestSubstringKDistinct("eceba", k = 2)`:

| right | char | count map | size | shrink? | window | best |
|---|---|---|---|---|---|---|
| 0 | e | {e:1} | 1 | no | [0,0] | 1 |
| 1 | c | {e:1,c:1} | 2 | no | [0,1] | 2 |
| 2 | e | {e:2,c:1} | 2 | no | [0,2] | 3 |
| 3 | b | {e:2,c:1,b:1} | 3 | yes: remove s[0]='e' -> {e:1,c:1,b:1}, left=1 | [1,3] | 3 |
| 4 | a | {e:1,c:1,b:1,a:1} | 4 | yes: remove s[1]='c' -> {e:1,b:1,a:1}, left=2; still size 3 -> remove s[2]='e', count reaches 0, removed -> {b:1,a:1}, left=3 | [3,4] | 3 |

Final answer: `3`, from the window `"ece"`. Time complexity: O(n). Space complexity: O(k).

## 7. Gotchas & takeaways

> Gotcha: the `k == 0` edge case needs care — a window can never satisfy "at most 0 distinct characters" while containing anything, so the shrink loop must be able to push `left` past `right` entirely; make sure the loop condition (`right - left + 1`) does not compute a negative or nonsensical length in that state.

- This is the general template that Fruit Into Baskets specializes; solving one solves both.
- Related problems: Fruit Into Baskets, Longest Substring Without Repeating Characters (the special case `k` equals the alphabet size, or equivalently "no repeats" phrased differently), Subarrays with K Different Integers (the "exactly k" counting version, using the atMost(k) − atMost(k−1) trick).
