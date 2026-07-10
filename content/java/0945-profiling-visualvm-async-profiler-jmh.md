---
card: java
gi: 945
slug: profiling-visualvm-async-profiler-jmh
title: Profiling (VisualVM, async-profiler, JMH)
---

## 1. What it is

Profiling is measuring *where* a program actually spends its CPU time, allocates memory, or blocks on locks, as opposed to guessing based on reading the source code — three complementary tools cover this in the Java ecosystem, each for a different job. **VisualVM** is a free, GUI-based profiler bundled with (or easily added to) most JDK distributions, good for interactive, exploratory sessions: attach to a running process, watch live CPU/memory graphs, and take an on-demand CPU or memory snapshot. **async-profiler** is a low-overhead, sampling-based command-line profiler that works by periodically capturing stack traces (including native and JIT-compiled frames, which some profilers miss) without needing bytecode instrumentation, making it accurate and safe enough for production use, and it commonly outputs a **flame graph** — a visualization where each box is a stack frame, width represents time spent, and stacking represents call depth, making the most expensive call paths visually obvious at a glance. **JMH** (Java Microbenchmark Harness) is different in kind from the other two: rather than profiling a whole running application, it precisely measures the performance of one small, isolated piece of code (a single method or algorithm), carefully accounting for JIT warm-up, dead-code elimination, and other pitfalls that make naive hand-rolled "time it with `System.nanoTime()`" benchmarks unreliable.

## 2. Why & when

Use VisualVM for a first, interactive look at an application you don't yet have a specific hypothesis about — its live graphs are good for spotting an obvious CPU spike or memory growth pattern, and its snapshot-based CPU profiler is fine for a quick check, though its instrumentation-based sampling can itself introduce enough overhead to skew results under heavier load. Reach for async-profiler once you have a specific performance question and need trustworthy numbers, especially on a production or production-like system — its low overhead (achieved via a technique closer to how native profilers work, avoiding some of the classic Java profiler pitfalls like "safepoint bias," where samples are only ever taken at safepoints, skewing results toward whatever code happens to reach safepoints most often) makes it safe to run against real, loaded services, and its flame-graph output is often the fastest way to see "which specific method call path burns the most CPU" without wading through a table of numbers. Reach for JMH specifically when the question is "which of these two implementations of the same small operation is actually faster" — a question that's surprisingly easy to get a *wrong* answer to via naive benchmarking, since the JIT compiler's warm-up behavior, escape analysis, and dead-code elimination can all silently invalidate a hand-rolled timing loop's result without any obvious sign that something went wrong.

## 3. Core concept

```
VisualVM:        attach to running JVM -> live graphs (CPU%, heap, threads)
                  -> on-demand snapshot -> exploratory, good first look, some overhead

async-profiler:   attach or launch with agent -> low-overhead SAMPLING of stack traces
                  -> flame graph output:
                       widest boxes = most time spent in that call path
                       stacked boxes = deeper call chain
                  -> safe for production, precise answers to "where does time go"

JMH:              @Benchmark-annotated method -> harness handles JIT warm-up,
                  iterations, dead-code elimination avoidance -> statistically
                  sound throughput/latency numbers for ONE isolated piece of code
                  -> answers "is implementation A actually faster than B", NOT
                     "where does my whole app spend time"
```

Each tool answers a different-shaped question: VisualVM and async-profiler both profile a *running application's* behavior (the difference being overhead and precision), while JMH measures one *isolated piece of code* in a controlled, repeatable way — using JMH to profile a whole app, or a whole-app profiler to compare two algorithm variants precisely, is a common but avoidable mismatch.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A flame graph with stacked boxes representing call depth and box width representing time spent, with the widest box at the top highlighting the most expensive call path" >
  <rect x="20" y="130" width="600" height="25" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">main()</text>

  <rect x="30" y="100" width="250" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">processRequest()</text>
  <rect x="290" y="100" width="150" height="25" fill="#1c2430" stroke="#79c0ff"/>
  <text x="365" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">logEvent()</text>

  <rect x="40" y="70" width="220" height="25" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="87" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">parseJson()  -- WIDEST: most CPU time</text>

  <rect x="50" y="40" width="120" height="25" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="57" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Regex.matches()</text>

  <text x="320" y="20" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Width = time spent; height = call stack depth</text>
