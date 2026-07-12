---
card: microservices
gi: 113
slug: point-to-point-queue-messaging
title: "Point-to-point (queue) messaging"
---

## 1. What it is

Point-to-point messaging is a delivery model where each message sent to a queue is consumed by exactly one receiver, even if several receivers are listening on that same queue. It is the messaging equivalent of a single ticket at a deli counter: whichever consumer is free grabs the next message, and no other consumer sees that same message again.

## 2. Why & when

Point-to-point fits work that must happen exactly once per unit of work — processing a single order, charging a single payment, resizing a single uploaded image — where having two different consumers both do that same piece of work would be a bug, not a feature. It is the natural model for distributing a workload across a pool of interchangeable workers so the work gets done once, by whichever worker is available, and the pool can be scaled up or down to handle more or less load.

Reach for [publish/subscribe](0114-publishsubscribe-topic-messaging.md) instead when the same event genuinely needs to be seen by multiple independent consumers doing different things with it (an email service and an analytics service both reacting to the same `OrderPlaced` event) — point-to-point is specifically for when only one consumer, whichever one grabs it, should act.

## 3. Core concept

A queue holds messages in (typically) first-in-first-out order; any number of consumers can attach to the same queue, but the broker hands each message to only one of them, then removes it from the queue once delivered (or acknowledged).

```java
queue.send("ResizeImage:photo42.jpg");
queue.send("ResizeImage:photo43.jpg");

// worker A and worker B both call receive() on the SAME queue,
// but each message goes to only ONE of them
String job = queue.receive(); // worker A might get photo42, worker B might get photo43 -- never both
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer sends messages into a single queue; two workers pull from the same queue but each message is delivered to only one worker">
  <rect x="20" y="80" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Producer</text>

  <rect x="230" y="60" width="180" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Queue</text>
  <rect x="250" y="98" width="30" height="22" fill="#79c0ff" opacity="0.5"/>
  <rect x="290" y="98" width="30" height="22" fill="#79c0ff" opacity="0.5"/>
  <rect x="330" y="98" width="30" height="22" fill="#79c0ff" opacity="0.5"/>

  <rect x="480" y="20" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Worker A</text>
  <rect x="480" y="150" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="175" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Worker B</text>

  <line x1="140" y1="100" x2="228" y2="100" stroke="#8b949e" marker-end="url(#arr3)"/>
  <line x1="410" y1="90" x2="478" y2="45" stroke="#8b949e" marker-end="url(#arr3)"/>
  <line x1="410" y1="110" x2="478" y2="165" stroke="#8b949e" marker-end="url(#arr3)"/>
  <text x="440" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">one msg each,</text>
  <text x="440" y="150" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">never both</text>

  <defs>
    <marker id="arr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each message in the queue is claimed by exactly one worker; the two workers never process the same message.

## 5. Runnable example

Scenario: an image-resizing job queue that starts with one worker draining it, grows to a pool of two competing workers to show that each job still goes to only one of them, and finally adds atomic claiming so concurrent workers can never race for and duplicate-process the same job.

### Level 1 — Basic

```java
// File: SingleWorkerQueue.java -- one producer, one worker, plain point-to-point delivery.
import java.util.concurrent.*;

public class SingleWorkerQueue {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> resizeQueue = new LinkedBlockingQueue<>();
        resizeQueue.put("ResizeImage:photo42.jpg");
        resizeQueue.put("ResizeImage:photo43.jpg");
        resizeQueue.put("ResizeImage:photo44.jpg");

        while (!resizeQueue.isEmpty()) {
            String job = resizeQueue.take();
            System.out.println("[worker-1] processing " + job);
        }
    }
}
```

**How to run:** `javac SingleWorkerQueue.java && java SingleWorkerQueue` (JDK 17+).

With a single worker every job naturally goes to it in order — the point-to-point property is trivially true but not yet interesting.

### Level 2 — Intermediate

```java
// File: CompetingWorkersQueue.java -- two workers pull from the SAME queue; each job goes to exactly one.
import java.util.concurrent.*;

public class CompetingWorkersQueue {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> resizeQueue = new LinkedBlockingQueue<>();
        for (int i = 42; i <= 47; i++) resizeQueue.put("ResizeImage:photo" + i + ".jpg");

