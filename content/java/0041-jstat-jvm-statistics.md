---
card: java
gi: 41
slug: jstat-jvm-statistics
title: jstat — JVM statistics
---

## 1. What it is

**`jstat`** is a JDK command-line tool that polls and prints JVM performance statistics — GC activity, heap sizes, class-loading counts, and JIT compilation counters — at a fixed interval without attaching a full debugger.

```bash
jstat -gc <pid> <interval_ms> <count>

# Example: GC stats every 1 second, 10 times
jstat -gc 1234 1000 10
```

`jstat` is lightweight: it reads counters from shared memory (`/tmp/hsperfdata_<user>/`) that the JVM updates continuously. No attach overhead, no GC pause triggered.

## 2. Why & when

Use `jstat` when:
- **Watching GC activity in real time** — is GC running every 5 seconds? Is Old Gen slowly filling up?
- **Diagnosing GC pressure** before a heap dump — `jstat -gcutil` shows time spent in GC as a %.
- **Monitoring class-loading** — slow startup? `jstat -class` shows how many classes loaded and how fast.
- **JIT compilation rate** — `jstat -compiler` shows methods compiled.

`jstat` is the go-to tool on servers where you cannot install monitoring agents. It's read-only (no side effects) and streams at whatever interval you specify.

## 3. Core concept

```bash
# Most useful options:
jstat -gcutil <pid> 1000     # GC utilization %: S0% S1% E% O% M% YGC YGCT FGC FGCT GCT
jstat -gc     <pid> 1000     # GC sizes in KB:  S0C S1C S0U S1U EC EU OC OU MC MU ...
jstat -gccause <pid> 1000    # -gcutil + cause of last/current GC
jstat -class   <pid> 1000    # class-loading: Loaded Bytes Unloaded Bytes Time
jstat -compiler <pid> 1000   # JIT: Compiled Failed Invalid Time FailedType FailedMethod

# Column key for -gcutil:
# S0% S1% = Survivor 0/1 utilization %
# E%      = Eden utilization %
# O%      = Old Gen utilization %
# M%      = Metaspace utilization %
# YGC     = number of Young GCs
# YGCT    = total time in Young GCs (s)
# FGC     = number of Full GCs
# FGCT    = total time in Full GCs (s)
# GCT     = total GC time (s)

# Sample -gcutil output:
#   S0%    S1%     E%    O%    M%   CCS%  YGC  YGCT  FGC  FGCT  GCT
#    0.00  32.64  45.32  12.45 94.36 91.23  42  0.234   0   0.000  0.234
```

