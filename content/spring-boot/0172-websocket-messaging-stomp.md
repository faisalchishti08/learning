---
card: spring-boot
gi: 172
slug: websocket-messaging-stomp
title: WebSocket messaging (STOMP)
---

## 1. What it is

**WebSocket** upgrades an HTTP connection to a full-duplex channel — both client and server can push data at any time. **STOMP (Simple Text Oriented Messaging Protocol)** adds a messaging layer on top of WebSocket: topics, subscriptions, and destinations, similar to JMS but over the browser. Spring Boot auto-configures both via `spring-boot-starter-websocket`, wiring `SimpMessagingTemplate` for server-push and `@MessageMapping` + `@SubscribeMapping` for handling frames.

## 2. Why & when

**Why over HTTP polling:**
- HTTP polling (client asks "anything new?" every second) wastes bandwidth and adds latency.
- WebSocket keeps one connection open; the server pushes immediately when data changes.

**Why STOMP over raw WebSocket:**
- Raw WebSocket is a byte stream — you manage framing, routing, and subscriptions yourself.
- STOMP adds destinations (`/topic/prices`, `/queue/user.123`) and subscribe semantics — Spring maps these to `@MessageMapping` methods automatically.

**When to use:**
- Live dashboards, collaborative editors, chat applications.
- Server-push notifications to specific users or broadcast to all.

**Not ideal for:** server-to-server messaging (use AMQP/Kafka) or simple one-off HTTP data fetches.

## 3. Core concept

Spring's STOMP-over-WebSocket architecture has three channels:

1. **Client connects** via WebSocket to a configured endpoint (e.g., `/ws`).
2. **Client subscribes** to a destination: `/topic/prices` (broadcast) or `/user/queue/replies` (personal).
3. **Client sends** STOMP SEND frames to `/app/some-route` → Spring routes to `@MessageMapping("some-route")`.
4. **Server publishes** via `SimpMessagingTemplate.convertAndSend("/topic/prices", payload)` → all subscribers receive it.

Key annotations:
- `@EnableWebSocketMessageBroker` — activates the subsystem.
- `@MessageMapping("/route")` — handles incoming SEND frames from clients.
- `@SendTo("/topic/dest")` — sends return value to a topic.
- `@SubscribeMapping("/route")` — responds to SUBSCRIBE frames (one-time reply to the subscriber).

An optional **message broker relay** connects Spring to a real STOMP broker (RabbitMQ, ActiveMQ) for true fan-out at scale.

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser connects via WebSocket/STOMP to Spring, server pushes to topic, multiple browsers receive">
  <!-- Browsers -->
  <rect x="10" y="50" width="100" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="60" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Browser A</text>

  <rect x="10" y="130" width="100" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="60" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Browser B</text>

  <!-- Arrows to Spring -->
  <line x1="113" y1="70" x2="200" y2="100" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#wa)"/>
  <line x1="113" y1="150" x2="200" y2="120" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#wa)"/>

  <!-- Spring Boot WebSocket -->
  <rect x="205" y="65" width="175" height="95" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="292" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring WebSocket</text>
  <text x="292" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@MessageMapping</text>
  <text x="292" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SimpMessagingTemplate</text>
  <text x="292" y="136" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">in-memory broker</text>
  <text x="292" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/topic/  /queue/  /app/</text>

  <!-- Arrow to optional broker -->
  <line x1="383" y1="112" x2="450" y2="112" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#wb)"/>
  <rect x="455" y="88" width="130" height="48" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="520" y="109" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Optional Broker Relay</text>
  <text x="520" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">RabbitMQ / ActiveMQ</text>

  <!-- Push arrows back to browsers -->
  <line x1="205" y1="85" x2="117" y2="70" stroke="#6db33f" stroke-width="2" marker-end="url(#wb)"/>
  <line x1="205" y1="140" x2="117" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#wb)"/>
  <text x="155" y="62" fill="#6db33f" font-size="8" font-family="sans-serif">push</text>
  <text x="155" y="168" fill="#6db33f" font-size="8" font-family="sans-serif">push</text>

  <text x="360" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Browsers subscribe to /topic/; server publishes once, all subscribers receive simultaneously</text>

  <defs>
    <marker id="wa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

All subscribers on `/topic/prices` receive each push in a single `convertAndSend` call.

## 5. Runnable example

