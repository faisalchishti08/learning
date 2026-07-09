---
card: java
gi: 609
slug: unified-jvm-logging
title: Unified JVM logging
---

## 1. What it is

Unified JVM logging is a JDK 9 framework (`-Xlog`) that consolidates all JVM-internal logging — garbage collection, class loading, thread activity, compilation, modules, and dozens of other subsystems — under a single configuration syntax. Instead of dozens of separate `-XX:+Print*` flags (each with its own format and behaviour), you use a unified `-Xlog:tag1,tag2:output:decorators:level` syntax that controls which subsystems log, where the output goes, what metadata decorators appear, and at what verbosity level. This makes JVM diagnostic logging predictable, consistent, and scriptable.

## 2. Why & when

Before JDK 9, JVM diagnostic logging was a patchwork of ad-hoc flags: `-XX:+PrintGC`, `-XX:+PrintGCDetails`, `-XX:+PrintGCTimeStamps`, `-XX:+TraceClassLoading`, `-XX:+TraceClassUnloading`, `-XX:+PrintCompilation`, and dozens more. Each had its own format, its own output destination (stdout vs stderr), and its own timestamp style. Debugging a complex JVM issue often required stitching together output from 5+ different flags with incompatible formats. Unified logging replaces all of this with a single, composable system: `-Xlog:gc+class=info:stdout:time,level,tags` gives you both GC and class-loading logs at info level, on stdout, with timestamps, log level, and tag names as decorators — one consistent format across all subsystems.

## 3. Core concept

```
-Xlog:selector:output:decorators:output-options

Examples:
  -Xlog:gc*
    All GC-related logs at default level

  -Xlog:gc+class=debug:file=gc-class.log:time,level,tags
    GC and class loading debug logs, file output, with specific decorators

  -Xlog:all=warning:stderr:none
    All subsystems at warning level or higher to stderr, no decorators

  -Xlog:gc=trace::uptime,level,tags
    Trace-level GC logs to stdout with uptime and level decorators
```

The `selector` is a comma-separated list of tag names (e.g. `gc`, `class`, `thread`, `compilation`, `modules`). Tags can be combined with `+` (AND) and wildcards (`gc*` matches all GC-related tags). The `output` can be `stdout`, `stderr`, or `file=path`. `decorators` control metadata: `time` (ISO-8601), `uptime` (seconds), `timemillis` (ms since epoch), `level`, `tags`, `pid`, `tid`. The `output-options` control rotation and file size.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unified JVM logging replaces dozens of -XX:+Print flags with -Xlog:selector:output:decorators">
  <rect x="20" y="10" width="600" height="190" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">-Xlog:gc+class=info:file=diag.log:time,level,tags:filecount=5,filesize=10M</text>

  <rect x="30" y="50" width="100" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="80" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">gc+class</text>
  <text x="140" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">selector</text>

  <rect x="180" y="50" width="100" height="30" rx="4" fill="#79c0ff" stroke="#79c0ff"/>
  <text x="230" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">file=diag.log</text>
  <text x="290" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">output</text>

  <rect x="330" y="50" width="120" height="30" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="390" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">time,level,tags</text>
  <text x="460" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">decorators</text>

  <text x="30" y="110" fill="#8b949e" font-size="10" font-family="sans-serif">Replaces:</text>
  <text x="30" y="128" fill="#f85149" font-size="9" font-family="monospace">  -XX:+PrintGC  -XX:+PrintGCDetails  -XX:+PrintGCTimeStamps</text>
  <text x="30" y="145" fill="#f85149" font-size="9" font-family="monospace">  -XX:+TraceClassLoading  -XX:+TraceClassUnloading</text>
  <text x="30" y="162" fill="#f85149" font-size="9" font-family="monospace">  -XX:+PrintCompilation  -XX:+LogCompilation</text>

  <text x="30" y="190" fill="#6db33f" font-size="10" font-family="monospace">  → -Xlog:gc+class+compilation=info</text>
