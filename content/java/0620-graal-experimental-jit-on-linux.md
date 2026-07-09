---
card: java
gi: 620
slug: graal-experimental-jit-on-linux
title: Graal experimental JIT (on Linux)
---

## 1. What it is

Java 10 included an experimental Just-In-Time (JIT) compiler called **Graal**, written in Java itself, as an alternative to the C2 (Server) compiler written in C++. Graal is a research JIT compiler that uses a new intermediate representation (Graal IR) and aggressive optimisations like partial escape analysis, speculative inlining, and automatic vectorisation. In Java 10, Graal was available only on Linux x64 and had to be explicitly enabled with `-XX:+UnlockExperimentalVMOptions -XX:+UseJVMCICompiler`. It is the foundation of GraalVM, the polyglot runtime that supports multiple languages on the JVM.

## 2. Why & when

The C2 compiler, written in C++ in the HotSpot JVM, has served Java well for over two decades. However, it is notoriously difficult to maintain and extend — its codebase is hundreds of thousands of lines of complex C++ with deep assumptions about the JVM internals. Graal, written in Java, is easier to develop, debug, and optimise. It can be developed using standard Java tooling (IDEs, debuggers, profilers) and benefits from Java's memory safety. For early adopters on Linux in Java 10, Graal offered a glimpse of the future: a JIT compiler that could eventually match or exceed C2's performance while being more maintainable. The experimental flag in Java 10 was the first step toward Graal becoming a production compiler (which it achieved in JDK 16+ as the default on certain platforms).

## 3. Core concept

```bash
# Enable Graal JIT on Linux (JDK 10+)
java -XX:+UnlockExperimentalVMOptions \
     -XX:+UseJVMCICompiler \
     -jar myapp.jar

# JVMCI = JVM Compiler Interface — the pluggable compiler API
# Graal implements JVMCI, replacing C2 for JIT compilation
```

Graal plugs into the JVM via the **JVM Compiler Interface (JVMCI)**, a JDK 9 API that allows a Java-based compiler to replace C2. When enabled, the JVM routes all JIT compilation requests through JVMCI, which delegates to Graal. C1 (the client compiler, for quick compilations) is still used for initial compilations; Graal handles the heavy optimisations that C2 would normally do.

## 4. Diagram

<svg viewBox="0 0 580 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Graal JIT replaces C2 via the JVMCI pluggable compiler interface">
  <rect x="20" y="10" width="540" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#8b949e" font-size="10" font-family="sans-serif">JDK 9 and earlier (fixed compiler pipeline):</text>
  <rect x="30" y="45" width="180" height="30" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="120" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Interpreter → C1 → C2</text>
  <text x="220" y="65" fill="#8b949e" font-size="9" font-family="sans-serif">(C++ compilers only)</text>

  <line x1="30" y1="85" x2="540" y2="85" stroke="#8b949e" stroke-width="0.5"/>

  <text x="30" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">JDK 10+ with Graal (pluggable via JVMCI):</text>
  <rect x="30" y="115" width="120" height="30" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="90" y="135" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Interpreter → C1</text>
  <text x="160" y="135" fill="#8b949e" font-size="10" font-family="monospace">→</text>
  <rect x="175" y="115" width="120" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="235" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Graal (Java)</text>
  <text x="305" y="135" fill="#8b949e" font-size="9" font-family="sans-serif">← replaces C2</text>

  <text x="30" y="165" fill="#8b949e" font-size="9" font-family="sans-serif">Graal compiles Java bytecode → optimised machine code, same execution model as C2</text>
</svg>

Graal slots into the JIT pipeline at the same point C2 occupies — it's a drop-in replacement at the compiler level.

## 5. Runnable example

Scenario: demonstrating the concept and comparison of Graal vs C2 — starting with checking the active JIT compiler, extending to a computational benchmark that shows the effect of JIT compilation, and finally providing a guide to enabling and evaluating Graal.

### Level 1 — Basic

