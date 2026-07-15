---
card: spring-integration
gi: 36
slug: event-driven-consumer
title: "Event-driven consumer"
---

## 1. What it is

An event-driven consumer is an endpoint subscribed directly to a subscribable channel (`DirectChannel`, card 0008, `PublishSubscribeChannel`, `ExecutorChannel`, card 0013, and similar) — dispatch happens automatically the instant a message is sent, with no polling schedule involved at all. It is the direct counterpart to the polling consumer (card 0035): where a polling consumer actively checks a channel on a schedule, an event-driven consumer is reactively invoked by the channel itself, immediately, as part of the `send()` call.

## 2. Why & when

You reach for an event-driven consumer specifically when immediate reaction to a message matters more than controlled, scheduled processing:

- **Low latency between a message arriving and being processed is important** — there's no polling interval to wait out; dispatch happens as part of the same `send()` call (synchronously for `DirectChannel`, or nearly-immediately via a pool for `ExecutorChannel`), avoiding the latency floor a polling consumer (card 0035) inherently has.
- **The channel type is already subscribable** — `DirectChannel` and its relatives dispatch to subscribers automatically; there's no separate polling configuration to add, since the channel itself is the trigger mechanism.
- **The processing rate should track the arrival rate directly**, rather than being smoothed or batched by a fixed poll schedule — an event-driven consumer processes each message as it comes, for better or worse (a burst causes a burst of processing, not a throttled batch).

## 3. Core concept

Think of an event-driven consumer like a doorbell that rings the instant someone presses it, as opposed to the polling consumer's fixed 8am mailbox check (card 0035). There's no schedule to wait for — the moment the visitor's finger presses the button, the chime sounds and whoever's inside reacts right then. This immediacy is exactly what `DirectChannel`'s synchronous `send()`-triggers-`subscribe()` mechanism (card 0008) already provides — an event-driven consumer is simply the name for an endpoint taking advantage of that automatic dispatch.

```java
@ServiceActivator(inputChannel = "orders") // NO poller attribute at all — this IS an event-driven consumer
public void processOrder(Order order) {
    fulfillmentService.process(order);
}
```

Because `orders` here is a subscribable channel (`DirectChannel` by default, unless configured otherwise), this endpoint is invoked automatically, synchronously, the instant a message is sent to `orders` — there's no polling schedule to configure, and none would even apply.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Event-driven consumer: send() on a subscribable channel immediately and automatically invokes the subscribed handler, with no polling schedule involved">
  <rect x="20" y="50" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send()</text>

  <line x1="140" y1="72" x2="220" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#ed1)"/>
  <text x="180" y="58" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">immediate, automatic</text>

  <rect x="230" y="50" width="150" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DirectChannel</text>
  <text x="305" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">subscribable</text>

  <line x1="380" y1="72" x2="440" y2="72" stroke="#79c0ff" stroke-width="2" marker-end="url(#ed2)"/>
  <text x="410" y="58" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">invoked NOW</text>

  <rect x="450" y="50" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">event-driven consumer</text>
  <text x="530" y="87" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">no polling schedule</text>

  <defs>
    <marker id="ed1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ed2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

No schedule, no delay — dispatch happens as an inherent part of the `send()` call itself.

## 5. Runnable example

The scenario: the same order-processing endpoint from card 0035's polling examples, now built event-driven for direct latency comparison, then a burst comparison showing the behavioral difference explicitly, and finally an event-driven consumer combined with async dispatch for concurrent immediate reaction.

### Level 1 — Basic

```java
// BasicEventDrivenConsumerDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicEventDrivenConsumerDemo {
    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();

        // what @ServiceActivator(inputChannel="orders") with NO poller does for you:
        orders.subscribe(m -> System.out.println("Processed IMMEDIATELY: " + m.getPayload()
            + " at " + System.nanoTime() + "ns"));

        System.out.println("Sending at " + System.nanoTime() + "ns");
        orders.send(MessageBuilder.withPayload("order-1").build());
        System.out.println("send() returned — processing already happened, synchronously, above");
    }
}
```

How to run: `java BasicEventDrivenConsumerDemo.java`. Expected output: `Sending at ...ns`, then `Processed IMMEDIATELY: order-1 at ...ns` (a nanosecond timestamp essentially identical to the send), then `send() returned...` — there is no gap between sending and processing; the handler runs as an inherent part of the `send()` call itself, not on any later schedule.

### Level 2 — Intermediate

