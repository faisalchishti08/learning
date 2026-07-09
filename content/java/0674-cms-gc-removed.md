---
card: java
gi: 674
slug: cms-gc-removed
title: CMS GC removed
---

## 1. What it is

**Java 14** (JEP 363) **removed** the Concurrent Mark Sweep (CMS) garbage collector entirely from the JDK. CMS had been Java's primary low-pause-time collector for over a decade before G1 became the default in Java 9, but it was formally **deprecated** back in Java 9 (JEP 291) with a clear warning that it would eventually be removed. Java 14 followed through: the `-XX:+UseConcMarkSweepGC` flag no longer selects a real collector — attempting to use it causes the JVM to **fail to start**, printing an error rather than silently falling back to a different collector or ignoring the flag. Any application, deployment script, or `JAVA_OPTS` configuration still specifying CMS needs to be updated to use G1 (the default), ZGC, Shenandoah, or another supported collector before upgrading to Java 14 or later.

## 2. Why & when

CMS's fundamental design — concurrent marking and sweeping, but *without* concurrent compaction — meant it was prone to heap fragmentation over time, which could eventually force a very expensive, full stop-the-world compaction as a last resort, undermining the very low-pause-time goal CMS existed for. G1, introduced as a full replacement in Java 7/9, was specifically designed to compact concurrently (avoiding this fragmentation trap) and had matured into a strictly better default choice for the vast majority of workloads that previously reached for CMS. Maintaining CMS's code alongside G1, ZGC, and Shenandoah imposed a real ongoing cost on OpenJDK's maintainers for a collector actively being out-competed by newer designs — hence the long, telegraphed deprecation-then-removal path (Java 9 deprecation, Java 14 removal), giving the ecosystem five years of advance notice. If you're maintaining or upgrading any Java application that still specifies `-XX:+UseConcMarkSweepGC`, you must address this before moving to Java 14+ — there's no compatibility shim or silent fallback.

## 3. Core concept

```bash
# Pre-Java 14: CMS was deprecated but still functional
java -XX:+UseConcMarkSweepGC -Xmx4g MyApp   # worked, but printed a deprecation warning

# Java 14+: this now FAILS TO START
java -XX:+UseConcMarkSweepGC -Xmx4g MyApp
# Error: Unrecognized VM option 'UseConcMarkSweepGC'
# Error: Could not create the Java Virtual Machine.
# Error: A fatal exception has occurred. Program will exit.

# The migration path: use G1 (the default; this flag is often unnecessary)
java -XX:+UseG1GC -Xmx4g MyApp
# ...or ZGC / Shenandoah for lower-pause-time needs, if your workload calls for it
java -XX:+UnlockExperimentalVMOptions -XX:+UseZGC -Xmx4g MyApp
```

Since G1 has been the JVM's **default** collector since Java 9, many applications that never explicitly set `-XX:+UseConcMarkSweepGC` are entirely unaffected by this removal — the risk is specifically for configurations that pinned CMS explicitly.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CMS deprecated in Java 9 with a warning, then removed in Java 14 causing startup failure if still specified">
  <rect x="10" y="20" width="180" height="120" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="42" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 9</text>
  <text x="100" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CMS deprecated</text>
  <text x="100" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(JEP 291)</text>
  <text x="100" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Still works,</text>
  <text x="100" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">prints warning.</text>

  <line x1="190" y1="80" x2="230" y2="80" stroke="#8b949e" stroke-width="2" marker-end="url(#cm1)"/>

  <rect x="240" y="20" width="180" height="120" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="330" y="42" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Java 14</text>
  <text x="330" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">CMS removed</text>
  <text x="330" y="82" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">(JEP 363)</text>
  <text x="330" y="105" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">JVM fails to start</text>
  <text x="330" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">if flag is used.</text>

  <line x1="430" y1="80" x2="470" y2="80" stroke="#6db33f" stroke-width="2" marker-end="url(#cm2)"/>

  <rect x="480" y="20" width="130" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Migrate to</text>
  <text x="545" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">G1 (default)</text>
  <text x="545" y="85" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">ZGC</text>
  <text x="545" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Shenandoah</text>

  <defs>
    <marker id="cm1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="cm2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Five years separated CMS's deprecation warning from its actual removal — a long, clearly telegraphed migration window.

