---
card: leetcode-patterns
gi: 78
slug: teemo-attacking
title: Teemo Attacking
---

## 1. What it is

An attacker poisons a target at given timestamps `timeSeries`. Each poison lasts exactly `duration` seconds. If a new poison attack lands while the target is still poisoned, the poison duration does not stack — it just extends the existing poison window (or restarts it) rather than adding a fresh, separate duration on top. Find the total number of seconds the target is poisoned. Example: `timeSeries = [1,4]`, `duration = 2` → `4` (poisoned during `[1,3)` and `[4,6)`, no overlap, total `2 + 2 = 4`).

## 2. Why & when

Each attack timestamp `t` defines an interval `[t, t + duration)`. "How many total seconds is the target poisoned" is exactly "what is the total length covered by the union of these intervals" — the same union-of-intervals idea used in Employee Free Time, but here you want the covered length, not the gaps.

## 3. Core concept

**Key idea:** convert each attack into an interval `[t, t + duration)`. Since the timestamps are already given in increasing order, compare each interval to the previous one directly: if it overlaps, only count the non-overlapping portion; if it does not overlap, count the whole duration.

**Steps:**
1. If `timeSeries` is empty, return `0`.
2. Set `total = 0`.
3. For each index `i` from `1` to `n - 1`:
   - The gap between attacks is `timeSeries[i] - timeSeries[i-1]`.
   - If that gap is less than `duration`, the poison windows overlap — add only the gap (`timeSeries[i] - timeSeries[i-1]`) to `total`, since that is the non-overlapping portion contributed by the *previous* attack.
   - Otherwise, add the full `duration` for the previous attack.
4. After the loop, add the full `duration` for the last attack (its window is never truncated by a following attack).

**Why it is correct:** when two consecutive poison windows overlap, the earlier attack only contributes poisoned time up until the next attack starts (since the next attack re-applies poison from that point, whether or not it "stacks," the target is already poisoned continuously). Summing each attack's non-overlapping contribution, plus the final attack's full duration, gives exactly the total covered length.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Poison duration windows overlapping and merging in total covered time">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">timeSeries = [1, 2], duration = 2 -&gt; windows [1,3) and [2,4)</text>
    <rect x="40" y="45" width="80" height="20" fill="#161b22" stroke="#79c0ff"/><text x="80" y="60" fill="#e6edf3" text-anchor="middle" font-size="10">[1,3)</text>
    <rect x="80" y="70" width="80" height="20" fill="#161b22" stroke="#f0883e"/><text x="120" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">[2,4)</text>
    <rect x="40" y="100" width="120" height="18" fill="none" stroke="#3fb950" stroke-dasharray="3,2"/><text x="100" y="113" fill="#3fb950" text-anchor="middle" font-size="10">covered: [1,4) = 3 seconds</text>
    <text x="20" y="140" fill="#8b949e">gap between attacks (2-1=1) &lt; duration (2) -&gt; only 1 second from first attack counted, plus full 2 from second</text>
  </g>
</svg>

Overlapping windows `[1,3)` and `[2,4)` cover `3` total seconds, not `4` — the first attack only contributes its non-overlapping `1` second before the second attack's window takes over.

## 5. Runnable example

```java
// TeemoAttacking.java
public class TeemoAttacking {

    // Level 1 -- Brute force: mark every poisoned second in a boolean
    // array (or set), then count marked seconds. O(n * duration) time --
    // wastes work re-marking seconds already covered by an earlier attack.
    static int bruteForce(int[] timeSeries, int duration) {
        if (timeSeries.length == 0) return 0;
        java.util.Set<Integer> poisoned = new java.util.HashSet<>();
        for (int t : timeSeries) {
            for (int s = t; s < t + duration; s++) poisoned.add(s);
        }
        return poisoned.size();
    }

    // KEY INSIGHT: since timestamps are already sorted, comparing each
    // attack only to the ONE before it is enough -- if the gap to the
    // next attack is shorter than duration, only that gap (not the full
    // duration) is the earlier attack's real contribution.

    // Level 2 -- Optimal: single pass comparing consecutive gaps.
    // O(n) time, O(1) extra space.
    public static int findPoisonedDuration(int[] timeSeries, int duration) {
        if (timeSeries.length == 0) return 0;
        int total = 0;
        for (int i = 1; i < timeSeries.length; i++) {
            int gap = timeSeries[i] - timeSeries[i - 1];
            total += Math.min(gap, duration);
        }
        return total + duration; // final attack always contributes fully
    }

    // Level 3 -- Hardened: a single attack (no gaps to compare), and
    // back-to-back attacks where the gap exactly equals duration (no
    // overlap at all).
    static int hardened(int[] timeSeries, int duration) {
        return findPoisonedDuration(timeSeries, duration);
    }

    public static void main(String[] args) {
        int[] a = {1, 4};
        System.out.println("brute force: " + bruteForce(a, 2));
        System.out.println("optimal:     " + findPoisonedDuration(a, 2));

        int[] overlapping = {1, 2};
        System.out.println("overlapping (expect 3): " + findPoisonedDuration(overlapping, 2));

        int[] single = {5};
        System.out.println("single attack (expect 2): " + hardened(single, 2));
    }
}
```

How to run: save as `TeemoAttacking.java`, then run `java TeemoAttacking.java`.

## 6. Walkthrough

Dry run of `findPoisonedDuration({1, 4}, 2)`:

| step | timeSeries[i-1] | timeSeries[i] | gap | min(gap, duration) | total |
|---|---|---|---|---|---|
| 1 | 1 | 4 | 3 | min(3,2)=2 | 2 |

After the loop, add the final `duration` (`2`) for the last attack: `total = 2 + 2 = 4`. Matches the expected answer, since `[1,3)` and `[4,6)` do not overlap. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to add the final attack's full `duration` after the loop undercounts by `duration` seconds, since the loop only accounts for each attack's contribution *up to the next attack*, never the last one's remaining window.

- This problem measures covered length rather than gaps (Employee Free Time) or peak overlap (Meeting Rooms II) — the same "compare consecutive sorted intervals" shape, applied to a third kind of question.
- Related problems: Merge Intervals (general union), Employee Free Time (the complement of the union).
