---
card: java
gi: 887
slug: cyclicbarrier
title: CyclicBarrier
---

## 1. What it is

`CyclicBarrier` is a reusable synchronization point for a fixed number of threads: each thread calls `await()`, and none of them proceed past that point until *all* of them have arrived — at which point every thread is released simultaneously, and the barrier automatically resets, ready to be used again for the next round. Optionally, a barrier action (a `Runnable` passed to the constructor) runs once, on one of the arriving threads, exactly at the moment the last thread arrives and before any thread is released — useful for a step that must happen exactly once between rounds.

## 2. Why & when

Use `CyclicBarrier` whenever a fixed group of threads must repeatedly reach the same point together before any of them continues — parallel simulations that proceed in discrete time steps (every thread must finish computing step N before any of them starts step N+1), or a multi-phase algorithm where each phase depends on every thread having finished the previous one. This is exactly the case where [`CountDownLatch`](0886-countdownlatch.md) falls short, since a latch is single-use — `CyclicBarrier` resets automatically after each round, making it the right tool for anything iterative. The barrier action is useful for aggregating or logging something exactly once per round (like combining each thread's partial result into a shared total) without needing a separate synchronization mechanism just for that one step.

## 3. Core concept

```java
CyclicBarrier barrier = new CyclicBarrier(4, () -> System.out.println("all 4 threads reached the barrier -- advancing"));

// Each of 4 threads, once per round:
computeStepN();
barrier.await(); // blocks until all 4 have called this; barrier action runs once; then all 4 proceed together
computeStepNPlus1();
barrier.await(); // barrier automatically RESET -- reusable for the next round
```

The barrier action runs exactly once per round, on whichever thread happens to be the *last* to call `await()` — not on every thread, and not on a separate dedicated thread.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four threads computing step N at different speeds, all arriving at the barrier, barrier action runs once, all four released together to compute step N+1, barrier resets automatically">
  <rect x="20" y="20" width="130" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T1: step N (fast)</text>
  <rect x="20" y="55" width="130" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="85" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T2: step N (slow)</text>
  <rect x="20" y="90" width="130" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T3: step N (medium)</text>
  <rect x="20" y="125" width="130" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="145" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T4: step N (medium)</text>

  <rect x="260" y="60" width="120" height="50" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="320" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">BARRIER</text>
  <text x="320" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">waits for all 4</text>

  <line x1="150" y1="35" x2="256" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a22)"/>
  <line x1="150" y1="70" x2="256" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a22)"/>
  <line x1="150" y1="105" x2="256" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a22)"/>
  <line x1="150" y1="140" x2="256" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a22)"/>

  <rect x="460" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">all 4 released together</text>
  <text x="535" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">barrier auto-resets</text>
  <line x1="380" y1="85" x2="456" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a22)"/>

  <defs><marker id="a22" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The slowest thread determines when the barrier opens; all four are released at once, and the barrier is immediately ready for the next round.*

## 5. Runnable example

Scenario: a simple multi-phase simulation where several threads must complete each phase before any proceeds to the next, growing from an unsynchronized (buggy) version, to a correct `CyclicBarrier` per-phase, to a version using the barrier action to aggregate each phase's results and using `BrokenBarrierException` handling for robustness.

### Level 1 — Basic

```java
public class UnsynchronizedPhases {
    static void computePhase(int workerId, int phase) {
        try { Thread.sleep((workerId + 1) * 20L); } catch (InterruptedException ignored) {}
        System.out.println("worker " + workerId + " finished phase " + phase);
    }

    public static void main(String[] args) throws InterruptedException {
        int workers = 3;
        Thread[] threads = new Thread[workers];
        for (int w = 0; w < workers; w++) {
            final int id = w;
            threads[w] = new Thread(() -> {
                for (int phase = 1; phase <= 2; phase++) {
                    computePhase(id, phase); // NOTHING stops a fast worker from racing ahead to phase 2
                    // before a slow worker has even finished phase 1 -- phases are NOT actually synchronized
                }
            });
            threads[w].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("done -- but phase 1 and phase 2 work may have interleaved incorrectly");
    }
}
```

**How to run:** `java UnsynchronizedPhases.java` (JDK 17+).

