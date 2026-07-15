---
card: spring-integration
gi: 29
slug: bridge
title: "Bridge"
---

## 1. What it is

A `Bridge` (`@BridgeFrom`/`@BridgeTo`, or a `<bridge>` element in XML configuration) is the simplest possible endpoint: it connects two channels directly, forwarding every message from the input channel to the output channel unchanged — no transformation, no filtering, no routing decision. Its entire job is connecting two channels of potentially different *types* (e.g., a `QueueChannel`, card 0010, to a `DirectChannel`, card 0008), which otherwise have no automatic way to hand messages to each other.

## 2. Why & when

You reach for `Bridge` specifically when two channels need to be connected but nothing about the message itself needs to change:

- **A pollable channel (`QueueChannel`) needs to feed a subscribable channel (`DirectChannel`)**, or vice versa — these two channel families don't automatically connect to each other; a poller-backed `Bridge` is what actively pulls from the queue and pushes into the direct channel's subscribers.
- **You want a clean seam in a flow's wiring** — a named connection point between two logical stages, useful for later inserting a `ChannelInterceptor` (card 0015) or swapping one channel implementation for another without touching either side's actual endpoint logic.
- **A flow's configuration needs an explicit "and then just forward this" step**, often at integration boundaries where one subsystem's output channel needs to become another subsystem's input channel, with the bridge as the deliberate, visible connector between them.

## 3. Core concept

Think of a `Bridge` like a simple footbridge connecting two riverbanks that would otherwise have no way to reach each other — nothing on the bridge changes who's crossing it, no toll booth inspects them, no fork sends them different directions. It exists purely to make the crossing physically possible where the two banks (channel types) don't naturally meet.

```java
@Bean
@BridgeFrom("pollableChannel")
public MessageChannel directChannel() {
    return new DirectChannel();
}
```

Every message that arrives on `pollableChannel` (a `QueueChannel`, requiring a poller to drain it) is bridged straight through to `directChannel` — the bridge itself contains no logic beyond "receive from one side, send to the other," with a poller doing the actual pulling for the pollable side.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bridge connects a pollable QueueChannel to a subscribable DirectChannel, forwarding every message unchanged via a poller">
  <rect x="20" y="50" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">QueueChannel</text>
  <text x="95" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pollable</text>

  <line x1="170" y1="75" x2="240" y2="75" stroke="#6db33f" stroke-width="2" marker-end="url(#br1)"/>
  <text x="205" y="60" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">poller drains</text>

  <rect x="250" y="55" width="110" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Bridge</text>

  <line x1="360" y1="75" x2="420" y2="75" stroke="#79c0ff" stroke-width="2" marker-end="url(#br2)"/>

  <rect x="430" y="50" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="505" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DirectChannel</text>
  <text x="505" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">subscribable</text>

  <defs>
    <marker id="br1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="br2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The bridge does nothing to the message itself — its only job is making the crossing between two otherwise-incompatible channel types possible.

## 5. Runnable example

The scenario: a queue-based intake channel needing to feed a direct-dispatch processing channel, starting with a basic manual bridge, then a poller-driven bridge running continuously, and finally a bridge combined with an interceptor as an insertion seam.

### Level 1 — Basic

```java
// BasicBridgeDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicBridgeDemo {
    public static void main(String[] args) {
        QueueChannel pollableChannel = new QueueChannel();
        DirectChannel directChannel = new DirectChannel();
        directChannel.subscribe(m -> System.out.println("Processed via direct dispatch: " + m.getPayload()));

        pollableChannel.send(MessageBuilder.withPayload("order-1").build());

        // what a Bridge does for you: receive() from one side, send() to the other
        var message = pollableChannel.receive();
        directChannel.send(message);
    }
}
```

How to run: `java BasicBridgeDemo.java`. Expected output: `Processed via direct dispatch: order-1` — the message crossed from a pollable queue channel to a subscribable direct channel, unchanged, via the bridge's simple receive-then-send.

### Level 2 — Intermediate

A real bridge is poller-driven, continuously draining the pollable side on a schedule rather than requiring a manual `receive()`/`send()` call per message — modeled here with a background thread polling every 100ms.

```java
// PollerDrivenBridgeDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class PollerDrivenBridgeDemo {
    public static void main(String[] args) throws InterruptedException {
        QueueChannel pollableChannel = new QueueChannel();
        DirectChannel directChannel = new DirectChannel();
        directChannel.subscribe(m -> System.out.println("Processed via direct dispatch: " + m.getPayload()));

        // what a poller-backed Bridge does continuously, on its own schedule:
        Thread bridgePoller = new Thread(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                Message<?> message = pollableChannel.receive(200); // poll with a timeout
                if (message != null) {
                    directChannel.send(message);
                }
            }
        });
        bridgePoller.setDaemon(true);
        bridgePoller.start();

        pollableChannel.send(MessageBuilder.withPayload("order-1").build());
        Thread.sleep(50);
        pollableChannel.send(MessageBuilder.withPayload("order-2").build());
        Thread.sleep(300); // let the poller drain both
    }
}
```

