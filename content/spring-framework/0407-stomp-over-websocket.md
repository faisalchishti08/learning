---
card: spring-framework
gi: 407
slug: stomp-over-websocket
title: "STOMP over WebSocket"
---

## 1. What it is

STOMP (Simple/Streaming Text Oriented Messaging Protocol) is a small, text-based messaging protocol with a frame format similar to HTTP (a command, headers, an optional body). Spring's WebSocket support can run STOMP as a sub-protocol *inside* a raw WebSocket connection, giving you familiar messaging semantics — subscribe to a destination, send to a destination — on top of a WebSocket instead of having to invent your own message framing over raw WebSocket frames.

```java
@Controller
class ChatController {
    @MessageMapping("/chat.send")          // client sends to /app/chat.send
    @SendTo("/topic/messages")             // broadcast result to /topic/messages
    ChatMessage handle(ChatMessage message) {
        return message;
    }
}
```

## 2. Why & when

A raw WebSocket connection is just a bidirectional byte/text stream — it has no built-in concept of "topics," "subscriptions," or "routing a message to the right handler." Building that yourself means inventing a message envelope format and writing your own dispatch logic. STOMP already defines that envelope and a small vocabulary (`SEND`, `SUBSCRIBE`, `MESSAGE`, `CONNECT`), and Spring's STOMP support maps it directly onto familiar Spring MVC-style annotations (`@MessageMapping`, similar in spirit to `@RequestMapping`) plus the `Message`/`MessageChannel` abstractions from the Spring Messaging card.

Reach for STOMP over WebSocket when:

- You need real-time, bidirectional communication with a clear publish/subscribe model — chat, live notifications, collaborative editing, live dashboards.
- You want the server to broadcast a message to many subscribed clients (a topic) without manually tracking which WebSocket sessions are interested in what.
- You'd rather write `@MessageMapping`-annotated methods than manage raw `WebSocketHandler` message parsing yourself (covered in the WebSocket Servlet-stack card for when you do need that lower level).

## 3. Core concept

```
 Client                                  Server
   |                                        |
   |--- CONNECT (STOMP frame) ------------->|
   |<-- CONNECTED --------------------------|
   |                                        |
   |--- SUBSCRIBE /topic/messages --------->|  (client interested in this destination)
   |                                        |
   |--- SEND /app/chat.send  {"text":"hi"}->|
   |                                        |    @MessageMapping("/chat.send") handles it
   |                                        |    @SendTo("/topic/messages") broadcasts result
   |<-- MESSAGE /topic/messages {"text":"hi"}--|  (delivered to every subscriber, including sender)
```

`@MessageMapping` routes an incoming `SEND` frame to a handler method the same way `@RequestMapping` routes an HTTP request to a controller method; `@SendTo` (or an injected `SimpMessagingTemplate`) is how the result gets broadcast back out to subscribers of a destination.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two clients subscribe to a topic, one sends a message, both receive the broadcast">
  <rect x="10" y="20" width="130" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client A</text>

  <rect x="10" y="140" width="130" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="167" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client B</text>

  <rect x="250" y="80" width="150" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@MessageMapping</text>
  <text x="325" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/app/chat.send</text>

  <rect x="470" y="80" width="150" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/topic/messages</text>
  <text x="545" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">broadcast target</text>

  <line x1="140" y1="35" x2="245" y2="90" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="180" y="55" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">SEND</text>

  <line x1="400" y1="102" x2="465" y2="102" stroke="#79c0ff" stroke-width="2" marker-end="url(#b)"/>

  <line x1="470" y1="95" x2="140" y2="35" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4"/>
  <line x1="470" y1="110" x2="140" y2="155" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#b)"/>
  <text x="300" y="180" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">MESSAGE broadcast to every subscriber (dashed)</text>

  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Only Client A sends, but the broadcast target's subscribers — both A and B — receive the resulting `MESSAGE` frame.

## 5. Runnable example

### Level 1 — Basic

A minimal STOMP endpoint that echoes a message back to a broadcast topic, using Spring's built-in simple in-memory broker (no external message broker needed).

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.stereotype.Controller;
import org.springframework.web.socket.config.annotation.*;

public class StompBasic {

    record ChatMessage(String user, String text) {}

    @Controller
    static class ChatController {
        @MessageMapping("/chat.send")
        @SendTo("/topic/messages")
        ChatMessage handle(ChatMessage message) {
            System.out.println("Server received: " + message);
            return message; // broadcast the same message to every /topic/messages subscriber
        }
    }

    @Configuration
    @EnableWebSocketMessageBroker
    static class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
        @Override
        public void configureMessageBroker(MessageBrokerRegistry registry) {
            registry.enableSimpleBroker("/topic");   // in-memory broker for broadcast destinations
            registry.setApplicationDestinationPrefixes("/app"); // client SEND destinations start with /app
        }

