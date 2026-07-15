---
card: spring-integration
gi: 10
slug: queuechannel
title: "QueueChannel"
---

## 1. What it is

`QueueChannel` is a `MessageChannel` implementation backed by an internal, in-memory blocking queue: a sender's `send()` call places a message onto the queue and returns immediately (the sender is not blocked waiting for anything to actually process it), and a separate consumer must explicitly call `receive()` (or have a poller configured to call it on their behalf) to pull a message off. Unlike `DirectChannel` (card 0008), where dispatch is synchronous and happens on the sender's own thread, `QueueChannel` decouples the sender's timing from the consumer's timing entirely — the message simply waits in the queue until someone is ready for it.

## 2. Why & when

You reach for `QueueChannel` specifically when you need to decouple *when* a message is sent from *when* it's actually processed — a decoupling `DirectChannel` deliberately doesn't provide:

- **A slow or currently-busy consumer shouldn't block the sender.** With `DirectChannel`, a slow handler directly slows down whoever called `send()`, since dispatch is synchronous; with `QueueChannel`, `send()` returns as soon as the message is queued, regardless of how backed up the consumer currently is.
- **A burst of messages arriving faster than they can be processed needs somewhere to wait**, rather than either blocking every sender or being dropped — the queue absorbs that burst, smoothing out the mismatch between arrival rate and processing rate.
- **The sender and consumer may run on entirely different threads** — a poller (a `PollerMetadata`-configured trigger) pulls messages off the queue at its own pace, on its own thread, completely decoupled from whatever thread(s) called `send()`.
- **You want an explicit, boundedly-sized buffer between two processing stages**, giving you deliberate control over how much in-flight, not-yet-processed work is allowed to accumulate before further sends either block or are rejected (a bounded `QueueChannel`'s capacity limit, discussed further in the runnable example below).

## 3. Core concept

Think of `QueueChannel` like a physical in-tray on someone's desk, as opposed to `DirectChannel`'s "hand it directly to a colleague and wait." Dropping a document into an in-tray takes an instant — you don't stand there waiting for the recipient to actually read and act on it; you simply place it in the tray and walk away, free to do other things immediately. The recipient checks their in-tray on their own schedule, pulling out and handling documents whenever they're ready, completely decoupled from whenever each document was originally dropped off.

```java
QueueChannel channel = new QueueChannel(); // unbounded by default

channel.send(MessageBuilder.withPayload("order-123").build());
// send() returns IMMEDIATELY — nothing has been "handled" yet, the message just sits in the queue

Message<?> received = channel.receive(); // an EXPLICIT, separate pull, whenever the consumer is ready
System.out.println("Received: " + received.getPayload());
```

Nothing happens to the message between `send()` and `receive()` except sitting in the internal queue — no handler runs automatically the way it would with `DirectChannel`'s subscribers; something has to actively call `receive()` (directly, or via a configured poller) to move a message along.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="QueueChannel decouples sender and receiver timing: send() returns immediately after enqueueing, and a separate receive() call, on its own thread and schedule, pulls messages off later">
  <rect x="20" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">send() caller</text>

  <line x1="150" y1="105" x2="220" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#q1)"/>
  <text x="185" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">returns instantly</text>

  <rect x="230" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">QueueChannel</text>
  <text x="320" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">internal blocking queue</text>
  <text x="320" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">messages wait here</text>

  <line x1="410" y1="105" x2="480" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#q2)"/>
  <text x="445" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">separate receive()</text>

  <rect x="490" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">consumer, own thread</text>

  <defs>
    <marker id="q1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="q2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`send()` and `receive()` are entirely separate calls, on potentially separate threads, with the queue absorbing the timing gap between them.

## 5. Runnable example

The scenario: an order-intake step feeding a slower order-processing step, starting with basic decoupled send/receive, then observing the queue absorb a burst of sends faster than a consumer drains them, and finally a bounded queue's capacity limit blocking a sender once full.

### Level 1 — Basic

```java
// BasicQueueChannelDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicQueueChannelDemo {
    public static void main(String[] args) {
        QueueChannel channel = new QueueChannel(); // unbounded

        System.out.println("Before send()");
        channel.send(MessageBuilder.withPayload("order-123").build());
        System.out.println("After send()"); // this prints IMMEDIATELY, nothing has been "handled" yet

        Message<?> received = channel.receive(); // explicit, separate pull
        System.out.println("Received via explicit receive(): " + received.getPayload());
    }
}
```

How to run: `java BasicQueueChannelDemo.java`. Expected output order: `Before send()`, `After send()`, `Received via explicit receive(): order-123` — proving `send()` returns before anything resembling "handling" occurs; the message just waits in the internal queue until `receive()` is explicitly called.

### Level 2 — Intermediate

Because `send()` never blocks waiting on a consumer (for an unbounded queue), a burst of sends can outpace a slower consumer — the queue simply grows to absorb the difference, and the consumer drains it at its own pace afterward.

```java
// BurstAbsorptionDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BurstAbsorptionDemo {
    public static void main(String[] args) throws InterruptedException {
        QueueChannel channel = new QueueChannel();

        // a burst of 5 sends, all completing instantly, regardless of how fast anything downstream is
        for (int i = 1; i <= 5; i++) {
            channel.send(MessageBuilder.withPayload("order-" + i).build());
            System.out.println("Sent order-" + i);
        }
        System.out.println("All 5 sends completed. Queue currently holds: " + channel.getQueueSize() + " messages");

        // a SLOW consumer, draining one at a time, on its own schedule
        for (int i = 1; i <= 5; i++) {
            Thread.sleep(50); // simulates the consumer being busy/slow
            Message<?> received = channel.receive();
            System.out.println("Consumer drained: " + received.getPayload());
        }
    }
}
```

How to run: `java BurstAbsorptionDemo.java`. Expected output: all 5 `Sent order-N` lines print immediately, back to back, followed by `Queue currently holds: 5 messages`, and only afterward does the slower consumer loop drain them one at a time with a visible pause between each — demonstrating the queue fully absorbing the burst before the consumer starts catching up.

### Level 3 — Advanced

A bounded `QueueChannel` (constructed with a fixed capacity) makes `send()` block once the queue is full, providing deliberate backpressure — a sender attempting to add a sixth message to a five-capacity queue that hasn't yet been drained will wait rather than growing the queue unboundedly.

```java
// BoundedQueueBackpressureDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.*;

public class BoundedQueueBackpressureDemo {
    public static void main(String[] args) throws Exception {
        QueueChannel channel = new QueueChannel(2); // BOUNDED: capacity of 2

        channel.send(MessageBuilder.withPayload("order-1").build());
        channel.send(MessageBuilder.withPayload("order-2").build());
        System.out.println("Queue full at capacity 2. Queue size: " + channel.getQueueSize());

        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Boolean> blockedSend = executor.submit(() ->
            channel.send(MessageBuilder.withPayload("order-3").build(), 2000)); // blocks up to 2s waiting for room

        Thread.sleep(300); // give the blocked send a moment to actually start waiting
        System.out.println("order-3's send() is currently BLOCKED, waiting for room in the full queue...");

        channel.receive(); // drains ONE message, freeing a slot
        System.out.println("Consumer drained one message, freeing a slot");

        boolean sent = blockedSend.get(); // the previously-blocked send() now succeeds
        System.out.println("order-3 send() succeeded after room freed up: " + sent);
        executor.shutdown();
    }
}
```

How to run: `java BoundedQueueBackpressureDemo.java`. Expected output shows the queue filling to its capacity of 2, a third send blocking (visible via the "currently BLOCKED" message before anything frees up), then succeeding only after `receive()` drains one slot — demonstrating that a bounded `QueueChannel` applies real backpressure to senders rather than growing without limit.

## 6. Walkthrough

Tracing `BoundedQueueBackpressureDemo` in execution order:

1. `channel.send(...)` for `"order-1"` and `"order-2"` both succeed immediately — the bounded queue (capacity 2) has room for both, so neither call blocks.
2. `channel.getQueueSize()` confirms the queue now holds exactly 2 messages, its full capacity.
3. A background thread attempts `channel.send(..., 2000)` for `"order-3"` — because the queue is already full, this call blocks (up to the given 2-second timeout), waiting for room to free up rather than failing immediately or growing the queue past its bound.
4. The main thread sleeps briefly, then prints confirmation that `order-3`'s send is currently blocked — at this point, the queue genuinely has one sender waiting on room that doesn't yet exist.
5. `channel.receive()` on the main thread drains `"order-1"` (the queue's oldest message, FIFO by default), freeing one slot in the bounded queue.
6. The previously-blocked `send()` for `"order-3"` immediately notices the freed slot and completes successfully, returning `true` from its `Future`.

```
send("order-1") -> queue: [order-1]           (size 1/2)
send("order-2") -> queue: [order-1, order-2]  (size 2/2, FULL)
send("order-3") -> BLOCKS (queue full, no room)
receive()       -> drains order-1 -> queue: [order-2] (size 1/2, room freed)
send("order-3") -> unblocks, succeeds -> queue: [order-2, order-3] (size 2/2)
```

## 7. Gotchas & takeaways

> An unbounded `QueueChannel` (the default, no capacity argument) can grow without limit if senders consistently outpace consumers — the same bounded-resource-usage risk discussed for microservices generally: under sustained overload, an unbounded queue just keeps absorbing messages until memory runs out, rather than ever applying backpressure. Always consider a bounded capacity for any `QueueChannel` handling real, potentially-bursty production traffic.

- `QueueChannel` decouples sender and consumer *timing* — `send()` returns as soon as the message is queued, with a separate `receive()` call (often driven by a configured poller) pulling messages off independently.
- Use it specifically when a slow or currently-busy consumer shouldn't block whatever is sending messages, or when sender and consumer genuinely need to run on different threads or schedules.
- An unbounded `QueueChannel` risks unbounded memory growth under sustained overload; a bounded one applies real backpressure, blocking (or, with `offer`-style calls, failing fast) once full.
- Unlike `DirectChannel` (card 0008), an exception thrown while eventually processing a message pulled via `receive()` does *not* propagate back to the original `send()` caller — by the time the exception occurs, the original sender has long since moved on, having only ever enqueued the message.
- A `QueueChannel` typically needs an explicit consumer (a poller, or manual `receive()` calls) to actually drain it — messages sent to a `QueueChannel` with nothing configured to receive from it simply accumulate indefinitely, silently, with no processing ever happening.
