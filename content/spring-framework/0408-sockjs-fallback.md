---
card: spring-framework
gi: 408
slug: sockjs-fallback
title: "SockJS fallback"
---

## 1. What it is

SockJS is a browser-JavaScript library and matching server-side protocol that emulates a WebSocket connection using whatever transport actually works in a given environment — a real WebSocket when available, and one of several HTTP-based fallbacks (like long-polling or streaming XHR) when it isn't. Spring's WebSocket support integrates SockJS on the server side with one extra call, `.withSockJS()`, on the endpoint registration.

```java
@Override
public void registerStompEndpoints(StompEndpointRegistry registry) {
    registry.addEndpoint("/ws-chat").withSockJS(); // adds automatic fallback support
}
```

## 2. Why & when

WebSocket is broadly supported today, but real deployments still hit environments where a WebSocket connection can't be established: a restrictive corporate proxy that only allows plain HTTP, an older browser, or a load balancer/reverse proxy in front of the application that isn't configured to pass WebSocket upgrade headers through. Without a fallback, those clients simply can't use your real-time feature at all. SockJS exists to make that failure invisible to your application code — the client library automatically tries a real WebSocket first, and transparently downgrades to an HTTP-based transport if that fails, while your server-side `@MessageMapping`/`SimpMessagingTemplate` code stays exactly the same either way.

Add SockJS support when:

- You're building a public-facing feature and can't fully control or predict every client's network environment (corporate proxies, older infrastructure).
- You want graceful degradation instead of a hard failure for the subset of clients where WebSocket doesn't work, at the cost of slightly higher latency for those specific clients on a fallback transport.

Skip it for internal tools or environments you fully control, where you know WebSocket works end-to-end (e.g., a known modern browser hitting a properly configured load balancer) — SockJS adds a small amount of protocol overhead and infrastructure requirements (session affinity, as covered below) that aren't worth it if you don't need the fallback.

## 3. Core concept

```
 Client (SockJS JS library)
        |
        v
  Try: real WebSocket connection
        |
   succeeds? -----------------------------> yes -> use it directly
        |
        no (blocked by proxy, old browser, etc.)
        |
        v
  Try: HTTP streaming (XHR streaming)
        |
   succeeds? -----------------------------> yes -> use it, framed as SockJS "sessions"
        |
        no
        |
        v
  Fall back: HTTP long-polling
        (works almost everywhere plain HTTP works)
```

From the server's perspective, all of this negotiation happens inside the `.withSockJS()`-configured endpoint — your `@MessageMapping` handlers and `SimpMessagingTemplate` calls never need to know which underlying transport a given client actually ended up using.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SockJS negotiates the best available transport, falling back from WebSocket to HTTP streaming to long-polling">
  <rect x="10" y="70" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SockJS client</text>

  <rect x="240" y="10" width="160" height="42" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="36" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. WebSocket (best)</text>

  <rect x="240" y="80" width="160" height="42" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="106" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. HTTP streaming</text>

  <rect x="240" y="150" width="160" height="42" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="176" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. HTTP long-polling</text>

  <rect x="470" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Same server endpoint</text>

  <line x1="150" y1="90" x2="235" y2="30" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="150" y1="95" x2="235" y2="100" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="150" y1="100" x2="235" y2="165" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="400" y1="30" x2="465" y2="85" stroke="#8b949e" stroke-width="1"/>
  <line x1="400" y1="100" x2="465" y2="98" stroke="#8b949e" stroke-width="1"/>
  <line x1="400" y1="170" x2="465" y2="110" stroke="#8b949e" stroke-width="1"/>
</svg>

Whichever transport wins the negotiation, the server sees traffic through the same registered endpoint.

## 5. Runnable example

### Level 1 — Basic

Register a STOMP endpoint with SockJS enabled, and inspect the extra HTTP endpoints SockJS adds — visible by calling the SockJS "info" endpoint, which the client library uses to decide what transports are viable before connecting.

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.*;

public class SockJsBasic {

    @Configuration
    @EnableWebSocketMessageBroker
    static class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
        @Override
        public void configureMessageBroker(MessageBrokerRegistry registry) {
            registry.enableSimpleBroker("/topic");
            registry.setApplicationDestinationPrefixes("/app");
        }

