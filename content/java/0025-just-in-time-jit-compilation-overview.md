---
card: java
gi: 25
slug: just-in-time-jit-compilation-overview
title: Just-In-Time (JIT) compilation overview
---

## 1. What it is

**Just-In-Time (JIT) compilation** is the process by which the JVM converts frequently-executed bytecode into native machine code at runtime — while the program is running. Unlike ahead-of-time compilation (where the compiler runs before execution), JIT compiles *during* execution, guided by profiling data collected as the program runs.

HotSpot JVM (the reference JVM) uses a **two-tier JIT**: C1 (client compiler) for fast, lightly-optimised compilation and C2 (server compiler) for heavily-optimised but slower compilation of "hot" methods.

## 2. Why & when

JIT is why Java can match or exceed C++ performance on long-running workloads:

- **Startup**: bytecode is *interpreted* — no compilation latency, process starts fast.
- **Warm-up (C1)**: methods called ~1,000 times are compiled by C1 with basic optimisations (inlining, dead-code elimination). Code now runs ~10–100× faster than interpreted.
- **Steady-state (C2)**: methods called ~10,000 times are re-compiled by C2 with aggressive loop unrolling, escape analysis, auto-vectorisation (SIMD), and speculative deoptimisation. Peak performance.

You care about JIT when:
- Profiling shows JVM startup time dominates (consider GraalVM Native Image or CDS instead).
- A method is unexpectedly slow because it was never hot enough to be JIT-compiled.
- `-XX:+PrintCompilation` output shows excessive deoptimisations.

## 3. Core concept

```
Bytecode                 JVM Execution Model
─────────                ────────────────────
.class file → [Interpreter] → runs bytecode line-by-line (slow)
                    ↓ invocation counter hits threshold (~1 000)
              [C1 Compiler] → native code with profiling instrumentation
                    ↓ invocation counter hits threshold (~10 000)
              [C2 Compiler] → optimised native code (SIMD, inline, escape analysis)
                    ↓ profile assumption violated (e.g. new subclass loaded)
              [Deoptimisation] → falls back to interpreter, re-profiles
```

Key C2 optimisations:
- **Method inlining** — replaces `obj.method()` call with the method body (eliminates call overhead, enables further optimisations)
- **Escape analysis** — detects objects that don't escape the method and allocates them on the stack (not heap), eliminating GC pressure
- **Loop unrolling** — replicates loop body N times to reduce branch overhead
- **Speculative deoptimisation** — assumes a virtual call always goes to one class; generates fast non-virtual code; backs out if assumption is violated

JIT compilation runs on **background compiler threads** (`-XX:CICompilerCount=N`). The application thread continues running interpreted or C1 code while C2 works.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JIT compilation tiers: interpret → C1 → C2 with profiling counters">
  <!-- Background -->
  <rect x="10" y="10" width="660" height="210" rx="8" fill="#0d1117"/>

  <!-- Stages -->
  <!-- Interpret -->
  <rect x="30" y="40" width="130" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Interpreter</text>
  <text x="95" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bytecode → slow ops</text>
  <text x="95" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">counter &gt; 1 000</text>

  <!-- C1 -->
  <rect x="270" y="40" width="130" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="335" y="65" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">C1 Compiler</text>
  <text x="335" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fast native + profile</text>
  <text x="335" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">counter &gt; 10 000</text>

  <!-- C2 -->
  <rect x="510" y="40" width="130" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="575" y="65" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">C2 Compiler</text>
  <text x="575" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">peak native</text>

  <!-- Arrows -->
  <line x1="160" y1="70" x2="265" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="400" y1="70" x2="505" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>

  <!-- Deopt arrow -->
  <path d="M 575 100 Q 575 160 335 175 Q 165 175 95 135" fill="none" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arr3)"/>
  <text x="340" y="192" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">deoptimise (assumption violated)</text>

  <!-- optimisations labels -->
  <text x="510" y="125" fill="#6db33f" font-size="8" font-family="sans-serif">inline · escape · SIMD</text>
  <text x="510" y="138" fill="#6db33f" font-size="8" font-family="sans-serif">loop-unroll · spec. deopt</text>

  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8" fill="none" stroke="#8b949e" stroke-width="1.5"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8" fill="none" stroke="#79c0ff" stroke-width="1.5"/>
    </marker>
    <marker id="arr3" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8" fill="none" stroke="#f0883e" stroke-width="1.5"/>
    </marker>
  </defs>
