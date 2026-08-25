# Java Synchronization Primitives

## Overview

Beyond `synchronized` and `volatile`, Java provides high-level coordination tools in `java.util.concurrent`: `CountDownLatch`, `CyclicBarrier`, `Semaphore`, `Exchanger`, and `Phaser`. Each solves a specific thread coordination pattern.

---

## 1. CountDownLatch

### What is it

A one-time countdown. One or more threads wait at `await()` until another thread (or threads) call `countDown()` enough times to reach zero. Not reusable.

### Visual Diagram

```
CountDownLatch(3):
  count = 3

  Thread A: await()  ← blocks
  Thread B: await()  ← blocks

  Worker 1: countDown() → count = 2
  Worker 2: countDown() → count = 1
  Worker 3: countDown() → count = 0 ← RELEASES all waiting threads

  Thread A: resumes
  Thread B: resumes

Use cases:
  - Wait for N services to start before accepting requests
  - Wait for N workers to finish before aggregating results
  - Signal "ready" to all threads simultaneously (count=1)
```

### Example 1 — Wait for Workers to Finish

```java
import java.util.concurrent.*;

public class CountDownLatchDemo {
    public static void main(String[] args) throws InterruptedException {
        int numWorkers = 5;
        CountDownLatch latch = new CountDownLatch(numWorkers);
        int[] results = new int[numWorkers];

        for (int i = 0; i < numWorkers; i++) {
            final int id = i;
            new Thread(() -> {
                try {
                    Thread.sleep((long)(Math.random() * 200));
                    results[id] = id * id; // simulate work
                    System.out.println("Worker " + id + " done");
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    latch.countDown(); // ALWAYS in finally — even on exception
                }
            }).start();
        }

        latch.await(); // main thread waits until all 5 countDown() calls
        System.out.println("All workers done, collecting results...");
        int sum = 0;
        for (int r : results) sum += r;
        System.out.println("Sum of squares: " + sum); // 0+1+4+9+16 = 30
    }
}
```

**What this does:** Main thread blocks at `await()` until all 5 workers call `countDown()`. The `finally` block guarantees `countDown()` is called even if a worker throws.

### Example 2 — Starting Gun Pattern (count=1)

```java
import java.util.concurrent.*;

public class StartingGun {
    public static void main(String[] args) throws InterruptedException {
        CountDownLatch ready = new CountDownLatch(5);  // workers signal ready
        CountDownLatch start = new CountDownLatch(1);  // main signals start

        for (int i = 0; i < 5; i++) {
            final int id = i;
            new Thread(() -> {
                try {
                    ready.countDown();  // tell main: I'm ready
                    start.await();      // wait for starting gun
                    System.out.println("Worker " + id + " started!");
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }).start();
        }

        ready.await();          // wait until all workers ready
        System.out.println("All workers ready — FIRE!");
        start.countDown();      // release all workers simultaneously
    }
}
```

**What this does:** Two-latch pattern: workers signal they're ready, main waits for all, then fires them simultaneously. Classic parallel benchmark setup.

### Dry Run — CountDownLatch(3)

```
State: count=3, waiting=[Thread-A]

t=1: Worker1.countDown() → count=2  (Thread-A still blocked)
t=2: Worker2.countDown() → count=1  (Thread-A still blocked)
t=3: Worker3.countDown() → count=0  → latch opens → Thread-A.await() returns
t=4: Thread-A continues

Note: countdown is irreversible — count can never go back up.
Note: CountDownLatch is NOT reusable. Use CyclicBarrier for reuse.
```

---

## 2. CyclicBarrier

### What is it

A barrier that N threads must all reach before any proceeds. **Reusable** — after all threads pass, the barrier resets for the next cycle. Optional barrier action runs when all threads arrive.

### Visual Diagram

```
CyclicBarrier(3, barrierAction):
  Round 1:
    Thread A: await() → waits
    Thread B: await() → waits
    Thread C: await() → ALL HERE → run barrierAction → all released
  
  Round 2 (barrier auto-resets):
    Thread A: await() → waits
    Thread B: await() → waits
    Thread C: await() → ALL HERE → run barrierAction → all released

vs. CountDownLatch:
  CDL: one-time, countdown from N to 0, different threads can count
  CB:  reusable, N threads must all arrive, then all proceed together
```

### Example 1 — Phased Parallel Computation

