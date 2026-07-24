---
card: leetcode-patterns
gi: 291
slug: kth-distinct-string-in-an-array
title: Kth Distinct String in an Array
---

## 1. What it is

A "distinct string" in an array is one that occurs EXACTLY once. Given an array of strings `arr` and an integer `k`, return the `k`-th distinct string in `arr`, in the ORDER it appears. If fewer than `k` distinct strings exist, return an empty string. Example: `arr = ["d","b","c","b","c","a"]`, `k = 2` → `"a"` (distinct strings, in order: `"d"`, then `"a"`; the 2nd one is `"a"`).

## 2. Why & when

This is a frequency-filtering problem: instead of ranking items BY frequency, you filter for a specific frequency (exactly `1`) and then rank the survivors by their ORIGINAL array order, not by count. It is a lighter cousin of the Top-K Elements pattern, sharing the "count first" step but skipping any heap or bucket sort, since order of appearance — not frequency magnitude — decides the final ranking. Use this shape whenever a problem needs "the k-th item that satisfies a frequency condition, in original order."

## 3. Core concept

**Key idea:** count every string's frequency first, then walk the array a second time in its ORIGINAL order, keeping only strings with frequency exactly `1`, and stop once you have passed `k` of them.

**Steps:**
1. Build a `HashMap<String, Integer>` counting occurrences of each string in `arr`.
2. Walk `arr` again, in order. For each string with count exactly `1`, increment a counter.
3. When the counter reaches `k`, return that string immediately.
4. If the walk finishes without the counter reaching `k`, return `""`.

**Why it is correct:** the first pass establishes each string's TRUE final frequency across the whole array, so the second pass can correctly test "is this occurrence's string distinct" without needing to look ahead. Walking the array a second time in its original index order (rather than any sorted or bucketed order) directly matches the problem's requirement of returning the `k`-th distinct string BY APPEARANCE ORDER, not by any other ranking.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Filtering an array for strings with count exactly 1, in original order, and picking the 2nd such string">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr = [d, b, c, b, c, a], k = 2</text>
    <text x="10" y="45">counts: d=1, b=2, c=2, a=1</text>
    <text x="10" y="70">scan in order: d (count 1, 1st distinct)</text>
    <text x="10" y="90">b (count 2, skip), c (count 2, skip), b (skip), c (skip)</text>
    <text x="10" y="110">a (count 1, 2nd distinct) -&gt; return</text>
    <rect x="10" y="120" width="130" height="24" fill="#3fb950"/><text x="75" y="137" fill="#0d1117" text-anchor="middle" font-size="10">result = "a"</text>
  </g>
</svg>

The second pass walks `arr` in its original order, skipping any string whose total count is not exactly 1.

## 5. Runnable example

```java
// KthDistinctString.java
import java.util.HashMap;
import java.util.Map;

public class KthDistinctString {

    // KEY INSIGHT: count first (to know each string's TRUE final
    // frequency), then filter a second pass in ORIGINAL order --
    // ranking here is by appearance order, not by frequency size,
    // so no heap or bucket sort is needed.

    static String kthDistinct(String[] arr, int k) {
        Map<String, Integer> counts = new HashMap<>();
        for (String s : arr) counts.merge(s, 1, Integer::sum);

        int seen = 0;
        for (String s : arr) {
            if (counts.get(s) == 1) {
                seen++;
                if (seen == k) return s;
            }
        }
        return "";
    }

    public static void main(String[] args) {
        System.out.println(kthDistinct(new String[]{"d", "b", "c", "b", "c", "a"}, 2));
        // a
        System.out.println(kthDistinct(new String[]{"aaa", "aa", "a"}, 1));
        // aaa
        System.out.println(kthDistinct(new String[]{"a", "b", "a"}, 3));
        // "" (only one distinct string, "b", but k = 3)
    }
}
```

**How to run:** `java KthDistinctString.java`

## 6. Walkthrough

Trace `kthDistinct(["d","b","c","b","c","a"], 2)`:

| index | string | count | is distinct? | seen |
|---|---|---|---|---|
| 0 | d | 1 | yes | 1 (not k=2 yet) |
| 1 | b | 2 | no | 1 |
| 2 | c | 2 | no | 1 |
| 3 | b | 2 | no | 1 |
| 4 | c | 2 | no | 1 |
| 5 | a | 1 | yes | 2 -&gt; matches k, return "a" |

Final result: `"a"`. Time complexity is O(n): one pass to count, one pass to filter, each O(n). Space is O(n), for the count map.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to return as soon as a string with count `1` is found the FIRST time it is scanned — but you must count the ENTIRE array first, since a string appearing later in the array could raise an earlier-looking "distinct" string's count above `1` by the time the full array is known.

- This is a two-pass pattern: count everything first, then filter in original order — resist the urge to combine both passes into one, since a string's true count is only known after the full array has been scanned.
- "Distinct" here means "appears exactly once," not "appears for the first time" — do not confuse this with deduplication problems that keep only the FIRST occurrence of every value.
- Related problems: Top K Frequent Elements (ranks by frequency size, not appearance order), First Unique Character in a String (the same "count first, then find by frequency" idea, applied to characters).
