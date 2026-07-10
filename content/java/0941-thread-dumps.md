---
card: java
gi: 941
slug: thread-dumps
title: Thread dumps
---

## 1. What it is

A thread dump is a text snapshot of every thread currently running inside a JVM process at one instant: its name, its state (`RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, `TERMINATED`), and its complete stack trace — the exact chain of method calls it's currently in the middle of. It can be triggered with `jcmd <pid> Thread.print`, the older `jstack <pid>`, by sending a JVM process the `SIGQUIT` signal (`kill -3 <pid>` on Unix-like systems, which prints the dump to the process's standard output), or through a monitoring tool's UI. Unlike a [heap dump](0940-heap-dumps-analysis.md), which captures *object* state, a thread dump captures *execution* state — it is the primary tool for diagnosing why an application has become unresponsive, is spinning at high CPU with no apparent progress, or has deadlocked, because it shows you exactly what every thread was doing (or waiting for) at that moment.

## 2. Why & when

Thread dumps are the right tool whenever an application hangs, stalls, or becomes suddenly slow with no corresponding memory-pressure symptoms — the kind of problem where "the process is still running, but nothing useful seems to be happening." Taking one (or, better, several a few seconds apart) reveals patterns that are otherwise invisible from the outside: threads stuck in `BLOCKED` state all waiting on the same lock (contention), a group of threads all `WAITING` on the same condition that never gets signaled (a missed notify), or — most dramatically — a genuine deadlock, which the JVM itself detects and reports explicitly in the dump when two or more threads are each waiting for a lock the other holds. Because thread dumps are cheap and near-instantaneous to capture (unlike heap dumps, they don't require walking the whole object graph), it's standard practice to capture two or three a few seconds apart when diagnosing a hang: if the same threads show the identical stack trace across all of them, they are genuinely stuck (not just momentarily slow), which is the single most useful signal for distinguishing a real deadlock or livelock from ordinary transient contention.

## 3. Core concept

```
jcmd <pid> Thread.print output, per thread:

"pool-1-thread-3" #14 prio=5 os_prio=0 tid=0x... nid=0x... waiting on condition [0x...]
   java.lang.Thread.State: WAITING (parking)
        at jdk.internal.misc.Unsafe.park(...)
        at java.util.concurrent.locks.LockSupport.park(...)
        at java.util.concurrent.LinkedBlockingQueue.take(...)
        at MyWorker.run(MyWorker.java:42)

Key fields: thread name, STATE, and full call stack at the moment of the dump.

Found in Java 8+ automatically at the end of the dump if present:
"Found one Java-level deadlock:"
  ThreadA is waiting to lock <0x...> (held by ThreadB)
  ThreadB is waiting to lock <0x...> (held by ThreadA)
```

The state and stack trace together tell you not just *that* a thread is stuck, but *exactly where* and, usually, *why* — which lock, which queue, which method call is blocking it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads in a classic deadlock: Thread A holds lock 1 and waits for lock 2, while Thread B holds lock 2 and waits for lock 1" >
  <rect x="30" y="40" width="140" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="64" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Thread A: BLOCKED</text>

  <rect x="470" y="40" width="140" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="64" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B: BLOCKED</text>

  <rect x="230" y="20" width="80" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="39" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Lock 1 (held by A)</text>

  <rect x="330" y="70" width="80" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="370" y="89" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Lock 2 (held by B)</text>

  <line x1="170" y1="55" x2="230" y2="35" stroke="#6db33f"/>
  <text x="200" y="20" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">holds</text>
  <line x1="330" y1="85" x2="170" y2="65" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="250" y="105" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">A waits for Lock 2</text>

  <line x1="470" y1="65" x2="410" y2="85" stroke="#6db33f"/>
  <text x="440" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">holds</text>
  <line x1="310" y1="35" x2="470" y2="55" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="400" y="30" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">B waits for Lock 1</text>

  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Neither can ever proceed -- the JVM detects and reports this cycle explicitly in the thread dump</text>
</svg>

*A classic deadlock cycle: each thread holds a lock the other needs, and the JVM's thread dump detects and reports this explicitly.*

## 5. Runnable example

Scenario: reproduce and diagnose a genuine deadlock using real thread-dump tooling — starting with a basic two-thread program that deliberately locks in an inconsistent order, then capturing and reading a thread dump to see the "Found one Java-level deadlock" report, then fixing it by enforcing a consistent lock ordering and confirming the deadlock no longer occurs.

### Level 1 — Basic

```java
public class DeadlockDemo {
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws Exception {
        System.out.println("PID: " + ProcessHandle.current().pid());

        Thread t1 = new Thread(() -> {
            synchronized (lockA) {
                sleepQuietly(200);
                synchronized (lockB) {
                    System.out.println("t1 got both locks");
                }
            }
        }, "Thread-1");

        Thread t2 = new Thread(() -> {
            synchronized (lockB) {
                sleepQuietly(200);
                synchronized (lockA) { // opposite order from t1 -- deadlock risk
                    System.out.println("t2 got both locks");
                }
            }
        }, "Thread-2");

        t1.start();
        t2.start();
        t1.join();
        t2.join();
        System.out.println("done (this line is never reached if deadlocked)");
    }

    static void sleepQuietly(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
```

**How to run:** `java DeadlockDemo.java` (JDK 17+), then in a second terminal (within the 200ms window), run `jcmd <PID> Thread.print`.

Expected output (the program hangs forever; the thread dump reveals why):
```
PID: 51022
(program appears to hang -- neither "t1 got both locks" nor "t2 got both locks" ever prints)
```

Since `t1` locks `lockA` then `lockB` while `t2` locks `lockB` then `lockA`, both threads can simultaneously acquire their first lock and then block forever waiting for the other's — the program never terminates on its own.

### Level 2 — Intermediate

```java
public class DeadlockWithDumpEvidence {
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws Exception {
        System.out.println("PID: " + ProcessHandle.current().pid());
        Thread t1 = new Thread(() -> {
            synchronized (lockA) {
                sleepQuietly(300);
                synchronized (lockB) { System.out.println("t1 done"); }
            }
        }, "Worker-A");
        Thread t2 = new Thread(() -> {
            synchronized (lockB) {
                sleepQuietly(300);
                synchronized (lockA) { System.out.println("t2 done"); }
            }
        }, "Worker-B");
        t1.start(); t2.start();
        t1.join(); t2.join();
    }

    static void sleepQuietly(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
```

**How to run:** `java DeadlockWithDumpEvidence.java`, then `jcmd <PID> Thread.print > dump.txt` while it hangs, and inspect `dump.txt`.

Expected excerpt from `dump.txt`:
```
"Worker-A" #13 prio=5 ... tid=0x... nid=0x... waiting for monitor entry [0x...]
   java.lang.Thread.State: BLOCKED (on object monitor)
        at DeadlockWithDumpEvidence.lambda$main$0(DeadlockWithDumpEvidence.java:8)
        - waiting to lock <0x000000076b418f38> (a java.lang.Object)
        - locked <0x000000076b418f28> (a java.lang.Object)

"Worker-B" #14 prio=5 ... tid=0x... nid=0x... waiting for monitor entry [0x...]
   java.lang.Thread.State: BLOCKED (on object monitor)
        at DeadlockWithDumpEvidence.lambda$main$1(DeadlockWithDumpEvidence.java:13)
        - waiting to lock <0x000000076b418f28> (a java.lang.Object)
        - locked <0x000000076b418f38> (a java.lang.Object)

Found one Java-level deadlock:
=============================
"Worker-A":
  waiting to lock monitor 0x... (object 0x000000076b418f38, a java.lang.Object),
  which is held by "Worker-B"
"Worker-B":
  waiting to lock monitor 0x... (object 0x000000076b418f28, a java.lang.Object),
  which is held by "Worker-A"
```

The real-world concern added: the JVM itself detects the deadlock cycle and reports it explicitly at the end of the dump ("Found one Java-level deadlock") — you don't have to manually trace the "waiting to lock" / "locked" lines yourself to confirm it, though those lines are exactly the raw evidence the JVM's own detection is based on.

### Level 3 — Advanced

```java
public class DeadlockFixedConsistentOrdering {
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws Exception {
        Thread t1 = new Thread(() -> acquireInOrder("Worker-A"), "Worker-A");
        Thread t2 = new Thread(() -> acquireInOrder("Worker-B"), "Worker-B");
        long start = System.nanoTime();
        t1.start(); t2.start();
        t1.join(); t2.join();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("both threads completed without deadlock, elapsed: " + elapsedMs + "ms");
    }

    // BOTH threads always lock lockA THEN lockB -- a consistent global ordering eliminates the cycle.
    static void acquireInOrder(String name) {
        synchronized (lockA) {
            sleepQuietly(100);
            synchronized (lockB) {
                System.out.println(name + " got both locks safely");
            }
        }
    }

    static void sleepQuietly(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
```

**How to run:** `java DeadlockFixedConsistentOrdering.java` (JDK 17+) — this always completes.

Expected output:
```
Worker-A got both locks safely
Worker-B got both locks safely
both threads completed without deadlock, elapsed: 203ms
```

The production-flavored hard case: the fix requires no additional locking primitives or timeout logic — simply enforcing that *every* thread acquires `lockA` before `lockB`, never the reverse, structurally eliminates the circular-wait condition that a deadlock requires; whichever thread gets `lockA` first simply proceeds to `lockB` uncontested while the other genuinely waits (not deadlocks) for `lockA` to be released, exactly the correctness argument a real production fix for this class of bug would rely on.

## 6. Walkthrough

Tracing `DeadlockWithDumpEvidence.main` end to end, alongside the thread dump it produces:

1. `t1` (named `Worker-A`) starts and immediately acquires `lockA`'s monitor, then sleeps for 300ms while still holding it — during this window, it has *not yet* attempted to acquire `lockB`.
2. `t2` (named `Worker-B`), running concurrently, acquires `lockB`'s monitor and similarly sleeps for 300ms while holding it, without yet attempting `lockA`.
3. After roughly 300ms, `Worker-A` wakes and attempts `synchronized (lockB)` — but `lockB` is currently held by `Worker-B`, so `Worker-A` blocks, entering the `BLOCKED` state shown in the dump.
4. At essentially the same moment, `Worker-B` wakes and attempts `synchronized (lockA)` — but `lockA` is held by `Worker-A`, so `Worker-B` also blocks.
5. Neither thread can ever proceed from here: `Worker-A` holds `lockA` and needs `lockB`; `Worker-B` holds `lockB` and needs `lockA` — a genuine circular wait, which is the JVM's precise definition of deadlock, and exactly what running `jcmd <PID> Thread.print` while the program is stuck captures: both threads' stack traces show `BLOCKED (on object monitor)` at the line attempting the second `synchronized` block, with "waiting to lock" pointing at the object the *other* thread's "locked" line confirms it currently holds.
6. The JVM's own deadlock detector, run as part of producing the thread dump, recognizes this exact cycle (thread waits on a lock held by a thread that in turn waits on a lock the first thread holds) and prints the explicit "Found one Java-level deadlock" section — sparing you from having to manually cross-reference the "waiting to lock" / "locked" lines across every thread yourself, though understanding how to do so manually is what lets you diagnose more complex, longer cycles (three or more threads) that the automatic detector still finds but that are easier to double-check by eye once you know the pattern.

## 7. Gotchas & takeaways

> **Gotcha:** a hung thread that is `RUNNABLE` (not `BLOCKED` or `WAITING`) in a thread dump is not evidence of a deadlock — it means the thread is actively executing code (possibly a busy-loop, an infinite loop, or genuinely slow computation), which is a different problem (a livelock or CPU-bound bug) with a different fix; always check the reported *state* before assuming "stuck" means "deadlocked."

- A thread dump captures every thread's name, state, and full call stack at one instant — the primary tool for diagnosing hangs, stalls, contention, and deadlocks, as distinct from a heap dump's object-graph snapshot.
- Capture with `jcmd <pid> Thread.print` (or `jstack <pid>`); taking two or three a few seconds apart and comparing them is the standard way to confirm a thread is genuinely stuck rather than just momentarily slow.
- The JVM automatically detects circular lock-wait cycles and reports them explicitly as "Found one Java-level deadlock," including which thread waits on which lock and which thread currently holds it.
- The classic fix for a lock-ordering deadlock is enforcing a single, globally consistent acquisition order across every thread — if every thread always locks A before B, the circular-wait condition a deadlock requires can never arise.
- A thread reported as `RUNNABLE` is actively executing, not deadlocked — a hang with `RUNNABLE` threads points to a busy-loop or genuinely slow computation, not lock contention.
- See [heap dumps & analysis](0940-heap-dumps-analysis.md) for the complementary tool used when the symptom is memory growth rather than unresponsiveness, and [Java Flight Recorder (JFR)](0942-java-flight-recorder-jfr.md) for continuously recording thread and lock activity over time rather than a single instant.
