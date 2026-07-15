---
card: spring-integration
gi: 11
slug: prioritychannel
title: "PriorityChannel"
---

## 1. What it is

`PriorityChannel` is a `MessageChannel` implementation, just like `QueueChannel` (card 0010), backed by an internal queue that a consumer drains via `receive()` — but instead of ordering messages strictly first-in-first-out, it orders them by priority. By default it looks for a `priority` header (an `Integer`) on each message; when you `receive()`, the highest-priority message currently waiting comes off first, regardless of how long it has sat in the queue relative to lower-priority messages sent earlier.

## 2. Why & when

You reach for `PriorityChannel` specifically when arrival order and processing order need to diverge based on business importance:

- **Some messages are genuinely more urgent than others.** A `fraud-alert` message that arrives after ten routine `balance-update` messages still needs to jump the queue and be processed first — FIFO ordering (what `QueueChannel` gives you) would make it wait behind everything already queued.
- **You have a single consumer (or pool) that cannot keep up with total volume**, and when it falls behind, you want the backlog to drain in importance order rather than arrival order — so under load, low-priority work is the work that waits, not high-priority work.
- **You want this behavior without building a custom priority queue by hand** — `PriorityChannel` gives you priority-ordered draining as a drop-in channel type, using the same `send()`/`receive()` contract as any other `MessageChannel`.

## 3. Core concept

Think of `PriorityChannel` like a hospital triage queue rather than a bank teller's line. A bank teller's line (`QueueChannel`) serves whoever arrived first; triage serves whoever is most critical, even if they walked in last. A patient with a broken arm who arrived an hour ago still waits behind a patient with chest pain who just arrived, because the ordering principle is severity, not arrival time.

```java
PriorityChannel channel = new PriorityChannel();

channel.send(MessageBuilder.withPayload("balance-update").setHeader("priority", 1).build());
channel.send(MessageBuilder.withPayload("fraud-alert").setHeader("priority", 10).build());

Message<?> first = channel.receive();
System.out.println(first.getPayload()); // "fraud-alert" — HIGHER priority, even though sent SECOND
```

Internally, `PriorityChannel` wraps a `java.util.concurrent.PriorityBlockingQueue`, using a comparator that reads the `priority` header (higher number = higher priority by default) to decide ordering — everything else about `send()`/`receive()` semantics matches `QueueChannel`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PriorityChannel reorders messages by priority header: a fraud-alert sent after two lower-priority messages is still received first">
  <rect x="20" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send: balance-update (p=1)</text>

  <rect x="20" y="64" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send: login-event (p=3)</text>

  <rect x="20" y="108" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="95" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send: fraud-alert (p=10)</text>

  <line x1="170" y1="60" x2="230" y2="100" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="170" y1="80" x2="230" y2="105" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="170" y1="125" x2="230" y2="90" stroke="#79c0ff" stroke-width="2"/>

  <rect x="230" y="60" width="180" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PriorityChannel</text>
  <text x="320" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ordered: p=10, p=3, p=1</text>
  <text x="320" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">highest priority</text>
  <text x="320" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">drains first</text>

  <line x1="410" y1="105" x2="480" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#p1)"/>
  <text x="445" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">receive()</text>

  <rect x="490" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">consumer gets</text>
  <text x="555" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fraud-alert first</text>

  <defs>
    <marker id="p1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Arrival order was balance-update, login-event, fraud-alert; drain order flips to priority order: fraud-alert first.

## 5. Runnable example

The scenario: an event-intake channel handling routine `balance-update` events alongside urgent `fraud-alert` events, starting with basic priority ordering, then a mixed burst under a single consumer, and finally a tie-break with a custom comparator for same-priority messages.

### Level 1 — Basic

```java
// BasicPriorityChannelDemo.java
import org.springframework.integration.channel.PriorityChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicPriorityChannelDemo {
    public static void main(String[] args) {
        PriorityChannel channel = new PriorityChannel();

        channel.send(MessageBuilder.withPayload("balance-update").setHeader("priority", 1).build());
        channel.send(MessageBuilder.withPayload("fraud-alert").setHeader("priority", 10).build());

        Message<?> first = channel.receive();
        Message<?> second = channel.receive();
        System.out.println("First received: " + first.getPayload());   // fraud-alert, despite being sent SECOND
        System.out.println("Second received: " + second.getPayload()); // balance-update
    }
}
```

How to run: `java BasicPriorityChannelDemo.java`. Expected output: `First received: fraud-alert`, `Second received: balance-update` — proving drain order follows the `priority` header, not send order.

### Level 2 — Intermediate

A realistic event-intake channel receives a mixed burst of events at different priorities; a single consumer draining afterward should always see the highest-priority backlog item next, no matter how the burst was interleaved.