</svg>

One syntax replaces an entire ecosystem of legacy `-XX:+Print*` flags.

## 5. Runnable example

Scenario: a diagnostic logging setup for a memory-intensive application — starting with basic GC logging, extending to combined subsystem logging with file output, and finally building a production-grade logging configuration with rotation and decorator tuning.

### Level 1 — Basic

```java
// File: UnifiedLoggingDemo.java

public class UnifiedLoggingDemo {
    public static void main(String[] args) {
        System.out.println("=== Unified JVM Logging (-Xlog) ===\n");

        System.out.println("Run this program with different -Xlog flags to see logs:");
        System.out.println();
        System.out.println("1. Basic GC logging:");
        System.out.println("   $ java -Xlog:gc UnifiedLoggingDemo.java");
        System.out.println("   [0.123s][info][gc] GC(0) Pause Young ...");
        System.out.println();
        System.out.println("2. GC + class loading:");
        System.out.println("   $ java -Xlog:gc+class UnifiedLoggingDemo.java");
        System.out.println();
        System.out.println("3. Debug-level GC to a file:");
        System.out.println("   $ java -Xlog:gc*=debug:file=gc-debug.log UnifiedLoggingDemo.java");
        System.out.println();
        System.out.println("4. All subsystems at warning level:");
        System.out.println("   $ java -Xlog:all=warning UnifiedLoggingDemo.java");
        System.out.println();
        System.out.println("5. Show all available log tags:");
        System.out.println("   $ java -Xlog:help");
        System.out.println("   (lists all tags: gc, class, thread, compilation, ...)\n");

        System.out.println("Key tags:");
        System.out.println("  gc            Garbage collection events");
        System.out.println("  class         Class loading/unloading");
        System.out.println("  thread        Thread start/stop/state changes");
        System.out.println("  compilation   JIT compiler activity");
        System.out.println("  modules       Module system operations");
    }
}
```

**How to run:** `java UnifiedLoggingDemo.java`

Expected output:
```
=== Unified JVM Logging (-Xlog) ===

Run this program with different -Xlog flags to see logs:

1. Basic GC logging:
   $ java -Xlog:gc UnifiedLoggingDemo.java
   [0.123s][info][gc] GC(0) Pause Young ...

2. GC + class loading:
   $ java -Xlog:gc+class UnifiedLoggingDemo.java

3. Debug-level GC to a file:
   $ java -Xlog:gc*=debug:file=gc-debug.log UnifiedLoggingDemo.java

4. All subsystems at warning level:
   $ java -Xlog:all=warning UnifiedLoggingDemo.java

5. Show all available log tags:
   $ java -Xlog:help
   (lists all tags: gc, class, thread, compilation, ...)

Key tags:
  gc            Garbage collection events
  class         Class loading/unloading
  thread        Thread start/stop/state changes
  compilation   JIT compiler activity
  modules       Module system operations
```

The simplest exploration: run the JVM with various `-Xlog` selectors to see different subsystem logs. Tag selectors use `+` for AND combinations and `*` for wildcards.

### Level 2 — Intermediate

