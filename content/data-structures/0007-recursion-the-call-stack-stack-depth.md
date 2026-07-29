---
card: data-structures
gi: 7
slug: recursion-the-call-stack-stack-depth
title: Recursion, the call stack & stack depth
---

## 1. What it is

**Recursion** is a function calling itself to solve a smaller version of the same problem, until reaching a **base case** that returns directly without further recursion. Every recursive (and non-recursive) function call is tracked by the runtime's **call stack** — a stack of "stack frames," each holding one in-progress function call's local variables and its return address. **Stack depth** is how many frames are currently on that stack; recursion that goes too deep without reaching a base case exhausts the stack, causing a `StackOverflowError`.

## 2. Why & when

Understanding the call stack is essential for reasoning about *any* recursive function's memory cost and failure modes — recursion is not "free" just because it looks like elegant math; each recursive call consumes real memory for its stack frame, and that memory is only released when the call returns. Recognize the signal whenever a problem naturally decomposes into "solve a smaller version of the same problem, then combine" (trees, divide-and-conquer, backtracking) — but also recognize when input size makes deep recursion risky.

## 3. Core concept

**How the call stack works, step by step:** when function `f` calls function `g`, a new stack frame for `g` is pushed on top of the stack, containing `g`'s parameters, local variables, and the address to return to once `g` finishes. `g` runs; if `g` calls another function, another frame is pushed on top of *that*. When a function returns, its frame is popped off the stack, and execution resumes in the frame now on top.

**Why recursion directly corresponds to stack depth:** each recursive call to `f` pushes a new frame for that specific call, even though it is "the same function" being called again — the runtime does not know or care that it is recursion; it simply pushes a frame for every call, recursive or not. A recursive function that calls itself `n` times before reaching its base case builds up `n` stack frames, all still "in progress," waiting for the base case to return so they can unwind one by one.

**Why deep recursion causes `StackOverflowError`:** the call stack has a fixed, finite size (configurable via JVM flags like `-Xss`, but always finite). Each stack frame consumes some fixed amount of that space. A recursive function with no base case, or one whose base case is only reached after too many calls (for example, naive recursion over an array of a million elements, one call per element), can exhaust the entire stack before ever returning — the JVM detects this and throws `StackOverflowError` rather than corrupting memory.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stack frames piling up during recursive calls to factorial(3), then unwinding as base case is reached and each call returns">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">building up (calls)</text>
    <rect x="60" y="30" width="180" height="30" fill="#161b22" stroke="#30363d"/><text x="150" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">factorial(3)</text>
    <rect x="60" y="60" width="180" height="30" fill="#161b22" stroke="#30363d"/><text x="150" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">factorial(2)</text>
    <rect x="60" y="90" width="180" height="30" fill="#161b22" stroke="#3fb950"/><text x="150" y="110" fill="#e6edf3" text-anchor="middle" font-size="11">factorial(1) - base case</text>
    <text x="500" y="20" fill="#8b949e" text-anchor="middle">unwinding (returns)</text>
    <text x="500" y="50" fill="#79c0ff" text-anchor="middle">factorial(1) returns 1</text>
    <text x="500" y="80" fill="#79c0ff" text-anchor="middle">factorial(2) returns 2*1=2</text>
    <text x="500" y="110" fill="#79c0ff" text-anchor="middle">factorial(3) returns 3*2=6</text>
  </g>
</svg>

Each recursive call pushes a new frame on top; the base case's frame returns first, and each waiting frame above it resumes and returns in turn, unwinding the stack in reverse order.

## 5. Runnable example

**Level 1 — Basic.** A simple recursive factorial demonstrating normal call-stack growth and unwinding for small `n`.

**Level 2 — Measuring depth.** Track and print the actual recursion depth reached, to see the stack grow in real time.

**Level 3 — Triggering a StackOverflowError deliberately.** Demonstrate what happens when recursion depth exceeds the stack's capacity, and how to catch it.

```java
// RecursionCallStack.java
public class RecursionCallStack {

    // Level 1: basic recursion.
    static long factorial(int n) {
        if (n <= 1) return 1; // base case
        return n * factorial(n - 1); // recursive case
    }

    // Level 2: track depth explicitly.
    static int maxDepthSeen = 0;
    static long factorialWithDepthTracking(int n, int depth) {
        maxDepthSeen = Math.max(maxDepthSeen, depth);
        if (n <= 1) return 1;
        return n * factorialWithDepthTracking(n - 1, depth + 1);
    }

    // Level 3: recursion with no base case ever reached - will overflow the stack.
    static int countUntilOverflow(int depth) {
        return 1 + countUntilOverflow(depth + 1); // no base case: recurses forever
    }

    public static void main(String[] args) {
        System.out.println("factorial(5) = " + factorial(5));

        factorialWithDepthTracking(5, 1);
        System.out.println("max recursion depth for factorial(5): " + maxDepthSeen);

        try {
            countUntilOverflow(0);
        } catch (StackOverflowError e) {
            System.out.println("caught StackOverflowError: the call stack has a finite size");
        }
    }
}
```

**How to run:** save as `RecursionCallStack.java`, then run `java RecursionCallStack.java`.

## 6. Walkthrough

1. `factorial(5)` calls `factorial(4)`, which calls `factorial(3)`, and so on, down to `factorial(1)`, which hits the base case and returns `1` directly without recursing further.
2. Each of these calls is still "on the stack," waiting: `factorial(2)`'s call to `factorial(1)` has not returned yet when `factorial(1)` starts running, so `factorial(2)`'s frame remains on the stack the whole time `factorial(1)` executes.
3. Once `factorial(1)` returns `1`, `factorial(2)` resumes and computes `2 * 1 = 2`, then returns. `factorial(3)` resumes and computes `3 * 2 = 6`, and so on, unwinding all the way back up to the original `factorial(5)` call.
4. `factorialWithDepthTracking(5, 1)` confirms this directly: `maxDepthSeen` reaches `5`, matching the five nested calls (`factorial(5)` through `factorial(1)`) that were simultaneously on the stack at the deepest point.
5. `countUntilOverflow` has no base case — it recurses forever, each call pushing one more frame, until the JVM's stack space is exhausted and a `StackOverflowError` is thrown, caught here to demonstrate the failure mode without crashing the whole program.

## 7. Gotchas & takeaways

> Gotcha: recursion over a large input (a linked list or array with hundreds of thousands of elements, using one recursive call per element) can hit `StackOverflowError` even though the *algorithm* is logically correct — the fix is usually converting to an iterative loop, or restructuring the recursion to be tail-recursive (though Java, unlike some languages, does not automatically optimize tail calls to avoid stack growth).

- Every function call, recursive or not, pushes a stack frame; recursion depth directly equals how many frames are simultaneously "in progress" and unreturned.
- A missing or unreachable base case causes unbounded recursion, which always eventually crashes with `StackOverflowError`, since the call stack's size is finite.
- Related concepts: [Recursive vs iterative tradeoffs](0008-recursive-vs-iterative-tradeoffs.md) (when to prefer an iterative rewrite specifically to avoid stack-depth risk), [Stack vs heap allocation](0011-stack-vs-heap-allocation.md) (the broader memory-model context the call stack is part of).
