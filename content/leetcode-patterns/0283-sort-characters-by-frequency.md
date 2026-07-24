---
card: leetcode-patterns
gi: 283
slug: sort-characters-by-frequency
title: Sort Characters By Frequency
---

## 1. What it is

Given a string `s`, sort its characters in decreasing order based on how often each character occurs, and return the sorted string. Example: `s = "tree"` → `"eert"` (`e` occurs twice, `r` and `t` once each; both `"eert"` and `"eetr"` are valid answers).

## 2. Why & when

This is the string version of Top K Frequent Elements: rank every distinct character by frequency, then rebuild a string from that ranking. It uses the bucket-sort-by-frequency template directly, since here you want ALL characters ranked, not just the top `k`. Use this shape whenever a problem wants a full frequency-ordered rebuild, not just a top-k subset.

## 3. Core concept

**Key idea:** count each character's frequency, bucket characters by frequency, then read buckets from highest to lowest, appending each character `freq` times to build the output string.

**Steps:**
1. Build a `HashMap<Character, Integer>` counting occurrences of each character in `s`.
2. Create `buckets`, an array sized `s.length() + 1`, where `buckets[freq]` holds every character with that exact frequency.
3. Walk `buckets` from the highest index down to `1`. For each character found, append it to a `StringBuilder` `freq` times.

**Why it is correct:** every character's frequency is between `1` and `s.length()`, so the bucket array covers every possible frequency. Reading from the highest bucket first places the most frequent characters at the front of the output, matching "decreasing order of frequency" exactly, and appending each character `freq` times reconstructs a string with the correct total length.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frequency buckets for the string tree showing e in bucket 2 and r, t in bucket 1">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "tree"</text>
    <text x="10" y="45">counts: t -&gt; 1, r -&gt; 1, e -&gt; 2</text>
    <text x="10" y="70">bucket[2] = [e]</text>
    <text x="10" y="90">bucket[1] = [t, r]</text>
    <text x="10" y="115">append e twice, then t once, then r once</text>
    <rect x="10" y="125" width="130" height="24" fill="#3fb950"/><text x="75" y="142" fill="#0d1117" text-anchor="middle" font-size="10">result = "eetr"</text>
  </g>
</svg>

Bucket 2 (frequency 2) is read before bucket 1, so `e` appears before `t` and `r`.

## 5. Runnable example

```java
// SortCharactersByFrequency.java
import java.util.*;

public class SortCharactersByFrequency {

    // Level 1 -- Brute force: put (char, count) pairs into a list,
    // sort by count descending with a comparator, then rebuild the
    // string. Correct, but O(m log m) for m distinct characters, an
    // unneeded comparison sort.

    // KEY INSIGHT: frequency is bounded by s.length(), so bucket by
    // count directly instead of comparing counts with a sort.

    // Level 2 -- Optimal: bucket sort by frequency, O(n).
    static String frequencySort(String s) {
        Map<Character, Integer> counts = new HashMap<>();
        for (char c : s.toCharArray()) counts.merge(c, 1, Integer::sum);

        List<Character>[] buckets = new List[s.length() + 1];
        for (Map.Entry<Character, Integer> e : counts.entrySet()) {
            int freq = e.getValue();
            if (buckets[freq] == null) buckets[freq] = new ArrayList<>();
            buckets[freq].add(e.getKey());
        }

        StringBuilder sb = new StringBuilder();
        for (int freq = buckets.length - 1; freq >= 1; freq--) {
            if (buckets[freq] == null) continue;
            for (char c : buckets[freq]) {
                for (int i = 0; i < freq; i++) sb.append(c);
            }
        }
        return sb.toString();
    }

    // Level 3 -- Hardened: works for a single-character string (one
    // bucket, one character repeated once) and for a string where
    // every character is distinct (every character lands in
    // bucket[1], output length still matches input length).

    public static void main(String[] args) {
        System.out.println(frequencySort("tree"));
        // eetr (order among same-frequency chars may vary)
        System.out.println(frequencySort("cccaaa"));
        // cccaaa (or aaaccc)
    }
}
```

**How to run:** `java SortCharactersByFrequency.java`

## 6. Walkthrough

Trace `frequencySort("tree")`:

| step | state |
|---|---|
| counts | `{t:1, r:1, e:2}` |
| bucket[2] | `[e]` |
| bucket[1] | `[t, r]` |
| scan freq=4..3 | empty, skip |
| scan freq=2 | append `e` twice -&gt; `"ee"` |
| scan freq=1 | append `t` once, `r` once -&gt; `"eetr"` |

Final result: `"eetr"`. Time complexity is O(n): one pass to count, one pass to bucket, and appending each character exactly as many times as it occurs (total appends equal `s.length()`). Space is O(n), for the count map, buckets, and output string.

## 7. Gotchas & takeaways

> Gotcha: the inner loop must append each character exactly `freq` times — appending it only once per bucket entry would silently drop repeated characters and shrink the output length below `s.length()`.

- This is Top K Frequent Elements generalized to "rank ALL items," not just the top `k` — the bucket-sort template stays identical, only the stopping condition changes (read every bucket, not just until `k` items are collected).
- A max-heap keyed by frequency also works here, at O(n log m) for `m` distinct characters — the bucket approach is strictly faster since it avoids comparisons entirely.
- Related problems: Top K Frequent Elements (the same bucket-by-frequency idea, capped at `k` results), Top K Frequent Words (frequency ranking with an alphabetical tie-break).
