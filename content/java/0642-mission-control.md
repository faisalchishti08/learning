---
card: java
gi: 642
slug: mission-control
title: Mission Control
---

## 1. What it is

**JDK Mission Control (JMC)** is a graphical tool suite for monitoring, managing, and troubleshooting Java applications. It was open-sourced alongside JDK Flight Recorder in Java 11 (JEP 329). JMC consists of two main components: the **JMX Console** (real-time monitoring of running JVMs — CPU, memory, threads, MBeans) and the **JFR Browser** (offline analysis of `.jfr` flight recordings — timeline, event tables, automated analysis rules). JMC can connect to local or remote JVMs via JMX and can trigger flight recordings on demand. It is the primary visual analysis tool for JFR data, replacing the need for third-party profiler UIs for basic-to-intermediate diagnostics.

## 2. Why & when

Before JMC was open-sourced, developers using OpenJDK had no official GUI for JVM monitoring — they relied on `jconsole` (limited), `VisualVM` (community), or commercial APM tools. JMC's open-sourcing provided a professional-grade, free diagnostic tool that integrates seamlessly with JFR. Use JMC when you need to: visually explore a `.jfr` recording to understand a performance incident, monitor a running JVM's heap/threads/GC in real-time, trigger flight recordings on production servers, or run automated analysis rules that detect common problems (memory leaks, high GC, lock contention) automatically.

## 3. Core concept

```bash
# Start JMC (included in some JDK distributions, or download separately)
jmc &

# Open a .jfr recording file:
#   File → Open File → select recording.jfr

# Connect to a running JVM:
#   JVM must be started with JMX enabled:
java -Dcom.sun.management.jmxremote.port=7091      -Dcom.sun.management.jmxremote.authenticate=false      -Dcom.sun.management.jmxremote.ssl=false      MyApp.java
#   In JMC: File → Connect → localhost:7091
```