## 5. Runnable example

Scenario: a deployment script that still hardcodes CMS flags from an older Java version — first demonstrating the startup failure this causes on Java 14+, then fixing it by switching to G1, then writing a small defensive launcher script that checks the JVM's actual collector before running critical application logic, catching a misconfiguration early with a clear message rather than an inscrutable crash log.

### Level 1 — Basic

```java
// File: SimpleApp.java
public class SimpleApp {
    public static void main(String[] args) {
        System.out.println("Application started successfully.");
    }
}
```

**How to run (demonstrating the Java 14+ removal):**
```
javac SimpleApp.java
java -XX:+UseConcMarkSweepGC SimpleApp
```

Expected output on Java 14+ (the JVM never even reaches `main`):
```
Unrecognized VM option 'UseConcMarkSweepGC'
Error: Could not create the Java Virtual Machine.
Error: A fatal exception has occurred. Program will exit.
```

### Level 2 — Intermediate

**How to fix the deployment script** by switching to G1 (or simply removing the flag, since G1 has been the default since Java 9):
```
java -XX:+UseG1GC SimpleApp
```

Expected output:
```
Application started successfully.
```

Or, since G1 is already the default collector, the flag is entirely optional:
```
java SimpleApp
```

Expected output:
```
Application started successfully.
```

The fix is often as simple as deleting a stale flag from a launch script — many `-XX:+UseConcMarkSweepGC` occurrences in older deployment configurations were set when CMS genuinely was the recommended low-pause choice (pre-Java 9), and simply removing them lets the JVM use its modern, better-performing default.

### Level 3 — Advanced

```java
// File: SafeLauncherCheck.java
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import java.util.List;

public class SafeLauncherCheck {
    public static void main(String[] args) {
        RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
        List<String> jvmArgs = runtime.getInputArguments();

        boolean hasStaleGcFlag = jvmArgs.stream()
            .anyMatch(arg -> arg.contains("UseConcMarkSweepGC") || arg.contains("UseParNewGC"));

        if (hasStaleGcFlag) {
            System.err.println("WARNING: detected a legacy CMS-related GC flag in JVM arguments.");
            System.err.println("These flags were removed/deprecated and may cause failures on newer JDKs.");
            System.err.println("Detected args: " + jvmArgs);
        } else {
            System.out.println("No legacy GC flags detected. JVM args: " + jvmArgs);
        }

        System.out.println("Application logic starts here.");
    }
}
```

**How to run (simulating a launcher that self-checks its own JVM configuration):**
```
java -XX:+UseG1GC -Xmx512m SafeLauncherCheck
```

Expected output:
```
No legacy GC flags detected. JVM args: [-XX:+UseG1GC, -Xmx512m]
Application logic starts here.
```