```java
import java.util.concurrent.*;

public class CyclicBarrierDemo {
    public static void main(String[] args) throws Exception {
        int numThreads = 3;
        int[] partialResults = new int[numThreads];

        Runnable barrierAction = () -> {
            int total = 0;
            for (int r : partialResults) total += r;
            System.out.println("Phase complete — total: " + total);
        };

        CyclicBarrier barrier = new CyclicBarrier(numThreads, barrierAction);

        for (int i = 0; i < numThreads; i++) {
            final int id = i;
            new Thread(() -> {
                try {
                    for (int phase = 0; phase < 3; phase++) {
                        // Phase work
                        partialResults[id] = (phase + 1) * (id + 1);
                        System.out.println("T" + id + " phase " + phase + " done");
                        barrier.await(); // wait for all threads at this phase
                        // After await: all threads proceed to next phase
                    }
                } catch (Exception e) { e.printStackTrace(); }
            }).start();
        }
    }
}
```

**What this does:** Three threads each compute partial results for three phases. After every phase, all threads synchronize at the barrier — the barrier action aggregates results, then all proceed to the next phase.

> ⚠️ **Pitfall:** If one thread throws an exception while waiting at the barrier, all other waiting threads get `BrokenBarrierException`. Always handle it.

---

## 3. Semaphore

### What is it

Controls access to a limited pool of resources. Maintains a permit count — `acquire()` decrements (blocks if 0), `release()` increments. Can be used as a mutex (1 permit) or to limit concurrent access (N permits).

### Visual Diagram

```
Semaphore(3):  permits = 3  (max 3 concurrent accesses)

Thread 1: acquire() → permits=2, proceeds
Thread 2: acquire() → permits=1, proceeds
Thread 3: acquire() → permits=0, proceeds
Thread 4: acquire() → permits=0, BLOCKS

Thread 1: release() → permits=1
Thread 4: unblocks  → permits=0, proceeds

Use cases:
  - Connection pool (max N DB connections)
  - Rate limiting (max N concurrent requests)
  - Resource-bounded operations (max N file handles)
```

### Example 1 — Connection Pool Simulation

```java
import java.util.concurrent.*;

public class SemaphoreDemo {
    static Semaphore pool = new Semaphore(3); // max 3 concurrent "connections"

    static void useConnection(int threadId) throws InterruptedException {
        pool.acquire(); // blocks if all 3 in use
        try {
            System.out.println("T" + threadId + " acquired connection | available=" + pool.availablePermits());
            Thread.sleep(100); // simulate using connection
        } finally {
            pool.release(); // ALWAYS in finally
            System.out.println("T" + threadId + " released connection");
        }
    }

    public static void main(String[] args) throws Exception {
        ExecutorService exec = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 8; i++) {
            final int id = i;
            exec.submit(() -> {
                try { useConnection(id); }
                catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }
        exec.shutdown();
        exec.awaitTermination(10, TimeUnit.SECONDS);
    }
}
```

**What this does:** 8 threads compete for 3 permits. At most 3 run concurrently; others block in `acquire()`. `release()` in `finally` ensures permits are always returned.

### Example 2 — tryAcquire (Non-Blocking)

```java
import java.util.concurrent.*;

public class TryAcquireDemo {
    public static void main(String[] args) throws InterruptedException {
        Semaphore sem = new Semaphore(2);
        sem.acquire();
        sem.acquire(); // now 0 permits

        // Non-blocking attempt
        boolean got = sem.tryAcquire(); // returns false immediately
        System.out.println("Got permit: " + got); // false

        // Timed attempt
        boolean gotTimed = sem.tryAcquire(100, TimeUnit.MILLISECONDS); // wait up to 100ms
        System.out.println("Got timed permit: " + gotTimed); // false

        sem.release();
        boolean gotAfterRelease = sem.tryAcquire(); // true now
        System.out.println("Got after release: " + gotAfterRelease); // true
    }
}
```

**What this does:** `tryAcquire()` is the non-blocking form — returns immediately. Useful for "try to acquire, do something else if unavailable" patterns, avoiding deadlocks.

---

## 4. Exchanger

### What is it

Two threads swap objects at a synchronization point. Both threads call `exchange(val)` — each blocks until the other arrives, then they swap values.

### Visual Diagram

```
Exchanger<String>

Thread A: exchange("from-A") → blocks
Thread B: exchange("from-B") → both unblock

Thread A receives: "from-B"
Thread B receives: "from-A"

Use case: pipeline stages passing work — producer/consumer swap buffers
```

### Example 1 — Buffer Swap (Producer-Consumer)