</svg>

Three-tier JIT: interpret → C1 (fast compile with profiling) → C2 (peak optimised native). Deoptimisation falls back when speculative assumptions are violated.

## 5. Runnable example

Scenario: measure how JIT warm-up affects throughput — same loop runs progressively faster as C1 then C2 kick in.

### Level 1 — Basic

```java
// JitWarmup.java
public class JitWarmup {
    static long sumTo(int n) {
        long sum = 0;
        for (int i = 1; i <= n; i++) sum += i;
        return sum;
    }

    public static void main(String[] args) {
        // Run 5 rounds; each round calls sumTo 1 000 times
        // C1 typically kicks in around round 1-2, C2 around round 3-4
        for (int round = 0; round < 5; round++) {
            long start = System.nanoTime();
            long result = 0;
            for (int i = 0; i < 1_000; i++) {
                result = sumTo(10_000);
            }
            long micros = (System.nanoTime() - start) / 1_000;
            System.out.printf("Round %d: %5d µs  (result=%d)%n", round + 1, micros, result);
        }
    }
}
```

**How to run:** `java JitWarmup.java`

Each successive round should be faster (interpreter → C1 → C2). The exact thresholds depend on `-server`/`-client` mode and the JVM flags; the trend is the point.

### Level 2 — Intermediate

Same benchmark extended with `-XX:+PrintCompilation` flag detection and multiple method sizes to show that JIT inlines small methods aggressively.

```java
// JitInlineDemo.java
public class JitInlineDemo {

    // Tiny method — C2 will inline this into callers
    static int square(int x) { return x * x; }

    // Larger method — less likely to be fully inlined
    static long heavyLoop(int n) {
        long sum = 0;
        for (int i = 0; i < n; i++) {
            sum += square(i);  // after inlining: sum += i*i;
        }
        return sum;
    }

    public static void main(String[] args) {
        System.out.println("Run with: java -XX:+PrintCompilation JitInlineDemo.java");
        System.out.println("(PrintCompilation shows method compilation events)");
        System.out.println();

        // Warm-up phase
        long dummy = 0;
        for (int round = 0; round < 20; round++) {
            long start = System.nanoTime();
            for (int i = 0; i < 500; i++) dummy += heavyLoop(1_000);
            long us = (System.nanoTime() - start) / 1_000;

            String tier = round < 3 ? "interpret" : round < 8 ? "C1" : "C2";
            System.out.printf("Round %2d [%-9s]: %6d µs%n", round + 1, tier, us);
        }
        System.out.println("(dummy=" + dummy + " to prevent dead-code elimination)");

        System.out.println("\nInline benefit: after C2 inlines square() into heavyLoop(),");
        System.out.println("  sum += square(i)  becomes  sum += i*i  — no call overhead.");
    }
}
```

**How to run:** `java JitInlineDemo.java` or `java -XX:+PrintCompilation JitInlineDemo.java`

`PrintCompilation` output lines like `1 3 java.lang.String::hashCode (55 bytes)` show: `[id] [tier] [class:method] ([size] bytes)`. Tier 3 = C1, tier 4 = C2.

### Level 3 — Advanced

Same warm-up measurement grown to detect JIT tiers programmatically using `java.lang.management.CompilationMXBean` and show how escape analysis affects allocation rate.

