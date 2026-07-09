---
card: java
gi: 661
slug: dynamic-cds-archives
title: Dynamic CDS archives
---

## 1. What it is

**Dynamic CDS Archives**, added in **Java 13** (JEP 350), extend Class-Data Sharing (CDS — introduced in earlier Java versions to speed up JVM startup by pre-parsing and memory-mapping core class metadata) with the ability to create a CDS archive **automatically at application exit**, capturing whatever classes were actually loaded during that run — including your application's own classes and library classes, not just JDK classes. Before this, creating a CDS archive (AppCDS) required a separate, manual step: run your app once with `-XX:+RecordDynamicDumpInfo` tracing enabled to produce a class list, then run a second dedicated dump step to build the archive from that list — a multi-command workflow most developers never bothered with. Dynamic CDS collapses this into one command: `-XX:ArchiveClassesAtExit=<path>.jsa` runs your program normally and, when it exits, writes out an archive of the classes loaded during that run, ready to be reused on the next startup with `-XX:SharedArchiveFile=<path>.jsa`.

## 2. Why & when

JVM startup time is dominated in part by class loading and verification — parsing `.class` files, verifying bytecode, and building in-memory metadata for every class the running program touches. CDS avoids repeating this work by memory-mapping a pre-built archive of class metadata, but pre-Java-13 AppCDS required developers to hand-build a class list and run a separate archiving step, which was enough friction that many projects never adopted it despite the startup-time win. Dynamic CDS makes archive creation a one-line addition to how you already run your app: exercise your application's normal startup path once with `-XX:ArchiveClassesAtExit`, and the archive captures the real classes your app actually loads — application classes and third-party library classes included, not just `java.*` classes. This is most valuable for short-lived JVM processes where startup time is a significant fraction of total runtime — CLI tools, serverless/FaaS functions, and containers that restart frequently — where shaving tens to hundreds of milliseconds off startup meaningfully improves the experience.

## 3. Core concept

```bash
# Step 1 (one time): run your app normally, but tell the JVM to dump
# a CDS archive of whatever classes get loaded, when the app exits.
java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar com.example.Main

# Step 2 (every subsequent run): reuse that archive to skip re-parsing
# all those classes from scratch.
java -XX:SharedArchiveFile=app.jsa -cp app.jar com.example.Main
```

Compare this to the older, multi-step AppCDS workflow it simplifies:
```bash
# Old AppCDS: 3 separate steps
java -XX:DumpLoadedClassList=classes.lst -cp app.jar com.example.Main
java -Xshare:dump -XX:SharedClassListFile=classes.lst -XX:SharedArchiveFile=app-static.jsa -cp app.jar
java -XX:SharedArchiveFile=app-static.jsa -cp app.jar com.example.Main
```

Dynamic CDS reduces the "capture a class list, then dump" two-step into a single run that produces the archive as a side effect of exiting.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="First run with ArchiveClassesAtExit records loaded classes into a jsa file at exit; subsequent runs with SharedArchiveFile memory-map that archive to skip class parsing">
  <rect x="10" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Run 1 (one-time capture)</text>
  <text x="25" y="65" fill="#e6edf3" font-size="9" font-family="monospace">java -XX:ArchiveClassesAtExit=app.jsa</text>
  <text x="25" y="80" fill="#8b949e" font-size="9" font-family="sans-serif">App runs normally → exits → app.jsa written</text>

  <line x1="150" y1="100" x2="150" y2="130" stroke="#8b949e" stroke-width="2" marker-end="url(#cd1)"/>
  <rect x="30" y="130" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">app.jsa (classes from run 1)</text>

  <rect x="330" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Run 2+ (reuse archive)</text>
  <text x="345" y="65" fill="#e6edf3" font-size="9" font-family="monospace">java -XX:SharedArchiveFile=app.jsa</text>
  <text x="345" y="90" fill="#8b949e" font-size="9" font-family="sans-serif">JVM memory-maps app.jsa instead</text>
  <text x="345" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">of parsing+verifying each class</text>
  <text x="345" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">from .class files individually.</text>
  <text x="345" y="145" fill="#79c0ff" font-size="9" font-family="sans-serif">Result: faster JVM startup.</text>

  <line x1="270" y1="145" x2="330" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#cd2)"/>

  <defs>
    <marker id="cd1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="cd2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

