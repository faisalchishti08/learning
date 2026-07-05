---
card: java
gi: 20
slug: jvm-java-virtual-machine-what-it-is
title: JVM (Java Virtual Machine) — what it is
---

## 1. What it is

The **Java Virtual Machine (JVM)** is an abstract computing machine — a specification for a computer that doesn't physically exist but is emulated in software. The JVM reads `.class` files (containing bytecode), verifies them, and executes them by translating bytecode to native machine code for the actual CPU. Every Java program runs inside a JVM instance.

The JVM has five key responsibilities:
1. **Class loading** — find, load, link, and initialise `.class` files.
2. **Bytecode verification** — reject malformed or potentially malicious class files before executing them.
3. **Execution** — interpret bytecode or compile it to native code via JIT (Just-In-Time compilation).
4. **Memory management** — allocate heap and stack memory, run garbage collection.
5. **Runtime services** — threading, exception handling, I/O coordination, security.

## 2. Why & when

Without the JVM, compiled Java bytecode is useless — there is no real CPU that can execute JVM bytecode natively. The JVM is the engine that makes "write once, run anywhere" work: the same `.class` file runs on any machine that has a JVM.

The JVM matters beyond Java itself: Kotlin, Scala, Clojure, Groovy, and JRuby all compile to JVM bytecode and run on the JVM. The JVM is a general-purpose execution platform, not a Java-specific one.

Understanding the JVM matters when:
- Diagnosing OutOfMemoryError, StackOverflowError, or GC pauses.
- Tuning `-Xmx`, `-Xms`, GC algorithm flags.
- Understanding why code runs faster after warm-up (JIT compilation).
- Writing memory-efficient code (understanding heap vs stack allocation).
- Debugging class-loading issues (`ClassNotFoundException`, version mismatches).

## 3. Core concept

The JVM is specified by the **JVMS (JVM Specification)** — a document defining every aspect of its behaviour. Implementations (HotSpot, OpenJ9, GraalVM) must behave identically from a user's perspective but can use different internal strategies.

**JVM memory areas** (the JVMS defines these):
```
┌──────────────────────────────────────────────┐
│  JVM Process                                 │
│                                              │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Per-thread  │  │ Shared (all threads) │  │
│  │             │  │                      │  │
│  │  PC Register│  │  Heap                │  │
│  │  JVM Stack  │  │  (objects, GC'd)     │  │
│  │  Native     │  │                      │  │
│  │  Method     │  │  Method Area         │  │
│  │  Stack      │  │  (class data, JIT)   │  │
│  └─────────────┘  │                      │  │
│                   │  Run-Time Constant   │  │
│                   │  Pool                │  │
│                   └──────────────────────┘  │
└──────────────────────────────────────────────┘
```

**Execution lifecycle:**
1. **Class loading** — `ClassLoader` finds the `.class` file (from JAR, filesystem, or network), reads the bytes, and creates a `Class` object.
2. **Verification** — the bytecode verifier checks structural correctness: valid opcodes, type-safe stack operations, no out-of-bounds accesses. This happens before any bytecode executes.
3. **Preparation** — static fields are allocated and zero-initialised.
4. **Resolution** — symbolic references (`ClassName.methodName`) are resolved to actual memory addresses.
5. **Initialisation** — `<clinit>` (static initialisers) are executed.
6. **Execution** — bytecode runs (interpreted or JIT-compiled).

## 4. Diagram

<svg viewBox="0 0 680 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JVM internals: class loader, bytecode verifier, JIT, GC, heap and stack">
  <defs>
    <marker id="ajvm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Bytecode input -->
  <rect x="20" y="110" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.class</text>
  <text x="65" y="141" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">bytecode</text>
  <line x1="110" y1="130" x2="128" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajvm)"/>

  <!-- Class loader -->
  <rect x="130" y="100" width="100" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ClassLoader</text>
  <text x="180" y="137" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">load · link</text>
  <text x="180" y="149" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">verify · init</text>
  <line x1="230" y1="130" x2="248" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajvm)"/>

  <!-- Execution engine -->
  <rect x="250" y="80" width="170" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="335" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Execution Engine</text>
  <rect x="260" y="110" width="70" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="123" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Interpreter</text>
  <text x="295" y="135" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">(cold code)</text>
  <rect x="340" y="110" width="70" height="30" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="375" y="123" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">JIT (C1/C2)</text>
  <text x="375" y="135" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">(hot code)</text>
  <line x1="420" y1="130" x2="438" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajvm)"/>

  <!-- Native output -->
  <rect x="440" y="110" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Native code</text>
  <text x="490" y="141" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">x64/ARM/etc.</text>

  <!-- Memory areas -->
  <rect x="20"  y="190" width="130" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="208" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="sans-serif">Heap (GC)</text>
  <text x="85" y="222" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">objects · arrays</text>

  <rect x="160" y="190" width="120" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="220" y="208" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="sans-serif">Stack (per thread)</text>
  <text x="220" y="222" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">frames · locals</text>

  <rect x="290" y="190" width="120" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="208" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="sans-serif">Method Area</text>
  <text x="350" y="222" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">class data · JIT cache</text>

  <rect x="420" y="190" width="110" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="475" y="208" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="sans-serif">PC Register</text>
  <text x="475" y="222" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">current bytecode ptr</text>
