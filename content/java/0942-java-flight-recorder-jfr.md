---
card: java
gi: 942
slug: java-flight-recorder-jfr
title: Java Flight Recorder (JFR)
---

## 1. What it is

Java Flight Recorder (JFR) is a low-overhead event-recording framework built directly into the JVM (free and fully supported since Java 11, after originating as a commercial Oracle feature) that continuously captures detailed data about what the JVM and application are doing — GC pauses, thread states, method-execution sampling, lock contention, exceptions thrown, allocation hot spots, and dozens of other event types — into a compact binary `.jfr` file, with overhead low enough (typically under 1–2%) to leave running in production continuously, not just during a dedicated debugging session. Unlike a [thread dump](0941-thread-dumps.md) (one instant) or a [heap dump](0940-heap-dumps-analysis.md) (one snapshot), a JFR recording captures a *continuous window of time*, which is exactly what makes it able to answer questions like "what was happening in the 30 seconds leading up to that slow request?" rather than only "what does the system look like right now?"

## 2. Why & when

JFR is the right tool whenever the mystery is time-dependent — a periodic slowdown, an intermittent GC pause that's hard to catch with a manually-triggered thread or heap dump, or a "why was this particular request slow" question where you don't know in advance exactly when the problem will occur. Because its overhead is low enough to run continuously, a common production pattern is to always have a JFR "continuous recording" running with a rolling time window (say, the last hour), so that when something goes wrong, you already have data covering the lead-up to the incident rather than needing to reproduce it live. It complements, rather than replaces, targeted tools: a JFR recording will show you *that* a long GC pause or lock-contention spike occurred and roughly when, but drilling into the exact object graph responsible still benefits from a [heap dump](0940-heap-dumps-analysis.md), and drilling into exact stack traces at a moment of contention still benefits from a [thread dump](0941-thread-dumps.md) — JFR's role is providing the continuous, low-overhead timeline that tells you *where* in time to look.

## 3. Core concept

```
Start a recording:
  java -XX:StartFlightRecording=filename=recording.jfr,duration=60s MyApp.java
  (or attach to a running process: jcmd <pid> JFR.start ... / jcmd <pid> JFR.dump ...)

Recording captures events continuously over the window, e.g.:
  [t=0.5s]  jdk.GarbageCollection        pause=2.1ms
  [t=1.2s]  jdk.JavaMonitorEnter         thread=Worker-3 monitor=lockA duration=45ms
  [t=3.0s]  jdk.ExecutionSample          thread=Worker-1 stack=[...]
  [t=8.4s]  jdk.GarbageCollection        pause=180ms   <-- the anomaly you're hunting for
  ...

Analyze afterward with:  JDK Mission Control (JMC), opening recording.jfr,
  which visualizes the whole timeline: GC pauses, CPU/thread activity, lock contention, allocations.
```

The key structural difference from a dump: JFR is continuous and event-based over a *duration*, letting you correlate multiple kinds of events (a GC pause, a lock-contention spike, an allocation surge) that happened around the same moment in time.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JFR recording timeline showing GC pause, lock contention, and execution sample events plotted continuously across a recording window, with a spike correlated across event types" >
  <line x1="20" y1="140" x2="620" y2="140" stroke="#8b949e"/>
  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">time -&gt;</text>

  <circle cx="80" cy="120" r="4" fill="#6db33f"/>
  <circle cx="180" cy="118" r="4" fill="#6db33f"/>
  <circle cx="300" cy="60" r="7" fill="#f0883e"/>
  <text x="300" y="45" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">180ms GC pause</text>
  <circle cx="420" cy="119" r="4" fill="#6db33f"/>
  <text x="150" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">jdk.GarbageCollection events</text>

  <rect x="290" y="80" width="60" height="10" fill="#79c0ff"/>
  <text x="320" y="78" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">lock contention spike</text>

  <rect x="285" y="95" width="70" height="10" fill="#e6edf3" opacity="0.5"/>
  <text x="320" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">alloc rate surge</text>

  <line x1="300" y1="20" x2="300" y2="140" stroke="#f0883e" stroke-dasharray="3"/>
  <text x="300" y="15" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">all three correlate at the same instant</text>
