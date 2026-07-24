---
card: leetcode-patterns
gi: 292
slug: maximum-number-of-coins-you-can-get
title: Maximum Number of Coins You Can Get
---

## 1. What it is

There are `3n` piles of coins. In each of `n` rounds: you pick any 3 remaining piles; Alice takes the pile with the MOST coins; Bob takes the pile with the SECOND most coins of those 3; you keep the LAST one. Given `piles`, return the maximum number of coins you can end up with by choosing groupings optimally. Example: `piles = [2,4,1,2,7,8]` → `9`.

## 2. Why & when

This is a ranking-and-selection problem: sorting the piles fully reveals the optimal grouping strategy in one pass, with no simulation needed. It belongs to the Top-K Elements family because it hinges on the same core idea — reason about items by their SORTED rank to decide which ones to keep — even though the final technique is direct index arithmetic on a sorted array rather than a heap. Use this shape whenever an optimal greedy strategy becomes obvious only after sorting, and the answer is a sum over specific, regularly-spaced positions.

## 3. Core concept

**Key idea:** sort all piles ascending. Alice will always end up taking the largest pile in each group of 3 (she is unbeatable at "most coins," so never fight her for it). To maximize your OWN total, you should always let Bob take the smallest pile of the 3, keeping the MIDDLE pile for yourself.

**Steps:**
1. Sort `piles` ascending.
2. To always give Bob the globally smallest remaining piles (which you cannot use anyway, since he only ever takes the second-largest of a group), group the SMALLEST `n` piles with the largest ones so those small piles always end up going to Bob.
3. After sorting, the optimal groups pair the largest pile with the next-largest AVAILABLE pile (for you) and the smallest remaining pile (for Bob). This works out to: you always keep piles at indices `n, n+2, n+4, ..., 3n-2` (0-indexed, ascending sort).
4. Sum `piles[n] + piles[n+2] + ... + piles[3n-2]`.

**Why it is correct:** Alice always takes the single largest pile in any group she is offered, so you cannot deny her the overall largest pile — it is always lost to Alice. Given that, your best move each round is to sacrifice the CURRENT smallest remaining pile to Bob (since it is the least valuable pile to lose), pair it with the current largest remaining pile (lost to Alice anyway), and keep the next-largest pile for yourself. Repeating this greedy trade `n` times, on a sorted array, lands you exactly on piles at indices `n, n+2, …, 3n-2`.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sorted piles 1,2,2,4,7,8 grouped so Alice takes the largest, Bob takes the smallest remaining, and you keep the middle pile each round">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">piles = [2,4,1,2,7,8], n = 2 -&gt; sorted: [1,2,2,4,7,8]</text>
    <text x="10" y="45">round 1: group {1(Bob), 7(you), 8(Alice)}</text>
    <text x="10" y="65">round 2: group {2(Bob), 4(you), 2(Alice)}</text>
    <text x="10" y="90">your piles: indices n=2 and n+2=4 -&gt; values 2, 7</text>
    <rect x="10" y="105" width="150" height="24" fill="#3fb950"/><text x="85" y="122" fill="#0d1117" text-anchor="middle" font-size="10">total = 2 + 7 = 9</text>
  </g>
</svg>

Sacrificing the smallest remaining pile to Bob each round preserves the largest possible "middle" pile for you.

## 5. Runnable example

```java
// MaximumCoinsYouCanGet.java
import java.util.Arrays;

public class MaximumCoinsYouCanGet {

    // KEY INSIGHT: Alice always claims the single largest remaining
    // pile no matter what. Given that loss is unavoidable, sacrifice
    // the current SMALLEST pile to Bob each round, keeping the
    // middle pile -- on a sorted array this lands on indices
    // n, n+2, ..., 3n-2.

    static int maxCoins(int[] piles) {
        Arrays.sort(piles);
        int n = piles.length / 3;
        int total = 0;
        for (int i = n; i < piles.length - 1; i += 2) {
            total += piles[i];
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(maxCoins(new int[]{2, 4, 1, 2, 7, 8}));
        // 9
        System.out.println(maxCoins(new int[]{9, 8, 7, 6, 5, 1, 2, 3, 4}));
        // 18
    }
}
```

**How to run:** `java MaximumCoinsYouCanGet.java`

## 6. Walkthrough

Trace `maxCoins([2,4,1,2,7,8])`:

| step | value |
|---|---|
| sorted piles | [1, 2, 2, 4, 7, 8] |
| n = piles.length / 3 | 2 |
| loop bound | i from n=2, while i &lt; piles.length-1=5, step 2 |
| i=2 | piles[2] = 2, total = 2 |
| i=4 | piles[4] = 7, total = 9 |
| i=6 | 6 &lt; 5 is false, loop stops |

The two indices `2` and `4` hold the piles you keep, values `2` and `7`, summing to `9`. This matches the expected answer. Time complexity is O(m log m) for the sort, where `m = 3n` is the total pile count. The summation loop is O(n). Space is O(log m) to O(m), depending on the sort implementation.

## 7. Gotchas & takeaways

> Gotcha: it is easy to mis-derive the index range and off-by-one the loop bounds — always sanity-check the formula against the official example (`piles=[2,4,1,2,7,8]` must give `9`) before trusting a derived index range on a new input.

- Sorting first turns a seemingly complex 3-way greedy game into simple, fixed index arithmetic — no simulation of rounds is required.
- The core insight ("you cannot beat Alice for the largest pile, so minimize what you lose to Bob instead") is a classic greedy reframing: focus on the loss you CAN control, not the one you cannot.
- Related problems: Sort the People (a simpler full-array sort-by-paired-key problem), Least Number of Unique Integers after K Removals (another greedy problem that becomes simple after sorting).
