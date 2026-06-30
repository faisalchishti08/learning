---
card: spring-framework
gi: 66
slug: websocket-scope
title: websocket scope
---

## 1. What it is

**WebSocket scope** creates one bean instance per WebSocket session. A WebSocket session begins when a client opens a WebSocket connection and ends when the connection closes. Within that session, all message handlers and beans that participate in the same WebSocket conversation share the same scoped bean instance.

```java
@Component
@Scope(scopeName = "websocket",
       proxyMode = ScopedProxyMode.TARGET_CLASS)
public class WebSocketSubscriptionState {
    private final Set<String> subscribedTopics = new CopyOnWriteArraySet<>();
    // Holds state for one client's WebSocket connection lifetime
}
```

WebSocket scope is provided by Spring's messaging infrastructure (`spring-messaging` / `spring-websocket`) and must be explicitly registered — it is not available by default in a servlet container.

In one sentence: **A WebSocket-scoped bean lives for the lifetime of a single WebSocket connection, giving each connected client their own stateful bean for the duration of that long-lived TCP conversation.**

## 2. Why & when

Use WebSocket scope for:

- **Subscription state** — which topics a connected client has subscribed to.
- **Per-connection message buffer** — accumulate partial messages for a client.
- **Connection-specific configuration** — locale, user identity, compression settings resolved at handshake.
- **Chat room context** — the room a user is in, their display name, message rate state.

WebSocket sessions are typically longer than HTTP requests but shorter than HTTP sessions. Unlike HTTP session scope, a WebSocket session has no idle timeout — it lasts until the TCP connection closes.

Do NOT use WebSocket scope in non-WebSocket code paths (HTTP controllers, batch jobs) — the WebSocket scope is not registered in those contexts.

## 3. Core concept

```
WebSocket scope registration (required):
  @Configuration
  @EnableWebSocketMessageBroker
  public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    @Override
    public void configureWebSocketTransport(WebSocketTransportRegistration reg) {
      // scope is auto-registered by @EnableWebSocketMessageBroker
    }
  }

  Or manually:
  ConfigurableBeanFactory bf = ...;
  bf.registerScope("websocket", new WebSocketScope());

Lifecycle:
  Client connects → WebSocket session created
    → WebSocket-scoped bean created for this session
    → All @MessageMapping methods running in this session's thread(s)
       get the SAME bean instance
  Client disconnects → bean.destroy() called

Relationship to HTTP session:
  One HTTP session can have MULTIPLE WebSocket sessions (multiple tabs).
  HTTP session scope ≠ WebSocket scope.
  WebSocket scope is nested inside the HTTP session's lifecycle.
```

## 4. Diagram

<svg viewBox="0 0 660 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebSocket scope: one bean per WebSocket connection, multiple connections from same HTTP session are separate">
  <defs>
    <marker id="a66" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="202" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">WebSocket scope — one bean per WebSocket connection</text>

  <!-- HTTP Session (Alice) -->
  <rect x="15" y="30" width="630" height="160" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="330" y="47" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP Session (Alice — JSESSIONID=AAA)</text>

  <!-- WS Connection 1 (tab 1) -->
  <rect x="30" y="55" width="290" height="125" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="175" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">WebSocket WS-1 (browser tab 1)</text>

  <rect x="40" y="80" width="270" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="175" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">SubscriptionState#WS1 — topics=[/chat/room-A]</text>

  <text x="175" y="122" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">MSG 1: subscribe /chat/room-A → state updated</text>
  <text x="175" y="135" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">MSG 2: send "hello" → state used for routing</text>
  <text x="175" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">MSG 3: unsubscribe → state updated</text>
  <text x="175" y="165" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">Tab closed → WS-1 closed → SubscriptionState#WS1 destroyed</text>

  <!-- WS Connection 2 (tab 2) -->
  <rect x="340" y="55" width="290" height="125" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">WebSocket WS-2 (browser tab 2)</text>

  <rect x="350" y="80" width="270" height="28" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="485" y="97" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">SubscriptionState#WS2 — topics=[/chat/room-B]</text>

  <text x="485" y="122" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Different topics, separate bean instance</text>
  <text x="485" y="135" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">WS-1 state never leaked into WS-2</text>
  <text x="485" y="165" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">Independent from WS-1 lifecycle</text>

  <text x="330" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Alice's two browser tabs = two WS sessions = two SubscriptionState beans. HTTP session = one.</text>
