---
card: java
gi: 854
slug: daemon-vs-user-threads
title: Daemon vs user threads
---

## 1. What it is

Every Java thread is either a **user thread** (the default) or a **daemon thread**, set via `thread.setDaemon(true)` **before** calling `start()` (changing it afterward throws `IllegalThreadStateException`). The distinction determines what keeps the JVM process alive: the JVM continues running as long as **any** user thread is still alive, but exits automatically the moment **only** daemon threads remain, regardless of whether those daemon threads have finished their work. Daemon threads are meant for background support tasks that should never, by their mere existence, prevent the application from shutting down — the JVM's own garbage collector thread is a classic example of an internal daemon thread.

## 2. Why & when

An application with genuine "real work" happening on user threads should keep the JVM running until that work completes — that's the default, and it's correct for most threads most of the time. But some threads exist purely to support other work — a periodic cache-cleanup task, a metrics-reporting heartbeat, a connection-pool idle-timeout monitor — and none of these should be the *reason* the JVM stays alive if every actual piece of application work has already finished. Marking such a thread as a daemon means the JVM can exit cleanly once the real work (on user threads) is done, without needing to explicitly signal every background helper thread to stop first. The critical caveat: daemon threads are terminated **abruptly** when the JVM decides to exit — no guarantee that a `finally` block, a `try`-with-resources close, or any cleanup logic inside that daemon thread actually gets to run. Daemon threads are for work whose incompleteness at shutdown time is genuinely acceptable, never for anything that must complete or clean up reliably.

## 3. Core concept

```java
Thread userThread = new Thread(() -> {
    try { Thread.sleep(2000); } catch (InterruptedException ignored) {}
    System.out.println("user thread finished its 2-second task");
});
// userThread.isDaemon() is false by default -- the JVM will wait for it.

Thread daemonThread = new Thread(() -> {
    while (true) {
        try { Thread.sleep(500); } catch (InterruptedException ignored) { return; }
        System.out.println("daemon heartbeat...");
    }
});
daemonThread.setDaemon(true); // MUST be set before start()
daemonThread.start();
userThread.start();

// If userThread were the ONLY thread besides main and daemonThread, the JVM would exit
// as soon as main() returns and userThread finishes -- daemonThread would be killed mid-loop,
// with no guarantee its current iteration (or any cleanup) completes.
```

`daemonThread`'s infinite loop never naturally terminates on its own — it relies entirely on the JVM's shutdown behavior (or an explicit interrupt) to stop, which is exactly the intended usage pattern for a background daemon.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The JVM stays alive as long as any user thread is running, but exits immediately once only daemon threads remain, abruptly terminating them mid-execution">
  <rect x="40" y="30" width="240" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">user thread (default)</text>
  <text x="160" y="72" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">JVM waits for it to finish</text>

  <rect x="340" y="30" width="240" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="460" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">daemon thread</text>
  <text x="460" y="72" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">killed abruptly when JVM exits</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JVM exits the instant only daemon threads remain — no cleanup guarantee for them</text>
</svg>

*The JVM waits for every user thread but abandons daemon threads instantly once no user threads remain.*

## 5. Runnable example

Scenario: an application with a real background task and a heartbeat monitor, growing from basic daemon-vs-user contrast, through observing the JVM exit abruptly killing a daemon mid-loop, to a cautionary demonstration of why cleanup logic must never rely on a daemon thread finishing gracefully.

### Level 1 — Basic

```java
public class DaemonBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread userThread = new Thread(() -> {
            System.out.println("user thread: default isDaemon() = " + Thread.currentThread().isDaemon());
        });

        Thread daemonThread = new Thread(() -> {
            System.out.println("daemon thread: isDaemon() = " + Thread.currentThread().isDaemon());
        });
        daemonThread.setDaemon(true); // must be set BEFORE start()

        userThread.start();
        daemonThread.start();
        userThread.join();
        daemonThread.join();
    }
}
```

**How to run:** `java DaemonBasic.java` (JDK 17+).

Expected output (order may vary slightly):
```
user thread: default isDaemon() = false
daemon thread: isDaemon() = true
```

Setting daemon status is straightforward — the important behavior difference only becomes visible once the JVM is deciding whether to keep running or exit, which this basic example doesn't yet exercise (since both threads finish quickly and both are joined).

### Level 2 — Intermediate

```java
public class DaemonAbruptTermination {
    public static void main(String[] args) throws InterruptedException {
        Thread heartbeat = new Thread(() -> {
            int beat = 0;
            while (true) {
                beat++;
                System.out.println("heartbeat #" + beat);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    return;
                }
            }
        });
        heartbeat.setDaemon(true);
        heartbeat.start();

        // The "real work" -- a short-lived user thread (main itself counts as a user thread too).
        System.out.println("main thread doing its work...");
        Thread.sleep(350); // simulate ~3-4 heartbeats' worth of "real work" time
        System.out.println("main thread finishing -- JVM will exit now, killing the daemon abruptly");
        // No join() on heartbeat -- main simply returns, and the JVM exits immediately since
        // heartbeat is the ONLY other thread, and it's a daemon.
    }
}
```