```java
// File: GraalDemo.java

public class GraalDemo {
    public static void main(String[] args) {
        System.out.println("=== Graal Experimental JIT (JDK 10+) ===\n");

        System.out.println("Graal is a Java-based JIT compiler that replaces");
        System.out.println("the C2 (Server) compiler. In JDK 10, it's experimental");
        System.out.println("and available on Linux x64 only.\n");

        System.out.println("To enable Graal:");
        System.out.println("  $ java -XX:+UnlockExperimentalVMOptions \\");
        System.out.println("      -XX:+UseJVMCICompiler \\");
        System.out.println("      -jar myapp.jar\n");

        System.out.println("To check which compiler is active:");
        System.out.println("  $ java -XX:+UnlockExperimentalVMOptions \\");
        System.out.println("      -XX:+UseJVMCICompiler \\");
        System.out.println("      -XX:+PrintCompilation MyApp.java");
        System.out.println("  (Look for JVMCI/Graal in the compilation output)\n");

        System.out.println("Platform support in JDK 10:");
        System.out.println("  Linux x64: ✅ (experimental)");
        System.out.println("  macOS:     ❌ (not available)");
        System.out.println("  Windows:   ❌ (not available)\n");

        System.out.println("Graal later became the basis of GraalVM and");
        System.out.println("the default JIT on ARM64 (JDK 16+) and in");
        System.out.println("some configurations on x64.");
    }
}
```

**How to run:** `java GraalDemo.java`

Expected output:
```
=== Graal Experimental JIT (JDK 10+) ===

Graal is a Java-based JIT compiler that replaces
the C2 (Server) compiler. In JDK 10, it's experimental
and available on Linux x64 only.

To enable Graal:
  $ java -XX:+UnlockExperimentalVMOptions \
      -XX:+UseJVMCICompiler \
      -jar myapp.jar

To check which compiler is active:
  $ java -XX:+UnlockExperimentalVMOptions \
      -XX:+UseJVMCICompiler \
      -XX:+PrintCompilation MyApp.java
  (Look for JVMCI/Graal in the compilation output)

Platform support in JDK 10:
  Linux x64: ✅ (experimental)
  macOS:     ❌ (not available)
  Windows:   ❌ (not available)

Graal later became the basis of GraalVM and
the default JIT on ARM64 (JDK 16+) and in
some configurations on x64.
```

The simplest overview: what Graal is, how to enable it, and its platform limitations in JDK 10.

### Level 2 — Intermediate

```java
// File: JITBenchmark.java

public class JITBenchmark {

    // A computationally intensive workload that benefits from JIT
    static long fibonacci(long n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }

    static long loopSum(int iterations) {
        long sum = 0;
        for (int i = 0; i < iterations; i++) {
            sum += i * i;
        }
        return sum;
    }

    public static void main(String[] args) {
        System.out.println("=== JIT Compilation Benchmark ===\n");

        // Warm up — let the JIT kick in
        System.out.println("Warming up (first runs are interpreted, later runs are JIT-compiled)...\n");

        // Fibonacci warmup (small n to be fast)
        for (int i = 0; i < 5; i++) {
            long start = System.nanoTime();
            long result = fibonacci(35);
            long time = System.nanoTime() - start;
            System.out.printf("  Run %d: fibonacci(35)=%d (%d ms)%n",
                i + 1, result, time / 1_000_000);
        }

        System.out.println("\nLoop summation warmup:");
        for (int i = 0; i < 5; i++) {
            long start = System.nanoTime();
            long result = loopSum(100_000_000);
            long time = System.nanoTime() - start;
            System.out.printf("  Run %d: sum=%d (%d ms)%n",
                i + 1, result, time / 1_000_000);
        }

        System.out.println("\nNotice: later runs are faster — the JIT compiled the hot methods.");
        System.out.println("Comparing C2 vs Graal would show different optimisation patterns.");
        System.out.println("C2 typically achieves steady-state within 2-3 runs.");
        System.out.println("Graal may take more warmup but can achieve better peak performance.");
    }
}
```

**How to run:** `java JITBenchmark.java`