`jstat` reads `/tmp/hsperfdata_<user>/<pid>` — a memory-mapped file the JVM maintains with performance counters. This is why `jstat` is fast and safe: no JVMTI attach needed.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jstat reads performance counters from JVM shared memory and prints them at intervals">
  <rect x="8" y="8" width="664" height="184" rx="8" fill="#0d1117"/>

  <!-- JVM + shared memory -->
  <rect x="20" y="25" width="240" height="155" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Running JVM</text>

  <rect x="35" y="55"  width="210" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="69" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GC counters: YGC=42, YGCT=0.234s</text>

  <rect x="35" y="83"  width="210" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Heap: Eden 45% / S1 32% / Old 12%</text>

  <rect x="35" y="111" width="210" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Classes loaded: 4,213</text>

  <rect x="35" y="139" width="210" height="28" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="140" y="151" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">/tmp/hsperfdata_user/1234</text>
  <text x="140" y="162" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(memory-mapped file)</text>

  <!-- jstat tool -->
  <rect x="315" y="80" width="100" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="365" y="100" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">jstat</text>
  <text x="365" y="115" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">-gcutil 1000 10</text>

  <!-- mmap read arrow -->
  <line x1="245" y1="153" x2="311" y2="103" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#st1)"/>
  <text x="270" y="143" fill="#79c0ff" font-size="7" font-family="sans-serif">mmap read</text>

  <!-- Output -->
  <rect x="470" y="35" width="200" height="130" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="570" y="53" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stdout (every 1s)</text>
  <text x="485" y="70"  fill="#6db33f" font-size="7" font-family="monospace">S0%  S1%  E%   O%   YGC</text>
  <text x="485" y="82"  fill="#e6edf3" font-size="7" font-family="monospace">0.00 32.6 45.3 12.4  42</text>
  <text x="485" y="94"  fill="#e6edf3" font-size="7" font-family="monospace">0.00 32.6 62.1 12.4  42</text>
  <text x="485" y="106" fill="#e6edf3" font-size="7" font-family="monospace">0.00 32.6 78.9 12.4  42</text>
  <text x="485" y="118" fill="#6db33f" font-size="7" font-family="monospace">0.00 14.2  5.6 19.8  43 ← YGC</text>
  <text x="485" y="130" fill="#e6edf3" font-size="7" font-family="monospace">0.00 14.2 22.1 19.8  43</text>
  <text x="485" y="142" fill="#8b949e" font-size="7" font-family="monospace">... repeats ×10 total</text>

  <line x1="415" y1="103" x2="466" y2="103" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#st2)"/>

  <defs>
    <marker id="st1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="st2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jstat` reads memory-mapped counters that the JVM maintains continuously. No attach overhead, no GC pause. The same row repeats every `<interval>` ms.

## 5. Runnable example

Scenario: an object-allocation service that generates lots of short-lived objects (Young GC pressure) and gradually promotes some to Old Gen. Watch `jstat -gcutil` as the heap fills up.

### Level 1 — Basic

```java
// JstatBasic.java — show GC counters via JMX (same data as jstat)
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JstatBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jstat GC counters demo ===\n");
        System.out.println("PID: " + ProcessHandle.current().pid());

        Path jstat = findTool("jstat");
        System.out.println("jstat tool: " + (jstat != null ? jstat : "not found"));

        // Print jstat-equivalent data from JMX
        System.out.println("\n--- GC pools (equivalent to jstat -gcutil) ---");
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            MemoryUsage u = pool.getUsage();
            if (u.getMax() <= 0) continue;
            double pct = 100.0 * u.getUsed() / u.getMax();
            System.out.printf("  %-35s %5.1f%% used (%d KB / %d KB)%n",
                pool.getName(), pct, u.getUsed() / 1024, u.getMax() / 1024);
        }

        System.out.println("\n--- GC collection counts (YGC / FGC) ---");
        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.printf("  %-30s count=%-5d time=%d ms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime());
        }

        System.out.println("\n--- jstat commands ---");
        long pid = ProcessHandle.current().pid();
        System.out.println("  jstat -gcutil "   + pid + " 1000     # GC utilization % every 1s");
        System.out.println("  jstat -gc "       + pid + " 1000     # GC sizes in KB");
        System.out.println("  jstat -gccause "  + pid + " 1000     # + cause of last GC");
        System.out.println("  jstat -class "    + pid + " 1000     # class loading counters");
        System.out.println("  jstat -compiler " + pid + " 1000     # JIT compilation stats");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JstatBasic.java`

`GarbageCollectorMXBean.getCollectionCount()` and `getCollectionTime()` are exactly the values `jstat -gcutil` shows as `YGC`/`YGCT`/`FGC`/`FGCT`. This is the same data source — the JVM's internal performance counters.

### Level 2 — Intermediate

Same allocation service: launch a loop that creates many short-lived objects and some long-lived ones, then watch `jstat -gcutil` printed every second.

```java
// JstatWatch.java — generate GC pressure, then run jstat against self
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JstatWatch {
    static final List<byte[]> SURVIVORS = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        Path jstat = findTool("jstat");
        if (jstat == null) { System.err.println("JDK required"); return; }

        long pid = ProcessHandle.current().pid();
        System.out.println("=== GC pressure demo + jstat watch ===");
        System.out.println("PID: " + pid);

        // Run jstat in background — 12 readings × 1 second each
        Process jstatP = new ProcessBuilder(
            jstat.toString(), "-gcutil", String.valueOf(pid), "1000", "12")
            .redirectErrorStream(true).start();

        // Generate GC pressure: lots of short-lived objects + some promoted
        System.out.println("Generating allocation pressure...");
        Random rng = new Random();
        for (int round = 0; round < 10; round++) {
            // Short-lived: create and discard 1000 × 100KB arrays
            for (int i = 0; i < 1000; i++) {
                byte[] tmp = new byte[100_000]; // 100 KB — will be GC'd
                tmp[0] = (byte) rng.nextInt(); // prevent dead-code elimination
            }
            // Long-lived: keep some (they promote to Old Gen after surviving GC)
            if (round % 3 == 0)
                SURVIVORS.add(new byte[512_000]); // 512 KB survives

            System.gc(); // encourage GC for demo purposes
            Thread.sleep(900);
        }

        // Print jstat output
        String jstatOut = new String(jstatP.getInputStream().readAllBytes());
        jstatP.waitFor();
        System.out.println("\n--- jstat -gcutil output ---");
        System.out.println(jstatOut);

        // Explain the columns
        System.out.println("Columns: S0%=Survivor0, S1%=Survivor1, E%=Eden,");
        System.out.println("         O%=Old, M%=Metaspace, YGC=young-GC-count, FGC=full-GC-count");
        System.out.println("Watch E% rise → drop (Young GC ran) → rise again.");
        System.out.println("O% slowly increases as SURVIVORS promotions accumulate.");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JstatWatch.java`

Watch `E%` (Eden) rise and fall with each Young GC. `O%` (Old Gen) climbs slightly each time a `SURVIVOR` array gets promoted. `YGC` increments with each collection. This is exactly how you diagnose GC pressure in production.

### Level 3 — Advanced

Same allocation service grown to parse `jstat -gccause` output programmatically, detect "too many Young GCs per second" as a signal of GC pressure, and recommend tuning flags.

```java
// JstatAnalyze.java — parse jstat output, detect GC pressure, suggest tuning
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JstatAnalyze {
    static final List<byte[]> SURVIVORS = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        Path jstat = findTool("jstat");
        if (jstat == null) { System.err.println("JDK required"); return; }

        long pid = ProcessHandle.current().pid();
        System.out.println("=== jstat GC pressure analyzer ===");

        // Start jstat: 20 readings × 500ms
        Process jstatP = new ProcessBuilder(
            jstat.toString(), "-gccause", String.valueOf(pid), "500", "20")
            .redirectErrorStream(true).start();

        // Generate heavy GC pressure
        Random rng = new Random();
        for (int round = 0; round < 9; round++) {
            for (int i = 0; i < 2000; i++) {
                byte[] tmp = new byte[50_000];
                tmp[0] = (byte) rng.nextInt();
            }
            if (round % 2 == 0) SURVIVORS.add(new byte[1_000_000]);
            Thread.sleep(450);
        }

        String raw = new String(jstatP.getInputStream().readAllBytes());
        jstatP.waitFor();

        System.out.println("\n--- jstat -gccause output ---");
        System.out.println(raw);

        // Parse: extract YGC and YGCT columns to compute avg GC pause
        List<String[]> rows = new ArrayList<>();
        for (String line : raw.lines().skip(1).toList()) {
            String[] cols = line.trim().split("\\s+");
            if (cols.length >= 7) rows.add(cols);
        }

        if (rows.size() >= 2) {
            // Columns in gccause: S0 S1 E O M CCS YGC YGCT FGC FGCT GCT LGCC GCC
            try {
                String[] first = rows.get(0);
                String[] last  = rows.get(rows.size() - 1);
                double ygcDelta  = Double.parseDouble(last[6])  - Double.parseDouble(first[6]);
                double ygctDelta = Double.parseDouble(last[7])  - Double.parseDouble(first[7]);
                double fgcDelta  = Double.parseDouble(last[8])  - Double.parseDouble(first[8]);
                double elapsedS  = rows.size() * 0.5;

                System.out.println("\n--- Analysis ---");
                System.out.printf("Elapsed: %.1f s%n", elapsedS);
                System.out.printf("Young GCs: %.0f (%.1f/s)%n", ygcDelta, ygcDelta / elapsedS);
                System.out.printf("Full GCs:  %.0f%n", fgcDelta);
                if (ygcDelta > 0)
                    System.out.printf("Avg Young GC pause: %.1f ms%n", ygctDelta / ygcDelta * 1000);

                double gcPct = ygctDelta / elapsedS * 100;
                System.out.printf("GC overhead: %.1f%%%n", gcPct);

                System.out.println("\n--- Recommendations ---");
                if (ygcDelta / elapsedS > 2)
                    System.out.println("  HIGH GC RATE: increase Eden with -Xmn or -XX:NewRatio");
                if (fgcDelta > 0)
                    System.out.println("  FULL GC: Old Gen filling up — increase -Xmx or fix memory leak");
                if (gcPct > 5)
                    System.out.println("  GC OVERHEAD >5%: app spending too much time in GC");
                System.out.println("  -XX:+PrintGCDetails -XX:+PrintGCDateStamps → GC logs for deeper analysis");
                System.out.println("  -Xlog:gc*:file=gc.log:time → JDK 9+ unified GC logging");
            } catch (NumberFormatException e) {
                System.out.println("(parse error — column format may differ by JVM)");
            }
        }
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JstatAnalyze.java`

Parses `jstat -gccause` rows to compute Young GC rate, average pause, and GC overhead %. If GC rate exceeds 2/second or overhead exceeds 5%, it prints tuning recommendations — the same logic a monitoring alert would use.

## 6. Walkthrough

Execution trace in `JstatAnalyze.main`:

**Background `jstat` process.** `jstat -gccause <pid> 500 20` starts in a child process. It opens `/tmp/hsperfdata_<user>/<pid>` (a memory-mapped shared-memory file the JVM writes constantly) and reads performance counters every 500 ms, 20 times total.

**Allocation loop.** Each round creates 2,000 × 50 KB `byte[]` arrays — 100 MB of short-lived garbage per round. These fill Eden. When Eden fills, the JVM triggers a **Young GC** (also called Minor GC): live objects from Eden and Survivor 0 are copied to Survivor 1 (or promoted to Old Gen if they've survived enough GCs). The dead arrays are freed. `YGC` counter increments; `E%` drops.

**Promotion.** Every other round, a 1 MB `byte[]` is added to `SURVIVORS` (a static list). These objects survive every Young GC. After enough GC cycles (`-XX:MaxTenuringThreshold`, default 15), they are promoted to Old Gen. `O%` column rises.

**`jstat` columns (gccause):**

| Column | Meaning |
|--------|---------|
| `S0`, `S1`, `E` | Survivor 0/1 and Eden utilization % |
| `O` | Old Gen utilization % |
| `M` | Metaspace % |
| `YGC` | Total Young GC count |
| `YGCT` | Total time in Young GC (seconds) |
| `FGC` | Total Full GC count |
| `LGCC` | Cause of **last** GC (e.g., `G1 Evacuation Pause`) |
| `GCC` | Cause of **current** GC (or `No GC`) |

**Parsing and analysis.** The code diffs the first and last rows: `ygcDelta / elapsedS` = Young GCs per second. `ygctDelta / ygcDelta * 1000` = average Young GC pause in ms. GC overhead = `ygctDelta / elapsedS × 100%`. A GC overhead > 10% means the JVM is fighting to keep up — the classic memory leak or undersized heap symptom.

## 7. Gotchas & takeaways

> **`jstat` only works if `/tmp/hsperfdata_<user>/` is writable.** Some containerised environments (Docker with read-only `/tmp` or `--tmpfs /tmp:ro`) prevent the JVM from creating the performance data file. Add `-XX:-UsePerfData` to disable perfdata entirely if the filesystem is read-only, or mount a writable `/tmp`. Without the perfdata file, `jstat` will print "No such process" even though the JVM is running.

> **`jstat -gcutil` columns don't exist for ZGC or Shenandoah** in the same format. These GCs use different region structures; some columns show `0.00` for S0/S1 because they don't use Survivor spaces. Use `-gc` instead for absolute KB numbers, which all GC algorithms populate.

- `jstat -gcutil <pid> 1000` — most useful starting command; run until you see a pattern.
- `E%` rising then suddenly dropping = Young GC fired; `O%` rising = objects being promoted.
- `FGC > 0` in a short window = Old Gen pressure — check for memory leaks or insufficient heap.
- `-gccause` adds `LGCC` column = cause of last GC (e.g., `G1 Evacuation Pause`, `System.gc()`).
- `jstat -class <pid>` = class loading rate; useful during startup to see if a framework is loading thousands of classes.
- `jstat` reads shared memory — no JVMTI attach, no GC pause, safe for production use.