</svg>

Alice opens two browser tabs — two WebSocket sessions, two `SubscriptionState` beans. Both are under the same HTTP session (same `JSESSIONID`) but are independent WebSocket-scoped instances.

## 5. Runnable example

Scenario: a `ChatRoomState` bean that tracks a connected user's current room, unread messages, and typing indicator — one per WebSocket connection.

### Level 1 — Basic

Simulate one WebSocket session lifecycle: connect → send messages → disconnect.

```java
// WebSocketScopeDemo.java — run with: java WebSocketScopeDemo.java
import java.util.*;

public class WebSocketScopeDemo {

    // ── websocket-scoped bean ─────────────────────────────────────────
    static class ChatRoomState {
        private static int count = 0;
        final int    id;
        final String wsSessionId;
        final String userId;
        private String currentRoom;
        private final List<String> unreadMessages = new ArrayList<>();
        private boolean typing = false;

        ChatRoomState(String wsSessionId, String userId) {
            id            = ++count;
            this.wsSessionId = wsSessionId;
            this.userId      = userId;
            System.out.println("  [WS BEAN CREATED #" + id + "] ws=" + wsSessionId
                + " user=" + userId);
        }

        void joinRoom(String room) {
            currentRoom = room;
            System.out.println("  [JOIN] user=" + userId + " room=" + room + " ws=" + wsSessionId);
        }

        void receiveMessage(String from, String text) {
            unreadMessages.add(from + ": " + text);
            System.out.println("  [RECV] " + from + " → " + userId + ": " + text
                + " (unread=" + unreadMessages.size() + ")");
        }

        void setTyping(boolean t) {
            typing = t;
            System.out.println("  [TYPING] " + userId + (t ? " started" : " stopped") + " typing");
        }

        List<String> markAllRead() {
            List<String> msgs = new ArrayList<>(unreadMessages);
            unreadMessages.clear();
            System.out.println("  [READ ALL] " + userId + " read " + msgs.size() + " messages");
            return msgs;
        }

        void destroy() {
            System.out.println("  [WS BEAN DESTROYED #" + id + "] ws=" + wsSessionId
                + " user=" + userId + " room=" + currentRoom
                + " unread=" + unreadMessages.size());
        }
    }

    // ── simulated WebSocket message handler ───────────────────────────
    static void handleMessage(ChatRoomState state, String type, String... args) {
        System.out.println("[MSG] wsId=" + state.wsSessionId + " type=" + type);
        switch (type) {
            case "JOIN"    -> state.joinRoom(args[0]);
            case "RECEIVE" -> state.receiveMessage(args[0], args[1]);
            case "TYPING"  -> state.setTyping(Boolean.parseBoolean(args[0]));
            case "READ"    -> state.markAllRead();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Alice connects on tab 1 ===");
        ChatRoomState ws1 = new ChatRoomState("ws-001", "alice");
        handleMessage(ws1, "JOIN",    "room-general");
        handleMessage(ws1, "RECEIVE", "bob",   "Hey Alice!");
        handleMessage(ws1, "RECEIVE", "carol", "Hello everyone!");
        handleMessage(ws1, "TYPING",  "true");
        handleMessage(ws1, "TYPING",  "false");
        handleMessage(ws1, "READ");

        System.out.println("\n=== Bob connects ===");
        ChatRoomState ws2 = new ChatRoomState("ws-002", "bob");
        handleMessage(ws2, "JOIN",    "room-dev");
        handleMessage(ws2, "RECEIVE", "dave",  "PR #42 is ready");

        System.out.println("\n=== Alice receives more, then disconnects ===");
        handleMessage(ws1, "RECEIVE", "dave", "Ping!");

        System.out.println("\n=== Connection closures ===");
        ws1.destroy();
        ws2.destroy();
        System.out.println("[WS BEANS CREATED] " + ChatRoomState.count);
    }
}
```

