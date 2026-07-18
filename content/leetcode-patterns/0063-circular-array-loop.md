---
card: leetcode-patterns
gi: 63
slug: circular-array-loop
title: Circular Array Loop
---

## 1. What it is

Given a circular array `nums` of non-zero integers, where `nums[i]` tells you how many steps to move (positive = forward, negative = backward, wrapping around both ends), determine whether there is a cycle. A valid cycle must have length greater than `1` and every step in it must move in the same direction (all forward or all backward). Example: `nums = [2,-1,1,2,2]` → `true` (there is a valid cycle starting at index 0: `0 -> 2 -> 3 -> 0`).

## 2. Why & when

This is the hardest problem in the section because it adds two extra constraints on top of ordinary cycle detection: the cycle must have length `> 1` (a self-loop, where `nums[i] % n == 0`, does not count), and every move in the cycle must share the same sign. It shows how to adapt the base fast & slow pointers template when a problem adds validity rules beyond "does a cycle exist".

## 3. Core concept

**Key idea:** treat each index as a node, with `next(i) = (i + nums[i]) mod n` (adjusted to stay non-negative) as its outgoing pointer — but only follow that pointer while the direction (sign of `nums[i]`) stays consistent with where you started. Run fast & slow pointers from every unvisited index, but abandon the search early if the direction changes or a self-loop is hit.

**Steps:**
1. For each starting index `i` not yet marked visited:
   - Define `next(x) = (x + nums[x]) mod n`, wrapping negative results back into range.
   - Run fast & slow pointers, but at each step check both `nums[current]` share the same sign as `nums[i]` (the starting direction). If not, break out — no valid cycle from this start.
   - Also check that `next(current) != current` (a length-1 self-loop is invalid). If it is a self-loop, break out.
   - If `slow == fast` under these constraints, a valid cycle exists — return `true`.
2. Mark every index visited along a failed path, so later starts do not redo the same wasted work.
3. If no start produces a valid cycle, return `false`.

**Why it works:** the same lapping logic from the base pattern still detects *some* cycle in the direction-consistent sub-graph. Filtering out sign changes and self-loops before checking `slow == fast` ensures that a "yes" answer only fires for cycles that satisfy the problem's extra validity rules.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Circular array cycle with consistent direction">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [2, -1, 1, 2, 2], all indices move forward: 0 -&gt; 2 -&gt; 3 -&gt; 0</text>
    <circle cx="80" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/><text x="80" y="95" fill="#e6edf3" text-anchor="middle">idx 0</text><text x="80" y="112" fill="#8b949e" text-anchor="middle" font-size="10">val 2</text>
    <circle cx="200" cy="60" r="22" fill="#161b22" stroke="#30363d"/><text x="200" y="55" fill="#e6edf3" text-anchor="middle">idx 1</text><text x="200" y="72" fill="#8b949e" text-anchor="middle" font-size="10">val -1</text>
    <circle cx="320" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">idx 2</text><text x="320" y="112" fill="#8b949e" text-anchor="middle" font-size="10">val 1</text>
    <circle cx="200" cy="160" r="22" fill="#161b22" stroke="#79c0ff"/><text x="200" y="155" fill="#e6edf3" text-anchor="middle">idx 3</text><text x="200" y="172" fill="#8b949e" text-anchor="middle" font-size="10">val 2</text>
    <line x1="98" y1="88" x2="185" y2="70" stroke="#30363d" stroke-dasharray="3,3"/>
    <path d="M100,110 C160,130 260,130 300,112" fill="none" stroke="#8b949e" marker-end="url(#g)"/>
    <path d="M320,122 C300,150 240,158 222,160" fill="none" stroke="#8b949e" marker-end="url(#g)"/>
    <path d="M188,140 C120,110 90,110 82,110" fill="none" stroke="#8b949e" marker-end="url(#g)"/>
    <defs><marker id="g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="200" fill="#8b949e">index 1 is skipped (its negative value would break the all-forward direction)</text>
  </g>
</svg>

Indices `0 -> 2 -> 3 -> 0` form a valid, direction-consistent, length-3 cycle; index `1`'s negative value is never entered because it breaks the forward-only rule.

## 5. Runnable example