</svg>

*JFR's continuous timeline lets you correlate a GC pause spike with concurrent lock-contention and allocation events at the same moment, rather than examining each in isolation.*

## 5. Runnable example

Scenario: capture and analyze a real JFR recording of a workload with an intermittent anomaly — starting with a basic continuous recording of a normal workload, then introducing a deliberate periodic slowdown and locating it in the recording, then dumping a recording from an already-running process without needing to restart it.

### Level 1 — Basic

```java
public class JfrBaselineWorkload {
    public static void main(String[] args) throws InterruptedException {
        for (int round = 0; round < 30; round++) {
            java.util.List<byte[]> temp = new java.util.ArrayList<>();
            for (int i = 0; i < 10_000; i++) {
                temp.add(new byte[200]);
            }
            System.out.println("round " + round + " complete");
            Thread.sleep(200);
        }
    }
}
```

**How to run:** `java -XX:StartFlightRecording=filename=baseline.jfr,duration=60s JfrBaselineWorkload.java` (JDK 17+).

Expected output:
```
round 0 complete
round 1 complete
...
round 29 complete
```
And, after the run, a `baseline.jfr` file is written to disk — open it with `jmc baseline.jfr` (JDK Mission Control) to see a smooth, unremarkable timeline: small, regular young-generation GC pauses with no anomalies.

This establishes what a "normal," unremarkable JFR timeline looks like — small, evenly-spaced GC events and steady CPU usage, the baseline against which the next example's anomaly will stand out.

### Level 2 — Intermediate

```java
import java.util.*;

public class JfrWithIntermittentAnomaly {
    static final Object lock = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread contender = new Thread(() -> {
            while (true) {
                synchronized (lock) {
                    try { Thread.sleep(150); } catch (InterruptedException ignored) {}
                }
            }
        });
        contender.setDaemon(true);
        contender.start();

        List<byte[]> retained = new ArrayList<>();
        for (int round = 0; round < 30; round++) {
            synchronized (lock) { // contends with 'contender' periodically -- visible as lock contention in JFR
                retained.add(new byte[50_000]);
            }
            System.out.println("round " + round + " complete, retained=" + retained.size());
            Thread.sleep(100);
        }
    }
}
```

**How to run:** `java -XX:StartFlightRecording=filename=anomaly.jfr,duration=60s JfrWithIntermittentAnomaly.java` (JDK 17+), then open `anomaly.jfr` in JMC and inspect the "Lock Instances" / "Java Monitor" view.

Expected observation in JMC:
```
Lock Instances view shows repeated JavaMonitorEnter events on 'lock' with wait
times clustering around 100-150ms, correlated with the main thread's periodic
allocation of retained byte[50000] arrays.
```

The real-world concern added: the background `contender` thread deliberately holds `lock` for 150ms at a time in a tight loop, periodically forcing the main thread's own `synchronized (lock)` block to wait — this is exactly the kind of intermittent, hard-to-reproduce-on-demand contention that a continuous JFR recording captures naturally, since it doesn't require you to have manually triggered a thread dump at precisely the right 100ms window.

### Level 3 — Advanced

```java
public class JfrAttachToRunningProcess {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("PID: " + ProcessHandle.current().pid());
        java.util.List<byte[]> retained = new java.util.ArrayList<>();
        for (int round = 0; round < 100; round++) {
            for (int i = 0; i < 5_000; i++) {
                retained.add(new byte[500]);
            }
            System.out.println("round " + round + ", retained=" + retained.size());
            Thread.sleep(300);
        }
    }
}
```

**How to run:** `java JfrAttachToRunningProcess.java` (JDK 17+, no JFR flags needed at startup), then, in a second terminal, attach live: `jcmd <PID> JFR.start name=live duration=20s filename=live.jfr`, wait 20 seconds, then `jcmd <PID> JFR.dump name=live filename=live.jfr` if needed, and finally open `live.jfr` in JMC.

Expected output shape (first terminal, unaffected by attaching JFR):
```
PID: 52310
round 0, retained=5000
round 1, retained=10000
...
```
And a `live.jfr` file capturing exactly the 20-second window requested, without ever having restarted the process.

