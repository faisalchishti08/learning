---
card: spring-integration
gi: 8
slug: directchannel
title: "DirectChannel"
---

## 1. What it is

`DirectChannel` is Spring Integration's simplest and default `MessageChannel` implementation: when a message is sent, it's dispatched synchronously, directly to exactly one subscribed handler, on the same thread that called `send()`. There's no buffering, no queueing, and — with the default load-balancing dispatcher — if more than one handler subscribes to the same `DirectChannel`, messages are distributed round-robin across them rather than delivered to all of them (that "deliver to all subscribers" behavior belongs to `PublishSubscribeChannel`, card 0009).

## 2. Why & when

Most integration steps within a single application don't need the complexity or overhead of buffering, separate threads, or broker-style delivery guarantees — they just need "call this next step with this message," synchronously, as part of the same unit of work. `DirectChannel` exists to be exactly that: the lowest-overhead channel implementation, matching plain method-call semantics almost exactly, while still providing the decoupling benefits of the channel abstraction (card 0004) — the sender still doesn't need a direct reference to the handler, just to the channel.

Use `DirectChannel` when:

- Connecting sequential steps within a single logical flow where synchronous, same-thread dispatch is acceptable (and usually desirable, for simplicity and to preserve a single transactional context across the steps).
- The sender should be aware if the very next processing step fails — since dispatch is synchronous, an exception thrown by the handler propagates directly back to the sender's `send()` call.
- No decoupling of *timing* is needed (unlike `QueueChannel`, card 0010) — only decoupling of *identity/reference*, which `DirectChannel` still provides.

## 3. Core concept

Think of `DirectChannel` like handing a document directly to a colleague standing right next to you and waiting while they immediately act on it — there's no in-tray, no delay, and if they have a problem with the document, you find out about it right then and there, on the spot, since you're still standing there. This is the default, simplest kind of hand-off: nothing is buffered, nobody has to come back later to check an in-tray, and the two of you are, for that moment, working in lockstep.

```java
DirectChannel channel = new DirectChannel();
channel.subscribe(message -> System.out.println("Handling: " + message.getPayload()));

boolean sent = channel.send(MessageBuilder.withPayload("order-123").build());
// By the time send() returns, the subscriber has ALREADY finished handling the message —
// dispatch happened synchronously, on this same thread.
```

If more than one subscriber is registered on the same `DirectChannel`, the default dispatcher load-balances round-robin across them — each message goes to exactly one subscriber, rotating which one, rather than to all of them.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DirectChannel dispatches synchronously on the sender's own thread to exactly one subscriber, round-robin if more than one is registered">
  <rect x="20" y="80" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">send() caller</text>

  <line x1="160" y1="105" x2="220" y2="105" stroke="#3fb950" stroke-width="2" marker-end="url(#w1)"/>
  <text x="190" y="90" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">same thread</text>

  <rect x="230" y="60" width="150" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DirectChannel</text>
  <text x="305" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no buffer</text>
  <text x="305" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">round-robin if &gt;1 sub</text>

  <line x1="380" y1="105" x2="440" y2="105" stroke="#3fb950" stroke-width="2" marker-end="url(#w2)"/>

  <rect x="450" y="80" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="525" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ONE subscriber</text>

  <defs>
    <marker id="w1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="w2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

`send()` doesn't return until the (single) subscriber has finished handling the message — no buffering, no separate thread.

## 5. Runnable example

The scenario: an order-validation step feeding a processing step, starting with basic synchronous dispatch, then observing how an exception in the handler propagates directly back to the sender, and finally load-balancing across multiple worker subscribers.

### Level 1 — Basic

```java
// BasicDirectChannelDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicDirectChannelDemo {
    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();
        channel.subscribe(message -> System.out.println("Handling: " + message.getPayload()));

        System.out.println("Before send()");
        channel.send(MessageBuilder.withPayload("order-123").build());
        System.out.println("After send()"); // this only prints AFTER the handler has already run
    }
}
```

**How to run:** run with Spring Integration on the classpath: `java BasicDirectChannelDemo.java`. Expected output, in this exact order: `Before send()`, `Handling: order-123`, `After send()` — proving dispatch is synchronous: `send()` doesn't return control to the caller until the subscriber has completely finished.

### Level 2 — Intermediate

Because dispatch is synchronous and on the same thread, an exception thrown inside the subscriber propagates directly out of `send()` — the sender finds out about a downstream failure immediately, without needing separate error-handling machinery.

