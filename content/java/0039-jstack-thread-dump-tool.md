---
card: java
gi: 39
slug: jstack-thread-dump-tool
title: jstack — thread dump tool
---

## 1. What it is

**`jstack`** is a JDK command-line tool that prints a snapshot of all thread states inside a running JVM — a **thread dump**. Each thread's name, state (`RUNNABLE`, `WAITING`, `BLOCKED`, `TIMED_WAITING`), and full stack trace is shown. `jstack` works on live processes and on Java core dump files.

```bash
jstack <pid>              # thread dump of a live JVM process
jstack -l <pid>           # include lock/monitor ownership info
jstack -F <pid>           # force dump even if JVM is hung (uses debugger attach)
```

Modern alternative (same output): `jcmd <pid> Thread.print`

## 2. Why & when

`jstack` is the first tool to reach for when diagnosing:
- **Deadlocks** — `jstack` explicitly prints `Found one Java-level deadlock:` with the offending threads.
- **High CPU** — compare two dumps taken seconds apart; threads that appear `RUNNABLE` in the same method in both dumps are the hot-spot.
- **Application hangs** — every thread is `WAITING` or `BLOCKED` → likely lock contention or a missing `notify()`.
- **Thread pool saturation** — all worker threads `BLOCKED` or `WAITING` → pool is exhausted.

It is non-destructive (attaches, reads, detaches) and typically adds < 1 ms pause in production.

## 3. Core concept

Thread states in a dump:

| State | Meaning |
|-------|---------|
| `RUNNABLE` | Thread is executing (or ready, on CPU) |
| `BLOCKED` | Waiting to acquire an intrinsic lock (`synchronized`) |
| `WAITING` | Waiting indefinitely: `Object.wait()`, `LockSupport.park()`, `Thread.join()` |
| `TIMED_WAITING` | Like WAITING but with a timeout: `Thread.sleep()`, `wait(ms)` |
| `TERMINATED` | Thread has finished |

```bash
# Sample output for one thread:
"http-nio-8080-exec-1" #27 daemon prio=5 os_prio=0 cpu=3.50ms elapsed=42.00s tid=0x00007f...
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000007> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:211)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(...)
        at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:435)
        at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1073)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(...)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(...)
        at java.lang.Thread.run(Thread.java:...)
```

Deadlock detection appears at the end of the dump:
```
Found one Java-level deadlock:
=============================
"Thread-1":
  waiting to lock monitor 0x... (object of type Lock-A)
  which is held by "Thread-2"
"Thread-2":
  waiting to lock monitor 0x... (object of type Lock-B)
  which is held by "Thread-1"
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jstack captures thread states from a running JVM and prints them to stdout">
  <rect x="8" y="8" width="664" height="194" rx="8" fill="#0d1117"/>

  <!-- JVM box -->
  <rect x="20" y="25" width="260" height="160" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Running JVM</text>

  <!-- Threads inside -->
  <rect x="35"  y="55" width="110" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="90"  y="65" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Thread-1</text>
  <text x="90"  y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">RUNNABLE</text>

  <rect x="155" y="55" width="110" height="28" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="210" y="65" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Thread-2</text>
  <text x="210" y="76" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">BLOCKED</text>

  <rect x="35"  y="95" width="110" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="90"  y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GC-Thread</text>
  <text x="90"  y="116" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">WAITING</text>

  <rect x="155" y="95" width="110" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="210" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Finalizer</text>
  <text x="210" y="116" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">WAITING</text>

  <rect x="35"  y="135" width="230" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="150" y="145" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">http-nio-exec-3</text>
  <text x="150" y="156" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">TIMED_WAITING (sleeping)</text>

  <!-- jstack attach -->
  <rect x="330" y="75" width="110" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="385" y="99" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">jstack</text>
  <text x="385" y="115" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">-l &lt;pid&gt;</text>

  <!-- arrow: JVM -> jstack -->
  <line x1="280" y1="100" x2="326" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#js1)"/>

  <!-- Output -->
  <rect x="490" y="30" width="170" height="145" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="50" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stdout</text>
  <text x="505" y="68"  fill="#6db33f" font-size="8" font-family="monospace">"Thread-1" RUNNABLE</text>
  <text x="505" y="82"  fill="#8b949e" font-size="8" font-family="monospace">  at work() line 42</text>
  <text x="505" y="96"  fill="#79c0ff" font-size="8" font-family="monospace">"Thread-2" BLOCKED</text>
  <text x="505" y="110" fill="#8b949e" font-size="8" font-family="monospace">  waiting for lock-A</text>
  <text x="505" y="128" fill="#e6edf3" font-size="8" font-family="monospace">Found deadlock:</text>
  <text x="505" y="142" fill="#8b949e" font-size="8" font-family="monospace">  Thread-2 → lock-A</text>
  <text x="505" y="156" fill="#8b949e" font-size="8" font-family="monospace">  Thread-1 → lock-B</text>

  <!-- arrow: jstack -> output -->
  <line x1="440" y1="100" x2="486" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#js2)"/>

  <defs>
    <marker id="js1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="js2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jstack` attaches to the JVM, reads all thread stack frames atomically, detaches, then prints the dump. The JVM continues running — no restart required.