The production-flavored hard case: this demonstrates JFR's ability to attach to an *already-running* production process on demand, with no restart and no pre-planned startup flags — exactly the capability needed when a production incident is already in progress and you cannot afford to bounce the service just to start capturing diagnostic data; `jcmd`'s `JFR.start`/`JFR.dump` subcommands make this possible entirely from outside the process.

## 6. Walkthrough

Tracing `JfrWithIntermittentAnomaly.main` end to end, alongside what the resulting recording shows:

1. The daemon thread `contender` starts first and immediately enters an infinite loop: acquire `lock`, sleep 150ms while holding it, release, repeat — this thread runs entirely independently of the main thread's own progress, deliberately creating a recurring window during which `lock` is unavailable to anyone else.
2. The main thread's loop begins; each round, it attempts `synchronized (lock)` to safely append a new `byte[50000]` array to `retained` — but because `contender` frequently already holds `lock` at that moment, the main thread often has to wait, sometimes close to the full 150ms, before it can proceed.
3. Throughout this entire execution, the JFR recording (started via the `-XX:StartFlightRecording` flag at JVM launch) is continuously capturing `jdk.JavaMonitorEnter` events every time any thread has to wait for a monitor it doesn't yet hold — recording both which lock was contended and how long the wait lasted, with no need for you to have anticipated exactly when contention would occur.
4. Simultaneously, the recording also captures ordinary `jdk.GarbageCollection` events as `retained` grows and periodically triggers young-generation collections, and `jdk.ExecutionSample` events sampling what each thread's stack looks like at regular intervals — all of these land in the same recording, on the same shared timeline.
5. After the program finishes (or the recording's configured duration elapses), the `.jfr` file is complete and can be opened in JDK Mission Control, whose "Java Monitor" or "Lock Instances" view directly surfaces the repeated `JavaMonitorEnter` events on `lock`, showing their wait-time distribution clustering right around 100–150ms — precisely matching `contender`'s hold time, giving you a direct, quantified answer (which lock, how often, how long) without needing to have caught the contention live with a manually-timed thread dump.
6. Because JFR's overhead is low enough to leave on by default, this same recording setup — rather than being a one-off diagnostic exercise added only after a problem was already suspected — is exactly the kind of "always-on" continuous recording a real production service would keep running, so that when contention or a GC anomaly does occur, the data covering it is already captured rather than needing to be reproduced after the fact.

## 7. Gotchas & takeaways

> **Gotcha:** JFR's default event set favors low overhead over maximum detail — some deeper event types (very fine-grained allocation-site tracking, for instance) are only enabled under a more verbose "profile" configuration (`-XX:StartFlightRecording=settings=profile`), which carries higher overhead than the default `settings=default`; choose the configuration deliberately based on whether you're running an always-on production recording (favor `default`) or a short, targeted deep-dive session (favor `profile`), rather than assuming one setting fits every situation.

- JFR continuously records detailed JVM and application events (GC pauses, lock contention, execution samples, allocations, and more) into a compact `.jfr` file, with overhead low enough to run in production continuously.
- Unlike a [thread dump](0941-thread-dumps.md) or [heap dump](0940-heap-dumps-analysis.md) (single-instant snapshots), a JFR recording covers a continuous time window, letting you correlate multiple event types happening around the same moment.
- Start recording at JVM launch with `-XX:StartFlightRecording=...`, or attach to an already-running process with `jcmd <pid> JFR.start` / `JFR.dump` — no restart required, which matters during a live incident.
- Analyze recordings with JDK Mission Control (JMC), which visualizes GC, thread, lock-contention, and allocation timelines together, making intermittent or hard-to-reproduce anomalies far easier to locate than with manually-timed dumps.
- A common production pattern is an always-on, rolling-window continuous recording, so diagnostic data covering an incident's lead-up already exists by the time anyone notices the incident.
- See [Java Mission Control (JMC)](0943-java-mission-control-jmc.md) for the companion analysis tool used to open and explore `.jfr` files, and [GC logging](0944-gc-logging.md) for a complementary, simpler, text-based way to track GC behavior specifically.