        @Override
        public void registerStompEndpoints(StompEndpointRegistry registry) {
            registry.addEndpoint("/ws-chat"); // clients connect here
        }
    }
}
```

How to run: this class defines the server-side configuration; run it inside a Spring Boot web application (`spring-boot-starter-websocket`) and connect with a STOMP-over-WebSocket JavaScript client (e.g. `@stomp/stompjs`) to `ws://localhost:8080/ws-chat`, `SUBSCRIBE` to `/topic/messages`, then `SEND` to `/app/chat.send`.

`enableSimpleBroker("/topic")` activates Spring's built-in in-memory broker for any destination starting with `/topic` — messages sent there are simply broadcast to all current subscribers, no external broker process required. `setApplicationDestinationPrefixes("/app")` means a client's `SEND` to `/app/chat.send` gets routed to the `@MessageMapping("/chat.send")` method (the `/app` prefix is stripped for matching). `@SendTo("/topic/messages")` takes the method's return value and publishes it to that broker destination automatically.

### Level 2 — Intermediate

Add user-specific messaging (private replies) alongside the broadcast topic, and inject `SimpMessagingTemplate` to send messages outside the request/response flow — e.g., from a scheduled job or another service, not just from within a `@MessageMapping` method.

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.stereotype.Controller;
import org.springframework.web.socket.config.annotation.*;

import java.security.Principal;

public class StompIntermediate {

    record ChatMessage(String user, String text) {}
    record PrivateNotice(String text) {}

    @Controller
    static class ChatController {
        private final SimpMessagingTemplate messagingTemplate;
        ChatController(SimpMessagingTemplate messagingTemplate) { this.messagingTemplate = messagingTemplate; }

        @MessageMapping("/chat.send")
        @SendTo("/topic/messages")
        ChatMessage handle(ChatMessage message) {
            return message;
        }

        @MessageMapping("/chat.whisper")
        void whisper(ChatMessage message, Principal principal) {
            // Send privately to one specific user's own destination, not broadcast to /topic.
            messagingTemplate.convertAndSendToUser(
                    message.user(), "/queue/private", new PrivateNotice("Whisper: " + message.text()));
        }

        void notifyAllUsers(String announcement) {
            // Called from anywhere — not tied to an incoming client message at all.
            messagingTemplate.convertAndSend("/topic/announcements", announcement);
        }
    }

    @Configuration
    @EnableWebSocketMessageBroker
    static class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
        @Override
        public void configureMessageBroker(MessageBrokerRegistry registry) {
            registry.enableSimpleBroker("/topic", "/queue"); // /queue used for per-user destinations
            registry.setApplicationDestinationPrefixes("/app");
            registry.setUserDestinationPrefix("/user"); // convertAndSendToUser targets /user/{name}/...
        }

        @Override
        public void registerStompEndpoints(StompEndpointRegistry registry) {
            registry.addEndpoint("/ws-chat");
        }
    }
}
```

How to run: same as Level 1 — run inside a Spring Boot web application, with an authenticated STOMP session so `Principal` is populated for `whisper`.

`SimpMessagingTemplate.convertAndSendToUser(username, destination, payload)` routes a message specifically to the WebSocket session(s) belonging to that user, resolved internally to a per-session destination even though multiple users are subscribed to `/user/queue/private` in general — Spring translates the logical per-user destination into the correct concrete session automatically. `notifyAllUsers` shows the template can be called from *anywhere* in the application (a scheduled job, an event listener), not just from inside a `@MessageMapping` handler, decoupling "who triggers a broadcast" from "how STOMP delivers it."

### Level 3 — Advanced

Production STOMP setups need authentication/authorization at the message level (not just at WebSocket handshake time) and a way to reject a malformed or unauthorized `SEND` before it reaches business logic — done via a `ChannelInterceptor` on the inbound channel, tying back directly to the Spring Messaging card's interceptor mechanism.

```java
import org.springframework.context.annotation.*;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.stereotype.Controller;
import org.springframework.web.socket.config.annotation.*;

public class StompAdvanced {

    record ChatMessage(String user, String text) {}

