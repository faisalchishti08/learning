---
card: leetcode-patterns
gi: 453
slug: dota2-senate
title: Dota2 Senate
---

## 1. What it is

Senators from two parties, Radiant (`R`) and Dire (`D`), vote in ROUNDS, in the given order. On each senator's turn, they may BAN one senator from the OTHER party (removing them from all future rounds). This repeats until only one party remains. Return which party wins. Example: `senate = "RD"` → `"Radiant"`.

## 2. Why & when

Use this shape whenever a problem describes a TURN-BASED elimination process where each participant, acting optimally (or by a fixed simple rule), removes an opponent to maximize their own side's chances. The greedy rule: each senator should ban the OPPONENT WHO WOULD ACT SOONEST — the most immediate threat — since eliminating a later threat leaves an earlier, more urgent one still able to act first.

## 3. Core concept

**Key idea:** simulate the voting using two QUEUES, one per party, storing the ORIGINAL INDEX of each senator. Repeatedly compare the FRONT of both queues (whichever senator's turn comes first); that senator bans the other, and REJOINS the back of their own queue, shifted forward by `n` (the total senator count) — this models "their next turn happens in the NEXT round."

**Steps:**
1. Fill a `radiant` queue and a `dire` queue with the ORIGINAL indices of each party's senators, in order.
2. While both queues are non-empty: pop the FRONT of each queue, `r` and `d`. Whichever index is SMALLER acts first and bans the other: if `r < d`, Radiant survives and rejoins with index `r + n`; otherwise Dire survives and rejoins with index `d + n`.
3. Once one queue is empty, the OTHER party has won.

**Why comparing indices (with the `+ n` re-queuing trick) correctly simulates the turn order across MULTIPLE rounds:** adding `n` to a surviving senator's index preserves their RELATIVE turn order versus everyone else's future turns — a senator who just acted will naturally be compared against opponents from LATER in the current round, or from the NEXT round, exactly as if the voting had genuinely continued round after round, without needing to explicitly simulate separate "rounds" as distinct phases.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two queues comparing their front elements the smaller index acts first banning the other and rejoining with index plus n">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">senate = "RD" (n=2) -- radiant=[0], dire=[1]</text>
    <text x="10" y="45">compare fronts: r=0, d=1 -- r &lt; d, so Radiant (0) bans Dire (1)</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">radiant re-queues as 0+2=2; dire queue now empty -- Radiant wins</text>
  </g>
</svg>

Comparing the two queues' front indices, and re-queuing the survivor `n` positions later, simulates every future round without an explicit round-by-round loop.

## 5. Runnable example

```java
// Dota2Senate.java
import java.util.LinkedList;
import java.util.Queue;

public class Dota2Senate {

    // KEY INSIGHT: the senator whose turn comes SOONEST bans the
    // other -- re-queuing the survivor at index+n correctly models
    // their next turn happening one full round later.

    static String predictPartyVictory(String senate) {
        int n = senate.length();
        Queue<Integer> radiant = new LinkedList<>();
        Queue<Integer> dire = new LinkedList<>();
        for (int i = 0; i < n; i++) {
            if (senate.charAt(i) == 'R') radiant.add(i);
            else dire.add(i);
        }

        while (!radiant.isEmpty() && !dire.isEmpty()) {
            int r = radiant.poll(), d = dire.poll();
            if (r < d) radiant.add(r + n);
            else dire.add(d + n);
        }
        return radiant.isEmpty() ? "Dire" : "Radiant";
    }

    public static void main(String[] args) {
        System.out.println(predictPartyVictory("RD"));
        // Radiant
        System.out.println(predictPartyVictory("RDD"));
        // Dire
    }
}
```

**How to run:** `java Dota2Senate.java`

## 6. Walkthrough

Trace `predictPartyVictory("RDD")` (`n = 3`, `radiant = [0]`, `dire = [1, 2]`):

| step | radiant front | dire front | winner of this comparison | radiant after | dire after |
|---|---|---|---|---|---|
| 1 | 0 | 1 | 0 &lt; 1, Radiant bans Dire(1) | [3] | [2] |
| 2 | 3 | 2 | 2 &lt; 3, Dire bans Radiant(3) | [] | [5] |

Radiant's queue is now empty, so `dire` wins: the function returns `"Dire"`, matching the expected answer. Time complexity is O(n) (each senator is processed a constant number of times across all rounds combined). Space is O(n) for the two queues.

## 7. Gotchas & takeaways

> Gotcha: re-queuing the SURVIVOR at their ORIGINAL index (instead of `index + n`) breaks the simulation — without the `+ n` offset, the survivor's turn order relative to senators later in the SAME round (who have not acted yet) would be computed incorrectly, since their index would no longer reflect "this senator's next turn is one full round away."

- Two queues of ORIGINAL indices, compared and re-queued with a `+ n` offset: the elegant trick that avoids simulating explicit "rounds" as a separate outer loop.
- The senator with the SMALLER index acts first and eliminates the other — this greedy "handle the most urgent turn first" rule is what a real round-based simulation would do anyway, just computed more directly.
- Related problems: Gas Station (a different greedy simulation, tracking a cumulative balance rather than competing turn orders), Queue Reconstruction by Height (a different queue-based greedy — building a final arrangement via careful INSERTION order, rather than simulating elimination rounds).
