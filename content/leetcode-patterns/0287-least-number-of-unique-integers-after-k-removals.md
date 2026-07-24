---
card: leetcode-patterns
gi: 287
slug: least-number-of-unique-integers-after-k-removals
title: Least Number of Unique Integers after K Removals
---

## 1. What it is

Given an integer array `arr` and an integer `k`, remove exactly `k` elements so that the number of DISTINCT remaining integers is as small as possible, then return that count. Example: `arr = [5,5,4]`, `k = 1` → `1` (remove the one `4`, leaving only `5`s).

## 2. Why & when

This is the "k LEAST frequent" mirror of Top K Frequent Elements: to shrink the distinct-value count fastest, always remove the values that are currently rarest first, since a single removal of a value with count `1` eliminates a whole distinct value, while removing one occurrence of a value with count `5` eliminates none. It uses the frequency-bucket-sort template, read in ascending order instead of descending. Use this shape whenever a problem asks you to spend a limited "budget" (here, `k` removals) as efficiently as possible against frequency counts.

## 3. Core concept

**Key idea:** sort distinct values by frequency ASCENDING, and greedily remove entire low-frequency groups first, since eliminating a whole group (however small) is the only way a removal reduces the distinct count.

**Steps:**
1. Count each value's frequency with a `HashMap`.
2. Extract the frequencies into a list and sort it ascending (or use a min-heap).
3. Walk the sorted frequencies from smallest to largest. For each frequency `f`, if `k >= f`, subtract `f` from `k`, and reduce the number of remaining distinct integers by one (this whole group got removed).
4. Stop as soon as `k < f` for the current group (not enough budget left to clear it entirely) — the answer is the number of distinct values you have NOT yet cleared.

**Why it is correct:** removing a distinct value entirely requires spending removals equal to its full count. To minimize the FINAL distinct count with a fixed removal budget, you should always clear the cheapest (lowest-frequency) group first — clearing a low-frequency group "costs" fewer removals per distinct value eliminated than clearing a high-frequency group, so a greedy ascending sweep uses the budget most efficiently.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Removing frequency groups ascending, using k=1 to fully remove the group with frequency 1 first">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr = [5,5,4], k = 1</text>
    <text x="10" y="45">counts: 5 -&gt; 2, 4 -&gt; 1</text>
    <text x="10" y="65">sorted frequencies ascending: [1, 2]</text>
    <text x="10" y="90">f=1: k(1) &gt;= 1 -&gt; remove group, k -&gt; 0, distinct -&gt; 1</text>
    <text x="10" y="110">f=2: k(0) &lt; 2 -&gt; stop, group of 5 survives</text>
    <rect x="10" y="125" width="150" height="24" fill="#3fb950"/><text x="85" y="142" fill="#0d1117" text-anchor="middle" font-size="10">answer = 1</text>
  </g>
</svg>

Clearing the cheapest group (frequency 1) first uses the removal budget most efficiently.

## 5. Runnable example

```java
// LeastUniqueIntegersAfterKRemovals.java
import java.util.*;

public class LeastUniqueIntegersAfterKRemovals {

    // KEY INSIGHT: to shrink the distinct count, only fully-cleared
    // groups matter. Clearing the lowest-frequency groups first
    // eliminates the most distinct values per removal spent.

    static int findLeastNumOfUniqueInts(int[] arr, int k) {
        Map<Integer, Integer> counts = new HashMap<>();
        for (int num : arr) counts.merge(num, 1, Integer::sum);

        List<Integer> freqs = new ArrayList<>(counts.values());
        Collections.sort(freqs); // ascending

        int distinctRemaining = freqs.size();
        for (int f : freqs) {
            if (k >= f) {
                k -= f;
                distinctRemaining--;
            } else {
                break; // not enough budget to clear this or any larger group
            }
        }
        return distinctRemaining;
    }

    public static void main(String[] args) {
        System.out.println(findLeastNumOfUniqueInts(new int[]{5, 5, 4}, 1));
        // 1
        System.out.println(findLeastNumOfUniqueInts(new int[]{4, 3, 1, 1, 3, 3, 2}, 3));
        // 2
    }
}
```

**How to run:** `java LeastUniqueIntegersAfterKRemovals.java`

## 6. Walkthrough

Trace `findLeastNumOfUniqueInts([4,3,1,1,3,3,2], 3)`:

| step | value |
|---|---|
| counts | 4:1, 3:3, 1:2, 2:1 |
| sorted frequencies ascending | [1, 1, 2, 3] |
| distinctRemaining start | 4 |
| f=1: k(3)&gt;=1 -&gt; k=2, distinct=3 | (cleared value 4 or 2) |
| f=1: k(2)&gt;=1 -&gt; k=1, distinct=2 | (cleared the other of 4/2) |
| f=2: k(1)&lt;2 -&gt; stop | budget too small to clear this group |

Final answer: `2`. Time complexity is O(n log n), dominated by sorting the distinct frequencies (at most `n` of them). Space is O(n), for the count map and frequency list.

## 7. Gotchas & takeaways

> Gotcha: stopping the loop the instant `k < f` is required — continuing to check LARGER frequencies after that point is pointless, since the list is sorted ascending and every remaining group costs even more to clear.

- This mirrors Top K Frequent Elements exactly, but reversed: there you keep the top-k MOST frequent, here you greedily discard the LEAST frequent groups first.
- A partial removal (removing fewer than `f` occurrences from a group) NEVER reduces the distinct count — only fully clearing a group does, which is why the algorithm only ever considers whole-group removals.
- Related problems: Top K Frequent Elements (frequency ranking descending instead of ascending), Task Scheduler (frequency-driven greedy scheduling under a different kind of budget).
