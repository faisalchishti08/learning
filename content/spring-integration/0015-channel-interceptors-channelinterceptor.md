---
card: spring-integration
gi: 15
slug: channel-interceptors-channelinterceptor
title: "Channel interceptors (ChannelInterceptor)"
---

## 1. What it is

`ChannelInterceptor` is an interface you implement to observe or modify messages as they pass through a channel, without touching the channel's own send/receive logic or the endpoints on either side. A channel (any of the types in cards 0008–0014) can have any number of interceptors registered on it; each interceptor's callback methods — `preSend`, `postSend`, `preReceive`, `postReceive`, and a few others — fire automatically at the corresponding point in the message's journey through that channel.

## 2. Why & when

You reach for `ChannelInterceptor` specifically when you need cross-cutting behavior applied uniformly to every message on a channel, without modifying every handler that touches it:

- **Logging or metrics need to observe every message on a channel** — how many messages pass through, their payload types, timing between send and receive — without scattering logging calls across every handler subscribed to that channel.
- **You need to veto or modify a message before it's actually dispatched**, such as rejecting messages that fail a validation check, or enriching every message with a common header (a correlation ID, a timestamp) — `preSend` can return `null` to block the send entirely, or return a modified `Message` to substitute.
- **You want the same behavior applied consistently across multiple different channels** (e.g., every channel in a subsystem gets the same tracing interceptor) by registering the interceptor on each, rather than duplicating logic inside each channel's handlers.

## 3. Core concept

Think of `ChannelInterceptor` like airport security checkpoints positioned along a walkway, as opposed to a bouncer at a single door. Every message that walks down that particular corridor (channel) passes through the checkpoint, gets observed (and possibly stopped or stamped) at each point, and continues on — the checkpoint doesn't care who owns the corridor's endpoints, and multiple checkpoints can be stacked along the same corridor, each running in registration order.

```java
DirectChannel channel = new DirectChannel();
channel.addInterceptor(new ChannelInterceptor() {
    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        System.out.println("About to send: " + message.getPayload());
        return message; // return null here would VETO the send entirely
    }
    @Override
    public void postSend(Message<?> message, MessageChannel channel, boolean sent) {
        System.out.println("Send completed, sent=" + sent);
    }
});
```

`preSend` runs before the message reaches any subscriber, and can transform or veto it; `postSend` runs after dispatch completes (regardless of success), purely for observation — the pattern repeats symmetrically for `preReceive`/`postReceive` on pollable channels.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ChannelInterceptor callbacks fire around send: preSend can modify or veto, postSend observes the outcome, before the message reaches subscribers">
  <rect x="20" y="75" width="110" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send()</text>

  <line x1="130" y1="97" x2="180" y2="97" stroke="#6db33f" stroke-width="2" marker-end="url(#i1)"/>

  <rect x="190" y="30" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">preSend()</text>
  <text x="255" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">modify or veto</text>

  <line x1="255" y1="70" x2="255" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#i3)"/>

  <rect x="190" y="115" width="130" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="255" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">channel dispatch</text>
  <text x="255" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">to subscribers</text>

  <line x1="320" y1="97" x2="380" y2="97" stroke="#79c0ff" stroke-width="2" marker-end="url(#i2)"/>

  <rect x="390" y="75" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="455" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">postSend()</text>
  <text x="455" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">observe outcome</text>

  <defs>
    <marker id="i1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="i2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="i3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`preSend` runs first and can alter or block the message; only if it isn't vetoed does dispatch proceed, followed by `postSend`'s observation of the result.

## 5. Runnable example

The scenario: an order channel needing a correlation ID stamped on every message, then request validation that vetoes bad messages, and finally end-to-end timing across a stack of multiple interceptors.

### Level 1 — Basic

```java
// BasicInterceptorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;
import java.util.UUID;

public class BasicInterceptorDemo {
    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();
        channel.subscribe(m -> System.out.println("Handled with correlationId=" + m.getHeaders().get("correlationId")));

        channel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                String id = UUID.randomUUID().toString().substring(0, 8);
                System.out.println("preSend: stamping correlationId=" + id);
                return MessageBuilder.fromMessage(message).setHeader("correlationId", id).build();
            }
        });

        channel.send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java BasicInterceptorDemo.java`. Expected output: `preSend: stamping correlationId=XXXXXXXX` followed by `Handled with correlationId=XXXXXXXX` with the same ID — proving the message returned from `preSend` (with the added header) is what actually reaches the subscribed handler, not the original.

### Level 2 — Intermediate

`preSend` returning `null` vetoes the send entirely — no subscriber is invoked, and `postSend` still fires with `sent=false`, letting validation logic reject messages transparently to callers who only look at the channel, not each handler.

