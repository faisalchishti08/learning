---
card: java
gi: 944
slug: gc-logging
title: GC logging
---

## 1. What it is

GC logging is the JVM's built-in facility for writing a structured, human-readable record of every garbage-collection event as it happens, controlled via the unified logging framework introduced in Java 9 (`-Xlog:gc*`, replacing the older, differently-formatted `-XX:+PrintGCDetails` flags used before it). Each line records what kind of collection ran (young, mixed, full), how long it took, and how much memory was reclaimed — enough detail, read over time, to build a complete picture of a running application's GC behavior: pause frequency, pause duration trends, and whether the collector is keeping up with the application's allocation rate or is instead sliding toward increasingly expensive full collections. It is the simplest, lowest-overhead, and most universally-available of all the GC diagnostic tools covered so far — unlike a [heap dump](0940-heap-dumps-analysis.md) or [JFR recording](0942-java-flight-recorder-jfr.md), a GC log is just plain text, viewable with `tail -f`, `grep`, or any log-aggregation tool already in place for a service's other logs.

## 2. Why & when

GC logging is worth enabling essentially everywhere in production, by default — its overhead is negligible (it's just writing a line of text per GC event, an event that already happened and would have occurred regardless of whether it's logged), and the value of having a continuous historical record when something eventually does go wrong for a long-running service is high enough that omitting it is rarely justified. It is the first place to look whenever a GC-related question arises: is this service's occasional latency spike correlated with GC pauses at all, is old-generation occupancy trending upward over the service's lifetime (pointing at a [memory leak](0938-memory-leaks-in-managed-memory.md)), or did a specific incident coincide with a "Pause Full" fallback event. Because it's plain text and low-overhead, it's also the natural first-line diagnostic tool to check before reaching for something heavier like a [JFR recording](0942-java-flight-recorder-jfr.md) or [heap dump](0940-heap-dumps-analysis.md) — those tools answer "why," while the GC log usually answers "whether, when, and roughly how bad" quickly enough to decide if the heavier tools are even needed.

## 3. Core concept

```
-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=10M

Breaking down the flag:
  gc*              -- log all GC-related tags (gc, gc+heap, gc+ergo, etc.)
  file=gc.log       -- write to this file instead of stdout
  time,uptime,...   -- decorators: what metadata to prefix each line with
  filecount=5,filesize=10M  -- log ROTATION: keep 5 files of 10MB each, oldest overwritten

Sample log lines:
[2026-07-10T10:15:22.001+0000][0.512s][info][gc] GC(0) Pause Young (Normal) ... 12M->4M(64M) 1.821ms
[2026-07-10T10:15:30.204+0000][8.715s][info][gc] GC(14) Pause Full (G1 Compaction Pause) ... 60M->22M(64M) 210ms
```

Log rotation (`filecount`/`filesize`) matters for any long-running service: without it, an always-on GC log for a service running for months would grow without bound — exactly the kind of unbounded-growth mistake worth avoiding on the *logging* side, even while using logging to hunt for unbounded growth elsewhere.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A GC log file being written continuously, with rotation kicking in once the current file reaches its size limit, cycling through a fixed number of files" >
  <rect x="20" y="40" width="120" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">gc.log.0 (active, filling)</text>

  <rect x="160" y="40" width="100" height="40" fill="#1c2430" stroke="#8b949e"/>
  <text x="210" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">gc.log.1</text>

  <rect x="280" y="40" width="100" height="40" fill="#1c2430" stroke="#8b949e"/>
  <text x="330" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">gc.log.2</text>

  <rect x="400" y="40" width="100" height="40" fill="#1c2430" stroke="#8b949e"/>
  <text x="450" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">gc.log.3</text>

  <rect x="520" y="40" width="100" height="40" fill="none" stroke="#f0883e" stroke-dasharray="3"/>
  <text x="570" y="64" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">gc.log.4 (oldest, next overwritten)</text>

  <path d="M 620 80 Q 620 130 320 130 Q 20 130 20 80" fill="none" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">when gc.log.0 fills, it rotates to .1, pushing the oldest file out -- bounded total disk usage</text>
</svg>

*Log rotation keeps GC logging safe to leave on indefinitely — bounded total disk usage, no unbounded growth of its own.*

