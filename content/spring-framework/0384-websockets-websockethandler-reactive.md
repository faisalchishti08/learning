---
card: spring-framework
gi: 384
slug: websockets-websockethandler-reactive
title: "WebSockets (WebSocketHandler, reactive)"
---

## 1. What it is

Spring WebFlux's WebSocket support centers on `WebSocketHandler` — a single-method interface (`Mono<Void> handle(WebSocketSession session)`) representing an entire WebSocket connection's lifecycle, with the session's inbound messages exposed as a `Flux<WebSocketMessage>` and outbound messages sent via a `Mono`/`Flux`-accepting `session.send(...)` method — a fully reactive, bidirectional communication model distinct from both the request/response pattern most of WebFlux covers and from Spring MVC's own (Servlet-based) WebSocket support.

```java
@Component
public class EchoWebSocketHandler implements WebSocketHandler {
    @Override
    public Mono<Void> handle(WebSocketSession session) {
        Flux<WebSocketMessage> output = session.receive()
            .map(message -> session.textMessage("Echo: " + message.getPayloadAsText()));
        return session.send(output);
    }
}
```

## 2. Why & when

WebSockets provide a persistent, full-duplex connection — unlike HTTP's request/response model (even SSE, which is one-directional server-to-client), a WebSocket connection lets both client and server send messages to each other at any time over the same open connection. Use WebSockets when:

- You need genuine bidirectional communication — a chat application, a collaborative editing tool, a multiplayer game's real-time state sync — where the client also needs to send data to the server over the persistent connection, not just receive server-pushed updates (which SSE handles more simply for one-directional cases).
- You're already building a WebFlux application and want the WebSocket handling to compose naturally with the same reactive types (`Mono`/`Flux`) used everywhere else, rather than bridging to a different, callback-based WebSocket API.
- Low-latency, high-frequency message exchange matters, where the overhead of establishing a new HTTP request/response cycle per message (even with HTTP/2 multiplexing) would be wasteful compared to one persistent connection.

## 3. Core concept

```
WebSocketHandler.handle(WebSocketSession session) -> Mono<Void>:

  session.receive()            -> Flux<WebSocketMessage>   (INBOUND, from client)
  session.send(Flux<...>)       -> Mono<Void>                (OUTBOUND, to client)

  The handler's returned Mono<Void> represents the ENTIRE
  connection's lifetime — it completes when the connection closes
  (either side), and WebFlux keeps the connection open for as long
  as this Mono hasn't completed.

Common patterns:

  ECHO:  session.send(session.receive().map(transformFn))

  BROADCAST (one message reaches ALL connected sessions):
    Sinks.Many<String> broadcastSink = Sinks.many().multicast().onBackpressureBuffer();
    each session's handle() subscribes to broadcastSink.asFlux() for OUTBOUND,
    and pushes its own INBOUND messages into broadcastSink for others to receive

Registration — via a HandlerMapping + WebSocketHandlerAdapter, similar
in spirit to functional endpoints' RouterFunction registration:

  SimpleUrlHandlerMapping mapping URL patterns to WebSocketHandler beans,
  paired with a WebSocketHandlerAdapter bean
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Bidirectional flow: receive() and send() over ONE persistent connection</text>

  <rect x="20" y="60" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="95" text-anchor="middle" fill="#79c0ff" font-size="11">Client (browser)</text>

  <line x1="200" y1="80" x2="500" y2="80" stroke="#6db33f" marker-end="url(#a60)"/>
  <text x="350" y="72" text-anchor="middle" fill="#6db33f" font-size="9">session.receive() — INBOUND</text>

  <line x1="500" y1="105" x2="200" y2="105" stroke="#79c0ff" marker-end="url(#a60)"/>
  <text x="350" y="120" text-anchor="middle" fill="#79c0ff" font-size="9">session.send(...) — OUTBOUND</text>

  <rect x="500" y="60" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="600" y="95" text-anchor="middle" fill="#6db33f" font-size="11">WebSocketHandler</text>

  <defs>
    <marker id="a60" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*One persistent connection carries both `receive()` (inbound `Flux`) and `send()` (outbound `Mono`/`Flux`) simultaneously.*

## 5. Runnable example

### Level 1 — Basic

A minimal echo handler, registered via `HandlerMapping`:

```java
// EchoWebSocketHandler.java
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.socket.WebSocketHandler;
import org.springframework.web.reactive.socket.WebSocketMessage;
import org.springframework.web.reactive.socket.WebSocketSession;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Component
public class EchoWebSocketHandler implements WebSocketHandler {
    @Override
    public Mono<Void> handle(WebSocketSession session) {
        Flux<WebSocketMessage> output = session.receive()
            .map(message -> session.textMessage("Echo: " + message.getPayloadAsText()));
        return session.send(output);
    }
}
```

```java
// WebSocketConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.HandlerMapping;
import org.springframework.web.reactive.handler.SimpleUrlHandlerMapping;
import org.springframework.web.reactive.socket.WebSocketHandler;
import org.springframework.web.reactive.socket.server.support.WebSocketHandlerAdapter;

