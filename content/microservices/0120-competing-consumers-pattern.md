---
card: microservices
gi: 120
slug: competing-consumers-pattern
title: "Competing consumers pattern"
---

## 1. What it is

The competing consumers pattern is running multiple instances of the same consumer against one shared [point-to-point queue](0113-point-to-point-queue-messaging.md) so they "compete" for messages — the broker hands each message to exactly one available instance, and adding more instances increases total throughput without any coordination code between the instances themselves.

## 2. Why & when

A single consumer instance can only process messages as fast as one process can go; if messages arrive faster than that, the queue backs up no matter how well-optimized the single consumer's code is. Competing consumers solves this the same way adding more checkout lanes at a store solves a line getting too long: multiple workers pull from the same queue, and because the broker (not the workers) decides who gets which message, there's no need for the workers to talk to each other or coordinate who takes what.

Reach for this pattern whenever a queue's processing rate needs to scale independently of any single consumer instance's capacity — which is most background-job and event-processing workloads. It requires the underlying channel to be point-to-point (queue-style, one consumer per message); pub/sub topics use a related but different scaling mechanism, [consumer groups and partitions](0121-consumer-groups-partitions.md).

## 3. Core concept

Any number of consumer processes attach to the same queue with identical processing logic; the broker's own claim/ack mechanism ensures no two instances ever receive the same message, so instances can be added or removed purely to adjust throughput, with zero code changes and zero coordination.

```java
// N identical worker processes, all pointed at the SAME queue --
// each one just calls receive() in a loop; the broker handles distribution
while (true) {
    Job job = queue.receive(); // broker guarantees only ONE instance gets any given job
    process(job);
    job.ack();
}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One shared queue is drained by three identical competing consumer instances; adding a fourth instance increases throughput without any code change or coordination between instances">
  <rect x="20" y="80" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">resize-jobs</text>
  <text x="95" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">shared queue</text>

  <rect x="260" y="20" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Worker 1</text>
  <rect x="260" y="90" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Worker 2</text>
  <rect x="260" y="160" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="185" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Worker 3</text>

  <line x1="170" y1="105" x2="258" y2="40" stroke="#8b949e" marker-end="url(#arr8)"/>
  <line x1="170" y1="105" x2="258" y2="110" stroke="#8b949e" marker-end="url(#arr8)"/>
  <line x1="170" y1="105" x2="258" y2="180" stroke="#8b949e" marker-end="url(#arr8)"/>

  <rect x="440" y="90" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="515" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ Worker 4 (scale out)</text>

  <defs>
    <marker id="arr8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Any number of identical workers can attach to one queue; the broker splits messages between whichever are currently available.

## 5. Runnable example

Scenario: an image-resize job queue that starts with one worker (a throughput baseline), scales to a pool of competing workers to measure the throughput gain, and finally handles a worker dying mid-run to show the pattern's resilience — surviving workers simply pick up the slack with zero coordination code.

### Level 1 — Basic

```java
// File: SingleWorkerBaseline.java -- one worker, establishing the throughput baseline.
import java.util.concurrent.*;

public class SingleWorkerBaseline {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> jobs = new LinkedBlockingQueue<>();
        for (int i = 1; i <= 12; i++) jobs.put(i);