How to run: `java WebSocketScopeDemo.java`

Two WebSocket connections → two `ChatRoomState` instances. Alice's `ws1` and Bob's `ws2` are completely independent. `ws1.destroy()` is called when Alice's tab closes — Bob's `ws2` is unaffected. The `count` verifies only two instances were ever created.

### Level 2 — Intermediate

Multiple WebSocket connections from the same user (two tabs) — each gets its own scoped bean, demonstrating that WebSocket scope is narrower than HTTP session scope.

```java
// WebSocketScopeDemo2.java — run with: java WebSocketScopeDemo2.java
import java.util.*;

public class WebSocketScopeDemo2 {

    // ── websocket-scoped state ─────────────────────────────────────────
    static class ConnectionState {
        private static int count = 0;
        final int    id;
        final String wsId;
        final String userId;
        final String userAgent;
        private String room;
        private int    messagesSent     = 0;
        private int    messagesReceived = 0;
        private final long connectedMs  = System.currentTimeMillis();

        ConnectionState(String wsId, String userId, String userAgent) {
            id = ++count;
            this.wsId      = wsId;
            this.userId    = userId;
            this.userAgent = userAgent;
            System.out.printf("  [WS#%d CREATED] wsId=%s user=%s ua=%s%n",
                id, wsId, userId, userAgent.substring(0, Math.min(userAgent.length(), 20)));
        }

        void joinRoom(String r)   { room = r; System.out.printf("  [WS#%d] joined %s%n", id, r); }
        void sent()               { messagesSent++; }
        void received(String msg) { messagesReceived++;
            System.out.printf("  [WS#%d] recv msg=%s (total=%d)%n", id, msg, messagesReceived); }

        String stats() {
            long durationMs = System.currentTimeMillis() - connectedMs;
            return String.format("WS#%d wsId=%s user=%s room=%s sent=%d recv=%d duration=%dms",
                id, wsId, userId, room, messagesSent, messagesReceived, durationMs);
        }

        void destroy() { System.out.println("  [WS#" + id + " DESTROYED] " + stats()); }
    }

    // ── simulated server: maps wsId → connection state ─────────────────
    static class ChatServer {
        private final Map<String, ConnectionState> connections = new LinkedHashMap<>();

        void connect(String wsId, String userId, String userAgent) {
            connections.put(wsId, new ConnectionState(wsId, userId, userAgent));
        }

        void sendMessage(String wsId, String room, String msg) {
            ConnectionState state = connections.get(wsId);
            System.out.printf("[SEND] wsId=%s user=%s room=%s msg=%s%n",
                wsId, state.userId, room, msg);
            state.joinRoom(room);
            state.sent();
            // Deliver to other connections in same room
            connections.values().stream()
                .filter(s -> room.equals(s.room) && !s.wsId.equals(wsId))
                .forEach(s -> s.received(state.userId + ": " + msg));
        }

        void disconnect(String wsId) {
            ConnectionState s = connections.remove(wsId);
            if (s != null) s.destroy();
        }

        void printAll() {
            System.out.println("[ACTIVE WS CONNECTIONS] " + connections.size());
            connections.values().forEach(s -> System.out.println("  " + s.stats()));
        }
    }

    public static void main(String[] args) {
        ChatServer server = new ChatServer();

        System.out.println("=== Connections ===");
        server.connect("ws-alice-tab1", "alice", "Chrome/120 (Desktop)");
        server.connect("ws-alice-tab2", "alice", "Chrome/120 (Mobile)");  // SAME user, DIFFERENT ws bean
        server.connect("ws-bob",        "bob",   "Firefox/121");

        System.out.println("\n=== Alice joins room from both tabs ===");
        server.sendMessage("ws-alice-tab1", "room-general", "Hello from desktop!");
        server.sendMessage("ws-alice-tab2", "room-general", "Also here on mobile");
        server.sendMessage("ws-bob",        "room-general", "Hey Alice!");

        System.out.println("\n[KEY] Alice has TWO WS beans (#1 and #2) — same HTTP session, different WS sessions");
        server.printAll();

        System.out.println("\n=== Disconnections ===");
        server.disconnect("ws-alice-tab1");  // only tab1 closed — tab2 still active
        System.out.println("  Alice tab2 still active:");
        server.printAll();
        server.disconnect("ws-alice-tab2");
        server.disconnect("ws-bob");
        System.out.println("[WS BEANS TOTAL] " + ConnectionState.count);
    }
}
```

