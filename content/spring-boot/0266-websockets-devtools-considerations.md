---
card: spring-boot
gi: 266
slug: websockets-devtools-considerations
title: WebSockets DevTools considerations
---

## 1. What it is

When your Spring Boot application uses **WebSockets** alongside **DevTools**, there are several important interactions to be aware of:

1. **DevTools' own LiveReload uses WebSockets** on port 35729. This is separate from your application WebSocket endpoint, but both coexist in the same process.
2. **DevTools restart drops all active WebSocket connections** — since the application context is recreated, all `WebSocketSession` objects are closed. Connected browser clients see `onclose` events.
3. **SockJS / STOMP clients may reconnect automatically** — Spring's STOMP-over-SockJS client has built-in reconnection logic; raw `WebSocket` clients do not.
4. **During active WebSocket sessions, DevTools restart can appear to hang** — the restart waits for Tomcat to close, but WebSocket connections hold Tomcat threads. DevTools has a quiet period that normally handles this, but a stalled long-lived WebSocket can delay restart.

## 2. Why & when

You encounter these issues when:
- Building a real-time feature (chat, live notifications, collaborative editing) and also using DevTools for fast iteration.
- Adding WebSocket integration to an existing DevTools-enabled app.
- Debugging why the browser's WebSocket connection drops every time you save a Java file.

Understanding the interaction helps you configure DevTools and your WebSocket client to work together smoothly during development, while knowing what to expect at restart time.

## 3. Core concept

A Spring Boot DevTools restart is *not* a JVM restart — it recreates the Spring `ApplicationContext`. But from a WebSocket perspective:

- The embedded Tomcat (or Netty/Undertow) is stopped and restarted.
- All WebSocket upgrade connections are severed when Tomcat stops.
- The `WebSocketSession.close()` callback fires on the server side.
- The browser WebSocket's `onclose` event fires on the client side.

For **STOMP over SockJS** (`@MessageMapping`, `SimpMessagingTemplate`):
- Spring's `WebSocketStompClient` has reconnect logic built in.
- SockJS clients automatically reconnect after a few seconds.
- Subscriptions must be re-established after reconnect.

For **raw WebSocket** (`@ServerEndpoint` or `WebSocketHandler`):
- The browser's native `WebSocket` does not auto-reconnect.
- The client must implement reconnection manually.

The **LiveReload WebSocket** (port 35729) is managed by DevTools separately — it also drops on restart but reconnects when the new server instance starts. The browser extension handles this transparently.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DevTools restart dropping WebSocket connections and SockJS auto-reconnect behavior">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>

  <!-- Timeline -->
  <line x1="30" y1="120" x2="670" y2="120" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Connected -->
  <circle cx="80" cy="120" r="6" fill="#6db33f"/>
  <text x="80" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">WS open</text>

  <!-- Restart -->
  <circle cx="250" cy="120" r="8" fill="#ff7b72"/>
  <text x="250" y="105" fill="#ff7b72" font-size="11" text-anchor="middle" font-family="sans-serif">DevTools restart</text>
  <text x="250" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Tomcat stops</text>

  <!-- Connection drop -->
  <line x1="250" y1="135" x2="250" y2="165" stroke="#ff7b72" stroke-width="2"/>
  <text x="250" y="178" fill="#ff7b72" font-size="9" text-anchor="middle" font-family="sans-serif">onclose fires</text>

  <!-- Context recreated -->
  <rect x="250" y="125" width="130" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">context restart (~1s)</text>

  <!-- SockJS reconnect -->
  <circle cx="400" cy="120" r="6" fill="#79c0ff"/>
  <text x="400" y="105" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Tomcat up</text>

  <!-- Auto-reconnect arrow -->
  <line x1="420" y1="175" x2="500" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="460" y="190" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SockJS auto-reconnects</text>

  <circle cx="530" cy="120" r="6" fill="#6db33f"/>
  <text x="530" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">WS restored</text>

  <!-- Raw WS note -->
  <text x="580" y="170" fill="#ff7b72" font-size="9" text-anchor="middle" font-family="sans-serif">Raw WebSocket:</text>
  <text x="580" y="185" fill="#ff7b72" font-size="9" text-anchor="middle" font-family="sans-serif">no auto-reconnect</text>
  <text x="580" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(manual logic needed)</text>
</svg>

DevTools restart severs all WebSocket connections; SockJS clients reconnect automatically, raw WebSocket clients must reconnect manually.

## 5. Runnable example