Directly contrasting a `DirectChannel` (event-driven) against a `QueueChannel` with manual polling (from card 0035's approach) for the exact same burst of messages makes the behavioral difference concrete: event-driven processes each message the instant it's sent; polling only picks messages up on its next scheduled tick.

```java
// EventDrivenVsPollingComparisonDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;

public class EventDrivenVsPollingComparisonDemo {
    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();

        // EVENT-DRIVEN: reacts instantly to each send()
        DirectChannel eventDriven = new DirectChannel();
        eventDriven.subscribe(m -> System.out.println("[event-driven] processed " + m.getPayload()
            + " at +" + (System.currentTimeMillis() - start) + "ms"));

        // POLLING: only checked once, at a fixed later time (simulating a 400ms poll interval)
        QueueChannel polling = new QueueChannel();

        for (int i = 1; i <= 3; i++) {
            eventDriven.send(MessageBuilder.withPayload("order-" + i).build());
            polling.send(MessageBuilder.withPayload("order-" + i).build());
        }
        System.out.println("All 3 messages sent to BOTH channels at +" + (System.currentTimeMillis() - start) + "ms");

        Thread.sleep(400); // simulating waiting for the polling consumer's next scheduled tick
        var m1 = polling.receive(0);
        var m2 = polling.receive(0);
        var m3 = polling.receive(0);
        System.out.println("[polling] finally processed all 3 at +" + (System.currentTimeMillis() - start) + "ms: "
            + m1.getPayload() + ", " + m2.getPayload() + ", " + m3.getPayload());
    }
}
```

How to run: `java EventDrivenVsPollingComparisonDemo.java`. Expected output: three `[event-driven] processed ...` lines all at essentially `+0ms`, immediately followed by `All 3 messages sent...`, and only ~400ms later does `[polling] finally processed all 3 at +400ms: ...` appear — the identical three messages, sent at the identical moment to both channel types, were handled instantly by the event-driven consumer but sat waiting for the polling consumer's next scheduled check.

### Level 3 — Advanced

Combining an event-driven consumer with an `ExecutorChannel` (card 0013) shows immediate *and* concurrent reaction: each message is still dispatched the instant it's sent (no polling schedule), but dispatch happens onto pool threads rather than synchronously blocking the sender, giving both immediacy and throughput.

```java
// AsyncEventDrivenConsumerDemo.java
import org.springframework.integration.channel.ExecutorChannel;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import java.util.concurrent.CountDownLatch;

public class AsyncEventDrivenConsumerDemo {
    public static void main(String[] args) throws InterruptedException {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(3);
        executor.initialize();

        ExecutorChannel orders = new ExecutorChannel(executor); // still event-driven — no poller anywhere
        CountDownLatch latch = new CountDownLatch(3);
        long start = System.currentTimeMillis();

        orders.subscribe(m -> {
            System.out.println(Thread.currentThread().getName() + " reacted to " + m.getPayload()
                + " at +" + (System.currentTimeMillis() - start) + "ms (no poll schedule involved)");
            latch.countDown();
        });

        for (int i = 1; i <= 3; i++) {
            orders.send(MessageBuilder.withPayload("order-" + i).build()); // dispatched IMMEDIATELY, just asynchronously
        }
        System.out.println("All 3 sends completed at +" + (System.currentTimeMillis() - start) + "ms");

        latch.await();
        executor.shutdown();
    }
}
```

How to run: `java AsyncEventDrivenConsumerDemo.java`. Expected output: `All 3 sends completed at +~0ms` prints almost immediately, and all three `... reacted to order-N at +~0ms` lines (from different pool threads) appear right after, all still at essentially `+0ms` — dispatch remained event-driven (no polling delay whatsoever), just handled asynchronously across pool threads rather than blocking the sender synchronously.

## 6. Walkthrough

Tracing `EventDrivenVsPollingComparisonDemo` in execution order:

1. The `for` loop's first iteration calls `eventDriven.send(...)` for `order-1` — because `eventDriven` is a `DirectChannel`, this call synchronously invokes the subscribed handler *before* `send()` even returns, printing the `[event-driven] processed order-1 at +0ms` line immediately.
2. The same iteration then calls `polling.send(...)` for `order-1` — because `polling` is a `QueueChannel`, this call only enqueues the message; nothing observes or processes it yet, since nothing is actively checking the channel.
3. This pattern repeats for `order-2` and `order-3`: each event-driven send triggers immediate processing, while each polling send simply adds to the queue with no immediate effect.
4. After the loop, `All 3 messages sent to BOTH channels at +0ms` prints — by this point, all three event-driven messages have *already* been fully processed, while all three polling messages are still sitting, untouched, in the `QueueChannel`'s internal queue.
5. The main thread then sleeps 400ms, standing in for the polling consumer's fixed poll interval — during this entire window, the three queued messages remain exactly where they were, since nothing is checking the channel.
6. Only after the sleep does the code manually call `polling.receive(0)` three times, finally retrieving and printing all three messages at once, roughly 400ms after they were actually sent — a direct, measurable illustration of the latency floor a polling consumer (card 0035) has that an event-driven consumer simply doesn't.

```
t=0ms: send(order-1) to DirectChannel -> [event-driven] processed order-1 at +0ms  (SYNCHRONOUS, immediate)
t=0ms: send(order-1) to QueueChannel  -> just enqueued, NOTHING happens yet
... (same for order-2, order-3) ...
t=0ms: "All 3 messages sent..." printed (event-driven side ALREADY DONE)
t=400ms: polling consumer FINALLY checks -> processes all 3 at once
```

## 7. Gotchas & takeaways

> Because an event-driven consumer on a synchronous channel like `DirectChannel` runs as part of the sender's own `send()` call, a slow handler directly slows down every sender — there's no polling schedule to absorb or decouple that cost, unlike the polling consumer's inherent batching/throttling behavior (card 0035). If a handler's work is genuinely slow or bursty, pair event-driven dispatch with an asynchronous channel type (`ExecutorChannel`, card 0013, as in Level 3) rather than assuming "event-driven" automatically means "won't block anything."

- An event-driven consumer is subscribed directly to a subscribable channel (`DirectChannel` and relatives) and is invoked automatically, immediately, as part of the channel's `send()` call — no polling schedule is involved at all.
- Use it when low latency between message arrival and processing matters, or when the channel is already subscribable and adding polling configuration would be pointless overhead.
- Unlike a polling consumer (card 0035), an event-driven consumer doesn't smooth or batch bursts — a burst of sends causes a burst of immediate processing, for better (low latency) or worse (no natural throttling).
- On a synchronous channel, an event-driven handler's execution time directly adds to the sender's `send()` call duration — pair with an asynchronous channel (`ExecutorChannel`, card 0013) if that coupling is undesirable.
- The choice between event-driven and polling consumers is fundamentally a tradeoff between immediate reactivity (event-driven) and controlled, scheduled, throttled processing (polling) — neither is universally "better," and the right choice depends on which property the specific flow actually needs.
