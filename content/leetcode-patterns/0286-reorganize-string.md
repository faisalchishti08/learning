---
card: leetcode-patterns
gi: 286
slug: reorganize-string
title: Reorganize String
---

## 1. What it is

Given a string `s`, rearrange its characters so that no two adjacent characters are the same, and return any such rearrangement. If no valid rearrangement exists, return an empty string. Example: `s = "aab"` → `"aba"`.

## 2. Why & when

This problem always places the CURRENTLY most frequent remaining character next, using a max-heap keyed by frequency — the same size-k-heap mechanics as Task Scheduler, but greedily building a string instead of a time-slotted schedule. Use this shape whenever a problem must interleave items so that no two identical items sit next to each other.

## 3. Core concept

**Key idea:** repeatedly take the two characters with the highest remaining counts from a max-heap, append one, then the other, to guarantee no two identical characters land next to each other.

**Steps:**
1. Count each character's frequency. If any character's frequency exceeds `(s.length() + 1) / 2`, no valid rearrangement exists — return `""` immediately (that character alone cannot be spaced out enough).
2. Push every `(character, count)` pair into a max-heap ordered by count.
3. While the heap has at least two entries: pop the two most frequent, append both to the result, decrement each count, and push back any that still have a positive count.
4. If exactly one entry remains with count `1`, append it (it is safe alone, since it will not have an identical neighbor before it).

**Why it is correct:** always placing the two currently-most-frequent characters together in each round guarantees the most "dangerous" (most repeated) characters get spaced out earliest and most often, leaving less frequent characters to fill in the safe gaps between them. The upfront check `frequency > (n+1)/2` is exactly the condition under which even perfect spacing cannot avoid two occurrences landing adjacent, by the pigeonhole principle.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap greedy interleaving of aab into aba, alternating the two most frequent remaining characters">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "aab"  (counts: a=2, b=1)</text>
    <text x="10" y="45">heap: [(a,2), (b,1)]</text>
    <text x="10" y="65">pop a, pop b -&gt; append "a","b" -&gt; result "ab"</text>
    <text x="10" y="85">a count-&gt;1, push back (a,1); b count-&gt;0, discard</text>
    <text x="10" y="105">heap: [(a,1)] -&gt; only one left, append -&gt; result "aba"</text>
    <rect x="10" y="120" width="130" height="24" fill="#3fb950"/><text x="75" y="137" fill="#0d1117" text-anchor="middle" font-size="10">result = "aba"</text>
  </g>
</svg>

Pairing the two most frequent remaining characters each round keeps identical letters apart.

## 5. Runnable example

```java
// ReorganizeString.java
import java.util.*;

public class ReorganizeString {

    // KEY INSIGHT: no valid arrangement exists if one character's
    // count exceeds (n+1)/2 -- otherwise, always placing the two
    // currently most frequent characters together each round keeps
    // identical characters apart.

    static String reorganizeString(String s) {
        int n = s.length();
        int[] counts = new int[26];
        for (char c : s.toCharArray()) counts[c - 'a']++;

        for (int c : counts) {
            if (c > (n + 1) / 2) return "";
        }

        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> b[1] - a[1]);
        for (int i = 0; i < 26; i++) {
            if (counts[i] > 0) heap.offer(new int[]{i, counts[i]});
        }

        StringBuilder sb = new StringBuilder();
        while (heap.size() >= 2) {
            int[] first = heap.poll();
            int[] second = heap.poll();
            sb.append((char) ('a' + first[0]));
            sb.append((char) ('a' + second[0]));
            if (--first[1] > 0) heap.offer(first);
            if (--second[1] > 0) heap.offer(second);
        }
        if (!heap.isEmpty()) {
            sb.append((char) ('a' + heap.peek()[0])); // count is guaranteed 1
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println(reorganizeString("aab"));
        // aba
        System.out.println(reorganizeString("aaab"));
        // "" (a's count 3 exceeds (4+1)/2 = 2)
    }
}
```

**How to run:** `java ReorganizeString.java`

## 6. Walkthrough

Trace `reorganizeString("aab")`:

| step | heap before | action | result |
|---|---|---|---|
| feasibility check | — | max count 2 <= (3+1)/2=2, OK | — |
| round 1 | [(a,2),(b,1)] | pop a, pop b, append both, a-&gt;1 pushed back, b-&gt;0 dropped | "ab" |
| round 2 | [(a,1)] | only one left, append it | "aba" |

Final result: `"aba"`, no two adjacent characters equal. Time complexity is O(n log 26), effectively O(n) since the heap holds at most 26 entries (one per letter). Space is O(1) beyond the output, since the heap and count array are bounded by the fixed alphabet size.

## 7. Gotchas & takeaways

> Gotcha: the feasibility check must use `(n + 1) / 2` (integer division), not `n / 2` — for odd-length strings like `"aab"` (`n=3`), `(3+1)/2 = 2` correctly allows `a` to appear twice, while `3/2 = 1` would incorrectly reject a valid input.

- This is Task Scheduler's greedy idea (always advance the most frequent remaining item) applied to building a string instead of filling time slots.
- Popping and processing TWO heap entries per round (not one) is what guarantees separation — popping only one at a time risks the same character coming back around too soon.
- Related problems: Task Scheduler (identical greedy-by-frequency idea, with an explicit cooldown length `n` instead of the implicit "adjacent" constraint).
