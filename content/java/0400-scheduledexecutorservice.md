---
card: java
gi: 400
slug: scheduledexecutorservice
title: ScheduledExecutorService
---

## 1. What it is

`ScheduledExecutorService` extends `ExecutorService` with the ability to run tasks **after a delay** or **repeatedly on a schedule**, instead of only "as soon as possible." Its three main methods are `schedule(task, delay, unit)` (run once, after waiting), `scheduleAtFixedRate(task, initialDelay, period, unit)` (run repeatedly, aiming to start each run at fixed intervals from the *start* time), and `scheduleWithFixedDelay(task, initialDelay, delay, unit)` (run repeatedly, but wait a fixed gap after each run *finishes* before starting the next). You get one via `Executors.newScheduledThreadPool(n)`.

## 2. Why & when

Before `ScheduledExecutorService`, the old way to run something later or repeatedly was `java.util.Timer` with `TimerTask` — but `Timer` uses a single background thread for *all* scheduled tasks, so one slow or misbehaving task (or one that throws an uncaught exception) can delay or silently kill every other scheduled task sharing that timer. `ScheduledExecutorService` fixes both problems: it's backed by a real thread pool (so multiple scheduled tasks can run concurrently), and one task's exception doesn't affect the others.

You reach for it whenever you need "do X once after a delay" (retry a failed operation after a backoff) or "do X repeatedly forever" (a heartbeat, a periodic cache refresh, a health check) — essentially the professional replacement for `Timer`/`TimerTask` and for handwritten `Thread.sleep()`-in-a-loop patterns.

## 3. Core concept

```java
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

scheduler.schedule(() -> System.out.println("Runs once, after 2 seconds"), 2, TimeUnit.SECONDS);

scheduler.scheduleAtFixedRate(
    () -> System.out.println("Tick"), 0, 1, TimeUnit.SECONDS); // every 1s, measured from start times

scheduler.scheduleWithFixedDelay(
    () -> System.out.println("Tock"), 0, 1, TimeUnit.SECONDS); // 1s gap AFTER each run finishes
```

The distinction between the last two matters: if a task under `scheduleAtFixedRate` takes longer than the period, the next run starts immediately after (it doesn't overlap, but it doesn't wait either) — the schedule can "catch up" aggressively. `scheduleWithFixedDelay` instead always waits the full delay *after* the previous run completes, so a slow task naturally spaces out subsequent runs.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="scheduleAtFixedRate measures gaps from start times; scheduleWithFixedDelay measures gaps from each run's end">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#e6edf3" font-size="11" font-family="sans-serif">scheduleAtFixedRate(task, 0, 1s) -- gap measured from START to START</text>
  <rect x="20" y="40" width="60" height="20" fill="#6db33f"/>
  <rect x="100" y="40" width="60" height="20" fill="#6db33f"/>
  <rect x="180" y="40" width="60" height="20" fill="#6db33f"/>
  <line x1="20" y1="70" x2="80" y2="70" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="82" fill="#8b949e" font-size="9" text-anchor="middle">1s</text>
  <line x1="100" y1="70" x2="160" y2="70" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="82" fill="#8b949e" font-size="9" text-anchor="middle">1s</text>

  <text x="20" y="120" fill="#e6edf3" font-size="11" font-family="sans-serif">scheduleWithFixedDelay(task, 0, 1s) -- gap measured from END to next START</text>
  <rect x="20" y="132" width="90" height="20" fill="#79c0ff"/>
  <line x1="110" y1="142" x2="170" y2="142" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="140" y="130" fill="#f85149" font-size="9" text-anchor="middle">always 1s</text>
  <rect x="170" y="132" width="90" height="20" fill="#79c0ff"/>
</svg>

Fixed-rate schedules the next start from the previous start; fixed-delay schedules it from the previous end — they diverge as soon as a task runs long.

## 5. Runnable example

Scenario: a background job that pings a server's `/health` endpoint — the same health-check task, evolved from a single delayed check, through a naive repeating check, to a robust version that handles a slow/failing check and can be cancelled cleanly.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class HealthCheckOnce {
    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

        System.out.println("Scheduling health check...");
        scheduler.schedule(() -> {
            System.out.println("Health check ran at " + System.currentTimeMillis());
        }, 2, TimeUnit.SECONDS);

        scheduler.shutdown();
        scheduler.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java HealthCheckOnce.java`

`schedule(task, 2, TimeUnit.SECONDS)` runs the health check exactly once, after a 2-second delay — useful for a one-off retry-after-backoff, but not yet a recurring monitor.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class HealthCheckRepeating {
    static int checkCount = 0;

    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

        ScheduledFuture<?> handle = scheduler.scheduleAtFixedRate(() -> {
            checkCount++;
            System.out.println("Health check #" + checkCount + " OK");
        }, 0, 1, TimeUnit.SECONDS); // starts immediately, repeats every 1s

        Thread.sleep(3500);          // let it run a few times
        handle.cancel(false);        // stop the recurring schedule
        scheduler.shutdown();
    }
}
```