        @Override
        public void registerStompEndpoints(StompEndpointRegistry registry) {
            registry.addEndpoint("/ws-chat").withSockJS();
            // Without SockJS, this line would just be:
            //   registry.addEndpoint("/ws-chat");
            // and clients without WebSocket support would simply fail to connect.
        }
    }
}
```

How to run: run inside a Spring Boot web application (`spring-boot-starter-websocket`), then `curl http://localhost:8080/ws-chat/info` and observe a JSON response like `{"entropy":...,"origins":["*:*"],"cookie_needed":true,"websocket":true}` — this `/info` endpoint exists purely because `.withSockJS()` was added.

`.withSockJS()` registers several additional HTTP endpoints under `/ws-chat/**` (an `/info` endpoint, and per-session-transport endpoints for streaming/polling) alongside the original raw WebSocket endpoint — the SockJS JavaScript client queries `/info` first to learn what the server supports before choosing a transport.

### Level 2 — Intermediate

Configure SockJS-specific tuning (heartbeat interval, disabled transports) relevant to production behavior, and add a client-side connection example showing the automatic fallback negotiation from the browser's perspective.

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.*;

public class SockJsIntermediate {

    @Configuration
    @EnableWebSocketMessageBroker
    static class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
        @Override
        public void configureMessageBroker(MessageBrokerRegistry registry) {
            registry.enableSimpleBroker("/topic");
            registry.setApplicationDestinationPrefixes("/app");
        }

        @Override
        public void registerStompEndpoints(StompEndpointRegistry registry) {
            registry.addEndpoint("/ws-chat")
                    .withSockJS()
                    .setHeartbeatTime(25_000)       // ping every 25s to detect dead connections
                    .setDisconnectDelay(5_000)       // grace period before declaring a session gone
                    .setStreamBytesLimit(128 * 1024); // rotate streaming transport after 128KB
        }
    }
}
```

```javascript
// Client side (browser), for reference — not part of the Java example above:
import SockJS from 'sockjs-client';
import { Client } from '@stomp/stompjs';

const stompClient = new Client({
  webSocketFactory: () => new SockJS('/ws-chat'), // SockJS negotiates the transport automatically
  onConnect: () => {
    stompClient.subscribe('/topic/messages', (msg) => console.log(JSON.parse(msg.body)));
    stompClient.publish({ destination: '/app/chat.send', body: JSON.stringify({ text: 'hi' }) });
  },
});
stompClient.activate();
```

How to run: run the server config inside a Spring Boot web application, and load the client snippet in a browser page bundled with `sockjs-client` and `@stomp/stompjs`.

`setHeartbeatTime(25_000)` configures how often SockJS pings an idle connection to detect a dead session — important because HTTP-based fallback transports (unlike real WebSocket) don't have TCP-level keep-alive semantics that reveal a dropped connection quickly. `setStreamBytesLimit` forces the streaming HTTP transport to periodically close and reopen the underlying request, working around browsers and proxies that buffer indefinitely-long HTTP responses and would otherwise never deliver data to the client in a timely way.

### Level 3 — Advanced

Production deployments behind a load balancer need **session affinity** (sticky sessions) for SockJS's HTTP-based fallback transports, since a client's long-polling or streaming "session" is a sequence of separate HTTP requests that must all reach the *same* server instance holding that session's state — unlike a single long-lived WebSocket connection, which only ever needs one server. This configuration shows the CORS and origin restrictions relevant to a real deployment, plus a custom `TaskScheduler` for the SockJS heartbeat.

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.web.socket.config.annotation.*;

public class SockJsAdvanced {

    @Configuration
    @EnableWebSocketMessageBroker
    static class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
        @Override
        public void configureMessageBroker(MessageBrokerRegistry registry) {
            registry.enableSimpleBroker("/topic")
                    .setHeartbeatValue(new long[]{10_000, 10_000})
                    .setTaskScheduler(heartbeatScheduler());
            registry.setApplicationDestinationPrefixes("/app");
        }

        @Override
        public void registerStompEndpoints(StompEndpointRegistry registry) {
            registry.addEndpoint("/ws-chat")
                    .setAllowedOriginPatterns("https://app.example.com") // restrict cross-origin access
                    .withSockJS()
                    .setSessionCookieNeeded(true); // needed so a load balancer can route by session cookie
        }

        @Bean
        TaskScheduler heartbeatScheduler() {
            var scheduler = new ThreadPoolTaskScheduler();
            scheduler.setPoolSize(1);
            scheduler.setThreadNamePrefix("stomp-heartbeat-");
            scheduler.initialize();
            return scheduler;
        }
    }
}
```

