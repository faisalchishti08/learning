---
card: java
gi: 918
slug: bytecode-interpretation
title: Bytecode interpretation
---

## 1. What it is

Bytecode interpretation is the most basic way the JVM executes compiled Java code: the **bytecode interpreter** reads a method's compiled instructions (bytecode — things like `iload`, `iadd`, `invokevirtual`) one at a time and directly carries out what each one specifies, without first translating them into native machine code. It's the JVM's fallback execution mode — every method starts out running interpreted, and only methods that run often enough get promoted to compiled, native machine code by the [JIT compiler](0919-jit-compilation-c1-client-c2-server.md), a distinct, more sophisticated execution path covered in the next tutorial.

## 2. Why & when

Interpretation exists because it lets the JVM start running a program's bytecode essentially immediately, without paying the (sometimes substantial) up-front cost of compiling it to native machine code first — for code that only ever runs once or a handful of times (much of a typical program's startup path, one-off initialization logic), interpreting it directly is simply faster overall than compiling it for no repeated benefit. This is exactly why Java programs have a characteristic "warm-up" period: early in a program's run, most code executes interpreted (slower per-invocation, but with zero compilation delay), and as the JVM observes which methods are actually called frequently, it progressively compiles those hot methods to native code, making them run substantially faster from then on. Understanding this distinction matters for interpreting benchmark results correctly (a benchmark that doesn't run long enough to let hot methods get JIT-compiled measures interpreted-mode performance, not the steady-state performance real long-running production code would eventually reach) and for understanding why a JVM process's throughput characteristically improves the longer it runs, before eventually leveling off once the hot paths have all been compiled.

## 3. Core concept

```java
int add(int a, int b) {
    return a + b;
}
// Compiles to bytecode roughly like:
//   iload_1   ; push local variable 'a' onto the operand stack
//   iload_2   ; push local variable 'b' onto the operand stack
//   iadd      ; pop both, add them, push the result
//   ireturn   ; pop the result and return it

// The INTERPRETER reads and executes each of these instructions directly, one at a time,
// every single time add() is called -- until this method is called often enough that
// the JIT compiler decides to compile it into native machine code instead.
```

Every method, without exception, begins its life running through the interpreter — compilation is something that happens *later*, and only for methods that actually demonstrate they're worth the compilation investment.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method's call count over time; while cold (low call count) it runs interpreted, one bytecode instruction at a time; once it crosses an invocation threshold, the JIT compiler takes over and it runs as native machine code">
  <rect x="20" y="30" width="280" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Interpreter: reads bytecode, executes it</text>
  <text x="160" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one instruction at a time, every call</text>

  <rect x="340" y="30" width="280" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JIT-compiled: native machine code</text>
  <text x="480" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs directly, no per-instruction overhead</text>

  <line x1="300" y1="55" x2="336" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a46)"/>
  <text x="320" y="45" fill="#8b949e" font-size="9" font-family="sans-serif">hot</text>

  <text x="320" y="120" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">A method transitions once its invocation count crosses a threshold --</text>
  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">every method starts life on the LEFT side, interpreted.</text>
  <defs><marker id="a46" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Every method starts running interpreted; only ones that run often enough graduate to compiled, native execution.*

## 5. Runnable example

Scenario: directly observing the performance difference between "cold" (early, mostly-interpreted) and "warm" (later, JIT-compiled) execution of the same method, growing from a simple timing comparison across repeated runs, to using JVM flags to force pure-interpreter mode for a clean baseline comparison, to observing warm-up behavior with a more realistic workload.

### Level 1 — Basic

