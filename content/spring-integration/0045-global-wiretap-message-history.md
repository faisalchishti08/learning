---
card: spring-integration
gi: 45
slug: global-wiretap-message-history
title: "Global wiretap & message history"
---

## 1. What it is

A wiretap is a `ChannelInterceptor` (card 0015) variant, `WireTap`, that copies every message passing through a channel to a separate "tap" channel, without affecting the original flow at all — the original message continues to its normal destination unchanged, while an identical copy is sent elsewhere purely for observation. A *global* wiretap applies this to every channel in the application at once (via a pattern-matching interceptor registered centrally) rather than being added to one channel individually. Message history is a related but distinct feature: a `history` header, when enabled, accumulates a record of every channel and endpoint a message has actually passed through, giving a complete trace of its journey after the fact.

## 2. Why & when

You reach for a global wiretap or message history specifically when you need visibility into a flow's actual behavior without modifying the flow's own logic:

- **You want to observe traffic on many (or all) channels for debugging or monitoring, without adding a custom interceptor to each one individually** — a global wiretap, configured once with a channel-name pattern, taps every matching channel automatically, including ones added to the application later.
- **You need to log or audit every message passing through the system**, sent to a logging or auditing subsystem, while the original flow proceeds completely unaffected — the tap channel is a parallel, non-interfering copy, not a detour.
- **You're debugging "which path did this message actually take through the flow"** — message history gives a definitive, chronological record of every channel a specific message visited, which is far more reliable than trying to reconstruct the path from scattered log statements across different endpoints.

## 3. Core concept

Think of a wiretap exactly like its namesake: a phone line where the actual call proceeds completely normally between the two original parties, while a separate listening line receives an identical copy of the conversation for someone else to monitor — neither original party's conversation is delayed, altered, or aware of the tap. Message history, by contrast, is like a passport with entry and exit stamps from every country a traveler actually visited — read the passport afterward, and the traveler's exact route is right there, page by page, in order.

```java
@Bean
public GlobalChannelInterceptorWrapper wireTapAllChannels() {
    WireTap wireTap = new WireTap("monitoringChannel");
    GlobalChannelInterceptorWrapper wrapper = new GlobalChannelInterceptorWrapper(wireTap);
    wrapper.setPatterns(new String[]{"*"}); // apply to EVERY channel in the application
    return wrapper;
}

@ServiceActivator(inputChannel = "monitoringChannel")
public void logTappedMessage(Message<?> message) {
    System.out.println("[monitor] " + message.getPayload() + " history=" + message.getHeaders().get(IntegrationMessageHeaderAccessor.HISTORY));
}
```

Every message on every channel matching the pattern gets a copy sent to `monitoringChannel`, and if message history is enabled, that copy's `history` header shows the complete list of channels the original message has passed through so far.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A global wiretap copies every message from any matching channel to a monitoring channel, without altering the original flow; message history accumulates the channels a message has passed through" >
  <rect x="20" y="30" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">channel A (orders)</text>

  <line x1="160" y1="50" x2="220" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#wt1)"/>
  <text x="330" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; continues NORMALLY to endpoint</text>

  <line x1="90" y1="70" x2="90" y2="110" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#wt2)"/>
  <text x="140" y="95" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">tap: identical copy</text>

  <rect x="20" y="120" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="90" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">monitoringChannel</text>

  <rect x="450" y="30" width="150" height="130" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="525" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">history header</text>
  <text x="525" y="75" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">1. orders</text>
  <text x="525" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">2. validOrders</text>
  <text x="525" y="115" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3. discountedOrders</text>
  <text x="525" y="145" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">the message's full journey</text>

  <defs>
    <marker id="wt1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wt2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The original flow is never delayed or altered by the tap; message history is a passive, accumulating record carried along on the message itself.

## 5. Runnable example

The scenario: an order flow needing centralized monitoring without touching its own endpoint logic, starting with a basic single-channel wiretap, then a pattern-based wiretap covering multiple channels, and finally message history tracing a message's full journey across several channels.

### Level 1 — Basic

