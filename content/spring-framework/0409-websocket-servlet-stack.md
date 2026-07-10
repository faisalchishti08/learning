---
card: spring-framework
gi: 409
slug: websocket-servlet-stack
title: "WebSocket (Servlet stack)"
---

## 1. What it is

This is the lower-level WebSocket API in Spring's Servlet (Spring MVC) stack: implementing `WebSocketHandler` directly to handle raw connection lifecycle events (`afterConnectionEstablished`, `handleMessage`, `afterConnectionClosed`) and raw `WebSocketMessage` payloads, registered via `WebSocketConfigurer`, without STOMP's framing or `@MessageMapping` routing on top. It's the foundation the STOMP support from the previous cards is actually built on.

```java
class EchoHandler extends TextWebSocketHandler {
    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        session.sendMessage(new TextMessage("Echo: " + message.getPayload()));
    }
}
```

## 2. Why & when

STOMP over WebSocket (covered earlier in this section) gives you routing, pub/sub semantics, and annotated handler methods — but that structure comes with STOMP's own frame format and assumptions (destinations, subscriptions). Sometimes you need a WebSocket connection that speaks a *different* protocol entirely (a custom binary protocol, a third-party JSON-RPC-style protocol a client library expects) or you need to manage connection lifecycle and session state yourself with full control. The raw `WebSocketHandler` API is that lower level: you get the connection and its message stream directly, with no protocol assumptions layered on top.

Reach for the raw Servlet-stack WebSocket API when:

- The client speaks a specific wire protocol that isn't STOMP (e.g., integrating with a pre-existing JavaScript library or hardware device that has its own message format).
- You need fine-grained control over connection lifecycle — custom logic on connect/disconnect, manual session tracking, binary message handling — that would fight against STOMP's higher-level abstractions.
- You're building the foundation for a higher-level abstraction yourself, or you specifically want to understand what STOMP support is doing underneath (useful for debugging STOMP issues, since they ultimately surface as `WebSocketSession` and `WebSocketMessage` events at this layer).

For most application-level real-time features (chat, notifications, live updates), STOMP's structure saves you from reinventing message routing — reach for the raw API specifically when STOMP's assumptions don't fit.

## 3. Core concept

```
 WebSocketConfigurer.registerWebSocketHandlers(registry)
        |
        v
 registry.addHandler(myHandler, "/ws-echo")
        |
        v
                WebSocketHandler (your implementation)
        |
        +-- afterConnectionEstablished(session)   <- connection opened
        +-- handleMessage(session, message)        <- a message arrived
        +-- handleTransportError(session, ex)       <- something went wrong
        +-- afterConnectionClosed(session, status) <- connection closed
```

Every event carries a `WebSocketSession`, which is your handle for sending messages back (`session.sendMessage(...)`), inspecting connection attributes, or closing the connection — there's no implicit routing or broadcast; whatever fan-out or session bookkeeping you need, you implement yourself.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebSocketHandler lifecycle: connect, message exchange, close">
  <rect x="10" y="80" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">afterConnectionEstablished</text>

  <rect x="245" y="80" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">handleMessage (N times)</text>

  <rect x="480" y="80" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">afterConnectionClosed</text>

  <line x1="160" y1="103" x2="240" y2="103" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="395" y1="103" x2="475" y2="103" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <path d="M 320 80 A 40 30 0 1 1 320 126" fill="none" stroke="#79c0ff" stroke-width="1.5"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`handleMessage` fires once per incoming message for the life of the connection, bracketed by exactly one open and one close event.

## 5. Runnable example

### Level 1 — Basic

A minimal echo handler using `TextWebSocketHandler`, a convenience base class that dispatches text and binary messages to separate overridable methods instead of one generic `handleMessage`.

```java
import org.springframework.context.annotation.*;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.config.annotation.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

public class WebSocketBasic {

    static class EchoHandler extends TextWebSocketHandler {
        @Override
        public void afterConnectionEstablished(WebSocketSession session) throws Exception {
            System.out.println("Connected: " + session.getId());
        }

        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
            System.out.println("Received: " + message.getPayload());
            session.sendMessage(new TextMessage("Echo: " + message.getPayload()));
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, org.springframework.web.socket.CloseStatus status) {
            System.out.println("Closed: " + session.getId() + " (" + status + ")");
        }
    }

    @Configuration
    @EnableWebSocket
    static class Config implements WebSocketConfigurer {
        @Override
        public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
            registry.addHandler(new EchoHandler(), "/ws-echo");
        }
    }
}
```

How to run: run inside a Spring Boot web application (`spring-boot-starter-websocket`), then connect with any WebSocket client to `ws://localhost:8080/ws-echo` and send text — expect the same text back prefixed with `"Echo: "`.