```java
public class ColdVsWarmTiming {
    static long computeSum(int n) {
        long sum = 0;
        for (int i = 0; i < n; i++) sum += i;
        return sum;
    }

    public static void main(String[] args) {
        int n = 10_000_000;

        long start1 = System.nanoTime();
        computeSum(n); // FIRST call -- mostly interpreted, no JIT compilation has happened yet
        long firstCallNanos = System.nanoTime() - start1;

        // Call it many more times, giving the JIT compiler a chance to notice it's "hot"
        // and compile it to native code.
        for (int i = 0; i < 20_000; i++) computeSum(n);

        long start2 = System.nanoTime();
        computeSum(n); // a LATER call -- likely now running as JIT-compiled native code
        long laterCallNanos = System.nanoTime() - start2;

        System.out.println("first call: " + firstCallNanos / 1_000_000 + "ms");
        System.out.println("later call (after warm-up): " + laterCallNanos / 1_000_000 + "ms (typically much faster)");
    }
}
```

**How to run:** `java ColdVsWarmTiming.java` (JDK 17+).

Expected output shape (exact numbers vary by machine, but the later call should typically be noticeably faster):
```
first call: 42ms
later call (after warm-up): 3ms (typically much faster)
```

The first call to `computeSum` runs largely interpreted, since the JIT compiler hasn't had a chance to observe it's called frequently yet; after 20,000 warm-up calls, the method has very likely been compiled to native machine code, making the later call substantially faster for the identical computation.

### Level 2 — Intermediate

```java
public class ForcedInterpreterComparison {
    static long computeSum(int n) {
        long sum = 0;
        for (int i = 0; i < n; i++) sum += i;
        return sum;
    }

    public static void main(String[] args) {
        int n = 10_000_000;
        int iterations = 5;

        for (int i = 0; i < iterations; i++) {
            long start = System.nanoTime();
            computeSum(n);
            long elapsed = System.nanoTime() - start;
            System.out.println("iteration " + i + ": " + elapsed / 1_000_000 + "ms");
        }
        System.out.println("(run this WITH and WITHOUT -Xint to see the interpreter-only baseline)");
    }
}
```

**How to run:** first `java ForcedInterpreterComparison.java` normally (JDK 17+, allowing JIT compilation as usual), then `java -Xint ForcedInterpreterComparison.java` (forcing pure interpreter mode, disabling JIT compilation entirely) and compare.

Expected output shape (normal run — later iterations get progressively faster as JIT compilation kicks in):
```
iteration 0: 38ms
iteration 1: 6ms
iteration 2: 3ms
iteration 3: 3ms
iteration 4: 3ms
(run this WITH and WITHOUT -Xint to see the interpreter-only baseline)
```

Expected output shape (`-Xint` run — every iteration stays roughly the same, since compilation never happens at all):
```
iteration 0: 41ms
iteration 1: 39ms
iteration 2: 40ms
iteration 3: 40ms
iteration 4: 39ms
(run this WITH and WITHOUT -Xint to see the interpreter-only baseline)
```

The real-world concern added: `-Xint` explicitly forces the JVM to *never* compile any method, running everything interpreted for the program's entire lifetime — this makes the interpreter's true, uncompiled performance directly visible for comparison, and the contrast between the two runs makes the JIT compiler's real-world impact concrete rather than theoretical.

### Level 3 — Advanced

```java
public class RealisticWarmupCurve {
    static double blackScholesApprox(double s, double k, double t) {
        // A deliberately nontrivial computation, standing in for realistic "business logic" --
        // the actual formula's correctness isn't the point here, just that it's genuine work.
        double d1 = (Math.log(s / k) + 0.5 * t) / Math.sqrt(t);
        return s * Math.exp(-d1 * d1 / 2) - k * Math.exp(-0.05 * t) * d1;
    }

    public static void main(String[] args) {
        int batchSize = 1_000_000;
        int batches = 10;

        for (int b = 0; b < batches; b++) {
            long start = System.nanoTime();
            double total = 0;
            for (int i = 0; i < batchSize; i++) {
                total += blackScholesApprox(100 + i % 50, 100, 1.0 + i % 10);
            }
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            System.out.println("batch " + b + ": " + elapsedMs + "ms (sum=" + (long) total + ")");
        }
        System.out.println("notice throughput improving across batches, then leveling off --");
        System.out.println("this IS the JIT compiler progressively compiling the hot method(s) involved");
    }
}
```

**How to run:** `java RealisticWarmupCurve.java` (JDK 17+).