import java.util.Map;

@Configuration
public class WebSocketConfig {

    @Bean
    public HandlerMapping webSocketMapping(EchoWebSocketHandler handler) {
        SimpleUrlHandlerMapping mapping = new SimpleUrlHandlerMapping();
        mapping.setUrlMap(Map.of("/ws/echo", handler));
        mapping.setOrder(-1);   // HIGH priority — checked before other mappings
        return mapping;
    }

    @Bean
    public WebSocketHandlerAdapter webSocketHandlerAdapter() {
        return new WebSocketHandlerAdapter();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Using a WebSocket client (e.g. websocat, or a browser console):
websocat ws://localhost:8080/ws/echo
> hello
< Echo: hello
> another message
< Echo: another message
```

`session.receive()` provides every inbound message the client sends as a `Flux<WebSocketMessage>` element; `.map(...)` transforms each into an outbound echo message, and `session.send(output)` writes each transformed message back to the same client — the entire bidirectional exchange is expressed as a single reactive pipeline, with no manual message-loop or callback registration needed.

### Level 2 — Intermediate

A broadcast chat handler — every connected client's messages reach every other connected client, using `Sinks.Many` (the same programmatic bridging primitive from the SSE card) to fan out messages across independent WebSocket sessions:

```java
// ChatWebSocketHandler.java
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.socket.WebSocketHandler;
import org.springframework.web.reactive.socket.WebSocketMessage;
import org.springframework.web.reactive.socket.WebSocketSession;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Sinks;

@Component
public class ChatWebSocketHandler implements WebSocketHandler {

    private final Sinks.Many<String> broadcastSink = Sinks.many().multicast().onBackpressureBuffer();

    @Override
    public Mono<Void> handle(WebSocketSession session) {
        // INBOUND: every message this client sends is pushed into the SHARED sink,
        // reaching every other currently-connected session subscribed to it.
        Mono<Void> input = session.receive()
            .doOnNext(message -> broadcastSink.tryEmitNext(message.getPayloadAsText()))
            .then();

        // OUTBOUND: this session subscribes to the SAME shared sink, receiving
        // every message ANY client (including itself) has sent.
        Flux<WebSocketMessage> output = broadcastSink.asFlux()
            .map(session::textMessage);

        return Mono.zip(input, session.send(output)).then();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Terminal 1:
websocat ws://localhost:8080/ws/chat
> Hi everyone

# Terminal 2 (connected concurrently):
websocat ws://localhost:8080/ws/chat
< Hi everyone     <- received the message Terminal 1 sent
> Hello back
```

**What changed:** Unlike the echo handler (Level 1), where each client only ever sees its own messages reflected back, the shared `broadcastSink` fans every inbound message out to every currently-connected session's outbound stream — this is structurally identical to the `Sinks.Many`-based SSE notification pattern from the earlier card, just with genuinely bidirectional communication instead of one-directional server-to-client push.

### Level 3 — Advanced

Production concern: session lifecycle management (tracking connected clients, cleaning up on disconnect), per-message error isolation (one client's malformed message shouldn't crash the whole broadcast), and a heartbeat/ping mechanism to detect and clean up dead connections:

```java
// ChatWebSocketHandler.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.socket.WebSocketHandler;
import org.springframework.web.reactive.socket.WebSocketMessage;
import org.springframework.web.reactive.socket.WebSocketSession;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Sinks;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class ChatWebSocketHandler implements WebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(ChatWebSocketHandler.class);
    private final Sinks.Many<String> broadcastSink = Sinks.many().multicast().onBackpressureBuffer();
    private final AtomicInteger connectedCount = new AtomicInteger(0);

    @Override
    public Mono<Void> handle(WebSocketSession session) {
        String sessionId = session.getId();
        connectedCount.incrementAndGet();
        log.info("Session {} connected, total: {}", sessionId, connectedCount.get());

        Mono<Void> input = session.receive()
            .doOnNext(message -> {
                String text = message.getPayloadAsText();
                if (text.length() > 1000) {
                    log.warn("Session {} sent an oversized message, ignoring", sessionId);
                    return;   // ignore malformed/abusive input, don't let it disrupt the broadcast
                }
                broadcastSink.tryEmitNext(sessionId.substring(0, 8) + ": " + text);
            })
            .doOnError(ex -> log.warn("Session {} inbound error: {}", sessionId, ex.getMessage()))
            .onErrorResume(ex -> Mono.empty())   // one bad message shouldn't kill the whole session
            .then();

        Flux<WebSocketMessage> heartbeat = Flux.interval(Duration.ofSeconds(30))
            .map(tick -> session.textMessage("__heartbeat__"));

        Flux<WebSocketMessage> chatMessages = broadcastSink.asFlux().map(session::textMessage);

        Mono<Void> output = session.send(Flux.merge(chatMessages, heartbeat));

        return Mono.zip(input, output)
            .then()
            .doFinally(signal -> {
                connectedCount.decrementAndGet();
                log.info("Session {} disconnected ({}), total: {}", sessionId, signal, connectedCount.get());
            });
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

websocat ws://localhost:8080/ws/chat
# server log: "Session abc-123-... connected, total: 1"
> Hello
# server log shows the broadcast, other connected clients receive "abc12345: Hello"
# __heartbeat__ arrives every 30 seconds

# Ctrl+C disconnects:
# server log: "Session abc-123-... disconnected (onComplete), total: 0"
```

**What changed and why:**
- `.onErrorResume(ex -> Mono.empty())` on the `input` pipeline ensures that an error in processing one inbound message (or, more critically, an error in the underlying connection's message stream itself, like a malformed WebSocket frame) doesn't propagate up and terminate the entire `handle()` Mono for this session prematurely — the message-length check similarly guards against a specific, anticipated abuse pattern (oversized payloads) without needing an exception at all.
- `Flux.merge(chatMessages, heartbeat)` combines the genuine chat broadcast stream with a periodic heartbeat, directly mirroring the SSE card's equivalent pattern — WebSocket connections, like SSE ones, can be silently closed by intermediate proxies/load balancers if they appear idle for too long; periodic heartbeat frames prevent this.
- `.doFinally(signal -> {...})` provides reliable connection lifecycle tracking (`connectedCount`, logging) regardless of *how* the connection ends — client-initiated close, server-initiated close, or an error — exactly mirroring the `.doFinally`-based cleanup pattern used in both the SSE and `WebFilter` cards, reinforcing that this "always runs on completion" guarantee is a consistent, reusable pattern across many different reactive scenarios in WebFlux.

## 6. Walkthrough

**Connection: a client connects to `ws://localhost:8080/ws/chat`, sends `"Hello"`, another already-connected client is listening (Level 3 code).**

1. The WebSocket handshake (an HTTP `Upgrade` request/response) completes, and `WebSocketHandlerAdapter` (registered in `WebSocketConfig`) invokes `ChatWebSocketHandler.handle(session)` for this new connection. `connectedCount` increments to reflect this new session, logged immediately.
2. Inside `handle`: the `input`, `heartbeat`, `chatMessages`, and `output` pipelines are all constructed — none of them have started producing/consuming data yet; this is purely pipeline construction, following the same laziness principle as every other reactive composition covered throughout this section.
3. `Mono.zip(input, output)` is returned as the method's result. WebFlux subscribes to this `Mono`, which in turn subscribes to both `input` and `output` — this is what actually activates the connection's bidirectional message flow.
4. `output`'s subscription (via `session.send(Flux.merge(chatMessages, heartbeat))`) begins listening to both `chatMessages` (fed by `broadcastSink`) and the `heartbeat` interval — this client is now ready to receive both kinds of outbound messages, though none have been emitted yet.
5. Some time later, this client sends the text message `"Hello"` over the WebSocket connection. This arrives as an element in `session.receive()`'s `Flux<WebSocketMessage>`, triggering `input`'s `.doOnNext(...)` callback.
6. Inside the callback: `text.length() (5) > 1000` is `false`, so the message isn't discarded. `broadcastSink.tryEmitNext(sessionId.substring(0,8) + ": Hello")` pushes this formatted message into the shared sink.
7. Because the *other* already-connected client's `output` pipeline is also subscribed to `broadcastSink.asFlux()` (via that other session's own `chatMessages` binding, from its own independent `handle()` invocation), this emission reaches that other client's outbound stream too — `.map(session::textMessage)` wraps it as a `WebSocketMessage`, and `session.send(...)` writes it over that other client's own, separate WebSocket connection.
8. That other client receives the formatted broadcast message: `"abc12345: Hello"` (using the sending session's truncated id as a simple sender label).
9. Meanwhile, independently, every 30 seconds, each connected session's own `heartbeat` `Flux.interval` ticks, producing a `"__heartbeat__"` text message that merges into that specific session's own `output` stream and gets sent — heartbeats are per-connection, not broadcast, since each session constructs its own independent `heartbeat` Flux inside its own `handle()` invocation.

**Eventual disconnection of the message-sending client.**

1. When this client's connection closes (client-initiated, network failure, or otherwise), the underlying `session.receive()` `Flux` completes or errors, which propagates through `input`'s composition, eventually completing (or, if suppressed via `onErrorResume`, completing gracefully) the overall `Mono.zip(input, output)` this session's `handle()` call returned.
2. `.doFinally(signal -> {...})` fires: `connectedCount.decrementAndGet()` and the disconnect log line execute, regardless of whether the disconnection was clean or abrupt — this cleanup is guaranteed by `doFinally`'s "always runs" contract.

## 7. Gotchas & takeaways

> **A WebSocket session's `handle()` method's returned `Mono<Void>` completing is what closes the connection** — if your composed pipeline (like `Mono.zip(input, output)`) never naturally completes (e.g., both `input` and `output` are built from genuinely infinite `Flux`es with no termination condition), the connection stays open indefinitely, which is often intentional for a long-lived chat/streaming connection but must be a deliberate choice, not an oversight.

> **`Sinks.many().multicast()` (used for broadcast, exactly as in the SSE card) only delivers messages to sessions connected at the time of emission** — a client connecting after a chat message was sent never sees that earlier message, which is often the correct behavior for a live chat but worth confirming matches your actual requirements; `Sinks.many().replay(...)` exists for scenarios needing message history replay to newly joining clients.

> **One session's error in its `receive()`/`input` pipeline, if not explicitly isolated (via `onErrorResume`, as in the Level 3 example), can terminate that session's entire `handle()` Mono prematurely** — always consider whether errors specific to one client's message stream should end just that client's connection (often correct) or whether some errors should be swallowed and logged instead, to keep a session alive through a transient glitch.

- `WebSocketHandler.handle(session)` represents an entire connection's lifecycle as a single `Mono<Void>`, with `session.receive()` (inbound `Flux`) and `session.send(...)` (outbound) composing the bidirectional message flow reactively.
- `Sinks.Many` bridges independent WebSocket sessions for broadcast scenarios, directly mirroring the same pattern used for SSE fan-out in the earlier card.
- Pair chat/broadcast streams with periodic heartbeats (via `Flux.merge`) to prevent intermediate infrastructure from closing seemingly-idle long-lived connections.
- Isolate per-message or per-session errors with `onErrorResume` where a transient issue shouldn't terminate an otherwise-healthy connection, and use `doFinally` for reliable, unconditional connection lifecycle cleanup.
