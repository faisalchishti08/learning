---
card: leetcode-patterns
gi: 309
slug: restore-ip-addresses
title: Restore IP Addresses
---

## 1. What it is

Given a string `s` containing only digits, return every possible valid IP address that can be formed by inserting exactly 3 dots into `s`. A valid IP address has 4 parts, each an integer from `0` to `255`, with NO leading zeros (except the single digit `"0"` itself). Example: `s = "25525511135"` → `["255.255.11.135","255.255.111.35"]`.

## 2. Why & when

This is a string-partitioning backtracking problem: decide where each of the 4 segments ends, checking validity (range `0`–`255`, no leading zero) as each segment is chosen. Use this shape whenever a problem must split a string into a fixed number of parts, each satisfying its own local validity rule.

## 3. Core concept

**Key idea:** try every possible length (1, 2, or 3 digits) for the CURRENT segment, validate it, and recurse to place the remaining segments in the rest of the string.

**Steps:**
1. Define `backtrack(startIndex, segmentsPlaced, currentParts)`.
2. **Base case:** if `segmentsPlaced == 4`: if `startIndex == s.length()` (the whole string was consumed exactly), join `currentParts` with dots and record it; either way, return.
3. **Prune:** if `startIndex == s.length()` (ran out of string too early) or `4 - segmentsPlaced` segments cannot possibly fit in the remaining characters, stop.
4. **Loop:** for `length` from `1` to `3`: if `startIndex + length > s.length()`, stop the loop (segment would run past the string). Extract `segment = s.substring(startIndex, startIndex + length)`. If `segment` has a leading zero with length `> 1`, or its numeric value exceeds `255`, skip it (prune). Otherwise, choose `segment`, recurse, then un-choose.

**Why it is correct:** trying every length from 1 to 3 covers every possible way to split off the next segment, since a valid IP segment is never longer than 3 digits (`255` is the maximum). The two validity checks (leading zero, value `> 255`) exactly match the problem's definition of a valid segment, so any segment that fails either check can never be part of a valid final address, and pruning it early avoids wasted recursive work.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Trying segment lengths 1, 2, and 3 at each step, validating range and leading zeros, to split the digit string into 4 valid IP parts">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "25525511135"</text>
    <text x="10" y="45">segment 1: try "2" ✓, "25" ✓, "255" ✓ -&gt; branch on each</text>
    <text x="10" y="65">following "255": segment 2: try "2" ✓, "25" ✓, "255" ✓</text>
    <text x="10" y="85">following "255.255": segment 3: try "1" ✓, "11" ✓, "113" ✗ (only 2 chars remain for seg 4 if "113"?)</text>
    <text x="10" y="105">segment 4: remaining digits must fill exactly, check leading zero and range</text>
    <rect x="10" y="120" width="230" height="24" fill="#3fb950"/><text x="125" y="137" fill="#0d1117" text-anchor="middle" font-size="10">"255.255.11.135" is one valid result</text>
  </g>
</svg>

Each segment tries lengths 1 through 3, validated against the leading-zero and 0–255 range rules, before recursing to place the rest.

## 5. Runnable example

```java
// RestoreIPAddresses.java
import java.util.*;

public class RestoreIPAddresses {

    // KEY INSIGHT: a valid IP segment is at most 3 digits, so trying
    // lengths 1, 2, 3 at each step covers every possibility; checking
    // leading-zero and range rules immediately prunes invalid
    // segments before recursing further.

    static List<String> restoreIpAddresses(String s) {
        List<String> results = new ArrayList<>();
        backtrack(s, 0, new ArrayList<>(), results);
        return results;
    }

    static void backtrack(String s, int start, List<String> parts, List<String> results) {
        if (parts.size() == 4) {
            if (start == s.length()) {
                results.add(String.join(".", parts));
            }
            return;
        }

        for (int length = 1; length <= 3 && start + length <= s.length(); length++) {
            String segment = s.substring(start, start + length);
            if (!isValidSegment(segment)) continue; // prune

            parts.add(segment);                       // choose
            backtrack(s, start + length, parts, results); // recurse
            parts.remove(parts.size() - 1);            // un-choose
        }
    }

    static boolean isValidSegment(String segment) {
        if (segment.length() > 1 && segment.charAt(0) == '0') return false; // leading zero
        int value = Integer.parseInt(segment);
        return value <= 255;
    }

    public static void main(String[] args) {
        System.out.println(restoreIpAddresses("25525511135"));
        // [255.255.11.135, 255.255.111.35]
        System.out.println(restoreIpAddresses("0000"));
        // [0.0.0.0]
    }
}
```

**How to run:** `java RestoreIPAddresses.java`

## 6. Walkthrough

Trace one successful path for `restoreIpAddresses("25525511135")`:

| segmentsPlaced | start | length tried | segment | valid? | parts after |
|---|---|---|---|---|---|
| 0 | 0 | 3 | "255" | yes | [255] |
| 1 | 3 | 3 | "255" | yes | [255, 255] |
| 2 | 6 | 2 | "11" | yes | [255, 255, 11] |
| 3 | 8 | 3 | "135" | yes | [255, 255, 11, 135] |
| 4 | 11 | — | start == s.length() (11) | record "255.255.11.135" | — |

The search also finds `"255.255.111.35"` via a different length-3-then-2 split at the third segment. Time complexity is O(1) in the loose sense — the search space is bounded by `3^4 = 81` possible segment-length combinations, regardless of input size, since the string can contain at most 12 digits for any valid IP. Space is O(1) beyond the output, for the same reason.

## 7. Gotchas & takeaways

> Gotcha: the leading-zero check must apply to segments LONGER than 1 character — `"0"` alone is a perfectly valid segment, but `"00"`, `"01"`, or `"012"` are not, since a multi-digit segment starting with `'0'` is never a valid non-negative integer representation without a leading zero.

- Bounding the segment length to `1..3` (never trying longer) is itself a form of pruning, derived directly from the problem's own constraint that no valid segment exceeds `255`.
- The base case's extra check (`start == s.length()`) is essential — without it, a search that reaches 4 segments but has NOT consumed the whole string would incorrectly record a partial address.
- Related problems: Word Break (a similar string-partitioning backtracking idea, checking dictionary membership instead of numeric range), Palindrome Partitioning (partitioning a string where each piece must satisfy a different local rule).
