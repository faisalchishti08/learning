---
card: leetcode-patterns
gi: 288
slug: top-k-frequent-words
title: Top K Frequent Words
---

## 1. What it is

Given an array of strings `words` and an integer `k`, return the `k` most frequent words, SORTED by frequency descending; if two words have the same frequency, the LEXICOGRAPHICALLY SMALLER word comes first. Example: `words = ["i","love","leetcode","i","love","coding"]`, `k = 2` → `["i","love"]`.

## 2. Why & when

This is Top K Frequent Elements with a tie-break rule, which turns a simple counting problem into a two-key ranking problem: sort by frequency descending, THEN alphabetically ascending. That extra tie-break rules out the plain bucket-sort template (whose buckets have no defined internal order), so this problem uses a heap with a custom comparator instead. Use this shape whenever "most frequent" ties need a secondary, deterministic ordering rule.

## 3. Core concept

**Key idea:** use a min-heap of size `k`, ordered so the "worst" word (lowest frequency, or alphabetically LARGEST among equal frequencies) sits at the head and gets evicted first.

**Steps:**
1. Count each word's frequency with a `HashMap<String, Integer>`.
2. Create a min-heap of `(word, count)` pairs with a comparator: order by count ASCENDING first; for equal counts, order by word DESCENDING (so alphabetically later words are "worse" and sit near the head, ready to be evicted).
3. Offer every distinct word to the heap; if the heap size exceeds `k`, poll (remove) the head.
4. Drain the heap into a list and reverse it, since the heap empties smallest/worst-first, but the answer needs largest/best-first.

**Why it is correct:** the comparator encodes BOTH ranking rules at once (frequency first, alphabetical order as the tiebreaker), so the heap's usual "evict the head on overflow" behavior automatically respects both rules together — a word only survives if no other word is both more frequent, or equally frequent and alphabetically smaller. Reversing the drained list restores the requested descending-by-rank order.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap of size 2 ordered by frequency ascending then word descending, keeping i and love as the two most frequent words">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">words: i, love, leetcode, i, love, coding  (k=2)</text>
    <text x="10" y="45">counts: i=2, love=2, leetcode=1, coding=1</text>
    <text x="10" y="70">heap order: count asc, then word desc (worst at head)</text>
    <text x="10" y="90">offer leetcode, coding, i, love (evicting when size &gt; 2)</text>
    <text x="10" y="110">final heap holds: {i:2, love:2}  (both beat leetcode/coding)</text>
    <text x="10" y="130">drain smallest-first: love, i -&gt; reverse</text>
    <rect x="10" y="145" width="150" height="24" fill="#3fb950"/><text x="85" y="162" fill="#0d1117" text-anchor="middle" font-size="10">result = [i, love]</text>
  </g>
</svg>

Both `i` and `love` tie at frequency 2; alphabetical order (`i` before `love`) breaks the tie.

## 5. Runnable example

```java
// TopKFrequentWords.java
import java.util.*;

public class TopKFrequentWords {

    // KEY INSIGHT: encode BOTH ranking rules (frequency, then
    // alphabetical tiebreak) into one comparator, so the size-k
    // heap's normal eviction logic respects both automatically.

    static List<String> topKFrequent(String[] words, int k) {
        Map<String, Integer> counts = new HashMap<>();
        for (String w : words) counts.merge(w, 1, Integer::sum);

        PriorityQueue<Map.Entry<String, Integer>> heap = new PriorityQueue<>(
            (a, b) -> {
                if (!a.getValue().equals(b.getValue())) {
                    return a.getValue() - b.getValue(); // lower count = worse = near head
                }
                return b.getKey().compareTo(a.getKey()); // alphabetically later = worse
            }
        );

        for (Map.Entry<String, Integer> e : counts.entrySet()) {
            heap.offer(e);
            if (heap.size() > k) heap.poll();
        }

        LinkedList<String> result = new LinkedList<>();
        while (!heap.isEmpty()) {
            result.addFirst(heap.poll().getKey()); // reverse: best word ends up first
        }
        return result;
    }

    public static void main(String[] args) {
        String[] words = {"i", "love", "leetcode", "i", "love", "coding"};
        System.out.println(topKFrequent(words, 2));
        // [i, love]
    }
}
```

**How to run:** `java TopKFrequentWords.java`

## 6. Walkthrough

Trace `topKFrequent(["i","love","leetcode","i","love","coding"], 2)`:

| step | state |
|---|---|
| counts | i:2, love:2, leetcode:1, coding:1 |
| offer leetcode | heap = [(leetcode,1)] |
| offer coding | heap = [(coding,1),(leetcode,1)], head is worse of the two by word desc: leetcode |
| offer i | size 3 &gt; 2, evict head (leetcode,1) -&gt; heap = [(coding,1),(i,2)] |
| offer love | size 3 &gt; 2, evict head (coding,1) -&gt; heap = [(i,2),(love,2)], head is worse by word desc: love |
| drain | poll love -&gt; addFirst -&gt; [love]; poll i -&gt; addFirst -&gt; [i, love] |

Final result: `["i", "love"]`. Time complexity is O(n log k), for `n` distinct words and `k` heap operations bounded at O(log k) each; the final drain-and-reverse costs O(k log k). Space is O(n), for the count map, plus O(k) for the heap.

## 7. Gotchas & takeaways

> Gotcha: getting the tiebreak comparator direction backwards is the most common bug here — the heap's HEAD must be the "worst" entry (so it gets evicted first), which for equal counts means the ALPHABETICALLY LARGER word, not the smaller one. Mixing this up returns the wrong words on ties.

- The two-key comparator (frequency, then alphabetical) is the general technique for any "top-k with a tiebreak" problem — the size-k-heap template stays the same, only the comparator logic grows.
- Draining a min-heap always yields ascending (worst-to-best) order, so reversing (here via `addFirst`) is required to present results best-first, as most problems expect.
- Related problems: Top K Frequent Elements (the same pattern without a tiebreak rule), Sort Characters By Frequency (frequency ranking with no explicit tiebreak needed).
