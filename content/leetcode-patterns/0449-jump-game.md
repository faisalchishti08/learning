---
card: leetcode-patterns
gi: 449
slug: jump-game
title: Jump Game
---

## 1. What it is

Given an array where `nums[i]` is the MAXIMUM jump length from position `i`, determine whether you can reach the LAST index, starting from index `0`. Example: `nums = [2,3,1,1,4]` → `true`. Example: `nums = [3,2,1,0,4]` → `false`.

## 2. Why & when

Use this shape whenever a problem asks a REACHABILITY question over a sequence of positions with per-position jump limits. The greedy rule: track the FARTHEST index reachable so far as you scan left to right; if you ever reach an index BEYOND that farthest reach, the destination is unreachable.

## 3. Core concept

**Key idea:** maintain `farthestReachable`, the largest index provably reachable using jumps from positions already visited.

**Steps:**
1. Initialize `farthestReachable = 0`.
2. For each index `i` from `0` onward: if `i > farthestReachable`, no jump sequence could have reached `i` at all — return `false` immediately.
3. Otherwise, update `farthestReachable = max(farthestReachable, i + nums[i])`.
4. If the loop completes without ever failing, return `true` (the last index was always within `farthestReachable` by the time it was checked).

**Why tracking only the MAXIMUM reach (not every specific path) is correct:** the question is ONLY "can you reach the end," not "how" — for any index `i` that is reachable, ALL that matters for future decisions is the FARTHEST index its jump can reach, since a shorter jump from the same position can never help more than the longest one already available. Tracking the running maximum implicitly considers every possible path's best reach, without needing to enumerate any of them explicitly.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a running farthest reachable index extending as each position is visited with failure the instant the current index exceeds that reach">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [2, 3, 1, 1, 4]</text>
    <text x="10" y="45">i=0: reach=max(0,0+2)=2; i=1: reach=max(2,1+3)=4; i=2: reach=max(4,2+1)=4</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">reach already covers index 4 (the last index) -- true</text>
  </g>
</svg>

The running farthest-reach value is updated at every index, implicitly covering every possible jump path.

## 5. Runnable example

```java
// JumpGame.java
public class JumpGame {

    // KEY INSIGHT: only the FARTHEST reachable index matters -- track
    // a running maximum instead of enumerating every possible jump
    // sequence.

    static boolean canJump(int[] nums) {
        int farthestReachable = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > farthestReachable) return false;
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

**How to run:** `java JumpGame.java`

## 6. Walkthrough

Trace `canJump([3,2,1,0,4])`:

| i | i > farthestReachable? | nums[i] | farthestReachable after |
|---|---|---|---|
| 0 | 0 > 0? no | 3 | max(0, 0+3)=3 |
| 1 | 1 > 3? no | 2 | max(3, 1+2)=3 |
| 2 | 2 > 3? no | 1 | max(3, 2+1)=3 |
| 3 | 3 > 3? no | 0 | max(3, 3+0)=3 |
| 4 | 4 > 3? YES | — | return false |

The function returns `false` at index `4`, matching the expected answer: the `0` at index `3` traps every path before it can reach the final index. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: checking `i > farthestReachable` BEFORE updating `farthestReachable` for the current index is essential — checking in the wrong order (or skipping the check entirely) would let the loop silently read `nums[i]` for an UNREACHABLE index, producing a value that has no real meaning.

- Tracking a single running maximum (`farthestReachable`) is the entire greedy insight — no need to try every possible sequence of jumps.
- This is the simpler, feasibility-only cousin of Jump Game II, which additionally MINIMIZES the number of jumps needed, not just checks whether reaching the end is possible at all.
- Related problems: Jump Game II (the same reachability idea, extended to count the minimum number of jumps), Gas Station (a different running-value greedy — a cumulative balance, not a farthest-reach index).
