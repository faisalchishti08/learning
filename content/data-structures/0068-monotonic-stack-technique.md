---
card: data-structures
gi: 68
slug: monotonic-stack-technique
title: Monotonic stack technique
---

## 1. What it is

A **monotonic stack** is a stack kept in strictly increasing (or strictly decreasing) order from bottom to top, by popping elements that would break that order before pushing a new one. It is a technique built on top of a plain stack, used to answer "what is the nearest bigger/smaller element" questions in a single linear pass.

## 2. Why & when

Use it whenever a problem asks for the **nearest** element on one side that is greater or smaller than the current one, for every element in an array — like "next greater element," "daily temperatures," or "largest rectangle in a histogram." The naive approach checks every pair, at O(n²). A monotonic stack solves it in O(n), because each element is pushed and popped from the stack at most once.

## 3. Core concept

**How the operation transforms the structure.** Walk the array left to right. Before pushing the current element's index, pop every index off the top of the stack whose value is *smaller* than the current value (for a decreasing stack, used to find "next greater"). Each popped index has just found its answer: the current element is its next greater element. Then push the current index.

**Why this works.** Once a smaller element is popped because a bigger one showed up, that bigger element is now the nearest bigger element to its left for everything still in the stack — it will keep blocking any future, even-bigger element from "reaching past" it in the answer. The stack's contents, read bottom to top, are always a decreasing sequence of "still waiting for their next greater element" candidates.

**Why it is O(n) despite the nested-looking while loop.** Each index is pushed exactly once and popped at most once across the entire run. The total number of pop operations, summed over the whole algorithm, cannot exceed the total number of pushes — so the amortized cost per element is O(1), and the whole pass is O(n).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Processing the array 2, 1, 5, 3 with a decreasing monotonic stack, popping smaller elements when a bigger one arrives and recording their next greater element">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">array: [2, 1, 5, 3]  (indices 0..3)</text>
    <text x="20" y="42" fill="#e6edf3">i=0 (val 2): stack empty -&gt; push 0.  stack: [0]</text>
    <text x="20" y="62" fill="#e6edf3">i=1 (val 1): 1 &lt; 2, no pop -&gt; push 1. stack: [0, 1]</text>
    <text x="20" y="82" fill="#79c0ff">i=2 (val 5): 5&gt;1 pop 1 (answer[1]=5); 5&gt;2 pop 0 (answer[0]=5) -&gt; push 2. stack: [2]</text>
    <text x="20" y="102" fill="#e6edf3">i=3 (val 3): 3 &lt; 5, no pop -&gt; push 3. stack: [2, 3]</text>
    <text x="20" y="128" fill="#f0883e">end: indices 2, 3 never popped -&gt; answer = -1 (no next greater)</text>
    <text x="20" y="150" fill="#a5d6ff">final answer array: [5, 5, -1, -1]</text>
  </g>
</svg>

Each pop assigns an answer to the popped index; whatever remains on the stack at the end has no next-greater element.

## 5. Runnable example

```java
// MonotonicStackTemplate.java
import java.util.ArrayDeque;
import java.util.Deque;

public class MonotonicStackTemplate {

    // The reusable template: next greater element to the right, for every index. O(n).
    static int[] nextGreaterElement(int[] nums) {
        int[] answer = new int[nums.length];
        java.util.Arrays.fill(answer, -1); // default: no next greater element
        Deque<Integer> stack = new ArrayDeque<>(); // holds indices, values strictly decreasing bottom to top

        for (int i = 0; i < nums.length; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
                int popped = stack.pop();
                answer[popped] = nums[i]; // nums[i] is the next greater element for the popped index
            }
            stack.push(i);
        }
        return answer;
    }

    static void basicLevel() {
        int[] nums = {2, 1, 5, 3};
        System.out.println("basic: nextGreaterElement([2,1,5,3]) -> " + java.util.Arrays.toString(nextGreaterElement(nums)));
    }

    // Intermediate: apply the same template to "daily temperatures" -- distance to next warmer day, not the value itself.
    static int[] dailyTemperatures(int[] temps) {
        int[] answer = new int[temps.length]; // default 0: no warmer day ahead
        Deque<Integer> stack = new ArrayDeque<>();

        for (int i = 0; i < temps.length; i++) {
            while (!stack.isEmpty() && temps[stack.peek()] < temps[i]) {
                int popped = stack.pop();
                answer[popped] = i - popped; // distance in days, not the temperature value
            }
            stack.push(i);
        }
        return answer;
    }

    static void intermediateLevel() {
        int[] temps = {73, 74, 75, 71, 69, 72, 76, 73};
        System.out.println("intermediate: dailyTemperatures -> " + java.util.Arrays.toString(dailyTemperatures(temps)));
    }

    // Advanced: previous smaller element (mirror of "next greater"), template flipped to walk and compare direction.
    static int[] previousSmallerElement(int[] nums) {
        int[] answer = new int[nums.length];
        java.util.Arrays.fill(answer, -1);
        Deque<Integer> stack = new ArrayDeque<>(); // values strictly increasing bottom to top

        for (int i = 0; i < nums.length; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] >= nums[i]) stack.pop(); // discard: cannot be anyone's answer anymore
            if (!stack.isEmpty()) answer[i] = nums[stack.peek()];
            stack.push(i);
        }
        return answer;
    }

    static void advancedLevel() {
        int[] nums = {4, 2, 5, 1, 3};
        System.out.println("advanced: previousSmallerElement([4,2,5,1,3]) -> " + java.util.Arrays.toString(previousSmallerElement(nums)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MonotonicStackTemplate.java`, then run `java MonotonicStackTemplate.java`.

## 6. Walkthrough

Trace `nextGreaterElement([2, 1, 5, 3])`:

| i | nums[i] | stack before | action | stack after | answer so far |
|---|---|---|---|---|---|
| 0 | 2 | `[]` | push 0 | `[0]` | `[-1,-1,-1,-1]` |
| 1 | 1 | `[0]` | 1 < 2, no pop; push 1 | `[0,1]` | `[-1,-1,-1,-1]` |
| 2 | 5 | `[0,1]` | 5>1 pop 1, answer[1]=5; 5>2 pop 0, answer[0]=5; push 2 | `[2]` | `[5,5,-1,-1]` |
| 3 | 3 | `[2]` | 3 < 5, no pop; push 3 | `[2,3]` | `[5,5,-1,-1]` |

Final answer: `[5, 5, -1, -1]`. Indices `2` and `3` (values `5` and `3`) never found anything bigger to their right, so they stay `-1`.

## 7. Gotchas & takeaways

> Gotcha: using `<` vs `<=` in the pop condition changes behavior on equal values — `nums[stack.peek()] < nums[i]` (strict) means equal values do NOT pop each other, so the *first* occurrence of a repeated value is treated as its own next-greater candidate rather than being immediately replaced. Match the strictness to what the problem asks (next *strictly* greater vs next greater-or-equal).

- A monotonic stack keeps its contents in strictly increasing or decreasing order by popping violators before each push.
- It solves "nearest bigger/smaller element" problems in O(n), since each element is pushed and popped at most once.
- The same template flips for four variants: next/previous, greater/smaller — only the comparison direction and scan direction change.
- Related concepts: [Next-greater-element problems](0069-next-greater-element-problems.md), [LIFO semantics](0062-lifo-semantics.md).
