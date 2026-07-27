---
card: leetcode-patterns
gi: 466
slug: monotonic-stack-signal-next-greater-smaller-element-or-histo
title: Monotonic Stack — signal: next greater/smaller element or histogram spans
---

## 1. What it is

A monotonic stack is a stack that you keep strictly increasing or strictly decreasing from bottom to top. Before you push a new element, you pop off every element that would break that order. The pops are not wasted work — each popped element just found its answer (its next greater or next smaller neighbor).

## 2. Why & when

Reach for a monotonic stack when a brute-force solution scans forward from every index to find "the next element that is bigger" or "the next element that is smaller," giving O(n²) time. A monotonic stack answers all of these in one O(n) pass, because each element is pushed once and popped at most once.

Learn to recognize these signals in a problem statement:

- **"Find the next greater (or smaller) element"** for every position in an array. This is the textbook use case: "Next Greater Element," "Daily Temperatures."
- **"Find the previous greater (or smaller) element."** Same idea, scanned from the other direction or with the answer stored differently.
- **A histogram, skyline, or bar-heights problem** asking for the largest rectangle or the span a bar can "see" before a taller bar blocks it. The stack tracks bars whose maximum extent is not yet known.
- **"Remove some elements to make the sequence as small/large as possible"** while keeping relative order — problems like "Remove K Digits" or "Remove Duplicate Letters" use a monotonic stack to greedily discard elements that violate an ordering rule.
- **Stock span or "how many consecutive days behind me were smaller"** — the answer is the distance back to the last element that breaks monotonicity.

The alternative is a nested loop (O(n²)) or, for range-minimum-style problems, a segment tree (O(n log n), more code). A monotonic stack is the answer whenever the question is about the *nearest* element satisfying an ordering comparison, in O(n) time.

## 3. Core concept

**Key idea:** as you scan left to right, maintain a stack where values are monotonic (say, decreasing top to bottom). When the current element breaks that order — it is bigger than the value at the top — that top element has just found its "next greater element": the current one. Pop it, record the answer, and repeat until the stack is monotonic again, then push the current element.

**General steps:**
1. Choose the direction of monotonicity based on what you are asked for (increasing stack for "next smaller," decreasing stack for "next greater").
2. Walk the input left to right (or right to left, depending on the problem).
3. While the stack is not empty and the current element violates the order (e.g. current is greater than the top, for a decreasing stack), pop the top and record the current element as its answer.
4. Push the current element (or its index) onto the stack.
5. After the scan, anything left on the stack has no answer within the array (return -1 or a sentinel for those).

**Why it works:** every element is pushed exactly once and popped at most once, so the total number of push and pop operations across the whole run is at most 2n. That bounds the total work at O(n), even though it looks like nested loops (a `while` inside a `for`).

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decreasing monotonic stack popping elements as a taller bar arrives">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Array: [3, 1, 4, 1, 5] -- find next greater element</text>
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="50" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="170" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="95" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="145" y="63" fill="#79c0ff" text-anchor="middle">4</text>
    <text x="195" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="245" y="63" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="145" y="95" fill="#79c0ff" text-anchor="middle">arrives, pops 3 and 1</text>
    <text x="20" y="130" fill="#8b949e">Stack before index 2: [3, 1] (bottom to top, decreasing)</text>
    <text x="20" y="150" fill="#3fb950">4 &gt; 1: pop 1, answer(1) = 4</text>
    <text x="20" y="170" fill="#3fb950">4 &gt; 3: pop 3, answer(3) = 4</text>
    <text x="20" y="190" fill="#8b949e">Stack after: [4]. Push continues with the rest of the array.</text>
  </g>
</svg>

Each new taller bar pops every shorter bar below it off the stack, and each pop resolves one element's "next greater" answer.

## 5. Runnable example

The artifact below is a reusable signal-checker: given an array, it reports whether "next greater element" queries on it are worth solving with a monotonic stack (they always are, in O(n) — this demonstrates the win over brute force by counting comparisons).

### Signal-checker

```java
// MonotonicStackSignal.java
import java.util.*;

public class MonotonicStackSignal {

    // Counts comparisons for a brute-force "next greater element" scan.
    static int bruteForceComparisons(int[] arr) {
        int comparisons = 0;
        for (int i = 0; i < arr.length; i++) {
            for (int j = i + 1; j < arr.length; j++) {
                comparisons++;
                if (arr[j] > arr[i]) break;
            }
        }
        return comparisons;
    }

    // Counts push/pop operations for the monotonic-stack version.
    static int stackOperations(int[] arr) {
        Deque<Integer> stack = new ArrayDeque<>();
        int ops = 0;
        for (int num : arr) {
            while (!stack.isEmpty() && stack.peek() < num) {
                stack.pop();
                ops++;
            }
            stack.push(num);
            ops++;
        }
        return ops;
    }

    public static void main(String[] args) {
        int[] worstCase = {5, 4, 3, 2, 1, 6}; // last element is bigger than everything
        System.out.println("brute force comparisons: " + bruteForceComparisons(worstCase));
        System.out.println("monotonic stack operations: " + stackOperations(worstCase));
        System.out.println("-> stack operations stay at or below 2n = " + (2 * worstCase.length));
    }
}
```

**How to run:** save as `MonotonicStackSignal.java`, then run `java MonotonicStackSignal.java`.

## 6. Walkthrough

1. You read a problem asking: "for each element, find the next element to its right that is strictly greater." That phrase — "next greater" — is the signal.
2. You decide to keep a **decreasing** stack (top is always the smallest element seen that has no answer yet), because you are popping elements when a *bigger* one shows up.
3. On `worstCase = {5, 4, 3, 2, 1, 6}`, the brute-force method compares every pair until it finds a bigger element to the right, which for this input costs many comparisons (each of `5, 4, 3, 2, 1` scans ahead to find `6`).
4. The monotonic-stack version pushes `5, 4, 3, 2, 1` without any pops (each is smaller than the one before, so the stack stays decreasing). When `6` arrives, it pops all five in one pass — five pops, five earlier pushes, one final push — a total bounded by `2n`.
5. Printing both counts confirms the stack version scales linearly, even on this worst-case input, while the brute-force count grows toward the nested-loop bound.

## 7. Gotchas & takeaways

> Gotcha: mixing up "next greater" and "next smaller" flips which direction the stack must stay monotonic. If you push blindly without checking which comparison the problem wants, you will pop the wrong elements and get answers for the wrong query.

- Signal words: "next greater," "next smaller," "previous greater/smaller," "histogram," "span," "how many days until."
- Decreasing stack for "next greater element" queries; increasing stack for "next smaller element" queries.
- Each element is pushed once and popped at most once, so the pattern is always O(n) time.
