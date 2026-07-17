---
card: leetcode-patterns
gi: 25
slug: bag-of-tokens
title: Bag of Tokens
---

## 1. What it is

You have `power` starting energy and an array `tokens`. For each token, you may either play it face-up, spending `power` equal to `tokens[i]` to gain 1 score, or play it face-down, gaining `power` equal to `tokens[i]` but losing 1 score (only allowed if score is at least 1). Each token can be used once. Return the maximum score achievable. Example: `tokens = [100, 200, 300, 400]`, `power = 200` → answer `2`.

## 2. Why & when

To maximize score, you want to spend power on the *cheapest* tokens (face-up) and only cash in the *most expensive* tokens for power (face-down) when you are stuck and need more power to keep playing. Sorting the tokens, then greedily working from both ends with opposite-ends two pointers, implements exactly that strategy.

## 3. Core concept

**Key idea:** greedily play the cheapest available token face-up whenever you can afford it (this is always at least as good as playing a pricier one, since it gains the same +1 score for less power spent); when you cannot afford any remaining token, sacrifice the most expensive one face-down to refuel, if you have score to spare.

**Steps:**
1. Sort `tokens`. Set `left = 0`, `right = tokens.length - 1`, `score = 0`, `best = 0`.
2. While `left <= right`:
   - If `power >= tokens[left]`, play it face-up: `power -= tokens[left]`, `score++`, `left++`. Update `best = max(best, score)`.
   - Else if `score > 0`, play the most expensive token face-down: `power += tokens[right]`, `score--`, `right--`.
   - Else (cannot afford the cheapest, and no score to sacrifice), stop — no further moves help.
3. Return `best`.

**Why it is correct:** playing the cheapest affordable token face-up is never worse than any other face-up choice — you always gain the same +1 score, and using less power leaves more power for later. Symmetrically, if you must play a token face-down to keep going, sacrificing the most expensive one recovers the most power per point of score lost. Tracking `best` (not just the final `score`) matters because it is sometimes optimal to stop before using every token.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bag of tokens greedy two pointers">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">sorted tokens = [100, 200, 300, 400], power = 200</text>
    <rect x="20" y="40" width="50" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="70" y="40" width="50" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="50" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="40" width="50" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="45" y="60" fill="#e6edf3" text-anchor="middle">100</text>
    <text x="95" y="60" fill="#e6edf3" text-anchor="middle">200</text>
    <text x="145" y="60" fill="#e6edf3" text-anchor="middle">300</text>
    <text x="195" y="60" fill="#e6edf3" text-anchor="middle">400</text>
    <text x="20" y="95" fill="#8b949e">power(200) &gt;= tokens[left](100) -&gt; play face-up: power=100, score=1</text>
    <text x="20" y="118" fill="#8b949e">power(100) &lt; tokens[left](200) -&gt; play face-down 400: power=500, score=0</text>
  </g>
</svg>

Cheap tokens are spent on for score; when power runs out, the priciest remaining token is cashed in to refuel.

## 5. Runnable example

```java
// BagOfTokens.java
import java.util.Arrays;

public class BagOfTokens {

    // Level 1 -- Brute force: try every subset/order of play choices with
    // recursion (exponential). Shown conceptually; not run on large input
    // here, to keep the contrast with the greedy two-pointer solution clear.
    static int bruteForceSmall(int[] tokens, int power) {
        return recurse(tokens, 0, tokens.length - 1, power, 0);
    }

    private static int recurse(int[] tokens, int left, int right, int power, int score) {
        if (left > right) return score;
        int best = score;
        if (power >= tokens[left]) {
            best = Math.max(best, recurse(tokens, left + 1, right, power - tokens[left], score + 1));
        }
        if (score > 0) {
            best = Math.max(best, recurse(tokens, left, right - 1, power + tokens[right], score - 1));
        }
        return best;
    }

    // KEY INSIGHT: sorting first turns the greedy "cheapest token for
    // score, priciest token for power" strategy into a simple opposite-ends
    // two-pointer scan, with no need to search all play orders.

    // Level 2 -- Optimal: sort + two pointers, greedy. O(n log n) time,
    // O(1) extra space.
    public static int bagOfTokensScore(int[] tokens, int power) {
        Arrays.sort(tokens);
        int left = 0, right = tokens.length - 1;
        int score = 0, best = 0;
        while (left <= right) {
            if (power >= tokens[left]) {
                power -= tokens[left];
                score++;
                left++;
                best = Math.max(best, score);
            } else if (score > 0) {
                power += tokens[right];
                score--;
                right--;
            } else {
                break;
            }
        }
        return best;
    }

    // Level 3 -- Hardened: power too small to afford even the cheapest
    // token, and score is 0, breaks out of the loop immediately, correctly
    // returning 0.
    static int hardened(int[] tokens, int power) {
        if (tokens == null || tokens.length == 0) return 0;
        return bagOfTokensScore(tokens, power);
    }

    public static void main(String[] args) {
        int[] tokens = {100, 200, 300, 400};
        System.out.println("optimal: " + bagOfTokensScore(tokens, 200));
        System.out.println("too little power: " + hardened(new int[] {50}, 10));
    }
}
```

How to run: save as `BagOfTokens.java`, then run `java BagOfTokens.java`.

## 6. Walkthrough

Dry run of `bagOfTokensScore({100, 200, 300, 400}, power = 200)`:

| step | left | right | power | condition | action | score | best |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 3 | 200 | 200 >= 100 | play up, power=100, left=1 | 1 | 1 |
| 2 | 1 | 3 | 100 | 100 < 200, score>0 | play down 400, power=500, right=2 | 0 | 1 |
| 3 | 1 | 2 | 500 | 500 >= 200 | play up, power=300, left=2 | 1 | 1 |
| 4 | 2 | 2 | 300 | 300 >= 300 | play up, power=0, left=3 | 2 | 2 |
| 5 | 3 | 2 | — | left > right | loop ends | — | — |

Final answer: `2`, matching the expected result. Time complexity: O(n log n), dominated by the sort. Space complexity: O(1) extra.

## 7. Gotchas & takeaways

> Gotcha: forgetting to track `best` separately from the final `score` is a common bug — the greedy scan can pass through a score that later drops (from a face-down play used only to survive), so the maximum must be captured the moment it is reached, not read at the end.

- This greedy-plus-two-pointers shape also appears in scheduling and resource-allocation problems: sort by cost, then trade cheap gains against expensive refuels from both ends.
- Related problems: Boats to Save People (a simpler greedy pairing, no refuel step), Candy, Jump Game II.
