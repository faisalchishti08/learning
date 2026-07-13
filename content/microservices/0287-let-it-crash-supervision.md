---
card: microservices
gi: 287
slug: let-it-crash-supervision
title: "Let-it-crash / supervision"
---

## 1. What it is

Let-it-crash is a resilience philosophy — popularized by Erlang/OTP and its supervision trees — that says: don't try to anticipate and handle every possible failure mode inside a unit of work; instead, let that unit fail completely and quickly when something unexpected happens, and rely on an external *supervisor* to notice the failure and restart it into a known-good state. Rather than defensive code littered with speculative error handling for conditions that are hard to predict, the unit is kept simple and allowed to die; recovery is the supervisor's job, not the unit's own job.

## 2. Why & when

Code that tries to handle every conceivable failure inline tends to accumulate defensive complexity, and worse, it can mask bugs by continuing to run in a corrupted or inconsistent state that's hard to reason about — a half-broken worker limping along is often more dangerous than one that's cleanly dead. Let-it-crash inverts this: a worker that hits something truly unexpected just dies immediately, taking any corrupted in-process state down with it, and a supervisor restarts a fresh instance from scratch, which is by construction back to a known-good starting state.

This works well specifically because the unit of failure is small and cheap to restart — a single actor, a single worker thread, a single container/pod — and its state (if any needs to survive) lives outside it, in a database or message queue, not only in memory. Use let-it-crash for stateless or externally-persisted workers where a fresh restart is cheap and safe: message consumers, background job processors, container orchestration (Kubernetes restarting a crashed pod is exactly this pattern at the infrastructure level). It is a poor fit for anything holding unrecoverable in-memory state that would be lost on crash with no way to reconstruct it.

## 3. Core concept

A supervisor watches a worker; on an uncaught failure, it restarts the worker instead of trying to recover the worker's internal state.

```java
class Supervisor {
    final java.util.function.Supplier<Runnable> workerFactory;
    int restartCount = 0;
    final int maxRestarts;

    Supervisor(java.util.function.Supplier<Runnable> workerFactory, int maxRestarts) {
        this.workerFactory = workerFactory; this.maxRestarts = maxRestarts;
    }

    void runSupervised() {
        while (restartCount <= maxRestarts) {
            try {
                workerFactory.get().run(); // a fresh worker EVERY restart -- no carried-over broken state
                return; // clean completion
            } catch (Throwable crash) {
                restartCount++;
                System.out.println("Worker crashed (" + crash.getMessage() + "), restarting (" + restartCount + "/" + maxRestarts + ")");
            }
        }
        throw new IllegalStateException("exceeded max restarts, giving up");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A worker runs and hits an unexpected failure, crashing completely rather than attempting to self-heal; a supervisor detects the crash and starts a brand-new worker instance from a known-good state, repeating this cycle up to a maximum restart count">
  <rect x="30" y="30" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">worker (attempt 1)</text>

  <line x1="160" y1="50" x2="230" y2="50" stroke="#8b949e" marker-end="url(#arr287)"/>
  <text x="195" y="40" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">crash</text>

  <rect x="240" y="30" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">supervisor</text>

  <line x1="305" y1="70" x2="95" y2="105" stroke="#8b949e" marker-end="url(#arr287)"/>
  <text x="200" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">restart: fresh instance</text>

  <rect x="30" y="110" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="134" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">worker (attempt 2, clean)</text>

  <defs><marker id="arr287" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The crashed worker is discarded entirely; the supervisor's restart produces a fresh instance rather than repairing the broken one.

## 5. Runnable example

Scenario: a worker that tries to defensively catch and limp along through an unexpected error, ending up in inconsistent state, extended to let it crash cleanly and be supervised with a fresh restart, and finally combining this with a bounded restart count and backoff so a persistently failing worker doesn't restart forever, mirroring how Kubernetes' pod restart policy and CrashLoopBackOff behave.

### Level 1 — Basic

```java
// File: DefensiveLimpingWorker.java -- catches an unexpected error and
// tries to "keep going," but its internal state is now inconsistent,
// producing subtly wrong output on every subsequent operation.
public class DefensiveLimpingWorker {
    static class Worker {
        int processedCount = 0;
        double runningTotal = 0;

        void process(int item) {
            try {
                if (item < 0) throw new IllegalArgumentException("unexpected negative item: " + item);
                runningTotal += item;
                processedCount++;
            } catch (Exception e) {
                // "Handle" it and keep going -- but processedCount and runningTotal
                // may now be silently out of sync with what was actually processed.
                System.out.println("  Caught and ignored: " + e.getMessage() + " (worker limps on)");
            }
        }
    }