        long start = System.currentTimeMillis();
        while (!jobs.isEmpty()) {
            int job = jobs.take();
            Thread.sleep(50); // simulated per-job processing cost
        }
        System.out.println("1 worker processed 12 jobs in " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

**How to run:** `javac SingleWorkerBaseline.java && java SingleWorkerBaseline` (JDK 17+).

Expected output (approximately, timing varies): `1 worker processed 12 jobs in 600ms` — twelve jobs at ~50ms each, done strictly one at a time.

### Level 2 — Intermediate

```java
// File: CompetingWorkerPool.java -- the same 12 jobs, now drained by 4 competing workers.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CompetingWorkerPool {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> jobs = new LinkedBlockingQueue<>();
        for (int i = 1; i <= 12; i++) jobs.put(i);

        int numWorkers = 4;
        AtomicInteger[] processedCount = new AtomicInteger[numWorkers];
        for (int i = 0; i < numWorkers; i++) processedCount[i] = new AtomicInteger();

        ExecutorService pool = Executors.newFixedThreadPool(numWorkers);
        long start = System.currentTimeMillis();
        for (int w = 0; w < numWorkers; w++) {
            int workerId = w;
            pool.submit(() -> {
                Integer job;
                try {
                    while ((job = jobs.poll(100, TimeUnit.MILLISECONDS)) != null) {
                        Thread.sleep(50); // identical per-job cost as Level 1
                        processedCount[workerId].incrementAndGet();
                    }
                } catch (InterruptedException ignored) { }
            });
        }
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println(numWorkers + " workers processed 12 jobs in " + (System.currentTimeMillis() - start) + "ms");
        for (int i = 0; i < numWorkers; i++) System.out.println("  worker-" + i + " handled " + processedCount[i].get() + " jobs");
    }
}
```

**How to run:** `javac CompetingWorkerPool.java && java CompetingWorkerPool` (JDK 17+).

Expected output (approximately, timing and per-worker split vary):
```
4 workers processed 12 jobs in 150ms
  worker-0 handled 3 jobs
  worker-1 handled 3 jobs
  worker-2 handled 4 jobs
  worker-3 handled 2 jobs
```

Four competing workers cut total time roughly 4x versus Level 1, with no coordination code between them — each just independently calls `poll` on the same queue, and the queue's own thread-safety guarantees the split.

### Level 3 — Advanced

```java
// File: SurvivingWorkerDeath.java -- one worker "dies" mid-run; the surviving
// competing workers simply absorb its remaining share with zero code changes.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SurvivingWorkerDeath {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> jobs = new LinkedBlockingQueue<>();
        for (int i = 1; i <= 12; i++) jobs.put(i);

        int numWorkers = 4;
        AtomicInteger[] processedCount = new AtomicInteger[numWorkers];
        for (int i = 0; i < numWorkers; i++) processedCount[i] = new AtomicInteger();
        AtomicInteger totalProcessed = new AtomicInteger();

        ExecutorService pool = Executors.newFixedThreadPool(numWorkers);
        for (int w = 0; w < numWorkers; w++) {
            int workerId = w;
            pool.submit(() -> {
                try {
                    if (workerId == 2) { // worker-2 "dies" after processing exactly 1 job
                        Integer job = jobs.poll(100, TimeUnit.MILLISECONDS);
                        if (job != null) { Thread.sleep(50); processedCount[workerId].incrementAndGet(); totalProcessed.incrementAndGet(); }
                        System.out.println("  worker-2 CRASHED after 1 job -- stops pulling from the queue entirely");
                        return; // simulates a crashed process: this worker does nothing more
                    }
                    Integer job;
                    while ((job = jobs.poll(150, TimeUnit.MILLISECONDS)) != null) {
                        Thread.sleep(50);
                        processedCount[workerId].incrementAndGet();
                        totalProcessed.incrementAndGet();
                    }
                } catch (InterruptedException ignored) { }
            });
        }
        pool.shutdown();
        pool.awaitTermination(3, TimeUnit.SECONDS);

        System.out.println("Total jobs completed: " + totalProcessed.get() + " / 12 (all done despite worker-2 dying)");
        for (int i = 0; i < numWorkers; i++) System.out.println("  worker-" + i + " handled " + processedCount[i].get() + " jobs");
    }
}
```

**How to run:** `javac SurvivingWorkerDeath.java && java SurvivingWorkerDeath` (JDK 17+).

Expected output (exact per-worker split varies, but total is always 12):
```
  worker-2 CRASHED after 1 job -- stops pulling from the queue entirely
Total jobs completed: 12 / 12 (all done despite worker-2 dying)
  worker-0 handled 4 jobs
  worker-1 handled 4 jobs
  worker-2 handled 1 jobs
  worker-3 handled 3 jobs
```

## 6. Walkthrough

1. **Level 1** — a single loop calls `jobs.take()` twelve times sequentially, each followed by a 50ms simulated processing cost, so total wall-clock time is roughly 12 × 50ms = 600ms — the ceiling one process alone can achieve.
2. **Level 2, four identical workers** — each of the four submitted tasks runs the *exact same* loop logic, polling the *same* `jobs` queue; none of them know how many other workers exist or coordinate in any way beyond calling `poll` on a shared, thread-safe queue.
3. **Level 2, the throughput result** — because up to four jobs are being processed simultaneously (one per worker thread), the total wall-clock time drops to roughly 150ms — close to a 4x improvement over Level 1 — purely from adding worker instances, with the per-job processing logic completely unchanged.
4. **Level 2, the uneven split** — the per-worker counts don't come out perfectly even (3, 3, 4, 2 in the sample run) because whichever worker happens to call `poll` first, when a job becomes available, wins it; this randomness is expected and harmless, since the pattern only promises total throughput scaling, not perfectly balanced individual worker loads.
5. **Level 3, simulating a crash** — `worker-2`'s task branch processes exactly one job, prints a "CRASHED" message, and then `return`s, meaning it never calls `poll` again for the rest of the run — this models a worker process dying or being killed mid-execution.
6. **Level 3, the other workers unaffected** — `worker-0`, `worker-1`, and `worker-3` continue their identical polling loops completely unaware that `worker-2` stopped; because all four were only ever independently pulling from the same shared queue, the remaining jobs simply get picked up by whichever of the three survivors calls `poll` next.
7. **Level 3, the outcome** — `totalProcessed` still reaches 12 out of 12, proving that no job is lost or left unprocessed just because one competing consumer instance disappeared — the surviving instances absorb the dead one's share automatically, with no explicit failover logic written anywhere in the program.

## 7. Gotchas & takeaways

> **Gotcha:** competing consumers assumes every instance is stateless with respect to which job it gets — if worker instances maintain any kind of in-memory state that depends on receiving a *specific* message (rather than being able to handle any message the queue happens to hand them), the pattern breaks, because there is no way to control or predict which instance any given message goes to.

- Competing consumers scales processing throughput by running multiple identical instances against one shared point-to-point queue, with the broker distributing messages between them.
- Instances require zero coordination with each other — each simply polls the same queue independently, and the broker's own claim guarantee prevents duplicate delivery to different instances.
- Adding or removing instances changes throughput without any code change, making this the standard way to scale background/job-processing workloads horizontally.
- The pattern is inherently resilient to individual instance failure: surviving instances automatically absorb a dead instance's share, since nothing was ever routed specifically *to* that instance.
- This pattern requires point-to-point delivery; scaling consumption of a pub/sub topic instead uses [consumer groups and partitions](0121-consumer-groups-partitions.md), a related but distinct mechanism.
