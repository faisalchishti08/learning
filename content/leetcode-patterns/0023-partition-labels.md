---
card: leetcode-patterns
gi: 23
slug: partition-labels
title: Partition Labels
---

## 1. What it is

Given a string `s`, partition it into as many parts as possible so that each letter appears in at most one part, and return the list of part lengths. Example: `s = "ababcbacadefegdehijhklij"` → `[9, 7, 8]`, meaning the string splits into three chunks where no letter crosses a chunk boundary.

## 2. Why & when

Each part must extend far enough to include every occurrence of every letter inside it. That "extend the boundary until it is safe to cut" behavior is a same-direction two-pointer scan, using each letter's *last occurrence index* as the signal for how far the current part must reach.

## 3. Core concept

**Key idea:** precompute the last index at which each letter appears anywhere in `s`. Then scan left to right, growing the current part's end to the maximum last-index seen so far among letters already included; when the scan position reaches that end, the part is complete.

**Steps:**
1. Build a `lastIndex` map (or a 26-slot array): for each letter, its last position in `s`.
2. Set `start = 0` (start of the current part), `end = 0` (the farthest the current part must reach).
3. For each index `i` from 0 to `s.length() - 1`:
   - Update `end = max(end, lastIndex[s.charAt(i)])`.
   - If `i == end`, the current part is complete — record its length (`end - start + 1`), then set `start = i + 1` for the next part.
4. Return the recorded lengths.

**Why it is correct:** `end` always reflects the furthest any letter *already included* needs the part to extend. Once the scan pointer `i` catches up to `end` without `end` growing further, every letter seen so far has had its last occurrence included — it is safe to cut, because no letter in this part reappears later.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Partition labels growing window until safe to cut">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "a b a c b"  (last 'a'=2, 'b'=4, 'c'=3)</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="180" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">c</text>
    <text x="200" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="20" y="95" fill="#8b949e">i=0 'a': end=max(0,2)=2</text>
    <text x="20" y="118" fill="#8b949e">i=1 'b': end=max(2,4)=4; i=2 'a': end stays 4; i=3 'c': end=max(4,3)=4</text>
    <text x="20" y="141" fill="#8b949e">i=4 'b': end=4, i==end -&gt; cut here, length 5</text>
  </g>
</svg>

`end` tracks the furthest boundary any included letter demands; the part closes exactly when the scan catches up to it.

## 5. Runnable example

```java
// PartitionLabels.java
import java.util.ArrayList;
import java.util.List;

public class PartitionLabels {

    // Level 1 -- Brute force: for each starting position, repeatedly scan
    // the current window to find the max last-occurrence of any letter
    // inside it, re-scanning the window every time it grows. O(n^2) worst
    // case, since a window can be rescanned many times as it grows.
    static List<Integer> bruteForce(String s) {
        int[] last = new int[26];
        for (int i = 0; i < s.length(); i++) last[s.charAt(i) - 'a'] = i;

        List<Integer> result = new ArrayList<>();
        int start = 0;
        while (start < s.length()) {
            int end = last[s.charAt(start) - 'a'];
            int i = start;
            while (i <= end) {
                end = Math.max(end, last[s.charAt(i) - 'a']);
                i++;
            }
            result.add(end - start + 1);
            start = end + 1;
        }
        return result;
    }

    // KEY INSIGHT: a single forward pass can track the growing boundary
    // directly -- once the scan pointer reaches that boundary, the part is
    // guaranteed complete, so no re-scanning is needed.

    // Level 2 -- Optimal: one pass, tracking end as you go. O(n) time,
    // O(1) space beyond the 26-slot last-index table and the output list.
    public static List<Integer> partitionLabels(String s) {
        int[] last = new int[26];
        for (int i = 0; i < s.length(); i++) {
            last[s.charAt(i) - 'a'] = i;
        }

        List<Integer> result = new ArrayList<>();
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            end = Math.max(end, last[s.charAt(i) - 'a']);
            if (i == end) {
                result.add(end - start + 1);
                start = i + 1;
            }
        }
        return result;
    }

    // Level 3 -- Hardened: a string where every letter is unique produces
    // one part per character, and a string that is all one repeated
    // letter produces a single part covering the whole string -- both
    // fall out of the same loop with no special casing.
    static List<Integer> hardened(String s) {
        if (s == null || s.isEmpty()) return new ArrayList<>();
        return partitionLabels(s);
    }

    public static void main(String[] args) {
        String s = "ababcbacadefegdehijhklij";
        System.out.println("optimal: " + partitionLabels(s));
        System.out.println("all unique: " + hardened("abcde"));
        System.out.println("all same:   " + hardened("aaaa"));
    }
}
```

How to run: save as `PartitionLabels.java`, then run `java PartitionLabels.java`.

## 6. Walkthrough

Dry run of `partitionLabels("ababcbaca")` (a shortened prefix; last occurrences: `a`→6, `b`→5, `c`→8):

| i | s[i] | last[s[i]] | end after update | i == end? | action |
|---|---|---|---|---|---|
| 0 | a | 6 | 6 | no | — |
| 1 | b | 5 | 6 | no | — |
| 2 | a | 6 | 6 | no | — |
| 3 | b | 5 | 6 | no | — |
| 4 | c | 8 | 8 | no | — |
| 5 | b | 5 | 8 | no | — |
| 6 | a | 6 | 8 | no | — |
| 7 | c | 8 | 8 | no | — |
| 8 | a | 6 | 8 | yes | record length = end - start + 1 = 8 - 0 + 1 = 9 |

Result for this prefix: one part of length 9 covering the whole string, since `c`'s last occurrence at index 8 forces the boundary all the way to the end. Time complexity: O(n): one pass to build `last`, one pass to scan. Space complexity: O(1) beyond the fixed 26-slot table.

## 7. Gotchas & takeaways

> Gotcha: checking `i == end` before updating `end` on the current character gives the wrong answer — you must update `end` with the current character's last occurrence *first*, then check whether the scan has caught up.

- This pattern — "extend a boundary based on a lookahead table, cut when the scan catches up" — also solves interval-merging-style problems.
- Related problems: Merge Intervals, Video Stitching, Non-overlapping Intervals.