    public static void main(String[] args) {
        Worker worker = new Worker();
        int[] items = { 10, 20, -5, 30 }; // an unexpected negative item mid-stream
        for (int item : items) worker.process(item);
        System.out.println("processedCount=" + worker.processedCount + " runningTotal=" + worker.runningTotal
                + " (average would be computed as " + (worker.runningTotal / worker.processedCount) + ")");
    }
}
```

How to run: `java DefensiveLimpingWorker.java`

The worker catches the unexpected negative item and "continues," but it has no real recovery logic — it just swallows the error and moves on. Its counters remain internally consistent by luck in this simple example, but in any worker with more complex, interrelated state, catching an unanticipated error and continuing risks leaving that state in a form nobody explicitly designed for or tested — a subtle, hard-to-detect correctness bug rather than a clean, visible failure.

### Level 2 — Intermediate

```java
// File: LetItCrashWithSupervisor.java -- the worker does NOT try to
// handle the unexpected condition; it throws immediately and dies. A
// supervisor catches the crash and restarts a completely FRESH worker.
public class LetItCrashWithSupervisor {
    static class Worker {
        int processedCount = 0;
        double runningTotal = 0;

        void process(int item) {
            if (item < 0) throw new IllegalStateException("unexpected negative item: " + item); // just DIE
            runningTotal += item;
            processedCount++;
        }
    }

    static class Supervisor {
        int restartCount = 0;
        final int maxRestarts = 3;

        void runSupervised(int[] items) {
            int startIndex = 0;
            while (restartCount <= maxRestarts && startIndex < items.length) {
                Worker worker = new Worker(); // FRESH instance every restart -- no carried-over state
                try {
                    for (int i = startIndex; i < items.length; i++) {
                        worker.process(items[i]);
                        startIndex = i + 1;
                    }
                    System.out.println("Completed cleanly. processedCount=" + worker.processedCount
                            + " runningTotal=" + worker.runningTotal);
                    return;
                } catch (Exception crash) {
                    restartCount++;
                    System.out.println("Worker CRASHED on item at index " + startIndex + ": " + crash.getMessage()
                            + " -- restarting fresh worker (" + restartCount + "/" + maxRestarts + "), skipping bad item");
                    startIndex++; // skip the item that caused the crash, then restart clean
                }
            }
        }
    }

    public static void main(String[] args) {
        new Supervisor().runSupervised(new int[]{ 10, 20, -5, 30 });
    }
}
```

How to run: `java LetItCrashWithSupervisor.java`

The worker throws immediately and completely on the unexpected negative item, rather than trying to handle it inline. The supervisor catches that crash, logs it, skips the offending item, and creates a brand-new `Worker` instance — resetting `processedCount` and `runningTotal` to a known-clean state of 0 — before resuming from the next item. The final printed totals reflect only the items successfully processed by the *current, clean* worker instance, with no risk of carrying forward any inconsistency from the crash.

### Level 3 — Advanced

```java
// File: BoundedRestartsWithBackoff.java -- adds what a real supervisor
// (or Kubernetes' pod restart policy) needs: a maximum restart count so
// a PERSISTENTLY failing worker doesn't restart forever (CrashLoopBackOff),
// plus exponential backoff between restarts to avoid hammering whatever
// resource is causing the crash.
public class BoundedRestartsWithBackoff {
    static class Worker {
        void process(int item) {
            if (item < 0) throw new IllegalStateException("unexpected negative item: " + item);
            System.out.println("  processed: " + item);
        }
    }

    static class Supervisor {
        int restartCount = 0;
        final int maxRestarts = 3;
        long backoffMillis = 100;

