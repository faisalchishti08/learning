---
card: spring-integration
gi: 12
slug: rendezvouschannel
title: "RendezvousChannel"
---

## 1. What it is

`RendezvousChannel` is a `MessageChannel` implementation, in the same `QueueChannel`-family (card 0010) as `PriorityChannel` (card 0011), but with zero capacity: it is backed by a `SynchronousQueue` rather than a buffering queue. A `send()` call does not return until a consumer is actively waiting and calls `receive()` to accept that exact message — the two calls must happen at the same moment, a genuine hand-off, with no intermediate storage at all.

## 2. Why & when

You reach for `RendezvousChannel` specifically when you need the sender to know, synchronously, that a consumer has actually taken the message — not merely that it was queued:

- **You want direct hand-off confirmation**, not just "it's somewhere in a buffer." `send()` returning tells you a consumer was there, ready, and took it at that instant — a stronger guarantee than `QueueChannel`'s "it's queued, someone will get to it eventually."
- **You want to throttle a producer to exactly the consumer's pace**, with zero buffering in between — useful when buffering itself is undesirable (e.g., messages represent physical resource handoffs, or staleness in a buffer would be actively harmful).
- **You're building a strict producer/consumer rendezvous point** — analogous to Go's unbuffered channels or `java.util.concurrent.SynchronousQueue` directly — where the coordination guarantee itself, not throughput, is the point.

## 3. Core concept

Think of `RendezvousChannel` like a relay race baton hand-off, as opposed to `QueueChannel`'s in-tray. In a relay race, the outgoing runner does not simply drop the baton on the ground and run off (that would be a queue); they physically hold it until the incoming runner's hand is there to take it, at the same moment, in the same place. Neither runner can "finish" the hand-off alone — both must be present simultaneously.

```java
RendezvousChannel channel = new RendezvousChannel();

// on one thread:
channel.send(MessageBuilder.withPayload("token").build()); // BLOCKS until a receiver is ready

// on another thread, happening around the same time:
Message<?> received = channel.receive(); // BLOCKS until a sender is ready
```

Neither call can complete on its own — `send()` blocks until a `receive()` is simultaneously waiting (and vice versa), which is exactly the zero-capacity, direct-hand-off behavior a `SynchronousQueue` provides underneath.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RendezvousChannel: send() and receive() both block until they happen simultaneously, with zero buffering in between">
  <rect x="20" y="80" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sender thread</text>
  <text x="90" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">send() BLOCKS</text>

  <rect x="250" y="65" width="140" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RendezvousChannel</text>
  <text x="320" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">zero capacity</text>
  <text x="320" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">direct hand-off only</text>

  <rect x="480" y="80" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">receiver thread</text>
  <text x="550" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">receive() BLOCKS</text>

  <line x1="160" y1="105" x2="248" y2="105" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <line x1="392" y1="105" x2="478" y2="105" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="320" y="45" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">both unblock ONLY at the same instant</text>
  <line x1="200" y1="55" x2="440" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#r1)" marker-start="url(#r2)"/>

  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M7,0 L0,3 L7,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

There is no buffer between the two boxes — the message passes directly from sender to receiver only when both are simultaneously present.

## 5. Runnable example

The scenario: a control-plane handing an authorization token directly from an issuing thread to a waiting consumer thread, starting with a basic blocking hand-off, then observing what happens when no consumer is ready, and finally a timed hand-off used as a readiness gate between two worker stages.

### Level 1 — Basic

```java
// BasicRendezvousDemo.java
import org.springframework.integration.channel.RendezvousChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicRendezvousDemo {
    public static void main(String[] args) throws InterruptedException {
        RendezvousChannel channel = new RendezvousChannel();

        Thread receiver = new Thread(() -> {
            Message<?> received = channel.receive();
            System.out.println("Receiver got: " + received.getPayload());
        });
        receiver.start();

        Thread.sleep(100); // give the receiver thread time to reach receive() and start waiting
        System.out.println("Sender about to send() — a receiver is already waiting");
        channel.send(MessageBuilder.withPayload("token-abc").build());
        System.out.println("send() returned — hand-off confirmed complete");

        receiver.join();
    }
}
```

How to run: `java BasicRendezvousDemo.java`. Expected output: `Sender about to send()...`, `send() returned — hand-off confirmed complete`, then `Receiver got: token-abc` — `send()` only returns once the waiting receiver has actually taken the message.

### Level 2 — Intermediate

Unlike `QueueChannel`, sending to a `RendezvousChannel` with nobody currently waiting doesn't queue the message anywhere — the sender genuinely blocks until a consumer shows up, which can be a real production hazard if you don't account for it (a `send()` with no timeout, and no receiver ever arriving, blocks forever).

```java
// TimedSendNoReceiverDemo.java
import org.springframework.integration.channel.RendezvousChannel;
import org.springframework.messaging.support.MessageBuilder;

public class TimedSendNoReceiverDemo {
    public static void main(String[] args) {
        RendezvousChannel channel = new RendezvousChannel();

        System.out.println("Attempting send() with a 1-second timeout, no receiver is waiting...");
        long start = System.currentTimeMillis();
        boolean sent = channel.send(MessageBuilder.withPayload("token-xyz").build(), 1000);
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("send() returned: " + sent + " after ~" + elapsed + "ms");
        // sent == false: the timeout elapsed with no receiver ever showing up to complete the hand-off
    }
}
```