```java
// JitProfiler.java
import java.lang.management.*;
import java.util.ArrayList;

public class JitProfiler {

    // Object that may escape (allocated on heap)
    record Point(int x, int y) {
        int distSq() { return x * x + y * y; }
    }

    static long sumDistSq(int n) {
        long sum = 0;
        for (int i = 0; i < n; i++) {
            Point p = new Point(i, i + 1);  // escape analysis: does p escape?
            sum += p.distSq();               // if not → stack alloc (no GC)
        }
        return sum;
    }

    static long sumDirectly(int n) {
        long sum = 0;
        for (int i = 0; i < n; i++) {
            sum += i * i + (i + 1) * (i + 1);  // no object allocation
        }
        return sum;
    }

    public static void main(String[] args) throws Exception {
        CompilationMXBean comp = ManagementFactory.getCompilationMXBean();
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();

        System.out.println("JIT compiler: " + comp.getName());
        System.out.println("Compilation time tracking: " + comp.isCompilationTimeMonitoringSupported());

        // Warm up then measure
        int ROUNDS = 15;
        int OPS_PER_ROUND = 2_000;

        System.out.println("\n[ sumDistSq — Point records (escape analysis test) ]");
        measureRounds("Point alloc", () -> sumDistSq(OPS_PER_ROUND), ROUNDS, comp, mem);

        System.out.println("\n[ sumDirectly — no object allocation ]");
        measureRounds("No alloc   ", () -> sumDirectly(OPS_PER_ROUND), ROUNDS, comp, mem);
    }

    static void measureRounds(String label, Runnable work, int rounds,
                               CompilationMXBean comp, MemoryMXBean mem) {
        long prevCompMs = comp.isCompilationTimeMonitoringSupported()
            ? comp.getTotalCompilationTime() : -1;

        for (int r = 0; r < rounds; r++) {
            long gcBefore = mem.getHeapMemoryUsage().getUsed();
            long t0 = System.nanoTime();
            for (int i = 0; i < 100; i++) work.run();
            long us = (System.nanoTime() - t0) / 1_000;

            long compMs = comp.isCompilationTimeMonitoringSupported()
                ? comp.getTotalCompilationTime() : -1;
            long dComp = compMs - prevCompMs;
            prevCompMs = compMs;

            System.out.printf("  [%s] round %2d: %5d µs %s%n",
                label, r + 1, us,
                dComp > 0 ? " +JIT " + dComp + "ms" : "");
        }
    }
}
```

**How to run:** `java JitProfiler.java`

`CompilationMXBean.getTotalCompilationTime()` increases while JIT is active — rounds where it increases are warm-up rounds. Once it stabilises, the code has reached peak compiled state.

## 6. Walkthrough

Execution in `JitProfiler.main`:

1. **`CompilationMXBean`** — obtained via `ManagementFactory.getCompilationMXBean()`. Reports the JIT compiler name (e.g., `"HotSpot 64-Bit Tiered Compilers"`) and total wall-clock time spent compiling. This time only advances when the background C1/C2 compiler threads are active.

2. **`sumDistSq` vs `sumDirectly`** — both compute the same sum. `sumDistSq` allocates a `Point` record per iteration. After C2's escape analysis determines `p` never leaves the loop body, it eliminates the heap allocation entirely — making it as fast as `sumDirectly`. This is why `@JvmStatic` helper records in Kotlin/Java can be "zero allocation" at runtime.

3. **`measureRounds`** — each round calls the work 100× and measures total time. Watch for the pattern:
   - Rounds 1–3: high latency, `+JIT Nms` visible in output (compiler threads busy)
   - Rounds 4–8: latency drops as C1 code runs
   - Rounds 9+: latency stabilises at peak (C2 compiled, no more JIT activity)

4. **`dComp > 0`** — delta compilation time. Non-zero means JIT compiler threads were active during this round, meaning the code was not yet at peak optimisation.

5. **Deoptimisation not shown here**, but triggered when: a virtual method's inline assumption is broken (a new subclass is loaded), a class is initialised that changes a `final static` assumption, or an uncommon exception is thrown in a path JIT assumed was cold.

## 7. Gotchas & takeaways

> **JIT warm-up is the main reason Java benchmarks must use JMH (Java Microbenchmark Harness).** A naive loop that measures the first N iterations includes interpreter and C1 overhead. JMH runs thousands of warm-up iterations before measuring, ensuring C2-compiled code is being timed.

> **`-XX:+PrintCompilation` is a diagnostic flag.** In production, use JFR (`jcmd <pid> JFR.start`) — `PrintCompilation` adds overhead and floods logs.

- JVM uses a two-tier JIT: C1 (fast, lighter) → C2 (slow, peak).
- Thresholds: ~1 000 invocations → C1; ~10 000 → C2 (configurable with `-XX:CompileThreshold`).
- Method inlining is C2's most impactful optimisation — it enables all subsequent optimisations.
- Escape analysis eliminates heap allocations for objects that don't escape their scope.
- Deoptimisation is not a crash — the JVM gracefully falls back to the interpreter and re-profiles.
- `java -XX:+PrintCompilation` shows live JIT activity; JFR is the production alternative.