```java
// PropagatingExceptionDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class PropagatingExceptionDemo {
    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();
        channel.subscribe(message -> {
            String order = (String) message.getPayload();
            if (order.contains("INVALID")) {
                throw new IllegalArgumentException("Cannot process: " + order);
            }
            System.out.println("Handling: " + order);
        });

        try {
            channel.send(MessageBuilder.withPayload("INVALID-order-999").build());
        } catch (RuntimeException e) {
            // The exception thrown INSIDE the subscriber surfaces directly here, on the sender's own thread.
            System.out.println("Caught at sender: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:** run `java PropagatingExceptionDemo.java`. Expected output: `Caught at sender: Cannot process: INVALID-order-999` — Spring Integration wraps the handler's exception in a `MessageHandlingException` (hence `.getCause()` here), but the essential point holds: the failure surfaces synchronously, directly to the code that called `send()`, exactly as if it had called the handler method directly itself.

### Level 3 — Advanced

Registering multiple subscribers on the same `DirectChannel` demonstrates the default round-robin load-balancing dispatch — useful for spreading work across a small pool of equivalent worker handlers without any additional configuration.

```java
// LoadBalancedDirectChannelDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancedDirectChannelDemo {
    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();
        AtomicInteger worker1Count = new AtomicInteger();
        AtomicInteger worker2Count = new AtomicInteger();

        channel.subscribe(message -> {
            worker1Count.incrementAndGet();
            System.out.println("Worker 1 handling: " + message.getPayload());
        });
        channel.subscribe(message -> {
            worker2Count.incrementAndGet();
            System.out.println("Worker 2 handling: " + message.getPayload());
        });

        for (int i = 1; i <= 4; i++) {
            channel.send(MessageBuilder.withPayload("order-" + i).build());
        }

        System.out.println("Worker 1 handled: " + worker1Count.get() + " messages");
        System.out.println("Worker 2 handled: " + worker2Count.get() + " messages");
    }
}
```

**How to run:** run `java LoadBalancedDirectChannelDemo.java`. Expected output: each of the four messages is handled by exactly one worker, alternating — `Worker 1 handling: order-1`, `Worker 2 handling: order-2`, `Worker 1 handling: order-3`, `Worker 2 handling: order-4` — followed by `Worker 1 handled: 2 messages` and `Worker 2 handled: 2 messages`, demonstrating the default dispatcher's round-robin behavior: each message goes to exactly one subscriber, never both, rotating which one gets the next message.

## 6. Walkthrough

Tracing the four `send()` calls in `LoadBalancedDirectChannelDemo`, in execution order:

1. `channel.send(...)` for `"order-1"` is dispatched by `DirectChannel`'s default `LoadBalancingStrategy` to the first subscriber in its rotation — Worker 1 — which increments its counter and prints its handling message; `send()` doesn't return until this completes.
2. `channel.send(...)` for `"order-2"` is dispatched to the *next* subscriber in the rotation — Worker 2 this time, not Worker 1 again — which handles it and increments its own counter.
3. `channel.send(...)` for `"order-3"` rotates back to Worker 1.
4. `channel.send(...)` for `"order-4"` rotates back to Worker 2.
5. After all four sends complete, `worker1Count` holds `2` (having handled messages 1 and 3) and `worker2Count` holds `2` (having handled messages 2 and 4) — confirming that each individual message was handled by exactly one worker, with the channel's dispatcher alternating which one across successive sends, rather than delivering every message to both.

```
send("order-1") -> dispatcher picks Worker 1 -> Worker1Count=1
send("order-2") -> dispatcher picks Worker 2 -> Worker2Count=1
send("order-3") -> dispatcher picks Worker 1 -> Worker1Count=2
send("order-4") -> dispatcher picks Worker 2 -> Worker2Count=2
```

## 7. Gotchas & takeaways

> `DirectChannel` with multiple subscribers does **not** deliver each message to every subscriber — it round-robins, delivering each message to exactly one. This is a common point of confusion for anyone expecting "publish to everyone" behavior; that's `PublishSubscribeChannel`'s job (card 0009), not `DirectChannel`'s, and picking the wrong one silently changes an application's actual delivery semantics without any error being raised.

- `DirectChannel` is Spring Integration's default channel type and the lowest-overhead option — reach for it as the default choice for connecting sequential steps within one flow unless a specific reason (buffering, broadcast, ordering by priority) calls for something else.
- Because dispatch is synchronous, a slow or blocking handler directly slows down whatever called `send()` — there's no built-in decoupling of timing, unlike `QueueChannel` (card 0010).
- An exception thrown by a subscriber propagates directly back to the `send()` caller (wrapped in a `MessageHandlingException`), meaning error handling for a `DirectChannel`-based step usually belongs right around the `send()` call itself, not in some separate asynchronous error channel.
- Multiple subscribers on the same `DirectChannel` share work round-robin by default — a genuine, if simple, load-balancing mechanism useful for spreading a fixed pool of equivalent workers across incoming messages with zero extra configuration.
- Because `DirectChannel` dispatch happens on the caller's own thread, it naturally preserves whatever transactional or security context was active when `send()` was called — a property worth relying on deliberately, and one that's lost the moment a flow crosses into an asynchronous, thread-switching channel type.