Expected output:
```
=== JIT Compilation Benchmark ===

Warming up (first runs are interpreted, later runs are JIT-compiled)...

  Run 1: fibonacci(35)=9227465 (125 ms)
  Run 2: fibonacci(35)=9227465 (110 ms)
  Run 3: fibonacci(35)=9227465 (98 ms)
  Run 4: fibonacci(35)=9227465 (95 ms)
  Run 5: fibonacci(35)=9227465 (92 ms)

Loop summation warmup:
  Run 1: sum=... (45 ms)
  Run 2: sum=... (22 ms)
  Run 3: sum=... (20 ms)
  Run 4: sum=... (18 ms)
  Run 5: sum=... (18 ms)

Notice: later runs are faster — the JIT compiled the hot methods.
Comparing C2 vs Graal would show different optimisation patterns.
C2 typically achieves steady-state within 2-3 runs.
Graal may take more warmup but can achieve better peak performance.
```

The real-world benchmark: a computational workload that demonstrates JIT warmup. The pattern (first runs slow, later runs fast) is the same regardless of which JIT compiler is used — the difference between C2 and Graal is in how quickly they reach peak performance and what peak performance they achieve.

### Level 3 — Advanced

```java
// File: CompilerComparison.java

public class CompilerComparison {

    public static void main(String[] args) {
        System.out.println("=== C2 vs Graal: Compiler Comparison ===\n");

        System.out.printf("%-25s %-25s %-25s%n", "Aspect", "C2 (Server)", "Graal (Experimental)");
        System.out.println("─".repeat(75));

        System.out.printf("%-25s %-25s %-25s%n",
            "Language", "C++", "Java");
        System.out.printf("%-25s %-25s %-25s%n",
            "Codebase", "~300K lines C++", "~200K lines Java");
        System.out.printf("%-25s %-25s %-25s%n",
            "Escape Analysis", "Full", "Partial (better)");
        System.out.printf("%-25s %-25s %-25s%n",
            "Inlining", "Standard", "Speculative");
        System.out.printf("%-25s %-25s %-25s%n",
            "Vectorisation", "Auto (limited)", "Auto (aggressive)");
        System.out.printf("%-25s %-25s %-25s%n",
            "Peak perf (x64)", "Excellent", "Comparable+");
        System.out.printf("%-25s %-25s %-25s%n",
            "Warmup time", "Short (2-3 runs)", "Longer (5-10 runs)");
        System.out.printf("%-25s %-25s %-25s%n",
            "JDK 10 status", "Default", "Experimental (Linux)");
        System.out.printf("%-25s %-25s %-25s%n",
            "JDK 16+ status", "Default (x64)", "Default (AArch64)");

        System.out.println("\nKey Graal advantages (eventual):");
        System.out.println("  1. Written in Java — easier to maintain, debug, and contribute to");
        System.out.println("  2. Partial escape analysis — can optimise allocations that");
        System.out.println("     C2 would leave on the heap");
        System.out.println("  3. Speculative inlining — can inline through virtual calls");
        System.out.println("     based on runtime type profiles");
        System.out.println("  4. Foundation of GraalVM polyglot runtime");

        System.out.println("\nPractical guidance for JDK 10:");
        System.out.println("  • C2 is the safe choice for production");
        System.out.println("  • Graal is experimental — test, benchmark, but don't deploy");
        System.out.println("  • On Linux x64, you can A/B test with the flags shown above");
        System.out.println("  • Graal's real impact came later (JDK 16+ and GraalVM)");

        // Check if Graal might be available
        String os = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();
        boolean graalAvailable = os.contains("linux") && arch.contains("64");
        System.out.println("\nGraal available on this system: " + graalAvailable);
        System.out.println("  OS: " + os + ", Arch: " + arch);
    }
}
```

**How to run:** `java CompilerComparison.java`

