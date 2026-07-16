---
card: spring-amqp
gi: 18
slug: batching-batchingrabbittemplate
title: "Batching (BatchingRabbitTemplate)"
---

## 1. What it is

`BatchingRabbitTemplate` wraps a regular `RabbitTemplate` and accumulates individual `send`/`convertAndSend` calls into an internal buffer, flushing them as a single physical AMQP message (containing multiple logical messages concatenated together per a configurable `BatchingStrategy`) once a size threshold, a message count threshold, or a timeout is reached — whichever comes first. On the consuming side, a batch-aware listener container (or a `BatchMessageListener`) unpacks that single physical message back into its individual logical messages before handing them to application code.

## 2. Why & when

You reach for batching specifically when per-message publishing overhead becomes a genuine throughput bottleneck:

- **Publishing a very high volume of small, similarly-structured messages** — sensor readings, log lines, or high-frequency metric events each carry a fixed per-message overhead (network round trip, broker bookkeeping); batching several logical messages into one physical send amortizes that overhead across all of them.
- **Network round-trip latency, not message processing itself, is the actual bottleneck** — if the constraining factor is how many separate publish calls can go out per second rather than raw data volume, reducing the number of physical sends (while keeping the same total logical message count) directly increases achievable throughput.
- **Do not reach for batching by default** — it adds latency (messages wait in the buffer for the batch to fill or the timeout to elapse) and complexity (consumers must be batch-aware); apply it specifically where profiling shows per-message publish overhead is the actual constraint, not preemptively.

## 3. Core concept

Think of unbatched publishing as a delivery van making a separate trip for every single small package, one at a time — reliable, but the van's own travel time between trips dominates when packages are numerous and individually small. Batching is like waiting until either the van is reasonably full or a maximum wait time has passed, then making one trip carrying many packages at once — the per-trip overhead (the van's travel time) is now amortized across many packages instead of paid once per package, at the cost of the first package in a van having to wait for the others before the trip actually happens.

```java
@Bean
public BatchingRabbitTemplate batchingRabbitTemplate(ConnectionFactory connectionFactory) {
    BatchingStrategy batchingStrategy = new SimpleBatchingStrategy(
        50,          // batch up to 50 messages
        4096,        // or 4KB total size, whichever limit hits first
        5000);       // or after 5 seconds, whichever comes first

    TaskScheduler scheduler = new ThreadPoolTaskScheduler();
    ((ThreadPoolTaskScheduler) scheduler).initialize();

    return new BatchingRabbitTemplate(connectionFactory, batchingStrategy, scheduler);
}

// Application code calls convertAndSend exactly as with a normal RabbitTemplate --
// the batching happens transparently underneath.
batchingRabbitTemplate.convertAndSend("metrics.exchange", "metric.reading", reading);
```

Each individual `convertAndSend` call looks identical to non-batched usage; the accumulation and eventual flush into one physical message happen entirely inside the template.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without batching, each logical message is a separate physical send with its own overhead; with batching, several logical messages accumulate in a buffer and are flushed as one physical message once a size, count, or time threshold is reached" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Unbatched</text>
  <rect x="20" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="50" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">send 1</text>
  <rect x="90" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">send 2</text>
  <rect x="160" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="190" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">send 3</text>
  <text x="120" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 physical sends, 3x round-trip overhead</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Batched</text>
  <rect x="340" y="30" width="280" height="30" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="monospace">[msg1][msg2][msg3] -- one physical send</text>
  <text x="480" y="80" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">1 physical send, overhead paid once</text>
</svg>

Round-trip overhead is amortized across every message in the batch, at the cost of the buffering delay.

## 5. Runnable example

The scenario: batching high-frequency sensor readings before publishing, simulated with a plain in-memory buffer standing in for `BatchingRabbitTemplate`'s accumulate-and-flush logic (no real RabbitMQ broker or scheduler needed to demonstrate the threshold-based flush behavior), starting with a basic count-based flush, then adding a size-based flush as an alternative trigger, then adding a timeout-based flush to ensure a partially-filled batch doesn't wait indefinitely.

