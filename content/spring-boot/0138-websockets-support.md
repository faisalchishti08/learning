---
card: spring-boot
gi: 138
slug: websockets-support
title: WebSockets support
---

## 1. What it is

**WebSockets** provide full-duplex communication over a single, persistent TCP connection. Unlike HTTP (request → response → close), a WebSocket stays open and either side can send data at any time. Spring Boot auto-configures WebSocket support on top of Spring's `@EnableWebSocket` (low-level) or Spring's STOMP/SockJS messaging layer (high-level). For Spring MVC apps, `spring-boot-starter-websocket` is the starter. WebFlux supports WebSockets natively via `WebSocketHandler`.

## 2. Why & when

Use WebSockets for real-time, bidirectional communication where polling is too slow or wasteful:

- **Chat applications** — messages pushed from server to all participants instantly.
- **Live dashboards** — metrics, prices, or scores streamed continuously.
- **Collaborative tools** — shared editors, whiteboards.
- **Gaming** — low-latency game state synchronisation.

For one-way server push (notifications, event feeds) without the overhead of full duplex, **Server-Sent Events (SSE)** is simpler. WebSockets are best when the *client* also needs to push data to the server frequently.

## 3. Core concept

**Two layers in Spring:**

1. **Low-level WebSocket API** — `WebSocketHandler` interface, `TextMessage`, `BinaryMessage`. Full control, but you manage the protocol yourself.

2. **STOMP over WebSocket** — `@EnableWebSocketMessageBroker` adds a STOMP sub-protocol (Simple Text Oriented Messaging Protocol). You get message routing, pub/sub topics, and integration with Spring's `@MessageMapping` and `@SendTo` — much like `@RequestMapping` for HTTP.

**SockJS** is a fallback layer that emulates WebSockets over HTTP long-polling when the browser or network doesn't support WebSockets natively. Typically enabled alongside STOMP.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="108" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Browser Client</text>
  <text x="85" y="125" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">SockJS / WS</text>
  <rect x="230" y="60" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="317" y="88" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">STOMP Broker</text>
  <rect x="230" y="130" width="175" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="317" y="155" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">@MessageMapping</text>
  <text x="317" y="171" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">@SendTo topic</text>
  <rect x="480" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">All Subscribers</text>
  <text x="565" y="125" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">/topic/chat</text>
  <line x1="152" y1="110" x2="226" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ws)"/>
  <line x1="152" y1="110" x2="226" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#ws2)"/>
  <line x1="407" y1="85" x2="476" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ws3)"/>
  <text x="440" y="82" fill="#8b949e" font-size="10" font-family="sans-serif">broadcast</text>
  <defs>
    <marker id="ws" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ws2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ws3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Browser connects via WebSocket/SockJS; STOMP broker routes `@MessageMapping` to handler; result broadcast to `/topic/chat` subscribers.

## 5. Runnable example

```java
// WebSocketApp.java  —  Spring Boot project with spring-boot-starter-websocket
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.stereotype.Controller;
import org.springframework.web.socket.config.annotation.*;

@SpringBootApplication
public class WebSocketApp {
    public static void main(String[] args) {
        SpringApplication.run(WebSocketApp.class, args);
    }
}

// STOMP WebSocket configuration
@Configuration
@EnableWebSocketMessageBroker
class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // WebSocket endpoint — clients connect here
        registry.addEndpoint("/ws").withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // In-memory broker for topic subscriptions
        registry.enableSimpleBroker("/topic");
        // Prefix for messages handled by @MessageMapping
        registry.setApplicationDestinationPrefixes("/app");
    }
}

// Message classes
record ChatMessage(String sender, String content) {}
record OutputMessage(String sender, String content, String time) {}

// Message handler
@Controller
class ChatController {

    @MessageMapping("/chat")           // clients send to /app/chat
    @SendTo("/topic/messages")         // broadcast to all /topic/messages subscribers
    public OutputMessage handleChat(ChatMessage message) throws InterruptedException {
        Thread.sleep(100); // simulate processing
        return new OutputMessage(
                message.sender(),
                message.content(),
                java.time.LocalTime.now().toString()
        );
    }
}
```

**How to run:** add `spring-boot-starter-websocket` to `pom.xml`, start the app. Connect from a STOMP-capable client:
```javascript
// In a browser console with sockjs-client and @stomp/stompjs:
const client = new StompJs.Client({ brokerURL: 'ws://localhost:8080/ws' });
client.onConnect = () => {
    client.subscribe('/topic/messages', msg => console.log(msg.body));
    client.publish({ destination: '/app/chat', body: JSON.stringify({sender:'Alice', content:'Hello!'}) });
};
client.activate();
```

## 6. Walkthrough

- `@EnableWebSocketMessageBroker` activates Spring's STOMP over WebSocket infrastructure. It sets up the `SimpMessagingTemplate`, the in-memory broker, and the dispatch pipeline.
- `registry.addEndpoint("/ws").withSockJS()` exposes the WebSocket handshake endpoint at `/ws`. `.withSockJS()` adds an HTTP-polling fallback for environments without WebSocket support.
- `registry.enableSimpleBroker("/topic")` starts an in-memory message broker for prefix `/topic`. For production with many nodes, replace with a full STOMP broker (RabbitMQ, ActiveMQ) via `enableStompBrokerRelay`.
- `registry.setApplicationDestinationPrefixes("/app")` means client messages sent to `/app/chat` are routed to the `@MessageMapping("/chat")` method. The `/app` prefix is stripped before matching.
- `@SendTo("/topic/messages")` broadcasts the return value to all clients subscribed to `/topic/messages`. The broker delivers it to each subscriber's WebSocket connection.
- The `OutputMessage` record is serialised to JSON by Jackson and sent as a STOMP frame.

## 7. Gotchas & takeaways

> WebSocket connections are long-lived — they hold server resources (a socket, memory for session state) for their entire lifetime. Size your server (thread pool, connections limit) accordingly. Heartbeat configuration (`setHeartbeatValue`) prevents idle connections from timing out.

> STOMP's in-memory broker (`enableSimpleBroker`) is single-node only. For multi-instance deployments, use a STOMP relay to RabbitMQ or ActiveMQ so messages from one instance reach subscribers on another.

- `@SendToUser("/queue/reply")` sends a message to a specific user's private queue — useful for direct messages or per-user notifications.
- `SimpMessagingTemplate.convertAndSend("/topic/x", payload)` lets any Spring bean push messages to a topic programmatically (e.g. from a scheduled job or after a database update).
- Spring Security integrates with STOMP — apply `@EnableWebSocketSecurity` and configure STOMP CONNECT/SUBSCRIBE/SEND authorisation.
- For WebFlux, implement `WebSocketHandler` and register it via `SimpleUrlHandlerMapping` — STOMP is not natively supported in the reactive stack without a bridge.
