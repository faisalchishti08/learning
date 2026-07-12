---
card: spring-session
gi: 19
slug: websocket-integration
title: "WebSocket integration"
---

## 1. What it is

Spring Session's WebSocket integration keeps a WebSocket connection's associated `HttpSession` alive in the shared store for as long as the WebSocket connection itself is open, even past the point where the session would normally expire from HTTP inactivity — via `SessionRepositoryMessageInterceptor`, registered on the STOMP/WebSocket message channel.

## 2. Why & when

A WebSocket connection, once established, can stay open and actively used for a long time with no ordinary HTTP requests happening at all — a chat application, a live dashboard, a collaborative editor. Without special handling, the `HttpSession` that was used to authenticate the WebSocket handshake would simply expire from inactivity (card 0007) after `maxInactiveInterval`, since nothing about an open WebSocket connection touches the session the normal HTTP way. If that session expires while the socket is still actively being used, subsequent security checks or session-dependent logic tied to that session silently break, even though the user is very much still actively engaged.

Reach for WebSocket session integration when:

- Building any WebSocket-based feature (chat, live notifications, collaborative editing, real-time dashboards) in an application that also relies on `HttpSession` for authentication or per-user state — the socket needs to keep that session alive for its own duration.
- Debugging "WebSocket messages start failing after N minutes" — a very common symptom of the underlying `HttpSession` expiring mid-connection because nothing was refreshing it.
- Deciding whether this integration is needed at all — a WebSocket implementation using an entirely separate, socket-specific authentication mechanism (not tied to `HttpSession`) doesn't need this integration.

## 3. Core concept

Think of an `HttpSession`'s normal expiration as a parking meter that resets every time a coin (an HTTP request) is inserted — no coins for 30 minutes, and the meter expires, regardless of what's happening. A WebSocket connection is like someone parked at that meter who's still actively there the whole time, just not physically walking up to insert new coins — they're using the space continuously, but the meter has no way to know that on its own. Spring Session's WebSocket integration is the attendant who notices the car is still occupied and actively used, and manually keeps feeding the meter on its owner's behalf for as long as the car remains there — so the session doesn't expire out from under an actively-used connection.

```java
@Configuration
public class WebSocketSessionConfig extends AbstractSessionWebSocketMessageBrokerConfigurer<Session> {
    // Registers SessionRepositoryMessageInterceptor, which touches (refreshes)
    // the HttpSession associated with a STOMP session on every inbound message.
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every WebSocket message passing through the interceptor refreshes the associated HttpSession's expiration timer">
  <rect x="20" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">WebSocket client</text>

  <rect x="240" y="90" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SessionRepository</text>
  <text x="340" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MessageInterceptor</text>

  <rect x="510" y="90" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="580" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HttpSession</text>
  <text x="580" y="128" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">TTL refreshed</text>

  <line x1="170" y1="115" x2="235" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">message</text>
  <line x1="440" y1="115" x2="505" y2="115" stroke="#3fb950" stroke-width="1.5"/>
</svg>

Even a heartbeat-only message (no application-meaningful content) is enough to trigger this refresh, since the interceptor runs on every inbound message regardless of type.

## 5. Runnable example

The scenario: enabling WebSocket session refresh for a chat application, growing to observe the refresh happening on a real, long-running connection, and finally to handle the case of an idle WebSocket connection (open but genuinely inactive) where refreshing the session on every message isn't enough by itself.

### Level 1 — Basic

```java
// WebSocketSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.session.Session;
import org.springframework.session.web.socket.config.annotation.AbstractSessionWebSocketMessageBrokerConfigurer;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;

@Configuration
public class WebSocketSessionConfig extends AbstractSessionWebSocketMessageBrokerConfigurer<Session> {

    @Override
    protected void configureStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/chat").withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic");
        registry.setApplicationDestinationPrefixes("/app");
    }
}
```

**How to run:** add this alongside any Spring Session store configuration in a Spring Boot app with `spring-boot-starter-websocket`. Connect a WebSocket client to `/chat`, and send periodic messages over a duration longer than the configured `maxInactiveInterval` (temporarily shortened to, say, 60 seconds for testing). Expected behavior: unlike a plain HTTP-only session that would expire at 60 seconds of no requests, this session remains valid for as long as the WebSocket connection keeps sending messages — each message refreshes it.

### Level 2 — Intermediate

Making the refresh behavior directly observable helps confirm it's actually working, rather than trusting it blindly — logging the session's expiry timestamp before and after each message shows the refresh happening in real time.

```java
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.stereotype.Component;

import java.time.Instant;

@Component
public class SessionRefreshObserver implements ChannelInterceptor {

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor = StompHeaderAccessor.wrap(message);
        Object httpSession = accessor.getSessionAttributes() != null
                ? accessor.getSessionAttributes().get("HTTP_SESSION_ID_ATTR_NAME")
                : null;

