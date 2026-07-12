---
card: spring-security
gi: 119
slug: websocket-security
title: "WebSocket security"
---

## 1. What it is

A WebSocket connection begins life as an ordinary HTTP request (the "upgrade" handshake), so the standard `SecurityFilterChain` from every earlier card already authenticates *that* initial request normally — but once the connection upgrades to a long-lived, bidirectional WebSocket, every subsequent message flowing over it is no longer a separate HTTP request the filter chain can intercept individually. Spring Security's WebSocket support addresses this at the STOMP messaging layer (Spring's higher-level protocol commonly layered over raw WebSockets): `AuthorizationChannelInterceptor`, wired via `@EnableWebSocketSecurity`, inspects each inbound STOMP `Message` — `CONNECT`, `SUBSCRIBE`, `SEND` — and authorizes it individually, using the principal established during the original handshake.

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketSecurityConfig {

    @Bean
    AuthorizationManager<Message<?>> messageAuthorizationManager(MessageMatcherDelegatingAuthorizationManager.Builder messages) {
        messages
            .simpDestMatchers("/topic/public/**").permitAll()
            .simpSubscribeDestMatchers("/user/queue/**").authenticated()
            .simpDestMatchers("/app/admin/**").hasRole("ADMIN")
            .anyMessage().authenticated();
        return messages.build();
    }
}
```

## 2. Why & when

Every authorization mechanism covered so far — `authorizeHttpRequests`, method security — assumes a discrete request/response cycle where a filter chain runs, makes a decision, and the request either proceeds or is rejected, all within one HTTP exchange. A WebSocket connection breaks that model at the transport level: after the initial handshake, an application can receive an arbitrary number of messages over the *same* open connection, each one potentially targeting a different destination (a chat channel, an admin command topic) that may warrant a completely different authorization decision — a user authenticated to read `/topic/public/announcements` shouldn't automatically be authorized to send messages to `/app/admin/broadcast` over that same socket. WebSocket security exists specifically to re-introduce per-message authorization into a transport that would otherwise only ever check identity once, at connection time.

Reach for WebSocket security when:

- Building a chat, live-notification, or collaborative-editing feature where different STOMP destinations warrant different access levels — some public, some requiring authentication, some requiring a specific role.
- A single WebSocket connection is used for both reading (subscribing to updates) and writing (sending commands) — these are frequently different authorization concerns (`simpSubscribeDestMatchers` vs. `simpDestMatchers` for sends) even over the same socket.
- The application needs to prevent a connected-but-unprivileged client from subscribing to a destination carrying sensitive data (another user's private notification queue, for instance) despite having successfully completed the initial handshake as *some* authenticated user.

## 3. Core concept

```
WebSocket / STOMP message types Spring Security can authorize independently:
    CONNECT      -- the initial handshake message (identity already established via the HTTP upgrade)
    SUBSCRIBE    -- a client asking to RECEIVE messages sent to a destination (e.g. /topic/chat)
    SEND         -- a client asking to SEND a message to a destination (e.g. /app/chat.send)
    DISCONNECT   -- the connection closing

AuthorizationChannelInterceptor, per INBOUND message:
  1. read the message's destination and type (SUBSCRIBE vs SEND vs CONNECT)
  2. find the FIRST matching rule (simpDestMatchers / simpSubscribeDestMatchers / etc.), in order
  3. evaluate that rule against the principal established at CONNECT time
  4. rule passes -> message proceeds to its handler
     rule fails  -> message REJECTED, an error frame sent back (or the message silently dropped,
                    depending on configuration) -- the CONNECTION itself is NOT necessarily closed

CRITICAL: authorization here happens PER MESSAGE, not once per connection --
          a connection legitimately established (CONNECT authorized) can still have
          INDIVIDUAL messages over it rejected based on destination-specific rules.