        void runSupervised(int[] items) throws InterruptedException {
            int startIndex = 0;
            while (startIndex < items.length) {
                Worker worker = new Worker();
                try {
                    for (int i = startIndex; i < items.length; i++) {
                        worker.process(items[i]);
                        startIndex = i + 1;
                    }
                    System.out.println("Completed cleanly.");
                    return;
                } catch (Exception crash) {
                    restartCount++;
                    if (restartCount > maxRestarts) {
                        System.out.println("GIVING UP: exceeded max restarts (" + maxRestarts
                                + ") -- this item is persistently crashing, needs human intervention");
                        startIndex++; // permanently skip the poison item, don't restart forever
                        restartCount = 0; // reset budget for the NEXT item
                        continue;
                    }
                    System.out.println("Worker CRASHED: " + crash.getMessage()
                            + " -- restart " + restartCount + "/" + maxRestarts
                            + ", backing off " + backoffMillis + "ms before retry");
                    Thread.sleep(backoffMillis);
                    backoffMillis *= 2; // EXPONENTIAL backoff -- avoids hammering a struggling resource
                }
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // Every item is negative -- persistently poisoned data, simulating a truly broken input.
        new Supervisor().runSupervised(new int[]{ -1, -2, -3, -4, 10 });
    }
}
```

How to run: `java BoundedRestartsWithBackoff.java`

The first item, `-1`, crashes the worker every single restart attempt (it's structurally always going to fail — a "poison" item). The supervisor restarts up to `maxRestarts` (3) times with exponentially increasing backoff (100ms, 200ms, 400ms) between attempts, giving whatever transient condition might be causing the crash a chance to resolve. Since this item is *persistently* broken rather than transiently, all 3 restart attempts fail, and the supervisor gives up on that specific item, permanently skips it, resets its restart budget, and moves on to the next item (`-2`, which is also broken and follows the same pattern) — until it finally reaches `10`, which processes successfully. This mirrors Kubernetes' real behavior: a pod that crashes repeatedly gets restarted with exponential backoff, and if it keeps crashing, it enters `CrashLoopBackOff`, signaling that the problem needs human attention rather than infinite automatic restarts.

## 6. Walkthrough

Trace `BoundedRestartsWithBackoff.main` in order. **First**, `runSupervised` is called with `items = {-1, -2, -3, -4, 10}` and `startIndex=0`.

**Attempt 1** creates a fresh `Worker`, enters the `for` loop at `i=0`, and calls `worker.process(-1)`, which immediately throws `IllegalStateException`. This is caught; `restartCount` becomes 1, which is `<= maxRestarts(3)`, so the supervisor prints the crash message, sleeps 100ms, doubles `backoffMillis` to 200, and loops back to the top of the `while`.

**Attempt 2** creates *another* fresh `Worker` (discarding the crashed one entirely — no shared state carries over), and again calls `process(-1)` at the same `startIndex=0` (unchanged since no items were successfully processed). It crashes again; `restartCount` becomes 2, still `<= 3`, backoff sleeps 200ms then becomes 400ms.

**Attempt 3** follows the same pattern: `restartCount` becomes 3, still `<= 3` (the boundary case), backoff sleeps 400ms then becomes 800ms.

**Attempt 4**: `process(-1)` crashes a fourth time; `restartCount` becomes 4, which now exceeds `maxRestarts(3)`. This triggers the `restartCount > maxRestarts` branch: the supervisor prints "GIVING UP," increments `startIndex` to 1 (permanently abandoning item `-1`), resets `restartCount` to 0 (a fresh budget for the *next* item), and `continue`s the outer loop.

**The exact same four-attempt cycle repeats for item `-2`** at `startIndex=1`, then for `-3` at `startIndex=2`, then for `-4` at `startIndex=3` — each poison item burns through its own independent restart budget before being permanently skipped.

**Finally, at `startIndex=4`**, a fresh worker processes item `10` successfully — `process(10)` doesn't throw, the inner `for` loop completes without exception, and `runSupervised` prints "Completed cleanly" and returns.

```
item -1: attempt1 crash -> backoff100ms -> attempt2 crash -> backoff200ms -> attempt3 crash -> backoff400ms -> attempt4 crash -> GIVE UP, skip permanently
item -2: (same 4-attempt cycle, restart budget reset)
item -3: (same 4-attempt cycle)
item -4: (same 4-attempt cycle)
item 10: attempt1 SUCCEEDS -> "Completed cleanly"
```

## 7. Gotchas & takeaways

> Let-it-crash only works safely when the unit of failure holds no unrecoverable state — if a worker's in-memory progress cannot be reconstructed after a crash (no checkpoint, no durable queue position), crashing it loses that progress permanently. Pair let-it-crash with externalized, durable state (a database row, a message queue offset) so a fresh restart can pick up where the crashed instance left off.

- Let-it-crash trades defensive, speculative error-handling code for simplicity: the worker only needs to handle conditions it actually knows how to recover from, and can safely die on everything else.
- A supervisor must bound its restart attempts — unlimited restarting of a persistently failing worker (a "crash loop") wastes resources and can mask a bug that needs human attention, rather than eventually surfacing it.
- Exponential backoff between restarts avoids hammering a struggling downstream resource (e.g., a database that's briefly unavailable) with a tight restart loop that could make the underlying problem worse.
- This pattern operates at multiple levels of a real system simultaneously: application-level supervisors (actor frameworks, message-consumer retry logic) and infrastructure-level supervisors (Kubernetes restarting crashed pods) are the same idea applied at different granularities.
