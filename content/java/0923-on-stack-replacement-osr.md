---
card: java
gi: 923
slug: on-stack-replacement-osr
title: On-stack replacement (OSR)
---

## 1. What it is

On-stack replacement (OSR) lets the JVM swap a currently-*executing* method's interpreted execution for compiled native code **mid-execution**, without waiting for the method to return and be called again. Ordinarily, JIT compilation only takes effect on a method's *next* invocation — but a single method call containing a long-running loop (one that never returns, or takes a very long time to) would never get the benefit of compilation at all under that rule, since it's still running the very first (and only) time it's called. OSR specifically targets exactly this case: the JVM detects a loop that's iterating a large number of times, compiles the containing method (or specifically the hot loop) in the background, and then transfers execution — including reconstructing the loop's current local variable state — directly into the newly-compiled code, continuing from wherever the loop currently was, without restarting it.

## 2. Why & when

Without OSR, a single call to a method with a very long-running loop (processing a huge array in one pass, an event loop, a long computation) would run entirely interpreted for its whole duration, since normal JIT compilation only benefits *future* calls to a method, and this call never returns to make another call possible. This matters directly for any program with long-lived, loop-heavy single invocations — a `main` method's own top-level loop is the single most common example, since `main` is typically called exactly once, for the entire life of the program, and any hot loop directly inside it would otherwise never benefit from compilation without OSR specifically detecting and compiling it mid-flight. Understanding OSR explains why even code inside `main` itself (not refactored into a separate, repeatedly-called method) still benefits from JIT compilation, and explains a specific, sometimes-visible characteristic in profiling output: a brief transition point partway through a long-running loop's execution, right where OSR compilation kicks in and execution jumps into newly-compiled code.

## 3. Core concept

```java
public static void main(String[] args) {
    long total = 0;
    for (long i = 0; i < 10_000_000_000L; i++) { // a SINGLE, very long-running loop, inside main() itself
        total += i % 7;
    }
    // Without OSR, this ENTIRE loop -- called only once, in the single main() invocation --
    // would run interpreted for its full 10 billion iterations. OSR detects this loop is hot
    // PARTWAY THROUGH, compiles it, and transfers execution into the compiled version --
    // continuing seamlessly from wherever the loop currently is, without restarting from i=0.
    System.out.println(total);
}
```

The loop's logic never changes from the programmer's perspective — OSR is entirely a JVM-internal mechanism that makes long-running, single-invocation loops benefit from compilation exactly as if they had been structured as a repeatedly-called method all along.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A long-running loop starts interpreted; partway through, the JVM detects it is hot, compiles it in the background, and performs on-stack replacement to transfer execution into the compiled version, continuing from the current iteration without restarting">
  <rect x="20" y="60" width="220" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="130" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Interpreted (i = 0 ... N)</text>

  <rect x="400" y="60" width="220" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Compiled (i = N ... 10 billion)</text>

  <rect x="260" y="20" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OSR: swap in place</text>
  <line x1="240" y1="70" x2="320" y2="48" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a50)"/>
  <line x1="320" y1="48" x2="400" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a50)"/>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Loop state (i, total, ...) is preserved across the transition -- execution CONTINUES, never restarts.</text>
  <defs><marker id="a50" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Execution transitions from interpreted to compiled code mid-loop, with the loop's current state carried across seamlessly, rather than restarting from the beginning.*

## 5. Runnable example

Scenario: observing OSR's effect on a single, long-running loop directly inside `main`, growing from a basic demonstration of a long single-invocation loop benefiting from compilation, to using JVM logging to directly observe an OSR compilation event, to comparing against an artificially forced-interpreter-only run to quantify OSR's real contribution.

### Level 1 — Basic

```java
public class LongRunningLoopInMain {
    public static void main(String[] args) {
        long start = System.nanoTime();
        long total = 0;
        for (long i = 0; i < 2_000_000_000L; i++) { // ONE loop, called ONCE, inside main() itself
            total += i % 7;
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms");
        System.out.println("(this single loop STILL got JIT-compiled partway through, via OSR)");
    }
}
```

**How to run:** `java LongRunningLoopInMain.java` (JDK 17+).

Expected output shape (fast enough that pure interpretation for all 2 billion iterations clearly did not happen — evidence OSR kicked in):
```
total=..., elapsed=1850ms
(this single loop STILL got JIT-compiled partway through, via OSR)
```

Even though this loop lives entirely within `main`, which is called exactly once for the whole program, it still completes fast enough to strongly suggest compiled, not purely interpreted, execution — this is OSR's direct, if indirect, effect.

### Level 2 — Intermediate

```java
public class ObservingOsrCompilation {
    public static void main(String[] args) {
        long total = 0;
        for (long i = 0; i < 1_000_000_000L; i++) {
            total += i % 7;
        }
        System.out.println("total=" + total);
    }
}
```

