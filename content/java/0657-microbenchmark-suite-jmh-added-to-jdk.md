---
card: java
gi: 657
slug: microbenchmark-suite-jmh-added-to-jdk
title: Microbenchmark suite (JMH) added to JDK
---

## 1. What it is

Starting with **Java 12** (JEP 230), the OpenJDK source repository itself gained a **built-in microbenchmark suite** based on **JMH** (Java Microbenchmark Harness) — a set of benchmarks living under `test/micro/` in the JDK source tree, plus the build-system support to compile and run them. This is about the **JDK's own codebase**, not a new public API: it means the engineers who develop the JDK can now write and run rigorous, JMH-based performance benchmarks against JDK internals (collections, string operations, JVM primitives) as part of the standard OpenJDK build/test workflow, rather than relying on ad hoc external scripts. JMH itself is a well-established third-party benchmarking library (also used enormously in application code); this JEP is specifically about giving JDK contributors first-class, in-tree JMH support.

## 2. Why & when

Before this, if a JDK contributor wanted to benchmark a change (say, "does this tweak to `ArrayList.add` regress performance?"), there was no standard, checked-in way to do it — benchmarks lived in separate, unofficial repositories or personal scripts, making it hard to keep them in sync with the evolving JDK source, hard to onboard new contributors to a consistent benchmarking workflow, and hard to catch performance regressions systematically in CI. By vendoring JMH support directly into the JDK build, OpenJDK gained a shared, discoverable place (`test/micro/`) for performance-sensitive tests, using the same rigorous methodology (JVM warm-up handling, avoiding dead-code-elimination artifacts, statistical measurement) that JMH is known for in the broader Java community. As an application developer, this JEP itself doesn't hand you a new API — but it's worth knowing about because it signals the JDK's own performance testing discipline, and because it's a good excuse to look at **how** JMH avoids the classic pitfalls of hand-rolled microbenchmarks, since those same pitfalls apply just as much to benchmarks you write for your own code.

## 3. Core concept

```java
// A typical JMH benchmark class (using JMH as a dependency in YOUR project —
// this is the same style of benchmark the JDK itself now ships internally).
import org.openjdk.jmh.annotations.*;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Thread)
public class StringConcatBenchmark {

    @Benchmark
    public String plusOperator() {
        String s = "";
        for (int i = 0; i < 10; i++) s = s + i;
        return s;
    }

    @Benchmark
    public String stringBuilder() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 10; i++) sb.append(i);
        return sb.toString();
    }
}
```

JMH generates a wrapper harness around each `@Benchmark` method that runs warm-up iterations (to let the JIT compiler optimize the code, the way it would in a real long-running program) before the measured iterations begin, and it forces the result to be "consumed" so the JIT can't just delete the whole benchmark as dead code.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A naive hand-rolled benchmark measures cold, un-optimized code; JMH runs warm-up iterations first so measurement happens on JIT-optimized, steady-state code">
  <rect x="10" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="42" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Naive hand-rolled loop</text>
  <rect x="25" y="60" width="260" height="30" fill="#f85149" opacity="0.5"/>
  <text x="155" y="80" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">measure immediately (cold, unoptimized)</text>
  <text x="25" y="115" fill="#8b949e" font-size="9" font-family="sans-serif">Risks: JIT hasn't warmed up,</text>
  <text x="25" y="130" fill="#8b949e" font-size="9" font-family="sans-serif">dead-code elimination may</text>
  <text x="25" y="145" fill="#8b949e" font-size="9" font-family="sans-serif">skip the "unused" result entirely.</text>

  <rect x="320" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">JMH benchmark</text>
  <rect x="335" y="60" width="120" height="30" fill="#79c0ff" opacity="0.5"/>
  <text x="395" y="80" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">warm-up iters</text>
  <rect x="465" y="60" width="120" height="30" fill="#6db33f" opacity="0.7"/>
  <text x="525" y="80" fill="#0d1117" font-size="9" text-anchor="middle" font-family="monospace">measured iters</text>
  <text x="335" y="115" fill="#8b949e" font-size="9" font-family="sans-serif">JIT reaches steady state</text>
  <text x="335" y="130" fill="#8b949e" font-size="9" font-family="sans-serif">before measurement; results</text>
  <text x="335" y="145" fill="#8b949e" font-size="9" font-family="sans-serif">are "blackholed" to prevent DCE.</text>
</svg>

JMH separates warm-up from measurement and defeats compiler over-optimization, avoiding the two most common microbenchmarking mistakes.

## 5. Runnable example

