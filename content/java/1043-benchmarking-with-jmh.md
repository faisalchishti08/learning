---
card: java
gi: 1043
slug: benchmarking-with-jmh
title: Benchmarking with JMH
---

## 1. What it is

JMH (Java Microbenchmark Harness), built by the OpenJDK team specifically for this purpose, measures how long a small piece of Java code actually takes to run — accurately, which is far harder than it sounds on a JIT-compiled, garbage-collected runtime. A naive "measure with `System.nanoTime()` around a loop" benchmark is routinely wrong by orders of magnitude, because the JIT compiler can warm up mid-measurement, or — worse — notice that a computed result is never actually used and **eliminate the code entirely** (dead-code elimination), silently measuring nothing at all. JMH exists to sidestep both traps: it runs a proper warmup phase before measuring, and forces you to consume every computed result so the JIT can't optimize the work away.

## 2. Why & when

Benchmarking on the JVM is uniquely tricky because the runtime actively works against a naive measurement in two specific ways. First, the JIT compiler starts by interpreting bytecode and only compiles hot methods to optimized native code *after* they've run enough times — a benchmark that starts timing immediately measures a mix of slow interpreted execution and gradually-improving compiled execution, not the code's actual steady-state speed. Second, and more dangerously, if a benchmark computes a value and never uses it for anything visible, the JIT is free to recognize this and eliminate the entire computation — a benchmark can report "10 nanoseconds" for an operation that, in real, used code, actually takes 10 microseconds, because the JIT correctly determined the unused result didn't need to be computed at all.

Reach for JMH specifically when you need a trustworthy answer to "which of these two implementations is actually faster, and by how much" — comparing two algorithms, two data structures, two library calls for a genuinely performance-sensitive hot path. Skip formal benchmarking (JMH or otherwise) for code whose performance is clearly irrelevant to the application's actual bottlenecks — benchmarking effort is worth spending specifically where a measured difference would change a real decision.

## 3. Core concept

```java
import org.openjdk.jmh.annotations.*;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3)      // let the JIT warm up BEFORE measuring
@Measurement(iterations = 5) // then take 5 real measurement iterations
@Fork(1)                      // run in a fresh JVM process, isolated from other benchmarks
public class StringConcatBenchmark {

    @Benchmark
    public String concatWithPlus() {
        String result = "";
        for (int i = 0; i < 100; i++) {
            result += i; // naive concatenation -- creates many intermediate String objects
        }
        return result; // MUST return the result -- JMH consumes it, preventing dead-code elimination
    }

    @Benchmark
    public String concatWithBuilder() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            sb.append(i);
        }
        return sb.toString();
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JMH benchmark run showing a warmup phase where the JIT compiles hot code, followed by a measurement phase where actual timing samples are collected, contrasted with a naive benchmark that starts timing immediately with no warmup">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Naive: no warmup</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">timer starts immediately, mixed JIT states</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">JMH: warmup then measure</text>
  <rect x="380" y="40" width="100" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="430" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">warmup (discarded)</text>
  <rect x="490" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">measurement (kept)</text>
</svg>

JMH discards warmup-phase timings entirely, measuring only after the JIT has reached steady state.

## 5. Runnable example

Scenario: comparing `String` concatenation with `+` versus `StringBuilder`, evolving from a naive, misleading benchmark into a properly-warmed-up JMH benchmark that reveals the real difference.

### Level 1 — Basic

```java
// File: NaiveBenchmark.java -- a naive, MISLEADING benchmark: no warmup,
// timer starts immediately, JIT compilation state is inconsistent across runs.
public class NaiveBenchmark {
    public static void main(String[] args) {
        long start = System.nanoTime();
        String result = "";
        for (int i = 0; i < 100; i++) {
            result += i;
        }
        long elapsed = System.nanoTime() - start;
        System.out.println("Elapsed: " + elapsed + " ns, result length: " + result.length());
    }
}
```

**How to run:** save as `NaiveBenchmark.java`, then `javac NaiveBenchmark.java && java NaiveBenchmark` (JDK 17+).

Expected output (the exact nanosecond count will vary between runs, sometimes wildly):
```
Elapsed: <some number, often noisy/inconsistent between runs> ns, result length: 192
```

Running this program multiple times produces wildly inconsistent elapsed times, because the single measurement includes JVM startup and class-loading overhead, cold (uncompiled, interpreted) execution of the loop, and possibly the very beginning of JIT compilation kicking in mid-measurement — none of which represents this code's actual steady-state performance.

### Level 2 — Intermediate

```java
// File: WarmedUpBenchmark.java -- a hand-rolled improvement: run the operation
// MANY times first (a manual "warmup"), THEN measure -- closer to JMH's actual
// approach, though still missing JMH's protection against dead-code elimination.
public class WarmedUpBenchmark {
    static String concatWithPlus(int n) {
        String result = "";
        for (int i = 0; i < n; i++) {
            result += i;
        }
        return result;
    }

    public static void main(String[] args) {
        // Warmup: run it many times first, discarding the results, letting the
        // JIT compile this hot method before any real measurement begins.
        for (int i = 0; i < 10_000; i++) {
            concatWithPlus(100);
        }

        // NOW measure, after warmup -- a far more representative timing.
        long start = System.nanoTime();
        String result = concatWithPlus(100);
        long elapsed = System.nanoTime() - start;
        System.out.println("Warmed-up elapsed: " + elapsed + " ns, result length: " + result.length());
    }
}
```

**How to run:** save as `WarmedUpBenchmark.java`, then `javac WarmedUpBenchmark.java && java WarmedUpBenchmark` (JDK 17+).

Expected output (the exact number varies by machine, but should be noticeably smaller and more consistent across repeated runs than Level 1's):
```
Warmed-up elapsed: <some number, generally smaller and more stable than Level 1> ns, result length: 192
```

The real-world concern added: running the operation 10,000 times before measuring gives the JIT compiler a real chance to compile `concatWithPlus` to optimized native code before the timed measurement begins — much closer to the code's actual steady-state performance than Level 1's cold, single-shot measurement. This is still a hand-rolled approximation of what JMH automates and does far more rigorously.

### Level 3 — Advanced

```java
// File: src/main/java/StringConcatBenchmark.java
// A real JMH benchmark class -- requires the JMH annotation processor and
// dependencies on the classpath (see the pom.xml snippet below).
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.RunnerException;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
@State(Scope.Thread)
public class StringConcatBenchmark {

