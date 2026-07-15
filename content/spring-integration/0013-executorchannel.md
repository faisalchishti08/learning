---
card: spring-integration
gi: 13
slug: executorchannel
title: "ExecutorChannel"
---

## 1. What it is

`ExecutorChannel` is a `MessageChannel` implementation that dispatches each message to its subscribed handler on a thread pulled from a configured `TaskExecutor`, rather than on the sender's own thread (as `DirectChannel`, card 0008, does) or via an explicit pull (as `QueueChannel`, card 0010, does). `send()` hands the message off to the executor and returns as soon as the task is submitted — the actual handler invocation happens asynchronously, on whichever pool thread becomes available.

## 2. Why & when

You reach for `ExecutorChannel` specifically when you want asynchronous dispatch with concurrency control, without managing threads by hand:

- **You want the sender to return quickly**, without waiting for handler execution, but you still want dispatch to happen automatically (unlike `QueueChannel`, which needs an explicit `receive()` or poller) — `ExecutorChannel` submits to the pool and returns immediately.
- **Multiple handler invocations should run concurrently**, bounded by a thread pool's size, rather than serially on one thread (`DirectChannel`) or one-at-a-time via a single poller (`QueueChannel` with a default poller) — a pool with, say, 10 threads processes up to 10 messages in parallel.
- **You want to reuse a shared, well-understood concurrency primitive** (`java.util.concurrent.Executor` / Spring's `TaskExecutor` abstraction) for message dispatch, so pool sizing, queuing, and rejection policy are configured the same way you'd configure any other thread pool in the application.

## 3. Core concept

Think of `ExecutorChannel` like a dispatcher at a taxi stand handing each new fare to whichever driver is next in line, rather than the dispatcher personally driving every fare (`DirectChannel`) or fares waiting in a rack until a driver walks over and grabs one (`QueueChannel`). The dispatcher's job — matching a fare to an available driver — happens immediately and automatically; the actual driving (handling) happens on the driver's own time, in parallel with other drivers handling their own fares.

```java
ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
executor.setCorePoolSize(4);
executor.initialize();

ExecutorChannel channel = new ExecutorChannel(executor);
channel.subscribe(message -> {
    System.out.println(Thread.currentThread().getName() + " handling: " + message.getPayload());
});

channel.send(MessageBuilder.withPayload("order-1").build());
// send() returns almost immediately — the handler above runs on a POOL thread, not this one
```

Unlike `QueueChannel`, there's no separate `receive()` step: subscribing a handler to an `ExecutorChannel` is enough for dispatch to happen automatically, exactly like `DirectChannel` — the only difference is which thread runs the handler.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ExecutorChannel submits each message to a thread pool; send() returns immediately while handlers run concurrently on pool threads">
  <rect x="20" y="85" width="120" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">send() caller</text>

  <line x1="140" y1="107" x2="210" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#e1)"/>
  <text x="175" y="92" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">submit + return</text>

  <rect x="220" y="30" width="160" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ExecutorChannel</text>
  <text x="300" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">TaskExecutor pool</text>

  <rect x="235" y="80" width="130" height="24" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="300" y="96" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">thread-1: handling</text>
  <rect x="235" y="112" width="130" height="24" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="300" y="128" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">thread-2: handling</text>
  <rect x="235" y="144" width="130" height="24" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="300" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">thread-3: idle</text>

  <line x1="380" y1="90" x2="450" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e2)"/>
  <line x1="380" y1="122" x2="450" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e2)"/>
  <text x="490" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">handler</text>
  <text x="490" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">handler</text>

  <defs>
    <marker id="e1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="e2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`send()` returns as soon as the pool accepts the task; the same handler instance runs concurrently on multiple pool threads for different messages.

## 5. Runnable example

The scenario: an order-notification channel dispatching to a handler that simulates work, starting with basic async dispatch, then observing true concurrency across multiple messages, and finally handling pool saturation with a bounded queue and rejection policy.

### Level 1 — Basic

```java
// BasicExecutorChannelDemo.java
import org.springframework.integration.channel.ExecutorChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

public class BasicExecutorChannelDemo {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.initialize();

        ExecutorChannel channel = new ExecutorChannel(executor);
        channel.subscribe(message ->
            System.out.println(Thread.currentThread().getName() + " handling: " + message.getPayload()));

        System.out.println("Main thread: " + Thread.currentThread().getName());
        channel.send(MessageBuilder.withPayload("order-1").build());
        System.out.println("send() returned — handler may not have run yet");

        Thread.sleep(200); // let the pool thread finish for demo purposes
        executor.shutdown();
    }
}
```

How to run: `java BasicExecutorChannelDemo.java`. Expected output: the main thread's name is printed, then `send() returned...` typically prints before or interleaved with the handler's line — and the handler's line shows a *different* thread name (e.g. `ThreadPoolTaskExecutor-1`), proving dispatch happened off the sender's thread.

### Level 2 — Intermediate

With a pool of more than one thread, multiple messages sent in quick succession are handled genuinely concurrently, not one at a time — a real difference from `DirectChannel`'s synchronous, single-threaded dispatch.

```java
// ConcurrentDispatchDemo.java
import org.springframework.integration.channel.ExecutorChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import java.util.concurrent.CountDownLatch;

public class ConcurrentDispatchDemo {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.initialize();

        ExecutorChannel channel = new ExecutorChannel(executor);
        CountDownLatch latch = new CountDownLatch(4);

        channel.subscribe(message -> {
            System.out.println(Thread.currentThread().getName() + " START handling " + message.getPayload());
            try { Thread.sleep(200); } catch (InterruptedException ignored) {}
            System.out.println(Thread.currentThread().getName() + " DONE handling " + message.getPayload());
            latch.countDown();
        });

        for (int i = 1; i <= 4; i++) {
            channel.send(MessageBuilder.withPayload("order-" + i).build());
        }
        System.out.println("All 4 sends completed — total elapsed will show below");

        long start = System.currentTimeMillis();
        latch.await();
        System.out.println("All 4 handled in ~" + (System.currentTimeMillis() - start) + "ms (concurrent, not 4x200ms)");
        executor.shutdown();
    }
}
```

