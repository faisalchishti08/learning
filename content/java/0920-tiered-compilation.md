---
card: java
gi: 920
slug: tiered-compilation
title: Tiered compilation
---

## 1. What it is

Tiered compilation is HotSpot's default strategy for combining the [C1 and C2 JIT compilers](0919-jit-compilation-c1-client-c2-server.md) into a single, layered pipeline instead of forcing a choice between them. It defines five execution levels: level 0 is plain interpretation; levels 1–3 are progressively more instrumented C1 compilations (level 1 is C1 with no profiling, used for trivially simple methods; levels 2–3 add increasing amounts of profiling data collection, used to decide whether and how to optimize further); level 4 is full C2 compilation, using the profiling data gathered during the C1 levels to guide aggressive optimizations like [method inlining](0921-method-inlining.md) and [escape analysis](0922-escape-analysis-scalar-replacement.md). A method typically starts at level 0, quickly moves to a C1 level to get a fast performance boost while it's also collecting profiling data, and — only if it stays hot — eventually gets recompiled at level 4 by C2 using that accumulated profile.

## 2. Why & when

Tiered compilation exists to get the best of both compilers automatically, without requiring any code or configuration changes: methods get a fast, low-latency C1 compilation almost immediately if they're called even moderately often (avoiding a long stretch of slow interpreted execution), while genuinely hot methods eventually receive C2's much more aggressive, profile-guided optimizations once there's enough evidence (from the intermediate C1 levels' profiling) that the extra compilation investment will pay off. This is the default, "just works" configuration for essentially all modern production JVMs — you rarely need to think about it directly, but understanding the five-level pipeline explains why a program's throughput typically improves in visible stages rather than a single sharp jump, and why profiling data collected during the C1 stages (branch frequencies, actual types seen at a call site) is exactly what enables C2's most powerful optimizations, which depend on knowing how the code actually behaves at runtime, not just what it looks like statically.

## 3. Core concept

```
Level 0: Interpreter                          (no compilation, baseline)
Level 1: C1, no profiling                      (trivial methods -- nothing worth profiling)
Level 2: C1, limited profiling                  (invocation/loop-back-edge counts only)
Level 3: C1, full profiling                      (branch frequencies, type profiles at call sites)
Level 4: C2, fully optimized                     (uses accumulated profile data from levels 2/3)
```

A method's actual path through these levels depends on how it behaves — a method called only a handful of times might stop at level 1 or 3 and never reach level 4 at all, while a genuinely hot method progresses all the way to level 4, informed by the rich profiling data gathered along the way.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five tiered compilation levels: interpreter, three C1 sublevels with increasing profiling, and full C2 compilation at the top, with a method's progression depending on how hot it actually turns out to be">
  <rect x="20" y="140" width="110" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="75" y="160" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">L0: Interpreter</text>

  <rect x="150" y="110" width="110" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="205" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">L1: C1, no profile</text>

  <rect x="280" y="80" width="110" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">L2: C1, limited</text>

  <rect x="410" y="50" width="110" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">L3: C1, full profile</text>

  <rect x="540" y="20" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="585" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">L4: C2</text>

  <line x1="130" y1="150" x2="146" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="260" y1="120" x2="276" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="390" y1="90" x2="406" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="520" y1="60" x2="536" y2="40" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Not every method reaches L4 -- only genuinely hot ones justify the trip.</text>
  <defs><marker id="a48" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Progression through the five levels depends on actual observed call frequency — most methods stop early; only the hottest reach full C2 optimization.*

## 5. Runnable example

Scenario: observing tiered compilation's effect via the JVM's own compilation logging, growing from a basic demonstration with `-XX:+PrintCompilation` showing level transitions, to comparing a rarely-called method against a genuinely hot one, to disabling tiered compilation to see the contrast directly.

### Level 1 — Basic

```java
public class ObservingCompilationLevels {
    static int add(int a, int b) { return a + b; }

    public static void main(String[] args) {
        int sum = 0;
        for (int i = 0; i < 100_000; i++) {
            sum += add(i, 1); // called VERY frequently -- a strong candidate for tiered promotion
        }
        System.out.println("sum = " + sum);
    }
}
```