```java
// File: LoggingConfiguration.java
import java.io.*;
import java.util.*;

public class LoggingConfiguration {

    /*
    === Run with unified logging ===

    java -Xlog:gc+class=info:stdout:time,level,tags \
         -Xlog:compilation=debug:file=comp.log \
         LoggingConfiguration.java

    Output on stdout:
      [2026-07-09T12:00:00.123+0000][info][gc,class] GC(0) Pause Young ...
      [2026-07-09T12:00:00.234+0000][info][gc,class] Loaded java.lang.String

    Output in comp.log:
      [2026-07-09T12:00:00.345+0000][debug][compilation] Compiling method ...

    */

    public static void main(String[] args) {
        System.out.println("=== Unified Logging Configuration ===\n");

        System.out.println("Multiple -Xlog flags compose (latest wins for same output):");
        System.out.println();
        System.out.println("  -Xlog:gc+class=info:stdout:time,level,tags");
        System.out.println("    │        │        │      └── decorators: time=ISO, level=level, tags=which subsys");
        System.out.println("    │        │        └── output: stdout");
        System.out.println("    │        └── level: info (trace, debug, info, warning, error)");
        System.out.println("    └── selector: gc AND class\n");

        System.out.println("  -Xlog:compilation=debug:file=comp.log");
        System.out.println("    │             │       └── file output (no stdout pollution)");
        System.out.println("    │             └── level: debug");
        System.out.println("    └── selector: compilation\n");

        System.out.println("Log levels (increasing verbosity):");
        System.out.println("  off → error → warning → info → debug → trace");
        System.out.println("  (Each level includes all less-verbose levels)\n");

        System.out.println("Decorators (comma-separated, can include 'none'):");
        System.out.println("  time       — ISO-8601 timestamp with timezone");
        System.out.println("  utctime    — UTC timestamp");
        System.out.println("  uptime     — seconds since JVM start");
        System.out.println("  timemillis — milliseconds since epoch");
        System.out.println("  level      — log level (trace/debug/info/warning/error)");
        System.out.println("  tags       — tag set for the log line");
        System.out.println("  pid        — process ID");
        System.out.println("  tid        — thread ID");
    }
}
```

**How to run:** `java LoggingConfiguration.java`

Expected output:
```
=== Unified Logging Configuration ===

Multiple -Xlog flags compose (latest wins for same output):

  -Xlog:gc+class=info:stdout:time,level,tags
    │        │        │      └── decorators: time=ISO, level=level, tags=which subsys
    │        │        └── output: stdout
    │        └── level: info (trace, debug, info, warning, error)
    └── selector: gc AND class

  -Xlog:compilation=debug:file=comp.log
    │             │       └── file output (no stdout pollution)
    │             └── level: debug
    └── selector: compilation

Log levels (increasing verbosity):
  off → error → warning → info → debug → trace
  (Each level includes all less-verbose levels)

Decorators (comma-separated, can include 'none'):
  time       — ISO-8601 timestamp with timezone
  utctime    — UTC timestamp
  uptime     — seconds since JVM start
  timemillis — milliseconds since epoch
  level      — log level (trace/debug/info/warning/error)
  tags       — tag set for the log line
  pid        — process ID
  tid        — thread ID
```

The real-world configuration: splitting different subsystem logs to different destinations. GC and class loading go to stdout with ISO timestamps; compilation debug logs go to a file so they don't pollute the console.

### Level 3 — Advanced