```java
// WebSocketDevToolsDemo.java — run with: java WebSocketDevToolsDemo.java
// Demonstrates key configuration and client-side patterns for handling
// WebSocket connections alongside DevTools automatic restart.

public class WebSocketDevToolsDemo {

    public static void main(String[] args) {
        System.out.println("=== WebSockets + DevTools Considerations ===\n");
        printServerConfig();
        printClientPatterns();
        printDevToolsConfig();
        printTroubleshooting();
    }

    static void printServerConfig() {
        System.out.println("--- Spring WebSocket server config (normal, no changes for DevTools) ---");
        System.out.println("""
            @Configuration
            @EnableWebSocketMessageBroker
            public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

                @Override
                public void registerStompEndpoints(StompEndpointRegistry registry) {
                    registry.addEndpoint("/ws")
                            .withSockJS();   // SockJS fallback — auto-reconnects on restart
                }

                @Override
                public void configureMessageBroker(MessageBrokerRegistry registry) {
                    registry.enableSimpleBroker("/topic", "/queue");
                    registry.setApplicationDestinationPrefixes("/app");
                }
            }
            """);
    }

    static void printClientPatterns() {
        System.out.println("--- JavaScript client patterns ---\n");

        System.out.println("  Pattern 1: SockJS + STOMP (auto-reconnects after DevTools restart)");
        System.out.println("""
            const socket  = new SockJS('/ws');   // SockJS endpoint
            const stomp   = Stomp.over(socket);
            let connected = false;

            function connect() {
                stomp.connect({}, (frame) => {
                    connected = true;
                    console.log('Connected:', frame);
                    stomp.subscribe('/topic/updates', (msg) => {
                        console.log('Update:', msg.body);
                    });
                }, (error) => {
                    connected = false;
                    console.log('Disconnected, retrying in 5s...');
                    setTimeout(connect, 5000);  // manual reconnect for STOMP error
                });
            }
            connect();
            // SockJS transparently handles the connection drop from DevTools restart.
            """);

        System.out.println("  Pattern 2: Raw WebSocket with manual reconnect");
        System.out.println("""
            function connect() {
                const ws = new WebSocket('ws://localhost:8080/raw-ws');

                ws.onopen  = () => console.log('WebSocket open');
                ws.onmessage = (e) => console.log('Message:', e.data);
                ws.onerror = (e) => console.error('Error:', e);

                // REQUIRED with DevTools: raw WebSocket does not auto-reconnect
                ws.onclose = (e) => {
                    console.log('Closed (DevTools restart?), reconnecting in 2s...');
                    setTimeout(connect, 2000);
                };
            }
            connect();
            """);
    }

    static void printDevToolsConfig() {
        System.out.println("--- DevTools config to reduce WebSocket disruption ---");
        System.out.println("""
            # application.properties (DevTools settings)

            # Slow down restart detection — gives in-flight WS messages time to settle:
            spring.devtools.restart.quiet-period=1s

            # Use trigger file so restart only happens when YOU decide:
            spring.devtools.restart.trigger-file=.restart
            # (touch .restart to trigger restart manually)

            # Exclude paths that don't affect WS behavior from triggering restart:
            spring.devtools.restart.exclude=static/**,templates/**,public/**
            """);
    }

    static void printTroubleshooting() {
        System.out.println("--- Troubleshooting ---");
        String[][] issues = {
            {
                "Restart appears to hang (never completes)",
                "A WebSocket connection is holding a Tomcat thread. Increase quiet-period,\n"
                + "    or check if a client is sending continuous messages. Also check\n"
                + "    spring.lifecycle.timeout-per-shutdown-phase (increase to 10s during dev)."
            },
            {
                "LiveReload not firing after WebSocket code change",
                "LiveReload fires after DevTools restart completes. If restart hangs (see above),\n"
                + "    LiveReload also stalls. Fix the restart hang first."
            },
            {
                "SockJS subscription lost after restart",
                "SockJS reconnects the transport layer but doesn't re-send SUBSCRIBE frames.\n"
                + "    In the STOMP connect callback, always re-subscribe — don't assume subs persist."
            },
            {
                "Port 35729 conflicts with custom WebSocket server",
                "Change LiveReload port: spring.devtools.livereload.port=35730"
            },
        };
        for (var issue : issues) {
            System.out.printf("  PROBLEM : %s%n  FIX     : %s%n%n", issue[0], issue[1]);
        }
    }
}
```

**How to run:** `java WebSocketDevToolsDemo.java`

## 6. Walkthrough

- **SockJS auto-reconnect** — SockJS is a JavaScript library that wraps WebSocket with fallback transports (long-polling, SSE). When the underlying connection closes, SockJS automatically tries to reconnect. This is why `registry.addEndpoint("/ws").withSockJS()` is recommended for apps that use DevTools — the client recovers from DevTools restarts transparently.
- **STOMP `onerror` callback** — even with SockJS, STOMP-level disconnects (session timeout, server-side close) require a manual reconnect in the `onerror`/`onclose` handler. The pattern in `connect()` uses `setTimeout(connect, 5000)` — production apps should add backoff (2s, 4s, 8s, ...) to avoid hammering a recovering server.
- **Raw WebSocket `onclose`** — browsers close raw WebSockets without reconnecting. Every raw WebSocket implementation needs an `onclose` handler that schedules a reconnect. DevTools restarts trigger this close every time you save a Java file.
- **`trigger-file`** — the most productive setting when developing real-time features. Without it, every Java file save triggers a restart (and a WebSocket drop). With it, you control restarts explicitly, so you can make several changes and then restart once — reducing client disconnects to once per logical change instead of once per file.
- **Shutdown timeout** — `spring.lifecycle.timeout-per-shutdown-phase` during development should be short (5 s) so DevTools restarts quickly. Long-lived WebSocket connections that don't close themselves will cause the restart to wait until this timeout.

## 7. Gotchas & takeaways

> **WebSocket sessions are not migrated across DevTools restarts.** Any session state stored in `WebSocketSession.getAttributes()` or `simpSessionAttributes` is lost on restart. If you're developing stateful chat or game features, use `trigger-file` to restart only when you choose — not on every edit.

> **The Security context is re-evaluated after a restart.** If your WebSocket endpoint uses `@PreAuthorize` or Spring Security's WebSocket CSRF protection, the client may need to re-authenticate after a DevTools restart — this is normal. In development, consider relaxing WebSocket CSRF (`.csrf().disable()` in the WS config) to avoid authentication friction during rapid iteration.

- Use `.withSockJS()` on your endpoint during development — it makes your life easier when DevTools restarts.
- Always re-subscribe to STOMP destinations in the `connect()` callback, not just on first connection.
- `spring.devtools.restart.trigger-file=.restart` is your best friend when developing real-time features.
- Port 35729 (LiveReload) and your app's WebSocket port are independent — they don't conflict.
- In production, WebSocket connections don't encounter DevTools issues (DevTools is disabled); these are development-only concerns.
