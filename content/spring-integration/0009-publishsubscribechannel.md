---
card: spring-integration
gi: 9
slug: publishsubscribechannel
title: "PublishSubscribeChannel"
---

## 1. What it is

`PublishSubscribeChannel` is the `MessageChannel` implementation that delivers every message to **every** subscriber, in contrast to `DirectChannel`'s (card 0008) round-robin, one-subscriber-per-message behavior. It's the direct implementation of the classic **Publish-Subscribe Channel** EIP pattern: one event, broadcast to any number of independent, unaware-of-each-other listeners, each free to react in its own way without affecting the others.

## 2. Why & when

Some events genuinely need multiple, independent reactions — a new order being placed might need to trigger an email confirmation, an inventory update, and an analytics event, all as separate, unrelated concerns that shouldn't know about each other or block one another unnecessarily. Modeling this as several subscribers on `DirectChannel` would be wrong, since `DirectChannel` sends each individual message to only *one* of its subscribers, not all of them — exactly the opposite of what's needed here. `PublishSubscribeChannel` exists specifically to broadcast: every subscriber gets its own independent notification of the same event.

Use `PublishSubscribeChannel` when:

- More than one independent action needs to happen in response to the same event, and those actions shouldn't be coupled to or aware of each other.
- New reactions to an existing event need to be added over time without touching the code that publishes the event — a new subscriber can simply be added to the channel, and the publisher's code never changes.

## 3. Core concept

Think of `PublishSubscribeChannel` like a radio broadcast tower: the station transmits one signal, and every tuned-in receiver — a car radio, a home stereo, a phone app — picks up the exact same broadcast independently, each doing whatever it wants with it (playing it aloud, recording it, displaying the station name), with no awareness of, or dependency on, any of the other receivers. Contrast this with `DirectChannel`'s round-robin behavior, more like a dispatcher handing each individual customer at a counter to whichever one of several available clerks happens to be free next — each customer gets exactly one clerk, not all of them.

```java
PublishSubscribeChannel channel = new PublishSubscribeChannel();
channel.subscribe(message -> System.out.println("Email service notified: " + message.getPayload()));
channel.subscribe(message -> System.out.println("Inventory service notified: " + message.getPayload()));
channel.subscribe(message -> System.out.println("Analytics service notified: " + message.getPayload()));

channel.send(MessageBuilder.withPayload("order-123").build());
// ALL THREE subscribers are invoked for this single send() — not just one, unlike DirectChannel.
```

By default, `PublishSubscribeChannel` invokes its subscribers synchronously, on the sender's thread, one after another — an optional `Executor` can be supplied to dispatch to each subscriber asynchronously instead, decoupling the sender from having to wait for every subscriber to finish.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PublishSubscribeChannel delivers one message to every subscriber independently, unlike DirectChannel's round-robin single delivery">
  <rect x="20" y="90" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">send() caller</text>

  <line x1="160" y1="115" x2="220" y2="115" stroke="#3fb950" stroke-width="2" marker-end="url(#x1)"/>

  <rect x="230" y="80" width="150" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PublishSubscribeChannel</text>

  <line x1="380" y1="105" x2="450" y2="45" stroke="#3fb950" stroke-width="1.5" marker-end="url(#x2)"/>
  <line x1="380" y1="115" x2="450" y2="115" stroke="#3fb950" stroke-width="1.5" marker-end="url(#x3)"/>
  <line x1="380" y1="125" x2="450" y2="185" stroke="#3fb950" stroke-width="1.5" marker-end="url(#x4)"/>

  <rect x="460" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Email service</text>

  <rect x="460" y="92" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="119" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Inventory service</text>

  <rect x="460" y="163" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="190" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Analytics service</text>

  <defs>
    <marker id="x1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="x2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="x3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="x4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

One `send()` call notifies every subscriber independently — all three, not just one.

## 5. Runnable example

The scenario: broadcasting a new-order event to three independent services, starting with basic synchronous broadcast, then observing failure isolation between subscribers, and finally switching to asynchronous dispatch so slow subscribers don't block the sender or each other.

### Level 1 — Basic

```java
// BasicPubSubDemo.java
import org.springframework.integration.channel.PublishSubscribeChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicPubSubDemo {
    public static void main(String[] args) {
        PublishSubscribeChannel channel = new PublishSubscribeChannel();
        channel.subscribe(m -> System.out.println("Email service notified: " + m.getPayload()));
        channel.subscribe(m -> System.out.println("Inventory service notified: " + m.getPayload()));
        channel.subscribe(m -> System.out.println("Analytics service notified: " + m.getPayload()));

        channel.send(MessageBuilder.withPayload("order-123").build());
    }
}
```

**How to run:** run with Spring Integration on the classpath: `java BasicPubSubDemo.java`. Expected output: all three lines print — `Email service notified: order-123`, `Inventory service notified: order-123`, `Analytics service notified: order-123` — from a single `send()` call, confirming every subscriber independently received the same message.

### Level 2 — Intermediate

By default, if one subscriber throws an exception, it can prevent later-registered subscribers from being invoked at all (since default dispatch is sequential, on the same thread) — a real risk that an unrelated failure in one reaction blocks entirely unrelated reactions from happening.