A single "training" run captures the archive; every subsequent run of the same application reuses it to skip repeated class-parsing work at startup.

## 5. Runnable example

Scenario: measuring startup-time improvement for a small program that loads a moderate number of classes — first running without CDS as a baseline, then building and using a dynamic CDS archive, then a more thorough before/after comparison script that runs each configuration several times and reports averages.

### Level 1 — Basic

```java
// File: StartupApp.java
import java.util.*;
import java.util.stream.*;

public class StartupApp {
    public static void main(String[] args) {
        // Touch a reasonably varied set of JDK classes to give CDS something to capture.
        List<String> data = new ArrayList<>();
        for (int i = 0; i < 1000; i++) data.add("item-" + i);
        Map<Boolean, List<String>> partitioned = data.stream()
            .collect(Collectors.partitioningBy(s -> s.length() > 6));
        Optional<String> longest = data.stream().max(Comparator.comparingInt(String::length));
        System.out.println("Partitioned sizes: " + partitioned.get(true).size()
            + " / " + partitioned.get(false).size());
        System.out.println("Longest: " + longest.orElse("none"));
    }
}
```

**How to run (baseline, no CDS):**
```
javac StartupApp.java
time java StartupApp
```

Expected output (timing varies by machine; the point is the wall-clock time reported by `time`):
```
Partitioned sizes: 1000 / 0
Longest: item-999

real    0m0.128s
```

### Level 2 — Intermediate

**How to build and use a dynamic CDS archive for this same program:**
```
# One-time: run normally, capture an archive of classes loaded at exit.
java -XX:ArchiveClassesAtExit=startup-app.jsa StartupApp

# Subsequent runs: reuse the archive.
time java -XX:SharedArchiveFile=startup-app.jsa StartupApp
```

Expected output:
```
Partitioned sizes: 1000 / 0
Longest: item-999

real    0m0.089s
```

The program's output is identical — dynamic CDS is purely a startup-performance optimization and never changes program behavior — but the reported wall-clock time is lower on the second command, since the JVM memory-maps pre-parsed class metadata from `startup-app.jsa` instead of parsing and verifying each class from scratch. (Absolute numbers vary significantly by machine and JDK version; the *relative* improvement is the meaningful signal, and it's often more pronounced for larger applications with many classes.)

### Level 3 — Advanced

```java
// File: BenchmarkRunner.java (drives the comparison as an external process launcher)
import java.io.*;
import java.util.*;

public class BenchmarkRunner {
    public static void main(String[] args) throws Exception {
        String javaBin = System.getProperty("java.home") + File.separator + "bin" + File.separator + "java";

        System.out.println("Building dynamic CDS archive...");
        runAndWait(javaBin, "-XX:ArchiveClassesAtExit=bench.jsa", "-cp", ".", "StartupApp");

        List<Long> baseline = new ArrayList<>();
        List<Long> withCds = new ArrayList<>();

        for (int i = 0; i < 3; i++) {
            baseline.add(timeRun(javaBin, "-cp", ".", "StartupApp"));
            withCds.add(timeRun(javaBin, "-XX:SharedArchiveFile=bench.jsa", "-cp", ".", "StartupApp"));
        }

        System.out.println("Baseline runs (ms): " + baseline);
        System.out.println("With CDS runs (ms): " + withCds);
        System.out.printf("Average baseline: %.1f ms%n", average(baseline));
        System.out.printf("Average with CDS: %.1f ms%n", average(withCds));
    }

    static long timeRun(String... command) throws Exception {
        long start = System.nanoTime();
        runAndWait(command);
        return (System.nanoTime() - start) / 1_000_000;
    }

    static void runAndWait(String... command) throws Exception {
        Process p = new ProcessBuilder(command).redirectOutput(ProcessBuilder.Redirect.DISCARD)
            .redirectErrorStream(true).start();
        p.waitFor();
    }

    static double average(List<Long> values) {
        return values.stream().mapToLong(Long::longValue).average().orElse(0);
    }
}
```

**How to run:** `javac StartupApp.java BenchmarkRunner.java && java BenchmarkRunner`