How to run: `java WebSocketScopeDemo2.java`

Alice has two WebSocket connections (desktop + mobile) from what would be the same HTTP session. Two separate `ConnectionState` beans (#1 and #2). Closing tab1 destroys `ConnectionState#1` but `ConnectionState#2` (mobile tab) lives on. Three WebSocket connections → three WS-scoped beans.

### Level 3 — Advanced

A pub-sub system where WebSocket-scoped beans track subscriptions and the server routes messages to the right connection beans.

```java
// WebSocketScopeDemo3.java — run with: java WebSocketScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class WebSocketScopeDemo3 {

    // ── websocket-scoped subscription tracker ─────────────────────────
    static class SubscriptionTracker {
        private static final ConcurrentHashMap<String, SubscriptionTracker> REGISTRY =
            new ConcurrentHashMap<>();
        private static int count = 0;

        final int    id;
        final String wsId;
        final String userId;
        private final Set<String> subscriptions = new CopyOnWriteArraySet<>();
        private int  totalDelivered = 0;
        private int  totalDropped   = 0;

        SubscriptionTracker(String wsId, String userId) {
            id = ++count;
            this.wsId   = wsId;
            this.userId = userId;
            REGISTRY.put(wsId, this);
            System.out.printf("  [WS TRACKER#%d] wsId=%s user=%s%n", id, wsId, userId);
        }

        void subscribe(String topic) {
            subscriptions.add(topic);
            System.out.printf("  [WS#%d] SUBSCRIBE %s (total=%d)%n", id, topic, subscriptions.size());
        }

        void unsubscribe(String topic) {
            subscriptions.remove(topic);
            System.out.printf("  [WS#%d] UNSUBSCRIBE %s (remaining=%d)%n", id, topic, subscriptions.size());
        }

        boolean isSubscribed(String topic) { return subscriptions.contains(topic); }

        void deliver(String topic, String payload) {
            if (isSubscribed(topic)) {
                totalDelivered++;
                System.out.printf("    → [WS#%d %s] topic=%s payload=%s%n",
                    id, userId, topic, payload);
            } else {
                totalDropped++;
            }
        }

        void destroy() {
            REGISTRY.remove(wsId);
            System.out.printf("  [WS TRACKER#%d DESTROYED] user=%s delivered=%d dropped=%d subs=%s%n",
                id, userId, totalDelivered, totalDropped, subscriptions);
        }

        static Collection<SubscriptionTracker> all() { return REGISTRY.values(); }
    }

    // ── pub/sub broker ────────────────────────────────────────────────
    static class MessageBroker {
        void publish(String topic, String payload) {
            System.out.printf("[PUBLISH] topic=%s payload=%s → routing to %d connections...%n",
                topic, payload, SubscriptionTracker.all().size());
            SubscriptionTracker.all().forEach(t -> t.deliver(topic, payload));
        }
    }

    public static void main(String[] args) {
        MessageBroker broker = new MessageBroker();

        System.out.println("=== Connections ===");
        SubscriptionTracker ws1 = new SubscriptionTracker("ws-alice-1", "alice");
        SubscriptionTracker ws2 = new SubscriptionTracker("ws-alice-2", "alice");  // second tab
        SubscriptionTracker ws3 = new SubscriptionTracker("ws-bob",     "bob");
        SubscriptionTracker ws4 = new SubscriptionTracker("ws-carol",   "carol");

        System.out.println("\n=== Subscriptions ===");
        ws1.subscribe("/topic/orders");
        ws1.subscribe("/topic/notifications");
        ws2.subscribe("/topic/dashboard");              // alice's second tab: different topics
        ws3.subscribe("/topic/orders");
        ws3.subscribe("/topic/admin");
        ws4.subscribe("/topic/orders");
        ws4.subscribe("/topic/notifications");
        ws4.subscribe("/topic/dashboard");

        System.out.println("\n=== Publishing events ===");
        broker.publish("/topic/orders",        "order#ORD-001 shipped");
        System.out.println();
        broker.publish("/topic/notifications", "maintenance window in 1h");
        System.out.println();
        broker.publish("/topic/admin",         "new user registered");
        System.out.println();

        System.out.println("=== Alice unsubscribes notifications on tab 1 ===");
        ws1.unsubscribe("/topic/notifications");
        broker.publish("/topic/notifications", "system restored");

        System.out.println("\n=== Disconnections ===");
        ws1.destroy();
        ws2.destroy();
        ws3.destroy();
        ws4.destroy();
        System.out.println("[TOTAL WS BEANS CREATED] " + SubscriptionTracker.count);
    }
}
```

How to run: `java WebSocketScopeDemo3.java`

Four WebSocket connections, each a separate `SubscriptionTracker` bean. When `/topic/orders` is published, `ws1`, `ws3`, `ws4` receive it (subscribed); `ws2` does not (subscribed to `/topic/dashboard`). Alice's two tabs have independent subscription sets. The `REGISTRY` (equivalent to the Spring WebSocket scope store) maps `wsId → bean` and is cleaned on disconnect.

## 6. Walkthrough

**`broker.publish("/topic/orders", "order#ORD-001 shipped")`:**

```
all() = {ws1, ws2, ws3, ws4}

ws1.deliver("/topic/orders", "order#ORD-001 shipped"):
  isSubscribed("/topic/orders") → true (subscriptions={/topic/orders, /topic/notifications})
  totalDelivered++ → 1
  → [WS#1 alice] topic=/topic/orders payload=order#ORD-001 shipped

ws2.deliver("/topic/orders", "order#ORD-001 shipped"):
  isSubscribed("/topic/orders") → false (subscriptions={/topic/dashboard})
  totalDropped++ → 1
  → (no delivery)

ws3.deliver("/topic/orders", "order#ORD-001 shipped"):
  isSubscribed → true (subscriptions={/topic/orders, /topic/admin})
  → [WS#3 bob] topic=/topic/orders ...

ws4.deliver("/topic/orders", "order#ORD-001 shipped"):
  isSubscribed → true (subscriptions include /topic/orders)
  → [WS#4 carol] topic=/topic/orders ...

Delivered to ws1, ws3, ws4. Dropped for ws2.
```

**`ws1.destroy()` — connection close:**

```
REGISTRY.remove("ws-alice-1") → ws1 removed from pub-sub routing
subscriptions = {} (after unsubscribe above)
totalDelivered=1 (for orders), totalDropped=0 (already unsubscribed notifications before publish)
[WS TRACKER#1 DESTROYED] user=alice delivered=1 dropped=0
```

## 7. Gotchas & takeaways

> **WebSocket scope is NOT registered by default in a standard Spring application.** You must either use `@EnableWebSocketMessageBroker` (which registers it automatically) or manually register `WebSocketScope` with `ConfigurableBeanFactory.registerScope("websocket", new WebSocketScope())`. Without this, `@Scope("websocket")` throws `NoSuchBeanDefinitionException` at startup.

> **`@PreDestroy` IS called on WebSocket-scoped beans** — unlike prototype beans. The WebSocket scope keeps track of each session's beans and calls their destroy callbacks when the WebSocket session closes.

- One HTTP session can contain many WebSocket sessions (one per browser tab). Do not confuse WebSocket scope with session scope — they are independent.
- WebSocket-scoped beans cannot be injected into singletons without `proxyMode = ScopedProxyMode.TARGET_CLASS`, for the same reason as request and session scope.
- STOMP over WebSocket (the most common Spring use case) attaches WebSocket sessions to an internal session store — the WebSocket scope reads from this store to return the correct per-session bean.
- If the WebSocket connection drops (network interruption) without a clean close, the WebSocket session may remain active until a heartbeat timeout — the scoped bean is also kept alive during this window.
