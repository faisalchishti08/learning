---
card: leetcode-patterns
gi: 198
slug: two-heaps-complexity-o-log-n-per-insert
title: Two Heaps — complexity: O(log n) per insert
---

## 1. What it is

This page explains why two heaps runs in O(log n) time per insertion and O(1) time per median query, and lists the named problems that use the pattern, so you have both the proof and a reference set.

## 2. Why & when

Interviewers often ask "why is this fast" as a follow-up to a working solution. "Because heaps are fast" is not a full answer — you need to explain which operations are O(log n) versus O(1), and why re-sorting the whole dataset on every update (an easy first instinct) would be much worse.

## 3. Core concept

**Per-insert time — O(log n).** Each `addNum` call does at most: one `peek()` (O(1)), one `add()` into a heap of size up to n (O(log n), since a binary heap's insert re-heapifies along a path of height log n), and at most one rebalancing `poll()` + `add()` pair (also O(log n) each). All of these are constant-count operations, each individually O(log n), so the total per insert is O(log n).

**Per-query time — O(1).** `findMedian()` only reads `peek()` on one or both heaps — no traversal, no re-computation. This is the entire payoff of maintaining the heaps incrementally: the answer is always sitting at the top, ready to read.

**Compare to the naive alternative.** Inserting into a sorted array (or re-sorting on every query) costs O(n) per insert (shifting elements) or O(n log n) per query (re-sorting). Over n insertions, two heaps costs O(n log n) total; the naive sorted-insert approach costs O(n²) total. This is the same style of amortized-per-operation argument used to justify balanced binary search trees for the same task.

**Space — O(n).** Both heaps together hold every element seen so far, so total space is proportional to the number of elements — no way around this for a true running median, since you must remember every value's relative position.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Heap insert re-heapifies along one root-to-leaf path, height log n">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="170" cy="70" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="290" cy="70" r="14" fill="#161b22" stroke="#30363d"/>
    <circle cx="140" cy="110" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="200" cy="110" r="14" fill="#161b22" stroke="#30363d"/>
    <line x1="230" y1="44" x2="176" y2="58" stroke="#3fb950"/>
    <line x1="230" y1="44" x2="284" y2="58" stroke="#30363d"/>
    <line x1="170" y1="84" x2="146" y2="98" stroke="#3fb950"/>
    <line x1="170" y1="84" x2="194" y2="98" stroke="#30363d"/>
    <text x="10" y="150" fill="#8b949e">new element bubbles up ONE path, root to its insertion point -- height = log n</text>
  </g>
</svg>

A heap insert only touches the single path from the new leaf to the root, which has height `log n` — never the whole structure.

## 5. Runnable example

An instrumented version of the two-heaps template that counts actual heap operations performed per insert, confirming the O(log n) bound scales with heap size, not total elements processed.

```java
// ComplexityCheck.java
import java.util.*;

public class ComplexityCheck {
    static PriorityQueue<Integer> lower = new PriorityQueue<>(Collections.reverseOrder());
    static PriorityQueue<Integer> upper = new PriorityQueue<>();
    static int operationCount = 0;

    static void addNum(int num) {
        if (lower.isEmpty() || num <= lower.peek()) { lower.add(num); operationCount++; }
        else { upper.add(num); operationCount++; }

        if (lower.size() > upper.size() + 1) { upper.add(lower.poll()); operationCount += 2; }
        else if (upper.size() > lower.size()) { lower.add(upper.poll()); operationCount += 2; }
    }

    public static void main(String[] args) {
        int[] stream = {5, 3, 8, 4, 6, 7, 1, 9, 2, 0};
        for (int num : stream) {
            addNum(num);
            System.out.println("n=" + (lower.size() + upper.size())
                + " total heap ops so far=" + operationCount
                + " (at most 3 ops per insert, each O(log n))");
        }
    }
}
```

**How to run:** `java ComplexityCheck.java`

## 6. Walkthrough

1. `stream` has 10 elements, added one at a time.
2. Each call to `addNum` performs at most 1 initial `add()` plus at most 1 rebalancing `poll()`+`add()` pair — a small constant number of heap operations, never proportional to `n`.
3. Printing `operationCount` after each insert shows it grows linearly with the number of elements processed (at most 3 per insert), confirming no insert does disproportionate work as `n` grows.
4. Each individual `add()` or `poll()` call itself costs O(log n) internally (heap re-structuring along one path), so total work per `addNum` call is O(log n), and total work across all `n` insertions is O(n log n).
5. Compare this to sorting the whole array from scratch after every single insertion, which would cost O(n log n) per insertion and O(n² log n) total — dramatically worse.

## 7. Gotchas & takeaways

> Gotcha: assuming `findMedian()` is also O(log n) (confusing it with the insert cost) is a common mistake — reading the top of a heap is always O(1); only modifying a heap costs O(log n).

- Time: O(log n) per insert (heap re-structuring), O(1) per median query (just peek).
- Space: O(n), since every seen element must be stored in one of the two heaps.
- Reference problems that use this pattern: Find Median from Data Stream, Sliding Window Median, IPO, Furthest Building You Can Reach, Maximum Average Pass Ratio, Single-Threaded CPU, Process Tasks Using Servers, Minimize Deviation in Array, Find Right Interval.