## 5. Runnable example

Scenario: a bank account transfer simulation where two threads deadlock because each holds one lock and waits for the other. Use `jstack` output to find the deadlock.

### Level 1 — Basic

```java
// ThreadDumpBasic.java — print our own thread state programmatically
import java.lang.management.*;
import java.nio.file.*;

public class ThreadDumpBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Thread dump demo ===\n");

        // Show key thread states in this JVM
        ThreadMXBean tmx = ManagementFactory.getThreadMXBean();
        for (ThreadInfo ti : tmx.dumpAllThreads(true, true)) {
            System.out.printf("%-40s %s%n", "\"" + ti.getThreadName() + "\"", ti.getThreadState());
            StackTraceElement[] stack = ti.getStackTrace();
            for (int i = 0; i < Math.min(3, stack.length); i++)
                System.out.println("    at " + stack[i]);
            System.out.println();
        }

        Path jstack = findTool("jstack");
        System.out.println("jstack tool: " + (jstack != null ? jstack : "not found"));
        System.out.println("Command: jstack -l " + ProcessHandle.current().pid());
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java ThreadDumpBasic.java`

`ThreadMXBean.dumpAllThreads(true, true)` is the programmatic equivalent of `jstack -l` — the same data, accessible from within the JVM. The two `true` flags enable locked monitors and locked synchronizers in the output.

### Level 2 — Intermediate

Same bank-transfer scenario: two threads each grab their own account's lock, then try to grab the other's — causing a deadlock.

```java
// ThreadDumpDeadlock.java — create a real deadlock and detect it
import java.lang.management.*;
import java.util.concurrent.*;

public class ThreadDumpDeadlock {

    static final Object LOCK_ACCOUNT_A = new Object();
    static final Object LOCK_ACCOUNT_B = new Object();

    public static void main(String[] args) throws Exception {
        System.out.println("=== Deadlock demo ===");
        System.out.println("PID: " + ProcessHandle.current().pid());
        System.out.println("Run in another terminal: jstack -l " + ProcessHandle.current().pid());
        System.out.println();

        // Thread 1: transfer from A to B → grabs A, waits for B
        Thread t1 = new Thread(() -> {
            synchronized (LOCK_ACCOUNT_A) {
                System.out.println("Thread-1: locked Account-A");
                try { Thread.sleep(100); } catch (InterruptedException e) { return; }
                System.out.println("Thread-1: waiting for Account-B...");
                synchronized (LOCK_ACCOUNT_B) {
                    System.out.println("Thread-1: transfer A→B complete");
                }
            }
        }, "Transfer-A-to-B");

        // Thread 2: transfer from B to A → grabs B, waits for A
        Thread t2 = new Thread(() -> {
            synchronized (LOCK_ACCOUNT_B) {
                System.out.println("Thread-2: locked Account-B");
                try { Thread.sleep(100); } catch (InterruptedException e) { return; }
                System.out.println("Thread-2: waiting for Account-A...");
                synchronized (LOCK_ACCOUNT_A) {
                    System.out.println("Thread-2: transfer B→A complete");
                }
            }
        }, "Transfer-B-to-A");

        t1.start(); t2.start();
        Thread.sleep(500);

        // Detect deadlock programmatically
        ThreadMXBean tmx = ManagementFactory.getThreadMXBean();
        long[] deadlocked = tmx.findDeadlockedThreads();
        if (deadlocked != null) {
            System.out.println("\n*** DEADLOCK DETECTED (same as 'jstack -l' output) ***");
            for (ThreadInfo ti : tmx.getThreadInfo(deadlocked, true, true)) {
                System.out.printf("Thread \"%s\" is BLOCKED%n", ti.getThreadName());
                System.out.printf("  Waiting to lock: %s%n", ti.getLockName());
                System.out.printf("  Lock held by: \"%s\"%n", ti.getLockOwnerName());
            }
        }

        t1.interrupt(); t2.interrupt();
        System.out.println("\nInterrupted deadlocked threads.");
    }
}
```

