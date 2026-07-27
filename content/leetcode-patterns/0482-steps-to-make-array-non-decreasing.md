---
card: leetcode-patterns
gi: 482
slug: steps-to-make-array-non-decreasing
title: Steps to Make Array Non-decreasing
---

## 1. What it is

In one step, look at the array as it currently stands and remove every element `nums[i]` whose immediately preceding element (in that same, current array) is strictly greater than it — that is, remove `nums[i]` wherever `nums[i - 1] > nums[i]`. All such removals in a round happen at once, based on the array as it looked at the start of that round. Repeat rounds until no more removals happen. Return the total number of rounds. Example: `nums = [5, 3, 4, 4, 7, 3, 6, 11, 8, 5, 11]` → `3`.

## 2. Why & when

Each round only removes an element if its immediate left neighbor (in the current round) beats it — not any earlier element in the whole array. That distinction matters: a small element can "shield" a bigger one for a few rounds, until every smaller element between them has been cleared away and the bigger one finally becomes the immediate left neighbor. Counting how many rounds that shielding takes, for every element, is answered by a decreasing monotonic stack from the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family, where each stack entry also stores its own removal-round number. Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** scan left to right with a decreasing stack of `(value, roundRemoved)` pairs. When the current value is bigger than or equal to the stack's top, that top will be removed once it becomes adjacent to a bigger value — but the current value cannot be that "final blow" until every smaller element already shielding the top is also cleared. So the current element absorbs (pops) every smaller-or-equal entry, and its own removal round becomes one more than the **latest** round among everything it just absorbed (because it must wait for the slowest of those absorbed elements to clear first).

**Steps:**
1. Maintain a stack of `(value, roundRemoved)` pairs, where `roundRemoved` is the round in which this element gets removed (0 if it is never removed).
2. For each new value `num`: track `maxRoundPopped = 0`. While the stack is not empty and its top's value is less than or equal to `num`, pop it and update `maxRoundPopped = max(maxRoundPopped, poppedRound)`.
3. After the pops, if the stack still has an element left (necessarily bigger than `num`, since the stack stays decreasing), `num` will eventually be removed by it — but only once every absorbed element is gone, so `num`'s own round is `maxRoundPopped + 1`.
4. If the stack is empty after the pops, `num` is never removed — it becomes a new "wall" with `roundRemoved = 0`.
5. Push `(num, roundRemoved)`. The answer is the maximum `roundRemoved` seen across every element, since the whole array stabilizes only once the slowest-clearing element is finally gone.

**Why the round number can exceed 1:** an element is only removed once its immediate left neighbor is bigger. If several small elements sit between it and the actual bigger element, each of those small elements must be cleared first — one round at a time — before the bigger element becomes adjacent and finally removes it.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decreasing stack of value-round pairs where popped rounds compose into a later round for the current element">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [5, 3, 4, 4, 7, ...]</text>
    <text x="20" y="45" fill="#8b949e">5: stack empty -&gt; round=0. push (5,0). stack=[(5,0)]</text>
    <text x="20" y="65" fill="#8b949e">3: 5&gt;3, no pop. stack not empty -&gt; round=0+1=1. push (3,1). stack=[(5,0),(3,1)]</text>
    <text x="20" y="85" fill="#8b949e">4: pop (3,1) since 3&lt;=4 -&gt; maxPopped=1. stack has (5,0) left -&gt; round=1+1=2. stack=[(5,0),(4,2)]</text>
    <text x="20" y="105" fill="#8b949e">4: pop (4,2) since 4&lt;=4 -&gt; maxPopped=2. stack has (5,0) left -&gt; round=2+1=3. stack=[(5,0),(4,3)]</text>
    <text x="20" y="130" fill="#3fb950">7: pop (4,3) and (5,0) -&gt; maxPopped=3. stack now empty -&gt; round=0 (7 is a new wall). running max = 3</text>
  </g>
</svg>

Each absorbed element's own round contributes to how long the current element must wait to be exposed and finally removed.

## 5. Runnable example

**Level 1 — Brute force.** Simulate round by round: in each round, scan the current array and remove every element whose immediate left neighbor (from that same round) is bigger, based on the array as it stood at the round's start. Repeat until a round removes nothing. O(n²) worst case.

**KEY INSIGHT:** the round in which an element is finally removed equals one more than the latest round among every smaller element it must wait to see cleared first — a decreasing stack of `(value, roundRemoved)` computes this for every element in a single O(n) pass.

**Level 2 — Optimal.** Single-pass decreasing stack of `(value, roundRemoved)` pairs with a running maximum, O(n).

