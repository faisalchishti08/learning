---
card: java
gi: 410
slug: cyclicbarrier
title: CyclicBarrier
---

## 1. What it is

`CyclicBarrier` lets a fixed group of threads repeatedly wait for each other at a common point before any of them proceeds — every participant calls `await()`, and none of them return from that call until **all** of them have called it. Unlike `CountDownLatch`, a `CyclicBarrier` is **reusable**: once all threads pass the barrier, it automatically resets and can be used again for the next round. You can also give it an optional `Runnable` "barrier action" that runs once, exactly when the last thread arrives, before anyone is released.

## 2. Why & when

Some computations happen in synchronized **rounds** — several worker threads each compute part of a result, but no one can start round 2 until every thread has finished round 1 (because round 2 depends on all of round 1's results being available). A `CountDownLatch` can express "wait for round 1 to finish" once, but it can't be reset for round 2 without creating a brand-new latch each time and re-coordinating references to it across all threads.

`CyclicBarrier` solves exactly this: the same barrier object is reused round after round automatically. It's the natural fit for parallel algorithms structured in synchronized phases — a multi-threaded simulation stepping forward in lockstep, parallel matrix operations processing in passes, or any "everyone finishes phase N before anyone starts phase N+1" pattern.

## 3. Core concept

```java
import java.util.concurrent.CyclicBarrier;

CyclicBarrier barrier = new CyclicBarrier(3, () -> {
    System.out.println("All 3 threads reached the barrier — starting next phase");
}); // barrier action runs ONCE per round, exactly when the last thread arrives

// Each of 3 worker threads, once per round:
barrier.await(); // blocks until all 3 threads have called await() for this round
// ... all 3 threads now proceed together into the next phase ...
barrier.await(); // can be called again for round 2 — the SAME barrier object resets automatically
```

The barrier action runs on whichever thread happens to be the *last* to arrive — it's a convenient place to do "consolidate everyone's results from this round" work exactly once, without extra coordination.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three worker threads each finish phase 1 and call await; none proceed to phase 2 until all three have arrived at the barrier">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">Phase 1 work (different durations) -&gt; barrier.await() -&gt; Phase 2 (all released together)</text>

  <rect x="30" y="45" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="90" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">T1 phase-1 (fast)</text>
  <rect x="30" y="85" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="120" y="105" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">T2 phase-1 (medium)</text>
  <rect x="30" y="125" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="150" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">T3 phase-1 (slow)</text>

  <line x1="270" y1="60" x2="270" y2="150" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="270" y="170" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">barrier: everyone waits for T3</text>

  <rect x="290" y="45" width="120" height="110" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="350" y="105" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Phase 2 starts for ALL 3 at once</text>
</svg>

Fast threads finish phase 1 early but must wait at the barrier for the slowest one before phase 2 begins for anyone.

## 5. Runnable example

Scenario: a parallel simulation stepping through rounds, where each of 3 worker threads computes its slice of the current step and all must finish before the next step begins — the same simulation, evolved from a single-round barrier, through multiple rounds using the barrier's built-in reuse, to a version with a barrier action and proper handling of a thread that fails mid-round.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class SimulationOneRound {
    public static void main(String[] args) {
        CyclicBarrier barrier = new CyclicBarrier(3);

        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            try {
                Thread.sleep((long) (Math.random() * 200)); // simulate uneven work
                System.out.println(name + " finished step 1");
                barrier.await(); // waits here until all 3 threads arrive
                System.out.println(name + " proceeding to step 2");
            } catch (InterruptedException | BrokenBarrierException e) {
                Thread.currentThread().interrupt();
            }
        };

        new Thread(worker, "worker-1").start();
        new Thread(worker, "worker-2").start();
        new Thread(worker, "worker-3").start();
    }
}
```

**How to run:** `java SimulationOneRound.java`

Even though each worker's simulated step-1 work takes a different, random amount of time, **none** of them print `"proceeding to step 2"` until **all three** have printed `"finished step 1"` — the barrier enforces that synchronization point automatically.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class SimulationMultipleRounds {
    public static void main(String[] args) {
        int rounds = 3;
        CyclicBarrier barrier = new CyclicBarrier(3); // the SAME barrier reused across all rounds

        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            try {
                for (int round = 1; round <= rounds; round++) {
                    Thread.sleep((long) (Math.random() * 100));
                    System.out.println(name + " finished round " + round);
                    barrier.await(); // resets automatically after each round completes
                }
            } catch (InterruptedException | BrokenBarrierException e) {
                Thread.currentThread().interrupt();
            }
        };

        new Thread(worker, "worker-1").start();
        new Thread(worker, "worker-2").start();
        new Thread(worker, "worker-3").start();
    }
}
```

**How to run:** `java SimulationMultipleRounds.java`

