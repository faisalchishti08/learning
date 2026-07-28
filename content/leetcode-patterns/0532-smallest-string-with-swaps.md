---
card: leetcode-patterns
gi: 532
slug: smallest-string-with-swaps
title: Smallest String With Swaps
---

## 1. What it is

Given a string `s` and a list of index pairs `pairs`, where each pair `[i, j]` means you may swap the characters at those two indices **any number of times**, return the lexicographically smallest string reachable through any sequence of allowed swaps. Example: `s = "dcab"`, `pairs = [[0,3],[1,2]]` → `"bacd"` (indices `0` and `3` can freely swap, and so can `1` and `2`).

## 2. Why & when

"These positions can swap, and swaps chain transitively" (if `0` can swap with `3`, and `1` can swap with `2`, but also if some pair chained `0` to `1`, all four indices would become freely rearrangeable together) is a direct [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md). Any index reachable from another through a chain of allowed swaps can end up holding any character from that whole group, in any order. Constraints: up to 10,000 string length and pairs.

## 3. Core concept

**Key idea:** union every pair of indices connected by a swap. Within one connected group of indices, unlimited swaps mean you can arrange those positions' characters in **any order** — so the smallest result places the group's characters in sorted order back into the group's index positions (in increasing index order).

**Steps:**
1. Union-find over indices `0..n-1`. For each `[i, j]` in `pairs`, `union(i, j)`.
2. Group indices by their representative: `Map<Integer, List<Integer>> groups`.
3. For each group, collect the characters at those indices, sort them, then write the sorted characters back into the group's indices in increasing order.
4. Build the result string from all groups.

**Why sorting each group independently is optimal:** indices in different groups can never exchange characters with each other (no swap chain connects them), so each group's characters are a closed pool. Within a closed pool, placing the smallest available character at the smallest index, the next-smallest at the next index, and so on, produces the lexicographically smallest arrangement for that pool — and doing this independently per group is optimal for the whole string, since groups do not interact.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Indices 0 and 3 form one group, indices 1 and 2 form another; each group's characters get sorted independently">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">s = "dcab", pairs = [[0,3],[1,2]]</text>
    <text x="20" y="50" fill="#8b949e">index: 0=d  1=c  2=a  3=b</text>
    <circle cx="80" cy="90" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="95" fill="#e6edf3" text-anchor="middle" font-size="11">0:d</text>
    <circle cx="200" cy="90" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="200" y="95" fill="#e6edf3" text-anchor="middle" font-size="11">3:b</text>
    <line x1="96" y1="90" x2="184" y2="90" stroke="#3fb950"/>
    <text x="140" y="80" fill="#3fb950" font-size="10" text-anchor="middle">group A</text>
    <circle cx="380" cy="90" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="380" y="95" fill="#e6edf3" text-anchor="middle" font-size="11">1:c</text>
    <circle cx="500" cy="90" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="500" y="95" fill="#e6edf3" text-anchor="middle" font-size="11">2:a</text>
    <line x1="396" y1="90" x2="484" y2="90" stroke="#f0883e"/>
    <text x="440" y="80" fill="#f0883e" font-size="10" text-anchor="middle">group B</text>
    <text x="140" y="150" fill="#3fb950" text-anchor="middle">group A sorted [b,d] -&gt; index0=b, index3=d</text>
    <text x="440" y="150" fill="#f0883e" text-anchor="middle">group B sorted [a,c] -&gt; index1=a, index2=c</text>
  </g>
</svg>

Group A (indices `0`, `3`) sorts `{d, b}` to `[b, d]`. Group B (indices `1`, `2`) sorts `{c, a}` to `[a, c]`. Result: `"bacd"`.

## 5. Runnable example

**Level 1 — Brute force.** Try every reachable permutation via breadth-first search over swap states. Factorial in the worst case — infeasible beyond tiny strings.

**KEY INSIGHT:** unlimited swaps within a connected group of indices means the group's characters can be freely rearranged — so the problem reduces to "sort each group's characters independently," not "search for a swap sequence."

**Level 2 — Optimal.** Union-find to group indices, then sort characters within each group, O(n log n).

**Level 3 — Hardened.** Handles indices that appear in no pair at all (each stays its own singleton group, unaffected) and duplicate characters within a group.

```java
// SmallestStringWithSwaps.java
import java.util.*;

public class SmallestStringWithSwaps {

    static class DSU {
        int[] parent;
        DSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        void union(int a, int b) {
            parent[find(a)] = find(b);
        }
    }

    static String smallestStringWithSwaps(String s, List<List<Integer>> pairs) {
        int n = s.length();
        DSU dsu = new DSU(n);
        for (List<Integer> pair : pairs) {
            dsu.union(pair.get(0), pair.get(1));
        }

        Map<Integer, List<Integer>> groups = new HashMap<>();
        for (int i = 0; i < n; i++) {
            groups.computeIfAbsent(dsu.find(i), k -> new ArrayList<>()).add(i);
        }

        char[] result = s.toCharArray();
        for (List<Integer> indices : groups.values()) {
            List<Character> chars = new ArrayList<>();
            for (int idx : indices) chars.add(s.charAt(idx));
            Collections.sort(chars);
            Collections.sort(indices); // process this group's positions in increasing order
            for (int i = 0; i < indices.size(); i++) {
                result[indices.get(i)] = chars.get(i);
            }
        }
        return new String(result);
    }

    public static void main(String[] args) {
        List<List<Integer>> pairs1 = Arrays.asList(
                Arrays.asList(0, 3), Arrays.asList(1, 2));
        System.out.println(smallestStringWithSwaps("dcab", pairs1)); // bacd

        List<List<Integer>> pairs2 = Arrays.asList(
                Arrays.asList(0, 3), Arrays.asList(1, 2), Arrays.asList(0, 2));
        System.out.println(smallestStringWithSwaps("dcab", pairs2)); // abcd, all 4 indices chain into one group
    }
}
```

**How to run:** save as `SmallestStringWithSwaps.java`, then run `java SmallestStringWithSwaps.java`.

## 6. Walkthrough

Trace `smallestStringWithSwaps("dcab", [[0,3],[1,2]])`:

1. `union(0,3)` merges indices `0` and `3` into one group. `union(1,2)` merges indices `1` and `2` into a separate group.
2. Group by representative: group A = `{0,3}`, group B = `{1,2}` (exact representative values depend on the union order, but the grouping is what matters).
3. Group A's characters at indices `0` and `3` are `'d'` and `'b'`. Sorted: `['b','d']`. Written back to sorted indices `[0,3]`: `result[0]='b'`, `result[3]='d'`.
4. Group B's characters at indices `1` and `2` are `'c'` and `'a'`. Sorted: `['a','c']`. Written back to sorted indices `[1,2]`: `result[1]='a'`, `result[2]='c'`.
5. Final result: `"bacd"`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to sort the *indices* within a group before assigning sorted characters back places the smallest character at whichever index happens to appear first in an unsorted list, not at the group's smallest index — always sort both the characters and the indices before zipping them together.

- Signal: "swap any number of times along these connected pairs" means full freedom to rearrange within each connected group — reduce to "sort per group," not a swap simulation.
- An index that never appears in any pair is its own group of size 1, and keeps its original character untouched.
- Related problems: Accounts Merge, Most Stones Removed with Same Row or Column (same "group, then reason about the group" shape).