    @Controller
    static class ChatController {
        @MessageMapping("/chat.send")
        @SendTo("/topic/messages")
        ChatMessage handle(ChatMessage message) {
            if (message.text().length() > 500) {
                throw new IllegalArgumentException("Message too long");
            }
            return message;
        }
    }

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
            registry.addEndpoint("/ws-chat");
        }

        @Override
        public void configureClientInboundChannel(ChannelRegistration registration) {
            registration.interceptors(new ChannelInterceptor() {
                @Override
                public Message<?> preSend(Message<?> message, MessageChannel channel) {
                    StompHeaderAccessor accessor = StompHeaderAccessor.wrap(message);
                    if (StompCommand.SEND.equals(accessor.getCommand())) {
                        if (accessor.getUser() == null) {
                            System.out.println("Rejected unauthenticated SEND to " + accessor.getDestination());
                            return null; // block the frame from reaching @MessageMapping at all
                        }
                        System.out.println("Authenticated SEND from " + accessor.getUser().getName()
                                + " to " + accessor.getDestination());
                    }
                    return message;
                }
            });
        }
    }
}
```

How to run: same as Level 1 — run inside a Spring Boot web application with Spring Security configured so authenticated sessions populate a `Principal` on the STOMP session.

`configureClientInboundChannel` exposes the exact same `ChannelInterceptor`/`preSend` mechanism from the Spring Messaging card, applied specifically to the channel STOMP frames travel through on their way *in* from clients. Checking `accessor.getUser() == null` rejects any `SEND` frame from an unauthenticated session before it ever reaches `ChatController.handle`, centralizing that check once instead of repeating an auth check inside every `@MessageMapping` method.

## 6. Walkthrough

Trace one `SEND /app/chat.send` frame through `StompAdvanced`'s configuration, from an authenticated client:

1. **Frame arrives.** The client's WebSocket connection carries a STOMP `SEND` frame with destination `/app/chat.send` and a JSON body like `{"user":"ada","text":"hello"}`.
2. **Inbound channel interception.** Before any routing happens, the registered `ChannelInterceptor.preSend` runs. `StompHeaderAccessor.wrap(message)` extracts the STOMP-specific view of the message (command, destination, session user). Since the command is `SEND` and `accessor.getUser()` is populated (the session authenticated during the WebSocket handshake), the interceptor logs `"Authenticated SEND from ada to /app/chat.send"` and returns the message unchanged, allowing it through.
3. **Prefix stripping and routing.** The `/app` prefix (registered via `setApplicationDestinationPrefixes`) is stripped, leaving `/chat.send`, which is matched against `@MessageMapping("/chat.send")` on `ChatController`.
4. **Payload conversion.** The JSON body is deserialized into a `ChatMessage` record — the same Jackson-based conversion machinery used elsewhere in Spring's message-based features — and passed as the method's argument.
5. **Handler execution.** `handle(message)` checks the message length (500-char limit); assuming it's short enough, it returns the `ChatMessage` unchanged.
6. **`@SendTo` broadcast.** The return value is serialized back to JSON and published to `/topic/messages` via the simple in-memory broker.
7. **Fan-out to subscribers.** Every WebSocket session currently subscribed to `/topic/messages` receives a STOMP `MESSAGE` frame with that JSON body — this includes the original sender if they're also subscribed, which is why chat UIs typically see their own message echoed back through the same subscription rather than rendering it optimistically.

```
SEND /app/chat.send {user:ada, text:hello}
   -> inbound ChannelInterceptor.preSend
        user present? yes -> allow
   -> strip /app prefix -> match @MessageMapping("/chat.send")
   -> deserialize JSON -> ChatMessage
   -> handle() -> length OK -> return ChatMessage
   -> @SendTo("/topic/messages") -> broker publishes
   -> MESSAGE frame -> every subscriber of /topic/messages
```

If step 2 had found no authenticated user, the interceptor would return `null`, and neither step 3 nor any subsequent step would occur — the frame is silently dropped before it reaches any business logic, exactly like the low-priority message veto in the Spring Messaging card's `ChannelInterceptor` example.

## 7. Gotchas & takeaways

> Gotcha: `enableSimpleBroker(...)` uses an in-memory broker that lives entirely inside one application instance — if you run multiple instances behind a load balancer, a client subscribed to instance A never receives a broadcast triggered on instance B, since there's no shared broker state between them. Production multi-instance deployments need `enableStompBrokerRelay(...)` to delegate to a real external STOMP-capable broker (like RabbitMQ) that all instances connect to, so broadcasts reach every subscriber regardless of which instance they're connected to.

- STOMP gives WebSocket a familiar publish/subscribe vocabulary (`SEND`, `SUBSCRIBE`, topics) instead of requiring you to invent your own message framing over raw WebSocket frames.
- `@MessageMapping` + `@SendTo` covers the common request-then-broadcast pattern; `SimpMessagingTemplate` is the tool for sending messages from anywhere else in the application, including outside any incoming STOMP frame.
- `convertAndSendToUser` targets a specific authenticated user's session(s) without you needing to track WebSocket session IDs manually.
- Apply authentication/authorization checks via a `ChannelInterceptor` on the client inbound channel, centralizing the check once rather than duplicating it inside every `@MessageMapping` method.
