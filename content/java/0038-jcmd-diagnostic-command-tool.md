---
card: java
gi: 38
slug: jcmd-diagnostic-command-tool
title: jcmd — diagnostic command tool
---

## 1. What it is

**`jcmd`** is a JDK command-line tool for sending diagnostic commands to a running JVM process. It can trigger heap dumps, thread dumps, GC cycles, flight-recorder snapshots, and dozens of JVM diagnostic queries — all without restarting the process.

```bash
jcmd <pid> <command>       # send command to a specific JVM process
jcmd <pid> help            # list all commands that process supports
jcmd                       # list all running JVM processes (like jps)
```

`jcmd` is the modern, unified replacement for the older `jstack`, `jmap`, and `jinfo` tools. Everything those tools do, `jcmd` can do via named sub-commands.

## 2. Why & when

`jcmd` is the right tool for:
- **Live production diagnostics** without a restart: heap dump, thread dump, GC stats.
- **Triggering JFR (Java Flight Recorder)** recordings on a running process.
- **Querying JVM flags** that are currently active (`VM.flags`).
- **Printing system properties** (`VM.system_properties`) without a code change.
- **Force a GC cycle** (`GC.run`) on a running app to test GC behaviour.

Use `jcmd` when you need to inspect a live process non-destructively. For automated monitoring use `jstat`; for heap analysis use `jmap --heap` or the `jcmd GC.heap_info` sub-command.

## 3. Core concept

```bash
# List running JVMs
jcmd

# Discover what a PID supports
jcmd <pid> help

# Common commands
jcmd <pid> VM.flags                    # print active JVM flags
jcmd <pid> VM.system_properties        # print System.getProperties()
jcmd <pid> VM.version                  # JVM version info
jcmd <pid> VM.command_line             # original java command line
jcmd <pid> VM.uptime                   # how long process has been running

jcmd <pid> Thread.print                # thread dump (like jstack)
jcmd <pid> GC.run                      # trigger a full GC
jcmd <pid> GC.heap_info                # heap usage summary
jcmd <pid> GC.heap_dump filename=/tmp/heap.hprof   # heap dump (like jmap)
jcmd <pid> GC.class_stats              # per-class object counts

# Java Flight Recorder
jcmd <pid> JFR.start name=myRec duration=60s filename=/tmp/rec.jfr
jcmd <pid> JFR.stop  name=myRec
jcmd <pid> JFR.dump  name=myRec filename=/tmp/rec.jfr

# Native memory tracking
jcmd <pid> VM.native_memory summary
```