```java
import java.util.concurrent.*;
import java.util.*;

public class ExchangerDemo {
    public static void main(String[] args) throws Exception {
        Exchanger<List<Integer>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            try {
                List<Integer> buffer = new ArrayList<>();
                for (int batch = 0; batch < 3; batch++) {
                    buffer.clear();
                    for (int i = 0; i < 5; i++) buffer.add(batch * 5 + i);
                    System.out.println("Producer filled: " + buffer);
                    buffer = exchanger.exchange(buffer); // swap — get empty buffer back
                    System.out.println("Producer got back empty buffer");
                }
            } catch (InterruptedException e) {}
        });

        Thread consumer = new Thread(() -> {
            try {
                List<Integer> buffer = new ArrayList<>();
                for (int batch = 0; batch < 3; batch++) {
                    buffer = exchanger.exchange(buffer); // swap — get full buffer
                    System.out.println("Consumer processing: " + buffer);
                    buffer.clear(); // empty it
                }
            } catch (InterruptedException e) {}
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }
}
```

**What this does:** Double-buffering pattern. Producer fills buffer A; consumer processes buffer B. They swap at the exchange point, avoiding locks during the fill/process phases.

---

## 5. Phaser

### What is it

Flexible, reusable barrier similar to `CyclicBarrier` but supports dynamic registration/deregistration of parties. Supports multiple phases and hierarchical phasers for large-scale coordination.

### Visual Diagram

```
Phaser(3):
  Phase 0: all 3 arrive → advance to Phase 1
  Phase 1: all 3 arrive → advance to Phase 2
  ...

Dynamic: register() adds a party, arriveAndDeregister() removes one

vs. CyclicBarrier:
  CyclicBarrier: fixed N parties, cannot change
  Phaser:        parties can register/deregister between phases
```

### Example 1 — Phased Execution with Deregistration

```java
import java.util.concurrent.*;

public class PhaserDemo {
    public static void main(String[] args) {
        Phaser phaser = new Phaser(1); // 1 = main thread registers

        for (int i = 0; i < 3; i++) {
            final int id = i;
            phaser.register(); // each worker registers
            new Thread(() -> {
                for (int phase = 0; phase < 3; phase++) {
                    System.out.println("Worker " + id + " in phase " + phase);
                    if (phase == 1 && id == 0) {
                        phaser.arriveAndDeregister(); // worker 0 exits after phase 1
                        return;
                    }
                    phaser.arriveAndAwaitAdvance(); // wait for others at this phase
                }
                phaser.arriveAndDeregister(); // done
            }).start();
        }

        // Main orchestrates phases
        for (int phase = 0; phase < 3; phase++) {
            phaser.arriveAndAwaitAdvance(); // main participates in each phase
            System.out.println("=== Phase " + phase + " complete ===");
        }
        phaser.arriveAndDeregister(); // main done
    }
}
```

**What this does:** Worker 0 opts out after phase 1 via `arriveAndDeregister()`. Phaser dynamically adjusts the party count. This is impossible with `CyclicBarrier`.

---

## 6. Comparison Table

```
Primitive        | Reusable | Direction         | Use case
-----------------|----------|-------------------|---------------------------
CountDownLatch   | NO       | N→0, release all  | Wait for N events to happen
CyclicBarrier    | YES      | N arrive, proceed | N threads sync at checkpoint
Semaphore        | YES      | permits pool      | Limit concurrent resource access
Exchanger        | YES      | 2-thread swap     | Exchange data between thread pair
Phaser           | YES      | dynamic parties   | Multi-phase, dynamic participation

Rule of thumb:
  One-shot wait-for-N:      CountDownLatch
  Repeated sync checkpoint: CyclicBarrier
  Resource pool throttle:   Semaphore
  Buffer swap / pipeline:   Exchanger
  Complex multi-phase:      Phaser
```

---

## Quick Reference

```java
// CountDownLatch
CountDownLatch latch = new CountDownLatch(n);
latch.countDown();           // decrement
latch.await();               // block until 0
latch.await(t, unit);        // block with timeout

// CyclicBarrier
CyclicBarrier barrier = new CyclicBarrier(n, action);
barrier.await();             // block until n arrive
barrier.reset();             // manual reset

// Semaphore
Semaphore sem = new Semaphore(n, true); // fair
sem.acquire();               // block until permit
sem.acquire(n);              // acquire n permits
sem.tryAcquire();            // non-blocking
sem.tryAcquire(t, unit);     // timed
sem.release();               // return permit

// Phaser
Phaser phaser = new Phaser(n);
phaser.register();           // add party
phaser.arriveAndAwaitAdvance(); // arrive + wait for others
phaser.arriveAndDeregister(); // arrive + leave
phaser.getPhase();           // current phase number
```