```

Distinguishing `simpDestMatchers` (applies broadly, including sends) from `simpSubscribeDestMatchers` (applies specifically to subscription requests) lets read and write access to the same general area be governed by different rules.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing one open websocket connection carrying multiple stomp messages over time each message being individually authorized against destination specific rules regardless of the connections original successful handshake">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="320" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ONE open WebSocket connection (established once, via HTTP upgrade + CONNECT)</text>

  <rect x="40" y="80" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="115" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SUBSCRIBE</text>
  <text x="115" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">/topic/public/news</text>

  <rect x="255" y="80" width="150" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="330" y="100" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">SEND</text>
  <text x="330" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">/app/admin/broadcast</text>

  <rect x="470" y="80" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="545" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SUBSCRIBE</text>
  <text x="545" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">/user/queue/notify</text>

  <line x1="115" y1="130" x2="115" y2="160" stroke="#3fb950" stroke-width="1.6" marker-end="url(#ws119)"/>
  <line x1="330" y1="130" x2="330" y2="160" stroke="#f85149" stroke-width="1.6" marker-end="url(#ws119b)"/>
  <line x1="545" y1="130" x2="545" y2="160" stroke="#3fb950" stroke-width="1.6" marker-end="url(#ws119)"/>

  <rect x="40" y="162" width="150" height="30" rx="5" fill="#1c2430" stroke="#3fb950" stroke-width="1.2"/>
  <text x="115" y="182" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">ALLOWED (public)</text>

  <rect x="255" y="162" width="150" height="30" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="330" y="182" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">DENIED (needs ROLE_ADMIN)</text>

  <rect x="470" y="162" width="150" height="30" rx="5" fill="#1c2430" stroke="#3fb950" stroke-width="1.2"/>
  <text x="545" y="182" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">ALLOWED (own queue)</text>

  <defs>
    <marker id="ws119" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="ws119b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Each message over the one open connection is judged independently against its own destination-matched rule.

## 5. Runnable example

The scenario: model a STOMP-style message authorizer, growing from a single rule check into ordered rule matching (subscribe vs. send treated differently), then into a full simulated connection sending a mix of messages, some allowed and some rejected, without the connection itself ever closing.

### Level 1 — Basic

One rule, one message, checked.

```java
import java.util.*;

public class WebSocketSecurityLevel1 {
    record StompMessage(String type, String destination, Set<String> principalAuthorities) {}

    static boolean isAuthorized(StompMessage message, String requiredAuthority) {
        return message.principalAuthorities().contains(requiredAuthority);
    }

    public static void main(String[] args) {
        StompMessage subscribeToAdmin = new StompMessage("SUBSCRIBE", "/topic/admin/alerts", Set.of("ROLE_USER"));

        System.out.println("authorized: " + isAuthorized(subscribeToAdmin, "ROLE_ADMIN"));
    }
}
```

**How to run:** save as `WebSocketSecurityLevel1.java`, run `java WebSocketSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
authorized: false
```

`isAuthorized` is the minimal shape of `AuthorizationChannelInterceptor`'s per-message check: given a message and a required authority, does the connection's established principal have it?

### Level 2 — Intermediate

An ordered rule list distinguishing subscribe-specific rules from general destination rules, mirroring `simpSubscribeDestMatchers` versus `simpDestMatchers`.

```java
import java.util.*;
import java.util.function.*;

public class WebSocketSecurityLevel2 {
    record StompMessage(String type, String destination, Set<String> principalAuthorities) {}
    record Rule(Predicate<StompMessage> matcher, String requirement) {}

    static class MessageAuthorizationManager {
        private final List<Rule> rules = new ArrayList<>();

        MessageAuthorizationManager simpDestMatchers(String pattern, String requirement) {
            rules.add(new Rule(m -> matches(m.destination(), pattern), requirement));
            return this;
        }
        MessageAuthorizationManager simpSubscribeDestMatchers(String pattern, String requirement) {
            rules.add(new Rule(m -> "SUBSCRIBE".equals(m.type()) && matches(m.destination(), pattern), requirement));
            return this;
        }
        MessageAuthorizationManager anyMessage(String requirement) {
            rules.add(new Rule(m -> true, requirement));
            return this;
        }

        boolean authorize(StompMessage message) {
            for (Rule rule : rules) {
                if (rule.matcher().test(message)) {
                    return switch (rule.requirement()) {
                        case "permitAll" -> true;
                        case "authenticated" -> !message.principalAuthorities().isEmpty();
                        default -> message.principalAuthorities().contains(rule.requirement()); // a specific role/authority
                    };
                }
            }
            return false;
        }

        private static boolean matches(String destination, String pattern) {
            return destination.matches(pattern.replace("**", ".*"));
        }
    }

    public static void main(String[] args) {
        MessageAuthorizationManager manager = new MessageAuthorizationManager()
                .simpDestMatchers("/topic/public/**", "permitAll")
                .simpSubscribeDestMatchers("/user/queue/**", "authenticated")
                .simpDestMatchers("/app/admin/**", "ROLE_ADMIN")
                .anyMessage("authenticated");

        StompMessage publicSubscribe = new StompMessage("SUBSCRIBE", "/topic/public/news", Set.of());
        StompMessage privateQueueSubscribe = new StompMessage("SUBSCRIBE", "/user/queue/notify", Set.of("ROLE_USER"));
        StompMessage adminSend = new StompMessage("SEND", "/app/admin/broadcast", Set.of("ROLE_USER"));

        System.out.println("anonymous subscribes to public topic: " + manager.authorize(publicSubscribe));
        System.out.println("authenticated user subscribes to own queue: " + manager.authorize(privateQueueSubscribe));
        System.out.println("regular user sends to admin destination: " + manager.authorize(adminSend));
    }
}
```

**How to run:** save as `WebSocketSecurityLevel2.java`, run `java WebSocketSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
anonymous subscribes to public topic: true
authenticated user subscribes to own queue: true
regular user sends to admin destination: false
```

What changed: rules are now checked in order, first match wins — a public topic subscription needs no authentication at all, a private queue subscription needs any authenticated principal, and an admin destination needs a specific role — exactly mirroring the real `MessageMatcherDelegatingAuthorizationManager.Builder`'s configuration shape.

### Level 3 — Advanced

Simulate one full connection sending a sequence of messages over time, some allowed and some rejected — critically, a rejected message does not close the connection, only that specific message is refused, and later messages on the same connection are still evaluated independently.

```java
import java.util.*;
import java.util.function.*;

