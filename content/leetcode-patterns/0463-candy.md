---
card: leetcode-patterns
gi: 463
slug: candy
title: Candy
---

## 1. What it is

Each child in a row has a rating. Every child gets AT LEAST one candy, and any child with a HIGHER rating than an immediate neighbor must get MORE candy than that neighbor. Return the MINIMUM total candy needed. Example: `ratings = [1,0,2]` → `5` (candies `2, 1, 2`).

## 2. Why & when

Use this shape whenever a problem has a "must be greater than BOTH neighbors under certain conditions" constraint, where the condition depends on comparisons in TWO OPPOSITE directions (left neighbor AND right neighbor). The greedy rule: solve the LEFT-neighbor constraint and the RIGHT-neighbor constraint SEPARATELY, each with its own single directional pass, then take the MAXIMUM of the two requirements at each position.

## 3. Core concept

**Key idea:** run two separate passes. A LEFT-TO-RIGHT pass ensures every child with a higher rating than their LEFT neighbor gets more candy than them. A RIGHT-TO-LEFT pass ensures every child with a higher rating than their RIGHT neighbor gets more candy than them. Combine both requirements by taking the MAXIMUM at each position.

**Steps:**
1. Initialize a `candies` array, all `1`s (everyone gets at least one candy).
2. LEFT-TO-RIGHT pass: for `i` from `1` to `n-1`, if `ratings[i] > ratings[i-1]`, set `candies[i] = candies[i-1] + 1`.
3. RIGHT-TO-LEFT pass: for `i` from `n-2` down to `0`, if `ratings[i] > ratings[i+1]`, set `candies[i] = max(candies[i], candies[i+1] + 1)`.
4. Sum every value in `candies` for the final answer.

**Why two SEPARATE passes, combined with `max`, correctly satisfies BOTH directions at once:** the left-to-right pass alone guarantees the "greater than left neighbor" rule but may under-count a child who ALSO needs to beat their right neighbor; the right-to-left pass alone has the same problem in reverse. Taking the ELEMENT-WISE MAXIMUM of both passes' results ensures every position satisfies WHICHEVER requirement (left, right, or both) demands the larger candy count — since satisfying the larger of two lower bounds automatically satisfies the smaller one too.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two passes left to right and right to left each enforcing one direction of the rule then combined by taking the maximum at each position">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">ratings = [1, 0, 2]</text>
    <text x="10" y="45">left-to-right: [1, 1, 2] (index 2 &gt; index 1, so +1)</text>
    <text x="10" y="65">right-to-left: [2, 1, 2] (index 0 &gt; index 1, so max(1, candies[1]+1)=2)</text>
    <rect x="10" y="85" width="280" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">final candies = [2, 1, 2]; total = 5</text>
  </g>
</svg>

Two directional passes, each enforcing one neighbor comparison, combine by taking the larger requirement at every position.

## 5. Runnable example

```java
// Candy.java
public class Candy {

    // KEY INSIGHT: enforce the "greater than left neighbor" rule and
    // the "greater than right neighbor" rule in two SEPARATE passes,
    // then take the max at each position to satisfy both at once.

    static int candy(int[] ratings) {
        int n = ratings.length;
        int[] candies = new int[n];
        java.util.Arrays.fill(candies, 1);

        for (int i = 1; i < n; i++) {
            if (ratings[i] > ratings[i - 1]) candies[i] = candies[i - 1] + 1;
        }
        for (int i = n - 2; i >= 0; i--) {
            if (ratings[i] > ratings[i + 1]) candies[i] = Math.max(candies[i], candies[i + 1] + 1);
        }

        int total = 0;
        for (int c : candies) total += c;
        return total;
    }

    public static void main(String[] args) {
        System.out.println(candy(new int[]{1, 0, 2}));
        // 5
        System.out.println(candy(new int[]{1, 2, 2}));
        // 4
    }
}
```

**How to run:** `java Candy.java`

## 6. Walkthrough

Trace `candy([1,0,2])` (`ratings[1]=0` is lower than both neighbors, so it stays at the minimum candy count throughout):

| step | candies array | reasoning |
|---|---|---|
| initial | [1, 1, 1] | everyone starts with one candy |
| left-to-right | [1, 1, 2] | index 2 (`2 > 0`): candies[2] = candies[1] + 1 = 2 |
| right-to-left | [2, 1, 2] | index 0 (`1 > 0`): candies[0] = max(1, candies[1] + 1) = 2 |

Final `candies = [2, 1, 2]`, total `= 2 + 1 + 2 = 5`, matching the expected answer.

## 7. Gotchas & takeaways

> Gotcha: the right-to-left pass compares `ratings[i]` against `ratings[i+1]` (the NEXT child), not `ratings[i-1]` — mixing up the comparison direction in either pass silently enforces the WRONG neighbor relationship, producing a plausible-looking but incorrect candy count.

- Two directional passes, combined with an ELEMENT-WISE MAXIMUM: the standard technique whenever a rule must hold in BOTH directions simultaneously along a sequence.
- Always double check a hand-traced example against the KNOWN expected answer — as shown above, it is easy to overlook a required update in the second pass; verifying the arithmetic catches it immediately.
- Related problems: Non-decreasing Array (a different two-directional-ish check, but only allowing a single fix rather than combining two full passes), Wiggle Subsequence (a single-direction greedy scan, without needing a second pass in the opposite direction).