**How to run:** `java ThreadDumpDeadlock.java`

`ThreadMXBean.findDeadlockedThreads()` returns the thread IDs involved. While the program is paused in deadlock, run `jstack -l <pid>` in another terminal — you will see the same `Found one Java-level deadlock:` section that `jstack` prints.

### Level 3 — Advanced

Same bank-transfer scenario grown to use `ReentrantLock` (a `java.util.concurrent` lock), which `jstack -l` shows differently from `synchronized` blocks, plus a programmatic thread dump saved to a file for archiving.

```java
// ThreadDumpAdvanced.java — deadlock with ReentrantLock + dump-to-file
import java.lang.management.*;
import java.nio.file.*;
import java.util.concurrent.locks.*;
import java.io.*;

public class ThreadDumpAdvanced {

    static final ReentrantLock LOCK_A = new ReentrantLock();
    static final ReentrantLock LOCK_B = new ReentrantLock();

    public static void main(String[] args) throws Exception {
        System.out.println("=== ReentrantLock deadlock + thread dump to file ===");
        long pid = ProcessHandle.current().pid();

        Thread t1 = new Thread(() -> {
            LOCK_A.lock();
            try {
                System.out.println("T1: acquired LOCK_A");
                try { Thread.sleep(100); } catch (InterruptedException e) { return; }
                System.out.println("T1: trying LOCK_B...");
                LOCK_B.lock();
                try { System.out.println("T1: acquired LOCK_B (won't reach here)"); }
                finally { LOCK_B.unlock(); }
            } finally { LOCK_A.unlock(); }
        }, "Transfer-A→B");

        Thread t2 = new Thread(() -> {
            LOCK_B.lock();
            try {
                System.out.println("T2: acquired LOCK_B");
                try { Thread.sleep(100); } catch (InterruptedException e) { return; }
                System.out.println("T2: trying LOCK_A...");
                LOCK_A.lock();
                try { System.out.println("T2: acquired LOCK_A (won't reach here)"); }
                finally { LOCK_A.unlock(); }
            } finally { LOCK_B.unlock(); }
        }, "Transfer-B→A");

        t1.start(); t2.start();
        Thread.sleep(500);

        // Capture thread dump to a file (archiving pattern)
        Path dumpFile = Path.of(System.getProperty("java.io.tmpdir"))
            .resolve("threaddump-" + pid + ".txt");

        try (PrintWriter pw = new PrintWriter(new FileWriter(dumpFile.toFile()))) {
            ThreadMXBean tmx = ManagementFactory.getThreadMXBean();
            pw.println("Thread dump — PID " + pid + " — " + java.time.Instant.now());
            pw.println();

            // All threads
            for (ThreadInfo ti : tmx.dumpAllThreads(true, true)) {
                pw.printf("\"%s\" #%d %s%n", ti.getThreadName(), ti.getThreadId(), ti.getThreadState());
                for (StackTraceElement ste : ti.getStackTrace())
                    pw.println("\tat " + ste);
                for (MonitorInfo mi : ti.getLockedMonitors())
                    pw.println("\t- locked <monitor> " + mi.getClassName());
                for (LockInfo li : ti.getLockedSynchronizers())
                    pw.println("\t- locked <synchronizer> " + li.getClassName());
                pw.println();
            }

            // Deadlock section
            long[] dl = tmx.findDeadlockedThreads();
            if (dl != null) {
                pw.println("Found one Java-level deadlock:");
                for (ThreadInfo ti : tmx.getThreadInfo(dl, true, true)) {
                    pw.printf("  Thread \"%s\": BLOCKED on %s held by \"%s\"%n",
                        ti.getThreadName(), ti.getLockName(), ti.getLockOwnerName());
                }
            }
        }

        System.out.println("\nThread dump written to: " + dumpFile);
        System.out.println("(same content as 'jstack -l " + pid + "')");
        System.out.println();

        // Print deadlock summary to console
        ThreadMXBean tmx = ManagementFactory.getThreadMXBean();
        long[] dl = tmx.findDeadlockedThreads();
        if (dl != null) {
            System.out.println("*** Deadlock detected ***");
            for (ThreadInfo ti : tmx.getThreadInfo(dl, true, true)) {
                System.out.printf("  \"%s\" waiting for lock held by \"%s\"%n",
                    ti.getThreadName(), ti.getLockOwnerName());
                System.out.printf("  Lock: %s%n", ti.getLockName());
            }
        }

        System.out.println("\nFix: always lock in the SAME ORDER in all threads.");
        System.out.println("Lock-ordering protocol: always acquire LOCK_A before LOCK_B.");

        t1.interrupt(); t2.interrupt();
    }
}
```