```java
// MixedBurstPriorityDemo.java
import org.springframework.integration.channel.PriorityChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class MixedBurstPriorityDemo {
    public static void main(String[] args) {
        PriorityChannel channel = new PriorityChannel();

        String[] events = {"balance-update", "login-event", "fraud-alert", "balance-update", "password-reset"};
        int[] priorities = {1, 3, 10, 1, 7};

        for (int i = 0; i < events.length; i++) {
            channel.send(MessageBuilder.withPayload(events[i]).setHeader("priority", priorities[i]).build());
        }
        System.out.println("Burst of " + events.length + " events sent, in arrival order: fraud-alert was 3rd");

        System.out.println("Drain order (highest priority first):");
        for (int i = 0; i < events.length; i++) {
            Message<?> m = channel.receive();
            System.out.println("  " + m.getPayload() + " (priority=" + m.getHeaders().get("priority") + ")");
        }
    }
}
```

How to run: `java MixedBurstPriorityDemo.java`. Expected output drains in the order `fraud-alert (10)`, `password-reset (7)`, `login-event (3)`, then the two `balance-update (1)` events (FIFO among equal priorities) — showing the channel fully reorders the backlog by importance, not arrival position.

### Level 3 — Advanced

For finer control than a single integer header, `PriorityChannel` accepts a custom `Comparator<Message<?>>` in its constructor — useful when priority needs a secondary tie-break, such as an older message of equal priority being served before a newer one of the same priority (rather than the default's unspecified tie order).

```java
// CustomComparatorPriorityDemo.java
import org.springframework.integration.channel.PriorityChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Comparator;

public class CustomComparatorPriorityDemo {
    public static void main(String[] args) throws InterruptedException {
        // primary: higher priority header first; tie-break: earlier 'sentAt' header first
        Comparator<Message<?>> byPriorityThenAge = Comparator
            .comparingInt((Message<?> m) -> (Integer) m.getHeaders().get("priority")).reversed()
            .thenComparingLong(m -> (Long) m.getHeaders().get("sentAt"));

        PriorityChannel channel = new PriorityChannel(10, byPriorityThenAge);

        channel.send(MessageBuilder.withPayload("fraud-alert-A").setHeader("priority", 10)
            .setHeader("sentAt", System.currentTimeMillis()).build());
        Thread.sleep(10); // ensure a distinct, later timestamp
        channel.send(MessageBuilder.withPayload("fraud-alert-B").setHeader("priority", 10)
            .setHeader("sentAt", System.currentTimeMillis()).build());

        System.out.println("Both same priority (10); tie-break is arrival order:");
        System.out.println("  " + channel.receive().getPayload()); // fraud-alert-A (older)
        System.out.println("  " + channel.receive().getPayload()); // fraud-alert-B (newer)
    }
}
```

How to run: `java CustomComparatorPriorityDemo.java`. Expected output: `fraud-alert-A` then `fraud-alert-B` — the custom comparator deterministically breaks the priority=10 tie by timestamp, instead of leaving equal-priority ordering unspecified.

## 6. Walkthrough

Tracing `MixedBurstPriorityDemo` in execution order:

1. Five `send()` calls enqueue events in this arrival order: `balance-update(1)`, `login-event(3)`, `fraud-alert(10)`, `balance-update(1)`, `password-reset(7)` — each `send()` returns immediately, just like `QueueChannel`, since enqueueing is instant regardless of priority.
2. Internally, the `PriorityBlockingQueue` backing the channel keeps its contents ordered by the priority comparator on every insert, not just at drain time — so the queue's internal order after all five sends already reflects priority, not arrival sequence.
3. The first `channel.receive()` call pulls the highest-priority element: `fraud-alert(10)`, even though it was the third message sent.
4. The second `receive()` pulls `password-reset(7)`, the next-highest remaining priority.
5. The third `receive()` pulls `login-event(3)`.
6. The final two `receive()` calls drain the two `balance-update(1)` messages in the order they were originally sent relative to each other, since the default comparator only orders by priority and leaves equal-priority messages in their relative insertion order.

```
send order:   balance-update(1) -> login-event(3) -> fraud-alert(10) -> balance-update(1) -> password-reset(7)
internal queue (priority order): [fraud-alert(10), password-reset(7), login-event(3), balance-update(1), balance-update(1)]
receive order: fraud-alert(10) -> password-reset(7) -> login-event(3) -> balance-update(1) -> balance-update(1)
```

## 7. Gotchas & takeaways

> A message sent to a `PriorityChannel` with no `priority` header (or a non-`Integer` value in that header) does not throw — it is simply treated as having no defined priority and effectively sorts after all messages that do have one, per the default comparator's null-handling. Silently missing headers become silently deprioritized messages; validate that upstream senders actually set the header if priority ordering is load-bearing.

- `PriorityChannel` reorders by a `priority` header (default) or a custom `Comparator<Message<?>>`, unlike `QueueChannel`'s (card 0010) strict FIFO.
- Use it when some messages are genuinely more business-critical than others and a backlogged consumer should work through important items first.
- The default comparator's tie-break behavior between equal-priority messages is insertion order, but this is an implementation detail of the underlying `PriorityBlockingQueue`, not a documented guarantee — supply an explicit comparator if a specific tie-break matters.
- Like any `PriorityChannel`, it is still just a `QueueChannel`-family channel underneath: it needs an explicit consumer (poller or manual `receive()`) to drain, and an unbounded one can still grow without limit under sustained overload.
- Priority ordering only applies to messages currently sitting in the queue at receive time — a low-priority message already being processed by a consumer is not preempted by a higher-priority message that arrives afterward.
