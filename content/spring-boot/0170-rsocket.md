---
card: spring-boot
gi: 170
slug: rsocket
title: RSocket
---

## 1. What it is

**RSocket** is a binary, multiplexed, reactive-native protocol for inter-service communication over TCP, WebSocket, or AERON. Spring Boot auto-configures RSocket via `spring-boot-starter-rsocket`, giving you `RSocketRequester` for making requests and `@MessageMapping` for handling them — the same annotation used in WebSocket controllers but extended with RSocket's four interaction models.

Think of RSocket as HTTP/2 done right for microservices: full duplex, back-pressure aware, and network-transport agnostic.

## 2. Why & when

**Why RSocket over HTTP REST:**
- **Back-pressure:** the responder tells the requester how many items it can handle — no buffer overflow under load.
- **Four interaction models** in one protocol: fire-and-forget, request-response, request-stream, channel (bidirectional stream).
- **Multiplexing:** many logical connections over one TCP socket — avoids the head-of-line blocking HTTP/1.1 suffers.
- **Resumption:** a dropped connection can resume without losing in-flight requests.

**When to use:**
- Real-time streaming from server to client (live metrics, notifications).
- High-throughput microservice calls where per-request TCP overhead is prohibitive.
- Reactive pipelines using Spring WebFlux/Project Reactor end-to-end.

**Not ideal for:** browser-facing APIs (use WebSocket/HTTP instead) or teams not on reactive stacks.

## 3. Core concept

RSocket's four interaction models:

| Model | Description | Java type |
|---|---|---|
| **Request-Response** | One request, one reply (like HTTP) | `Mono<Response>` |
| **Fire-and-Forget** | One request, no reply | `Mono<Void>` |
| **Request-Stream** | One request, many replies | `Flux<Response>` |
| **Channel** | Many requests, many replies (full duplex) | `Flux<Response>` from `Flux<Request>` |

Server side: annotate a Spring bean method with `@MessageMapping("route.name")`. Spring routes incoming RSocket frames to the method by the route metadata in the frame.

Client side: `RSocketRequester.route("route.name").retrieveMono(ResponseType.class)` for request-response; `.retrieveFlux(...)` for streams.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RSocket interaction models: fire-forget, request-response, request-stream, channel">
  <!-- RSocketRequester (Client) -->
  <rect x="10" y="60" width="150" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="83" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client</text>
  <text x="85" y="99" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">RSocketRequester</text>
  <text x="85" y="119" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">fire-and-forget ➜</text>
  <text x="85" y="136" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">request-response ⇄</text>
  <text x="85" y="153" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">request-stream ➜⇇</text>
  <text x="85" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">channel ⇄⇄</text>

  <!-- Single TCP/WebSocket connection -->
  <rect x="200" y="100" width="240" height="50" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="121" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Single TCP Connection</text>
  <text x="320" y="138" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">multiplexed frames · back-pressure</text>

  <!-- Arrows -->
  <line x1="165" y1="125" x2="198" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rsa)"/>
  <line x1="200" y1="125" x2="168" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rsb)" stroke-dasharray="4,3"/>

  <!-- Server -->
  <rect x="445" y="60" width="150" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="83" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="520" y="99" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@MessageMapping</text>
  <text x="520" y="119" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Mono&lt;Void&gt;</text>
  <text x="520" y="136" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Mono&lt;Response&gt;</text>
  <text x="520" y="153" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Flux&lt;Response&gt;</text>
  <text x="520" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Flux&lt;&gt; from Flux&lt;&gt;</text>

  <line x1="445" y1="125" x2="445" y2="125" stroke="#79c0ff" stroke-width="0"/>
  <line x1="444" y1="125" x2="411" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rsb)"/>
  <line x1="445" y1="125" x2="445" y2="125"/>
  <!-- left side of server arrow -->
  <line x1="440" y1="125" x2="443" y2="125" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="443" y1="125" x2="443" y2="125"/>

  <!-- Arrow from TCP to server -->
  <line x1="442" y1="125" x2="446" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rsa)"/>

  <text x="350" y="205" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All four interaction models share one multiplexed connection with flow control</text>

  <defs>
    <marker id="rsa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rsb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Four interaction models over one TCP connection with built-in back-pressure signalling.

## 5. Runnable example