How to run: `java PollerDrivenBridgeDemo.java`. Expected output: `Processed via direct dispatch: order-1` followed by `Processed via direct dispatch: order-2` — both messages, sent at different times, are picked up automatically by the background polling loop without any manual intervention per message.

### Level 3 — Advanced

A bridge is a natural insertion point for a `ChannelInterceptor` (card 0015) — since it's already the deliberate seam between two channels, attaching cross-cutting logic (logging, metrics) at the bridge captures every message crossing that specific boundary, without needing to modify either side's actual endpoint.

```java
// BridgeWithInterceptorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;

public class BridgeWithInterceptorDemo {
    public static void main(String[] args) {
        QueueChannel pollableChannel = new QueueChannel();
        DirectChannel directChannel = new DirectChannel();
        directChannel.subscribe(m -> System.out.println("Processed: " + m.getPayload()));

        // an interceptor on the OUTPUT side of the bridge: observes every message crossing this seam
        directChannel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                System.out.println("[bridge seam] crossing: " + message.getPayload());
                return message;
            }
        });

        pollableChannel.send(MessageBuilder.withPayload("order-1").build());
        pollableChannel.send(MessageBuilder.withPayload("order-2").build());

        // bridge logic: drain everything currently queued, forward each
        Message<?> m;
        while ((m = pollableChannel.receive(100)) != null) {
            directChannel.send(m);
        }
    }
}
```

How to run: `java BridgeWithInterceptorDemo.java`. Expected output: `[bridge seam] crossing: order-1`, `Processed: order-1`, `[bridge seam] crossing: order-2`, `Processed: order-2` — every message crossing the bridge is observed by the interceptor, without either the queue-side producer or the direct-side consumer needing to know the interceptor exists.

## 6. Walkthrough

Tracing `PollerDrivenBridgeDemo` in execution order:

1. The background `bridgePoller` thread starts immediately and enters its loop, calling `pollableChannel.receive(200)` — this blocks (up to 200ms) waiting for a message, exactly like `QueueChannel`'s `receive()` behavior from card 0010.
2. `pollableChannel.send("order-1")` on the main thread places a message onto the queue; the poller thread's blocked `receive(200)` call unblocks almost immediately, returning that message.
3. The poller thread calls `directChannel.send(message)` — since `DirectChannel` dispatches synchronously, this immediately triggers the subscribed handler, printing `Processed via direct dispatch: order-1`, before the poller loop continues.
4. The poller loop immediately calls `receive(200)` again, this time blocking since nothing new has arrived yet.
5. After the main thread's 50ms sleep, `pollableChannel.send("order-2")` places a second message onto the queue, and the same unblock-forward-print sequence repeats for it.
6. The bridge's entire contribution across both messages was purely mechanical: continuously drain one channel type, forward to the other — no logic about the payload's content ever entered into it.

```
poller thread: receive(200) [BLOCKS] -> order-1 arrives -> unblocks -> directChannel.send(order-1) -> printed
poller thread: receive(200) [BLOCKS] -> order-2 arrives -> unblocks -> directChannel.send(order-2) -> printed
```

## 7. Gotchas & takeaways

> It's easy to reach for a `Bridge` where a `Transformer` (card 0021) or another endpoint archetype was actually needed — if there's ever a reason to inspect, modify, filter, or route the message, that's a signal the connection isn't "just a bridge" anymore. Keep bridges genuinely trivial (pure pass-through); the moment any logic creeps in, name the endpoint for what it actually does instead.

- `Bridge` connects two channels directly, forwarding every message unchanged — its sole purpose is making a connection possible between channel types that don't automatically interoperate (typically pollable to subscribable, or vice versa).
- Use it to connect a `QueueChannel`-family channel to a `DirectChannel`-family channel (or across other channel type boundaries), with a poller driving the pollable side.
- A bridge is a natural, deliberate seam for attaching a `ChannelInterceptor` (card 0015), since it already marks a clear boundary between two logical stages of a flow.
- Keep bridges free of actual logic — the moment content-based decisions are involved, a different endpoint archetype (`Transformer`, `Filter`, `Router`) is almost certainly the more honest fit.
- A poller-backed bridge's polling interval directly affects latency between a message landing on the pollable side and reaching the subscribable side — a longer poll interval trades responsiveness for lower polling overhead.