```java
// CircularArrayLoop.java
public class CircularArrayLoop {

    static int next(int[] nums, int i) {
        int n = nums.length;
        return ((i + nums[i]) % n + n) % n; // keep the result non-negative
    }

    // Level 1 -- Brute force: from every index, walk step by step with a
    // hash set, checking direction and self-loop rules. O(n^2) worst case
    // time (each start can re-walk shared nodes), O(n) space per walk.
    static boolean bruteForce(int[] nums) {
        int n = nums.length;
        for (int i = 0; i < n; i++) {
            java.util.Set<Integer> seen = new java.util.HashSet<>();
            int cur = i;
            boolean forward = nums[i] > 0;
            while (true) {
                if (nums[cur] > 0 != forward) break;
                int nxt = next(nums, cur);
                if (nxt == cur) break;
                if (!seen.add(cur)) return true;
                cur = nxt;
            }
        }
        return false;
    }

    // KEY INSIGHT: fast &amp; slow pointers still detects a cycle by lapping,
    // but here the "next" function must be filtered to only follow steps
    // that keep the same sign and never revisit the current index --
    // otherwise it would flag invalid mixed-direction or self-loop cycles.

    // Level 2 -- Optimal: fast &amp; slow pointers per unvisited start,
    // with direction and self-loop checks. O(n) time overall (each index
    // is visited a bounded number of times), O(1) extra space.
    public static boolean circularArrayLoop(int[] nums) {
        int n = nums.length;
        for (int i = 0; i < n; i++) {
            if (nums[i] == 0) continue;
            int slow = i, fast = i;
            boolean forward = nums[i] > 0;

            while (true) {
                slow = safeNext(nums, slow, forward);
                if (slow == -1) break;
                fast = safeNext(nums, fast, forward);
                if (fast == -1) break;
                fast = safeNext(nums, fast, forward);
                if (fast == -1) break;
                if (slow == fast) return true;
            }
        }
        return false;
    }

    // Returns -1 if the move is invalid (wrong direction or self-loop),
    // marking the index visited (0) along the way so future starts skip it.
    static int safeNext(int[] nums, int i, boolean forward) {
        boolean sameDirection = (nums[i] > 0) == forward;
        if (!sameDirection) return -1;
        int nxt = next(nums, i);
        if (nxt == i) return -1; // self-loop, invalid (length must be > 1)
        return nxt;
    }

    // Level 3 -- Hardened: an array where every value points to a
    // self-loop (e.g. [1,1,1,1]) must return false, since length-1
    // cycles are explicitly excluded.
    static boolean hardened(int[] nums) {
        return circularArrayLoop(nums);
    }

    public static void main(String[] args) {
        int[] nums1 = {2, -1, 1, 2, 2};
        System.out.println("brute force: " + bruteForce(nums1));
        System.out.println("optimal:     " + circularArrayLoop(nums1));

        int[] selfLoops = {1, 1, 1, 1};
        System.out.println("all self-loops (expect false): " + hardened(selfLoops));

        int[] mixedDirection = {-1, 2};
        System.out.println("mixed direction (expect false): " + hardened(mixedDirection));
    }
}
```

How to run: save as `CircularArrayLoop.java`, then run `java CircularArrayLoop.java`.

## 6. Walkthrough

Dry run of `circularArrayLoop({2,-1,1,2,2})` starting at `i = 0` (`forward = true`, since `nums[0] = 2 > 0`):

| step | slow | fast (after 2 sub-steps) | notes |
|---|---|---|---|
| start | 0 | 0 | |
| 1 | next(0)=2 | next(next(0))=next(2)=3 | both moves stay positive-direction |
| 2 | next(2)=3 | next(next(3))=next(0)=2 (then next(2)=3) | fast: 3->0 (valid) ->0->2 (valid) |
| — | slow=3, fast=3 | `slow == fast` -> return true | |

Index `1` (value `-1`) is never entered from this start, since reaching it would require a step whose destination breaks the forward-only rule, and `safeNext` returns `-1` for that case. Time complexity: O(n) overall, since each index is either resolved as part of a cycle or marked invalid and never revisited across different start points. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: checking direction consistency using only the *starting* index's sign, but forgetting to also re-check it on every subsequent step, lets the walk silently cross from a positive run into a negative one — producing a false "cycle found" on an invalid mixed-direction loop.

- The two extra rules — no self-loops, no direction changes — must be checked on *every* step of both `slow` and `fast`, not just at the start.
- Related problems: Find the Duplicate Number (simpler array-as-graph cycle, no direction constraint), Linked List Cycle II (the base two-phase technique this builds on).
