---
card: java
gi: 913
slug: jvm-stacks-stack-frames
title: JVM stacks & stack frames
---

## 1. What it is

Every thread has its own private JVM stack — a memory region entirely separate from the shared [heap](0911-heap.md) — that tracks the sequence of method calls currently in progress on that thread. Each time a method is called, a new **stack frame** is pushed onto that thread's stack; each frame holds the method's local variables (including primitive values and object references — though the *objects* those references point to live on the heap), an operand stack (used internally by the JVM to evaluate expressions and pass arguments), and a reference back to the calling frame's constant pool for resolving symbolic references. When a method returns, its frame is popped and discarded.

## 2. Why & when

Understanding stack frames explains two everyday phenomena directly: why `StackOverflowError` happens (each thread's stack has a bounded size, and deep or unbounded recursion keeps pushing frames until that bound is exceeded), and why a stack trace — the sequence of "at com.example.Foo.bar(Foo.java:42)" lines printed with every exception — is simply a snapshot of the frames currently on the stack at the moment the exception was created, read from the top (innermost, currently-executing call) down to the bottom (the outermost call, typically `main`). It matters directly whenever you're debugging a `StackOverflowError` (is there a legitimate deep call chain, or a broken recursive base case?), tuning thread stack size for a program that needs deeper recursion than the default allows (`-Xss`), or simply reading a stack trace and understanding exactly what it represents — an ordered record of "what called what," not an arbitrary log.

## 3. Core concept

```java
void methodA() {
    int x = 5;          // local variable in methodA's stack frame
    methodB();           // pushes a NEW frame for methodB onto THIS thread's stack
}
void methodB() {
    int y = 10;          // local variable in methodB's OWN, separate stack frame
    // methodA's frame (and its x) still exists below this one, on the same stack
}
// When methodB returns, its frame is popped; methodA's frame (and x) is still there, resuming execution.
```

Each thread has its own entirely separate stack — one thread's stack frames are never visible to or shared with another thread, which is exactly why local variables never need synchronization the way shared, heap-resident objects do.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A thread's stack growing as methods call other methods, each getting its own frame with local variables, and shrinking as methods return and their frames are popped">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">One thread's private stack</text>
  <rect x="60" y="30" width="200" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">main() frame</text>

  <rect x="60" y="75" width="200" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="97" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">methodA() frame -- x=5</text>

  <rect x="60" y="120" width="200" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">methodB() frame -- y=10 (TOP)</text>

  <text x="450" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">grows DOWN as calls nest deeper</text>
  <line x1="270" y1="47" x2="400" y2="47" stroke="#8b949e" stroke-width="1.5"/>
  <text x="450" y="140" fill="#8b949e" font-size="10" font-family="sans-serif">shrinks UP as methods return</text>
  <line x1="270" y1="137" x2="400" y2="137" stroke="#8b949e" stroke-width="1.5"/>
</svg>

*Each nested call pushes a new frame on top; each return pops the topmost frame — the stack trace of an exception is exactly this structure, read top to bottom.*

## 5. Runnable example

Scenario: observing stack depth directly through recursion, growing from a basic recursive function printing its own depth, to deliberately triggering and inspecting a `StackOverflowError`, to comparing default versus explicitly-configured thread stack sizes to allow deeper recursion.

### Level 1 — Basic

```java
public class ObservingStackDepth {
    static int countDown(int n) {
        if (n <= 0) return 0;
        int result = 1 + countDown(n - 1); // each call PUSHES a new frame
        return result;
    }

    public static void main(String[] args) {
        int depth = 1000;
        int result = countDown(depth);
        System.out.println("recursed " + depth + " levels deep, final result = " + result);
        System.out.println("(each level was its own stack frame, all on THIS thread's stack)");
    }
}
```

**How to run:** `java ObservingStackDepth.java` (JDK 17+).

Expected output:
```
recursed 1000 levels deep, final result = 1000
(each level was its own stack frame, all on THIS thread's stack)
```

Each recursive call to `countDown` pushes a new frame holding its own `n` and `result` locals — 1000 nested frames exist simultaneously on the stack at the deepest point, before any of them return and get popped.

### Level 2 — Intermediate

```java
public class TriggeringStackOverflow {
    static int recurseForever(int depth) {
        return 1 + recurseForever(depth + 1); // NO base case -- will recurse until the stack is exhausted
    }

    public static void main(String[] args) {
        try {
            recurseForever(0);
        } catch (StackOverflowError e) {
            StackTraceElement[] trace = e.getStackTrace();
            System.out.println("StackOverflowError caught -- stack trace has " + trace.length + " frames captured");
            System.out.println("top frame: " + trace[0]);
            System.out.println("(the thread's stack ran out of space for MORE frames, since this recursion has no base case)");
        }
    }
}
```

**How to run:** `java TriggeringStackOverflow.java`.

Expected output shape (exact frame count varies by default stack size and per-frame overhead, but is a large, consistent number reflecting how many `recurseForever` frames fit before exhaustion):
```
StackOverflowError caught -- stack trace has 1024 frames captured
top frame: TriggeringStackOverflow.recurseForever(TriggeringStackOverflow.java:3)
```

The real-world concern added: an unbounded recursive call chain (no base case) keeps pushing new frames until the thread's stack — a fixed-size region — has no room left, producing `StackOverflowError`; the caught error's own stack trace is itself a direct, inspectable record of (a truncated view of) exactly which frames were on the stack at the moment of exhaustion.

### Level 3 — Advanced

```java
public class ComparingStackSizes {
    static int countDeepestPossible(int n) {
        try {
            return countDeepestPossible(n + 1);
        } catch (StackOverflowError e) {
            return n; // report how deep we got before overflowing
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int[] defaultDepth = new int[1];
        Thread defaultStackThread = new Thread(() -> defaultDepth[0] = countDeepestPossible(0));
        defaultStackThread.start();
        defaultStackThread.join();
        System.out.println("default stack size reached depth: " + defaultDepth[0]);

        int[] largeDepth = new int[1];
        // Explicitly requesting a LARGER stack size for this specific thread via the
        // Thread constructor overload that accepts a stack size hint (JVM-dependent, best-effort).
        Thread largeStackThread = new Thread(null, () -> largeDepth[0] = countDeepestPossible(0),
            "large-stack-thread", 16 * 1024 * 1024); // 16MB requested stack size
        largeStackThread.start();
        largeStackThread.join();
        System.out.println("16MB stack size reached depth: " + largeDepth[0] + " (typically much deeper)");
    }
}
```

**How to run:** `java ComparingStackSizes.java` (JDK 17+).

Expected output shape (exact depths are highly JVM/platform-dependent, but the larger-stack thread should reach a substantially greater depth):
```
default stack size reached depth: 10842
16MB stack size reached depth: 87213 (typically much deeper)
```

This adds the production-flavored hard case: explicitly configuring a larger stack size for a specific thread (via the `Thread` constructor overload accepting a stack-size hint, which the JVM treats as a best-effort request, not an absolute guarantee) — demonstrating concretely that recursion depth before `StackOverflowError` is not some fixed universal Java limit, but is directly determined by the actual configured stack size of the specific thread doing the recursing, since a larger stack simply has room for more simultaneously-pending frames before exhaustion.

## 6. Walkthrough

Tracing why `largeStackThread` reaches a much greater recursion depth than `defaultStackThread`:

1. `defaultStackThread` is created with the ordinary `Thread(Runnable)` constructor, which uses the JVM's default per-thread stack size (commonly around 512KB–1MB on typical desktop JVM configurations, though this varies by platform and JVM settings).
2. Each nested call to `countDeepestPossible` pushes a new stack frame consuming some fixed amount of space (holding its own `n` parameter, its own tiny operand-stack usage for the arithmetic, and bookkeeping); with a smaller total stack budget, only a limited number of such frames fit before the JVM detects the stack is exhausted and throws `StackOverflowError`.
3. The `catch (StackOverflowError e) { return n; }` block runs in a context where the stack has *just* been detected as exhausted — the JVM typically reserves a small margin so that at least a modest amount of further execution (like this catch block, a few more method calls) remains possible immediately after the error is thrown, without immediately overflowing again.
4. `largeStackThread` is created via the `Thread(ThreadGroup, Runnable, String, long)` constructor, explicitly passing `16 * 1024 * 1024` (16MB) as a *requested* stack size — since this thread's total per-frame budget is dramatically larger than the default, substantially more nested `countDeepestPossible` frames fit before the same exhaustion condition is reached.
5. Both threads run the exact same recursive method with the exact same per-frame memory cost — the only variable is the total stack size available to each thread, which is precisely why the reported depths differ so significantly between them.
6. This demonstrates directly that `StackOverflowError`'s trigger point is a property of the specific thread's configured stack size, not an inherent property of the Java language or a fixed constant — code that overflows on one thread configuration might run successfully to a much greater depth on a thread configured with a larger stack.

## 7. Gotchas & takeaways

> **Gotcha:** the `Thread` constructor's stack-size parameter is explicitly documented as a hint the JVM is free to ignore or adjust — some JVM implementations or platforms may not honor it precisely, or may round it to a platform-specific minimum/maximum; never assume it as a hard guarantee, only as a best-effort request.

- Each thread has its own private stack, entirely separate from the shared heap; each method call pushes a new stack frame holding that call's local variables and operand-stack workspace, popped when the method returns.
- `StackOverflowError` occurs when a thread's stack has no room left for another frame — almost always caused by excessively deep or genuinely unbounded (missing base case) recursion.
- A stack trace is literally a snapshot of the frames present on a thread's stack at a given moment (typically, when an exception object is constructed) — reading one top-to-bottom is reading the call chain from innermost to outermost.
- A thread's stack size can be explicitly requested via a `Thread` constructor overload, allowing deeper recursion than the JVM's platform default, though this is a best-effort hint, not a guarantee, and is JVM/platform-dependent.
- See [the program counter register](0914-program-counter-pc-register.md) and [native method stacks](0915-native-method-stacks.md) for the other two per-thread runtime data areas that, together with the JVM stack, make up a thread's complete private execution state.
