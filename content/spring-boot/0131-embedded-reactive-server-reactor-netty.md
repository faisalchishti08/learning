---
card: spring-boot
gi: 131
slug: embedded-reactive-server-reactor-netty
title: Embedded reactive server (Reactor Netty)
---

## 1. What it is

When you use `spring-boot-starter-webflux`, Spring Boot auto-configures **Reactor Netty** as the embedded HTTP server instead of Tomcat. Reactor Netty is a non-blocking, event-driven server built on top of Netty, the high-performance async networking library. It processes HTTP requests on a small set of event-loop threads without blocking, enabling very high concurrency with low memory overhead.

## 2. Why & when

Tomcat (the Servlet default) gives each request its own thread. Reactor Netty uses an event loop: a fixed pool of threads handles I/O callbacks for thousands of concurrent connections simultaneously. Under high concurrency (many slow or long-lived requests), Reactor Netty uses far fewer resources.

Reactor Netty is the right choice when:

- Your WebFlux app needs maximum throughput under high concurrency.
- You're building a streaming or SSE endpoint.
- You need very low memory per connection (IoT gateways, proxies).

Spring Boot also supports **Undertow** as a reactive server (via `spring-boot-starter-undertow` on the WebFlux path) and Jetty with reactive support, but Reactor Netty is the default and the most battle-tested reactive choice.

## 3. Core concept

Reactor Netty wraps Netty's `EventLoopGroup` and `ServerBootstrap` into a `ReactorHttpHandlerAdapter`. Spring Boot's `ReactiveWebServerFactoryAutoConfiguration` detects `spring-boot-starter-webflux` and creates a `NettyReactiveWebServerFactory` bean.

Event-loop thread model:

- **Boss group**: accepts incoming TCP connections.
- **Worker group**: handles I/O reads/writes. Default: `2 × CPU` threads.
- No request ever blocks a worker thread — blocking calls must be offloaded to `Schedulers.boundedElastic()`.

Customisation follows the same pattern as Servlet containers: `WebServerFactoryCustomizer<NettyReactiveWebServerFactory>` or properties under `server.*`.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="120" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Clients</text>
  <text x="80" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">N connections</text>
  <rect x="215" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="84" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Boss EventLoop</text>
  <rect x="215" y="120" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="145" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Worker EventLoop</text>
  <text x="290" y="162" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">2×CPU threads</text>
  <rect x="445" y="80" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">DispatcherHandler</text>
  <text x="545" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">→ WebFlux pipeline</text>
  <line x1="142" y1="110" x2="211" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rn)"/>
  <line x1="142" y1="110" x2="211" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rn)"/>
  <line x1="367" y1="148" x2="441" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rn2)"/>
  <defs>
    <marker id="rn" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rn2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Boss EventLoop accepts TCP connections; Worker EventLoop reads/writes I/O without blocking; DispatcherHandler runs the WebFlux pipeline on the same threads.

## 5. Runnable example

```java
// ReactorNettyApp.java  —  Spring Boot project with spring-boot-starter-webflux
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.embedded.netty.NettyReactiveWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

@SpringBootApplication
public class ReactorNettyApp {
    public static void main(String[] args) {
        SpringApplication.run(ReactorNettyApp.class, args);
    }
}

@Configuration
class NettyConfig {

    // Customise Netty-specific settings
    @Bean
    public WebServerFactoryCustomizer<NettyReactiveWebServerFactory> nettyCustomizer() {
        return factory -> {
            factory.addServerCustomizers(server ->
                server.tcpConfiguration(tcp ->
                    tcp.option(io.netty.channel.ChannelOption.SO_BACKLOG, 1024)
                )
            );
        };
    }
}

@RestController
class ComputeController {

    @GetMapping("/compute")
    public Mono<String> compute() {
        // Offload blocking work to a bounded thread pool — never block the event loop
        return Mono.fromCallable(() -> {
                    Thread.sleep(50); // simulate blocking I/O
                    return "result";
                })
                .subscribeOn(Schedulers.boundedElastic())
                .map(r -> "Thread: " + Thread.currentThread().getName() + " → " + r);
    }

    @GetMapping("/fast")
    public Mono<String> fast() {
        // Pure reactive — safe on event-loop thread
        return Mono.just("Event loop: " + Thread.currentThread().getName());
    }
}
```

**How to run:** add `spring-boot-starter-webflux` to `pom.xml`, start the app, then:
- `curl http://localhost:8080/fast` — runs on Netty event-loop thread.
- `curl http://localhost:8080/compute` — blocking work offloaded to `boundedElastic` pool.

## 6. Walkthrough

- `spring-boot-starter-webflux` triggers `ReactiveWebServerFactoryAutoConfiguration`, which registers `NettyReactiveWebServerFactory` and starts Reactor Netty on the configured port.
- `WebServerFactoryCustomizer<NettyReactiveWebServerFactory>` targets only Reactor Netty. `factory.addServerCustomizers(...)` lets you call Netty's fluent API directly — here setting `SO_BACKLOG` to 1024 (TCP connection queue size).
- `/fast` returns a `Mono.just(...)` — fully non-blocking; it runs to completion on the Netty worker thread.
- `/compute` uses `Mono.fromCallable(...)` with `.subscribeOn(Schedulers.boundedElastic())`. `subscribeOn` moves the blocking `Thread.sleep` to a separate thread pool, freeing the event-loop thread to process other requests.
- The thread names in the response (`reactor-http-nio-N` vs. `boundedElastic-N`) confirm which pool executed each piece of work.
- `server.port`, `server.ssl.*`, and `server.http2.enabled` all work the same on Reactor Netty as on Tomcat.

## 7. Gotchas & takeaways

> **Never block a Netty event-loop thread.** `Thread.sleep`, JDBC, `File.read`, `RestTemplate.exchange` — any of these stall the entire event loop and kill throughput. Offload to `Schedulers.boundedElastic()`.

> Reactor Netty's default worker thread count is `2 × Runtime.getRuntime().availableProcessors()`. In containers with CPU limits, this may be very small (2–4 threads) — monitor thread utilisation under load.

- `NettyReactiveWebServerFactory` is the reactive equivalent of `TomcatServletWebServerFactory`.
- HTTP/2 on Reactor Netty requires TLS; enable with `server.http2.enabled=true` plus `server.ssl.*`.
- To switch to Undertow for reactive: exclude `spring-boot-starter-reactor-netty` and add `spring-boot-starter-undertow`.
- `server.netty.connection-timeout` and `server.netty.max-keep-alive-requests` are Reactor-Netty-specific properties available in Spring Boot.