`jcmd` talks to the JVM via the `attach` mechanism — a Unix-domain socket created by the JVM in `/tmp/` (or a named pipe on Windows). No network port needed; same-machine only.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jcmd sends commands to a running JVM via the attach mechanism">
  <rect x="8" y="8" width="664" height="184" rx="8" fill="#0d1117"/>

  <!-- Developer / terminal -->
  <rect x="20" y="60" width="130" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Terminal</text>
  <text x="30" y="100" fill="#6db33f" font-size="9" font-family="monospace">jcmd 1234</text>
  <text x="30" y="113" fill="#6db33f" font-size="9" font-family="monospace">  GC.heap_dump</text>
  <text x="30" y="126" fill="#6db33f" font-size="9" font-family="monospace">  filename=h.hprof</text>

  <!-- Attach socket -->
  <rect x="200" y="80" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="97" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">attach API</text>
  <text x="260" y="111" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">/tmp/.java_pid1234</text>

  <!-- Running JVM -->
  <rect x="375" y="30" width="270" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Running JVM (pid 1234)</text>
  <text x="395" y="72"  fill="#e6edf3" font-size="9" font-family="sans-serif">Diagnostic Commands Listener</text>
  <text x="395" y="90"  fill="#8b949e" font-size="9" font-family="monospace">VM.flags → prints -Xmx...</text>
  <text x="395" y="104" fill="#8b949e" font-size="9" font-family="monospace">Thread.print → dumps all threads</text>
  <text x="395" y="118" fill="#8b949e" font-size="9" font-family="monospace">GC.heap_dump → writes .hprof</text>
  <text x="395" y="132" fill="#8b949e" font-size="9" font-family="monospace">JFR.start → begins recording</text>
  <text x="395" y="146" fill="#8b949e" font-size="9" font-family="monospace">GC.run → triggers full GC</text>

  <!-- arrows -->
  <line x1="150" y1="100" x2="196" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jc1)"/>
  <line x1="320" y1="100" x2="371" y2="80"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jc2)"/>

  <defs>
    <marker id="jc1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="jc2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jcmd` communicates with the target JVM over a local socket created by the JVM's attach mechanism — no network port, no restart required.

## 5. Runnable example

Scenario: launch a long-running JVM process, use `jcmd` to discover it, query its state, take a heap dump, and examine flight-recorder capability — from zero to production-grade diagnostics.

### Level 1 — Basic

```java
// JcmdBasic.java — demonstrates jcmd from within the current JVM
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JcmdBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jcmd diagnostic demo ===\n");

        // Show our own PID (what you'd pass to jcmd)
        long pid = ProcessHandle.current().pid();
        System.out.println("This JVM's PID: " + pid);
        System.out.println("Run in another terminal: jcmd " + pid + " help");

        // Locate jcmd
        Path jcmd = findTool("jcmd");
        System.out.println("jcmd found: " + (jcmd != null ? jcmd : "NOT FOUND — needs JDK"));

        // Simulate what jcmd would report using JMX beans
        System.out.println("\n--- VM.version equivalent (ManagementFactory) ---");
        System.out.println("JVM: " + ManagementFactory.getRuntimeMXBean().getVmName());
        System.out.println("Version: " + ManagementFactory.getRuntimeMXBean().getVmVersion());
        System.out.println("Uptime: " + ManagementFactory.getRuntimeMXBean().getUptime() + " ms");

        System.out.println("\n--- GC.heap_info equivalent ---");
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            MemoryUsage u = pool.getUsage();
            if (u.getMax() > 0)
                System.out.printf("  %-30s used=%d KB max=%d KB%n",
                    pool.getName(), u.getUsed()/1024, u.getMax()/1024);
        }

        System.out.println("\n--- Key jcmd commands ---");
        String[][] cmds = {
            {"jcmd", "list all running JVMs"},
            {"jcmd <pid> help", "list commands for that process"},
            {"jcmd <pid> VM.flags", "print active JVM flags"},
            {"jcmd <pid> Thread.print", "thread dump"},
            {"jcmd <pid> GC.heap_info", "heap usage summary"},
            {"jcmd <pid> GC.heap_dump filename=/tmp/h.hprof", "write heap dump"},
            {"jcmd <pid> JFR.start duration=60s filename=/tmp/r.jfr", "JFR recording"},
        };
        for (var c : cmds) System.out.printf("  %-50s → %s%n", c[0], c[1]);
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JcmdBasic.java`

The program shows its own PID and demonstrates what `jcmd` sub-commands report. Open a second terminal and run `jcmd <pid> help` while the program is running (add a `Thread.sleep` if needed) to see all supported commands.

### Level 2 — Intermediate

Same scenario extended: launch a child JVM process, run `jcmd` against it while it's alive, capture the output of `VM.flags`, `GC.heap_info`, and `Thread.print`.

```java
// JcmdLive.java — launch a child JVM, run jcmd commands against it
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JcmdLive {

    // A simple long-running app to inspect
    static final String TARGET =
        "public class LongRunner {\n" +
        "    public static void main(String[] a) throws Exception {\n" +
        "        System.out.println(\"LongRunner ready pid=\" + ProcessHandle.current().pid());\n" +
        "        System.out.flush();\n" +
        "        Thread.sleep(30_000);\n" +  // wait 30 seconds
        "    }\n}\n";

    public static void main(String[] args) throws Exception {
        Path jcmd    = findTool("jcmd");
        Path java    = findTool("java");
        Path javac   = findTool("javac");
        if (jcmd == null || java == null || javac == null) {
            System.err.println("Full JDK required"); return;
        }

        Path work = Files.createTempDirectory("jcmd-demo");
        Path src  = work.resolve("LongRunner.java");
        Files.writeString(src, TARGET);

        // Compile
        new ProcessBuilder(javac.toString(), src.toString()).inheritIO().start().waitFor();

        // Launch LongRunner as a background process
        System.out.println("Launching LongRunner...");
        Process child = new ProcessBuilder(java.toString(), "-cp", work.toString(), "LongRunner")
            .redirectErrorStream(true).start();

        // Read PID from its stdout
        String line = new BufferedReader(new InputStreamReader(child.getInputStream())).readLine();
        System.out.println("Child: " + line);

        // Parse PID
        long childPid = child.pid();
        System.out.println("PID: " + childPid);

        Thread.sleep(500); // give JVM time to initialise

        // Run jcmd commands
        String[] commands = {"VM.flags", "GC.heap_info", "Thread.print"};
        for (String cmd : commands) {
            System.out.println("\n=== jcmd " + childPid + " " + cmd + " ===");
            Process jcmdP = new ProcessBuilder(jcmd.toString(), String.valueOf(childPid), cmd)
                .redirectErrorStream(true).start();
            String output = new String(jcmdP.getInputStream().readAllBytes());
            jcmdP.waitFor();
            // Print first 20 lines to keep output manageable
            output.lines().limit(20).forEach(l -> System.out.println("  " + l));
        }

        // Heap dump
        Path hprof = work.resolve("heap.hprof");
        System.out.println("\n=== jcmd " + childPid + " GC.heap_dump ===");
        Process dumpP = new ProcessBuilder(jcmd.toString(), String.valueOf(childPid),
            "GC.heap_dump", "filename=" + hprof).redirectErrorStream(true).start();
        System.out.println(new String(dumpP.getInputStream().readAllBytes()).strip());
        dumpP.waitFor();
        if (Files.exists(hprof))
            System.out.printf("Heap dump written: %d KB%n", Files.size(hprof) / 1024);

        child.destroyForcibly();
        Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nDone.");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JcmdLive.java`

Launches a real child JVM process, waits for it to be ready, then fires `VM.flags`, `GC.heap_info`, `Thread.print`, and `GC.heap_dump` against it via `jcmd`. You see the exact output `jcmd` produces for each command.

### Level 3 — Advanced

Same scenario with JFR (Java Flight Recorder) — start a recording, run workload, stop and read event count from the `.jfr` file header.

```java
// JcmdJFR.java — launch child JVM, run JFR recording via jcmd, inspect result
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JcmdJFR {

    static final String TARGET =
        "import java.util.*;\n" +
        "public class WorkloadApp {\n" +
        "    public static void main(String[] a) throws Exception {\n" +
        "        System.out.println(\"ready\");\n" +
        "        System.out.flush();\n" +
        "        Random rng = new Random();\n" +
        "        long sum = 0;\n" +
        "        for (int i = 0; i < 20_000_000; i++) sum += rng.nextInt(100);\n" +
        "        System.out.println(\"workload done sum=\" + sum);\n" +
        "        Thread.sleep(5_000);\n" +
        "    }\n}\n";

    public static void main(String[] args) throws Exception {
        Path jcmd  = findTool("jcmd");
        Path java  = findTool("java");
        Path javac = findTool("javac");
        if (jcmd == null || java == null || javac == null) {
            System.err.println("Full JDK required"); return;
        }

        Path work  = Files.createTempDirectory("jcmd-jfr");
        Path src   = work.resolve("WorkloadApp.java");
        Path jfrFile = work.resolve("workload.jfr");
        Files.writeString(src, TARGET);
        new ProcessBuilder(javac.toString(), src.toString()).inheritIO().start().waitFor();

        // Launch with -XX:+FlightRecorder enabled
        System.out.println("Launching WorkloadApp...");
        Process child = new ProcessBuilder(java.toString(),
            "-XX:+UnlockDiagnosticVMOptions",
            "-cp", work.toString(), "WorkloadApp")
            .redirectErrorStream(true).start();

        BufferedReader br = new BufferedReader(new InputStreamReader(child.getInputStream()));
        br.readLine(); // consume "ready"
        long pid = child.pid();
        System.out.println("WorkloadApp PID: " + pid);

        Thread.sleep(500);

        // Start JFR recording
        System.out.println("\n[ JFR.start ]");
        Process startP = new ProcessBuilder(jcmd.toString(), String.valueOf(pid),
            "JFR.start", "name=myRec", "settings=default")
            .redirectErrorStream(true).start();
        System.out.println(new String(startP.getInputStream().readAllBytes()).strip());
        startP.waitFor();

        // Let the workload run
        Thread.sleep(2000);

        // Stop and dump
        System.out.println("\n[ JFR.dump ]");
        Process dumpP = new ProcessBuilder(jcmd.toString(), String.valueOf(pid),
            "JFR.dump", "name=myRec", "filename=" + jfrFile)
            .redirectErrorStream(true).start();
        System.out.println(new String(dumpP.getInputStream().readAllBytes()).strip());
        dumpP.waitFor();

        System.out.println("\n[ JFR.stop ]");
        Process stopP = new ProcessBuilder(jcmd.toString(), String.valueOf(pid),
            "JFR.stop", "name=myRec")
            .redirectErrorStream(true).start();
        System.out.println(new String(stopP.getInputStream().readAllBytes()).strip());
        stopP.waitFor();

        if (Files.exists(jfrFile)) {
            long kb = Files.size(jfrFile) / 1024;
            System.out.printf("%nJFR file: %s (%d KB)%n", jfrFile, kb);
            System.out.println("Open with: jfr print --events CPULoad,GarbageCollection " + jfrFile);
            System.out.println("Or import into JDK Mission Control (jmc) for visual analysis.");
        } else {
            System.out.println("JFR file not created (process may have ended early).");
        }

        // Check VM.native_memory
        System.out.println("\n[ VM.native_memory — requires -XX:NativeMemoryTracking=summary ]");
        System.out.println("  (not enabled in this demo — add -XX:NativeMemoryTracking=summary to JVM flags)");
        System.out.println("  jcmd <pid> VM.native_memory summary");

        child.destroyForcibly();
        Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nDone. Cleaned up.");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JcmdJFR.java`

`JFR.start` begins a low-overhead recording (~1% CPU overhead with default settings). `JFR.dump` writes the `.jfr` binary while the process is still running. Inspect the file with `jfr print` (CLI) or JDK Mission Control.

## 6. Walkthrough

Execution trace in `JcmdLive.main`, showing how state flows from terminal command to JVM response:

**Launch the target.** A child `java` process starts `LongRunner`. The JVM creates an attach socket at `/tmp/.java_pid<PID>` during startup (controlled by `-XX:+EnableDynamicAgentLoading`, on by default).

**`jcmd <PID> VM.flags`** → `jcmd` connects to the attach socket, sends `"VM.flags"` as a string, and the JVM's diagnostic listener handles it by iterating all active `JVMFlag` entries and returning them as text. Output looks like `-XX:CICompilerCount=4 -XX:InitialHeapSize=... -Xmx...`.

**`jcmd <PID> GC.heap_info`** → the JVM queries each memory pool and returns a summary like:
```
 garbage-first heap   total 65536K, used 4096K [0x..., , 0x...]
  region size 1024K, 4 young (4096K), 0 survivors (0K)
 Metaspace       used 8888K, committed 9088K, reserved 1056768K
```

**`jcmd <PID> Thread.print`** → the JVM calls `Thread.getAllStackTraces()` internally, formats each thread's stack (similar to `jstack`), and sends the string to `jcmd`'s stdout.

**`GC.heap_dump filename=/tmp/heap.hprof`** → the JVM triggers a safe-point, pauses all threads briefly, and writes a binary `.hprof` file to disk. This file can be opened with Eclipse MAT, VisualVM, or `jmap -histo`. The process resumes immediately after the dump completes.

**JFR lifecycle** (`JcmdJFR`): `JFR.start` activates JFR sub-system in the running JVM with `settings=default` (a built-in profile). Events are collected in circular memory buffers. `JFR.dump` flushes current buffer contents to disk without stopping the recording. `JFR.stop` ends the recording and frees JFR memory.

## 7. Gotchas & takeaways

> **`jcmd` must run as the same user (or root) as the target JVM.** On Linux, `jcmd` uses `/tmp/.java_pid<PID>` — a Unix socket created with the JVM owner's permissions. Running `sudo jcmd` as root can see all JVMs, but running as a different non-root user fails silently (process appears in list but commands return "unable to open socket").

> **`GC.heap_dump` pauses the application.** Writing a heap dump requires a safe-point stop-the-world pause. On a JVM with 4 GB heap the pause is typically 5–30 seconds. Never trigger heap dumps on latency-sensitive production services without understanding the pause cost first.

- `jcmd <pid> help` — always run this first; supported commands vary by JVM flags and Java version.
- `jcmd` with no args lists all running JVMs (same as `jps -l`).
- `GC.heap_dump filename=` must be an absolute path; relative paths resolve to the JVM's working directory.
- `JFR.start settings=profile` uses a higher-fidelity profile than `default`; ~2-3% overhead.
- `VM.native_memory summary` requires starting the JVM with `-XX:NativeMemoryTracking=summary`.
- `jcmd` is the recommended unified tool; `jstack` / `jmap` are older but still work on modern JDKs.