        ExecutorService pool = Executors.newFixedThreadPool(2);
        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            String job;
            try {
                while ((job = resizeQueue.poll(200, TimeUnit.MILLISECONDS)) != null) {
                    System.out.println("[" + name + "] processing " + job); // each job printed by exactly ONE worker
                }
            } catch (InterruptedException ignored) { }
        };
        pool.submit(worker);
        pool.submit(worker);
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);
    }
}
```

**How to run:** `javac CompetingWorkersQueue.java && java CompetingWorkersQueue` (JDK 17+).

Both workers call `resizeQueue.poll` on the identical shared queue, but `BlockingQueue`'s internal locking guarantees each element is handed to only one caller — running this repeatedly shows the six jobs split unpredictably but completely between the two workers, never duplicated.

### Level 3 — Advanced

```java
// File: AtomicClaimQueue.java -- explicit atomic claiming with a visible in-flight state,
// modeling how a real broker prevents two workers from ever claiming the same message.
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicClaimQueue {
    record Job(int id, String payload) {}

    static class ClaimableQueue {
        private final BlockingQueue<Job> pending = new LinkedBlockingQueue<>();
        private final Set<Integer> inFlight = ConcurrentHashMap.newKeySet(); // tracks claimed-but-unacked jobs
        private final AtomicInteger claimAttempts = new AtomicInteger();

        void send(Job job) { pending.offer(job); }

        Job claim() throws InterruptedException {
            Job job = pending.take(); // BlockingQueue.take() is itself atomic -- only one thread ever gets a given job
            claimAttempts.incrementAndGet();
            inFlight.add(job.id());
            return job;
        }

        void acknowledge(Job job) { inFlight.remove(job.id()); }
    }

    public static void main(String[] args) throws InterruptedException {
        ClaimableQueue queue = new ClaimableQueue();
        for (int i = 42; i <= 47; i++) queue.send(new Job(i, "photo" + i + ".jpg"));

        Set<Integer> processedBy = ConcurrentHashMap.newKeySet(); // records every job id actually processed
        ExecutorService pool = Executors.newFixedThreadPool(3); // MORE workers than jobs-per-worker, to stress claiming
        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            try {
                Job job;
                while ((job = queue.claim()) != null) {
                    boolean firstTime = processedBy.add(job.id()); // false would mean a DUPLICATE claim happened
                    System.out.println("[" + name + "] claimed job " + job.id() + " (" + job.payload() + "), duplicate=" + !firstTime);
                    queue.acknowledge(job);
                    if (queue.pending.isEmpty()) break;
                }
            } catch (InterruptedException ignored) { }
        };
        pool.submit(worker); pool.submit(worker); pool.submit(worker);
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("Total attempts: " + queue.claimAttempts.get() + ", unique jobs processed: " + processedBy.size());
    }
}
```

**How to run:** `javac AtomicClaimQueue.java && java AtomicClaimQueue` (JDK 17+).

Expected output (order of which worker gets which job varies, but every `duplicate=` is `false`, and the final counts always match):
```
[pool-1-thread-1] claimed job 42 (photo42.jpg), duplicate=false
[pool-1-thread-2] claimed job 43 (photo43.jpg), duplicate=false
...
Total attempts: 6, unique jobs processed: 6
```

## 6. Walkthrough

1. **Level 1** — a single worker drains `resizeQueue` in a simple loop; with only one consumer, point-to-point delivery is indistinguishable from any other queue consumption pattern.
2. **Level 2, two workers on one queue** — both `worker` runnables call `resizeQueue.poll(...)` on the *same* `BlockingQueue` instance; the queue's internal synchronization means each `poll` call atomically removes and returns one element, so no two calls (even concurrent ones from different threads) can ever return the same job.
3. **Level 2, the observable split** — running the program shows each of the six jobs logged exactly once, prefixed by whichever worker happened to win that particular `poll` call — the defining point-to-point behavior, now with genuine concurrency instead of a single consumer.
4. **Level 3, explicit claim tracking** — `ClaimableQueue.claim()` calls the same atomic `take()` under the hood, then additionally records the job in an `inFlight` set and increments `claimAttempts`, modeling how a real broker (e.g., a JMS queue or RabbitMQ) tracks a message as "delivered but not yet acknowledged."
5. **Level 3, the duplicate check** — `processedBy.add(job.id())` returns `false` if that job id was already recorded, which would only happen if two workers had somehow claimed the same job; running this with three competing workers against six jobs and checking every `duplicate=false` is the test that proves the atomicity claim, not just an assertion of it.
6. **Level 3, final tally** — `claimAttempts.get()` (total claims made) and `processedBy.size()` (unique jobs seen) are printed together at the end; for point-to-point delivery to hold, these two numbers must always be equal — if a job were ever double-delivered, `claimAttempts` would exceed `processedBy.size()`.

## 7. Gotchas & takeaways

> **Gotcha:** point-to-point guarantees *at most one worker claims a message at a time*, but if a worker crashes after claiming a message and before acknowledging it (finishing the work), most real brokers will eventually redeliver that message to another worker — so "exactly one worker gets it" is really "exactly one worker gets it *per successful attempt*," and your job processing should be safe to retry; see [message acknowledgement modes](0117-message-acknowledgement-modes.md).

- Point-to-point (queue) messaging delivers each message to exactly one of the consumers listening on that queue, never to more than one.
- It is the natural fit for distributing units of work across a pool of interchangeable workers, since scaling the pool up or down changes throughput without changing correctness.
- It differs fundamentally from [publish/subscribe](0114-publishsubscribe-topic-messaging.md), where every subscriber receives its own copy of the same message.
- The atomicity of "claim" (only one consumer can successfully take a given message) is what a real broker's queue implementation is responsible for guaranteeing under concurrent access.
- Worker crashes between claim and acknowledgement are still possible and are handled by delivery/acknowledgement semantics, not by point-to-point routing itself — see [at-most-once / at-least-once / exactly-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md).
