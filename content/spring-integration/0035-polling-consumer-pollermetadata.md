---
card: spring-integration
gi: 35
slug: polling-consumer-pollermetadata
title: "Polling consumer & PollerMetadata"
---

## 1. What it is

A polling consumer is an endpoint that actively pulls messages from a pollable channel (`QueueChannel`, card 0010, and its relatives) on a schedule, rather than being pushed to automatically. `PollerMetadata` (usually configured via `@Poller` on an endpoint annotation) is the configuration object controlling exactly how that polling behaves — how often to poll, how many messages to take per poll cycle, and what triggers a poll at all (a fixed interval, a fixed delay, or a full cron expression).

## 2. Why & when

You reach for a polling consumer, and tune its `PollerMetadata`, specifically when an endpoint's input channel doesn't push messages to it automatically:

- **The input channel is a `QueueChannel` (or another pollable-only channel type)**, which has no built-in mechanism to notify subscribers when something arrives — a poller is what actively checks the channel on a schedule and delivers whatever it finds to the endpoint.
- **You want explicit control over processing rate**, independent of how fast messages actually arrive — a poller with a fixed interval processes at a steady pace even during a burst, naturally applying backpressure by simply not checking again until its next scheduled tick.
- **You want batch-style processing** — pulling and processing several messages together per poll cycle (via `maxMessagesPerPoll`) rather than one at a time, useful when per-message overhead (e.g., a database transaction) is expensive enough that batching amortizes it meaningfully.

## 3. Core concept

Think of a polling consumer like checking your mailbox on a fixed schedule — every morning at 8am, rain or shine, whether or not anything actually arrived — as opposed to a doorbell that rings automatically the instant a package is dropped off (an event-driven consumer, card 0036). The mail carrier doesn't wake you up when they deliver; you decide, independently, how often you're willing to go check.

```java
@ServiceActivator(inputChannel = "orders", poller = @Poller(fixedDelay = "1000", maxMessagesPerPoll = "5"))
public void processOrder(Order order) {
    fulfillmentService.process(order);
}
```

Every 1000ms, this endpoint's poller checks the `orders` channel and pulls up to 5 messages, invoking `processOrder` once per message pulled — if fewer than 5 are available, it processes whatever's there and waits for the next scheduled tick; it never blocks waiting for more to arrive mid-cycle.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Polling consumer checks a pollable channel on a fixed schedule, pulling up to maxMessagesPerPoll messages each tick, regardless of when they actually arrived">
  <rect x="20" y="30" width="140" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">QueueChannel</text>
  <text x="90" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">messages waiting</text>

  <line x1="90" y1="75" x2="90" y2="115" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="90" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no push notification</text>

  <rect x="220" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Poller</text>
  <text x="310" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixedDelay=1000, max=5</text>
  <text x="310" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">actively checks on schedule</text>

  <line x1="160" y1="55" x2="220" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#pc1)"/>
  <text x="190" y="42" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">pull</text>

  <line x1="400" y1="55" x2="460" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#pc2)"/>

  <rect x="470" y="30" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">endpoint handler</text>
  <text x="540" y="65" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">invoked per message</text>

  <defs>
    <marker id="pc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pc2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The poller is entirely active — it decides when to check, independent of when messages actually landed on the channel.

## 5. Runnable example

The scenario: an order-processing endpoint fed by a `QueueChannel`, starting with a basic fixed-delay poller, then batch processing via `maxMessagesPerPoll`, and finally observing how a burst arriving between poll ticks gets naturally throttled.

### Level 1 — Basic

```java
// BasicPollingConsumerDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicPollingConsumerDemo {
    public static void main(String[] args) throws InterruptedException {
        QueueChannel orders = new QueueChannel();
        orders.send(MessageBuilder.withPayload("order-1").build());

        // what @Poller(fixedDelay="500") does for you:
        Thread poller = new Thread(() -> {
            for (int i = 0; i < 3; i++) {
                Message<?> m = orders.receive(0); // non-blocking check, exactly what a poll TICK does
                System.out.println("Poll tick " + (i + 1) + ": " + (m != null ? "processed " + m.getPayload() : "nothing waiting"));
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }
        });
        poller.start();
        poller.join();
    }
}
```

How to run: `java BasicPollingConsumerDemo.java`. Expected output: `Poll tick 1: processed order-1`, then `Poll tick 2: nothing waiting`, then `Poll tick 3: nothing waiting` — the single available message was picked up on the first scheduled tick, and subsequent ticks (500ms apart) found the channel empty since nothing new arrived.

### Level 2 — Intermediate

With `maxMessagesPerPoll` greater than 1, each tick drains up to that many messages in one go rather than just one — useful for batching expensive per-message overhead (like a database transaction) across several messages at once.

```java
// MaxMessagesPerPollDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class MaxMessagesPerPollDemo {
    public static void main(String[] args) throws InterruptedException {
        QueueChannel orders = new QueueChannel();
        for (int i = 1; i <= 7; i++) {
            orders.send(MessageBuilder.withPayload("order-" + i).build());
        }

        int maxMessagesPerPoll = 3;
        int tick = 1;
        while (true) {
            int processedThisTick = 0;
            System.out.println("--- Poll tick " + tick + " ---");
            for (int i = 0; i < maxMessagesPerPoll; i++) {
                Message<?> m = orders.receive(0);
                if (m == null) break;
                System.out.println("  Processed: " + m.getPayload());
                processedThisTick++;
            }
            if (processedThisTick == 0) break; // nothing left, stop simulating ticks
            tick++;
            Thread.sleep(200);
        }
    }
}
```