```java
// File: ProductionLogging.java
import java.io.*;
import java.util.*;
import java.util.stream.*;

public class ProductionLogging {

    public static void main(String[] args) throws Exception {
        System.out.println("=== Production-Grade JVM Logging Setup ===\n");

        System.out.println("Recommended production logging configuration:\n");

        System.out.println("java \\");
        System.out.println("  -Xlog:gc*=info:file=/var/log/app/gc.log:time,level,tags:filecount=10,filesize=20M \\");
        System.out.println("  -Xlog:safepoint+class=info:file=/var/log/app/jvm.log:uptime,level,tags:filecount=5,filesize=10M \\");
        System.out.println("  -Xlog:all=warning:stderr:time,level,tags \\");
        System.out.println("  -Xlog:exceptions=debug:file=/var/log/app/exceptions.log::filecount=3,filesize=5M \\");
        System.out.println("  -jar myapp.jar\n");

        System.out.println("What each line does:\n");

        System.out.println("1. GC logs (rotated, 10×20MB files):");
        System.out.println("   Captures all GC events at info level to gc.log");
        System.out.println("   File rotation: 10 files of 20MB each = 200MB max");
        System.out.println("   Useful for: memory leak diagnosis, GC pause analysis\n");

        System.out.println("2. Safepoint + class loading (rotated, 5×10MB):");
        System.out.println("   Captures safepoint operations and class loading/unloading");
        System.out.println("   Useful for: diagnosing long safepoint pauses, classloader leaks\n");

        System.out.println("3. All subsystems at warning+ to stderr:");
        System.out.println("   Catches any JVM warning or error across ALL subsystems");
        System.out.println("   Sent to stderr so it shows in container/process logs");
        System.out.println("   Lightweight — only errors/warnings, not debug spam\n");

        System.out.println("4. Exception tracking:");
        System.out.println("   Captures thrown exceptions (including caught ones)");
        System.out.println("   Useful for: finding hidden exception hot paths\n");

        System.out.println("File rotation format:");
        System.out.println("  filecount=N   — keep N rotated files (gc.log.0, gc.log.1, ...)");
        System.out.println("  filesize=NM   — rotate when file reaches N megabytes");
        System.out.println("  Default: no rotation (single file, unbounded growth)\n");

        System.out.println("Dynamic runtime control (jcmd):");
        System.out.println("  $ jcmd <pid> VM.log what='gc*=debug' output='file=gc-new.log'");
        System.out.println("  $ jcmd <pid> VM.log disable");
        System.out.println("  (Change log configuration without restarting the JVM)");

        // Demonstrate with some GC-triggering allocations
        System.out.println("\n\n=== Local test (allocating objects to trigger GC) ===");
        List<byte[]> memory = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            memory.add(new byte[1_000_000]);
            System.out.println("Allocated block " + (i + 1));
        }
        System.out.println("\n(Try running: java -Xlog:gc*=info " + ProductionLogging.class.getSimpleName() + ".java");
        System.out.println("to see GC logs for these allocations)");
    }
}
```

**How to run:** `java ProductionLogging.java`

Expected output:
```
=== Production-Grade JVM Logging Setup ===

Recommended production logging configuration:

java \
  -Xlog:gc*=info:file=/var/log/app/gc.log:time,level,tags:filecount=10,filesize=20M \
  -Xlog:safepoint+class=info:file=/var/log/app/jvm.log:uptime,level,tags:filecount=5,filesize=10M \
  -Xlog:all=warning:stderr:time,level,tags \
  -Xlog:exceptions=debug:file=/var/log/app/exceptions.log::filecount=3,filesize=5M \
  -jar myapp.jar

What each line does:

1. GC logs (rotated, 10×20MB files):
   Captures all GC events at info level to gc.log
   File rotation: 10 files of 20MB each = 200MB max
   Useful for: memory leak diagnosis, GC pause analysis

2. Safepoint + class loading (rotated, 5×10MB):
   Captures safepoint operations and class loading/unloading
   Useful for: diagnosing long safepoint pauses, classloader leaks

3. All subsystems at warning+ to stderr:
   Catches any JVM warning or error across ALL subsystems
   Sent to stderr so it shows in container/process logs
   Lightweight — only errors/warnings, not debug spam

4. Exception tracking:
   Captures thrown exceptions (including caught ones)
   Useful for: finding hidden exception hot paths

File rotation format:
  filecount=N   — keep N rotated files (gc.log.0, gc.log.1, ...)
  filesize=NM   — rotate when file reaches N megabytes
  Default: no rotation (single file, unbounded growth)

Dynamic runtime control (jcmd):
  $ jcmd <pid> VM.log what='gc*=debug' output='file=gc-new.log'
  $ jcmd <pid> VM.log disable
  (Change log configuration without restarting the JVM)


=== Local test (allocating objects to trigger GC) ===
Allocated block 1
Allocated block 2
Allocated block 3
Allocated block 4
Allocated block 5

(Try running: java -Xlog:gc*=info ProductionLogging.java
to see GC logs for these allocations)
```

The production-flavoured setup: a multi-line `-Xlog` configuration covering all critical JVM subsystems with file rotation (preventing unbounded log growth), different verbosity levels per subsystem (debug-level GC, warning-level global), and separate output destinations (files for high-volume logs, stderr for warnings). The `jcmd VM.log` dynamic control lets operators change log levels at runtime without restarting — critical for debugging production issues.