Expected output:
```
=== C2 vs Graal: Compiler Comparison ===

Aspect                    C2 (Server)               Graal (Experimental)     
───────────────────────────────────────────────────────────────────────────
Language                  C++                       Java                     
Codebase                  ~300K lines C++           ~200K lines Java         
Escape Analysis           Full                      Partial (better)         
Inlining                  Standard                  Speculative              
Vectorisation             Auto (limited)            Auto (aggressive)        
Peak perf (x64)           Excellent                 Comparable+              
Warmup time               Short (2-3 runs)          Longer (5-10 runs)       
JDK 10 status             Default                   Experimental (Linux)     
JDK 16+ status            Default (x64)             Default (AArch64)        

Key Graal advantages (eventual):
  1. Written in Java — easier to maintain, debug, and contribute to
  2. Partial escape analysis — can optimise allocations that
     C2 would leave on the heap
  3. Speculative inlining — can inline through virtual calls
     based on runtime type profiles
  4. Foundation of GraalVM polyglot runtime

Practical guidance for JDK 10:
  • C2 is the safe choice for production
  • Graal is experimental — test, benchmark, but don't deploy
  • On Linux x64, you can A/B test with the flags shown above
  • Graal's real impact came later (JDK 16+ and GraalVM)

Graal available on this system: false/true
  OS: ..., Arch: ...
```

The production-flavoured comparison: C2 vs Graal across all relevant dimensions. The table shows Graal's architectural advantages (Java codebase, partial escape analysis) balanced against its JDK 10 limitations (experimental, Linux-only, longer warmup).

## 6. Walkthrough

Tracing what happens when Graal compiles a hot method:

1. **Method becomes hot**: The JVM's interpreter profiles method invocations. When a method exceeds the compilation threshold (default: 10,000 invocations for C1, higher for C2), the JVM queues it for JIT compilation.

2. **Compilation request**: With `-XX:+UseJVMCICompiler`, the compilation request is routed to JVMCI instead of the traditional C2 compiler thread. JVMCI is a Java API that the compiler implements.

3. **Graal receives the bytecode**: JVMCI passes the method's bytecode to Graal. Graal parses it and builds its own intermediate representation (Graal IR) — a graph-based IR where nodes represent operations and edges represent data and control flow.

4. **Graal optimisations**:
   - **Partial escape analysis**: unlike C2's "all-or-nothing" escape analysis, Graal can optimise an object that escapes on one path but not on another, scalar-replacing it on the non-escaping path.
   - **Speculative inlining**: Graal can inline a virtual method call based on the observed receiver type at runtime, with a deoptimisation guard that falls back to the interpreter if the assumption is violated.
   - **Aggressive vectorisation**: Graal recognises loops that operate on arrays of primitives and emits SIMD (Single Instruction Multiple Data) instructions for them.

5. **Machine code generation**: Graal emits platform-specific machine code (x64 instructions on Linux). The generated code is installed in the JVM's code cache.

6. **Method execution**: Subsequent invocations of the method use the compiled machine code directly, bypassing the interpreter. If a speculative assumption is violated (e.g., the receiver type changes), the JVM deoptimises — it discards the compiled code and falls back to the interpreter, re-profiling for a future recompilation.

## 7. Gotchas & takeaways

> Graal in JDK 10 is **experimental and not production-ready** — it is protected behind `-XX:+UnlockExperimentalVMOptions` for a reason. Performance may be worse than C2 for some workloads, warmup time is longer, and the compiler itself uses more memory (Graal is a Java application running inside the JVM). Do not use Graal in JDK 10 production environments without thorough benchmarking.

- Graal requires the `jdk.internal.vm.compiler` module to be present — this module ships with the JDK but is not loaded by default. `-XX:+UseJVMCICompiler` enables it.
- In JDK 10, Graal is only available on Linux x64. Support for macOS and Windows came later (JDK 11+). AArch64 support arrived in JDK 16.
- Graal is the compiler used by **GraalVM** for both JIT and AOT (native image) compilation. The JDK's bundled Graal is a subset focused on JIT; GraalVM adds polyglot capabilities (JavaScript, Python, Ruby, R, WebAssembly).
- `-XX:+PrintCompilation` shows which compiler compiled each method — with Graal active, methods compiled by Graal are prefixed differently from C2-compiled methods in the log output.
- The Graal compiler evolves rapidly — the JDK 10 version is significantly different from JDK 17's version, which is different from GraalVM's version. If evaluating Graal, use the latest version available for your platform. 