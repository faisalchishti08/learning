---
card: java
gi: 641
slug: flight-recorder-open-sourced
title: Flight Recorder open-sourced
---

## 1. What it is

**JDK Flight Recorder (JFR)** is a low-overhead, event-based profiling and diagnostics framework built into the JVM. It was originally a commercial feature of Oracle JDK (requiring a paid license), but in Java 11 (JEP 328), it was **open-sourced** and made freely available in OpenJDK builds. JFR records a detailed timeline of JVM and application events — thread scheduling, GC activity, lock contention, I/O, method profiling, exceptions — with less than 1% overhead. The recordings can be analysed in real-time via `jcmd` or written to `.jfr` files for post-hoc analysis in JDK Mission Control.

## 2. Why & when

Before JFR was open-sourced, developers using OpenJDK had to rely on external profilers (async-profiler, Java Flight Recorder in commercial Oracle JDK, or APM tools). JFR's open-sourcing democratised production-grade JVM profiling: every OpenJDK distribution now includes a built-in, low-overhead recorder that can run continuously in production. Use JFR when you need to diagnose performance issues (latency spikes, memory leaks, GC problems) in development, staging, or production — its <1% overhead means you can leave it running in production without fear. The `.jfr` file format is standardised and tool-agnostic.

## 3. Core concept

```bash
# Start a recording (via command line)
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr MyApp.java

# Start/stop via jcmd (attach to running JVM)
jcmd <pid> JFR.start duration=60s filename=recording.jfr
jcmd <pid> JFR.stop

# Dump the recording
jcmd <pid> JFR.dump filename=recording.jfr

# Analyse with JDK Mission Control:
jmc recording.jfr
```

JFR captures hundreds of event types: `jdk.GarbageCollection`, `jdk.ThreadSleep`, `jdk.FileRead`, `jdk.SocketRead`, `jdk.ExceptionThrow`, `jdk.JavaMonitorEnter` (lock contention), and many more. Events are recorded into thread-local buffers and periodically flushed to disk with minimal overhead.

## 4. Diagram

<svg viewBox="0 0 560 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JFR records JVM and application events with <1% overhead for post-hoc analysis">
  <rect x="10" y="10" width="540" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="110" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="75" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">JVM Events</text>
  <text x="75" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">GC, Threads, I/O</text>

  <text x="145" y="48" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="160" y="15" width="140" height="60" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="230" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Flight Recorder</text>
  <text x="230" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Thread-local buffers</text>
  <text x="230" y="63" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace"><1% overhead</text>

  <text x="315" y="48" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="330" y="20" width="100" height="50" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="380" y="40" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">recording.jfr</text>
  <text x="380" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">binary file</text>

  <text x="445" y="48" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="455" y="20" width="85" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="497" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">JMC / jfr</text>
  <text x="497" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">analysis tool</text>

  <text x="20" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">Open-sourced in Java 11 (JEP 328) — previously a commercial Oracle JDK feature</text>
  <text x="20" y="123" fill="#3fb950" font-size="9" font-family="sans-serif">Start: -XX:StartFlightRecording  |  jcmd <pid> JFR.start  |  jcmd <pid> JFR.dump</text>
</svg>

JFR is a continuous, low-overhead event recorder built into the JVM. Recordings are analysed in JDK Mission Control (JMC) or via the `jfr` command-line tool.

## 5. Runnable example

Scenario: demonstrating JFR recording and basic analysis — starting with enabling JFR, extending to programmatic control, and finally discussing event types and production use.

### Level 1 — Basic

```java
// File: JFRDemo.java
import java.util.*;

public class JFRDemo {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JFR Demo ===\n");
        System.out.println("PID: " + ProcessHandle.current().pid());
        System.out.println("\nTo record JFR events for this process:");
        System.out.println("  jcmd " + ProcessHandle.current().pid() + " JFR.start duration=30s filename=demo.jfr");
        System.out.println("\nOr start with JFR from command line:");
        System.out.println("  java -XX:StartFlightRecording=duration=30s,filename=demo.jfr JFRDemo.java");
        System.out.println("\nThis program will allocate objects for 30 seconds...\n");

        // Do some work to generate JFR events
        long start = System.currentTimeMillis();
        while (System.currentTimeMillis() - start < 30_000) {
            // Allocate objects (generates allocation events)
            byte[] data = new byte[1024];
            // Do some string ops
            String s = UUID.randomUUID().toString();
            s.toUpperCase();
            // Sleep a bit (generates thread sleep events)
            Thread.sleep(10);
        }

        System.out.println("Done. If JFR was recording, the file contains events from this run.");
    }
}
```

