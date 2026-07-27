---
card: leetcode-patterns
gi: 469
slug: next-greater-element-i
title: Next Greater Element I
---

## 1. What it is

You get two arrays, `nums1` and `nums2`, where `nums1` is a subset of `nums2` (all elements of `nums2` are distinct). For each element in `nums1`, find its next greater element in `nums2` — the first value to its right in `nums2` that is bigger — and return `-1` if none exists. Example: `nums1 = [4, 1, 2]`, `nums2 = [1, 3, 4, 2]` → `[-1, 3, -1]`.

## 2. Why & when

This is the canonical, simplest form of the monotonic-stack "next greater element" pattern. It belongs to the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family: the phrase "next greater element" is the direct tell. Constraints: `nums2` has up to 1000 distinct integers, and `nums1` is a subset of it.

## 3. Core concept

**Key idea:** precompute the next-greater answer for *every* element of `nums2` in one O(n) pass using a decreasing monotonic stack, store the results in a hash map, then look up each `nums1` element in O(1).

**Steps:**
1. Create a `Map<Integer, Integer>` to hold `value -> next greater value`.
2. Scan `nums2` left to right with a stack that stays decreasing.
3. Before pushing the current value, pop every stack value smaller than it — each popped value's next-greater answer is the current value; record it in the map.
4. Anything left on the stack at the end has no next greater element; leave those out of the map (they default to `-1` on lookup).
5. For each value in `nums1`, look it up in the map; if absent, the answer is `-1`.

**Why this is correct:** because `nums2`'s elements are all distinct, a plain hash map keyed by value (not index) is enough — no two elements share an answer slot. This is the simplest version of the pattern precisely because there is no need to track indices or distances, only values.

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanning nums2 with a decreasing stack to build the next-greater map">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums2 = [1, 3, 4, 2]</text>
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="95" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="145" y="63" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="195" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="100" fill="#8b949e">i=1 (3): pops 1 -&gt; map[1]=3. push 3.</text>
    <text x="20" y="120" fill="#8b949e">i=2 (4): pops 3 -&gt; map[3]=4. push 4.</text>
    <text x="20" y="140" fill="#8b949e">i=3 (2): 4 not &lt; 2, no pop. push 2.</text>
    <text x="20" y="160" fill="#3fb950">final map: {1:3, 3:4}. 4 and 2 have no answer.</text>
  </g>
</svg>

The decreasing stack pops a value the instant a bigger one shows up, immediately recording that value as the answer.

## 5. Runnable example

**Level 1 — Brute force.** For each `nums1` element, find it in `nums2`, then scan forward for the first bigger value. This is O(n · m) where n is `nums2`'s length.

**KEY INSIGHT:** the next-greater answer for every value in `nums2` can be computed once, for the whole array, in a single O(n) pass — then every `nums1` lookup is O(1). There is no need to re-scan `nums2` once per query.

**Level 2 — Optimal.** Build the map with a monotonic stack, then look up each `nums1` value.

**Level 3 — Hardened.** Handles `nums1` values that never appear as a "smaller than something" case (answer `-1`), and an empty `nums1`.

```java
// NextGreaterElement.java
import java.util.*;

public class NextGreaterElement {

    // Level 1: brute force, O(n * m)
    static int[] bruteForce(int[] nums1, int[] nums2) {
        int[] result = new int[nums1.length];
        for (int i = 0; i < nums1.length; i++) {
            int target = nums1[i];
            int j = 0;
            while (nums2[j] != target) j++;
            int answer = -1;
            for (int k = j + 1; k < nums2.length; k++) {
                if (nums2[k] > target) { answer = nums2[k]; break; }
            }
            result[i] = answer;
        }
        return result;
    }

    // Level 2 & 3: monotonic stack, O(n + m), handles missing answers and empty input
    static int[] nextGreaterElement(int[] nums1, int[] nums2) {
        Map<Integer, Integer> nextGreater = new HashMap<>();
        Deque<Integer> stack = new ArrayDeque<>(); // decreasing stack of values

        for (int num : nums2) {
            while (!stack.isEmpty() && stack.peek() < num) {
                nextGreater.put(stack.pop(), num);
            }
            stack.push(num);
        }

        int[] result = new int[nums1.length];
        for (int i = 0; i < nums1.length; i++) {
            result[i] = nextGreater.getOrDefault(nums1[i], -1);
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums1 = {4, 1, 2};
        int[] nums2 = {1, 3, 4, 2};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums1, nums2)));
        System.out.println("optimal:     " + Arrays.toString(nextGreaterElement(nums1, nums2)));

        System.out.println("empty nums1: " + Arrays.toString(nextGreaterElement(new int[]{}, nums2)));
    }
}
```

**How to run:** save as `NextGreaterElement.java`, then run `java NextGreaterElement.java`.

## 6. Walkthrough

Trace `nextGreaterElement({4, 1, 2}, {1, 3, 4, 2})`:

| step | num from nums2 | stack before | action | stack after | map |
|---|---|---|---|---|---|
| 1 | 1 | [] | push 1 | [1] | {} |
| 2 | 3 | [1] | pop 1 (1<3) → map[1]=3; push 3 | [3] | {1:3} |
| 3 | 4 | [3] | pop 3 (3<4) → map[3]=4; push 4 | [4] | {1:3, 3:4} |
| 4 | 2 | [4] | 4 not < 2, no pop; push 2 | [4, 2] | {1:3, 3:4} |

Lookups: `nums1[0]=4` → not in map → `-1`. `nums1[1]=1` → map has `3`. `nums1[2]=2` → not in map → `-1`. Final answer: `[-1, 3, -1]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to run the monotonic-stack scan over `nums1` instead of `nums2`. The next-greater relationship is defined by position in `nums2`, not `nums1` — always scan `nums2` to build the map, then only use `nums1` for lookups.

- This is the simplest form of the pattern: value-only stack, value-keyed hash map, no indices needed, because `nums2` has distinct elements.
- Time: O(n + m) — one pass to build the map, one pass to answer queries.
- Related problems: Next Greater Element II (circular array), Daily Temperatures (needs distance, so indices), Online Stock Span.