```java
// BasicWireTapDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;

public class BasicWireTapDemo {
    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel monitoringChannel = new DirectChannel();

        orders.subscribe(m -> System.out.println("[normal flow] processed: " + m.getPayload()));
        monitoringChannel.subscribe(m -> System.out.println("[wiretap] observed a copy: " + m.getPayload()));

        // what a WireTap interceptor does for you: forward a COPY, without interfering with the original send
        orders.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                monitoringChannel.send(message); // send a COPY to the tap
                return message; // the ORIGINAL still proceeds, completely unaffected
            }
        });

        orders.send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java BasicWireTapDemo.java`. Expected output: `[wiretap] observed a copy: order-1` then `[normal flow] processed: order-1` — the wiretap's interceptor fires first (as part of `preSend`, before dispatch), and the original flow still processes the message exactly as it would have with no tap present at all.

### Level 2 — Intermediate

A *global* wiretap uses a pattern to match multiple channel names at once, rather than being manually added to each channel individually — modeled here by applying the same tapping interceptor to every channel in a small registry whose name matches a wildcard-style pattern.

```java
// PatternBasedGlobalWireTapDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Map;

public class PatternBasedGlobalWireTapDemo {
    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel refunds = new DirectChannel();
        DirectChannel internalDebugChannel = new DirectChannel(); // intentionally NOT matched by the pattern
        DirectChannel monitoringChannel = new DirectChannel();

        monitoringChannel.subscribe(m -> System.out.println("[global wiretap] " + m.getPayload()));

        Map<String, DirectChannel> allChannels = Map.of("orders", orders, "refunds", refunds, "internalDebug", internalDebugChannel);
        String pattern = "orders,refunds"; // simulates a GLOBAL wiretap's channel-name pattern

        // what registering a GlobalChannelInterceptorWrapper with a pattern does for you:
        for (var entry : allChannels.entrySet()) {
            if (pattern.contains(entry.getKey())) { // simple stand-in for real pattern matching
                entry.getValue().addInterceptor(new ChannelInterceptor() {
                    @Override
                    public Message<?> preSend(Message<?> message, MessageChannel channel) {
                        monitoringChannel.send(message);
                        return message;
                    }
                });
            }
        }

        orders.subscribe(m -> System.out.println("[orders] handled: " + m.getPayload()));
        refunds.subscribe(m -> System.out.println("[refunds] handled: " + m.getPayload()));
        internalDebugChannel.subscribe(m -> System.out.println("[internalDebug] handled: " + m.getPayload()));

        orders.send(MessageBuilder.withPayload("order-1").build());
        refunds.send(MessageBuilder.withPayload("refund-1").build());
        internalDebugChannel.send(MessageBuilder.withPayload("debug-event").build()); // NOT tapped
    }
}
```

How to run: `java PatternBasedGlobalWireTapDemo.java`. Expected output: `[global wiretap] order-1`, `[orders] handled: order-1`, `[global wiretap] refund-1`, `[refunds] handled: refund-1`, then finally `[internalDebug] handled: debug-event` with **no** corresponding `[global wiretap]` line — `internalDebug` was never matched by the pattern, so it was never tapped, exactly as a real global wiretap's pattern configuration would exclude channels not matching it.

### Level 3 — Advanced

Message history accumulates a chronological record of every channel a specific message has actually passed through — shown here by manually building up a `history` header as a message moves through a multi-step flow, giving a complete after-the-fact trace of its journey.

```java
// MessageHistoryDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.ArrayList;
import java.util.List;

public class MessageHistoryDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel validOrders = new DirectChannel();
        DirectChannel discountedOrders = new DirectChannel();

        // what enabling message history does for you: append the channel name at each hop
        discountedOrders.subscribe(m -> {
            @SuppressWarnings("unchecked")
            List<String> history = (List<String>) m.getHeaders().get("history");
            System.out.println("Final payload: " + m.getPayload());
            System.out.println("Full journey (message history): " + history);
        });

        validOrders.subscribe(m -> {
            @SuppressWarnings("unchecked")
            List<String> history = new ArrayList<>((List<String>) m.getHeaders().get("history"));
            history.add("discountedOrders");
            Order o = (Order) m.getPayload();
            discountedOrders.send(MessageBuilder.withPayload(new Order(o.id(), o.amount() * 0.9))
                .setHeader("history", history).build());
        });

        orders.subscribe(m -> {
            List<String> history = new ArrayList<>(List.of("orders"));
            history.add("validOrders");
            validOrders.send(MessageBuilder.fromMessage(m).setHeader("history", history).build());
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build());
    }
}
```