### Level 1 — Basic

```java
// BatchingDemo.java
import java.util.*;

public class BatchingDemo {
    static List<String> buffer = new ArrayList<>();
    static int maxBatchSize = 3;

    // Stand-in for BatchingRabbitTemplate.convertAndSend: accumulates until the count threshold hits.
    static void convertAndSend(String payload) {
        buffer.add(payload);
        if (buffer.size() >= maxBatchSize) {
            flush();
        }
    }

    static void flush() {
        System.out.println("Flushing batch of " + buffer.size() + " messages as ONE physical send: " + buffer);
        buffer.clear();
    }

    public static void main(String[] args) {
        convertAndSend("reading-1");
        convertAndSend("reading-2");
        convertAndSend("reading-3"); // triggers the flush
    }
}
```

How to run: `java BatchingDemo.java`. Expected output: `Flushing batch of 3 messages as ONE physical send: [reading-1, reading-2, reading-3]` — three logical messages accumulated and sent as a single physical operation once the count threshold was reached.

### Level 2 — Intermediate

```java
// BatchingDemo.java
import java.util.*;

public class BatchingDemo {
    static List<String> buffer = new ArrayList<>();
    static int maxBatchSize = 5;
    static int maxTotalBytes = 30;

    // Real-world concern: batching should flush on whichever threshold is hit FIRST -- count OR
    // total size -- since a batch of few-but-large messages needs the same protection against
    // an unboundedly large single physical send as a batch of many-but-small ones.
    static void convertAndSend(String payload) {
        buffer.add(payload);
        int totalBytes = buffer.stream().mapToInt(String::length).sum();
        if (buffer.size() >= maxBatchSize || totalBytes >= maxTotalBytes) {
            flush(totalBytes >= maxTotalBytes ? "size threshold" : "count threshold");
        }
    }

    static void flush(String reason) {
        System.out.println("Flushing batch of " + buffer.size() + " messages (" + reason + "): " + buffer);
        buffer.clear();
    }

    public static void main(String[] args) {
        convertAndSend("short-1");
        convertAndSend("short-2");
        convertAndSend("this-is-a-much-longer-reading-payload"); // pushes total size over threshold
    }
}
```

How to run: `java BatchingDemo.java`. Expected output: `Flushing batch of 3 messages (size threshold): [short-1, short-2, this-is-a-much-longer-reading-payload]` — the flush triggered by the accumulated byte size crossing its threshold before the count threshold was ever reached, demonstrating the "whichever comes first" behavior between the two limits.

### Level 3 — Advanced

```java
// BatchingDemo.java
import java.util.*;
import java.util.concurrent.*;

public class BatchingDemo {
    static List<String> buffer = new ArrayList<>();
    static int maxBatchSize = 10;
    static int maxTotalBytes = 1000;
    static ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    static ScheduledFuture<?> pendingTimeoutFlush;

    // Production concern: a batch that never fills up (low traffic period) must still flush
    // eventually -- otherwise the first message in an under-filled batch could wait
    // indefinitely, which defeats the purpose for latency-sensitive data. A timeout guarantees
    // a maximum wait even when volume is too low to naturally trigger a count/size flush.
    static synchronized void convertAndSend(String payload) {
        buffer.add(payload);
        int totalBytes = buffer.stream().mapToInt(String::length).sum();

        if (buffer.size() >= maxBatchSize || totalBytes >= maxTotalBytes) {
            if (pendingTimeoutFlush != null) pendingTimeoutFlush.cancel(false);
            flush("count/size threshold");
            return;
        }

        if (pendingTimeoutFlush == null || pendingTimeoutFlush.isDone()) {
            pendingTimeoutFlush = scheduler.schedule(() -> flush("timeout, batch never filled"), 300, TimeUnit.MILLISECONDS);
        }
    }

    static synchronized void flush(String reason) {
        if (buffer.isEmpty()) return;
        System.out.println("Flushing batch of " + buffer.size() + " messages (" + reason + "): " + buffer);
        buffer.clear();
    }

    public static void main(String[] args) throws InterruptedException {
        convertAndSend("reading-1"); // low traffic -- batch will never fill on its own
        convertAndSend("reading-2");

        Thread.sleep(500); // wait long enough for the timeout-based flush to fire
        scheduler.shutdown();
    }
}
```