## 5. Runnable example

Scenario: use GC logging to answer a real diagnostic question end to end — starting with basic logging enabled on a workload, then adding rotation for a realistic long-running configuration, then parsing the log programmatically to extract a specific, actionable metric (a trend in pause duration over time).

### Level 1 — Basic

```java
import java.util.*;

public class GcLoggingBasicWorkload {
    public static void main(String[] args) throws InterruptedException {
        List<byte[]> retained = new ArrayList<>();
        for (int round = 0; round < 20; round++) {
            for (int i = 0; i < 5_000; i++) {
                retained.add(new byte[300]);
            }
            Thread.sleep(100);
        }
        System.out.println("done, retained=" + retained.size());
    }
}
```

**How to run:** `java -Xlog:gc -Xmx64m GcLoggingBasicWorkload.java` (JDK 17+).

Expected output (interleaved with the program's own output, on stdout since no `file=` was given):
```
[0.021s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 8M->2M(64M) 1.4ms
[0.045s][info][gc] GC(1) Pause Young (Normal) (G1 Evacuation Pause) 9M->2M(64M) 1.2ms
...
done, retained=100000
```

With no `file=` specified, GC log lines print directly to standard output alongside the program's own prints — fine for quick, ad hoc checks, but not what you'd want for a long-running production service, which is exactly what the next level addresses.

### Level 2 — Intermediate

```java
// (Same GcLoggingBasicWorkload.java as Level 1 -- this level changes only the logging CONFIGURATION)
```

**How to run:** `java -Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=1M -Xmx64m GcLoggingBasicWorkload.java` (JDK 17+; `gc*` widens the tag set beyond just `gc`, and rotation keeps the log bounded).

Expected content of `gc.log` after the run:
```
[2026-07-10T10:20:01.102+0000][0.021s][info][gc,heap] Heap region size: 1M
[2026-07-10T10:20:01.105+0000][0.023s][info][gc          ] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 8M->2M(64M) 1.4ms
[2026-07-10T10:20:01.106+0000][0.024s][info][gc,heap     ] GC(0) DefNew: 8M->2M(9M)
...
```

The real-world concern added: the wider `gc*` tag set captures additional detail (heap region sizing, per-generation breakdowns) beyond the plain `gc` tag alone, `file=gc.log` redirects output away from the application's own stdout entirely (essential once a service runs for months and you need a persistent record, not just terminal scrollback), and `filecount=5,filesize=1M` bounds total disk usage so the log itself never becomes an unbounded-growth problem.

### Level 3 — Advanced

```java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class GcLogPauseAnalyzer {
    public static void main(String[] args) throws Exception {
        // Parses gc.log (produced by a prior run) and reports pause-duration trend over time.
        Pattern pausePattern = Pattern.compile("Pause \\w+.*?([\\d.]+)ms\\s*$");
        List<Double> pausesMs = new ArrayList<>();

        for (String line : Files.readAllLines(Paths.get("gc.log"))) {
            Matcher m = pausePattern.matcher(line.trim());
            if (m.find()) {
                pausesMs.add(Double.parseDouble(m.group(1)));
            }
        }

        if (pausesMs.isEmpty()) {
            System.out.println("no pause events found -- run the workload with GC logging enabled first");
            return;
        }

        double firstHalfAvg = average(pausesMs.subList(0, pausesMs.size() / 2));
        double secondHalfAvg = average(pausesMs.subList(pausesMs.size() / 2, pausesMs.size()));
        System.out.printf("parsed %d pause events%n", pausesMs.size());
        System.out.printf("first-half avg pause: %.2fms, second-half avg pause: %.2fms%n", firstHalfAvg, secondHalfAvg);
        if (secondHalfAvg > firstHalfAvg * 1.5) {
            System.out.println("WARNING: pause durations trending upward -- investigate possible memory pressure or leak");
        } else {
            System.out.println("pause durations stable across the run");
        }
    }

    static double average(List<Double> vals) {
        return vals.stream().mapToDouble(Double::doubleValue).average().orElse(0);
    }
}
```

**How to run:** first generate a log with a genuinely worsening trend: `java -Xlog:gc*:file=gc.log -Xmx48m GcLoggingBasicWorkload.java` (a tight heap makes later pauses costlier as retained data grows relative to available space), then run `java GcLogPauseAnalyzer.java` (JDK 17+) in the same directory.

Expected output shape:
```
parsed 22 pause events
first-half avg pause: 1.35ms, second-half avg pause: 4.80ms
WARNING: pause durations trending upward -- investigate possible memory pressure or leak
```

The production-flavored hard case: rather than eyeballing a potentially thousands-of-lines-long log file by hand, this parses every pause event's duration with a regular expression and computes a concrete, quantified trend (first-half versus second-half average pause time) — turning "does this log look concerning" into an automatable, alertable check exactly the kind a real monitoring pipeline would run periodically against a service's live GC log.

## 6. Walkthrough

Tracing `GcLogPauseAnalyzer.main` end to end:

1. The program opens `gc.log` (produced by an earlier run of the workload under GC logging) and reads it line by line, applying a regular expression designed to match the pause-duration suffix common to G1's various pause-type log lines (`Pause Young (Normal) ... 1.4ms`, `Pause Full ... 210ms`, and so on).
2. Every line that matches contributes its parsed millisecond value to the `pausesMs` list, in the exact chronological order the events occurred in the log — since GC log lines are always written in time order, this list is implicitly a time series of pause durations across the run.
3. The list is split into its first and second halves, and each half's average pause duration is computed separately — a simple but effective way to detect a *trend* (pauses getting progressively worse over time) rather than just an overall average, which could mask a worsening pattern by averaging it together with an earlier, healthier period.
4. If the second half's average pause duration exceeds the first half's by more than 50%, the program prints an explicit warning — this threshold is a simple heuristic standing in for the kind of automated alerting rule a real monitoring system would apply to a live, continuously-updating GC log, flagging exactly the "old-generation occupancy pressure trending upward" symptom associated with a genuine [memory leak](0938-memory-leaks-in-managed-memory.md) or simply an undersized heap.
5. The final printed summary — parsed event count, both half-averages, and the resulting verdict — gives a complete, quantified answer to "is this service's GC behavior degrading over time," derived entirely from the same plain-text log file that was already being written with negligible overhead throughout the original run, without needing a heap dump, thread dump, or JFR recording to reach this first-pass conclusion.

## 7. Gotchas & takeaways

> **Gotcha:** unified logging's tag syntax changed significantly from the older, pre-Java-9 GC logging flags (`-XX:+PrintGCDetails`, `-XX:+PrintGCDateStamps`, and similar) — a startup script or deployment configuration inherited from an older JDK version may still reference these removed flags, which (like [CMS](0931-cms-removed.md)'s flags) will cause the JVM to fail to start on modern versions; always audit legacy GC logging flags specifically when upgrading a service across major JDK versions.