`TextWebSocketHandler` handles the boilerplate of dispatching by message type, so you only override `handleTextMessage`. `session.sendMessage(new TextMessage(...))` writes directly back on the same session that received the message — there's no routing or broadcast mechanism here at all, unlike STOMP's `@SendTo`.

### Level 2 — Intermediate

Track multiple connected sessions to broadcast a message to everyone — something STOMP's `@SendTo` gives you for free, but which the raw API requires you to implement explicitly.

```java
import org.springframework.context.annotation.*;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.config.annotation.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Collections;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class WebSocketIntermediate {

    static class BroadcastHandler extends TextWebSocketHandler {
        private final Set<WebSocketSession> sessions =
                Collections.newSetFromMap(new ConcurrentHashMap<>());

        @Override
        public void afterConnectionEstablished(WebSocketSession session) {
            sessions.add(session);
            System.out.println("Connected: " + session.getId() + " (total: " + sessions.size() + ")");
        }

        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
            for (WebSocketSession s : sessions) {
                if (s.isOpen()) {
                    s.sendMessage(new TextMessage(session.getId() + ": " + message.getPayload()));
                }
            }
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
            sessions.remove(session);
            System.out.println("Disconnected: " + session.getId() + " (total: " + sessions.size() + ")");
        }
    }

    @Configuration
    @EnableWebSocket
    static class Config implements WebSocketConfigurer {
        @Override
        public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
            registry.addHandler(new BroadcastHandler(), "/ws-broadcast")
                    .setAllowedOriginPatterns("*"); // demo-only: restrict this in production
        }
    }
}
```

How to run: same as Level 1, connecting multiple clients to `ws://localhost:8080/ws-broadcast` — a message from one client should appear on every connected client.

`Collections.newSetFromMap(new ConcurrentHashMap<>())` gives a thread-safe set, necessary because `afterConnectionEstablished`/`handleTextMessage`/`afterConnectionClosed` can be invoked concurrently from different sessions' I/O threads. Iterating `sessions` and calling `sendMessage` on each one implements the broadcast manually — exactly the fan-out logic STOMP's `@SendTo("/topic/...")` and simple broker handle automatically, made visible here as ordinary Java code.

### Level 3 — Advanced

Production raw WebSocket handlers need to handle backpressure (a slow client can't keep up with the rate you're sending) and per-session state (not just membership, but data associated with each connection), plus graceful handling of transport errors so one misbehaving client doesn't affect others.

```java
import org.springframework.context.annotation.*;
import org.springframework.web.socket.*;
import org.springframework.web.socket.config.annotation.*;
import org.springframework.web.socket.handler.ConcurrentWebSocketSessionDecorator;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class WebSocketAdvanced {

    record SessionState(String username, long connectedAtMillis) {}

    static class ChatHandler extends TextWebSocketHandler {
        private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
        private final Map<String, SessionState> sessionState = new ConcurrentHashMap<>();

        @Override
        public void afterConnectionEstablished(WebSocketSession rawSession) {
            // Wrap with backpressure handling: bounded send buffer + timeout, so one slow
            // client blocking on I/O can't stall the thread broadcasting to everyone else.
            WebSocketSession session = new ConcurrentWebSocketSessionDecorator(
                    rawSession, 5_000, 64 * 1024); // 5s send timeout, 64KB buffer limit

            String username = extractUsername(rawSession);
            sessions.put(session.getId(), session);
            sessionState.put(session.getId(), new SessionState(username, System.currentTimeMillis()));
            System.out.println(username + " connected as session " + session.getId());
        }

        private String extractUsername(WebSocketSession session) {
            var query = session.getUri() != null ? session.getUri().getQuery() : null;
            return query != null && query.startsWith("user=") ? query.substring(5) : "anonymous";
        }

        @Override
        protected void handleTextMessage(WebSocketSession rawSession, TextMessage message) {
            SessionState state = sessionState.get(rawSession.getId());
            String formatted = "[" + state.username() + "] " + message.getPayload();

            sessions.values().forEach(s -> {
                try {
                    if (s.isOpen()) {
                        s.sendMessage(new TextMessage(formatted));
                    }
                } catch (Exception e) {
                    // A single slow/broken client shouldn't break the broadcast to everyone else.
                    System.err.println("Failed to send to " + s.getId() + ": " + e.getMessage());
                }
            });
        }

        @Override
        public void handleTransportError(WebSocketSession session, Throwable exception) {
            System.err.println("Transport error on " + session.getId() + ": " + exception.getMessage());
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
            SessionState state = sessionState.remove(session.getId());
            sessions.remove(session.getId());
            System.out.println((state != null ? state.username() : session.getId())
                    + " disconnected: " + status);
        }
    }

    @Configuration
    @EnableWebSocket
    static class Config implements WebSocketConfigurer {
        @Override
        public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
            registry.addHandler(new ChatHandler(), "/ws-chat-raw")
                    .setAllowedOriginPatterns("https://app.example.com");
        }
    }
}
```