```java
// WebSocketStompDemo.java — simulates STOMP messaging without a server
// How to run: java WebSocketStompDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-websocket; use @EnableWebSocketMessageBroker

import java.util.*;

public class WebSocketStompDemo {

    // Simulate subscriptions: destination -> list of sessionIds
    static final Map<String, List<String>> subscriptions = new LinkedHashMap<>();
    // Simulate per-session message queues
    static final Map<String, List<String>> sessions = new LinkedHashMap<>();

    // Client subscribes to a STOMP destination
    static void subscribe(String sessionId, String destination) {
        subscriptions.computeIfAbsent(destination, k -> new ArrayList<>()).add(sessionId);
        sessions.putIfAbsent(sessionId, new ArrayList<>());
        System.out.printf("[STOMP SUBSCRIBE] session=%s  destination=%s%n", sessionId, destination);
    }

    // SimpMessagingTemplate.convertAndSend() equivalent
    static void broadcast(String destination, String payload) {
        List<String> subs = subscriptions.getOrDefault(destination, List.of());
        System.out.printf("%n[SimpMessagingTemplate] convertAndSend('%s', '%s') -> %d subscriber(s)%n",
                destination, payload, subs.size());
        for (String sessionId : subs) {
            sessions.get(sessionId).add(payload);
            System.out.printf("  pushed to session: %s%n", sessionId);
        }
    }

    // SimpMessagingTemplate.convertAndSendToUser() — personal queue
    static void sendToUser(String username, String queue, String payload) {
        String destination = "/user/" + username + queue;
        System.out.printf("%n[SimpMessagingTemplate] convertAndSendToUser('%s', '%s', '%s')%n",
                username, queue, payload);
        List<String> subs = subscriptions.getOrDefault(destination, List.of());
        subs.forEach(sid -> {
            sessions.get(sid).add(payload);
            System.out.printf("  private push to session: %s%n", sid);
        });
    }

    // @MessageMapping handler processes incoming SEND frames
    static void handleChat(String sessionId, String payload) {
        System.out.printf("%n[@MessageMapping('/chat')] from session=%s: '%s'%n", sessionId, payload);
        broadcast("/topic/chat", "Echo: " + payload);
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== WebSocket Messaging (STOMP) Demo ===\n");

        // 1. Clients connect and subscribe
        subscribe("sess-Alice", "/topic/chat");
        subscribe("sess-Bob",   "/topic/chat");
        subscribe("sess-Alice", "/user/Alice/queue/private");

        // 2. Server broadcasts a price update
        broadcast("/topic/chat", "Welcome to the chat room!");

        // 3. Client sends a message -> @MessageMapping processes it
        handleChat("sess-Alice", "Hello everyone");

        // 4. Server sends private message to Alice
        sendToUser("Alice", "/queue/private", "Alice, you have an admin notification");

        // 5. Show received messages per session
        System.out.println("\n--- Message Inboxes ---");
        sessions.forEach((sid, msgs) ->
            System.out.printf("Session %s received %d messages: %s%n", sid, msgs.size(), msgs));
    }
}
```

**How to run:** `java WebSocketStompDemo.java`

## 6. Walkthrough

- **`subscribe`** simulates the STOMP SUBSCRIBE frame. In Spring Boot, the client JavaScript calls `stompClient.subscribe('/topic/chat', callback)`.
- **`broadcast`** simulates `SimpMessagingTemplate.convertAndSend("/topic/chat", msg)` — one call pushes to all subscribers.
- **`sendToUser`** simulates `convertAndSendToUser("Alice", "/queue/private", msg)` — Spring builds the user-specific destination path and delivers to Alice's session only.
- **`handleChat`** simulates `@MessageMapping("/chat")` — Spring extracts the payload, calls the method, and its `@SendTo("/topic/chat")` return value (or explicit `broadcast` call) fans out to all.
- The inbox printout shows that Bob only received the broadcast messages, while Alice also received the private one.

## 7. Gotchas & takeaways

> The in-memory broker (`registry.enableSimpleBroker("/topic", "/queue")`) **does not survive server restart** and doesn't scale beyond one JVM instance. For multiple instances, configure a broker relay: `registry.enableStompBrokerRelay("/topic", "/queue").setRelayHost("rabbit")`.

> WebSocket connections stay open indefinitely — configure heartbeats (`setHeartbeatValue`) to detect dead connections and `setTaskScheduler` to drive them.

- Add `spring-boot-starter-websocket`; annotate a config class with `@EnableWebSocketMessageBroker`.
- `configureMessageBroker`: set `/topic` and `/queue` as broker destinations; `/app` as the application prefix.
- `registerStompEndpoints`: expose `/ws` (add `.withSockJS()` for fallback in older browsers).
- `@MessageMapping("/route")` + `@SendTo("/topic/dest")` is the common pattern for handling and broadcasting.
- Test with `StompClient` in Java tests or the STOMP.js library in the browser.