</svg>

Bytecode → ClassLoader (load + verify) → Execution Engine (interpret + JIT) → native code. Memory split: heap (GC), stacks, method area.

## 5. Runnable example

Scenario: observe the JVM's memory areas, class-loading behaviour, and JIT warm-up from inside a running program.

### Level 1 — Basic

```java
// JvmInternals.java
import java.lang.management.*;

public class JvmInternals {
    public static void main(String[] args) {
        // Heap
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        System.out.printf("Heap used/max: %d MB / %d MB%n",
            mem.getHeapMemoryUsage().getUsed() / (1024*1024),
            mem.getHeapMemoryUsage().getMax()  / (1024*1024));

        // Stack (per-thread, not directly inspectable, but the count shows threads)
        System.out.println("Live threads: " + ManagementFactory.getThreadMXBean().getThreadCount());

        // Loaded class count (method area)
        System.out.println("Classes loaded: " + ManagementFactory.getClassLoadingMXBean().getLoadedClassCount());

        // JVM name/version
        System.out.println("JVM: " + System.getProperty("java.vm.name"));
        System.out.println("JIT: " + System.getProperty("java.compiler", "<JIT info not exposed>"));
    }
}
```

**How to run:** `java JvmInternals.java`

`getLoadedClassCount()` shows how many classes the bootstrap + application class loaders have loaded so far. Even for this tiny program it's typically 400–800 classes (from `java.base` module alone).

### Level 2 — Intermediate

Same JVM internals probe extended to demonstrate the class-loader hierarchy (bootstrap → platform → application) and show which class loader loaded a specific class.

```java
// ClassLoaderHierarchy.java
import java.lang.management.*;

public class ClassLoaderHierarchy {
    public static void main(String[] args) {
        System.out.println("=== Class Loader Hierarchy ===\n");

        // Bootstrap class loader (loads java.lang, etc.) — represented as null in older Java
        ClassLoader bootstrap = String.class.getClassLoader();
        System.out.println("String (java.lang) loader   : " + bootstrap);
        System.out.println("  (null = bootstrap loader = loads java.base module)\n");

        // Platform class loader (loads javax.*, some java.* from non-base modules)
        ClassLoader platform = ClassLoader.getPlatformClassLoader();
        System.out.println("Platform class loader       : " + platform);

        // Application class loader (loads your app classes)
        ClassLoader app = ClassLoaderHierarchy.class.getClassLoader();
        System.out.println("Application class loader    : " + app);
        System.out.println("  Loads classes from: classpath / module path\n");

        // Walk the parent chain
        System.out.println("Class loader hierarchy:");
        ClassLoader cl = app;
        int depth = 0;
        while (cl != null) {
            System.out.println("  " + "  ".repeat(depth) + cl.getClass().getName() + " (" + cl.getName() + ")");
            cl = cl.getParent();
            depth++;
        }
        System.out.println("  " + "  ".repeat(depth) + "[bootstrap] (null parent)");
    }
}
```

**How to run:** `java ClassLoaderHierarchy.java`