## 6. Walkthrough

Tracing what happens when the JVM starts with `-Xlog:gc*=info:file=gc.log:time,level,tags:filecount=5,filesize=10M`:

1. **JVM startup**: The JVM parses the `-Xlog` argument during early initialisation, before the application's `main` method runs. The unified logging framework initialises with:
   - Selector: `gc*` (all GC-related tags: `gc`, `gc+phases`, `gc+heap`, `gc+metaspace`, etc.)
   - Level: `info` (log info, warning, and error — but not debug or trace)
   - Output: `file=gc.log`
   - Decorators: `time` (ISO-8601 timestamp), `level` (log level name), `tags` (tag set)
   - Output options: `filecount=5` (keep 5 rotated files), `filesize=10M` (rotate at 10 MB)

2. **First GC event**: The JVM triggers a minor GC (young generation collection). Inside the GC subsystem, the code calls `log_info(gc)("Pause Young (G1 Evacuation Pause) %dM->%dM(%dM) %.3fms", before, after, total, duration)`.

3. **Logging framework**: The `log_info` macro checks:
   - Is `gc` tag configured for at least `info` level? Yes.
   - The decorator string is assembled: `[2026-07-09T12:00:01.234+0000][info][gc]`.
   - The formatted message is appended: `GC(0) Pause Young (G1 Evacuation Pause) 128M->64M(512M) 2.345ms`.
   - The complete line `[2026-07-09T12:00:01.234+0000][info][gc] GC(0) Pause Young (G1 Evacuation Pause) 128M->64M(512M) 2.345ms` is written to `gc.log`.

4. **File rotation**: The logging framework tracks `gc.log`'s current size. When it exceeds 10 MB:
   - `gc.log` is renamed to `gc.log.0`.
   - Existing `gc.log.0` is renamed to `gc.log.1`, `gc.log.1` to `gc.log.2`, ..., `gc.log.3` to `gc.log.4`.
   - `gc.log.4` (the oldest rotated file, if it exists for the 5th rotation) is deleted.
   - A new `gc.log` is created.

5. **Runtime control**: An operator runs `jcmd <pid> VM.log what='gc*=debug' output='file=gc-new.log'`. The JVM's diagnostic command handler dynamically updates the logging configuration: GC logging is now at debug level (more verbose) and writes to `gc-new.log`. The original `gc.log` configuration is superseded. The operator can revert with `jcmd <pid> VM.log disable` and re-enable with the original configuration.

## 7. Gotchas & takeaways

> The old `-XX:+PrintGC` and related flags are **deprecated** in JDK 9 and may be removed in a future release. Migrate to `-Xlog:gc` equivalents. The mapping is mostly straightforward: `-XX:+PrintGC` → `-Xlog:gc`, `-XX:+PrintGCDetails` → `-Xlog:gc*`, `-XX:+PrintGCTimeStamps` → use `uptime` decorator.

- The selector syntax `tag1+tag2` means AND — both tags must match. Use comma `tag1,tag2` for OR — either tag matches. Wildcards (`gc*`) match all tags starting with `gc`.
- File output is **buffered** — log lines may not appear immediately in the file. This is usually acceptable for diagnostic logs but can cause confusion during debugging. To force flushing, add `file=gc.log` with no additional buffering options.
- The `all` pseudo-tag matches every logging tag in the JVM. `-Xlog:all=warning` is a good "global low-pass filter" to catch warnings from any subsystem without debug-noise from all of them.
- Logging has a small performance cost — `info` level is negligible for most applications, `debug` adds measurable overhead, and `trace` can be significant (especially for `gc*` with `trace` level, which logs every object movement). In production, use `info` for always-on logging and reserve `debug`/`trace` for targeted investigations.
- `-Xlog:help` prints all available tags and their descriptions. `-Xlog:logging=debug` shows what the logging framework itself is doing (meta-logging). These are the first two commands to try when configuring logging. 