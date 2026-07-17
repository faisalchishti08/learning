---
card: leetcode-patterns
gi: 41
slug: grumpy-bookstore-owner
title: Grumpy Bookstore Owner
---

## 1. What it is

A bookstore has `customers[i]` customers arriving in minute `i`, and `grumpy[i]` is `1` if the owner is grumpy that minute (those customers are unsatisfied) or `0` if not. The owner can use a "secret technique" to stay not-grumpy for `minutes` consecutive minutes, usable once. Return the maximum number of satisfied customers possible. Example: `customers = [1,0,1,2,1,1,7,5]`, `grumpy = [0,1,0,1,0,1,0,1]`, `minutes = 3` → answer `16`.

## 2. Why & when

The customers already satisfied (when `grumpy[i] == 0`) are a fixed baseline. The technique's value is the number of *additional* customers it can save — those in the grumpy minutes it covers. Finding the best `minutes`-length window to place the technique, to maximize the sum of customers it saves, is a fixed-size sliding window maximization.

## 3. Core concept

**Key idea:** split the problem into two independent parts — a guaranteed baseline (customers satisfied without any technique) and a bonus (extra customers saved by placing the technique optimally) — then find the best fixed-size window for the bonus.

**Steps:**
1. Compute `baseline`: the sum of `customers[i]` for every `i` where `grumpy[i] == 0`.
2. Compute the "grumpy-only" array conceptually: `extra[i] = customers[i]` if `grumpy[i] == 1`, else `0`.
3. Slide a fixed-size window of length `minutes` across `extra`, tracking its sum, to find the maximum sum achievable — this is exactly Maximum Average Subarray I's fixed-window-sum technique, without the final division.
4. Return `baseline + maxWindowSum`.

**Why it is correct:** the baseline is unaffected by where the technique is placed, since it only counts already-satisfied customers. The technique's benefit is additive and localized: it only helps during grumpy minutes it covers, and only those minutes' customer counts contribute extra satisfaction. Maximizing the sum of a fixed-length window over the grumpy-only array is exactly the amount of bonus the best placement achieves.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Grumpy bookstore owner window sliding over grumpy minutes">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">customers = [1,0,1,2,1,1,7,5], grumpy=[0,1,0,1,0,1,0,1], minutes=3</text>
    <text x="20" y="55" fill="#8b949e">baseline (grumpy=0 minutes): 1 + 1 + 1 + 7 = 10</text>
    <text x="20" y="80" fill="#8b949e">extra (grumpy=1 minutes only): [0,0,0,2,0,1,0,5]</text>
    <text x="20" y="105" fill="#79c0ff">best window of length 3 in extra: [1,0,5] sum=6 (indices 5-7)</text>
    <text x="20" y="130" fill="#f0883e">answer = baseline(10) + bonus(6) = 16</text>
  </g>
</svg>

Splitting into a fixed baseline plus a fixed-size window search over the "grumpy-only" values isolates the technique's placement decision.

## 5. Runnable example

```java
// GrumpyBookstoreOwner.java
public class GrumpyBookstoreOwner {

    // Level 1 -- Brute force: try every possible starting minute for the
    // technique, recomputing satisfied customers from scratch each time.
    // O(n * minutes) time, O(1) space.
    static int bruteForce(int[] customers, int[] grumpy, int minutes) {
        int n = customers.length, best = 0;
        for (int start = 0; start + minutes <= n; start++) {
            int total = 0;
            for (int i = 0; i < n; i++) {
                boolean covered = i >= start && i < start + minutes;
                if (grumpy[i] == 0 || covered) total += customers[i];
            }
            best = Math.max(best, total);
        }
        return best;
    }

    // KEY INSIGHT: split into a fixed baseline (already-satisfied
    // customers) plus a fixed-size window search for the best placement of
    // the technique over the grumpy-only customer counts.

    // Level 2 -- Optimal: baseline + fixed-size sliding window. O(n) time,
    // O(1) space.
    public static int maxSatisfied(int[] customers, int[] grumpy, int minutes) {
        int n = customers.length;
        int baseline = 0;
        for (int i = 0; i < n; i++) {
            if (grumpy[i] == 0) baseline += customers[i];
        }

        int windowBonus = 0;
        for (int i = 0; i < minutes; i++) {
            if (grumpy[i] == 1) windowBonus += customers[i];
        }
        int bestBonus = windowBonus;
        for (int i = minutes; i < n; i++) {
            if (grumpy[i] == 1) windowBonus += customers[i];
            if (grumpy[i - minutes] == 1) windowBonus -= customers[i - minutes];
            bestBonus = Math.max(bestBonus, windowBonus);
        }

        return baseline + bestBonus;
    }

    // Level 3 -- Hardened: minutes >= array length means the technique
    // covers everything -- the single window IS the whole array, and the
    // second loop never runs.
    static int hardened(int[] customers, int[] grumpy, int minutes) {
        if (customers == null || grumpy == null || customers.length != grumpy.length) {
            throw new IllegalArgumentException("customers and grumpy must have matching length");
        }
        return maxSatisfied(customers, grumpy, minutes);
    }

    public static void main(String[] args) {
        int[] customers = {1, 0, 1, 2, 1, 1, 7, 5};
        int[] grumpy = {0, 1, 0, 1, 0, 1, 0, 1};
        System.out.println("brute force: " + bruteForce(customers, grumpy, 3));
        System.out.println("optimal:     " + maxSatisfied(customers, grumpy, 3));
        System.out.println("minutes==n:  " + hardened(customers, grumpy, 8));
    }
}
```

How to run: save as `GrumpyBookstoreOwner.java`, then run `java GrumpyBookstoreOwner.java`.

## 6. Walkthrough

Dry run of `maxSatisfied` on the example, after computing `baseline = 10`:

| step | window (indices) | grumpy-only sum | bestBonus |
|---|---|---|---|
| init (0-2) | [0,1,2] | grumpy[1]=1 contributes 0 | 0 |
| i=3 | [1,2,3] | add grumpy[3]=1 (customers=2), remove grumpy[0]=0 (nothing) -> 2 | 2 |
| i=4 | [2,3,4] | remove grumpy[1]=1 (0) -> still 2 | 2 |
| i=5 | [3,4,5] | add grumpy[5]=1 (1), remove grumpy[2]=0 (nothing) -> 3 | 3 |
| i=6 | [4,5,6] | remove grumpy[3]=1 (2) -> 1 | 3 |
| i=7 | [5,6,7] | add grumpy[7]=1 (5), remove grumpy[4]=0 (nothing) -> 6 | 6 |

Final `bestBonus = 6`. Answer: `baseline(10) + bestBonus(6) = 16`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to check `grumpy[i] == 1` when adding/removing from the window sum would count already-satisfied customers as "bonus," double-counting them with the baseline.

- Splitting a problem into a fixed baseline plus an optimizable window is a reusable decomposition whenever part of the answer does not depend on the choice being optimized.
- Related problems: Maximum Average Subarray I, Maximum Points You Can Obtain from Cards (similar "fixed removable window" framing).
