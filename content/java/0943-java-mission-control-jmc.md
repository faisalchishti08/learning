---
card: java
gi: 943
slug: java-mission-control-jmc
title: Java Mission Control (JMC)
---

## 1. What it is

JDK Mission Control (JMC) is the free desktop application used to open, visualize, and explore [Java Flight Recorder](0942-java-flight-recorder-jfr.md) `.jfr` files — it is the analysis front-end to JFR's recording back-end. Where JFR is the low-overhead mechanism embedded in the JVM that *produces* a recording, JMC is the separate tool you actually use to *read* one: it renders the recording's timeline as interactive graphs (GC pauses over time, CPU usage per thread, heap occupancy), lets you drill into specific event types (lock contention, exceptions, allocations by class or call site), and can also attach live to a running JVM to start or manage recordings directly through its UI rather than the command line. It ships separately from the JDK itself (downloadable from Oracle or via most package managers) but is designed specifically around JFR's data format, so opening a `.jfr` file in JMC is the standard, expected next step after capturing one.

## 2. Why & when

JMC is worth reaching for specifically when a recording is large or complex enough that reading its raw event stream by hand (or via `jfr print`, JFR's own command-line summarizer) would be slow and error-prone — its automated rule-based analysis engine scans a recording and proactively flags likely problem areas (a specific GC pause pattern, high lock contention on a specific object, an exception thrown at a suspiciously high rate) with severity scores, giving you a prioritized starting point instead of a blank timeline to explore unguided. It is most valuable for exactly the kind of correlation-across-event-types investigation JFR recordings enable: for example, confirming that a spike in request latency lines up, in time, with both a longer-than-usual GC pause and a concurrent surge in lock-contention events, which is far easier to see as overlapping graphs on a shared timeline than by cross-referencing separate log files. For a quick, simple question ("did a full GC happen in this recording, and when"), the lighter-weight `jfr print --events jdk.GarbageCollection recording.jfr` command-line tool is often faster than launching a full desktop application — JMC earns its overhead specifically for deeper, multi-event-type investigation.

## 3. Core concept

```
JFR (embedded in the JVM)  -->  produces  -->  recording.jfr (binary event data)
                                                       |
                                                       v
JMC (separate desktop app) -->  opens & visualizes  --> interactive timeline:
   - GC tab: pause durations and types over time
   - Threads tab: per-thread CPU%, state, contention
   - Memory tab: allocation rate, by class and call site
   - Automated Analysis Results: rule-based, severity-scored findings,
     e.g. "Long GC pause detected: 210ms at t=8.4s"

Quick alternative for simple questions (no GUI needed):
   jfr print --events jdk.GarbageCollection recording.jfr
```

JMC's automated analysis engine is the key productivity feature: rather than manually scanning every event type across the whole recording, it surfaces the most likely-relevant findings first, ranked by severity, as a starting point for deeper manual investigation.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JMC's automated analysis results panel listing severity-scored findings such as a long GC pause and high lock contention, each linking to the corresponding point on the recording's timeline" >
  <rect x="20" y="20" width="600" height="130" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="38" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Automated Analysis Results</text>

  <rect x="40" y="50" width="560" height="25" fill="none" stroke="#f0883e"/>
  <text x="50" y="66" fill="#f0883e" font-size="9" font-family="sans-serif">[SEVERITY: 87] Long GC pause detected -- 210ms at t=8.4s</text>

  <rect x="40" y="80" width="560" height="25" fill="none" stroke="#f0883e"/>
  <text x="50" y="96" fill="#f0883e" font-size="9" font-family="sans-serif">[SEVERITY: 62] High lock contention on 'lockA' -- 340ms total wait</text>

  <rect x="40" y="110" width="560" height="25" fill="none" stroke="#79c0ff"/>
  <text x="50" y="126" fill="#79c0ff" font-size="9" font-family="sans-serif">[SEVERITY: 24] Elevated exception rate -- 1,200 thrown in 60s</text>
</svg>

*JMC scans a recording automatically and lists likely problem areas by severity, giving you a prioritized starting point rather than an unguided timeline.*

## 5. Runnable example

Scenario: produce a recording with a deliberately obvious problem, then use JMC-style analysis tools to locate it — starting with a basic recording, then querying it with the command-line `jfr` tool for a quick answer, then walking through what JMC's automated analysis would flag and why, connecting the tool's output back to the specific code responsible.

### Level 1 — Basic

```java
import java.util.*;

public class JmcTargetWorkload {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> retained = new ArrayList<>();
        for (int round = 0; round < 40; round++) {
            for (int i = 0; i < 8_000; i++) {
                retained.add(new byte[300]);
            }
            System.out.println("round " + round + ", retained=" + retained.size());
            Thread.sleep(150);
        }
    }
}
```

**How to run:** `java -Xmx128m -XX:StartFlightRecording=filename=jmc-demo.jfr,duration=60s JmcTargetWorkload.java` (JDK 17+; a small `-Xmx` combined with sustained retention should eventually produce a longer, more noticeable GC pause worth flagging).

Expected output:
```
round 0, retained=8000
...
round 39, retained=320000
```
A `jmc-demo.jfr` file is written at the end of the run, ready for analysis.

This produces the raw recording data — the point of this level is simply to have a `.jfr` file on disk that genuinely contains an interesting event to find in the next steps.

### Level 2 — Intermediate

```java
// (Same JmcTargetWorkload.java as Level 1 -- this level is about ANALYZING the recording it produced)
```

**How to run:** without opening JMC's GUI, first try the lightweight command-line summarizer: `jfr summary jmc-demo.jfr` followed by `jfr print --events jdk.GarbageCollection jmc-demo.jfr` (JDK 17+ ships the `jfr` CLI tool alongside `java`).

Expected output shape:
```
$ jfr summary jmc-demo.jfr
 Version: 2.1
 Chunks: 1
 Start: 2026-07-10T10:15:22Z
 Duration: 6.2 s
 ...
 Event Type                          Count
 jdk.GarbageCollection                  18
 jdk.JavaMonitorEnter                    0
 jdk.ExecutionSample                   620

$ jfr print --events jdk.GarbageCollection jmc-demo.jfr
jdk.GarbageCollection {
  startTime = 10:15:24.001
  gcId = 12
  name = "G1 Evacuation Pause"
  duration = 145.2 ms   <-- notably larger than the surrounding ~2ms pauses
}
```

The real-world concern added: before reaching for the full JMC desktop application, the command-line `jfr` tool already answers a specific, well-defined question ("was there an unusually long GC pause, and when") directly from the terminal — useful when working over SSH on a remote server with no GUI available, or simply when the question is narrow enough not to need JMC's richer, cross-event-type correlation view.

### Level 3 — Advanced

```java
import java.util.*;

public class JmcCorrelatedAnomaly {
    static final Object lock = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread contender = new Thread(() -> {
            while (true) {
                synchronized (lock) {
                    try { Thread.sleep(120); } catch (InterruptedException ignored) {}
                }
            }
        });
        contender.setDaemon(true);
        contender.start();

        List<byte[]> retained = new ArrayList<>();
        for (int round = 0; round < 40; round++) {
            synchronized (lock) {
                for (int i = 0; i < 8_000; i++) {
                    retained.add(new byte[300]);
                }
            }
            System.out.println("round " + round + ", retained=" + retained.size());
            Thread.sleep(150);
        }
    }
}
```

**How to run:** `java -Xmx128m -XX:StartFlightRecording=filename=correlated.jfr,duration=60s,settings=profile JmcCorrelatedAnomaly.java` (JDK 17+), then open `correlated.jfr` in JMC's GUI (`jmc correlated.jfr`) and check the "Automated Analysis Results" tab, then cross-reference the "Threads" and "GC" tabs at the same timestamp.

Expected findings in JMC's Automated Analysis Results:
```
[Long GC pause detected] a G1 Evacuation Pause of ~140ms at approximately t=8.4s
[High lock contention] repeated JavaMonitorEnter waits on 'lock', clustering around t=8-9s
```

The production-flavored hard case: because both the GC pause and the lock-contention spike are flagged as occurring around the same narrow time window, JMC's side-by-side timeline view (not just two separate findings in a list) lets you directly confirm they're related — here, because both the GC-triggering allocation loop and the background `contender` thread compete for the same `lock`, a long GC pause happening to coincide with a lock-held window compounds into a worse overall stall than either alone, which is exactly the kind of multi-factor interaction that's easy to miss when looking at GC logs and thread dumps as separate, disconnected data sources.

## 6. Walkthrough

Tracing the analysis process for `correlated.jfr`, in the order a real JMC session would follow:

1. Opening the recording in JMC first presents the "Automated Analysis Results" tab, which has already scanned every event type in the recording and surfaces its findings ranked by severity — this is the deliberate starting point, giving you specific things to investigate rather than an empty timeline.
2. The top finding, a long GC pause (~140ms, notably larger than typical young-generation pauses of only a few milliseconds), links directly to its position on the recording's timeline — clicking it jumps the view to approximately t=8.4s.
3. A second finding, high lock contention on `lock`, also links to a timeline position — and critically, that position overlaps almost exactly with the GC pause finding above, which is the signal worth investigating further rather than treating as two unrelated issues.
4. Switching to the "Threads" tab at that same timestamp shows the `contender` thread's state transitioning to `RUNNABLE`/holding-lock repeatedly, while the main thread's own attempt to enter `synchronized (lock)` (in order to append to `retained`) is shown blocked waiting for it — exactly matching the deliberate contention built into the code.
5. Switching to the "Memory"/"GC" tab at the same timestamp confirms the ~140ms G1 pause occurred while the main thread was *also* waiting on `lock` — meaning the effective end-to-end stall the main thread experienced in that round was not just the GC pause alone, but compounded by first waiting for the lock and only then hitting the GC pause (or vice versa, depending on exact timing), a composite delay that neither the GC log nor a single thread dump alone would have made as clearly visible as JMC's aligned, cross-event timeline does.
6. Having identified both contributing factors and confirmed their overlap directly (rather than assuming a coincidence), the concrete next step is exactly what the code itself demonstrates as fixable: separating the lock scope from the allocation-heavy loop (so lock contention and GC pressure are no longer both concentrated in the same critical section) — the same kind of targeted, evidence-based fix that [GC tuning](0937-gc-tuning-flags-ergonomics.md) and [thread dump](0941-thread-dumps.md) analysis each aim for individually, but which JMC's correlated view makes easier to spot as a compound problem in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** JMC's automated analysis rules are heuristic, not exhaustive — a genuine problem that doesn't match any built-in rule's pattern (an unusual application-specific slowdown, for instance) may produce no automated finding at all, even though the raw event data needed to diagnose it manually is still present in the recording; treat "Automated Analysis Results" as a helpful starting point, not a guarantee that every problem will be automatically flagged.

- JMC is the desktop analysis tool for [JFR](0942-java-flight-recorder-jfr.md) recordings — JFR produces the `.jfr` data inside the JVM, JMC visualizes and explores it afterward.
- Its "Automated Analysis Results" tab scans a recording for common problem patterns (long GC pauses, high lock contention, elevated exception rates) and surfaces them ranked by severity, giving a prioritized starting point.
- JMC's real strength is correlating multiple event types on a shared timeline — confirming, for instance, that a GC pause and a lock-contention spike happened at the same moment, which is much harder to see from separate log files.
- For simple, narrow questions, the lightweight command-line `jfr` tool (`jfr summary`, `jfr print --events ...`) often answers faster than launching the full GUI, especially over a remote/SSH session with no display.
- Automated analysis rules are heuristic, not exhaustive — an unusual, application-specific problem may require manually exploring the raw timeline rather than relying solely on flagged findings.
- See [Java Flight Recorder (JFR)](0942-java-flight-recorder-jfr.md) for how recordings are actually produced, and [profiling (VisualVM, async-profiler, JMH)](0945-profiling-visualvm-async-profiler-jmh.md) for complementary tools focused specifically on CPU/allocation profiling and microbenchmarking rather than JFR's broader, continuous-recording approach.