**How to run:** `java -XX:StartFlightRecording=duration=30s,filename=demo.jfr JFRDemo.java`

Expected output:
```
=== JFR Demo ===

PID: 12345

To record JFR events for this process:
  jcmd 12345 JFR.start duration=30s filename=demo.jfr

Or start with JFR from command line:
  java -XX:StartFlightRecording=duration=30s,filename=demo.jfr JFRDemo.java

This program will allocate objects for 30 seconds...

Done. If JFR was recording, the file contains events from this run.
```

### Level 2 — Intermediate

```java
// File: JFRProgrammatic.java
import jdk.jfr.*;
import java.util.*;

public class JFRProgrammatic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Programmatic JFR Control ===\n");

        // Create a recording configuration
        Recording recording = new Recording();
        recording.setName("MyAppRecording");
        recording.setDuration(java.time.Duration.ofSeconds(10));

        // Enable specific event types
        recording.enable("jdk.GarbageCollection");
        recording.enable("jdk.ThreadSleep");
        recording.enable("jdk.FileRead");
        recording.enable("jdk.ExceptionThrow");

        System.out.println("Recording started (10 seconds)...");
        recording.start();

        // Generate some events
        for (int i = 0; i < 5; i++) {
            // Allocate + GC pressure
            for (int j = 0; j < 10000; j++) {
                new Object();
            }

            // Thread sleep events
            Thread.sleep(500);

            // Throw and catch exceptions
            try {
                throw new RuntimeException("test exception " + i);
            } catch (RuntimeException e) {
                // caught — generates ExceptionThrow event
            }

            System.out.println("  Iteration " + (i + 1) + " complete");
        }

        // Stop and dump
        recording.stop();
        java.nio.file.Path file = java.nio.file.Path.of("myapp.jfr");
        recording.dump(file);
        recording.close();

        System.out.println("\nRecording saved to: " + file.toAbsolutePath());
        System.out.println("Size: " + java.nio.file.Files.size(file) + " bytes");

        // Print a summary of the recording
        System.out.println("\nEvents recorded: " + recording.getEvents().size());
        // Note: getEvents() may not work after close() in some JDK versions
    }
}
```

**How to run:** `java --add-modules jdk.jfr JFRProgrammatic.java`
(Note: on some JDK versions, the jdk.jfr module needs to be explicitly added)

Expected output:
```
=== Programmatic JFR Control ===

Recording started (10 seconds)...
  Iteration 1 complete
  ...
  Iteration 5 complete

Recording saved to: /path/to/myapp.jfr
Size: ... bytes
```

The real-world concern: programmatic JFR control via the `jdk.jfr` API. You can start/stop recordings, configure which events to capture, and dump to files — all from within your application code. This is useful for on-demand diagnostics (e.g., "start recording when latency exceeds threshold").

### Level 3 — Advanced