**How to run:** `java -XX:+PrintCompilation ObservingOsrCompilation.java 2>&1 | grep "%"` (JDK 17+; in HotSpot's `-XX:+PrintCompilation` log output, a `%` character in the compilation log line specifically marks an **OSR** compilation event, distinguishing it from ordinary, whole-method compilation events).

Expected output shape (the `%` marker and `@ N` notation, where `N` is the bytecode offset OSR occurred at, are the key signals):
```
   134   38 %     3       ObservingOsrCompilation::main @ 4 (23 bytes)
   210   52 %     4       ObservingOsrCompilation::main @ 4 (23 bytes)
total=3000000000
```

The real-world concern added: the `%` marker in the compilation log directly and explicitly identifies these as OSR compilation events, specifically for `main`'s loop — first at a C1 tier, then later re-OSR'd at C2 as the loop continues running and proves itself hot enough for the deeper optimization — concrete, JVM-provided evidence of exactly what this tutorial describes happening.

### Level 3 — Advanced

```java
public class QuantifyingOsrBenefit {
    public static void main(String[] args) {
        long start = System.nanoTime();
        long total = 0;
        for (long i = 0; i < 3_000_000_000L; i++) {
            total += i % 7;
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms");
    }
}
```

**How to run:** run this twice for comparison — once normally, `java QuantifyingOsrBenefit.java` (JDK 17+, OSR enabled as usual), and once with `java -XX:-UseOnStackReplacement QuantifyingOsrBenefit.java` (explicitly disabling OSR, forcing this loop to run purely interpreted for its entire duration, since it's never called a second time to benefit from ordinary, whole-method JIT compilation).

Expected output shape (dramatically different elapsed times, directly quantifying OSR's real contribution for this specific, long-running single-invocation loop):
```
(normal, OSR enabled):        total=..., elapsed=2650ms
(-XX:-UseOnStackReplacement):  total=..., elapsed=31000ms
```

This adds the production-flavored hard case: explicitly disabling OSR via `-XX:-UseOnStackReplacement` and directly comparing elapsed time against the normal, OSR-enabled run — since this loop lives entirely within a single call to `main` and is never invoked a second time, disabling OSR effectively forces the *entire* 3-billion-iteration loop to run purely interpreted (there's no other opportunity for this specific code to ever get compiled), producing a dramatic, directly measured difference that concretely quantifies just how significant OSR's contribution is for exactly this kind of long-running, single-invocation hot loop.

## 6. Walkthrough

Reasoning through the dramatic difference between the two runs in `QuantifyingOsrBenefit.main`:

1. In the normal run, the JVM's runtime profiling monitors loop back-edges (the point in a loop where execution jumps back to the top for another iteration) as part of its normal hot-code detection — once this count crosses a threshold (independent of, and in addition to, the ordinary method-invocation-count threshold used for whole-method compilation), the JVM recognizes this specific loop as hot, even though the containing method (`main`) itself has only been "invoked" once.
2. The JVM triggers OSR compilation: it compiles the loop's logic (and potentially the surrounding method context) to native code in the background, on a separate compiler thread, while the interpreter continues executing the loop's remaining iterations in the meantime.
3. Once the compiled version is ready, the JVM performs the actual on-stack replacement: it captures the loop's current state (crucially, including the current values of `i` and `total`, the loop's live local variables at that exact point) from the interpreter's stack frame, and transfers execution into the newly-compiled native code, initializing its own equivalent state from those captured values, so the loop continues from exactly where it left off — not restarting from `i = 0`.
4. From that point forward, the (large majority of the) remaining billions of iterations run as compiled native code, dramatically faster per-iteration than interpreted execution — this is why the normal run completes in a small fraction of the time the fully-interpreted run takes.
5. In the second run, `-XX:-UseOnStackReplacement` explicitly disables this entire mechanism — the JVM may still eventually decide the loop or method is "hot" by its invocation-count metrics, but without OSR, there's no way to transfer a currently-*executing*, never-returning loop into compiled code mid-flight; since `main` is never called again, this loop simply never gets the chance to run as compiled code at all, and executes purely interpreted for its full 3 billion iterations, directly explaining the dramatically slower measured time.
6. This comparison makes concrete something otherwise easy to take for granted: OSR isn't a minor implementation detail, but a genuinely load-bearing mechanism for a very common real-world pattern — a program's `main` method containing a substantial, long-running computation directly inline, rather than always being refactored into a separately, repeatedly-called method purely for compilation's sake.

## 7. Gotchas & takeaways

> **Gotcha:** OSR compilation and the ordinary invocation-triggered compilation of the *same* method can, in principle, use somewhat different compiled versions optimized for slightly different circumstances (an OSR-compiled version is specialized for continuing a loop already in progress from a specific point, versus a normally-compiled version optimized for a fresh call from the method's actual entry point) — this is an internal JVM implementation detail, but explains why compilation logs sometimes show what looks like the "same" method being compiled more than once, at the same or different tiers, for what appear to be different reasons.

- On-stack replacement lets the JVM swap a currently-executing, long-running loop from interpreted to compiled execution mid-flight, without needing to wait for the containing method to be called again.
- This matters most for long-running loops that live inside a method called only once (or very rarely) — `main`'s own top-level loops being the single most common practical example — which would otherwise never benefit from JIT compilation at all under the ordinary "compile on next invocation" rule.
- `-XX:+PrintCompilation`'s `%` marker directly identifies OSR compilation events in the JVM's own compilation log, distinguishing them from ordinary, whole-method compilations.
- `-XX:-UseOnStackReplacement` (primarily a diagnostic/benchmarking flag, not a typical production setting) disables this mechanism entirely, letting you directly measure and quantify its real-world contribution for a specific piece of code.
- See [tiered compilation](0920-tiered-compilation.md) for the broader compilation-level framework OSR operates within, and [deoptimization](0924-deoptimization.md) for the reverse process — safely falling back from compiled code to interpretation when a compiled version's assumptions turn out to no longer hold.