How to run: `java MessageHistoryDemo.java`. Expected output: `Final payload: Order[id=ORD-1, amount=90.0]` then `Full journey (message history): [orders, validOrders, discountedOrders]` — even though the message's *payload* changed along the way (plain order to discounted order), its accumulated `history` header preserved a complete, ordered record of every channel it actually passed through, from origin to final destination.

## 6. Walkthrough

Tracing `MessageHistoryDemo` in execution order:

1. `orders.send(...)` triggers the subscriber on `orders`, which builds an initial history list containing `"orders"` (the channel the message started on), then appends `"validOrders"` (the channel it's about to be sent to next) — this two-entry list is stamped onto a new message as its `history` header, then sent to `validOrders`.
2. `validOrders`'s subscriber receives that message, reads its current `history` header (`["orders", "validOrders"]`), copies it into a new mutable list, and appends `"discountedOrders"` — the channel it's about to forward to next — before building a new message carrying both the transformed `Order` payload and this now three-entry history.
3. `discountedOrders`'s subscriber receives the final message, whose `history` header now reads `["orders", "validOrders", "discountedOrders"]` — a complete, ordered record of every channel this specific message instance actually traveled through, accumulated one hop at a time.
4. Critically, the payload itself changed between steps (the original order became a discounted order), but the history header tracked the *channel journey*, independent of whatever payload transformations happened along the way — the two concerns (data transformation and path tracing) are entirely orthogonal.
5. In a real Spring Integration application, this exact accumulation happens automatically once message history is enabled (`spring.integration.channel.auto-create` and related history configuration), without every endpoint needing to manually copy and append to a header the way this simulation does explicitly.
6. The final printed history gives a debugging tool no amount of scattered per-endpoint logging could easily replicate: a single, authoritative, in-order list of exactly where this one specific message actually went.

```
orders.send(Order)
  -> orders subscriber: history=[orders, validOrders] -> validOrders.send(...)
  -> validOrders subscriber: history=[orders, validOrders, discountedOrders] -> discountedOrders.send(...)
  -> discountedOrders subscriber: prints final payload + full history
```

## 7. Gotchas & takeaways

> A global wiretap applied with an overly broad pattern (e.g., matching every channel in a high-throughput application) doubles the message volume flowing through the tapped channels' interceptor chain and adds load to whatever consumes the tap channel — it's easy to underestimate this cost, since the tap itself is designed to be invisible to the original flow's correctness, but it is never invisible to the system's overall throughput and resource usage. Scope wiretap patterns as narrowly as the actual monitoring need requires, and ensure the tap channel's consumer can keep up with the traffic it's now receiving.

- A wiretap copies every message from a channel to a separate tap channel, without altering the original flow's behavior at all — a global wiretap applies this via a pattern matching many channels at once, rather than per-channel manual configuration.
- Use a global wiretap for centralized monitoring, logging, or auditing across many (or all) channels without modifying each flow's own endpoint logic.
- Message history accumulates a chronological record of every channel a specific message has actually passed through, carried on the message itself via a `history` header — a definitive trace, distinct from (and complementary to) the wiretap's real-time observation.
- Message history tracks the *channel journey*, independent of whatever payload transformations happen along the way — a message's payload can change completely while its history still accurately reflects the path it traveled.
- Scope a global wiretap's pattern as narrowly as the actual need requires — an overly broad pattern adds real throughput and load cost across the tapped channels and their consumer, even though it never affects the tapped flow's own correctness.