</svg>

*In a flame graph, the widest box at each level shows exactly which call path consumes the most CPU time — here, `parseJson` dominates, with `Regex.matches` as its main contributor.*

## 5. Runnable example

Scenario: identify a genuine CPU hot spot and confirm a fix using all three tools in the roles they're actually best at — starting with a basic CPU-heavy workload profiled interactively, then locating the exact hot method with a flame graph, then using JMH to rigorously confirm that a proposed faster implementation is actually faster, not just apparently faster.

### Level 1 — Basic

```java
import java.util.regex.Pattern;

public class ProfilingTargetWorkload {
    static final Pattern SLOW_PATTERN = Pattern.compile("^[a-zA-Z0-9]+@[a-zA-Z0-9.]+\\.[a-zA-Z]{2,}$");

    public static void main(String[] args) {
        long matches = 0;
        for (int i = 0; i < 2_000_000; i++) {
            String candidate = "user" + i + "@example.com";
            if (SLOW_PATTERN.matcher(candidate).matches()) {
                matches++;
            }
        }
        System.out.println("matched: " + matches);
    }
}
```

**How to run:** `java ProfilingTargetWorkload.java` (JDK 17+); while it runs, attach VisualVM (`jvisualvm`) to its PID and watch the live CPU graph.

Expected output:
```
matched: 2000000
```
VisualVM's live CPU graph shows sustained near-100% CPU usage for the duration of the run — a clear, if unspecific, signal that this program is CPU-bound, without yet pinpointing exactly which method is responsible.

### Level 2 — Intermediate

```java
// (Same ProfilingTargetWorkload.java as Level 1 -- this level profiles it with async-profiler for a precise answer)
```

**How to run:** `java -agentpath:/path/to/libasyncProfiler.so=start,event=cpu,file=profile.html ProfilingTargetWorkload.java` (JDK 17+; async-profiler is a separate download, attached via the `-agentpath` JVM flag, producing an interactive flame-graph HTML file directly).

Expected observation when opening `profile.html`:
```
Flame graph shows:
  main() -> Pattern.matches() -> Matcher.matches() -- by far the widest box,
  consuming the vast majority of total CPU samples
```

The real-world concern added: unlike VisualVM's live percentage graph, async-profiler's flame graph pinpoints the *exact* call path — here, regex matching via `Pattern`/`Matcher` — as the dominant CPU consumer, with low enough overhead that this measurement is trustworthy even under sustained, realistic load, giving a specific, actionable target (this particular regex call) rather than a general "the CPU is busy" observation.

### Level 3 — Advanced

```java
import org.openjdk.jmh.annotations.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Thread)
public class EmailValidationBenchmark {
    static final Pattern REGEX_PATTERN = Pattern.compile("^[a-zA-Z0-9]+@[a-zA-Z0-9.]+\\.[a-zA-Z]{2,}$");
    String candidate = "user12345@example.com";

    @Benchmark
    public boolean regexApproach() {
        return REGEX_PATTERN.matcher(candidate).matches();
    }

    @Benchmark
    public boolean manualApproach() {
        // A hand-written, non-regex validation of the same rough shape --
        // the proposed "faster" alternative to be rigorously compared against regex.
        int at = candidate.indexOf('@');
        if (at <= 0 || at == candidate.length() - 1) return false;
        int dot = candidate.lastIndexOf('.');
        return dot > at + 1 && dot < candidate.length() - 2;
    }
}
```

**How to run:** requires a JMH project setup (Maven/Gradle with the `jmh-core`/`jmh-generator-annprocess` dependencies); run via `mvn clean package && java -jar target/benchmarks.jar EmailValidationBenchmark` (JDK 17+; JMH cannot run as a bare single-file script since it relies on annotation-processing code generation).

Expected output shape (illustrative — a real run prints detailed warm-up iteration data first):
```
Benchmark                                Mode  Cnt    Score    Error  Units
EmailValidationBenchmark.regexApproach   avgt   25  185.412 ± 3.201  ns/op
EmailValidationBenchmark.manualApproach  avgt   25   12.847 ± 0.415  ns/op
```