        System.out.printf("[%s] WebSocket message received; associated HttpSession refresh triggered%n",
                Instant.now());
        return message; // pass through unchanged — this interceptor only observes
    }
}
```

**How to run:** register this as an additional channel interceptor alongside `SessionRepositoryMessageInterceptor`, then send several WebSocket messages spaced a few seconds apart while separately polling the session's TTL directly (e.g. `redis-cli TTL` for a Redis-backed store, card 0009). Expected observation: the TTL resets to the full `maxInactiveInterval` value after each message, visibly confirming the refresh mechanism is genuinely extending the session's life on every inbound message, not just at connection establishment.

What changed: the refresh behavior — normally invisible — becomes directly observable, useful both for building confidence the integration is correctly configured and for diagnosing it if session expiration issues persist despite an active WebSocket connection.

### Level 3 — Advanced

A WebSocket connection that's open but genuinely idle (no messages flowing either direction for an extended period — the user has the tab open but isn't actively chatting) doesn't trigger any refresh either, since the refresh mechanism only fires on actual inbound messages. Production systems typically pair this with a periodic heartbeat/ping message specifically to keep the session alive during genuine idle periods where the user is still present but not actively sending real content.

```java
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class WebSocketHeartbeat {

    private final SimpMessagingTemplate messagingTemplate;
    private final Set<String> connectedSessionDestinations = ConcurrentHashMap.newKeySet();

    public WebSocketHeartbeat(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    public void registerConnection(String userDestination) {
        connectedSessionDestinations.add(userDestination);
    }

    public void unregisterConnection(String userDestination) {
        connectedSessionDestinations.remove(userDestination);
    }

    @Scheduled(fixedRate = 300_000) // every 5 minutes, well inside a typical 30-minute session timeout
    public void sendHeartbeats() {
        for (String destination : connectedSessionDestinations) {
            // Sending any message — even a trivial ping — through the message channel
            // triggers SessionRepositoryMessageInterceptor's refresh for that connection's
            // associated HttpSession, keeping it alive through genuinely idle periods.
            messagingTemplate.convertAndSend(destination, Map.of("type", "heartbeat"));
        }
    }
}
```

**How to run:** register connections on WebSocket connect events and unregister on disconnect, enable `@EnableScheduling`, then open a chat connection and deliberately send no application messages for longer than `maxInactiveInterval`. Expected behavior: without the heartbeat, the underlying `HttpSession` would expire despite the socket remaining technically open; with it, the periodic heartbeat message flowing through the channel keeps triggering the refresh, and the session — and therefore the connection's continued validity for anything session-dependent — survives the idle period.

What changed and why it's production-flavored: this closes the real gap between "the connection is technically open" and "the session is being actively refreshed" — a chat application where users often have the tab open in the background without actively typing needs this heartbeat to avoid a confusing failure mode where a long-idle-but-still-open connection silently loses its associated session and subsequent actions (like finally sending a message after a long pause) fail unexpectedly.

## 6. Walkthrough

Tracing session refresh across a WebSocket connection's lifetime, in execution order:

1. A user's browser establishes a WebSocket (STOMP-over-SockJS) connection to `/chat`, carrying the browser's existing `HttpSession` cookie as part of the handshake — the same session already established via normal HTTP login.
2. `SessionRepositoryMessageInterceptor`, registered via `AbstractSessionWebSocketMessageBrokerConfigurer` (Level 1), associates this specific WebSocket session with the underlying `HttpSession` for the duration of the connection.
3. As the user actively chats, each outbound message they send passes through the message channel; the interceptor's `preSend` hook fires on every one, calling into the `SessionRepository` to refresh (re-save, extending its expiry) the associated `HttpSession` — exactly mirroring what a normal HTTP request's end-of-request save (card 0004) would do.
4. If the user goes quiet — reading but not typing — no application messages flow, and without help, no refresh would occur; `WebSocketHeartbeat` (Level 3) periodically injects a lightweight message through the same channel specifically to keep triggering that refresh during this genuine idle period.
5. `SessionRefreshObserver` (Level 2) independently confirms, via direct inspection of the store's TTL, that each of these triggering events — whether real chat activity or a synthetic heartbeat — genuinely resets the session's expiration clock.
6. Should the WebSocket connection actually close (browser tab closed, network drop) without a clean disconnect event ever firing `unregisterConnection`, the heartbeat would (incorrectly) keep trying to send to a destination that no longer has a live connection — a reason `unregisterConnection` on disconnect events is essential, not merely tidy, for this mechanism to behave correctly at scale.

```
WebSocket connects -> HttpSession associated via SessionRepositoryMessageInterceptor
   |
active chat: each message -> preSend hook -> refresh HttpSession (extend TTL)
   |
idle period, no real messages -> WebSocketHeartbeat sends synthetic ping every 5min
   |                                    -> also passes through preSend hook -> refresh
   |
session TTL never lapses as long as connection stays open (real activity or heartbeat)
```

## 7. Gotchas & takeaways

> A WebSocket connection alone, without either real application traffic or an explicit heartbeat mechanism, does *not* automatically keep the associated `HttpSession` alive — the refresh only happens as a side effect of messages actually flowing through the interceptor-registered channel; an open-but-silent connection is functionally invisible to Spring Session's session-refresh mechanism, and its session will still expire on schedule.

- `maxInactiveInterval` should be considered in the context of expected WebSocket idle periods — a very short timeout combined with an infrequent heartbeat interval risks the session expiring in the gap between heartbeats; ensure the heartbeat interval is comfortably shorter than the timeout, not merely shorter in the average case.
- Disconnect handling (unregistering a connection from any heartbeat-sending mechanism) is essential — sending messages to a destination whose actual WebSocket connection has already closed wastes resources and, depending on implementation, can throw exceptions that need graceful handling rather than crashing the scheduled task for every other still-connected user.
- This integration keeps the `HttpSession` alive, which matters specifically for anything reading session-stored state (authentication, user preferences) during the WebSocket's own message handling — it doesn't, by itself, address separate concerns like WebSocket-specific authentication token expiration if the application uses a different mechanism for that.
- Testing this integration benefits enormously from a deliberately shortened `maxInactiveInterval` (seconds, not the default 30 minutes) — waiting out a real 30-minute window to verify refresh behavior during development is impractically slow.
- When debugging "WebSocket messages fail after some time in production but work fine in quick manual testing," suspect this exact mechanism first — quick manual tests rarely leave a connection idle long enough to hit the expiration window that only becomes visible after sustained, mostly-idle real-world usage.
