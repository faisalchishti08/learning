---
card: leetcode-patterns
gi: 444
slug: greedy-template-sort-or-use-a-heap-then-commit-greedily-with
title: "Greedy — template: sort or use a heap, then commit greedily with an exchange argument"
---

## 1. What it is

This page gives the general recipe for building a greedy solution: put the input in the RIGHT ORDER (usually via sorting, sometimes via a heap for a dynamically-changing "best remaining option"), then scan once, committing immediately to whatever the local rule picks.

## 2. Why & when

Use this recipe any time you suspect a problem is greedy-solvable: figure out what ORDER to process items in (this is usually the hardest and most important decision), define the LOCAL rule for each step, and mentally check the exchange argument before trusting it.

## 3. Core concept

**Step 1 — choose the processing order.** Many greedy problems become solvable only after a SPECIFIC sort: by size (Assign Cookies), by position (Jump Game), by height then position (Queue Reconstruction), or not sorted at all but scanned in original left-to-right order (Gas Station, Can Place Flowers). A HEAP is used instead of a plain sort when the "best remaining option" changes dynamically as you make choices (not needed by any problem in this specific section, but common in scheduling-style greedy problems).

**Step 2 — define the local rule.** At each step, state EXACTLY what "the best available choice" means: the smallest sufficient cookie, the farthest reachable index, whether the running gas balance ever goes negative, or which existing position to insert a new taller/shorter person into.

**Step 3 — sanity-check with an exchange argument.** Ask: "if some other valid solution made a DIFFERENT choice than my rule at this step, could I always swap it for my rule's choice without making things worse?" If yes, every step, the greedy rule is trustworthy — commit to it, in a single pass, with no revisiting.

**Step 4 — implement as a single pass (plus the initial sort/heap-build).** Once the order and rule are settled, the actual code is almost always a simple loop, tracking one or two running values, updating a count, or inserting into a structure.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="four step recipe choose order define rule check exchange argument then single pass implementation">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">1. choose order (sort/heap) -&gt; 2. define local rule -&gt; 3. check exchange argument</text>
    <text x="10" y="45" font-weight="bold">4. implement as one pass, committing immediately at each step</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">the ORDER is usually the hardest and most important decision</text>
  </g>
</svg>

Choosing the right processing order is usually the single hardest part of building a correct greedy solution.

## 5. Runnable example

```java
// GreedyTemplate.java
import java.util.Arrays;

public class GreedyTemplate {

    // General template applied to Jump Game: no sort needed here (the
    // "order" is simply left to right), local rule is "track the
    // farthest reachable index," single pass, no backtracking.
    static boolean canJump(int[] nums) {
        int farthestReachable = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > farthestReachable) return false; // this position is unreachable
            farthestReachable = Math.max(farthestReachable, i + nums[i]);
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(canJump(new int[]{2, 3, 1, 1, 4}));
        // true
        System.out.println(canJump(new int[]{3, 2, 1, 0, 4}));
        // false
    }
}
```

**How to run:** `java GreedyTemplate.java`

## 6. Walkthrough

1. Order: left to right, the natural order of the array — no sort needed for this particular problem.
2. Local rule: at each index, track the FARTHEST index reachable so far; if the CURRENT index ever exceeds that farthest reach, the end is unreachable.
3. Exchange argument: if some path reaches index `i` using fewer jumps than the greedy "always extend the farthest reach" rule tracks, that path's reach is still bounded by the SAME formula (`i + nums[i]`) — the greedy running maximum captures every possible path's best reach implicitly, so no alternative path could ever reach further than what is already tracked.
4. Single pass: `canJump` never revisits an earlier index or backtracks — it commits to updating `farthestReachable` once per index and moves on.
5. This same four-step process, with a different order and a different local rule, produces every other solution in this section.

## 7. Gotchas & takeaways

> Gotcha: skipping the exchange-argument sanity check and just "trying a greedy idea that feels right" is how most WRONG greedy solutions happen — always be able to state, in one sentence, WHY no other choice could ever beat the one your rule makes.

- The four-step recipe (order, rule, exchange argument, single pass) applies to every problem in this section — only the specific order and rule change.
- Sorting is the most common way to establish a usable order; a running single value (reach, balance, count) is the most common form the local rule takes.
- If you cannot articulate an exchange argument for why the greedy choice is safe, the problem likely needs DP (comparing multiple future-dependent options) instead of a greedy shortcut.