public class WebSocketSecurityLevel3 {
    record StompMessage(String type, String destination, Set<String> principalAuthorities) {}
    record Rule(Predicate<StompMessage> matcher, String requirement) {}

    static class MessageDeniedException extends RuntimeException { MessageDeniedException(String m) { super(m); } }

    static class MessageAuthorizationManager {
        private final List<Rule> rules = new ArrayList<>();
        MessageAuthorizationManager simpDestMatchers(String pattern, String requirement) {
            rules.add(new Rule(m -> matches(m.destination(), pattern), requirement)); return this;
        }
        MessageAuthorizationManager simpSubscribeDestMatchers(String pattern, String requirement) {
            rules.add(new Rule(m -> "SUBSCRIBE".equals(m.type()) && matches(m.destination(), pattern), requirement)); return this;
        }
        MessageAuthorizationManager anyMessage(String requirement) { rules.add(new Rule(m -> true, requirement)); return this; }

        boolean authorize(StompMessage message) {
            for (Rule rule : rules) {
                if (rule.matcher().test(message)) {
                    return switch (rule.requirement()) {
                        case "permitAll" -> true;
                        case "authenticated" -> !message.principalAuthorities().isEmpty();
                        default -> message.principalAuthorities().contains(rule.requirement());
                    };
                }
            }
            return false;
        }
        private static boolean matches(String destination, String pattern) { return destination.matches(pattern.replace("**", ".*")); }
    }

    // simulates ONE open connection processing a SEQUENCE of messages, one at a time
    static class WebSocketConnection {
        private final Set<String> principalAuthorities;
        private final MessageAuthorizationManager manager;
        private boolean stillOpen = true;
        private int processedCount = 0;

        WebSocketConnection(Set<String> principalAuthorities, MessageAuthorizationManager manager) {
            this.principalAuthorities = principalAuthorities;
            this.manager = manager;
        }

        void send(String type, String destination) {
            if (!stillOpen) { System.out.println("  connection already closed, message dropped"); return; }
            StompMessage message = new StompMessage(type, destination, principalAuthorities);
            processedCount++;
            if (manager.authorize(message)) {
                System.out.println("  [" + type + " " + destination + "] ALLOWED -- connection stays OPEN");
            } else {
                // REJECTED, but the connection itself is NOT closed -- only this message is refused
                System.out.println("  [" + type + " " + destination + "] DENIED -- connection stays OPEN, only this message refused");
            }
        }

        int getProcessedCount() { return processedCount; }
        boolean isOpen() { return stillOpen; }
    }

    public static void main(String[] args) {
        MessageAuthorizationManager manager = new MessageAuthorizationManager()
                .simpDestMatchers("/topic/public/**", "permitAll")
                .simpSubscribeDestMatchers("/user/queue/**", "authenticated")
                .simpDestMatchers("/app/admin/**", "ROLE_ADMIN")
                .anyMessage("authenticated");

        // bob is a regular, authenticated user -- no ROLE_ADMIN
        WebSocketConnection bobConnection = new WebSocketConnection(Set.of("ROLE_USER"), manager);

        System.out.println("--- bob's single connection, multiple messages over time ---");
        bobConnection.send("SUBSCRIBE", "/topic/public/news");     // allowed
        bobConnection.send("SUBSCRIBE", "/user/queue/notify");     // allowed
        bobConnection.send("SEND", "/app/admin/broadcast");        // denied -- but connection stays open
        bobConnection.send("SEND", "/app/chat.send");               // allowed (falls to anyMessage: authenticated)

        System.out.println("connection still open after a denial: " + bobConnection.isOpen());
        System.out.println("total messages processed on this ONE connection: " + bobConnection.getProcessedCount());
    }
}
```

**How to run:** save as `WebSocketSecurityLevel3.java`, run `java WebSocketSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- bob's single connection, multiple messages over time ---
  [SUBSCRIBE /topic/public/news] ALLOWED -- connection stays OPEN
  [SUBSCRIBE /user/queue/notify] ALLOWED -- connection stays OPEN
  [SEND /app/admin/broadcast] DENIED -- connection stays OPEN, only this message refused
  [SEND /app/chat.send] ALLOWED -- connection stays OPEN