**How to run:** `java DaemonAbruptTermination.java`. The exact number of heartbeats printed can vary slightly by timing, but the program always exits immediately once `main` returns, never waiting for `heartbeat` to run any further iterations.

Expected output shape:
```
main thread doing its work...
heartbeat #1
heartbeat #2
heartbeat #3
main thread finishing -- JVM will exit now, killing the daemon abruptly
```

The real-world concern added: `main` returns without ever calling `heartbeat.join()` or otherwise waiting for it — and the JVM exits immediately anyway, since `main` (a user thread) was the only thing keeping the process alive, and `heartbeat` being a daemon means its infinite loop is simply abandoned mid-execution, with no "heartbeat #4" or any further output ever appearing, no matter how the loop's logic might have wanted to continue.

### Level 3 — Advanced

```java
public class DaemonCleanupCaveat {
    public static void main(String[] args) throws InterruptedException {
        Thread daemonWithCleanup = new Thread(() -> {
            try {
                int iteration = 0;
                while (true) {
                    iteration++;
                    System.out.println("daemon working, iteration " + iteration);
                    Thread.sleep(100);
                }
            } finally {
                // THIS IS THE CAVEAT: this finally block is NOT guaranteed to run if the JVM
                // exits because main() finished while this daemon thread was still in its loop.
                System.out.println("daemon cleanup running -- but this line may NEVER print!");
            }
        });
        daemonWithCleanup.setDaemon(true);
        daemonWithCleanup.start();

        System.out.println("main doing brief work...");
        Thread.sleep(250);
        System.out.println("main exiting now -- watch whether the daemon's 'finally' cleanup message appears below");
        // No join(), no interrupt -- main simply returns. The daemon's finally block
        // is abandoned along with everything else, since the JVM does not wait for daemons.
    }
}
```

**How to run:** `java DaemonCleanupCaveat.java`. On virtually every JVM, the `"daemon cleanup running"` message from the `finally` block will **not** appear, because the JVM exits the instant `main` finishes, abandoning the daemon thread mid-`sleep` without ever letting its `finally` block execute.

Expected output shape:
```
main doing brief work...
daemon working, iteration 1
daemon working, iteration 2
main exiting now -- watch whether the daemon's 'finally' cleanup message appears below
```

Notice: the `"daemon cleanup running..."` line from the `finally` block is absent — this is the deliberate point of the example, demonstrating that daemon thread termination bypasses even `finally` blocks, `try`-with-resources cleanup, and any other cleanup mechanism, because the JVM's exit process does not politely unwind daemon threads' call stacks the way a normal method return or exception would.

## 6. Walkthrough

Tracing `DaemonCleanupCaveat.main`:

1. `daemonWithCleanup` is started, marked as a daemon before `start()` was called. Its `run()` method contains a `try { infinite loop } finally { cleanup }` structure — under *normal* circumstances (like an uncaught exception breaking the loop, or the loop returning via some other path), the `finally` block would reliably execute, exactly as `finally` blocks always do for ordinary control flow.
2. `main` sleeps briefly (250ms — roughly 2 heartbeat-loop iterations), then prints its final message and returns.
3. Once `main` returns, the JVM checks: are there any remaining **user** threads still running? `main` itself has just finished; `daemonWithCleanup` is the only other thread, and it's a daemon. Since no user threads remain, the JVM begins its exit process immediately.
4. The JVM's exit process does **not** involve gracefully unwinding daemon threads' stacks — it does not throw an exception into `daemonWithCleanup` to trigger its `finally` block, nor does it wait for the thread's current `Thread.sleep(100)` call to complete. The daemon thread is simply abandoned mid-execution, wherever it happens to be at that exact instant.
5. Consequently, the `finally` block's `System.out.println("daemon cleanup running...")` line never executes — the process terminates before that code ever gets a chance to run, definitively demonstrating that daemon-thread termination is fundamentally different from (and offers none of) the cleanup guarantees normal Java control flow (including exception handling) otherwise provides.

## 7. Gotchas & takeaways

> **Gotcha:** never place cleanup logic that matters (closing a file handle that must be flushed, releasing an external resource, completing a database transaction) inside a daemon thread's `finally` block or shutdown path, expecting it to run reliably — daemon threads can be abandoned by the JVM at any point, with zero cleanup guarantee. If a background task's cleanup genuinely matters, either use a user thread (and ensure it's properly joined or signaled to finish before the application intends to exit) or register a proper JVM shutdown hook (`Runtime.getRuntime().addShutdownHook(...)`), which the JVM does make a best effort to run during a normal (non-forcible) shutdown.

- A thread is a user thread by default; `setDaemon(true)`, called before `start()`, marks it as a daemon instead.
- The JVM continues running as long as any user thread is alive, and exits automatically the instant only daemon threads remain — regardless of whether those daemons have completed their work.
- Daemon threads are terminated abruptly on JVM exit — `finally` blocks, `try`-with-resources cleanup, and any other in-thread cleanup logic are not guaranteed to run.
- Reach for daemon threads specifically for background support tasks whose incompleteness at shutdown time is genuinely acceptable — never for work whose completion or cleanup actually matters.
- For cleanup that must reliably happen at shutdown, use a JVM shutdown hook or a properly joined user thread instead of relying on a daemon thread's own internal cleanup code.
