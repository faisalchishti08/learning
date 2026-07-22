---
card: leetcode-patterns
gi: 170
slug: find-the-town-judge
title: Find the Town Judge
---

## 1. What it is

In a town of `n` people labeled `1` to `n`, a list `trust` gives pairs `[a, b]` meaning person `a` trusts person `b`. The town judge trusts nobody, and everybody else trusts the judge. Return the judge's label if one exists, otherwise `-1`. Example: `n = 3`, `trust = [[1,3],[2,3]]` → `3`.

## 2. Why & when

This is a graph problem in disguise: `trust` edges form a directed graph, and the judge is the one node with in-degree `n-1` and out-degree `0`. Rather than traversing the graph, you can answer it directly by counting degrees — a useful reminder that not every graph question needs BFS or DFS.

## 3. Core concept

**Key idea:** track a single net "trust score" per person: `+1` when someone trusts them (in-degree), `-1` when they trust someone else (out-degree). The judge is the only person who ends with a score of exactly `n - 1`, because they receive n-1 trusts and give zero.

**Steps:**
1. Create a `score` array of size `n + 1` (1-indexed), initialized to `0`.
2. For each `[a, b]` in `trust`, decrement `score[a]` (a trusts someone, so a can't be judge) and increment `score[b]` (b gains a truster).
3. Scan `score[1..n]`; return the label `i` where `score[i] == n - 1`.
4. If no such label exists, return `-1`.

**Why it is correct:** a node's out-degree contributes `-1` per outgoing edge and in-degree contributes `+1` per incoming edge. The judge trusts nobody (out-degree 0) and is trusted by everyone else (in-degree n-1), so their net score is exactly `n - 1`; no other person can reach that score, since anyone who trusts someone has a negative contribution.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Everyone points to the judge, who points to nobody">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="90" r="20" fill="#161b22" stroke="#3fb950"/><text x="230" y="94" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="80" cy="40" r="16" fill="#161b22" stroke="#79c0ff"/><text x="80" y="44" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="80" cy="140" r="16" fill="#161b22" stroke="#79c0ff"/><text x="80" y="144" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="94" y1="50" x2="212" y2="82" stroke="#8b949e" marker-end="url(#a)"/>
    <line x1="94" y1="130" x2="212" y2="98" stroke="#8b949e" marker-end="url(#a)"/>
    <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">1 and 2 both trust 3; 3 trusts nobody -- score[3] = 2 = n-1, so 3 is the judge</text>
  </g>
</svg>

Person `3` has in-degree `2` (= n-1) and out-degree `0`; no one else can match that net score.

## 5. Runnable example

```java
// FindTheTownJudge.java
public class FindTheTownJudge {

    // Level 1 -- Brute force: build separate in-degree and out-degree
    // arrays, then scan for a person with in-degree == n-1 AND
    // out-degree == 0. Correct, and clear, but keeping two arrays and
    // checking two conditions is more bookkeeping than needed.

    // KEY INSIGHT: a single combined "net score" (in-degree minus
    // out-degree) captures both conditions in ONE array and ONE
    // comparison -- the judge is the unique person whose score hits
    // exactly n-1.

    // Level 2 -- Optimal: single net-score array.
    static int findJudge(int n, int[][] trust) {
        int[] score = new int[n + 1];
        for (int[] t : trust) {
            score[t[0]]--;
            score[t[1]]++;
        }
        for (int i = 1; i <= n; i++) {
            if (score[i] == n - 1) return i;
        }
        return -1;
    }

    // Level 3 -- Hardened: n == 1 with an empty trust list correctly
    // returns 1 (score[1] stays 0, and n-1 is also 0, so the single
    // person is trivially the judge with nobody to trust or be trusted
    // by).

    public static void main(String[] args) {
        System.out.println(findJudge(2, new int[][]{{1,2}})); // 2
        System.out.println(findJudge(3, new int[][]{{1,3},{2,3}})); // 3
        System.out.println(findJudge(3, new int[][]{{1,3},{2,3},{3,1}})); // -1
        System.out.println(findJudge(1, new int[][]{})); // 1
    }
}
```

**How to run:** `java FindTheTownJudge.java`

## 6. Walkthrough

Trace `n = 3`, `trust = [[1,3],[2,3]]`:

| Step | Edge processed | score[1] | score[2] | score[3] |
|---|---|---|---|---|
| start | — | 0 | 0 | 0 |
| 1 | `[1,3]` | -1 | 0 | 1 |
| 2 | `[2,3]` | -1 | -1 | 2 |
| scan | check `score[i] == n-1 (2)` | -1 ≠ 2 | -1 ≠ 2 | 2 = 2 → return 3 |

Time complexity is O(n + T), where T is the number of trust pairs, for building the score array and scanning it; space is O(n) for the array.

## 7. Gotchas & takeaways

> Checking only in-degree `== n - 1` without also ruling out outgoing trust lets a person who both trusts and is trusted by everyone else pass incorrectly; the net-score trick avoids this bug automatically, since any outgoing trust subtracts from their score.

- `n == 1` with no trust pairs is a valid edge case: the lone person is the judge by definition.
- If the judge label were not required to be found among `1..n`, an array-based score would need a hash map instead — array indexing only works because labels are `1` to `n`.
- Related problems: Find the Celebrity (a similar "everyone knows them, they know nobody" search, but interactive/API-based rather than edge-list based).