The same `barrier` object is reused across all 3 rounds without any manual reset — `CyclicBarrier`'s defining feature. Each round, all 3 threads must arrive before any proceeds to the next round, and this repeats identically for round 2 and round 3.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class SimulationWithActionAndFailure {
    public static void main(String[] args) {
        int rounds = 3;
        CyclicBarrier barrier = new CyclicBarrier(3, () ->
            System.out.println(">>> Round complete for all workers, advancing simulation clock <<<")
        );

        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            try {
                for (int round = 1; round <= rounds; round++) {
                    if (name.equals("worker-2") && round == 2) {
                        throw new RuntimeException("worker-2 crashed mid-round-2");
                    }
                    Thread.sleep((long) (Math.random() * 100));
                    System.out.println(name + " finished round " + round);
                    barrier.await();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (BrokenBarrierException e) {
                System.out.println(name + " found the barrier broken — another thread failed. Aborting.");
            } catch (RuntimeException e) {
                System.out.println(name + ": " + e.getMessage() + " — barrier is now broken for everyone");
                barrier.reset(); // explicitly reset so other threads don't hang forever waiting
            }
        };

        new Thread(worker, "worker-1").start();
        new Thread(worker, "worker-2").start();
        new Thread(worker, "worker-3").start();
    }
}
```

**How to run:** `java SimulationWithActionAndFailure.java`

If a thread that's supposed to call `barrier.await()` fails instead (an exception, or never arriving), the other threads waiting at the barrier don't wait forever — `CyclicBarrier` detects this and throws `BrokenBarrierException` on the *other* waiting threads, or code catching the failure explicitly can call `barrier.reset()` to force the barrier back to a usable state rather than leaving it permanently broken.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `barrier` is created for 3 parties, with a barrier action that prints an "advancing simulation clock" message. Three worker threads start.

**Round 1:** none of the three threads have the `if (name.equals("worker-2") && round == 2)` condition triggered yet (that's specifically for round 2), so all three sleep a random short duration, print `"finished round 1"`, and call `barrier.await()`. Once all three have called `await()`, the barrier action fires exactly once (printing the "advancing simulation clock" line), and then all three `await()` calls return, letting every thread proceed into round 2. The barrier automatically resets for reuse.

**Round 2:** `worker-2` hits `if (name.equals("worker-2") && round == 2)` and immediately throws `RuntimeException("worker-2 crashed mid-round-2")` — critically, this happens *before* `worker-2` calls `barrier.await()` for round 2, so `worker-2` never arrives at the barrier this round. Meanwhile, `worker-1` and `worker-3` finish their round-2 work normally and call `barrier.await()`, then sit blocked, waiting for a third party that will never arrive.

Back in `worker-2`'s thread, the `catch (RuntimeException e)` block catches the crash, prints the crash message, and calls `barrier.reset()`. This forcibly breaks the barrier for anyone currently waiting on it — both `worker-1` and `worker-3`, still blocked in their `await()` calls, immediately have that call throw `BrokenBarrierException` instead of continuing to wait forever. Their `catch (BrokenBarrierException e)` blocks catch this, print an "aborting" message, and their loops end (since the exception is caught outside the `for` loop, ending that thread's participation entirely).

Round 3 never happens for any thread, since the barrier was broken and reset happened outside the normal flow — this demonstrates why a broken barrier must be handled deliberately: without the explicit `reset()` call, `worker-1` and `worker-3` would have blocked at that barrier indefinitely.

Expected output shape (exact interleaving and which round-1 finishes first will vary due to random sleep durations, but the round-2 crash and abort always happen):
```
worker-1 finished round 1
worker-2 finished round 1
worker-3 finished round 1
>>> Round complete for all workers, advancing simulation clock <<<
worker-1 finished round 2
worker-2: worker-2 crashed mid-round-2 — barrier is now broken for everyone
worker-3 finished round 2
worker-1 found the barrier broken — another thread failed. Aborting.
worker-3 found the barrier broken — another thread failed. Aborting.
```

## 7. Gotchas & takeaways

> If **any** participating thread fails to call `await()` (crashes, times out, or is interrupted) before all others arrive, every other thread already waiting at that barrier gets a `BrokenBarrierException` thrown at them — a broken `CyclicBarrier` does not silently hang; it actively signals failure to everyone waiting. Always wrap `await()` in a `try/catch` that handles `BrokenBarrierException` deliberately, and consider whether `reset()` is appropriate to recover.

- Unlike `CountDownLatch`, `CyclicBarrier` automatically resets after all parties pass through, making it reusable across many rounds with the same object.
- The optional barrier-action `Runnable` runs exactly once per round, on whichever thread happens to arrive last — a natural place for "consolidate this round's results" logic.
- `await()` throws `InterruptedException` if the calling thread is interrupted while waiting, and `BrokenBarrierException` if the barrier was broken by another thread's failure (or by an explicit `reset()`).
- Best fit: a fixed, known number of threads that must proceed through synchronized phases together — parallel simulations, multi-pass computations, phase-based algorithms.
- If the number of participants can vary at runtime, or you only need a single synchronization point rather than repeated rounds, `CountDownLatch` is usually the simpler, more appropriate tool.