The production-flavored hard case: JMH's harness automatically runs enough warm-up iterations for the JIT compiler to reach steady-state performance before measuring, runs enough measured iterations to report a statistically meaningful error margin, and structures the benchmark so the JIT cannot simply eliminate the "unused" return value as dead code — giving a rigorous, trustworthy confirmation that the hand-written `manualApproach` is genuinely roughly 14x faster than the regex-based approach identified as the hot spot in Level 2, not just an artifact of a naively-written, unreliable timing loop.

## 6. Walkthrough

Tracing the full investigation across all three tools, in the order a real performance investigation would follow:

1. `ProfilingTargetWorkload` runs and VisualVM's live CPU graph (Level 1) confirms the program is genuinely CPU-bound throughout its run — this is the coarse, first-pass signal that justifies looking deeper, but it doesn't yet say *which* method is responsible.
2. Re-running the identical workload under async-profiler (Level 2) produces a flame graph whose widest box, at the appropriate call depth, is `Pattern.matches()`/`Matcher.matches()` — this is the precise, low-overhead answer to "where specifically does the CPU time go," obtained via sampling real stack traces rather than instrumentation, and trustworthy enough to act on.
3. Having identified regex matching as the hot call path, a developer proposes a hand-written, non-regex alternative (`manualApproach`) that checks for the presence and rough position of `@` and `.` directly via `String.indexOf`/`lastIndexOf` — a plausible-looking optimization, but one whose actual speed advantage should not be assumed without rigorous measurement, since naive ad hoc timing (a raw `System.nanoTime()` loop with no JIT warm-up accounted for) is notoriously easy to get wrong for exactly this kind of small, hot method.
4. JMH's `@Benchmark`-annotated methods (Level 3) are each run through the harness's full protocol: several warm-up iterations first (letting the JIT compiler fully optimize both methods before any iteration counts toward the reported result), followed by several measured iterations whose results are averaged and reported with an explicit error margin (`±3.201`, `±0.415`) — this error margin is itself important, since it tells you whether the reported difference between the two approaches is statistically meaningful or could just be noise.
5. The benchmark's design also avoids two classic JMH pitfalls implicitly: each `@Benchmark` method *returns* its result (rather than computing and discarding it), which prevents the JIT compiler's dead-code elimination from noticing the result is unused and optimizing the entire computation away — a benchmark that silently measures "how fast is doing nothing" instead of the intended operation is one of the most common ways naive Java benchmarking goes wrong.
6. The final reported numbers — regex approach at ~185ns/op versus the manual approach at ~13ns/op — give a rigorous, trustworthy confirmation of roughly a 14x speedup, closing the loop from "the app is CPU-bound" (VisualVM) to "specifically because of this regex call" (async-profiler) to "and this specific alternative implementation is a genuine, statistically-sound improvement, not just an illusion of one" (JMH).

## 7. Gotchas & takeaways

> **Gotcha:** writing a "quick benchmark" as a bare loop with `System.nanoTime()` calls before and after, with no JIT warm-up phase and a discarded/unused result, is a well-known trap — the JIT compiler may not have finished optimizing the code being measured yet (making early iterations look artificially slow) or may eliminate the entire computation as dead code (making it look impossibly fast); always use JMH for any benchmark whose result will actually inform a real decision.

- VisualVM is a GUI-based, exploratory profiler good for a first, interactive look at CPU/memory behavior in a running JVM, at the cost of some measurement overhead.
- async-profiler is a low-overhead, sampling-based profiler that produces flame graphs, precise and safe enough for production use, and the right tool once you need to pinpoint exactly which call path is expensive.
- JMH (Java Microbenchmark Harness) measures one small, isolated piece of code rigorously, correctly handling JIT warm-up and avoiding dead-code-elimination pitfalls that make naive hand-rolled benchmarks unreliable — it answers "is A faster than B," not "where does my whole app spend time."
- In a flame graph, box width represents time spent and stacking represents call depth — the widest box at any level is the most expensive call path at that point in the stack.
- Never trust a hand-rolled `System.nanoTime()` benchmark for a decision that matters — always reach for JMH, since JIT warm-up and dead-code elimination can silently invalidate naive timing loops without any obvious sign of error.
- See [JIT compilation (C1/C2)](0919-jit-compilation-c1-client-c2-server.md) for why warm-up specifically matters to JMH's design, and [Java Flight Recorder (JFR)](0942-java-flight-recorder-jfr.md) for a complementary, continuous-recording alternative to on-demand profiling sessions.
