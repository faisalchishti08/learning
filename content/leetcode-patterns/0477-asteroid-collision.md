---
card: leetcode-patterns
gi: 477
slug: asteroid-collision
title: Asteroid Collision
---

## 1. What it is

You get an array `asteroids` where each value's absolute value is its size, and its sign is its direction (positive moves right, negative moves left). When two asteroids meet, the smaller one explodes; if they are equal size, both explode. Two asteroids moving the same direction never meet. Return the state of the asteroids after all collisions settle. Example: `asteroids = [5, 10, -5]` → `[5, 10]` (`10` and `-5` collide, `-5` explodes since it is smaller).

## 2. Why & when

Collisions only happen between a right-moving asteroid (positive) followed later by a left-moving one (negative) — exactly the shape a stack tracks naturally: keep the right-movers you have seen so far, and resolve each new left-mover against them one at a time. This is a simulation use of the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family, using the stack to model "asteroids still in flight" rather than to answer a next-greater query directly. Constraints: up to 10,000 asteroids, sizes up to 1000, no asteroid has size `0`.

## 3. Core concept

**Key idea:** scan left to right, keeping a stack of asteroids still alive (all moving right, or a left-mover that survived everything before it). A new left-moving asteroid can only collide with right-movers already on the stack — so keep popping and comparing sizes until either the new asteroid explodes, the stack's top explodes, or they cancel out.

**Steps:**
1. For each asteroid `a` in the array: if `a` is positive (moving right), or the stack is empty, or the stack's top is negative (also moving left, so no collision is possible), push `a`.
2. Otherwise (`a` is negative and the stack's top is positive — a collision is possible): compare sizes.
   - If `|top| < |a|`, pop the top (it explodes) and re-check against the new top (the current asteroid may keep colliding).
   - If `|top| == |a|`, pop the top and discard the current asteroid (both explode).
   - If `|top| > |a|`, discard the current asteroid (it explodes); the top survives.
3. This comparison can repeat multiple times for a single incoming asteroid, since it might destroy several smaller right-movers in a row before either surviving or being destroyed itself.

**Why a `while` loop (not a single `if`) is needed:** one incoming left-mover can be bigger than several right-movers stacked in a row, destroying each in turn until it meets one that is equal or bigger, or the stack empties.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming left-moving asteroid destroying several right-moving asteroids in a row">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">asteroids = [5, 10, -5]</text>
    <text x="20" y="45" fill="#8b949e">5: push (positive). stack=[5]</text>
    <text x="20" y="65" fill="#8b949e">10: push (positive). stack=[5, 10]</text>
    <text x="20" y="90" fill="#f0883e">-5: top=10 (positive), collision. |10| &gt; |-5| -&gt; -5 explodes, 10 survives.</text>
    <text x="20" y="115" fill="#3fb950">stack unchanged: [5, 10] -&gt; final answer [5, 10]</text>
  </g>
</svg>

Only a right-mover on the stack meeting an incoming left-mover triggers a collision; the smaller of the two explodes.

## 5. Runnable example

**Level 1 — Brute force.** Repeatedly scan the array for any adjacent colliding pair, resolve it, and rescan from the start. O(n²) or worse, since a resolved collision can trigger another one behind it.

**KEY INSIGHT:** a stack of "still-flying right-movers" naturally models which asteroids a new left-mover can still hit — each survives or is destroyed in a single left-to-right pass, without ever rescanning from the beginning.

**Level 2 — Optimal.** Single-pass stack simulation, O(n).

**Level 3 — Hardened.** Handles a chain reaction (one asteroid destroys several in a row), equal-size collisions (both explode), and asteroids that never collide (all moving the same direction).

```java
// AsteroidCollision.java
import java.util.*;

public class AsteroidCollision {

    // Level 2 & 3: stack simulation, O(n)
    static int[] asteroidCollision(int[] asteroids) {
        Deque<Integer> stack = new ArrayDeque<>(); // bottom to top: flight order, left to right

        for (int a : asteroids) {
            boolean destroyed = false;

            while (!stack.isEmpty() && a < 0 && stack.peek() > 0) {
                int top = stack.peek();
                if (Math.abs(top) < Math.abs(a)) {
                    stack.pop(); // top explodes, keep checking the current asteroid
                } else if (Math.abs(top) == Math.abs(a)) {
                    stack.pop(); // both explode
                    destroyed = true;
                    break;
                } else {
                    destroyed = true; // current asteroid explodes, top survives
                    break;
                }
            }

            if (!destroyed) {
                stack.push(a);
            }
        }

        int[] result = new int[stack.size()];
        for (int i = result.length - 1; i >= 0; i--) {
            result[i] = stack.pop();
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(asteroidCollision(new int[]{5, 10, -5})));       // [5, 10]
        System.out.println(Arrays.toString(asteroidCollision(new int[]{8, -8})));            // [] (both explode)
        System.out.println(Arrays.toString(asteroidCollision(new int[]{10, 2, -5})));        // [10] (chain reaction)
        System.out.println(Arrays.toString(asteroidCollision(new int[]{-2, -1, 1, 2})));     // [-2, -1, 1, 2] (no collisions)
    }
}
```

**How to run:** save as `AsteroidCollision.java`, then run `java AsteroidCollision.java`.

## 6. Walkthrough

Trace `asteroidCollision({10, 2, -5})`, showing the chain reaction:

| asteroid | stack before | while-loop iterations | action | stack after |
|---|---|---|---|---|
| 10 | [] | none (positive) | push | [10] |
| 2 | [10] | none (positive) | push | [10, 2] |
| -5 | [10, 2] | top=2: `\|2\|<\|-5\|` → pop 2, continue | — | [10] |
| -5 (continued) | [10] | top=10: `\|10\|>\|-5\|` → -5 explodes, stop | destroyed = true | [10] |

The incoming `-5` destroys `2` first (smaller), then meets `10` (bigger) and explodes itself. Final stack, read bottom to top: `[10]`. Result: `[10]`, matching the expected chain-reaction outcome.

## 7. Gotchas & takeaways

> Gotcha: using a single `if` instead of a `while` to check for collisions misses chain reactions — an incoming asteroid can destroy several smaller right-movers in a row before finally surviving or being destroyed itself.

- Only a right-mover (positive) followed by a left-mover (negative) can collide; same-direction asteroids never interact, so push them without any check.
- Equal-size collisions destroy both — do not let either one survive by mistake.
- Time: O(n) — each asteroid is pushed once and popped at most once, the same amortized argument as [next greater element](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md), even though this problem is a simulation rather than a direct next-greater query.