`String.class.getClassLoader()` returns `null` — the bootstrap class loader is represented as null in Java (it's a native JVM component, not a Java object). The parent-delegation model means every class load starts at the bootstrap and only falls to the application loader if not found higher up.

### Level 3 — Advanced

Same JVM probe grown to demonstrate JIT warm-up by measuring the same method before and after it becomes "hot" (invocation count exceeds JIT threshold), showing the interpreter-to-JIT transition.

```java
// JvmJitWarmup.java
import java.lang.management.*;
import java.util.*;

public class JvmJitWarmup {

    // This method will be JIT-compiled after sufficient invocations
    static double mathHeavy(int n) {
        double acc = 0;
        for (int i = 1; i <= n; i++) acc += Math.sqrt(i) * Math.log(i + 1);
        return acc;
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== JVM JIT Warm-up Demo ===");
        System.out.println("JVM: " + System.getProperty("java.vm.name"));
        System.out.println();

        int N = 50_000;
        int ROUNDS = 12;
        long[] times = new long[ROUNDS];

        for (int r = 0; r < ROUNDS; r++) {
            long t0 = System.nanoTime();
            double result = mathHeavy(N);
            times[r] = (System.nanoTime() - t0) / 1_000;  // µs
        }

        System.out.printf("%-6s  %-10s  %s%n", "Round", "Time (µs)", "Interpretation");
        System.out.println("-".repeat(55));
        for (int r = 0; r < ROUNDS; r++) {
            String note;
            if (r == 0)        note = "interpreter (cold)";
            else if (r <= 2)   note = "interpreter / C1 JIT warmup";
            else if (r <= 5)   note = "C1 compiled (client JIT)";
            else               note = "C2 compiled (server JIT, fully optimised)";
            System.out.printf("  %3d    %8d µs  %s%n", r+1, times[r], note);
        }

        // Memory state after multiple GC-eligible allocations
        System.out.println("\n[ Memory after warm-up ]");
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        System.out.printf("Heap: %d MB used / %d MB committed%n",
            mem.getHeapMemoryUsage().getUsed() / (1024*1024),
            mem.getHeapMemoryUsage().getCommitted() / (1024*1024));
        System.out.printf("Non-heap (method area + JIT cache): %d MB%n",
            mem.getNonHeapMemoryUsage().getUsed() / (1024*1024));

        // Loaded class count
        System.out.println("Classes loaded: " +
            ManagementFactory.getClassLoadingMXBean().getLoadedClassCount());
    }
}
```

**How to run:** `java JvmJitWarmup.java`

Early rounds are slow (interpreter); later rounds are dramatically faster as HotSpot's C1 then C2 JIT compiler kicks in. Non-heap memory includes the Method Area where JIT-compiled native code is cached.

## 6. Walkthrough

Execution in `JvmJitWarmup.main`:

1. **12 rounds of `mathHeavy(50_000)`** — each call computes a sum of `sqrt(i) * log(i+1)` for 50,000 values. The first call runs fully interpreted. `System.nanoTime()` captures wall-clock nanoseconds before and after.

2. **Invocation counter** — HotSpot tracks how often each method is called. When the counter exceeds ~1,500 it triggers **C1 compilation** (the client JIT — fast compilation, moderate optimisation). When the counter exceeds ~10,000, it triggers **C2 compilation** (the server JIT — slow compilation, aggressive optimisation including loop unrolling, inlining, and SIMD generation).

3. **Time series** — you see a gradual speedup:
   - Round 1: interpreter ~500–2000 µs
   - Round 4: C1 compiled ~100–300 µs
   - Round 8+: C2 compiled ~20–80 µs

4. **Non-heap memory** — `getNonHeapMemoryUsage()` covers the Method Area (class metadata) plus the JIT code cache. After 12 rounds of compilation, the JIT cache grows as compiled native code for `mathHeavy` is stored here.

5. **Class loading** — `getLoadedClassCount()` shows how many classes have been loaded since JVM startup. `mathHeavy` itself doesn't load new classes, but each `ManagementFactory` call may trigger lazy-loading of management classes.

JIT state machine for `mathHeavy`:
```
Invocation 1:        → interpreter (bytecode step-by-step)
Invocation ~1,500:   → C1 JIT compile (runs in background)
Invocations 1500-9999: → C1-compiled native code (faster)
Invocation ~10,000:  → C2 JIT compile (background, aggressive)
Invocations 10000+:  → C2-compiled native code (fully optimised)
```

## 7. Gotchas & takeaways

> **Benchmarking without JIT warm-up is meaningless.** The first few executions of a method in a JVM-mode program run in the interpreter, which can be 10–100× slower than the JIT-compiled version. Always warm up (run the method several hundred times) before timing. Use JMH (Java Microbenchmark Harness) for reliable benchmarks.

> **`StackOverflowError` is NOT a heap error.** It's a stack error — too many nested method calls without returning. Each method call pushes a frame onto the per-thread JVM stack. Deep recursion without a base case fills the stack. The default stack depth varies (typically 500–2000 frames) and can be tuned with `-Xss`.

- JVM = class loader + bytecode verifier + execution engine (interpreter + JIT) + GC + runtime services.
- Heap stores objects (GC'd). JVM stack stores method frames (per thread, not GC'd). Method Area stores class data and JIT code.
- JIT warm-up: code is interpreted first, then C1-compiled (~1,500 invocations), then C2-compiled (~10,000 invocations).
- `ManagementFactory` exposes live JVM internals (memory, GC, threads, classes) — use it for diagnostics.
- `ClassLoader` hierarchy: bootstrap (null) ← platform ← application. Parent-delegation means every class load starts at bootstrap.
- Non-heap memory (Method Area + JIT code cache) is outside the heap and is not GC'd in the normal sense — it grows as new classes are loaded and methods are JIT-compiled.