```java
// ValidatingInterceptorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;

public class ValidatingInterceptorDemo {
    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();
        channel.subscribe(m -> System.out.println("Handler processed: " + m.getPayload()));

        channel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                String payload = (String) message.getPayload();
                if (payload.isBlank()) {
                    System.out.println("preSend: REJECTING blank payload");
                    return null; // VETO — handler will never be invoked
                }
                return message;
            }
            @Override
            public void postSend(Message<?> message, MessageChannel channel, boolean sent) {
                System.out.println("postSend: sent=" + sent + " for payload='" + message.getPayload() + "'");
            }
        });

        channel.send(MessageBuilder.withPayload("order-1").build()); // valid
        channel.send(MessageBuilder.withPayload("").build());        // vetoed
    }
}
```

How to run: `java ValidatingInterceptorDemo.java`. Expected output: `postSend: sent=true` and `Handler processed: order-1` for the first message, but for the second, `preSend: REJECTING blank payload` followed by `postSend: sent=false` and **no** `Handler processed` line — the handler is never invoked for the vetoed message.

### Level 3 — Advanced

Multiple interceptors stack in registration order for `preSend` and reverse order for `postSend` (like nested try/finally blocks), which lets one interceptor measure elapsed time across everything registered after it — a common pattern for end-to-end channel-level tracing.

```java
// TimingInterceptorStackDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;

public class TimingInterceptorStackDemo {
    public static void main(String[] args) throws InterruptedException {
        DirectChannel channel = new DirectChannel();
        channel.subscribe(m -> {
            System.out.println("Handler working...");
            try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        });

        // Registered FIRST: its preSend runs first, its postSend runs LAST (outermost)
        channel.addInterceptor(new ChannelInterceptor() {
            long start;
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                start = System.currentTimeMillis();
                System.out.println("Timing interceptor: preSend (outer)");
                return message;
            }
            @Override
            public void postSend(Message<?> message, MessageChannel channel, boolean sent) {
                System.out.println("Timing interceptor: postSend (outer) — elapsed=" + (System.currentTimeMillis() - start) + "ms");
            }
        });

        // Registered SECOND: its preSend runs second, its postSend runs FIRST (innermost)
        channel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                System.out.println("Logging interceptor: preSend (inner)");
                return message;
            }
            @Override
            public void postSend(Message<?> message, MessageChannel channel, boolean sent) {
                System.out.println("Logging interceptor: postSend (inner)");
            }
        });

        channel.send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java TimingInterceptorStackDemo.java`. Expected output order: `Timing interceptor: preSend (outer)`, `Logging interceptor: preSend (inner)`, `Handler working...`, `Logging interceptor: postSend (inner)`, `Timing interceptor: postSend (outer) — elapsed=~100ms` — the outer interceptor's `postSend` runs last, letting it measure the full duration including everything nested inside it.

## 6. Walkthrough

Tracing `TimingInterceptorStackDemo` in execution order:

1. `channel.send(...)` first invokes `preSend` on the timing interceptor (registered first), which records a start timestamp and prints its message — this runs before the message has been touched by anything else.
2. The (unmodified) message is then passed to the logging interceptor's `preSend`, which prints its own message — both interceptors have now had a chance to inspect or modify the message before dispatch.
3. Only after both `preSend` calls succeed (neither returned `null`) does the channel actually dispatch to the subscribed handler, which prints `Handler working...` and sleeps 100ms to simulate work.
4. Once the handler returns, `postSend` callbacks fire in **reverse** registration order: the logging interceptor's `postSend` (registered second) runs first, printing its message.
5. Finally, the timing interceptor's `postSend` (registered first) runs last, computing `System.currentTimeMillis() - start` — because it wraps everything registered after it, this elapsed time includes both the logging interceptor's work and the handler's 100ms sleep.
6. The reverse-order `postSend` execution is exactly analogous to nested `try`/`finally`: the first interceptor registered is the outermost wrapper, so its "after" logic naturally runs last, after everything nested inside has completed.

```
preSend:  timing(outer) -> logging(inner) -> [handler runs, ~100ms]
postSend: logging(inner) -> timing(outer)   <- reverse order, timing sees FULL elapsed time
```

## 7. Gotchas & takeaways

> A `preSend` implementation that returns `null` silently drops the message — no exception, no handler invocation, just a `postSend` callback with `sent=false`. If validation logic relies on this to reject bad input, make sure something (logging in `postSend`, or a dedicated monitoring interceptor) actually surfaces the rejection; otherwise messages can vanish with no visible trace of why.

- `ChannelInterceptor` lets cross-cutting logic (logging, metrics, validation, header enrichment) observe or modify every message on a channel, without touching the channel's handlers.
- `preSend` can transform the message (by returning a different `Message` instance) or veto the send entirely (by returning `null`); `postSend` is purely observational, firing after dispatch regardless of outcome.
- Multiple interceptors run `preSend` in registration order and `postSend` in reverse registration order — the same nesting discipline as `try`/`finally` blocks, useful for span-style timing.
- Interceptors apply per-channel; register the same interceptor instance (or equivalent instances) on multiple channels if the cross-cutting behavior needs to apply consistently across a subsystem.
- Because `preSend` runs synchronously in the caller's `send()` call (for synchronous channels like `DirectChannel`), expensive work inside an interceptor directly slows down every sender on that channel — keep interceptor logic lightweight, or dispatch heavy work asynchronously from within it.