JMC is a standalone application (Eclipse RCP-based). It is now developed as an independent open-source project at [github.com/openjdk/jmc](https://github.com/openjdk/jmc), separate from the JDK release cycle.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK Mission Control connects to live JVMs and analyses JFR recordings">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="250" height="55" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="145" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">JMX Console</text>
  <text x="145" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Real-time monitoring: CPU, heap, threads, MBeans</text>
  <text x="145" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Connect to local or remote JVMs</text>

  <rect x="290" y="20" width="250" height="55" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="415" y="40" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">JFR Browser</text>
  <text x="415" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Offline analysis of .jfr recordings</text>
  <text x="415" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Timeline, event tables, automated rules</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Open-sourced in Java 11 (JEP 329) | Previously a commercial Oracle JDK component</text>
  <text x="20" y="118" fill="#3fb950" font-size="9" font-family="sans-serif">Now an independent open-source project: github.com/openjdk/jmc | Separate from JDK release cycle</text>
</svg>

JMC provides both real-time JVM monitoring (JMX Console) and offline flight recording analysis (JFR Browser) in a single tool.

## 5. Runnable example

Scenario: exploring JMC's capabilities programmatically and demonstrating how to prepare a JVM for JMC connection — starting with basic information, extending to JMX configuration, and finally discussing JFR analysis.

### Level 1 — Basic

```java
// File: JMCDemo.java
public class JMCDemo {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JDK Mission Control Demo ===\n");
        System.out.println("PID: " + ProcessHandle.current().pid());
        System.out.println("Java: " + System.getProperty("java.version"));
        System.out.println("Vendor: " + System.getProperty("java.vendor"));

        System.out.println("\nTo connect JMC to this JVM:");
        System.out.println("  1. Start JMC: jmc &");
        System.out.println("  2. The JVM should appear in the JVM Browser");
        System.out.println("  3. Right-click → Start JMX Console");
        System.out.println("  4. Or: right-click → Start Flight Recording");

        System.out.println("\nFor remote JVM connections, start with:");
        System.out.println("  java -Dcom.sun.management.jmxremote.port=7091 \\");
        System.out.println("       -Dcom.sun.management.jmxremote.authenticate=false \\");
        System.out.println("       -Dcom.sun.management.jmxremote.ssl=false \\");
        System.out.println("       JMCDemo.java");

        System.out.println("\nThen in JMC: File → Connect → localhost:7091");

        // Keep JVM alive for you to explore with JMC
        System.out.println("\nKeeping JVM alive for 60 seconds for JMC exploration...");
        System.out.println("Press Ctrl+C to stop earlier.\n");

        for (int i = 60; i > 0; i--) {
            // Do some work to generate interesting metrics
            byte[] mem = new byte[1024 * 100];  // allocate
            Thread.sleep(1000);
            System.out.print("\rTime remaining: " + i + "s  ");
        }
        System.out.println("\nDone.");
    }
}
```

**How to run:** `java JMCDemo.java`

Expected output:
```
=== JDK Mission Control Demo ===

PID: 12345
Java: 17.0...
Vendor: ...

To connect JMC to this JVM:
  1. Start JMC: jmc &
  2. The JVM should appear in the JVM Browser
  ...

Keeping JVM alive for 60 seconds for JMC exploration...
```

### Level 2 — Intermediate

```java
// File: JMCMetrics.java
import java.lang.management.*;
import javax.management.*;
import java.util.*;

public class JMCMetrics {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JVM Metrics (visible in JMC JMX Console) ===\n");

        // These are the metrics JMC displays in its JMX Console

        // 1. Memory
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        MemoryUsage heap = memory.getHeapMemoryUsage();
        System.out.println("Heap Memory:");
        System.out.printf("  Used:      %,d bytes%n", heap.getUsed());
        System.out.printf("  Committed: %,d bytes%n", heap.getCommitted());
        System.out.printf("  Max:       %,d bytes%n", heap.getMax());

        // 2. Threads
        ThreadMXBean threads = ManagementFactory.getThreadMXBean();
        System.out.println("\nThreads:");
        System.out.println("  Live:        " + threads.getThreadCount());
        System.out.println("  Peak:        " + threads.getPeakThreadCount());
        System.out.println("  Daemon:      " + threads.getDaemonThreadCount());
        System.out.println("  TotalStarted:" + threads.getTotalStartedThreadCount());

        // 3. GC
        System.out.println("\nGarbage Collectors:");
        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.printf("  %-25s collections: %,d, time: %,d ms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime());
        }

        // 4. Operating System
        OperatingSystemMXBean os = ManagementFactory.getOperatingSystemMXBean();
        System.out.println("\nOS:");
        System.out.println("  CPU Cores:   " + os.getAvailableProcessors());
        System.out.println("  System Load: " + String.format("%.2f", os.getSystemLoadAverage()));
        System.out.println("  Arch:        " + os.getArch());

        // 5. Runtime
        RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
        System.out.println("\nRuntime:");
        System.out.println("  Uptime:      " + runtime.getUptime() + " ms");
        System.out.println("  VM Name:     " + runtime.getVmName());
        System.out.println("  Classpath:   " +
            (runtime.getClassPath().length() > 80 ?
             runtime.getClassPath().substring(0, 80) + "..." :
             runtime.getClassPath()));
    }
}
```

**How to run:** `java JMCMetrics.java`

Expected output:
```
=== JVM Metrics (visible in JMC JMX Console) ===

Heap Memory:
  Used:      ... bytes
  Committed: ... bytes
  Max:       ... bytes

Threads:
  Live:        ...
  Peak:        ...
  ...

Garbage Collectors:
  ...

OS:
  CPU Cores:   ...
  System Load: ...
  Arch:        ...

Runtime:
  Uptime:      ... ms
  VM Name:     ...
```

The real-world concern: understanding what JMC monitors. All these metrics are available via JMX MBeans (`java.lang:type=Memory`, `java.lang:type=Threading`, etc.) and are what JMC's JMX Console visualises in graphs, charts, and tables.

### Level 3 — Advanced

```java
// File: JMCAdvanced.java
import java.lang.management.*;

public class JMCAdvanced {
    public static void main(String[] args) {
        System.out.println("=== JMC — Advanced Capabilities ===\n");

        System.out.println("1. Automated Analysis Rules:");
        System.out.println("   JMC includes built-in rules that analyse .jfr recordings:");
        System.out.println("   - High GC pause time detection");
        System.out.println("   - Memory leak detection (growing old gen after GC)");
        System.out.println("   - Lock contention hotspots");
        System.out.println("   - High CPU usage by specific threads");
        System.out.println("   - I/O bottleneck identification");
        System.out.println("   Results appear as a report with severity (info/warning/error).");
        System.out.println();

        System.out.println("2. JFR Browser Features:");
        System.out.println("   - Timeline: zoomable, shows all events over time");
        System.out.println("   - Event Browser: table view, filterable, searchable");
        System.out.println("   - Thread view: per-thread activity timeline");
        System.out.println("   - GC view: pause times, phases, heap before/after");
        System.out.println("   - Lock Instances: which monitors are contended");
        System.out.println("   - Socket I/O: network read/write times");
        System.out.println();

        System.out.println("3. Production Workflow:");
        System.out.println("   a) Deploy JVM with: -XX:StartFlightRecording=disk=true");
        System.out.println("   b) Incident occurs → jcmd <pid> JFR.dump filename=incident.jfr");
        System.out.println("   c) Open incident.jfr in JMC");
        System.out.println("   d) Run 'Automated Analysis' for quick diagnosis");
        System.out.println("   e) Drill into timeline/events for root cause");
        System.out.println("   f) Export findings as HTML report for the team");
        System.out.println();

        System.out.println("4. JMC vs Alternatives:");
        System.out.printf("%-20s %-20s %-25s%n", "Tool", "Real-time", "JFR Analysis");
        System.out.println("-".repeat(65));
        System.out.printf("%-20s %-20s %-25s%n", "JMC", "Yes (JMX)", "Yes (full)");
        System.out.printf("%-20s %-20s %-25s%n", "VisualVM", "Yes", "Basic");
        System.out.printf("%-20s %-20s %-25s%n", "jconsole", "Yes (basic)", "No");
        System.out.printf("%-20s %-20s %-25s%n", "IntelliJ Profiler", "Yes", "Yes");
        System.out.printf("%-20s %-20s %-25s%n", "async-profiler", "No", "Export only");

        System.out.println("\n5. Obtaining JMC:");
        System.out.println("   - Some JDK distributions include JMC (Azul, Oracle)");
        System.out.println("   - Download from: https://adoptium.net/jmc/");
        System.out.println("   - Or build from source: github.com/openjdk/jmc");
        System.out.println("   - JMC is now independent of JDK releases —");
        System.out.println("     new JMC versions ship separately from new JDK versions");
    }
}
```

**How to run:** `java JMCAdvanced.java`

Expected output:
```
=== JMC — Advanced Capabilities ===

1. Automated Analysis Rules:
   ...

2. JFR Browser Features:
   ...

3. Production Workflow:
   ...

4. JMC vs Alternatives:
   ...

5. Obtaining JMC:
   ...
```

The production-flavoured hard cases: (1) **Automated analysis** — JMC's most powerful feature: one click to scan a `.jfr` file for known problems (memory leaks, lock contention, high GC). (2) **Remote connections** — connect JMC to production JVMs by enabling JMX with authentication and SSL (never disable auth in production!). (3) **JMC is now independent** — it ships separately from the JDK since Java 11. Download from Adoptium or build from the openjdk/jmc GitHub repository.

## 6. Walkthrough

Tracing a typical JMC diagnostic workflow:

1. **Deploy:** The application is deployed with `-XX:StartFlightRecording=disk=true,maxsize=500M`. JFR records continuously to a 500 MB circular disk buffer.

2. **Incident:** Users report a 5-second latency spike at 14:32. The operator runs: `jcmd 12345 JFR.dump filename=incident-1432.jfr`. The last ~30 minutes of JVM events are flushed to disk.

3. **Open in JMC:** `jmc &`, File → Open File → `incident-1432.jfr`. The JFR Browser opens.

4. **Automated Analysis:** Click "Automated Analysis Results." JMC runs 50+ rules and produces a report: "Warning: GC pause time exceeded 1 second at 14:31:58." "Information: Old generation occupancy grew from 40% to 95% between 14:25 and 14:32."

5. **Drill down:** Navigate to the timeline at 14:31:58. The GC view shows a full GC pause of 4.8 seconds. Switch to the memory view: old gen was filling steadily. Check thread activity: a background batch job was processing a 500 MB data file, allocating heavily.

6. **Root cause identified:** The batch job's memory usage wasn't bounded. Fix: add streaming/batching to limit memory. Export JMC report as HTML to share with the team.

## 7. Gotchas & takeaways

> JMC is **not included in all JDK distributions** — notably, it's absent from many standard OpenJDK builds. You may need to download it separately from [adoptium.net/jmc](https://adoptium.net/jmc/) or your JDK vendor's site. It is a separate download from the JDK.

- JMC is now an **independent open-source project** (github.com/openjdk/jmc) with its own release cycle. It supports JDK 8+ and works with `.jfr` files from JDK 8 through the latest versions.
- The **JMX Console** requires JMX to be enabled on the target JVM (enabled by default for local connections; needs configuration for remote). For production, always use JMX authentication and SSL.
- JMC's **automated analysis rules** are extensible — you can write custom rules in Java that run against `.jfr` files to detect application-specific problems.
- JMC is an **Eclipse RCP application** and requires a graphical environment. For headless/CLI analysis, use `jfr` command-line tool: `jfr summary recording.jfr` or `jfr print --events GC recording.jfr`.
- JMC replaced **Java VisualVM** as the recommended diagnostic tool. VisualVM is still available but JMC provides deeper JFR integration and more sophisticated analysis.