How to run: `java BatchingDemo.java`. Expected output: `Flushing batch of 2 messages (timeout, batch never filled): [reading-1, reading-2]` — printed after roughly 300ms, since the batch never reached its count or size threshold during this low-traffic window, but the timeout guarantees these two readings still get published within a bounded, predictable delay rather than waiting indefinitely for more traffic to arrive.

## 6. Walkthrough

Trace several logical messages through accumulation, threshold evaluation, and eventual flush.

1. **First `convertAndSend` call**: the very first logical message added to an empty buffer starts a new batching cycle; the template (or, in the example, the timeout scheduling logic) begins tracking accumulated count and size, and starts a timeout clock in case the batch never fills naturally.
2. **Subsequent calls accumulate**: each further `convertAndSend` call adds another logical message to the same in-progress buffer, checking after each addition whether the count or size threshold has now been crossed.
3. **Threshold reached, flush triggered**: the moment either the message-count limit or the total-size limit is reached (whichever comes first), the buffered messages are packed into a single physical `Message` (using the configured `BatchingStrategy` to concatenate them, typically with length-prefixing so the consumer can split them back apart) and published as one physical send.
4. **Timeout as a safety net**: if traffic is too low for the batch to naturally reach its count or size threshold within a reasonable time, the scheduled timeout fires instead, flushing whatever has accumulated so far — ensuring no message waits indefinitely just because volume happened to be low at that moment.
5. **Physical send occurs once**: regardless of which trigger caused the flush, exactly one physical AMQP publish happens for the entire batch, meaning the network round-trip and broker-side bookkeeping overhead is paid once for however many logical messages ended up in that batch.
6. **Consumer-side unpacking**: on the receiving end, a batch-aware listener container recognizes the physical message as a batch (via a header the `BatchingStrategy` sets) and splits it back into individual logical messages, delivering each to the application's listener method exactly as if it had arrived as its own separate message — the batching is, ideally, entirely transparent to the actual message-processing logic.

```
convertAndSend(msg1) -> buffer=[msg1], start timeout clock
convertAndSend(msg2) -> buffer=[msg1,msg2], below thresholds
  [either: threshold reached -> flush immediately]
  [or: timeout elapses first -> flush whatever accumulated]
    -> ONE physical send: [msg1][msg2]...
      -> consumer's batch-aware container splits back into individual messages
```

## 7. Gotchas & takeaways

> **Gotcha:** batching adds latency to every message in the batch except possibly the last one — a message that arrives at the very start of a batching window can sit buffered for the full timeout duration (or until the batch naturally fills) before it's actually sent; for genuinely latency-sensitive messages, this added delay may be unacceptable even though it improves aggregate throughput, so batching is a throughput-versus-latency trade-off, not a pure win.

- Reach for `BatchingRabbitTemplate` only when profiling or load testing shows per-message publish overhead is a genuine bottleneck — for most applications with moderate message volume, the added complexity and latency aren't worth it.
- Configure all three thresholds (count, size, timeout) deliberately — count and size protect against an unboundedly large single physical message, while the timeout protects against messages waiting indefinitely during low-traffic periods.
- Consumers must be explicitly batch-aware (a batch listener container, or logic recognizing the batching header) to correctly unpack a batched physical message back into its individual logical messages — pointing an ordinary, non-batch-aware consumer at a batched producer's queue results in the consumer receiving one large, unparsed blob instead of the expected individual messages.
- Batching is specifically a throughput optimization for high-volume, latency-tolerant message streams (metrics, logs, sensor data) — it is generally the wrong tool for individually significant, latency-sensitive business events like order placements or payment confirmations, where per-message timeliness usually matters more than aggregate publish efficiency.
