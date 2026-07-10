---
card: java
gi: 919
slug: jit-compilation-c1-client-c2-server
title: JIT compilation (C1 client, C2 server)
---

## 1. What it is

Just-In-Time (JIT) compilation is the process of translating a "hot" (frequently executed) method's bytecode into native machine code *while the program is running*, so future calls to that method run as directly-executed machine instructions instead of being stepped through by the [bytecode interpreter](0918-bytecode-interpretation.md). HotSpot (the reference JVM) historically ships two distinct JIT compilers with different tradeoffs: **C1** (the "client" compiler) compiles quickly but produces less aggressively optimized code, favoring fast startup; **C2** (the "server" compiler) takes longer to compile but applies much more sophisticated optimizations, favoring peak long-running throughput. Modern HotSpot JVMs use both together via [tiered compilation](0920-tiered-compilation.md): C1 compiles a method quickly first, and C2 later recompiles it more aggressively if it stays hot, getting the benefit of both compilers' strengths at different points in a method's lifetime.

## 2. Why & when

Understanding the C1/C2 distinction (and their combination via tiered compilation) explains a genuine, practical tradeoff: a program that runs briefly (a short-lived CLI tool, a quick script-like task) benefits more from fast, low-overhead C1 compilation, since it may never run long enough to amortize C2's higher compilation cost; a program that runs for a long time serving sustained load (a web server, a long-running batch job) benefits from eventually reaching C2-compiled code for its hot paths, since the extra compilation time pays for itself many times over across the method's remaining, much longer lifetime. This matters when choosing JVM flags for a specific deployment (`-client` versus `-server`, `-XX:TieredStopAtLevel` to cap which compiler tier is used, `-Xbatch` to make compilation synchronous for benchmarking clarity) and when interpreting performance measurements — a program measured only briefly may never reach C2-compiled steady-state performance at all.

## 3. Core concept

```
Interpreted execution (slowest, zero compile delay)
        |
        v  (method called enough times -- crosses C1 threshold)
C1-compiled ("client") -- fast compile, simpler optimizations, quick to produce
        |
        v  (still hot -- crosses C2 threshold, background recompilation)
C2-compiled ("server") -- slower compile, aggressive optimizations, best steady-state speed
```

A single method can genuinely pass through all three stages during one program's run — interpreted at first, C1-compiled once it's called somewhat often, and C2-compiled if it stays hot enough for long enough to justify the deeper optimization effort.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method progressing from interpreted execution, to fast C1 client compilation, to aggressively optimized C2 server compilation, as its invocation count grows over the program's lifetime">
  <rect x="10" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Interpreted</text>

  <rect x="230" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">C1 (client)</text>
  <text x="320" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fast compile, simpler</text>

  <rect x="450" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">C2 (server)</text>
  <text x="540" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">slower compile, best peak speed</text>

  <line x1="190" y1="85" x2="226" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a47)"/>
  <line x1="410" y1="85" x2="446" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a47)"/>
  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Tiered compilation runs BOTH stages of promotion automatically, by default.</text>
  <defs><marker id="a47" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A hot method progresses through increasingly optimized execution modes over the course of a program's run, without any code changes required.*

## 5. Runnable example

Scenario: observing the effect of capping the JIT compiler tier a program is allowed to use, growing from an uncapped baseline, to capping at C1-only, to comparing all three configurations directly for the same workload.

### Level 1 — Basic

```java
public class UncappedBaseline {
    static long fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public static void main(String[] args) {
        long start = System.nanoTime();
        long result = 0;
        for (int i = 0; i < 1000; i++) result = fib(30);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("fib(30) x1000, default (uncapped) compilation: " + elapsedMs + "ms, result=" + result);
    }
}
```

**How to run:** `java UncappedBaseline.java` (JDK 17+; default JVM behavior lets the compiler use whichever tiers it decides are appropriate).

Expected output shape (machine-dependent baseline):
```
fib(30) x1000, default (uncapped) compilation: 850ms, result=832040
```

This establishes a baseline using the JVM's normal, full tiered-compilation behavior — a comparison point for the next two levels.

### Level 2 — Intermediate

```java
public class CappedAtC1Only {
    static long fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public static void main(String[] args) {
        long start = System.nanoTime();
        long result = 0;
        for (int i = 0; i < 1000; i++) result = fib(30);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("fib(30) x1000, capped at C1 only: " + elapsedMs + "ms, result=" + result);
    }
}
```

**How to run:** `java -XX:TieredStopAtLevel=1 CappedAtC1Only.java` (JDK 17+; this flag prevents any method from ever being promoted beyond the fastest-compiling, least-optimizing C1 tier).