**Level 3 — Hardened.** Handles an already non-decreasing array (answer `0`) and a strictly decreasing array (every element but the first is removed in round 1).

```java
// StepsToMakeArrayNonDecreasing.java
import java.util.*;

public class StepsToMakeArrayNonDecreasing {

    // Level 1: brute force, simulating round by round, O(n^2) worst case
    static int bruteForce(int[] nums) {
        List<Integer> list = new ArrayList<>();
        for (int n : nums) list.add(n);
        int rounds = 0;
        while (true) {
            List<Integer> next = new ArrayList<>();
            boolean removedAny = false;
            for (int i = 0; i < list.size(); i++) {
                if (i > 0 && list.get(i - 1) > list.get(i)) {
                    removedAny = true; // this round's immediate left neighbor beats it
                } else {
                    next.add(list.get(i));
                }
            }
            if (!removedAny) break;
            list = next;
            rounds++;
        }
        return rounds;
    }

    // Level 2 & 3: monotonic stack of (value, roundRemoved), O(n)
    static int totalSteps(int[] nums) {
        Deque<int[]> stack = new ArrayDeque<>(); // {value, roundRemoved}
        int answer = 0;

        for (int num : nums) {
            int maxRoundPopped = 0;
            while (!stack.isEmpty() && stack.peek()[0] <= num) {
                maxRoundPopped = Math.max(maxRoundPopped, stack.pop()[1]);
            }
            int round = stack.isEmpty() ? 0 : maxRoundPopped + 1;
            stack.push(new int[]{num, round});
            answer = Math.max(answer, round);
        }
        return answer;
    }

    public static void main(String[] args) {
        int[] nums = {5, 3, 4, 4, 7, 3, 6, 11, 8, 5, 11};
        System.out.println("brute force: " + bruteForce(nums));
        System.out.println("optimal:     " + totalSteps(nums));

        System.out.println("already sorted: " + totalSteps(new int[]{1, 2, 3, 4}));
        System.out.println("strictly decreasing: " + totalSteps(new int[]{5, 4, 3, 2, 1}));
    }
}
```

**How to run:** save as `StepsToMakeArrayNonDecreasing.java`, then run `java StepsToMakeArrayNonDecreasing.java`.

## 6. Walkthrough

Trace `totalSteps({5, 3, 4, 4, 7, 3, 6, 11, 8, 5, 11})`:

| num | stack before | pops | maxRoundPopped | round assigned | stack after |
|---|---|---|---|---|---|
| 5 | [] | none | 0 | 0 (stack empty) | [(5,0)] |
| 3 | [(5,0)] | none (5 not <= 3) | 0 | 0+1=1 (stack has (5,0) left) | [(5,0),(3,1)] |
| 4 | [(5,0),(3,1)] | pop (3,1) | 1 | 1+1=2 | [(5,0),(4,2)] |
| 4 | [(5,0),(4,2)] | pop (4,2) | 2 | 2+1=3 | [(5,0),(4,3)] |
| 7 | [(5,0),(4,3)] | pop (4,3), pop (5,0) | 3 | stack empty -> 0 | [(7,0)] |
| 3 | [(7,0)] | none | 0 | 0+1=1 | [(7,0),(3,1)] |
| 6 | [(7,0),(3,1)] | pop (3,1) | 1 | 1+1=2 | [(7,0),(6,2)] |
| 11 | [(7,0),(6,2)] | pop (6,2), pop (7,0) | 2 | stack empty -> 0 | [(11,0)] |
| 8 | [(11,0)] | none | 0 | 0+1=1 | [(11,0),(8,1)] |
| 5 | [(11,0),(8,1)] | none (8 not <= 5) | 0 | 0+1=1 | [(11,0),(8,1),(5,1)] |
| 11 | [(11,0),(8,1),(5,1)] | pop (5,1), pop (8,1), pop old (11,0) | 1 | stack empty -> 0 | [(11,0)] |

The running maximum round assigned across the whole scan is `3` (reached at the second `4`), matching the expected number of rounds.

## 7. Gotchas & takeaways

> Gotcha: assigning `round = maxRoundPopped + 1` even when the stack is empty after popping is wrong — an element with nothing bigger left on the stack is never removed (it becomes a new non-decreasing "wall"), so its own round must be `0`, not `maxRoundPopped + 1`.

- The removal rule compares only to the *immediate* left neighbor within the current round, not to any earlier element in the whole array — small elements shield a bigger one for several rounds until they are all cleared.
- The final answer is the maximum round value seen across the whole scan, not the value on the last stack entry.
- Time: O(n) — same amortized push/pop bound as any monotonic-stack pattern.