Expected output shape (a fast worker's "phase 2" can print before a slow worker's "phase 1" — phases aren't actually kept in lockstep):
```
worker 0 finished phase 1
worker 0 finished phase 2
worker 1 finished phase 1
worker 2 finished phase 1
worker 1 finished phase 2
worker 2 finished phase 2
done -- but phase 1 and phase 2 work may have interleaved incorrectly
```

If phase 2's logic actually depends on *every* worker's phase 1 results being ready (a common real requirement in simulations), this unsynchronized version is simply incorrect — nothing enforces that ordering.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class CyclicBarrierPhases {
    static void computePhase(int workerId, int phase) {
        try { Thread.sleep((workerId + 1) * 20L); } catch (InterruptedException ignored) {}
        System.out.println("worker " + workerId + " finished phase " + phase);
    }

    public static void main(String[] args) throws InterruptedException {
        int workers = 3;
        CyclicBarrier barrier = new CyclicBarrier(workers,
            () -> System.out.println("--- all workers finished this phase, advancing ---"));

        Thread[] threads = new Thread[workers];
        for (int w = 0; w < workers; w++) {
            final int id = w;
            threads[w] = new Thread(() -> {
                try {
                    for (int phase = 1; phase <= 2; phase++) {
                        computePhase(id, phase);
                        barrier.await(); // blocks until ALL 3 workers finish this phase, then all proceed together
                    }
                } catch (InterruptedException | BrokenBarrierException e) {
                    Thread.currentThread().interrupt();
                }
            });
            threads[w].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("done -- phases were correctly kept in lockstep");
    }
}
```

**How to run:** `java CyclicBarrierPhases.java`.

Expected output shape (every worker's "phase 1" line, in some order, is guaranteed to appear before any worker's "phase 2" line):
```
worker 0 finished phase 1
worker 1 finished phase 1
worker 2 finished phase 1
--- all workers finished this phase, advancing ---
worker 0 finished phase 2
worker 1 finished phase 2
worker 2 finished phase 2
--- all workers finished this phase, advancing ---
done -- phases were correctly kept in lockstep
```

The real-world concern added: `barrier.await()` after each phase guarantees no worker starts phase 2 until every worker has finished phase 1 — the barrier action prints a clear marker each time all three converge, and the same barrier instance is automatically reused for the second round without any extra setup.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AggregatingBarrierAction {
    static int computePartial(int workerId, int phase) {
        try { Thread.sleep((workerId + 1) * 15L); } catch (InterruptedException ignored) {}
        return (workerId + 1) * phase; // each worker's contribution for this phase
    }

    public static void main(String[] args) throws InterruptedException {
        int workers = 4;
        AtomicInteger[] partials = new AtomicInteger[workers];
        for (int i = 0; i < workers; i++) partials[i] = new AtomicInteger(0);
        AtomicInteger phaseTotal = new AtomicInteger(0);

        // Barrier action: runs ONCE per round, aggregating every worker's partial result.
        CyclicBarrier barrier = new CyclicBarrier(workers, () -> {
            int sum = 0;
            for (AtomicInteger p : partials) sum += p.get();
            phaseTotal.set(sum);
            System.out.println("phase total = " + sum);
        });

        Thread[] threads = new Thread[workers];
        for (int w = 0; w < workers; w++) {
            final int id = w;
            threads[w] = new Thread(() -> {
                for (int phase = 1; phase <= 3; phase++) {
                    int result = computePartial(id, phase);
                    partials[id].set(result); // publish this worker's result BEFORE hitting the barrier
                    try {
                        barrier.await(); // barrier action reads ALL partials only after every worker has published
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    } catch (BrokenBarrierException e) {
                        System.out.println("barrier broken -- a worker was likely interrupted or timed out");
                        return;
                    }
                }
            });
            threads[w].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("final phase total = " + phaseTotal.get());
    }
}
```

**How to run:** `java AggregatingBarrierAction.java`.

Expected output:
```
phase total = 10
phase total = 20
phase total = 30
final phase total = 30
```

This adds the production-flavored hard case: using the barrier action itself to safely aggregate every worker's per-phase contribution, exactly once per round — since the barrier action runs *after* all workers have called `await()` (meaning every `partials[id].set(result)` write has already happened and is guaranteed visible), the aggregation never reads a stale or partially-updated value, and `BrokenBarrierException` is handled explicitly in case a worker is interrupted mid-wait, which would otherwise leave the remaining workers permanently stuck.

## 6. Walkthrough

Tracing one round of `AggregatingBarrierAction.main` (phase 1):

1. Each of the four worker threads calls `computePartial(id, 1)`, sleeping for a worker-specific duration and computing its own contribution — worker 0 computes `1*1=1`, worker 1 computes `2*1=2`, worker 2 computes `3*1=3`, worker 3 computes `4*1=4`.
2. Each worker stores its result into `partials[id]` **before** calling `barrier.await()` — this ordering is essential: the barrier's internal synchronization guarantees that by the time the barrier action runs, every worker's write to its own `partials` slot has already happened and is visible.
3. As each worker finishes its own phase-1 computation and calls `barrier.await()`, it blocks — until the fourth and final worker also calls `await()`.
4. The instant the last worker arrives, the barrier action (passed to the constructor) runs exactly once, on that last-arriving worker's thread: it sums all four `partials` values (1+2+3+4 = 10) into `phaseTotal`, and prints `"phase total = 10"`.
5. Only after the barrier action finishes are all four blocked `await()` calls released simultaneously — every worker proceeds to phase 2's iteration of the loop at essentially the same moment.
6. This exact sequence (compute, publish, await, aggregate, release) repeats automatically for phases 2 and 3, since `CyclicBarrier` resets itself after each successful round with no additional setup required — producing phase totals of 20 (2+4+6+8) and 30 (3+6+9+12) respectively.
7. After all three phases complete and every thread's loop finishes, `main`'s `join()` calls return, and the final printed total (30) reflects the last phase's aggregated value, confirming the whole three-round pipeline executed correctly in lockstep.

## 7. Gotchas & takeaways

> **Gotcha:** if any single thread waiting on the barrier is interrupted, or if `await(timeout)` times out for any one of them, the barrier becomes **broken** — every other thread's `await()` call (even ones that would otherwise have completed normally) immediately throws `BrokenBarrierException`. A `CyclicBarrier` used for genuinely critical coordination needs a real strategy for this failure mode, not just a best-effort catch block.

- `CyclicBarrier` blocks a fixed number of threads until all of them arrive, then releases them all together and automatically resets for reuse — unlike the single-use [`CountDownLatch`](0886-countdownlatch.md).
- The optional barrier action runs exactly once per round, on whichever thread happens to be the last to arrive — useful for aggregating results or logging a checkpoint between rounds.
- Publish each thread's per-round contribution *before* calling `await()`, so the barrier action (or any code after the barrier) can safely read every thread's value without a race.
- A broken barrier (due to interruption or timeout of any single waiting thread) propagates `BrokenBarrierException` to every other thread waiting on it — handle this explicitly if the coordination is critical to correctness.
- Use `CyclicBarrier` for a fixed, known group of peer threads synchronizing repeatedly; use [`Phaser`](0889-phaser.md) instead if the number of participating threads can change between phases.