```java
// File: JFRAdvanced.java
import jdk.jfr.*;
import java.nio.file.*;

public class JFRAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JFR — Production Best Practices ===\n");

        // 1. Continuous recording (always-on in production)
        System.out.println("1. Continuous Recording:");
        System.out.println("   -XX:StartFlightRecording=disk=true,maxsize=250M");
        System.out.println("   (Always-on recording, circular buffer, max 250 MB disk)");
        System.out.println("   Dump on demand: jcmd <pid> JFR.dump filename=incident.jfr");
        System.out.println();

        // 2. Custom events
        System.out.println("2. Custom JFR Events:");

        // Define and commit custom events
        @Name("com.myapp.Transaction")
        @Label("Transaction Event")
        @Description("A business transaction")
        class TransactionEvent extends Event {
            @Label("Transaction ID")
            String transactionId;

            @Label("Duration")
            long durationMs;

            @Label("Success")
            boolean success;
        }

        TransactionEvent event = new TransactionEvent();
        event.transactionId = "TX-12345";
        event.durationMs = 42;
        event.success = true;
        event.commit();  // writes to JFR buffers

        System.out.println("   Custom event committed: TX-12345 (42ms, success)");
        System.out.println("   Define events with @Name, @Label, @Description annotations");
        System.out.println("   Extend jdk.jfr.Event, call commit() when ready");
        System.out.println();

        // 3. JFR event types overview
        System.out.println("3. Common JFR Event Categories:");
        System.out.println("   jdk.GarbageCollection      — GC start/end, pause times");
        System.out.println("   jdk.ThreadSleep            — Thread.sleep() calls");
        System.out.println("   jdk.ThreadPark             — LockSupport.park() calls");
        System.out.println("   jdk.JavaMonitorEnter       — synchronized block entry (contention)");
        System.out.println("   jdk.FileRead / FileWrite   — File I/O events");
        System.out.println("   jdk.SocketRead / SocketWrite — Network I/O events");
        System.out.println("   jdk.ExceptionThrow         — Exception creation");
        System.out.println("   jdk.ExecutionSample        — Method profiling samples");
        System.out.println("   jdk.NativeMemoryUsage      — Native memory tracking");
    }
}
```

**How to run:** `java --add-modules jdk.jfr JFRAdvanced.java`

Expected output:
```
=== JFR — Production Best Practices ===

1. Continuous Recording:
   -XX:StartFlightRecording=disk=true,maxsize=250M
   (Always-on recording, circular buffer, max 250 MB disk)
   Dump on demand: jcmd <pid> JFR.dump filename=incident.jfr

2. Custom JFR Events:
   Custom event committed: TX-12345 (42ms, success)
   ...

3. Common JFR Event Categories:
   ...
```

The production-flavoured hard cases: (1) **Continuous recording** — the powerful "always-on" mode uses a circular disk buffer (default 250 MB). When an incident occurs, dump the buffer for post-mortem analysis. (2) **Custom events** — extend `jdk.jfr.Event` and annotate fields to create application-specific events that integrate with JFR tooling. (3) **Event selection** — JFR captures 150+ event types; enable only what you need to minimise overhead.

## 6. Walkthrough

Tracing a JFR recording session:

1. **Start:** JVM starts with `-XX:StartFlightRecording=disk=true,maxsize=250M`. JFR initialises thread-local buffers for each Java thread and a global disk buffer (circular, 250 MB max).

2. **During execution:** The JVM continuously writes events to thread-local buffers. When a buffer fills, it's flushed to the global disk buffer. Events include GC cycles, thread scheduling, I/O operations, lock acquisitions, exceptions, and method samples (if profiling is enabled). Overhead: <1% CPU, ~10-20 MB heap for buffers.

3. **Incident occurs:** A latency spike is detected. The operator runs `jcmd <pid> JFR.dump filename=incident.jfr`. JFR flushes all buffers to disk, creating a snapshot of recent events (covering the last N minutes depending on buffer size and event rate).

4. **Analysis:** The `.jfr` file is opened in JDK Mission Control. The analyst views the timeline, identifies the latency spike, drills into thread activity, GC pauses, lock contention, and I/O events around that time, and identifies the root cause.

5. **Continuous recording continues** — the circular buffer overwrites old events, so the dump always contains the most recent data.

## 7. Gotchas & takeaways

> The `jdk.jfr` module may not be present in all JDK distributions or may require `--add-modules jdk.jfr` on some JDK versions. Most modern OpenJDK builds (17+) include it by default. Check with `java --list-modules | grep jdk.jfr`.

- JFR's overhead is **<1% for default settings** and ~2% for full method profiling. This makes it safe for always-on production use — unlike traditional profilers that can add 50-200% overhead.
- The **`.jfr` file format** is standardised and supported by tools beyond JMC: IntelliJ IDEA, async-profiler converter, and various APM platforms can ingest `.jfr` files.
- **Custom events** allow you to correlate application-level transactions with JVM-level events. Define events for your business operations and see them alongside GC and thread events in JMC.
- JFR in Java 11 is the **open-source version** of what was previously Oracle JDK's commercial feature. It has feature parity with the commercial version as of Java 11.
- **Continuous recording** with a disk buffer is the recommended production setup. It's like a black box for your JVM — when something goes wrong, you have the data to diagnose it.
