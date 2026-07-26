---
card: leetcode-patterns
gi: 443
slug: greedy-signal-a-locally-optimal-choice-yields-a-global-optim
title: "Greedy — signal: a locally optimal choice yields a global optimum"
---

## 1. What it is

Greedy is the pattern for problems where making the BEST choice available RIGHT NOW, at every step, and never revisiting that choice, still produces the overall best answer. Think of handing out the smallest cookie that still satisfies a child, one child at a time — no lookahead, no backtracking, just committing to whatever locally looks best and moving on.

## 2. Why & when

Reach for this pattern whenever a problem asks for an optimal count, arrangement, or feasibility check, and a SIMPLE, LOCAL rule (sort first, or scan left to right making one obvious choice per step) turns out to already guarantee the global optimum — no DP table, no trying multiple options and comparing, is needed. The catch: not every optimization problem is greedy-solvable; the whole skill is recognizing WHEN a greedy choice is provably safe.

Learn to recognize these signals in a problem statement:

- **"Satisfy as many children as possible, matching the smallest possible cookie to each"** — a matching problem where sorting both sides first makes the smallest-fits-smallest greedy choice provably optimal.
- **"Can you reach the end, jumping at most `nums[i]` steps from position `i`?"** — a reachability problem, where tracking the farthest reachable position greedily, without trying every path, suffices.
- **"Find the starting gas station that lets you complete a circuit"** — a feasibility problem where a running total, reset only when it goes negative, greedily finds the answer.
- **"Rearrange people by height so each one's position matches how many taller people are in front of them"** — an insertion-based greedy, where processing in the RIGHT ORDER (tallest first) makes each insertion locally correct and permanently final.

The alternative — trying every possible choice at each step and comparing (i.e. full DP or brute-force search) — is always CORRECT but often unnecessary, and typically slower. Greedy is a strictly cheaper tool whenever it applies, but using it on a problem where it does NOT apply produces confidently wrong answers.

## 3. Core concept

Every greedy problem reduces to the SAME two-part justification, even though the specific "rule" changes per problem:

**The rule.** A simple, local decision procedure — usually "process items in a specific SORTED order, then take the best available option at each step" or "scan once, tracking a single running value (a reach, a balance, a count) and updating it greedily."

**The proof obligation (the EXCHANGE ARGUMENT).** To trust a greedy rule, you must be able to argue: "if an optimal solution did something DIFFERENT from what my greedy rule chooses, I could SWAP that choice for the greedy one without making the solution any worse." If this swap-and-compare argument holds for every step, the greedy rule is safe to use everywhere, without ever needing to check the other option.

**Why greedy works when it works:** the exchange argument proves that no OTHER choice could ever have been STRICTLY better than the greedy one — so committing to the greedy choice immediately, and never revisiting it, cannot lose any potential optimality versus exploring every alternative.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a sequence of local decisions each committed to immediately without ever revisiting a previous choice">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">step 1: pick locally best -&gt; step 2: pick locally best -&gt; step 3: ...</text>
    <rect x="10" y="40" width="90" height="26" fill="#3fb950"/><text x="55" y="58" text-anchor="middle" font-size="10" fill="#0d1117">committed</text>
    <rect x="110" y="40" width="90" height="26" fill="#3fb950"/><text x="155" y="58" text-anchor="middle" font-size="10" fill="#0d1117">committed</text>
    <rect x="210" y="40" width="90" height="26" fill="#3fb950"/><text x="255" y="58" text-anchor="middle" font-size="10" fill="#0d1117">committed</text>
    <rect x="10" y="80" width="300" height="24" fill="#3fb950"/><text x="160" y="97" fill="#0d1117" text-anchor="middle" font-size="10">no choice is ever revisited or compared against later</text>
  </g>
</svg>

Each step's choice is made once, locally, and never revisited — no backtracking, no comparison table.

## 5. Runnable example

```java
// GreedySignal.java
import java.util.Arrays;

public class GreedySignal {

    // Signal check: matching problem, sort both sides, take the
    // smallest sufficient option greedily.
    static int findContentChildren(int[] greed, int[] cookies) {
        Arrays.sort(greed);
        Arrays.sort(cookies);
        int child = 0, cookie = 0;
        while (child < greed.length && cookie < cookies.length) {
            if (cookies[cookie] >= greed[child]) child++;
            cookie++;
        }
        return child;
    }

    public static void main(String[] args) {
        System.out.println(findContentChildren(new int[]{1, 2, 3}, new int[]{1, 1}));
        // 1
    }
}
```

**How to run:** `java GreedySignal.java`

## 6. Walkthrough

1. You read a problem statement. "Satisfy as many as possible," "can you reach the end," "find a feasible starting point," or "rearrange by a property" are all potential greedy signals.
2. Running `findContentChildren([1,2,3], [1,1])` confirms only `1` child can be satisfied: the smallest cookie (`1`) satisfies the least-greedy child (needs `1`), but the second cookie (`1`) is too small for any remaining child (needs `2` or `3`).
3. Sorting BOTH arrays first is what makes the greedy "take the smallest sufficient cookie" rule provably optimal — matching a bigger cookie to a small need would only waste capacity that a bigger need could have used.
4. If the problem instead needed a REACHABILITY check (like Jump Game), the greedy rule would track a single running "farthest reachable position" instead of matching two sorted arrays — a different rule, but the same "one pass, no backtracking" shape.
5. This upfront classification (matching, reachability, feasibility-by-running-total, or order-dependent insertion) tells you which specific greedy rule the next page's template applies.

## 7. Gotchas & takeaways

> Gotcha: greedy is NOT a universal tool — it only works when an exchange argument actually holds. Applying a greedy shortcut to a problem that secretly needs to compare multiple future-dependent options (many interval-DP or knapsack-style problems) produces a wrong, but confident-looking, answer.

- The two-part justification — a simple local rule, plus an exchange argument proving no alternative choice ever beats it — is what separates a CORRECT greedy solution from a convenient-looking guess.
- Sorting first is one of the most common ways to make a greedy rule valid: it reorders the input so the "obviously correct" local choice is always available at each step.
- Tracking a single running value (a reach, a balance, a count) as you scan once is the OTHER common greedy shape, used for reachability and feasibility problems.