How to run: run inside a Spring Boot web application deployed behind a load balancer configured for session-cookie-based sticky routing (e.g., an AWS ALB with an application-controlled cookie, or nginx with `ip_hash`/cookie affinity).

`setAllowedOriginPatterns(...)` restricts which browser origins may open a SockJS/WebSocket connection at all — critical for a public endpoint, since without it any website could open a connection to your WebSocket endpoint from a user's browser. `setSessionCookieNeeded(true)` ensures SockJS sets a cookie identifying the session, which a properly configured load balancer can use to route every subsequent HTTP request from that SockJS session (for long-polling/streaming) back to the *same* application instance — without this affinity, a long-polling client's second request could land on a different instance that knows nothing about its session, breaking the connection.

## 6. Walkthrough

Trace a client connecting through `SockJsAdvanced`'s configuration when WebSocket is blocked by a corporate proxy:

1. **Info request.** The browser's SockJS client first issues `GET /ws-chat/info` to discover server capabilities and get an initial session cookie (because `setSessionCookieNeeded(true)` is set).
2. **WebSocket attempt fails.** The client tries to open a real WebSocket to `/ws-chat/<server-id>/<session-id>/websocket`; the corporate proxy blocks the `Upgrade: websocket` header, and the connection attempt fails or times out.
3. **Fallback to streaming.** SockJS's client-side negotiation logic automatically tries the next transport: an HTTP streaming request to `/ws-chat/<server-id>/<session-id>/xhr_streaming`. This request stays open, with the server writing STOMP frames as they occur, framed as SockJS messages.
4. **Load balancer routing.** Because the earlier `/info` response set a session cookie, the load balancer's sticky-session configuration routes this (and every subsequent) request for the same SockJS session to the *same* application instance that's holding the STOMP session state — critical, since a different instance would have no idea this session or its subscriptions exist.
5. **Byte limit rotation.** Once the streaming response accumulates a configured number of bytes (SockJS's default, or a custom `setStreamBytesLimit` if configured), the server closes that HTTP response and the client immediately opens a new one — working around proxies/browsers that buffer an indefinitely-long response and never actually deliver bytes to the application layer.
6. **Heartbeat.** Every 10 seconds (per `setHeartbeatValue(new long[]{10_000, 10_000})`), the STOMP layer sends a heartbeat frame over whichever transport is active, scheduled by the dedicated `stomp-heartbeat-` thread pool — this lets both sides detect a dead connection promptly even on a fallback transport that lacks WebSocket's own low-level keep-alive.
7. **Message flow unaffected.** From here, `@MessageMapping`/`SimpMessagingTemplate` code on the server, and `subscribe`/`publish` calls on the client, behave identically to the pure-WebSocket case from the STOMP card — the only difference is the underlying transport carrying the STOMP frames.

```
GET /ws-chat/info               -> session cookie set
WebSocket upgrade attempt       -> blocked by proxy
GET /ws-chat/.../xhr_streaming  -> load balancer routes via session cookie to correct instance
   (long-lived HTTP response carrying STOMP frames, rotated at byte limit)
heartbeat every 10s             -> keeps session alive, detects drops
STOMP SEND/SUBSCRIBE/MESSAGE    -> identical application-level behavior to raw WebSocket
```

## 7. Gotchas & takeaways

> Gotcha: deploying a SockJS-enabled endpoint behind a load balancer *without* configuring session affinity (sticky sessions) is a common production failure mode — everything works perfectly in local testing (one server instance, so every request naturally lands on the same place) and then breaks intermittently in production once traffic is spread across multiple instances, because a fallback transport's second HTTP request can land on an instance that has never heard of that session.

- SockJS makes WebSocket-unfriendly network environments transparent to your application code — the negotiation (WebSocket, then HTTP streaming, then long-polling) happens entirely client-side, with server-side `@MessageMapping` code unchanged.
- Enable it (`.withSockJS()`) for public-facing features with unpredictable client environments; skip it for internal tools where you control the network path end-to-end.
- HTTP-based fallback transports require session affinity at the load balancer — plan for sticky sessions (session-cookie-based routing) before deploying a SockJS endpoint behind more than one instance.
- Restrict allowed origins (`setAllowedOriginPatterns`) on any public SockJS/WebSocket endpoint — without it, any website can open a connection from a visiting user's browser.