Expected output (illustrative — actual milliseconds depend heavily on hardware and JDK build):
```
Building dynamic CDS archive...
Baseline runs (ms): [131, 126, 129]
Average baseline: 128.7 ms
With CDS runs (ms): [92, 88, 90]
Average with CDS: 90.0 ms
```

Level 3 automates the whole comparison: it first builds `bench.jsa` by launching `StartupApp` once with `-XX:ArchiveClassesAtExit`, then launches `StartupApp` 3 times each with and without `-XX:SharedArchiveFile`, timing each external process launch to produce an averaged, repeatable before/after comparison rather than a single noisy sample.

## 6. Walkthrough

1. `BenchmarkRunner.main` first calls `runAndWait` with `-XX:ArchiveClassesAtExit=bench.jsa`, which launches a **child JVM process** running `StartupApp`. That child process executes `StartupApp.main` normally — building its `List`, partitioning it, finding the longest string, printing results — with no behavior difference at all from a plain run.
2. As that child JVM loads classes to execute `StartupApp` (`ArrayList`, `Collectors`, `Stream`, `Optional`, `Comparator`, and `StartupApp` itself, among others), the JVM's dynamic-CDS machinery tracks which classes were actually loaded during this run.
3. When the child process's `main` method returns and the JVM begins its normal shutdown sequence, the `-XX:ArchiveClassesAtExit` flag causes the JVM to write out `bench.jsa` — a memory-mappable archive containing pre-parsed, pre-verified metadata for every class that run touched — as its very last action before the process exits.
4. Back in the parent `BenchmarkRunner`, the loop begins: `timeRun` records `System.nanoTime()`, launches a fresh child JVM running plain `StartupApp` (no CDS flags), waits for it to exit via `p.waitFor()`, and computes elapsed milliseconds. This "baseline" child JVM parses and verifies every needed class from its `.class` files on disk, the traditional way.
5. Immediately after, `timeRun` launches another child JVM, this time with `-XX:SharedArchiveFile=bench.jsa`. This JVM, during its own startup, memory-maps `bench.jsa` and finds most of the classes it needs already present in pre-parsed form in that archive — it can skip the parse/verify work for those classes entirely, only doing traditional class loading for anything not captured in the archive.
6. This baseline/with-CDS pair repeats 3 times total, appending each timing to the `baseline` and `withCds` lists respectively.
7. After all 6 child-process launches finish, `average(...)` computes the mean of each list, and the final `printf` calls report both averages side by side — the difference between them is the CDS-driven startup-time improvement, made more reliable by averaging across multiple runs rather than trusting a single potentially-noisy measurement.

```
parent BenchmarkRunner
  ├─ launch child JVM (ArchiveClassesAtExit) ──► runs StartupApp ──► writes bench.jsa at exit
  ├─ 3×: launch child JVM (no CDS)         ──► time each ──► baseline[]
  └─ 3×: launch child JVM (SharedArchiveFile) ──► time each ──► withCds[]
         └─ memory-maps bench.jsa, skips re-parsing archived classes
```

## 7. Gotchas & takeaways

> A dynamic CDS archive captures the classes loaded **during that specific run** — if a later run takes a different code path that loads additional classes not in the archive (e.g. an error-handling branch, a rarely-used feature flag), those extra classes simply load the traditional way; the archive doesn't cause failures for classes it doesn't contain, it just doesn't speed those specific classes up. Re-generate the archive periodically (especially after significant code or dependency changes) so it stays representative of your application's real class usage.

- `-XX:ArchiveClassesAtExit=<file>.jsa` captures whatever classes were loaded by that specific run, including application and library classes, not just JDK classes.
- `-XX:SharedArchiveFile=<file>.jsa` on a later run reuses that archive to skip re-parsing/re-verifying the classes it contains.
- This collapses the older multi-step AppCDS workflow (`DumpLoadedClassList` + `-Xshare:dump`) into a single "run once, capture automatically at exit" step.
- Most valuable for short-lived JVM processes (CLI tools, serverless functions, frequently-restarted containers) where startup time is a meaningful fraction of total execution time.
- The archive is a startup-performance optimization only — it never changes program behavior or output, so it's safe to add to deployment scripts without behavioral risk (though you should still validate the performance improvement with real measurements on your target hardware, as shown in Level 3).