Scenario: measuring whether `String` concatenation with `+` or `StringBuilder` is faster in a loop — first a naive hand-timed loop (showing the pitfalls), then a proper JMH benchmark of the same comparison, then extending the JMH benchmark with parameters to compare across different input sizes in one run.

### Level 1 — Basic

```java
// File: NaiveTiming.java
public class NaiveTiming {
    public static void main(String[] args) {
        int n = 1000;

        long start1 = System.nanoTime();
        String s = "";
        for (int i = 0; i < n; i++) {
            s = s + i;
        }
        long plusTime = System.nanoTime() - start1;

        long start2 = System.nanoTime();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(i);
        }
        String result = sb.toString();
        long builderTime = System.nanoTime() - start2;

        System.out.println("plus operator: " + (plusTime / 1000) + " microseconds");
        System.out.println("StringBuilder: " + (builderTime / 1000) + " microseconds");
        System.out.println("(lengths: " + s.length() + " vs " + result.length() + ")");
    }
}
```

**How to run:** `java NaiveTiming.java`

Expected output (numbers vary a lot run to run — that's exactly the problem):
```
plus operator: 45 microseconds
StringBuilder: 3 microseconds
(lengths: 2893 vs 2893)
```

This single-shot, no-warm-up measurement is exactly the kind of naive benchmark JMH exists to replace: run it several times and you'll see wildly different numbers, because the JIT compiler hasn't reached steady state and the JVM hasn't been given time to optimize either loop yet.

### Level 2 — Intermediate

```java
// File: StringConcatBenchmark.java
// Requires JMH on the classpath — with Maven, add dependencies:
//   org.openjdk.jmh:jmh-core and org.openjdk.jmh:jmh-generator-annprocess
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Thread)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
public class StringConcatBenchmark {

    @Benchmark
    public String plusOperator() {
        String s = "";
        for (int i = 0; i < 1000; i++) s = s + i;
        return s;
    }

    @Benchmark
    public String stringBuilder() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 1000; i++) sb.append(i);
        return sb.toString();
    }

    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
            .include(StringConcatBenchmark.class.getSimpleName())
            .build();
        new Runner(opt).run();
    }
}
```

**How to run:** with JMH dependencies on the classpath, compile and run this `main` (or, in a Maven/Gradle JMH setup, run `mvn clean install && java -jar target/benchmarks.jar StringConcatBenchmark`).

Expected output (abridged JMH report):
```
Benchmark                              Mode  Cnt   Score   Error  Units
StringConcatBenchmark.plusOperator     avgt    5  38.214 ± 2.103  us/op
StringConcatBenchmark.stringBuilder    avgt    5   2.847 ± 0.145  us/op
```

Unlike Level 1's single noisy measurement, JMH runs 3 warm-up iterations (discarded, letting the JIT optimize both methods) followed by 5 measured iterations, reporting an **average with an error margin** (`±`) — a statistically meaningful comparison instead of one noisy sample.

### Level 3 — Advanced

```java
// File: StringConcatSizedBenchmark.java
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Thread)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
public class StringConcatSizedBenchmark {

    @Param({"10", "100", "1000"})
    public int n;

    @Benchmark
    public String plusOperator() {
        String s = "";
        for (int i = 0; i < n; i++) s = s + i;
        return s;
    }

    @Benchmark
    public String stringBuilder() {
        StringBuilder sb = new StringBuilder(n * 4); // pre-size using the known parameter
        for (int i = 0; i < n; i++) sb.append(i);
        return sb.toString();
    }

    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
            .include(StringConcatSizedBenchmark.class.getSimpleName())
            .build();
        new Runner(opt).run();
    }
}
```

**How to run:** same JMH setup as Level 2.

Expected output (abridged; JMH runs every benchmark method once per `@Param` value):
```
Benchmark                                   (n)  Mode  Cnt    Score   Error  Units
StringConcatSizedBenchmark.plusOperator       10  avgt    5    0.412 ± 0.021  us/op
StringConcatSizedBenchmark.plusOperator      100  avgt    5    4.938 ± 0.312  us/op
StringConcatSizedBenchmark.plusOperator     1000  avgt    5   38.107 ± 1.987  us/op
StringConcatSizedBenchmark.stringBuilder      10  avgt    5    0.089 ± 0.006  us/op
StringConcatSizedBenchmark.stringBuilder     100  avgt    5    0.541 ± 0.034  us/op
StringConcatSizedBenchmark.stringBuilder    1000  avgt    5    2.812 ± 0.152  us/op
```

Level 3's `@Param({"10", "100", "1000"})` makes JMH run **every** `@Benchmark` method once for each listed value of `n`, revealing the key insight that raw microbenchmarking wouldn't show clearly in a single run: `plusOperator`'s cost grows **quadratically** with `n` (each `+` creates a new `String`, copying everything built so far), while `stringBuilder`'s cost grows **linearly** — the gap between the two widens dramatically as `n` increases from 10 to 1000.

## 6. Walkthrough

1. JMH's generated harness starts by reading the `@Param({"10", "100", "1000"})` annotation on the `n` field and the class-level annotations (`@Warmup(iterations = 3, ...)`, `@Measurement(iterations = 5, ...)`, `@Fork(1)`), building a full execution plan: run each `@Benchmark` method once per parameter value, each combination in its own forked JVM process (`@Fork(1)`) to avoid cross-benchmark JIT-state contamination.
2. For the first combination — `plusOperator` with `n = 10` — JMH forks a fresh JVM, sets the `n` field to `10` via reflection, and begins the **warm-up phase**: it calls `plusOperator()` repeatedly for roughly 3 one-second iterations, discarding all timing data from this phase. This lets the JIT compiler detect the method is "hot" and compile it down from interpreted bytecode to optimized machine code, just as would happen naturally in a long-running application.
3. Once warm-up completes, JMH enters the **measurement phase**: 5 more one-second iterations, this time recording precise timing data for each invocation of `plusOperator()`. Inside the method itself, the loop runs `n` times, each iteration doing `s = s + i` — string concatenation via `+` compiles to repeated `new StringBuilder(s).append(i).toString()` calls under the hood in older bytecode patterns, meaning each iteration re-copies the entire string built so far, an O(n) operation repeated n times — hence O(n²) total.
4. Crucially, JMH doesn't let the returned `String` just get discarded and optimized away: the harness consumes the benchmark method's return value (a "blackhole" mechanism), preventing the JIT's dead-code elimination from noticing "this loop's result is never used" and deleting the whole loop — a classic hand-rolled-benchmark trap that Level 1's naive code was vulnerable to.
5. JMH aggregates the 5 measured-iteration timings for this parameter combination into a mean (`Score`) and a confidence interval (`Error`), then reports one row: `plusOperator (n=10): 0.412 ± 0.021 us/op`.
6. This entire warm-up-then-measure-then-report cycle (steps 2–5) repeats independently for every remaining combination: `plusOperator` at `n=100`, `n=1000`, then `stringBuilder` at `n=10`, `n=100`, `n=1000` — each in its own fresh forked JVM.
7. After all combinations finish, JMH prints the consolidated results table. Reading down the `plusOperator` rows, the `Score` roughly quadruples each time `n` grows 10x (10→100→1000 shows a much-worse-than-linear pattern), while `stringBuilder`'s `Score` grows roughly proportionally to `n` — this side-by-side, statistically-sound comparison across input sizes is the payoff of using JMH's parameterized, warmed-up methodology instead of a single hand-timed loop.

```
JMH plan: for each @Param value of n, for each @Benchmark method:
    fork fresh JVM ──► warm-up (3×1s, discarded) ──► measure (5×1s, recorded)
                                    │
                            JIT reaches steady state before any number is kept
                                    │
    aggregate 5 measured iterations ──► Score ± Error ──► one report row
```

## 7. Gotchas & takeaways

> A hand-rolled `System.nanoTime()` benchmark like Level 1 is vulnerable to **two classic traps**: measuring cold/un-JIT-optimized code (giving misleadingly slow numbers for what will actually run fast in steady state), and having its "unused" result silently deleted by dead-code elimination (giving misleadingly fast — even zero — numbers for work the JIT decided never needed to happen). JMH's warm-up phases and blackhole mechanism exist specifically to close both traps; don't trust ad hoc timing loops for anything you plan to make a real engineering decision from.

- This JEP is about the **JDK's own** internal benchmark suite (`test/micro/`) gaining JMH support — it doesn't add a new public API to `java.*` that your application code calls.
- JMH itself (as a library you add to your own project's build) predates this JEP by years and is the de facto standard for Java microbenchmarking regardless of JDK version.
- Always separate warm-up iterations from measured iterations — the JIT compiler's behavior on cold code is not representative of a long-running application's steady state.
- Watch for dead-code elimination silently invalidating a benchmark's result — JMH's `@Benchmark` return-value consumption (or explicit `Blackhole` parameters) guards against this; hand-rolled loops usually don't.
- Use `@Param` to benchmark across multiple input sizes/configurations in one run — a single data point rarely tells the whole story about how an algorithm's cost scales.