How to run: run inside a Spring Boot web application, connect to `ws://localhost:8080/ws-chat-raw?user=ada`, send text messages, and observe them broadcast to all connected clients with the sender's username prefixed.

`ConcurrentWebSocketSessionDecorator` wraps the raw session with a bounded send buffer and timeout — if a client's connection is slow enough that 64KB of unsent messages queue up, or a single send takes longer than 5 seconds, the decorator closes that session rather than letting a slow client block the server-side thread indefinitely (which, without this decorator, could also delay broadcasts to every other connected client if `sendMessage` calls happen sequentially on a shared thread). The per-session `sessionState` map associates arbitrary application data (here, a username parsed from the connection's query string) with each session's lifecycle, something the raw API leaves entirely up to you to manage.

## 6. Walkthrough

Trace `WebSocketAdvanced.ChatHandler` handling one broadcast message, assuming three clients are connected and one of them has a slow network connection:

1. **Message arrives.** Client "ada" sends the text `"hello everyone"`; `handleTextMessage` is invoked with `rawSession` set to ada's session and `message.getPayload()` equal to `"hello everyone"`.
2. **State lookup.** `sessionState.get(rawSession.getId())` retrieves the `SessionState` recorded when ada connected, giving access to her username without needing to re-parse the connection URI on every message.
3. **Message formatting.** `formatted` becomes `"[ada] hello everyone"` — the server-side format every connected client will actually receive, regardless of how the sender phrased or labeled their own message client-side.
4. **Broadcast loop begins.** `sessions.values().forEach(...)` iterates all three currently-tracked sessions (including ada's own), sending the formatted message to each.
5. **Fast clients succeed immediately.** For the two clients with healthy connections, `s.sendMessage(...)` completes quickly — the `ConcurrentWebSocketSessionDecorator` wrapping each session has plenty of headroom under its 64KB buffer and 5-second timeout.
6. **Slow client hits backpressure.** For the third, slow client, if its outbound TCP buffer is already near capacity from previous unsent messages, the decorator either queues this message (if under the 64KB limit) or — if the limit is already exceeded — throws, which the surrounding `try/catch` in the broadcast loop catches, logging `"Failed to send to <id>: ..."` without interrupting the loop for the other two clients.
7. **Loop completes.** All three sessions have been attempted; the method returns. If the slow client's session was closed due to exceeding the buffer limit, its subsequent `afterConnectionClosed` callback fires independently, cleaning up its entry in both `sessions` and `sessionState`.

```
handleTextMessage(ada, "hello everyone")
   -> lookup ada's SessionState -> username "ada"
   -> format "[ada] hello everyone"
   -> for each of [ada, bob, slow-client]:
        try sendMessage(formatted)
          ada:   succeeds
          bob:   succeeds
          slow:  buffer over limit -> exception -> caught, logged, loop continues
   -> broadcast loop done (bob and ada received it; slow-client's session may be closed)
```

## 7. Gotchas & takeaways

> Gotcha: broadcasting to many sessions by calling `sendMessage` synchronously in a loop on a shared thread means one truly stuck (not just slow) client's blocking I/O can stall delivery to every subsequent session in the loop, even with `ConcurrentWebSocketSessionDecorator`'s timeout — the timeout bounds *how long* a stuck send blocks, but doesn't eliminate the blocking itself. High-fan-out broadcast scenarios often dispatch each `sendMessage` call to a separate thread/executor rather than looping synchronously, trading some complexity for isolation between recipients.

- Use the raw `WebSocketHandler` API when you need a non-STOMP protocol or full manual control over session lifecycle and broadcast logic; use STOMP (previous cards) when its routing and pub/sub model fits your use case, to avoid reimplementing session tracking and fan-out yourself.
- `TextWebSocketHandler`/`BinaryWebSocketHandler` are convenience base classes that split `handleMessage` into type-specific overrides — extend them instead of implementing `WebSocketHandler` directly unless you genuinely need to handle both message types identically.
- Wrap sessions with `ConcurrentWebSocketSessionDecorator` in any handler that broadcasts to multiple sessions, to bound how much a single slow client can affect send performance and memory.
- Session and application state (usernames, subscriptions, anything beyond the raw connection) is entirely your responsibility to track at this layer — there's no built-in equivalent to STOMP's destination/subscription model.