- GC logging (`-Xlog:gc*`, unified logging since Java 9) writes a plain-text, low-overhead, continuous record of every collection event — pause type, duration, and memory reclaimed — and is worth enabling by default in production.
- It's the natural first-line diagnostic: cheap enough to always have on, and answers "whether, when, and roughly how bad" quickly enough to decide whether heavier tools ([heap dumps](0940-heap-dumps-analysis.md), [JFR](0942-java-flight-recorder-jfr.md)) are needed.
- `file=` redirects output to a dedicated file instead of stdout, and `filecount`/`filesize` bound total disk usage via rotation — essential for any long-running service, so the log itself never becomes an unbounded-growth problem.
- Because it's plain text, GC logs are straightforward to parse programmatically (e.g., with a simple regex) to compute concrete trends like pause-duration drift over time, which can feed directly into automated monitoring and alerting.
- Legacy pre-Java-9 GC logging flags (`-XX:+PrintGCDetails` and similar) are removed on modern JDKs and will prevent the JVM from starting — audit for them specifically when upgrading a service's JDK version.
- See [GC tuning flags & ergonomics](0937-gc-tuning-flags-ergonomics.md) for how log evidence like this feeds directly into deciding which tuning flag to apply, and [Java Flight Recorder (JFR)](0942-java-flight-recorder-jfr.md) for a richer, event-correlated alternative once plain GC logs point at something worth investigating further.