How to run: `java ConcurrentDispatchDemo.java`. Expected output shows four different `START handling` lines from four different pool threads appearing close together (not one fully finishing before the next starts), and the total elapsed time is close to 200ms rather than 800ms — proving the four 200ms handler invocations ran in parallel across the 4-thread pool.

### Level 3 — Advanced

A production `ExecutorChannel` needs an explicitly bounded pool and queue, plus a rejection policy, so that a sustained burst beyond capacity fails predictably (via `RejectedExecutionException`, surfaced back through `send()`) rather than growing the pool or its queue without limit.

```java
// SaturatedPoolDemo.java
import org.springframework.integration.channel.ExecutorChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import java.util.concurrent.ThreadPoolExecutor;

public class SaturatedPoolDemo {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(1);
        executor.setMaxPoolSize(1);
        executor.setQueueCapacity(1); // only 1 task may wait beyond the 1 running
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.AbortPolicy()); // fail fast when full
        executor.initialize();

        ExecutorChannel channel = new ExecutorChannel(executor);
        channel.subscribe(message -> {
            try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            System.out.println("Handled: " + message.getPayload());
        });

        int accepted = 0, rejected = 0;
        for (int i = 1; i <= 4; i++) {
            try {
                channel.send(MessageBuilder.withPayload("order-" + i).build());
                accepted++;
                System.out.println("order-" + i + " ACCEPTED (running or queued)");
            } catch (Exception e) {
                rejected++;
                System.out.println("order-" + i + " REJECTED: " + e.getClass().getSimpleName());
            }
        }
        System.out.println("Accepted: " + accepted + ", Rejected: " + rejected);
        Thread.sleep(1200);
        executor.shutdown();
    }
}
```

How to run: `java SaturatedPoolDemo.java`. Expected output: `order-1` accepted (runs immediately), `order-2` accepted (fills the 1-slot queue), and `order-3`/`order-4` rejected with a `MessageDeliveryException` wrapping the pool's rejection — showing `Accepted: 2, Rejected: 2` — demonstrating that a bounded pool applies real, fail-fast backpressure instead of accepting unlimited work.

## 6. Walkthrough

Tracing `SaturatedPoolDemo` in execution order:

1. The `ThreadPoolTaskExecutor` is configured with exactly 1 core/max thread and a queue capacity of 1 — so at most 2 messages can be "in flight" (1 running + 1 queued) at any time.
2. `send()` for `order-1` submits a task to the pool; since no thread is busy, it starts running immediately (and will sleep 500ms). `send()` itself returns right away, having only submitted the task — it prints `order-1 ACCEPTED`.
3. `send()` for `order-2` submits a second task; the single thread is busy with `order-1`, but the queue has room for 1, so it's accepted into the queue and waits — `order-2 ACCEPTED`.
4. `send()` for `order-3` submits a third task; the thread is still busy and the queue is now full (already holding `order-2`), so the executor's `AbortPolicy` rejects it, throwing a `RejectedExecutionException` that `ExecutorChannel` wraps and propagates back out of `send()` — caught and printed as `order-3 REJECTED`.
5. `send()` for `order-4` hits the same full-queue condition and is also rejected.
6. After all four `send()` calls return, the main thread sleeps long enough for the pool to actually process `order-1` (500ms) then `order-2` (another 500ms), printing `Handled: order-1` and `Handled: order-2` — the two accepted messages do eventually get handled, just serially, since the pool only has one thread.

```
capacity: 1 running + 1 queued = 2 in flight max

send(order-1) -> pool: [RUNNING: order-1]                          ACCEPTED
send(order-2) -> pool: [RUNNING: order-1, QUEUED: order-2]          ACCEPTED
send(order-3) -> pool FULL (1 running + 1 queued)                   REJECTED
send(order-4) -> pool FULL                                          REJECTED
... 500ms later: order-1 finishes, order-2 starts running
... 500ms later: order-2 finishes
```

## 7. Gotchas & takeaways

> Because dispatch is asynchronous, an exception thrown inside the handler does **not** propagate back to the original `send()` caller — by the time the handler runs (on a pool thread, potentially much later), the sender has already moved on. Configure an `errorChannel` (or an `ErrorHandler` on the executor) if the caller needs to know about handler failures; silently swallowed exceptions on a saturated or misbehaving pool are a common production surprise.

- `ExecutorChannel` dispatches to subscribed handlers on a `TaskExecutor` pool thread — `send()` returns as soon as the task is submitted, not when the handler finishes, unlike `DirectChannel`'s (card 0008) synchronous dispatch.
- Use it when you want automatic, concurrent, pool-bounded dispatch without managing threads or an explicit poller (contrast with `QueueChannel`, card 0010, which requires a consumer to pull).
- Always bound the pool (`maxPoolSize`) and queue (`queueCapacity`) explicitly in production, and choose a deliberate rejection policy — an unbounded default configuration can silently accept unlimited backlog.
- Handler exceptions do not propagate to the `send()` caller by default; wire up error handling (an `errorChannel`, or a custom `ErrorHandler`) if failures need to be observed.
- Because handlers run concurrently across pool threads, any shared mutable state a handler touches must be thread-safe — a bug that never surfaces with `DirectChannel`'s single-threaded dispatch can appear only under `ExecutorChannel`'s genuine concurrency.
