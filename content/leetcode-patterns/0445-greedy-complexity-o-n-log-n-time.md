---
card: leetcode-patterns
gi: 445
slug: greedy-complexity-o-n-log-n-time
title: "Greedy — complexity: O(n log n) time"
---

## 1. What it is

This page states and justifies the complexity of greedy solutions, and lists the problems that use this pattern, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. Greedy solutions are typically among the CHEAPEST approaches available for a problem, since they replace an exponential (brute-force) or polynomial (DP) search with a single sorted pass.

## 3. Core concept

**Time complexity: O(n log n)** when a SORT is required first (Assign Cookies, Queue Reconstruction by Height), since sorting dominates the cost — the single pass that follows is only O(n).

**Time complexity: O(n)** when no sort is needed, and the problem is already processed in a natural order (Jump Game, Jump Game II, Gas Station, Lemonade Change, Can Place Flowers, Dota2 Senate).

**Space complexity: O(1)** for most greedy solutions beyond the input itself (a handful of running variables), though some (Queue Reconstruction's insertion-based result list, Dota2 Senate's queues) need O(n) auxiliary space to hold intermediate structures.

**Why greedy is typically cheaper than DP for the SAME problem, when it applies:** DP explores every reachable state and compares them; greedy commits to one choice per step without comparison, so its per-step cost is O(1) (or O(log n) for a heap-based variant), rather than O(n) or more per step. The tradeoff: this speed is only available when the exchange argument actually holds — otherwise, greedy silently produces a wrong answer instead of a slow-but-correct one.

## 4. Diagram

<svg viewBox="0 0 480 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sort dominated cost of n log n versus a plain single pass cost of n depending on whether sorting is required first">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">needs a sort first: O(n log n) total (sort dominates the single pass)</text>
    <text x="10" y="45" font-weight="bold">already in a usable order: O(n) total (just the single pass)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">greedy's single pass is always O(n) or O(n log n) with a heap</text>
  </g>
</svg>

Whether a sort is required is what usually decides between O(n) and O(n log n) for a greedy solution.

## 5. Runnable example

```java
// GreedyComplexity.java
import java.util.Arrays;

public class GreedyComplexity {

    // Confirms O(n log n): the sort dominates; the pass afterward is
    // a single O(n) scan, adding no further asymptotic cost.
    static int findContentChildrenCountingOps(int[] greed, int[] cookies, long[] ops) {
        Arrays.sort(greed);
        Arrays.sort(cookies);
        int child = 0, cookie = 0;
        while (child < greed.length && cookie < cookies.length) {
            ops[0]++;
            if (cookies[cookie] >= greed[child]) child++;
            cookie++;
        }
        return child;
    }

    public static void main(String[] args) {
        int[] greed = {1, 2, 3, 4, 5};
        int[] cookies = {1, 2, 3, 4, 5};
        long[] ops = {0};
        int result = findContentChildrenCountingOps(greed, cookies, ops);
        System.out.println("result=" + result + " ops=" + ops[0]);
        // ops stays at n == 5, confirming the pass itself is linear
    }
}
```

**How to run:** `java GreedyComplexity.java`

## 6. Walkthrough

1. `findContentChildrenCountingOps` runs the standard sort-then-scan template while counting every comparison in the single pass, in `ops`.
2. For arrays of length `5` each, `ops` stays at exactly `5`, confirming the SCAN itself is linear — all the extra cost of this solution comes from the SORT beforehand, not the greedy pass.
3. Doubling the array size to `10` keeps `ops` at `10` (still linear), while the sort's cost grows by its own `n log n` factor separately.
4. This separation — "sort cost" plus "scan cost" — is why the overall bound is written as O(n log n): the LARGER of the two terms dominates, and sorting is almost always the larger one.
5. For problems that skip the sort entirely (Jump Game, Gas Station), this same reasoning collapses straight to O(n), since there is no O(n log n) term to dominate.

## 7. Gotchas & takeaways

> Gotcha: assuming EVERY greedy solution is O(n) overlooks the sorting step that many of them require — always separately account for "cost to establish the right order" and "cost of the single pass," since the former is often the larger of the two.

- Time: O(n log n) when sorting is required first; O(n) when the input is already in a workable order. Space: O(1) typically, O(n) when an auxiliary structure (queue, result list) is needed.
- Greedy's speed advantage over DP comes specifically from making ONE choice per step with no comparison against alternatives — valid only when the exchange argument holds.
- Problems that use this pattern: Assign Cookies, Lemonade Change, Can Place Flowers, Jump Game, Jump Game II, Gas Station, Hand of Straights, Dota2 Senate, Queue Reconstruction by Height.