```java
// FailureIsolationDemo.java
import org.springframework.integration.channel.PublishSubscribeChannel;
import org.springframework.messaging.support.MessageBuilder;

public class FailureIsolationDemo {
    public static void main(String[] args) {
        PublishSubscribeChannel channel = new PublishSubscribeChannel();

        channel.subscribe(m -> System.out.println("Email service notified: " + m.getPayload()));
        channel.subscribe(m -> {
            throw new RuntimeException("Inventory service is down!"); // simulates a failing subscriber
        });
        channel.subscribe(m -> System.out.println("Analytics service notified: " + m.getPayload()));

        try {
            channel.send(MessageBuilder.withPayload("order-123").build());
        } catch (RuntimeException e) {
            System.out.println("send() threw: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:** run `java FailureIsolationDemo.java`. Expected output: `Email service notified: order-123` prints (the first subscriber, invoked before the failing one), then `send() threw: Inventory service is down!` — but critically, **`Analytics service notified: order-123` never prints**, because the default synchronous dispatcher stops invoking further subscribers once one throws, meaning a single failing subscriber can silently prevent unrelated, later-registered subscribers from ever running.

### Level 3 — Advanced

Configuring `PublishSubscribeChannel` with an `Executor` dispatches to each subscriber on its own thread, decoupling both timing (a slow subscriber no longer blocks the sender) and, importantly, failure isolation (one subscriber's exception no longer prevents others from running, since each runs independently).

```java
// AsyncPubSubDemo.java
import org.springframework.integration.channel.PublishSubscribeChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.Executors;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class AsyncPubSubDemo {
    public static void main(String[] args) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(3); // wait for all three subscribers to finish, for demo purposes

        PublishSubscribeChannel channel = new PublishSubscribeChannel(Executors.newFixedThreadPool(3));

        channel.subscribe(m -> {
            System.out.println("Email service notified: " + m.getPayload());
            latch.countDown();
        });
        channel.subscribe(m -> {
            try {
                throw new RuntimeException("Inventory service is down!");
            } finally {
                latch.countDown(); // even though this subscriber fails, it runs independently of the others
            }
        });
        channel.subscribe(m -> {
            System.out.println("Analytics service notified: " + m.getPayload());
            latch.countDown();
        });

        channel.send(MessageBuilder.withPayload("order-123").build());
        System.out.println("send() returned immediately — dispatch is happening on other threads.");

        latch.await(2, TimeUnit.SECONDS); // wait for the async subscribers to finish, for this demo's sake
        System.out.println("All subscribers have now run, independently.");
    }
}
```

**How to run:** run `java AsyncPubSubDemo.java`. Expected output (exact interleaving of the first few lines may vary slightly since subscribers now run concurrently): `send() returned immediately...` typically prints very early, followed by `Email service notified: order-123` and `Analytics service notified: order-123` both appearing (in either order), and finally `All subscribers have now run, independently.` — critically, **the Analytics subscriber runs successfully this time**, unaffected by the Inventory subscriber's failure, because each now dispatches on its own thread from the executor's pool rather than sharing one sequential, failure-halting call chain.

## 6. Walkthrough

Contrasting the synchronous (Level 2) and asynchronous (Level 3) dispatch of the same three subscribers, in execution order:

1. **Synchronous (Level 2):** `channel.send(...)` invokes subscribers one at a time, on the sender's own thread, in registration order. The Email subscriber runs and completes normally. The Inventory subscriber runs next and throws an exception — because dispatch is sequential and synchronous, this exception immediately propagates up through `send()` itself, and the dispatcher never proceeds to invoke the third (Analytics) subscriber at all.
2. **Asynchronous (Level 3):** `channel.send(...)` instead submits each subscriber's invocation as an independent task to the configured `Executor`, then returns immediately — this is why "send() returned immediately" prints so early, often before any subscriber has even started running.
3. The executor's thread pool picks up all three submitted tasks, generally running them concurrently on separate threads. The Email and Analytics subscribers each complete their `println` independently.
4. The Inventory subscriber's task also runs on its own thread; it throws its exception, but because it's running as an independent task submitted to the executor (not as one link in a sequential in-line call chain), that exception has no ability to prevent the Analytics subscriber's separately-running task from executing — the two are now genuinely decoupled.
5. The `CountDownLatch` (added purely for this demo, to make the asynchronous completion observable in a simple `main` method) reaches zero once all three subscriber tasks have run (successfully or not), and the final confirmation message prints.

```
Synchronous:  Email OK -> Inventory THROWS -> [Analytics NEVER RUNS] -> exception propagates from send()

Asynchronous: send() returns immediately, tasks submitted to executor
              Email    (thread A) -> OK
              Inventory(thread B) -> THROWS, but isolated to its own task
              Analytics(thread C) -> OK, unaffected by Inventory's failure
```

## 7. Gotchas & takeaways

> The default, synchronous dispatch mode of `PublishSubscribeChannel` means a single failing subscriber can silently prevent every subscriber registered *after* it from ever running for that message — this is easy to miss, since it doesn't look like a bug in isolated testing of each subscriber alone, only surfacing when subscribers are combined and one happens to fail before others in the registration order.

- `PublishSubscribeChannel` delivers every message to every subscriber — the direct opposite of `DirectChannel`'s round-robin, one-subscriber-per-message behavior (card 0008); confusing the two silently changes an application's actual delivery semantics.
- By default, dispatch is synchronous and sequential on the sender's thread — good for simplicity, but means a failing or slow subscriber directly affects both the sender and any not-yet-invoked subscribers.
- Supplying an `Executor` to the channel's constructor switches to asynchronous dispatch, decoupling both timing (the sender doesn't wait) and failure isolation (one subscriber's exception doesn't prevent others from running).
- Asynchronous dispatch trades away the synchronous guarantee that all subscribers have finished by the time `send()` returns — code relying on "every subscriber is done by now" needs an explicit coordination mechanism (like the `CountDownLatch` used purely for this demo) rather than assuming it from `send()`'s return.
- Reach for `PublishSubscribeChannel` specifically when several independent, unaware-of-each-other reactions need to happen for the same event — modeling that same requirement with multiple subscribers on a `DirectChannel` is a common and easy mistake that silently delivers each message to only one of them instead of all.