**How to run:** `java ThreadDumpAdvanced.java`

`ReentrantLock` deadlocks appear in `jstack -l` under `Locked ownable synchronizers` instead of monitor objects. The programmatic dump to a file is the production pattern: write a timed snapshot every N minutes to rolling files for post-incident analysis.

## 6. Walkthrough

Execution trace in `ThreadDumpAdvanced.main`:

**Threads start.** `Transfer-A→B` acquires `LOCK_A` (a `ReentrantLock`). `Transfer-B→A` acquires `LOCK_B`. Both call `Thread.sleep(100)` to ensure the other thread has locked its first lock before either proceeds.

**Deadlock forms.** After 100 ms:
- `Transfer-A→B` calls `LOCK_B.lock()`. `LOCK_B` is held by `Transfer-B→A`. Thread state: `WAITING` (parked inside `LockSupport.park()`).
- `Transfer-B→A` calls `LOCK_A.lock()`. `LOCK_A` is held by `Transfer-A→B`. Thread state: `WAITING`.

Neither can proceed — circular dependency. The JVM does **not** detect this automatically; it only registers it as `WAITING` (not `BLOCKED` — `BLOCKED` is for `synchronized` blocks only).

**`jstack -l` output for `ReentrantLock` deadlock:**
```
"Transfer-A→B" WAITING (parking)
   at sun.misc.Unsafe.park(Native Method)
   - parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
   at java.util.concurrent.locks.LockSupport.park(LockSupport.java:211)
   ...
   Locked ownable synchronizers:
   - <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)  ← LOCK_A held
```

**Programmatic detection.** `ThreadMXBean.findDeadlockedThreads()` returns the IDs of threads involved in deadlock cycles (both `synchronized` and `java.util.concurrent` locks). `getThreadInfo(ids, true, true)` — the two `true`s enable locked monitors and locked synchronizers — provides `getLockName()` and `getLockOwnerName()` per thread.

**Dump file.** The `PrintWriter` loop iterates all threads, printing each thread's stack traces, locked monitors, and locked synchronizers — the same structure `jstack -l` outputs. Rolling this file every minute and keeping 24 hours of history is standard practice for production incident investigation.

**Fix.** Consistent lock ordering: every code path that needs both locks must acquire them in the same sequence (e.g., always `LOCK_A` first, then `LOCK_B`). The deadlock is impossible if only one ordering exists.

## 7. Gotchas & takeaways

> **`BLOCKED` vs `WAITING`** is a critical distinction in a thread dump. `BLOCKED` means waiting for a `synchronized` monitor lock — it appears as `- waiting to lock <0x...>` and `jstack` explicitly names the holding thread. `WAITING` means parked via `LockSupport.park()` (used by `ReentrantLock`, `CountDownLatch`, `Semaphore`) — the lock owner is only visible in `Locked ownable synchronizers` when using `jstack -l`. Always use `-l` flag.

> **Take three dumps, two seconds apart.** A single dump doesn't distinguish "stuck forever" from "briefly waiting." Threads that appear in the same method in all three dumps are truly stuck. Threads that move between dumps are healthy.

- `jstack -l <pid>` — always use `-l` to see `java.util.concurrent` lock ownership.
- `jstack -F <pid>` — forces a dump when the JVM is hung (safe-point cannot be reached); slower, may not show all threads.
- `ThreadMXBean.findDeadlockedThreads()` — detects deadlocks involving `synchronized` AND `ReentrantLock`; null means no deadlock.
- Container PIDs: if running in Docker, PID `1` inside the container maps to the host PID visible in `/proc`. Use `jcmd <pid> Thread.print` from within the container.
- Thread names matter: name your threads (`new Thread(r, "payment-worker-1")`) — `jstack` output becomes instantly readable.