Expected output shape (typically somewhat slower than the uncapped baseline, since C2's deeper optimizations never get applied):
```
fib(30) x1000, capped at C1 only: 1120ms, result=832040
```

The real-world concern added: `-XX:TieredStopAtLevel=1` explicitly caps compilation at C1's level, preventing the JVM from ever escalating `fib` to C2's more aggressive optimizations, even though the method is clearly hot (called recursively, millions of times, across the 1000 outer iterations) — the resulting elapsed time is typically worse than the uncapped baseline, directly demonstrating C2's real value for genuinely hot, long-running code.

### Level 3 — Advanced

```java
public class InterpreterOnlyComparison {
    static long fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public static void main(String[] args) {
        long start = System.nanoTime();
        long result = 0;
        for (int i = 0; i < 1000; i++) result = fib(30);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("fib(30) x1000, pure interpreter (-Xint): " + elapsedMs + "ms, result=" + result);
        System.out.println("compare all three runs: -Xint (this), -XX:TieredStopAtLevel=1, and default --");
        System.out.println("this demonstrates the FULL spectrum: interpreted < C1-only < full tiered (C1+C2)");
    }
}
```

**How to run:** `java -Xint InterpreterOnlyComparison.java` (JDK 17+; forces pure interpreter mode, no JIT compilation of any kind).

Expected output shape (dramatically slower than both compiled variants, since every single recursive call is interpreted):
```
fib(30) x1000, pure interpreter (-Xint): 9800ms, result=832040
compare all three runs: -Xint (this), -XX:TieredStopAtLevel=1, and default --
this demonstrates the FULL spectrum: interpreted < C1-only < full tiered (C1+C2)
```

This adds the production-flavored hard case: running the identical, genuinely hot recursive workload under three configurations that span the entire compilation spectrum — pure interpretation (slowest, since every one of `fib`'s millions of recursive calls executes bytecode instruction by instruction), C1-only compilation (much faster than pure interpretation, but missing C2's deeper optimizations), and full, uncapped tiered compilation (fastest overall, since `fib` genuinely gets promoted all the way to C2's most aggressive optimization level given how hot it is) — making the practical, measured impact of each compilation tier concrete rather than theoretical.

## 6. Walkthrough

Comparing the three runs' relative performance:

1. Under `-Xint`, every single call to `fib` — and `fib` is called an enormous number of times, since it's naive, exponential recursion computing `fib(30)` a thousand times over — is executed by the bytecode interpreter, reading and carrying out each bytecode instruction one at a time, with absolutely no compilation ever happening. This is by far the slowest configuration, since the interpreter's per-instruction overhead is paid on every single one of millions of recursive calls.
2. Under `-XX:TieredStopAtLevel=1`, the JVM still notices `fib` is hot (called extremely frequently) and compiles it — but only ever using C1, the faster-to-compile, less-aggressively-optimizing compiler. This produces genuine native machine code, eliminating the interpreter's per-instruction overhead, so it's substantially faster than `-Xint` — but C1's optimizations (less thorough inlining, simpler register allocation, fewer speculative optimizations) leave real performance on the table compared to what C2 could achieve for a method this hot.
3. Under default (uncapped) settings, the JVM's tiered compilation system initially compiles `fib` with C1 (getting a quick performance boost early), but because `fib` continues to be called extremely frequently across all 1000 outer iterations, it eventually gets promoted further and recompiled by C2 in the background — C2 can apply much more aggressive optimizations (including things like deeper method inlining and more sophisticated register allocation) precisely because it has more time to analyze the method and more confidence (from having observed many actual invocations) about which optimizations are safe and beneficial to apply.
4. Because the workload here (`fib(30)` called 1000 times) is substantial and sustained enough to fully amortize C2's higher compilation cost many times over across its remaining execution, the default (full tiered, eventually reaching C2) configuration ends up fastest overall — directly validating the theoretical tradeoff: C1 for fast, low-latency compilation of moderately-hot code; C2 for maximum throughput on code that's hot enough, for long enough, to make its higher compilation cost worthwhile.

## 7. Gotchas & takeaways

> **Gotcha:** forcing `-XX:TieredStopAtLevel=1` or similar flags is occasionally useful for reducing JVM startup/warm-up time in specific, latency-sensitive scenarios (like short-lived serverless function invocations), but doing so trades away C2's peak throughput — this is a genuine tradeoff to make deliberately, based on your actual workload's runtime profile, not a "safe default" tweak to apply blindly.

- C1 ("client") compiles quickly with simpler optimizations, favoring fast startup; C2 ("server") compiles more slowly but applies much more aggressive optimizations, favoring peak long-running throughput.
- Modern HotSpot JVMs combine both automatically via [tiered compilation](0920-tiered-compilation.md) by default — most applications never need to choose one exclusively, benefiting from C1's fast initial compilation and C2's eventual, deeper optimization of genuinely hot code.
- `-Xint` disables JIT compilation entirely (pure interpretation); `-XX:TieredStopAtLevel=1` caps compilation at C1 only — both are primarily diagnostic/benchmarking tools rather than typical production configurations.
- A program's actual runtime profile (short-lived versus long-running and sustained) determines whether C1's fast compilation or C2's deeper optimization matters more — there's no universally "correct" choice independent of the workload.
- See [bytecode interpretation](0918-bytecode-interpretation.md) for the execution mode every method starts in before any compilation happens, and [tiered compilation](0920-tiered-compilation.md) for the precise mechanism that decides when and how a method progresses between these tiers.
