---
card: spring-integration
gi: 62
slug: websocket-support
title: "WebSocket support"
---

## 1. What it is

WebSocket support (`WebSocketInboundChannelAdapter`/`WebSocketOutboundChannelAdapter`, built on Spring's `WebSocketSession` abstraction) connects a flow to a full-duplex, persistent socket connection between client and server. Unlike HTTP support (card 0054), where every exchange is a fresh request that opens and closes, a WebSocket connection is opened once and stays open, letting either side push frames to the other at any time without waiting to be asked. Spring Integration treats each inbound WebSocket frame as a message and lets a flow publish outbound frames the same way it publishes to any other channel.

## 2. Why & when

You reach for WebSocket support when the integration point needs a persistent, low-latency, two-way channel rather than a request/response cycle:

- **The server needs to push data to clients without the client polling for it** — live price tickers, chat messages, or progress updates all need the server to speak first, which a request/response protocol like plain HTTP cannot do without repeated polling.
- **Round-trip latency matters and connection setup overhead is a cost you want to pay once** — a WebSocket handshake happens a single time up front; every message after that skips the TCP/TLS negotiation and HTTP header overhead that a fresh request would repeat.
- **The client is a browser** — WebSocket is a browser-native API, making it the natural choice when the far end of the flow is JavaScript running in a page, especially layered with STOMP (card 0061) for destination-based routing to browser subscribers.

## 3. Core concept

Think of HTTP as sending a letter and waiting for a reply — each letter is a self-contained round trip, and the mailbox closes between exchanges. A WebSocket connection is more like a phone call: once connected, either party can speak at any moment, and the line stays open until someone hangs up. Spring Integration's adapters sit at each end of that open line, turning what arrives into a `Message` for the flow, and turning what the flow sends into a frame on the wire.

```java
@Bean
public IntegrationFlow webSocketInboundFlow(WebSocketHandlerRegistration wsRegistration) {
    return IntegrationFlow.from(new WebSocketInboundChannelAdapter(
            wsServerContainer(), Arrays.asList("/ws/prices")))
        .handle((String payload, headers) -> priceService.handleClientMessage(payload))
        .get();
}
```

The registration ties a URL path to the adapter; every frame a connected client sends over `/ws/prices` becomes a message flowing through the same handler chain as any other Spring Integration message.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP is one request-response round trip per exchange; WebSocket opens one connection and both sides can send frames at any time afterward" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP: request/response per exchange</text>
  <rect x="20" y="30" width="90" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="49" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="210" y="30" width="90" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="255" y="49" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Server</text>
  <line x1="110" y1="40" x2="210" y2="40" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="160" y="36" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">request</text>
  <line x1="210" y1="55" x2="110" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="160" y="70" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">response, connection closes</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WebSocket: one open connection</text>
  <rect x="400" y="30" width="90" height="120" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="445" y="49" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="550" y="30" width="90" height="120" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="595" y="49" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Server</text>
  <line x1="490" y1="70" x2="550" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="550" y1="95" x2="490" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="550" y1="120" x2="490" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="520" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">frames flow either way, anytime</text>

  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
  </defs>
</svg>

HTTP closes the connection after every exchange; WebSocket keeps it open so either side can push at will.

## 5. Runnable example

The scenario: a live price-ticker feed, simulated with an in-process `WebSocketSession` stand-in (no real browser or servlet container needed to demonstrate the adapter's message-passing behavior), starting with a single push, then adding a subscription registry for multiple clients, then handling disconnects and backpressure.

### Level 1 — Basic

```java
// WebSocketPushDemo.java
import java.util.*;

public class WebSocketPushDemo {
    // Stand-in for a WebSocketSession: something the adapter can push frames onto.
    interface Session { void sendFrame(String payload); }

    static class LoggingSession implements Session {
        public void sendFrame(String payload) { System.out.println("[client received] " + payload); }
    }

    // Stand-in for WebSocketOutboundChannelAdapter: takes a message payload and pushes it to a session.
    static void outboundAdapterHandle(Session session, String priceUpdateJson) {
        session.sendFrame(priceUpdateJson);
    }

    public static void main(String[] args) {
        Session client = new LoggingSession();
        outboundAdapterHandle(client, "{\"symbol\":\"ACME\",\"price\":101.25}");
        outboundAdapterHandle(client, "{\"symbol\":\"ACME\",\"price\":101.40}");
    }
}
```

How to run: `java WebSocketPushDemo.java`. Expected output: two `[client received] {...}` lines, printed without the client ever asking — demonstrating the server-initiated push a request/response protocol cannot do.

### Level 2 — Intermediate

```java
// WebSocketPushDemo.java
import java.util.*;
import java.util.concurrent.*;

public class WebSocketPushDemo {
    interface Session { String id(); void sendFrame(String payload); }

    static class LoggingSession implements Session {
        private final String id;
        LoggingSession(String id) { this.id = id; }
        public String id() { return id; }
        public void sendFrame(String payload) { System.out.println("[" + id + " received] " + payload); }
    }

    // Real-world concern: many clients are subscribed at once; the adapter fans out to all of them,
    // the way a WebSocketInboundChannelAdapter's registered sessions do inside the container.
    static class SessionRegistry {
        private final Map<String, Session> sessions = new ConcurrentHashMap<>();
        void register(Session s) { sessions.put(s.id(), s); }
        void unregister(String id) { sessions.remove(id); }
        void broadcast(String payload) { sessions.values().forEach(s -> s.sendFrame(payload)); }
    }

    public static void main(String[] args) {
        SessionRegistry registry = new SessionRegistry();
        registry.register(new LoggingSession("client-A"));
        registry.register(new LoggingSession("client-B"));

        registry.broadcast("{\"symbol\":\"ACME\",\"price\":101.25}");
        registry.unregister("client-B"); // client-B disconnects
        registry.broadcast("{\"symbol\":\"ACME\",\"price\":101.40}");
    }
}
```

How to run: `java WebSocketPushDemo.java`. Expected output: the first broadcast reaches both clients; after `client-B` unregisters (simulating a disconnect), the second broadcast reaches only `client-A` — mirroring how a real container tracks which sessions are still open before fanning a message out to them.

### Level 3 — Advanced

```java
// WebSocketPushDemo.java
import java.util.*;
import java.util.concurrent.*;

public class WebSocketPushDemo {
    interface Session { String id(); void sendFrame(String payload); boolean isOpen(); }

    static class FlakySession implements Session {
        private final String id;
        private boolean open = true;
        private final int failAfter;
        private int sent = 0;
        FlakySession(String id, int failAfter) { this.id = id; this.failAfter = failAfter; }
        public String id() { return id; }
        public boolean isOpen() { return open; }
        public void sendFrame(String payload) {
            if (!open) throw new IllegalStateException("session closed: " + id);
            sent++;
            if (sent > failAfter) { open = false; throw new RuntimeException("connection dropped: " + id); }
            System.out.println("[" + id + " received] " + payload);
        }
    }

    // Production concern: a send can fail mid-broadcast (client dropped, slow consumer). The adapter
    // must not let one failing session stop delivery to the others, and must prune dead sessions.
    static class SessionRegistry {
        private final Map<String, Session> sessions = new ConcurrentHashMap<>();
        void register(Session s) { sessions.put(s.id(), s); }
        void broadcast(String payload) {
            for (Session s : sessions.values()) {
                try {
                    s.sendFrame(payload);
                } catch (RuntimeException ex) {
                    System.out.println("[registry] dropping dead session " + s.id() + ": " + ex.getMessage());
                    sessions.remove(s.id());
                }
            }
        }
    }

    public static void main(String[] args) {
        SessionRegistry registry = new SessionRegistry();
        registry.register(new FlakySession("client-A", 1)); // fails after 1 send
        registry.register(new FlakySession("client-B", 10));

        for (int i = 1; i <= 3; i++) {
            registry.broadcast("{\"tick\":" + i + "}");
        }
    }
}
```

How to run: `java WebSocketPushDemo.java`. Expected output: tick 1 reaches both clients; on tick 2, `client-A` throws and gets pruned with a `[registry] dropping dead session client-A` line, while `client-B` keeps receiving; tick 3 goes only to `client-B` — the isolation a production fan-out adapter needs so one bad connection can't take down delivery to everyone else.

## 6. Walkthrough

Trace a price update end to end, from the moment `priceService` decides to publish through to the browser tab that displays it.

1. **Source**: a price-changed event fires inside the application (a poller, a JMS listener, whatever produces the update) and hands a JSON payload like `{"symbol":"ACME","price":101.25}` to the flow's input channel.
2. **Flow**: the message reaches a `.handle(...)` step wired to a `WebSocketOutboundChannelAdapter`. The adapter extracts the payload and, using the session ID stored in the message headers (or a broadcast to all registered sessions, as in the example), calls `sendFrame` on the matching open `WebSocketSession`.
3. **Wire**: the container writes a WebSocket text frame containing the JSON payload onto the already-open TCP connection for that session — no handshake, no new connection, just a frame appended to an existing stream.
4. **Client**: the browser's `WebSocket.onmessage` handler fires with the frame's payload, and the page updates the displayed price — all without the browser having sent any request.
5. **Reverse direction**: if the browser sends a message back (say, a subscription change), the `WebSocketInboundChannelAdapter` on the server receives the frame, wraps it as a `Message` with the session ID in the headers, and publishes it to the flow's channel exactly like any other Spring Integration message — the same handler chain (transformers, routers, service activators) applies regardless of whether the message originated from a queue, a file, or a socket.

```
priceService.publish(json)
    -> WebSocketOutboundChannelAdapter.handleMessage(msg)
        -> session.sendTextMessage(json)      // frame written to open socket
            -> browser onmessage(json)         // no request/response cycle
```

## 7. Gotchas & takeaways

> **Gotcha:** unlike an HTTP adapter, a WebSocket session can die at any time without a clean close frame — network drop, browser tab closed, proxy timeout. Code that broadcasts to many sessions must catch send failures per-session (as in Level 3) rather than letting one dead connection abort the whole broadcast.

- WebSocket connections are stateful and long-lived; the server must track open sessions itself (a registry, or Spring's `WebSocketSession` map), unlike stateless HTTP where each request is independent.
- Because either side can send at any time, message ordering and backpressure need explicit thought — a slow client can build up a backlog of unsent frames if the adapter doesn't apply some flow control.
- WebSocket is commonly paired with STOMP (card 0061) when destination-based pub/sub semantics (subscribe to a topic, not just a raw socket) are needed on top of the raw frame protocol.
- Load balancers and reverse proxies need explicit configuration to keep a WebSocket connection open (they must not treat it like a short-lived HTTP request); sticky sessions or a shared session store are often required in multi-instance deployments.