**How to run:** `java HealthCheckRepeating.java`

`scheduleAtFixedRate` turns the one-off check into a recurring monitor, firing roughly every second; `handle.cancel(false)` stops future runs (letting a currently-running one finish, since we pass `false`) once we've observed enough checks — without ever calling `cancel`, this would run forever.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class HealthCheckRobust {
    static boolean pingServer(int checkNumber) {
        if (checkNumber == 2) throw new RuntimeException("connection reset"); // simulate 1 bad check
        return true;
    }

    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
        AtomicInteger runNumber = new AtomicInteger(0);

        ScheduledFuture<?> handle = scheduler.scheduleWithFixedDelay(() -> {
            int n = runNumber.incrementAndGet();
            try {
                boolean healthy = pingServer(n);
                System.out.println("Check #" + n + ": " + (healthy ? "healthy" : "unhealthy"));
            } catch (RuntimeException e) {
                // A scheduled task that throws uncaught silently stops repeating -- always catch inside the task
                System.out.println("Check #" + n + ": FAILED (" + e.getMessage() + ")");
            }
        }, 0, 500, TimeUnit.MILLISECONDS);

        Thread.sleep(2500);
        handle.cancel(false);
        scheduler.shutdown();
        scheduler.awaitTermination(1, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java HealthCheckRobust.java`

The task body wraps its logic in a `try/catch` — if a scheduled task under `scheduleAtFixedRate`/`scheduleWithFixedDelay` ever throws an uncaught exception, **all future executions silently stop** with no warning, which is a common production bug. Catching exceptions inside the task itself (as shown) keeps the schedule alive even when an individual check fails, so checks 3, 4, and 5 still run after check 2 fails.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `scheduler.scheduleWithFixedDelay(task, 0, 500, TimeUnit.MILLISECONDS)` schedules the health-check task to run first with no initial delay, then repeatedly with a 500ms gap measured from the *end* of one run to the *start* of the next.

The first execution fires almost immediately: `runNumber.incrementAndGet()` returns `1`, `pingServer(1)` returns `true` (the `checkNumber == 2` branch doesn't match), so `"Check #1: healthy"` is printed.

After a 500ms gap, the second execution fires: `n` becomes `2`, and `pingServer(2)` now hits `if (checkNumber == 2)` and throws `RuntimeException("connection reset")`. Because this happens *inside* the `try` block, the `catch (RuntimeException e)` clause catches it right there and prints `"Check #2: FAILED (connection reset)"` — critically, the exception never escapes the scheduled task itself, so `scheduleWithFixedDelay`'s internal machinery sees the task as having completed (from its point of view, without any exception) and schedules the next run normally.

After another 500ms gap, the third execution fires: `n` becomes `3`, `pingServer(3)` returns `true` (no match on `== 2` anymore), printing `"Check #3: healthy"`. The fourth and fifth executions behave the same way, both healthy.

Around the 2.5-second mark, `main`'s `Thread.sleep(2500)` returns, `handle.cancel(false)` stops any further scheduling (letting the current run, if any, finish since `mayInterruptIfRunning` is `false`), and `scheduler.shutdown()` plus `awaitTermination` wind the pool down.

Expected output (five checks over ~2.5 seconds, with check #2 failing but the schedule continuing anyway):
```
Check #1: healthy
Check #2: FAILED (connection reset)
Check #3: healthy
Check #4: healthy
Check #5: healthy
```

## 7. Gotchas & takeaways

> If a task scheduled with `scheduleAtFixedRate` or `scheduleWithFixedDelay` throws an **uncaught exception**, the entire schedule silently stops — no error is printed by default, and no further executions ever happen. Always wrap the task body in `try/catch` if you need it to keep running despite individual failures, exactly like Level 3 above.

- `schedule(task, delay, unit)` runs once, after the given delay.
- `scheduleAtFixedRate` aims for a constant interval between **start** times — if a run takes longer than the period, the next run starts as soon as the previous one finishes (no overlap, but no waiting either).
- `scheduleWithFixedDelay` waits a constant interval after each run **finishes** before starting the next — better when task duration is unpredictable and you don't want runs bunching up.
- `ScheduledExecutorService` uses a real thread pool, unlike the legacy `Timer`/`TimerTask`, so multiple scheduled tasks don't block each other and one task's failure doesn't kill others' schedules.
- Both scheduling methods return a `ScheduledFuture<?>` — call `.cancel(boolean mayInterruptIfRunning)` on it to stop future executions.
