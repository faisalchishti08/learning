---
card: leetcode-patterns
gi: 467
slug: monotonic-stack-template-keep-an-increasing-decreasing-stack
title: Monotonic Stack — template: keep an increasing/decreasing stack, pop on violation
---

## 1. What it is

The monotonic stack template is a single loop with one `while` inside a `for`. The `for` walks the array once; the inner `while` pops elements that no longer satisfy the ordering you want to keep. Memorize this one skeleton and adapt only the comparison to switch between "next greater" and "next smaller."

## 2. Why & when

Without a template, it is easy to get the pop condition backward (popping when the stack should grow, or growing when it should shrink), which produces subtly wrong answers rather than a crash. A fixed template lets you focus on two decisions: which direction to scan, and what comparison triggers a pop.

Use the **next-greater-to-the-right** template when the problem asks for the closest bigger (or smaller) element ahead of each position. Use the **indices-on-the-stack** variant (storing indices instead of values) whenever you also need the *distance* to that element, such as in "Daily Temperatures" or histogram-area problems.

## 3. Core concept

**Next greater element, values version.** Store a `Deque<Integer>` as the stack, kept decreasing from bottom to top. Scan left to right. Before pushing the current value, pop everything smaller than it — each pop's next-greater answer is the current value. Anything left unpopped at the end has no next greater element.

**Next greater element, indices version.** Store indices instead of values, so `arr[stack.peek()]` gives you the value to compare, and you can write the answer directly into a result array at that index (and compute distances, like "how many days until warmer").

**Why storing indices is often better:** values alone cannot tell you *where* the answer belongs in the output array, and cannot compute a distance. Indices let you do both, at the cost of one extra array lookup (`arr[index]`) whenever you need the value.

Both versions share the same loop shape: `for` scans forward once, `while` pops in violation of monotonicity, then push. The direction of the comparison (`>` vs `<`) decides whether the stack is decreasing (next greater) or increasing (next smaller).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Monotonic stack template control flow">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="260" height="40" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="150" y="45" fill="#e6edf3" text-anchor="middle">for (i = 0; i &lt; n; i++)</text>
    <rect x="20" y="80" width="260" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="105" fill="#e6edf3" text-anchor="middle">while (!empty &amp;&amp; arr[i] &gt; arr[top])</text>
    <rect x="20" y="140" width="260" height="40" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="165" fill="#e6edf3" text-anchor="middle">pop; answer[popped] = arr[i]</text>
    <line x1="150" y1="60" x2="150" y2="80" stroke="#8b949e" marker-end="url(#a1)"/>
    <line x1="150" y1="120" x2="150" y2="140" stroke="#8b949e" marker-end="url(#a1)"/>
    <path d="M280,160 C330,160 330,40 280,40" stroke="#8b949e" fill="none" marker-end="url(#a1)"/>
    <text x="400" y="45" fill="#e6edf3">after the while loop:</text>
    <text x="400" y="70" fill="#3fb950">push(i)</text>
    <text x="400" y="95" fill="#8b949e">leftover indices at the end</text>
    <text x="400" y="115" fill="#8b949e">have no next greater element</text>
  </g>
  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The `while` inside the `for` drains every index that the current element resolves, before the current index is pushed.

## 5. Runnable example

Both versions as generic, reusable methods. The indices version also returns the distance to each element's next greater neighbor.

```java
// MonotonicStackTemplates.java
import java.util.*;

public class MonotonicStackTemplates {

    // Values version: returns next-greater value for each element, or -1.
    static int[] nextGreaterValues(int[] arr) {
        int[] result = new int[arr.length];
        Arrays.fill(result, -1);
        Deque<Integer> stack = new ArrayDeque<>(); // holds values, decreasing
        for (int i = 0; i < arr.length; i++) {
            while (!stack.isEmpty() && stack.peek() < arr[i]) {
                // NOTE: this simple version cannot write back to the
                // original index once only values are stored -- that is
                // exactly why the indices version below is preferred.
                stack.pop();
            }
            stack.push(arr[i]);
        }
        return result; // left as -1s here; see indices version for real answers
    }

    // Indices version: returns next-greater value AND distance to it.
    static int[][] nextGreaterWithDistance(int[] arr) {
        int n = arr.length;
        int[] value = new int[n];
        int[] distance = new int[n];
        Arrays.fill(value, -1);
        Deque<Integer> stack = new ArrayDeque<>(); // holds indices, decreasing values
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && arr[stack.peek()] < arr[i]) {
                int idx = stack.pop();
                value[idx] = arr[i];
                distance[idx] = i - idx;
            }
            stack.push(i);
        }
        return new int[][] { value, distance };
    }

    public static void main(String[] args) {
        int[] arr = {73, 74, 75, 71, 69, 72, 76, 73};
        int[][] result = nextGreaterWithDistance(arr);
        System.out.println("values:    " + Arrays.toString(arr));
        System.out.println("next>:     " + Arrays.toString(result[0]));
        System.out.println("distance:  " + Arrays.toString(result[1]));
    }
}
```

**How to run:** save as `MonotonicStackTemplates.java`, then run `java MonotonicStackTemplates.java`.

## 6. Walkthrough

1. `nextGreaterWithDistance` is called on `{73, 74, 75, 71, 69, 72, 76, 73}`. The stack starts empty.
2. `i=0` (73): stack is empty, push index 0. Stack: `[0]`.
3. `i=1` (74): `arr[0]=73 < 74`, so pop index 0, set `value[0]=74`, `distance[0]=1`. Stack empty, push index 1. Stack: `[1]`.
4. `i=2` (75): `arr[1]=74 < 75`, pop index 1, `value[1]=75`, `distance[1]=1`. Push index 2. Stack: `[2]`.
5. `i=3` (71): `arr[2]=75` is not less than 71, so no pop. Push index 3. Stack: `[2, 3]`.
6. `i=4` (69): `arr[3]=71` is not less than 69, no pop. Push index 4. Stack: `[2, 3, 4]`.
7. `i=5` (72): `arr[4]=69 < 72`, pop index 4, `value[4]=72`, `distance[4]=1`. `arr[3]=71 < 72`, pop index 3, `value[3]=72`, `distance[3]=2`. `arr[2]=75` not less than 72, stop. Push index 5. Stack: `[2, 5]`.
8. The scan continues; indices left on the stack at the end (like index 6, holding 76, the maximum) keep `value = -1`, meaning no next-greater element exists for them.

## 7. Gotchas & takeaways

> Gotcha: storing plain values on the stack (as in `nextGreaterValues` above) makes it impossible to write the answer back to the correct original index once duplicates exist in the array. Always store indices when you need to report results per position.

- One `for` scans forward once; one `while` inside it pops on violation — that is the whole template.
- Decreasing stack (pop while top is smaller) answers "next greater"; increasing stack (pop while top is bigger) answers "next smaller."
- Store indices, not values, whenever you need the answer's position or its distance from the current element.
