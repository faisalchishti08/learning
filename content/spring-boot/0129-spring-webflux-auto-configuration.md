---
card: spring-boot
gi: 129
slug: spring-webflux-auto-configuration
title: Spring WebFlux auto-configuration
---

## 1. What it is

Spring WebFlux is Spring's reactive web framework — non-blocking, event-loop-driven, built on Project Reactor. Spring Boot auto-configures WebFlux when `spring-boot-starter-webflux` is on the classpath: it registers the reactive `DispatcherHandler`, codec configuration, resource handling, and an embedded Reactor Netty server (default). You write `@RestController` classes exactly as in Spring MVC; the difference is that handler methods can return `Mono<T>` or `Flux<T>` instead of plain objects.

## 2. Why & when

Spring MVC blocks a thread per request. Under high concurrency (thousands of simultaneous long-lived connections — streaming, SSE, chat, IoT), that thread-per-request model exhausts thread pools. WebFlux uses a small, fixed event-loop thread pool and processes I/O callbacks, handling far more concurrent connections with the same hardware.

Use WebFlux when:

- Your app makes many external I/O calls (HTTP, database) that can overlap.
- You need streaming responses (Server-Sent Events, reactive data streams).
- You're building a gateway or proxy where latency hiding matters.

Stick with Spring MVC when your code is synchronous or your team is unfamiliar with reactive programming — blocking the event loop is worse than threading.

## 3. Core concept

WebFlux's auto-configuration is triggered by `WebFluxAutoConfiguration` (presence of `spring-boot-starter-webflux`, absence of `spring-boot-starter-web` taking priority). Key beans registered:

- `DispatcherHandler` — reactive equivalent of `DispatcherServlet`.
- `RouterFunctionMapping` / `RequestMappingHandlerMapping` — handles `@RestController` and functional routes.
- `CodecCustomizer` — configures Jackson JSON, Protobuf, etc.
- Reactor Netty `HttpServer` wrapped as `WebServer`.

WebFlux supports two programming models: **annotation-based** (`@RestController`) identical in surface to Spring MVC, and **functional** (lambda routes with `RouterFunction<ServerResponse>`).

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">HTTP Request</text>
  <text x="85" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Reactor Netty</text>
  <rect x="230" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="107" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">DispatcherHandler</text>
  <rect x="460" y="55" width="190" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="82" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">@RestController</text>
  <text x="555" y="97" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">returns Mono / Flux</text>
  <rect x="460" y="120" width="190" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="144" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">RouterFunction</text>
  <text x="555" y="159" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">functional routing</text>
  <line x1="152" y1="110" x2="226" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wf)"/>
  <line x1="382" y1="100" x2="456" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wf2)"/>
  <line x1="382" y1="120" x2="456" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wf3)"/>
  <defs>
    <marker id="wf" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wf2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wf3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Reactor Netty receives requests, passes them to `DispatcherHandler`, which routes to annotation controllers or functional routes returning reactive types.

## 5. Runnable example

```java
// WebFluxApp.java  —  Spring Boot project with spring-boot-starter-webflux
// (do NOT also have spring-boot-starter-web; they conflict)

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.server.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

@SpringBootApplication
public class WebFluxApp {
    public static void main(String[] args) {
        SpringApplication.run(WebFluxApp.class, args);
    }

    // Functional routing style
    @Bean
    public RouterFunction<ServerResponse> routes() {
        return RouterFunctions.route()
                .GET("/ping", req -> ServerResponse.ok().bodyValue("pong"))
                .build();
    }
}

// Annotation style — identical surface to Spring MVC
@RestController
@RequestMapping("/items")
class ItemController {

    @GetMapping("/{id}")
    public Mono<String> getItem(@PathVariable int id) {
        // Async result — non-blocking
        return Mono.just("Item #" + id)
                   .delayElement(Duration.ofMillis(100));
    }

    @GetMapping(value = "/stream", produces = "text/event-stream")
    public Flux<String> streamItems() {
        // Server-Sent Events: emits one item per second
        return Flux.interval(Duration.ofSeconds(1))
                   .map(i -> "event-" + i)
                   .take(5);
    }
}
```

**How to run:** add `spring-boot-starter-webflux` (not `web`) to `pom.xml`, start the app, then:
- `curl http://localhost:8080/ping` → `pong`
- `curl http://localhost:8080/items/7` → `Item #7`
- `curl -N http://localhost:8080/items/stream` → 5 SSE events over 5 seconds

## 6. Walkthrough

- `spring-boot-starter-webflux` triggers `WebFluxAutoConfiguration` and `ReactiveWebServerFactoryAutoConfiguration`. These configure `DispatcherHandler` and start Reactor Netty on port 8080 (or `server.port`).
- The functional `RouterFunction` bean is detected by `RouterFunctionMapping`. It handles `GET /ping` and returns a `200 OK` with body `"pong"`.
- `ItemController` uses annotation-based routing. `Mono<String>` signals "I'll return one item asynchronously." `delayElement` simulates async I/O without blocking any thread.
- `Flux<String>` in `streamItems()` combined with `produces = "text/event-stream"` tells Spring WebFlux to serialise each emitted element as an SSE event. `.take(5)` limits the stream to 5 events.
- Reactor Netty runs a small event loop (default: CPU-count threads). All `Mono`/`Flux` operations are scheduled on these threads — never block them with `Thread.sleep` or JDBC calls.

## 7. Gotchas & takeaways

> Do NOT include both `spring-boot-starter-web` and `spring-boot-starter-webflux`. Spring Boot picks Spring MVC (servlet) when both are present; WebFlux is silently ignored. Use one or the other.

> Blocking a Reactor event-loop thread (with JDBC, `Thread.sleep`, or any blocking I/O) causes severe performance degradation. Move blocking work to a bounded thread pool with `Schedulers.boundedElastic()`.

- `@EnableWebFlux` is **not** needed in Spring Boot apps — auto-config handles it. Adding it disables some auto-configuration.
- WebFlux and Spring MVC share `@RestController`, `@GetMapping`, etc. — but the underlying runtime is completely different.
- `WebTestClient` is the WebFlux-native test client; use it instead of `MockMvc` for reactive controller tests.
- R2DBC provides non-blocking database access compatible with WebFlux; use it instead of JDBC for fully reactive pipelines.