Level 3 doesn't demonstrate a crash (since this same program couldn't even start with a truly unrecognized flag, as shown in Level 1) — instead it shows a **defensive pattern**: a launcher or startup-diagnostics class that inspects its own JVM arguments via `RuntimeMXBean.getInputArguments()` and proactively warns about *other* legacy-but-still-technically-accepted flags (like `-XX:+UseParNewGC`, CMS's companion young-generation collector, also removed) that might indicate a stale, pre-migration deployment configuration worth auditing, even in configurations that happen to still start successfully.

## 6. Walkthrough

1. When the JVM is launched with `java -XX:+UseG1GC -Xmx512m SafeLauncherCheck`, the JVM parses its command-line arguments *before* any Java code runs. Because `-XX:+UseG1GC` and `-Xmx512m` are both valid, recognized flags on Java 14+ (G1 was never removed — only CMS and a couple of related flags were), the JVM starts normally and proceeds to load and execute `SafeLauncherCheck.main`.
2. Inside `main`, `ManagementFactory.getRuntimeMXBean()` retrieves a management bean giving programmatic access to information about the running JVM instance itself — among other things, the exact list of arguments it was launched with.
3. `runtime.getInputArguments()` returns that list — in this case, `["-XX:+UseG1GC", "-Xmx512m"]` — reflecting exactly what was passed on the command line (not including the classpath or main-class arguments, just JVM-level flags).
4. `jvmArgs.stream().anyMatch(arg -> arg.contains("UseConcMarkSweepGC") || arg.contains("UseParNewGC"))` scans this list, checking whether any argument string contains either of two known-legacy, CMS-family flag names. Neither `"-XX:+UseG1GC"` nor `"-Xmx512m"` contains either substring, so `anyMatch` returns `false`.
5. Because `hasStaleGcFlag` is `false`, the `else` branch runs, printing the JVM arguments as a simple confirmation that nothing suspicious was detected, followed by `"Application logic starts here."` — signaling that the defensive check passed and normal application logic can proceed.
6. Contrast this with what would happen if this exact program were launched instead with `-XX:+UseConcMarkSweepGC` directly: as shown in Level 1, the JVM would **never reach `main` at all** — the flag is rejected at JVM startup, before any Java bytecode executes, which is precisely why this kind of self-check inside `main` can only catch *other*, still-technically-valid-but-suspicious flags (like a lingering `-XX:+UseParNewGC` combined with a *different*, still-working GC flag) — it cannot catch or gracefully handle the specific case of a genuinely removed flag causing an outright startup failure, since Java code never runs in that scenario.
7. This distinction — "flags that cause hard startup failure" vs. "flags that still parse but indicate a stale configuration" — is the practical lesson: auditing deployment scripts for `UseConcMarkSweepGC` specifically requires checking the scripts and configuration files themselves (as in Level 2's fix), not relying on in-application runtime checks, since the JVM never gets far enough to run such a check when the truly removed flag is present.

```
java -XX:+UseConcMarkSweepGC ... ──► JVM startup parses flags ──► UNRECOGNIZED ──► fatal error, exits
                                          (main() never runs — no in-app check possible)

java -XX:+UseG1GC ... ──► JVM startup parses flags ──► recognized ──► main() runs ──► in-app checks possible
```

## 7. Gotchas & takeaways

> A JVM launched with `-XX:+UseConcMarkSweepGC` on Java 14+ **fails before any application code runs at all** — there is no way to catch this inside `main`, add a fallback, or log a graceful warning from within the Java application itself. The fix must happen at the level of whatever launches the JVM: shell scripts, `JAVA_OPTS` environment variables, systemd unit files, Docker `CMD`/`ENTRYPOINT` lines, or application-server startup configuration.

- CMS's removal in Java 14 followed a five-year deprecation notice from Java 9 — a model of the kind of advance warning major JDK feature removals typically follow.
- The companion young-generation collector `-XX:+UseParNewGC` (meant to pair with CMS) was removed in the same wave — audit for both if migrating an older deployment.
- G1 has been the default collector since Java 9, so many applications that never explicitly specified a collector are entirely unaffected by CMS's removal.
- For workloads that specifically chose CMS for its low-pause-time characteristics, ZGC (Linux since Java 11, macOS/Windows since Java 14 — see [ZGC on macOS & Windows](0673-zgc-on-macos-windows.md)) or Shenandoah (see [Shenandoah GC (experimental)](0653-shenandoah-gc-experimental.md)) are the modern equivalents worth evaluating.
- Before upgrading any production JVM to Java 14+, grep deployment configurations (`JAVA_OPTS`, Dockerfiles, systemd units, application-server configs) for `UseConcMarkSweepGC` and `UseParNewGC` specifically — these are exactly the kind of stale flags that silently work for years until a JDK upgrade turns them into a hard startup failure.
