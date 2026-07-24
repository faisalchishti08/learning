---
card: leetcode-patterns
gi: 335
slug: tallest-billboard
title: Tallest Billboard
---

## 1. What it is

You have steel rods of various lengths in `rods`. Weld them into two SUPPORT PILLARS of EQUAL height, using each rod in AT MOST one pillar (or neither). Return the maximum possible height of the (equal) pillars. Example: `rods = [1,2,3,6]` → `6` (pillar 1: `[1,2,3]` summing to `6`; pillar 2: `[6]`).

## 2. Why & when

This generalizes Last Stone Weight II's "minimize the difference" idea into "each item goes into pillar A, pillar B, or is unused" — a THREE-WAY choice per item instead of 0/1 knapsack's two-way choice, tracked via the DIFFERENCE between the two pillar heights. Use this shape whenever a problem splits items into two groups (not necessarily using every item), and the goal involves both groups' totals being related (here, EQUAL).

## 3. Core concept

**Key idea:** track `dp[diff]` = the maximum height of the TALLER pillar, given that the two pillars currently differ by `diff` (where `diff = tallerHeight - shorterHeight`, always `>= 0`). For each rod, it can extend the taller pillar, extend the shorter pillar (possibly flipping which one is taller), or be left unused.

**Steps:**
1. Use a `Map<Integer, Integer>` for `dp`, since `diff` can range widely and most values are never reached — starting with `dp = {0: 0}` (zero rods used: pillars are equal, at height `0`).
2. For each rod `r` in `rods`: build a NEW map `newDp` as a copy of `dp` (representing "skip this rod").
3. For each existing `(diff, tallerHeight)` in `dp`: 
   - **Add `r` to the taller pillar:** new diff = `diff + r`, new tallerHeight = `tallerHeight + r`. Update `newDp[diff + r] = max(newDp.getOrDefault(diff+r, 0), tallerHeight + r)`.
   - **Add `r` to the shorter pillar:** the shorter pillar becomes `tallerHeight - diff + r`. If this exceeds `tallerHeight`, the pillars SWAP roles: new diff = `r - diff`, new tallerHeight = `tallerHeight - diff + r`. Otherwise: new diff = `diff - r`, new tallerHeight stays `tallerHeight`. Update `newDp` accordingly with the max.
4. Set `dp = newDp`. After all rods, return `dp.getOrDefault(0, 0)` — the tallest achievable height when the two pillars are EXACTLY equal (`diff = 0`).

**Why it is correct:** every rod has exactly 3 fates (unused, taller pillar, shorter pillar), and tracking the STATE as `(difference, taller height)` — rather than `(pillar A height, pillar B height)` separately — is sufficient, because the shorter pillar's height is always derivable as `tallerHeight - diff`. Using a hash map instead of an array is necessary because `diff` can range up to the sum of all rods, making a dense array wasteful when only a small fraction of possible differences are ever actually reachable.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="For a rod of length 3, three outcomes from a diff=2 taller=5 state: unused stays same, added to taller pillar increases diff, added to shorter pillar decreases or flips diff">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">state: diff=2, tallerHeight=5 (so pillars are 5 and 3); rod=3</text>
    <text x="10" y="45">unused: state stays (diff=2, taller=5)</text>
    <text x="10" y="65">add to taller pillar: new taller=5+3=8, diff=2+3=5 -&gt; (diff=5, taller=8)</text>
    <text x="10" y="85">add to shorter pillar: shorter becomes 3+3=6 &gt; taller(5) -&gt; SWAP -&gt; new taller=6, diff=6-5=1</text>
    <rect x="10" y="100" width="200" height="24" fill="#3fb950"/><text x="110" y="117" fill="#0d1117" text-anchor="middle" font-size="10">(diff=1, taller=6)</text>
  </g>
</svg>

Adding a rod to the shorter pillar can flip which pillar is "taller," so the state update must handle that swap.

## 5. Runnable example

```java
// TallestBillboard.java
import java.util.HashMap;
import java.util.Map;

public class TallestBillboard {

    // KEY INSIGHT: each rod has 3 fates (unused, taller pillar,
    // shorter pillar); tracking state as (difference, taller height)
    // is sufficient, since the shorter height is always
    // taller - diff -- a HashMap handles the sparse, wide range of
    // possible differences.

    static int tallestBillboard(int[] rods) {
        Map<Integer, Integer> dp = new HashMap<>();
        dp.put(0, 0);

        for (int rod : rods) {
            Map<Integer, Integer> newDp = new HashMap<>(dp);

            for (Map.Entry<Integer, Integer> entry : dp.entrySet()) {
                int diff = entry.getKey(), tallerHeight = entry.getValue();

                // add rod to the taller pillar
                int d1 = diff + rod, h1 = tallerHeight + rod;
                newDp.put(d1, Math.max(newDp.getOrDefault(d1, 0), h1));

                // add rod to the shorter pillar
                int shorterHeight = tallerHeight - diff + rod;
                int d2, h2;
                if (shorterHeight > tallerHeight) {
                    d2 = shorterHeight - tallerHeight;
                    h2 = shorterHeight;
                } else {
                    d2 = tallerHeight - shorterHeight;
                    h2 = tallerHeight;
                }
                newDp.put(d2, Math.max(newDp.getOrDefault(d2, 0), h2));
            }
            dp = newDp;
        }
        return dp.getOrDefault(0, 0);
    }

    public static void main(String[] args) {
        System.out.println(tallestBillboard(new int[]{1, 2, 3, 6}));
        // 6
        System.out.println(tallestBillboard(new int[]{1, 2, 3, 4, 5, 6}));
        // 10
    }
}
```

**How to run:** `java TallestBillboard.java`

## 6. Walkthrough

Trace the first two rods of `tallestBillboard([1,2,3,6])`:

| after rod | dp map (diff -&gt; tallerHeight) |
|---|---|
| start | {0: 0} |
| rod 1 | {0: 0 (unused), 1: 1 (rod1 on taller pillar)} |
| rod 2 | {0: 0, 1: 1, 2: 2 (rod2 alone), 3: 3 (rod1+rod2 same pillar), 1: 2 (rod1 vs rod2, diff=1,taller=2)} — map keeps the MAX height per diff, so diff=1 ends up storing max(1, 2) = 2 |

Continuing through rods `3` and `6` eventually reaches `dp[0] = 6` (pillars `[1,2,3]` and `[6]`, both height `6`). Time complexity is O(n · D), where `D` is the number of distinct differences reachable (bounded by the sum of all rods, but typically much smaller in practice). Space is O(D), for the hash map.

## 7. Gotchas & takeaways

> Gotcha: forgetting to handle the SWAP case (when adding a rod to the shorter pillar makes it taller than the previous "taller" pillar) silently produces an incorrect, always-non-negative-seeming `diff` that does not actually reflect which pillar is taller — always compare `shorterHeight` against `tallerHeight` explicitly, as shown, rather than assuming the taller pillar stays taller.

- The `(difference, tallerHeight)` state encoding is the key trick — it compresses "two independent pillar heights" into a state where only ONE value (`tallerHeight`) needs to be tracked per difference, since the other is always derivable.
- A `HashMap` (not a dense array) is essential here, unlike most 0/1 knapsack problems, because the difference dimension can be sparse relative to its full possible range.
- Related problems: Last Stone Weight II (a simpler 2-group difference-minimization problem, using a dense boolean array since the target range is small and known upfront), Target Sum (a related "each item has 2 fates" counting problem).