```java
// RSocketDemo.java — illustrates all four RSocket interaction models conceptually
// How to run: java RSocketDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-rsocket; use @MessageMapping + RSocketRequester

import java.util.List;
import java.util.function.Consumer;
import java.util.function.Function;

public class RSocketDemo {

    // Simulate server-side @MessageMapping handlers
    static void handleFireAndForget(String payload) {
        System.out.println("  [Server @MessageMapping fire-forget] received: " + payload);
    }

    static String handleRequestResponse(String payload) {
        return "Echo: " + payload.toUpperCase();
    }

    static List<String> handleRequestStream(String query) {
        return List.of(
            "Result[0] for " + query,
            "Result[1] for " + query,
            "Result[2] for " + query
        );
    }

    static List<String> handleChannel(List<String> requests) {
        // Bidirectional: for each client message, emit two responses
        return requests.stream()
                .flatMap(r -> List.of("ACK: " + r, "PROCESSED: " + r).stream())
                .toList();
    }

    // Simulate RSocketRequester client calls
    static void demoFireAndForget(Consumer<String> serverHandler) {
        System.out.println("\n--- 1. Fire-and-Forget ---");
        System.out.println("[Client] requester.route('audit').fireAndForget('login event')");
        serverHandler.accept("login event");  // no return value
        System.out.println("[Client] returns immediately (Mono<Void>)");
    }

    static void demoRequestResponse(Function<String,String> serverHandler) {
        System.out.println("\n--- 2. Request-Response ---");
        System.out.println("[Client] requester.route('echo').retrieveMono(String.class)");
        String response = serverHandler.apply("hello rsocket");
        System.out.println("[Client] received Mono<String>: " + response);
    }

    static void demoRequestStream(Function<String,List<String>> serverHandler) {
        System.out.println("\n--- 3. Request-Stream ---");
        System.out.println("[Client] requester.route('search').retrieveFlux(String.class)");
        List<String> stream = serverHandler.apply("metrics");
        stream.forEach(item -> System.out.println("[Client] Flux onNext: " + item));
        System.out.println("[Client] Flux onComplete");
    }

    static void demoChannel(Function<List<String>,List<String>> serverHandler) {
        System.out.println("\n--- 4. Channel (bidirectional stream) ---");
        List<String> clientFlux = List.of("msg-A", "msg-B", "msg-C");
        System.out.println("[Client] sending Flux: " + clientFlux);
        List<String> responses = serverHandler.apply(clientFlux);
        responses.forEach(r -> System.out.println("[Client] received: " + r));
    }

    public static void main(String[] args) {
        System.out.println("=== RSocket Four Interaction Models Demo ===");
        demoFireAndForget(RSocketDemo::handleFireAndForget);
        demoRequestResponse(RSocketDemo::handleRequestResponse);
        demoRequestStream(RSocketDemo::handleRequestStream);
        demoChannel(RSocketDemo::handleChannel);
    }
}
```

**How to run:** `java RSocketDemo.java`

## 6. Walkthrough

- **Fire-and-forget:** client calls `fireAndForget()` returning `Mono<Void>` — it subscribes but never waits for a response frame. Useful for audit logs and metrics where loss is acceptable.
- **Request-response:** `retrieveMono(String.class)` returns a `Mono<String>` that completes with exactly one frame from the server — semantically like HTTP but over RSocket's multiplexed channel.
- **Request-stream:** `retrieveFlux(String.class)` subscribes to a server-pushed stream. Back-pressure: the Reactor `Flux` subscriber's `request(n)` calls translate to RSocket REQUESTN frames, telling the server how many items the client is ready to receive.
- **Channel:** the client sends a `Flux<>` and receives a `Flux<>` — both sides stream concurrently. Ideal for real-time bidirectional data exchange.
- In Spring Boot, `@MessageMapping("route.name")` on a controller method handles each model based on the return and parameter types (Spring inspects signatures automatically).

## 7. Gotchas & takeaways

> RSocket **does not auto-start a server** unless you set `spring.rsocket.server.port`. Without it, the auto-configured beans are client-only.

> Back-pressure is only meaningful in **reactive pipelines**. Wrapping blocking code in `Mono.fromCallable` on a bounded `Schedulers.boundedElastic()` defeats the purpose — keep the entire chain non-blocking.

- Add `spring-boot-starter-rsocket` + `spring-boot-starter-webflux` (RSocket works with Reactor).
- `spring.rsocket.server.port=7000` starts a TCP RSocket server; `spring.rsocket.server.transport=websocket` for WebSocket.
- Build `RSocketRequester` with `RSocketRequester.builder().connectTcp("host", 7000)` on the client side.
- `@ConnectMapping` handles the initial connection setup frame — useful for auth handshakes.
- RSocket security integrates with Spring Security via `RSocketSecurity` — configure per-route authorization.