How to run: `java TimedSendNoReceiverDemo.java`. Expected output: `send() returned: false after ~1000ms` — with no receiver ever ready, the timed `send()` gives up and returns `false` rather than blocking indefinitely, which is the safe way to use `RendezvousChannel` when a receiver's presence isn't guaranteed.

### Level 3 — Advanced

Using a `RendezvousChannel` as a readiness gate between two worker stages: stage one does setup work, then rendezvouses to hand off a "ready" signal to stage two, guaranteeing stage two never proceeds before stage one has genuinely reached that point — a stronger guarantee than a shared boolean flag, since the hand-off itself is the synchronization.

```java
// ReadinessGateDemo.java
import org.springframework.integration.channel.RendezvousChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.CountDownLatch;

public class ReadinessGateDemo {
    public static void main(String[] args) throws InterruptedException {
        RendezvousChannel gate = new RendezvousChannel();
        CountDownLatch done = new CountDownLatch(1);

        Thread stageTwo = new Thread(() -> {
            System.out.println("Stage two waiting at the gate...");
            gate.receive(); // blocks until stage one rendezvouses here
            System.out.println("Stage two proceeding — stage one is CONFIRMED ready");
            done.countDown();
        });
        stageTwo.start();

        Thread stageOne = new Thread(() -> {
            System.out.println("Stage one doing setup work...");
            try { Thread.sleep(300); } catch (InterruptedException ignored) {}
            System.out.println("Stage one setup complete, signaling readiness via rendezvous");
            gate.send(MessageBuilder.withPayload("ready").build()); // blocks until stage two is there to receive
            System.out.println("Stage one confirmed stage two received the signal");
        });
        stageOne.start();

        done.await();
    }
}
```

How to run: `java ReadinessGateDemo.java`. Expected output shows `Stage two waiting at the gate...` and `Stage one doing setup work...` in either order, then (after ~300ms) `Stage one setup complete, signaling readiness via rendezvous`, immediately followed by `Stage two proceeding — stage one is CONFIRMED ready` and `Stage one confirmed stage two received the signal` — proving stage two genuinely cannot proceed until the exact moment stage one's `send()` completes the hand-off.

## 6. Walkthrough

Tracing `ReadinessGateDemo` in execution order:

1. `stageTwo` starts first (or concurrently) and immediately calls `gate.receive()`, which blocks — there is nothing in the (zero-capacity) channel yet, and no sender is present.
2. `stageOne` starts and performs simulated setup work (`Thread.sleep(300)`) — during this entire window, `stageTwo` remains blocked on `receive()`, since a `RendezvousChannel` has no buffer for `stageOne` to place anything into early.
3. Once setup finishes, `stageOne` calls `gate.send(...)`. At this exact point, both a sender and a waiting receiver are simultaneously present, so the `SynchronousQueue` underneath completes the hand-off atomically: `receive()` on `stageTwo` and `send()` on `stageOne` both unblock together.
4. `stageTwo` resumes with the received message, prints its confirmation, and counts down the latch.
5. `stageOne`'s `send()` call also returns at that same moment, and it prints its own confirmation that the hand-off is complete — both sides now know, with certainty, that the other reached this point.
6. The main thread's `done.await()` unblocks once `stageTwo` finishes, and the program exits.

```
stageTwo: receive() -------- BLOCKS -----------------------+
stageOne: [setup work, 300ms] ---- send() --- HANDOFF ------+---> both unblock simultaneously
                                                             |
                                                    stageTwo proceeds, stageOne confirms
```

## 7. Gotchas & takeaways

> An untimed `send()` (or `receive()`) on a `RendezvousChannel` with no counterpart ever arriving blocks forever — there is no buffer to fall back on, unlike `QueueChannel`. In production code, always use the timed overloads (`send(message, timeout)` / `receive(timeout)`) unless a permanently-blocking wait is genuinely the intended behavior, to avoid a thread hanging indefinitely on a rendezvous that never happens.

- `RendezvousChannel` has zero capacity — `send()` and `receive()` must happen at essentially the same instant, a direct hand-off with no intermediate storage, unlike `QueueChannel` (card 0010) or `PriorityChannel` (card 0011).
- Use it when the sender genuinely needs hand-off confirmation, not just "it's queued somewhere" — or when you want to throttle a producer to exactly a consumer's pace with zero buffering.
- Always prefer the timed `send`/`receive` overloads in production; an untimed call with no counterpart ever arriving blocks the calling thread indefinitely.
- It's still a `QueueChannel`-family channel underneath (backed by a `SynchronousQueue`, capacity zero), so it shares the same basic `MessageChannel` API — the difference is purely the buffering behavior, not the interface.
- Because there's no buffering, a burst of sends cannot be "absorbed" the way `QueueChannel` absorbs one — each `send()` in a burst must wait for its own dedicated `receive()`, so throughput is strictly bounded by how fast receivers show up, not by any queue depth.
