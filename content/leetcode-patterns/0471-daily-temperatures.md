---
card: leetcode-patterns
gi: 471
slug: daily-temperatures
title: Daily Temperatures
---

## 1. What it is

You get an array `temperatures` of daily temperatures. For each day, find how many days you must wait until a warmer temperature appears; if none ever does, the answer for that day is `0`. Example: `temperatures = [73, 74, 75, 71, 69, 72, 76, 73]` → `[1, 1, 4, 2, 1, 1, 0, 0]`.

## 2. Why & when

This is the "next greater element, but return the distance instead of the value" variant, part of the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family. The phrase "how many days until warmer" is the signal for a decreasing stack of *indices* (you need positions to compute a distance). Constraints: up to 100,000 days.

## 3. Core concept

**Key idea:** keep a decreasing stack of indices (temperatures at those indices are decreasing bottom to top, each still waiting for a warmer day). When a warmer temperature arrives, pop every colder-or-equal index below it and set that index's answer to `current index - popped index`.

**Steps:**
1. Create a `result` array of the same length, initialized to `0` (default: never gets warmer).
2. Maintain a stack of indices, decreasing by temperature.
3. For each day `i`: while the stack is not empty and `temperatures[i] > temperatures[stack.peek()]`, pop index `j` and set `result[j] = i - j`.
4. Push `i`.
5. Indices left on the stack at the end keep `result = 0` — no warmer day ever comes.

**Why this needs indices, not values:** the answer is a *distance* (`i - j`), which only indices can express. This differentiates it from [Next Greater Element I](0469-next-greater-element-i.md), which only needed the next greater *value*.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decreasing stack of indices resolving wait distances as warmer days arrive">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">temperatures = [73, 74, 75, 71, 69, 72, 76, 73]</text>
    <text x="20" y="45" fill="#8b949e">i=0 (73): push 0. stack=[0]</text>
    <text x="20" y="65" fill="#8b949e">i=1 (74): pop 0 (73&lt;74) -&gt; result[0]=1-0=1. push 1. stack=[1]</text>
    <text x="20" y="85" fill="#8b949e">i=2 (75): pop 1 (74&lt;75) -&gt; result[1]=2-1=1. push 2. stack=[2]</text>
    <text x="20" y="105" fill="#8b949e">i=3 (71): 75 not &lt; 71, push 3. stack=[2,3]</text>
    <text x="20" y="125" fill="#8b949e">i=4 (69): 71 not &lt; 69, push 4. stack=[2,3,4]</text>
    <text x="20" y="145" fill="#8b949e">i=5 (72): pop 4 (69&lt;72)->result[4]=1; pop 3 (71&lt;72)->result[3]=2. push 5. stack=[2,5]</text>
    <text x="20" y="165" fill="#3fb950">i=6 (76): pops 5 and 2 -&gt; result[5]=1, result[2]=4. stack=[6]</text>
  </g>
</svg>

Every pop computes `current index - popped index`, giving the exact number of days waited.

## 5. Runnable example

**Level 1 — Brute force.** For each day, scan forward until a warmer temperature appears. O(n²).

**KEY INSIGHT:** the wait distance for every day can be resolved in one forward pass: a colder day sits on the stack until a warmer one finally arrives, at which point its distance is just the index gap.

**Level 2 — Optimal.** Single-pass decreasing stack of indices, O(n).

**Level 3 — Hardened.** Handles a strictly decreasing array (nobody ever gets a warmer day, all zeros) and a single-day array.

```java
// DailyTemperatures.java
import java.util.*;

public class DailyTemperatures {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] temperatures) {
        int n = temperatures.length;
        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (temperatures[j] > temperatures[i]) {
                    result[i] = j - i;
                    break;
                }
            }
        }
        return result;
    }

    // Level 2 & 3: decreasing monotonic stack of indices, O(n)
    static int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] result = new int[n];
        Deque<Integer> stack = new ArrayDeque<>(); // decreasing temperatures, holds indices

        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && temperatures[i] > temperatures[stack.peek()]) {
                int j = stack.pop();
                result[j] = i - j;
            }
            stack.push(i);
        }
        return result;
    }

    public static void main(String[] args) {
        int[] temps = {73, 74, 75, 71, 69, 72, 76, 73};
        System.out.println("brute force: " + Arrays.toString(bruteForce(temps)));
        System.out.println("optimal:     " + Arrays.toString(dailyTemperatures(temps)));

        System.out.println("never warmer: " + Arrays.toString(dailyTemperatures(new int[]{5, 4, 3, 2, 1})));
        System.out.println("single day:   " + Arrays.toString(dailyTemperatures(new int[]{50})));
    }
}
```

**How to run:** save as `DailyTemperatures.java`, then run `java DailyTemperatures.java`.

## 6. Walkthrough

Dry-run `dailyTemperatures({73, 74, 75, 71, 69, 72, 76, 73})`:

| i | temp | stack before | action | stack after | result so far |
|---|---|---|---|---|---|
| 0 | 73 | [] | push 0 | [0] | [0,0,0,0,0,0,0,0] |
| 1 | 74 | [0] | pop 0 → result[0]=1; push 1 | [1] | [1,0,...] |
| 2 | 75 | [1] | pop 1 → result[1]=1; push 2 | [2] | [1,1,0,...] |
| 3 | 71 | [2] | 75 not < 71; push 3 | [2,3] | unchanged |
| 4 | 69 | [2,3] | 71 not < 69; push 4 | [2,3,4] | unchanged |
| 5 | 72 | [2,3,4] | pop 4→result[4]=1; pop 3→result[3]=2; push 5 | [2,5] | [1,1,0,2,1,0,0,0] |
| 6 | 76 | [2,5] | pop 5→result[5]=1; pop 2→result[2]=4; push 6 | [6] | [1,1,4,2,1,1,0,0] |
| 7 | 73 | [6] | 76 not < 73; push 7 | [6,7] | final |

Final result: `[1, 1, 4, 2, 1, 1, 0, 0]`, matching the expected output. Time: O(n), space: O(n) for the stack.

## 7. Gotchas & takeaways

> Gotcha: subtracting indices in the wrong order (`j - i` instead of `i - j`) silently produces negative distances. Always compute `current index - popped index`, since the popped index is always earlier.

- The wait-distance phrasing is the signal that you need indices on the stack, not values — see [Next Greater Element I](0469-next-greater-element-i.md) for the values-only variant of this same idea.
- Days with no warmer day ever get `result = 0`, matching the initialized default — no special-casing needed.
- Related problems: Next Greater Element I and II, Online Stock Span.