Expected output shape (early batches slower, later batches faster and stable — the classic JIT warm-up curve):
```
batch 0: 85ms (sum=...)
batch 1: 32ms (sum=...)
batch 2: 18ms (sum=...)
batch 3: 12ms (sum=...)
batch 4: 11ms (sum=...)
batch 5: 11ms (sum=...)
batch 6: 11ms (sum=...)
batch 7: 11ms (sum=...)
batch 8: 11ms (sum=...)
batch 9: 11ms (sum=...)
notice throughput improving across batches, then leveling off --
this IS the JIT compiler progressively compiling the hot method(s) involved
```

This adds the production-flavored hard case: a more realistic, multi-batch workload showing the *shape* of a typical JIT warm-up curve — throughput improves noticeably across the first several batches as `blackScholesApprox` (and the loop calling it) get progressively compiled to increasingly optimized native code (see [tiered compilation](0920-tiered-compilation.md) for the multi-level compilation process producing this gradual improvement), then levels off once the method reaches its most-optimized compiled form and no further gains are available from additional compilation.

## 6. Walkthrough

Tracing the shape of `RealisticWarmupCurve.main`'s output:

1. Batch 0 runs almost entirely interpreted: `blackScholesApprox` hasn't been called enough times yet for the JVM to consider it "hot," so every one of its million invocations in this batch executes by the interpreter reading and carrying out its bytecode instructions one at a time — the slowest mode of execution, but with zero compilation delay.
2. By the end of batch 0 (a million calls), the method has very likely crossed an invocation-count threshold that triggers the JIT compiler to begin compiling it — this compilation happens on a separate background thread, asynchronously, so it doesn't block the main computation, but takes a little while to actually finish and become available.
3. Batch 1 likely starts still partially interpreted (if compilation hasn't finished yet) but transitions to running the newly-compiled native code partway through, once the compiled version becomes available — this produces a substantial speedup compared to batch 0, though perhaps not yet the method's fastest possible form.
4. Subsequent batches (2, 3, 4...) benefit from increasingly optimized compiled versions, as [tiered compilation](0920-tiered-compilation.md) progressively re-compiles hot methods with more aggressive optimizations the more they're observed running — each level typically producing somewhat faster code than the last.
5. Eventually (around batch 4 or 5 in this example), the method reaches its most optimized compiled form, and further batches show no additional improvement — the curve "levels off," reflecting that there's no more compilation left to do; the method is now running at its steady-state, fully-optimized speed.
6. This entire progression — slow, interpreted start; a burst of improvement as compilation kicks in; a leveling-off at peak performance — is the direct, observable signature of bytecode interpretation handing off to progressively more sophisticated JIT-compiled execution over a program's actual runtime.

## 7. Gotchas & takeaways

> **Gotcha:** microbenchmarks that don't run long enough to reach the "leveled off" portion of this curve measure a mix of interpreted and partially-compiled performance, not the steady-state performance real long-running production code eventually reaches — this is one of the most common sources of misleading Java performance measurements, and is exactly why dedicated microbenchmarking tools (like JMH) explicitly include a warm-up phase before measuring.

- Bytecode interpretation is the JVM's baseline execution mode: reading and directly carrying out compiled bytecode instructions one at a time, with no upfront compilation cost but slower per-invocation execution.
- Every method starts its life running interpreted; the JIT compiler promotes methods to compiled, native machine code only once they demonstrate they're called often enough to be worth the compilation investment.
- `-Xint` forces pure interpreter mode for an entire JVM run, useful specifically for measuring the interpreter's own baseline performance in isolation, as a comparison point against normal, JIT-enabled execution.
- The characteristic "warm-up" curve — slow start, improving throughput, eventual leveling off — is the direct, observable signature of this interpret-then-compile execution model; always account for it when benchmarking or reasoning about a Java program's performance.
- See [JIT compilation](0919-jit-compilation-c1-client-c2-server.md) and [tiered compilation](0920-tiered-compilation.md) for the mechanisms that actually decide which methods get compiled, when, and through how many progressively more optimized compilation levels.