    @Benchmark
    public String concatWithPlus() {
        String result = "";
        for (int i = 0; i < 100; i++) {
            result += i;
        }
        return result; // returned value is CONSUMED by JMH, preventing dead-code elimination
    }

    @Benchmark
    public String concatWithBuilder() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            sb.append(i);
        }
        return sb.toString();
    }

    public static void main(String[] args) throws RunnerException {
        Options opt = new OptionsBuilder()
            .include(StringConcatBenchmark.class.getSimpleName())
            .build();
        new Runner(opt).run();
    }
}
```

```xml
<!-- Minimal JMH dependencies in pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-core</artifactId>
        <version>1.37</version>
    </dependency>
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-generator-annprocess</artifactId>
        <version>1.37</version>
        <scope>provided</scope>
    </dependency>
</dependencies>
```

**How to run:** place in a Maven project (with the dependencies above), then run `mvn compile exec:java -Dexec.mainClass=StringConcatBenchmark` (or package as an executable JAR per JMH's standard Maven archetype and run it directly).

Expected output (actual nanosecond values vary by machine, but the *relative* result — `concatWithBuilder` being substantially faster — is consistent):
```
Benchmark                                  Mode  Cnt    Score   Error  Units
StringConcatBenchmark.concatWithBuilder    avgt    5   ~800     ~50   ns/op
StringConcatBenchmark.concatWithPlus       avgt    5  ~4500     ~300   ns/op
```

The production-flavored hard case: JMH's `@Warmup`/`@Measurement` annotations formalize exactly what Level 2 approximated by hand, `@Fork(1)` runs the benchmark in a completely fresh JVM process to avoid any cross-contamination from other code that ran earlier in the same process, and returning the result from each `@Benchmark` method is what lets JMH consume it internally, guaranteeing the JIT can never eliminate the computation as dead code.

## 6. Walkthrough

Tracing what JMH actually does when running `StringConcatBenchmark`:

1. JMH forks a brand-new JVM process (per `@Fork(1)`) specifically for this benchmark class, ensuring no JIT compilation state, garbage collection history, or class-loading effects from any other code leak into this measurement.
2. Within that fresh process, JMH runs the **warmup phase**: it calls `concatWithPlus()` repeatedly (per `@Warmup(iterations = 3, time = 1)`, roughly three one-second-long batches of calls) — during this phase, the JIT compiler has the chance to notice `concatWithPlus` is being called frequently and compile it to optimized native code. Every timing from this phase is deliberately **discarded**.
3. Once the warmup phase completes, JMH begins the **measurement phase** (`@Measurement(iterations = 5, time = 1)`): it calls `concatWithPlus()` repeatedly again, but this time actually records the timing of each call, now that the method is running in its fully JIT-compiled, steady-state form — a far more representative number than any single cold measurement could produce.
4. Crucially, `concatWithPlus()` **returns** its `result` string — JMH's generated benchmarking code captures this return value into a special "blackhole" mechanism internally, which the JIT cannot prove is unused. Without this, the JIT would be free to notice that `result` is never actually used for anything visible and eliminate the entire loop as dead code, reporting a nonsensically fast (and completely wrong) time.
5. This entire process — fork, warmup, measure, consume the result — repeats identically for `concatWithBuilder()`.
6. JMH aggregates the recorded measurement-phase timings for each benchmark method into a final report showing average time per operation (`avgt`, per `@BenchmarkMode(Mode.AverageTime)`) along with an error margin, letting you compare `concatWithPlus` against `concatWithBuilder` with actual statistical confidence — rather than a single noisy `System.nanoTime()` measurement that could be wrong by an order of magnitude in either direction.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to return (or otherwise "consume," via JMH's `Blackhole` parameter) a benchmark method's computed result is the single most common way to accidentally benchmark nothing at all — the JIT's dead-code elimination is aggressive and can silently remove an entire loop's worth of work if it can prove the result is never actually used, making the reported time meaninglessly fast.

- JMH exists specifically to counter two ways naive JVM benchmarking is misleading: inconsistent JIT compilation state during measurement, and dead-code elimination silently removing unused computed results.
- `@Warmup` iterations are discarded entirely; only `@Measurement` iterations after warmup are recorded — this is what lets JMH measure a method's actual steady-state, JIT-compiled performance rather than a cold-start mixture.
- `@Fork` runs each benchmark in a fresh JVM process, preventing state from unrelated code (or other benchmarks) from contaminating the measurement.
- A `@Benchmark` method must return its computed result (or explicitly consume it via JMH's `Blackhole` API) — otherwise the JIT may eliminate the entire computation, and the benchmark reports a meaninglessly fast, wrong number.
- Reserve formal benchmarking effort for genuinely performance-sensitive hot paths where a measured difference would actually change a decision — not for code whose performance is clearly irrelevant to the application's real bottlenecks.
- A `println`-wrapped `System.nanoTime()` measurement (Level 1) is worse than no benchmark at all if its misleadingly precise-looking number gets treated as trustworthy — it's actively dangerous for exactly the reasons JMH's warmup and blackhole mechanisms exist to prevent.
