---
card: data-structures
gi: 69
slug: next-greater-element-problems
title: Next-greater-element problems
---

## 1. What it is

**Next-greater-element** problems ask: for each element in a sequence, find the first element after it (to the right) that is strictly bigger. This topic builds on the monotonic stack technique and covers the variations that show up in practice: a circular array, and looking up an element's answer from a *different* array than the one it was computed on.

## 2. Why & when

The plain "next greater" pattern generalizes to a lot of real problems: stock-span (how many consecutive prior days had a lower price), circular scheduling (wrap-around comparisons), and matching values across two related arrays. Recognizing the pattern — "nearest bigger/smaller to one side, computed once per element" — saves you from re-deriving the approach from scratch each time.

## 3. Core concept

**Key idea in one sentence.** Reuse the monotonic-decreasing-stack template from [Monotonic stack technique](0068-monotonic-stack-technique.md); each variant only changes what gets scanned, or what gets stored as the "answer."

**Level 1 — Brute force.** For every element, scan every element after it, stopping at the first bigger one. Correct, but O(n²) — for `n = 10,000` that is up to 100 million comparisons.

**KEY INSIGHT.** The monotonic stack computes every element's next-greater in one shared linear pass, because "pop when a bigger element appears" naturally assigns each popped element its answer at the exact moment that bigger element is discovered — no separate scan needed per element.

**Level 2 — Optimal, with two twists.**
- **Circular array:** conceptually loop the array twice (`i % n` for the value, but only push each index once, on its first pass), so an element near the end can still find its next-greater near the start.
- **Two related arrays (LeetCode 496 style):** compute next-greater for the *bigger* array once with the stack, store results in a map from value to next-greater, then look up each element of the *smaller* array in that map.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circular array processed by scanning it twice conceptually so the last element can wrap around and compare against elements near the start">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">circular array: [5, 4, 3, 2] -- index 3 (val 2) wraps to check index 0 (val 5)</text>
    <rect x="30" y="40" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="50" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <rect x="70" y="40" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="90" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <rect x="110" y="40" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="130" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="150" y="40" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="170" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <path d="M170,66 C170,110 50,110 50,66" fill="none" stroke="#79c0ff" marker-end="url(#wr)"/>
    <defs><marker id="wr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="110" y="130" fill="#79c0ff" text-anchor="middle" font-size="9">index 3 wraps around: index (3+1) % 4 = 0, value 5 &gt; 2 -&gt; next greater of 2 is 5</text>
  </g>
</svg>

Scanning indices `0..2n-1` with `i % n` for the value lets the last elements "see" wrapped-around elements near the start, without physically duplicating the array.

## 5. Runnable example

```java
// NextGreaterElementProblems.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;

public class NextGreaterElementProblems {

    // Level 1: brute force -- O(n^2), for comparison.
    static int[] nextGreaterBruteForce(int[] nums) {
        int[] answer = new int[nums.length];
        for (int i = 0; i < nums.length; i++) {
            answer[i] = -1;
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[j] > nums[i]) { answer[i] = nums[j]; break; }
            }
        }
        return answer;
    }

    static void basicLevel() {
        int[] nums = {2, 1, 5, 3};
        System.out.println("basic: brute force next greater -> " + java.util.Arrays.toString(nextGreaterBruteForce(nums)));
    }

    // Level 2, variant A: circular array -- scan indices 0..2n-1 using i % n, push each real index only once.
    static int[] nextGreaterCircular(int[] nums) {
        int n = nums.length;
        int[] answer = new int[n];
        java.util.Arrays.fill(answer, -1);
        Deque<Integer> stack = new ArrayDeque<>();

        for (int i = 0; i < 2 * n; i++) {
            int idx = i % n;
            while (!stack.isEmpty() && nums[stack.peek()] < nums[idx]) {
                answer[stack.pop()] = nums[idx];
            }
            if (i < n) stack.push(idx); // only push each real index once, during the first pass
        }
        return answer;
    }

    static void intermediateLevel() {
        int[] nums = {5, 4, 3, 2};
        System.out.println("intermediate: circular next greater [5,4,3,2] -> " + java.util.Arrays.toString(nextGreaterCircular(nums)));
    }

    // Level 2, variant B: two related arrays -- compute next-greater on the bigger array, then look up the smaller one.
    static int[] nextGreaterAcrossArrays(int[] queryValues, int[] fullArray) {
        Map<Integer, Integer> nextGreaterOf = new HashMap<>();
        Deque<Integer> stack = new ArrayDeque<>(); // holds VALUES here, since we need a value-to-value map

        for (int value : fullArray) {
            while (!stack.isEmpty() && stack.peek() < value) {
                nextGreaterOf.put(stack.pop(), value);
            }
            stack.push(value);
        }
        // whatever remains on the stack has no next greater element; leave it unmapped (defaults to -1 below)

        int[] answer = new int[queryValues.length];
        for (int i = 0; i < queryValues.length; i++) {
            answer[i] = nextGreaterOf.getOrDefault(queryValues[i], -1);
        }
        return answer;
    }

    static void advancedLevel() {
        int[] queryValues = {4, 1, 2};
        int[] fullArray = {1, 3, 4, 2};
        System.out.println("advanced: nextGreaterAcrossArrays([4,1,2], [1,3,4,2]) -> "
            + java.util.Arrays.toString(nextGreaterAcrossArrays(queryValues, fullArray)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `NextGreaterElementProblems.java`, then run `java NextGreaterElementProblems.java`.

## 6. Walkthrough

Trace `nextGreaterCircular([5, 4, 3, 2])`, `n = 4`, scanning `i = 0..7`:

| i | idx = i%n | val | action | stack after |
|---|---|---|---|---|
| 0 | 0 | 5 | push | `[0]` |
| 1 | 1 | 4 | no pop, push | `[0,1]` |
| 2 | 2 | 3 | no pop, push | `[0,1,2]` |
| 3 | 3 | 2 | no pop, push | `[0,1,2,3]` |
| 4 | 0 | 5 | 5>2 pop 3 (ans[3]=5); 5>3 pop 2 (ans[2]=5); 5>4 pop 1 (ans[1]=5); 5==5 stop | `[0]` |
| 5–7 | — | — | `i >= n`, nothing pushed; stack top is index 0 (val 5), nothing left is smaller | `[0]` |

Final answer: `[-1, 5, 5, 5]` — index `0` (value `5`) is the largest, so it never finds a next-greater even wrapping around.

For `nextGreaterAcrossArrays`, the stack computes `{1: 3, 3: 4}` from `fullArray = [1, 3, 4, 2]` (`4` and `2` are left unmapped, no next-greater). Looking up `queryValues = [4, 1, 2]` gives `[-1, 3, -1]`.

## 7. Gotchas & takeaways

> Gotcha: in the circular variant, pushing an index during BOTH passes would let the algorithm assign it an answer twice, and would also let an index find itself as its own "next greater" on the second lap — always push each real index only once, guarded by `if (i < n)`.

- Circular arrays: scan `2n` virtual steps with `i % n`, but push each real index only on its first appearance.
- Cross-array lookups: build a value-to-next-greater map from the array that has the full context, then look up the query array in it.
- Both variants reuse the exact same monotonic-stack core; only the indexing or the storage target changes.
- Related concepts: [Monotonic stack technique](0068-monotonic-stack-technique.md), [LIFO semantics](0062-lifo-semantics.md).
