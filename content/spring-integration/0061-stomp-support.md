---
card: spring-integration
gi: 61
slug: stomp-support
title: "STOMP support"
---

## 1. What it is

STOMP support (`Stomp.inboundAdapter(...)`/`Stomp.outboundAdapter(...)`) connects a flow to a broker over STOMP (Simple/Streaming Text Oriented Messaging Protocol) — a deliberately simple, text-based, HTTP-like messaging protocol commonly used as the wire protocol beneath WebSocket-based messaging (including Spring's own STOMP-over-WebSocket support for browser clients). Unlike the binary, broker-specific protocols underlying JMS (card 0057), AMQP (card 0058), or MQTT (card 0060), STOMP frames are plain text, human-readable, and structured similarly to HTTP requests — a command line, a set of headers, and a body — making STOMP a natural fit whenever a browser or other simple client needs to speak a messaging protocol directly.

## 2. Why & when

You reach for STOMP support specifically when the integration point communicates via STOMP frames, most commonly bridging a flow to browser-based, WebSocket-connected clients:

- **Browser clients need to send and receive messages over a persistent connection**, and STOMP-over-WebSocket is the standard way Spring applications expose that — a flow using STOMP support can publish to destinations that connected browser clients are subscribed to, or receive messages a browser client sends, without the browser needing to speak any broker-specific binary protocol directly.
- **A simple, debuggable, text-based protocol is valuable** — because STOMP frames are plain text and structurally similar to HTTP, they're straightforward to read directly in network traces or logs while debugging, unlike a binary protocol that requires specialized tooling to inspect.
- **You need a lightweight bridge between a full-featured broker (like RabbitMQ, which supports STOMP as one of several protocols it can speak) and STOMP-only clients** — some brokers expose a STOMP interface specifically to serve simpler or browser-based clients alongside their native, richer protocol.

## 3. Core concept

Think of a STOMP frame like a simple, handwritten note using a fixed, predictable format — a command word at the top (`SEND`, `SUBSCRIBE`, `MESSAGE`), a few labeled fields below it (headers, like a note's "To:" and "From:" lines), and the actual content underneath, followed by a clear terminator. Compare this to a broker's native binary protocol, which is more like a densely-packed, machine-optimized data structure — efficient to parse programmatically, but not something a human could casually read by glancing at it; STOMP deliberately trades some of that efficiency for simplicity and universal readability.

```java
@Bean
public IntegrationFlow stompOutboundFlow(StompSessionManager sessionManager) {
    return IntegrationFlow.from("orderStatusUpdates")
        .handle(Stomp.outboundAdapter(sessionManager)
            .destination("/topic/order-status")) // browser clients subscribed to this destination receive it
        .get();
}
```

A raw STOMP `SEND` frame for this looks roughly like:
```
SEND
destination:/topic/order-status
content-type:application/json

{"orderId":"ORD-1","status":"SHIPPED"}
```
— a command line, a couple of headers, a blank line, then the body, all in plain text — genuinely readable at a glance, unlike a comparable AMQP or Kafka wire-protocol frame.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A STOMP frame is plain text: a command line, headers, a blank line, then a body — structurally similar to an HTTP request, in contrast to binary broker protocols" >
  <rect x="20" y="20" width="280" height="130" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="8" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">STOMP frame (plain text)</text>
  <text x="35" y="42" fill="#79c0ff" font-size="9" font-family="monospace">SEND</text>
  <text x="35" y="62" fill="#e6edf3" font-size="8" font-family="monospace">destination:/topic/order-status</text>
  <text x="35" y="78" fill="#e6edf3" font-size="8" font-family="monospace">content-type:application/json</text>
  <text x="35" y="98" fill="#8b949e" font-size="7" font-family="monospace">(blank line)</text>
  <text x="35" y="120" fill="#6db33f" font-size="8" font-family="monospace">{"orderId":"ORD-1",</text>
  <text x="35" y="135" fill="#6db33f" font-size="8" font-family="monospace">"status":"SHIPPED"}</text>

  <rect x="340" y="20" width="280" height="130" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="8" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Binary broker protocol (e.g. AMQP)</text>
  <text x="355" y="55" fill="#8b949e" font-size="8" font-family="monospace">01 00 00 00 4A 00 3C 8F</text>
  <text x="355" y="75" fill="#8b949e" font-size="8" font-family="monospace">A2 F1 00 00 00 12 07 5F</text>
  <text x="355" y="95" fill="#8b949e" font-size="8" font-family="monospace">3E 00 09 D4 88 71 4B 00</text>
  <text x="355" y="120" fill="#8b949e" font-size="7" font-family="monospace">(not human-readable without tooling)</text>

  <defs></defs>
</svg>

STOMP's plain-text framing trades some parsing efficiency for genuine human readability, a deliberate design choice for its simplicity-focused use cases.

## 5. Runnable example

The scenario: publishing order status updates to browser clients over STOMP, simulated by constructing and parsing real STOMP frame text (genuinely runnable, since STOMP is just a text format, no actual broker connection needed to demonstrate the framing itself), starting with basic frame construction, then subscribing to a destination and matching incoming frames, and finally a full send/receive round trip using the text protocol end to end.

### Level 1 — Basic

```java
// StompFrameConstructionDemo.java
// Constructs and parses real STOMP frame TEXT directly, since STOMP is fundamentally a text
// protocol — this demonstrates the actual wire format without needing a live broker connection.
public class StompFrameConstructionDemo {
    static String buildSendFrame(String destination, String contentType, String body) {
        return "SEND\n"
            + "destination:" + destination + "\n"
            + "content-type:" + contentType + "\n"
            + "\n"
            + body
            + "\0"; // STOMP frames are NULL-terminated
    }

    public static void main(String[] args) {
        String frame = buildSendFrame("/topic/order-status", "application/json",
            "{\"orderId\":\"ORD-1\",\"status\":\"SHIPPED\"}");

        System.out.println("Raw STOMP frame (readable as plain text):");
        System.out.println(frame.replace("\0", "[NULL]"));
    }
}
```

How to run: `java StompFrameConstructionDemo.java`. Expected output: a plain-text STOMP `SEND` frame, printed exactly as it would appear on the wire — a command line, two headers, a blank line, the JSON body, and a `[NULL]` terminator — directly demonstrating STOMP's human-readable, HTTP-like structure.

### Level 2 — Intermediate

Parsing an incoming STOMP `MESSAGE` frame (what a subscribed client receives) back into its component parts — command, headers, body — mirroring what a STOMP client library does internally when it receives a frame from the broker.

```java
// StompFrameParsingDemo.java
import java.util.*;

public class StompFrameParsingDemo {
    record StompFrame(String command, Map<String, String> headers, String body) {}

    static StompFrame parseFrame(String rawFrame) {
        String[] lines = rawFrame.replace("\0", "").split("\n");
        String command = lines[0];
        Map<String, String> headers = new LinkedHashMap<>();
        int i = 1;
        while (i < lines.length && !lines[i].isEmpty()) {
            String[] parts = lines[i].split(":", 2);
            headers.put(parts[0], parts[1]);
            i++;
        }
        StringBuilder body = new StringBuilder();
        for (int j = i + 1; j < lines.length; j++) body.append(lines[j]);
        return new StompFrame(command, headers, body.toString());
    }

    public static void main(String[] args) {
        String incomingFrame = "MESSAGE\n"
            + "subscription:sub-0\n"
            + "destination:/topic/order-status\n"
            + "content-type:application/json\n"
            + "\n"
            + "{\"orderId\":\"ORD-1\",\"status\":\"SHIPPED\"}\0";

        StompFrame parsed = parseFrame(incomingFrame);
        System.out.println("Command: " + parsed.command());
        System.out.println("Destination header: " + parsed.headers().get("destination"));
        System.out.println("Subscription header: " + parsed.headers().get("subscription"));
        System.out.println("Body: " + parsed.body());
    }
}
```

How to run: `java StompFrameParsingDemo.java`. Expected output: `Command: MESSAGE`, `Destination header: /topic/order-status`, `Subscription header: sub-0`, `Body: {"orderId":"ORD-1","status":"SHIPPED"}` — the raw text frame was correctly decomposed into its command, headers, and body, exactly the parsing a real STOMP client library performs to hand a usable message object to application code.

### Level 3 — Advanced

A full local send/receive round trip: constructing a `SEND` frame, "publishing" it to an in-memory broker that tracks subscriptions by destination, and having a matching subscriber receive a properly-formatted `MESSAGE` frame in response — end to end, using the real text-based framing throughout.

```java
// FullStompRoundTripDemo.java
import java.util.*;

public class FullStompRoundTripDemo {
    record StompFrame(String command, Map<String, String> headers, String body) {}

    static Map<String, List<String>> subscriptionsByDestination = new HashMap<>(); // destination -> subscription IDs

    static void subscribe(String subscriptionId, String destination) {
        subscriptionsByDestination.computeIfAbsent(destination, d -> new ArrayList<>()).add(subscriptionId);
    }

    static StompFrame parseFrame(String raw) {
        String[] lines = raw.replace("\0", "").split("\n");
        Map<String, String> headers = new LinkedHashMap<>();
        int i = 1;
        while (i < lines.length && !lines[i].isEmpty()) {
            String[] parts = lines[i].split(":", 2);
            headers.put(parts[0], parts[1]);
            i++;
        }
        StringBuilder body = new StringBuilder();
        for (int j = i + 1; j < lines.length; j++) body.append(lines[j]);
        return new StompFrame(lines[0], headers, body.toString());
    }

    static List<String> handleSendFrame(String rawSendFrame) {
        StompFrame sendFrame = parseFrame(rawSendFrame);
        String destination = sendFrame.headers().get("destination");
        List<String> deliveredTo = new ArrayList<>();
        for (String subscriptionId : subscriptionsByDestination.getOrDefault(destination, List.of())) {
            String messageFrame = "MESSAGE\n"
                + "subscription:" + subscriptionId + "\n"
                + "destination:" + destination + "\n"
                + "\n" + sendFrame.body() + "\0";
            deliveredTo.add(messageFrame);
        }
        return deliveredTo;
    }

    public static void main(String[] args) {
        subscribe("sub-browser-1", "/topic/order-status");
        subscribe("sub-browser-2", "/topic/order-status");

        String sendFrame = "SEND\ndestination:/topic/order-status\n\n{\"orderId\":\"ORD-1\",\"status\":\"SHIPPED\"}\0";
        List<String> delivered = handleSendFrame(sendFrame);

        System.out.println("Delivered " + delivered.size() + " MESSAGE frames to subscribed browser clients:");
        delivered.forEach(f -> System.out.println("---\n" + f.replace("\0", "[NULL]")));
    }
}
```

How to run: `java FullStompRoundTripDemo.java`. Expected output: `Delivered 2 MESSAGE frames to subscribed browser clients:` followed by two properly-formatted `MESSAGE` frames, each carrying a different `subscription` header (`sub-browser-1` and `sub-browser-2`) but the identical order status body — one published `SEND` frame fanned out to every currently subscribed destination, exactly what a STOMP broker does for topic-style destinations, each subscriber's frame individually tagged so their own client library knows which local subscription callback to invoke.

## 6. Walkthrough

Tracing `FullStompRoundTripDemo` in execution order:

1. Two `subscribe(...)` calls register two separate subscription IDs (`sub-browser-1`, `sub-browser-2`) against the same destination, `/topic/order-status` — standing in for two different browser clients, each having independently issued their own STOMP `SUBSCRIBE` frame to that destination.
2. `handleSendFrame(sendFrame)` first parses the incoming raw `SEND` frame text into its command, headers, and body using the same `parseFrame` logic from Level 2 — extracting `destination="/topic/order-status"` and the JSON body.
3. The method looks up `subscriptionsByDestination.getOrDefault("/topic/order-status", ...)`, finding both previously-registered subscription IDs.
4. For each subscription ID, a brand-new `MESSAGE` frame is constructed as plain text — reusing the original body, but with a `subscription` header specific to *that* subscriber, and the *same* `destination` header — this per-subscriber `subscription` header is what lets each connected client's own STOMP library correctly route the incoming frame to the right local callback, even if that client has multiple active subscriptions.
5. Both constructed `MESSAGE` frames are collected into `deliveredTo` and returned.
6. `main` prints both delivered frames — confirming that a single `SEND` frame, published once, resulted in two independently-addressed `MESSAGE` frames, one per subscriber, exactly the topic-style fan-out behavior a real STOMP broker provides to multiple browser clients subscribed to the same destination.

```
subscribe(sub-browser-1, /topic/order-status)
subscribe(sub-browser-2, /topic/order-status)

SEND -> destination=/topic/order-status, body={...}
  -> lookup subscribers of /topic/order-status: [sub-browser-1, sub-browser-2]
  -> build MESSAGE frame for sub-browser-1 (same body, subscription=sub-browser-1)
  -> build MESSAGE frame for sub-browser-2 (same body, subscription=sub-browser-2)
  -> BOTH delivered
```

## 7. Gotchas & takeaways

> STOMP itself defines only the *framing* (command, headers, body structure) — it does not define routing semantics like AMQP's exchanges (card 0058) or guarantee delivery semantics like Kafka's log (card 0059); those behaviors depend entirely on whatever broker is speaking STOMP underneath (RabbitMQ's STOMP plugin, Spring's own simple in-memory STOMP broker relay, ActiveMQ). Two different STOMP-speaking brokers can have meaningfully different delivery guarantees and destination semantics despite using an identical wire format — never assume STOMP itself implies any particular reliability guarantee beyond what the specific underlying broker actually provides.

- STOMP support connects a flow to a broker over STOMP, a simple, plain-text, HTTP-like messaging protocol, most commonly used as the wire protocol for WebSocket-based browser messaging.
- Use STOMP support when bridging a flow to browser or other simple STOMP-speaking clients, or when a genuinely human-readable, easily-debuggable wire protocol is valuable.
- A STOMP frame consists of a command line, headers, a blank line, and a body, terminated by a null byte — structurally similar to an HTTP request, and directly readable in network traces without specialized binary-protocol tooling.
- A single published frame to a destination fans out to every currently subscribed client, each receiving their own individually-addressed `MESSAGE` frame tagged with their specific subscription ID.
- STOMP itself defines only framing, not routing or delivery guarantees — those depend entirely on whichever underlying broker is actually speaking STOMP, so different STOMP-speaking brokers can behave quite differently despite sharing the identical wire format.