How to run: `java MaxMessagesPerPollDemo.java`. Expected output: `Poll tick 1` processes `order-1`, `order-2`, `order-3` (3 messages, hitting the cap); `Poll tick 2` processes `order-4`, `order-5`, `order-6` (another 3); `Poll tick 3` processes only `order-7` (the remaining 1) — seven messages drained across three ticks, each tick capped at 3, rather than one message per tick across seven separate ticks.

### Level 3 — Advanced

A burst of messages arriving faster than the poller's fixed-delay schedule checks demonstrates natural throttling: the poller doesn't react to arrivals in real time — it only ever sees what's accumulated by the time its next scheduled tick actually runs, smoothing out bursts into steady, predictable processing batches.

```java
// BurstThrottlingDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.CountDownLatch;

public class BurstThrottlingDemo {
    public static void main(String[] args) throws InterruptedException {
        QueueChannel orders = new QueueChannel();
        CountDownLatch pollerDone = new CountDownLatch(1);

        // POLLER: fixed 300ms schedule, unaware of exactly when messages actually arrive
        Thread poller = new Thread(() -> {
            long start = System.currentTimeMillis();
            while (System.currentTimeMillis() - start < 1000) {
                int count = 0;
                Message<?> m;
                while ((m = orders.receive(0)) != null) count++;
                System.out.println("Tick at +" + (System.currentTimeMillis() - start) + "ms: drained " + count + " messages");
                try { Thread.sleep(300); } catch (InterruptedException ignored) {}
            }
            pollerDone.countDown();
        });
        poller.start();

        // BURST: 5 messages arrive quickly, all BEFORE the poller's next scheduled tick
        Thread.sleep(50);
        for (int i = 1; i <= 5; i++) {
            orders.send(MessageBuilder.withPayload("order-" + i).build());
        }
        System.out.println("Burst of 5 sent at once — poller hasn't ticked again yet");

        pollerDone.await();
    }
}
```

How to run: `java BurstThrottlingDemo.java`. Expected output: an early tick draining `0` messages, then `Burst of 5 sent at once...`, then the *next* scheduled tick (roughly 300ms after the previous one, not immediately after the burst) draining all `5` messages at once — the poller absorbed the entire burst into a single scheduled tick, rather than reacting to each message's arrival individually.

## 6. Walkthrough

Tracing `BurstThrottlingDemo` in execution order:

1. The poller thread starts its loop immediately, and its first tick (at roughly `+0ms`) finds the channel empty, printing `drained 0 messages`.
2. The poller sleeps 300ms before its next tick — during this sleep, it is not watching the channel at all; it has no way to react to anything that happens while it's asleep.
3. At `+50ms`, well within the poller's sleep window, the main thread sends all 5 burst messages to `orders` in rapid succession — from the channel's perspective, all 5 are now sitting there, but the poller has no idea yet, since it isn't checking.
4. The poller's `while` loop condition is only re-evaluated once its `Thread.sleep(300)` call returns — so the next tick doesn't happen until roughly `+300ms`, a full 250ms after the burst actually landed.
5. When that next tick finally runs, its inner `while ((m = orders.receive(0)) != null)` loop drains every message currently available — all 5 at once, since none had been picked up yet — printing `drained 5 messages`.
6. This is the defining behavior of a polling consumer versus an event-driven one (card 0036): the poller's schedule, not the messages' arrival times, determines when processing actually happens — a burst is absorbed and processed together on the next tick, rather than triggering five separate, immediate reactions.

```
t=0ms:    poller tick -> drains 0 (channel empty)
t=50ms:   burst of 5 messages sent (poller is ASLEEP, unaware)
t=300ms:  poller tick -> drains ALL 5 at once (first chance it gets to look)
```

## 7. Gotchas & takeaways

> A poller's fixed schedule means there's an inherent latency floor between a message arriving and it actually being processed — in the worst case, up to the full poll interval, if the message arrives just after a tick has already run. This is a deliberate tradeoff (steady, predictable load vs. immediate reactivity) but it's easy to be surprised by it if a polling consumer is used somewhere latency-sensitive; an event-driven consumer (card 0036, typically backed by a push-based channel like `DirectChannel`) reacts immediately instead, with no such floor.

- A polling consumer actively pulls from a pollable channel on a schedule controlled by `PollerMetadata` — how often (`fixedDelay`/`fixedRate`/`cron`) and how many messages per tick (`maxMessagesPerPoll`).
- Use it for channels that don't push automatically (`QueueChannel` and relatives), or when explicit control over processing rate/batching is desired, independent of arrival timing.
- A higher `maxMessagesPerPoll` batches more work per tick, useful for amortizing expensive per-message overhead; a lower value processes more incrementally.
- A poller absorbs bursts into whatever its next scheduled tick catches, rather than reacting to each arrival individually — this smooths load but introduces a latency floor up to the poll interval.
- Choose a poller when steady, controlled processing load matters more than immediate reactivity; choose an event-driven consumer (card 0036) when the opposite tradeoff is the right one.