connection still open after a denial: true
connection still open after a denial: true
total messages processed on this ONE connection: 4
```

What changed: `WebSocketConnection.send` processes an ordered sequence of messages over what remains, throughout, a *single* connection — the third message is denied, but `stillOpen` remains `true` and the fourth message is still evaluated and allowed independently, demonstrating precisely why per-message authorization (not just a one-time connection-level check) matters: a single denied action doesn't have to mean the entire session ends.

## 6. Walkthrough

Trace bob's four-message sequence from Level 3 end to end.

**Step 1 — the connection is established** (an HTTP upgrade request, authenticated normally via the standard `SecurityFilterChain`, then a STOMP `CONNECT` frame) — this corresponds to `WebSocketConnection`'s construction with `principalAuthorities = {"ROLE_USER"}`, representing bob's already-established identity from that handshake.

**Step 2 — bob subscribes to a public topic:**
```
SUBSCRIBE
destination: /topic/public/news
```
`manager.authorize(...)` checks rules in order: the first rule, `simpDestMatchers("/topic/public/**", "permitAll")`, matches this destination — its requirement is `"permitAll"`, which always returns `true` regardless of authentication state. Allowed.

**Step 3 — bob subscribes to his own private queue:**
```
SUBSCRIBE
destination: /user/queue/notify
```
The first rule doesn't match this destination; the second, `simpSubscribeDestMatchers("/user/queue/**", "authenticated")`, matches (both the `SUBSCRIBE` type and the destination pattern) — its requirement, `"authenticated"`, checks `!principalAuthorities.isEmpty()`, which is `true` for bob. Allowed.

**Step 4 — bob attempts to send to an admin-only destination:**
```
SEND
destination: /app/admin/broadcast
```
Rules one and two don't match (destination pattern and message type respectively); the third rule, `simpDestMatchers("/app/admin/**", "ROLE_ADMIN")`, matches the destination — its requirement is the specific authority `"ROLE_ADMIN"`, which bob's `{"ROLE_USER"}` does not contain. **Denied** — but critically, `WebSocketConnection.send` only logs the denial; it never sets `stillOpen = false`.

**Step 5 — bob sends an ordinary chat message on the same, still-open connection:**
```
SEND
destination: /app/chat.send
```
No prior rule matches; the catch-all `anyMessage("authenticated")` applies — bob is authenticated, so this is allowed, proving the connection genuinely survived the prior denial and continues normal operation.

```
ONE WebSocket connection, bob (ROLE_USER):
   msg 1: SUBSCRIBE /topic/public/news   -> rule 1 (permitAll)                  -> ALLOWED
   msg 2: SUBSCRIBE /user/queue/notify   -> rule 2 (authenticated)              -> ALLOWED
   msg 3: SEND /app/admin/broadcast      -> rule 3 (ROLE_ADMIN, bob lacks it)   -> DENIED (connection OPEN)
   msg 4: SEND /app/chat.send            -> catch-all (authenticated)          -> ALLOWED
```

## 7. Gotchas & takeaways

> **Gotcha:** a `SUBSCRIBE`-only rule (`simpSubscribeDestMatchers`) does not restrict `SEND` operations to the same destination pattern, and vice versa — a common misconfiguration is guarding a sensitive topic's subscription while forgetting that clients might also be able to `SEND` to that same destination path unless a separate `simpDestMatchers` rule (which applies more broadly) also covers it. Always be explicit about which message types a given destination pattern actually needs to restrict.

- Because a WebSocket connection is long-lived, authorization must happen per message (per `SUBSCRIBE`, per `SEND`), not just once at connection time — a successfully-established connection does not imply blanket authorization for everything sent over it afterward.
- `simpDestMatchers` applies broadly across message types touching a destination; `simpSubscribeDestMatchers` applies specifically to subscription requests — using the wrong one is a common source of read/write authorization gaps.
- A denied message does not close the underlying connection by default — only that specific message is refused, and subsequent messages continue to be evaluated independently against the same rule set.
- Rules are evaluated in the order they're declared, first match wins — exactly the same evaluation model as `authorizeHttpRequests`/`authorizeExchange` from earlier cards, just applied to STOMP messages instead of HTTP requests.
- The principal used for every per-message check traces back to whatever was established during the original HTTP-upgrade handshake and `CONNECT` frame — WebSocket security doesn't re-authenticate on every message, it re-*authorizes* against the same, already-established identity.