**How to run:** `java -XX:+PrintCompilation ObservingCompilationLevels.java 2>&1 | grep "::add"` (JDK 17+; `-XX:+PrintCompilation` logs every compilation event, including which level each one used — filtering to just `add`'s log lines makes its specific progression visible).

Expected output shape (the numbers in brackets like `3` or `4` indicate the tier; exact timing/counts vary by run):
```
     87   45       3       ObservingCompilationLevels::add (5 bytes)
    102   62       4       ObservingCompilationLevels::add (5 bytes)
sum = 704995000
```

The compilation log directly shows `add` being compiled first at tier 3 (C1 with full profiling) and then, shortly after, recompiled at tier 4 (C2, fully optimized) — a live, observable record of tiered compilation's progression for this specific, genuinely hot method.

### Level 2 — Intermediate

```java
public class RarelyCalledVsHot {
    static int rarelyCalled(int a, int b) { return a * b; } // called only a few times
    static int hotMethod(int a, int b) { return a + b; }     // called extremely often

    public static void main(String[] args) {
        int r = rarelyCalled(3, 4) + rarelyCalled(5, 6); // just 2 calls total

        int sum = 0;
        for (int i = 0; i < 500_000; i++) {
            sum += hotMethod(i, 1); // 500,000 calls -- a much stronger candidate for full C2 promotion
        }

        System.out.println("r = " + r + ", sum = " + sum);
    }
}
```

**How to run:** `java -XX:+PrintCompilation RarelyCalledVsHot.java 2>&1 | grep -E "::rarelyCalled|::hotMethod"` (JDK 17+).

Expected output shape (`rarelyCalled` may never appear in the log at all, or only reach a low tier; `hotMethod` progresses further):
```
    95   50       3       RarelyCalledVsHot::hotMethod (4 bytes)
   110   68       4       RarelyCalledVsHot::hotMethod (4 bytes)
r = 42, sum = 124999750000
```

The real-world concern added: `rarelyCalled`, called only twice, never accumulates enough invocations to justify any meaningful compilation investment (it may run purely interpreted, or receive at most a cheap, quick compilation, but never reaches C2) — while `hotMethod`, called 500,000 times, clearly progresses through the tiers all the way to level 4, directly demonstrating that tiered compilation's promotion decisions are driven by actual, observed call frequency, not by anything about the methods' source code alone.

### Level 3 — Advanced

```java
public class TieredVsNonTieredComparison {
    static long fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public static void main(String[] args) {
        long start = System.nanoTime();
        long result = 0;
        for (int i = 0; i < 500; i++) result = fib(32);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("fib(32) x500: " + elapsedMs + "ms, result=" + result);
    }
}
```

**How to run:** run this three ways and compare: `java TieredVsNonTieredComparison.java` (default, full tiered), `java -XX:-TieredCompilation TieredVsNonTieredComparison.java` (disables tiered compilation entirely, going straight to C2 for anything deemed worth compiling, skipping the intermediate C1 profiling stages), and `java -XX:TieredStopAtLevel=1 TieredVsNonTieredComparison.java` (JDK 17+, caps at C1 level 1, no profiling, no C2 at all).

Expected output shape (illustrative; exact numbers vary significantly by machine, but the relative ordering — full tiered typically fastest overall for this genuinely hot workload, non-tiered close behind after a possibly slower start, C1-only slowest of the compiled options):
```
default (tiered):        fib(32) x500: 780ms
-XX:-TieredCompilation:   fib(32) x500: 920ms
-XX:TieredStopAtLevel=1:  fib(32) x500: 1400ms
```

This adds the production-flavored hard case: directly comparing three real compilation configurations for the same genuinely hot, long-running workload — full tiered compilation (the default, getting quick C1 gains early and eventual C2 optimization later), non-tiered compilation (`-XX:-TieredCompilation`, which goes straight to C2 without the intermediate profiling stages, potentially compiling less accurately without the benefit of gathered profile data, and with a longer initial delay before any compiled code is available at all), and C1-only (missing C2's deeper optimizations entirely) — demonstrating that the *combination* tiered compilation provides is generally the best default for genuinely hot, sustained workloads, which is exactly why it's HotSpot's default strategy.

## 6. Walkthrough

Reasoning through why the default (tiered) configuration tends to perform best for `fib(32)` called 500 times:

1. Under default tiered compilation, `fib` starts interpreted (level 0), but because it's called an enormous number of times almost immediately (naive recursive `fib(32)` makes millions of recursive calls even for a single top-level invocation), it very quickly accumulates enough invocations to be compiled at a C1 level — getting some compiled-code speedup within the very first few calls, without waiting for a slower C2 compilation to become available first.
2. While running at a C1 profiling level (level 2 or 3), the JVM collects real profiling data about `fib`'s actual behavior — branch outcomes, whatever type information is relevant — which feeds directly into how effectively C2 can later optimize it.
3. Because `fib(32)` continues to be extremely hot throughout the remaining 499 outer-loop iterations, it gets promoted to level 4 (full C2 compilation) using that accumulated profile, receiving C2's most aggressive optimizations — informed by real runtime behavior, not just static analysis of the bytecode alone.
4. Under `-XX:-TieredCompilation`, the JVM skips the intermediate C1 profiling stages and compiles directly with C2 once a method is deemed hot enough — this means the first compiled version of `fib` takes longer to become available (C2 compilation itself is slower than C1's), and it's compiled without the benefit of the detailed runtime profile that the C1 stages would otherwise have gathered, potentially leaving some optimization opportunities on the table or requiring more speculative assumptions that could later need correction via [deoptimization](0924-deoptimization.md).
5. Under `-XX:TieredStopAtLevel=1`, `fib` never receives C2's deeper optimizations (method inlining, escape analysis, and more) at all — it settles for C1's comparatively modest optimization level, resulting in the slowest of the three compiled-code configurations for this sustained, genuinely hot workload.
6. Because the workload here is substantial enough (500 outer calls to an exponential recursive function) to fully amortize even C2's higher compilation cost many times over, the full tiered configuration — getting an early boost from C1 and later reaching C2's peak optimization — ends up performing best overall, exactly reflecting tiered compilation's design intent.

## 7. Gotchas & takeaways

> **Gotcha:** the specific compilation thresholds, level numbering, and exact promotion logic described here are HotSpot implementation details that can and do change across JDK versions — treat the five-level model as a helpful conceptual framework for understanding *why* Java's warm-up behavior looks the way it does, not as a fixed, permanently-guaranteed specification to hard-code assumptions against.

- Tiered compilation combines C1 and C2 into a five-level pipeline (interpreter, three progressively-profiled C1 levels, and full C2), letting methods get fast initial compilation gains from C1 while genuinely hot methods eventually receive C2's deeper, profile-guided optimizations.
- This is HotSpot's default strategy for essentially all modern production JVMs — it requires no explicit configuration to benefit from, unlike forcing a single compiler tier via flags like `-XX:TieredStopAtLevel` or `-XX:-TieredCompilation`.
- Profiling data gathered during the intermediate C1 levels (branch frequencies, type information at call sites) is what enables C2's most powerful optimizations — this is exactly why skipping straight to C2 (non-tiered mode) can sometimes underperform the full tiered pipeline for sustained workloads.
- `-XX:+PrintCompilation` is a direct, observable window into which methods get compiled, at which tier, and when — genuinely useful for understanding a specific program's actual compilation behavior rather than reasoning about it purely in the abstract.
- See [method inlining](0921-method-inlining.md), [escape analysis & scalar replacement](0922-escape-analysis-scalar-replacement.md), and [deoptimization](0924-deoptimization.md) for the specific optimizations and safety mechanisms that C2's level-4 compilation, informed by the profiling data described here, actually applies.
