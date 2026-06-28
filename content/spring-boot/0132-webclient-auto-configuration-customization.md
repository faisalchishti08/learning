---
card: spring-boot
gi: 132
slug: webclient-auto-configuration-customization
title: WebClient auto-configuration & customization
---

## 1. What it is

`WebClient` is Spring WebFlux's non-blocking HTTP client for making outbound HTTP calls. It returns `Mono<T>` and `Flux<T>` so the caller never blocks waiting for a response. Spring Boot auto-configures a `WebClient.Builder` bean (not a `WebClient` directly) that is pre-configured with base URL, codecs, and any registered `WebClientCustomizer` beans. You inject the builder, add app-specific settings, and call `.build()`.

## 2. Why & when

Use `WebClient` when:

- Your app is reactive (WebFlux) — blocking HTTP clients (`RestTemplate`) on the event loop would stall Netty.
- You need streaming responses (Server-Sent Events, chunked transfers) from a remote service.
- You want to make many concurrent outbound calls with minimal thread overhead.

`WebClient` also works in a Spring MVC (Servlet) app — it still makes non-blocking HTTP calls, but the response must eventually be blocked (`.block()`) to produce a synchronous result. For Spring MVC, prefer `RestClient` (introduced in Spring Boot 3.2) for synchronous use cases.

## 3. Core concept

Spring Boot registers **one** `WebClient.Builder` prototype bean via `WebClientAutoConfiguration`. Because `WebClient.Builder` is mutable, Spring Boot makes it a prototype (a new instance per injection) so multiple classes can each customize their own copy independently.

`WebClientCustomizer` beans are called during builder creation to apply shared configuration (base URL, default headers, timeouts, filters). The precedence:

```
Auto-configured Builder
  ↓ WebClientCustomizer beans (shared config)
  ↓ Your injected builder (.baseUrl(), .defaultHeader(), .build())
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="105" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">WebClientCustomizer</text>
  <text x="97" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">beans (@Beans)</text>
  <rect x="255" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="105" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">WebClient.Builder</text>
  <text x="335" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(prototype bean)</text>
  <rect x="495" y="55" width="165" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="82" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">WebClient A</text>
  <rect x="495" y="120" width="165" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="147" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">WebClient B</text>
  <line x1="177" y1="110" x2="251" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wc)"/>
  <text x="214" y="104" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">customize</text>
  <line x1="417" y1="95" x2="491" y2="77" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wc2)"/>
  <line x1="417" y1="125" x2="491" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wc2)"/>
  <text x="454" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">.build()</text>
  <defs>
    <marker id="wc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`WebClientCustomizer` beans apply shared config to the auto-configured builder; each class injects the builder prototype and calls `.build()` to get its own `WebClient`.

## 5. Runnable example

```java
// WebClientApp.java  —  Spring Boot project with spring-boot-starter-webflux
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.reactive.function.client.WebClientCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@SpringBootApplication
public class WebClientApp {
    public static void main(String[] args) {
        SpringApplication.run(WebClientApp.class, args);
    }
}

// Shared customizer: apply to ALL WebClient.Builder instances
@Configuration
class HttpClientConfig {

    @Bean
    public WebClientCustomizer responseTimeoutCustomizer() {
        return builder -> builder
                .defaultHeader("X-App-Name", "demo")
                .filter((request, next) -> {
                    System.out.println("→ " + request.method() + " " + request.url());
                    return next.exchange(request);
                });
    }
}

// Service builds its own WebClient from the injected builder
@Service
class PostService {

    private final WebClient client;

    PostService(WebClient.Builder builder) {
        this.client = builder
                .baseUrl("https://jsonplaceholder.typicode.com")
                .build();
    }

    public Mono<String> getPost(int id) {
        return client.get()
                .uri("/posts/{id}", id)
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofSeconds(5));
    }
}

@RestController
class PostController {

    private final PostService postService;

    PostController(PostService postService) {
        this.postService = postService;
    }

    @GetMapping("/post")
    public Mono<String> post() {
        return postService.getPost(1);
    }
}
```

**How to run:** start the app (needs internet access to `jsonplaceholder.typicode.com`), then `curl http://localhost:8080/post`. Watch the console for the outgoing request log from the customizer filter.

## 6. Walkthrough

- `WebClientCustomizer` bean adds a default header and a logging filter to *every* `WebClient.Builder` instance created in the application — shared cross-cutting config in one place.
- `PostService` injects `WebClient.Builder` (prototype, so a fresh copy). It calls `.baseUrl(...)` and `.build()` to produce a `WebClient` tied to the JSONPlaceholder API. The logging filter from the customizer is already wired in.
- `.get().uri("/posts/{id}", id)` constructs the request. URI templates are expanded just like in `RestTemplate`.
- `.retrieve().bodyToMono(String.class)` sends the request non-blocking and returns a `Mono<String>`. The HTTP response body is deserialized by the auto-configured Jackson codec.
- `.timeout(Duration.ofSeconds(5))` adds a reactive timeout — if the upstream server doesn't respond in 5 seconds, the `Mono` errors with `TimeoutException`.
- No `WebClient` singleton is needed — each service owns its `WebClient`, built from the shared builder.

## 7. Gotchas & takeaways

> Inject `WebClient.Builder`, not `WebClient`. `WebClient.Builder` is a prototype bean (new instance per injection). If you inject a shared `WebClient` singleton, base-URL or filter changes in one service affect others.

> `.block()` on a `Mono` inside a Reactor event-loop thread causes a deadlock. In WebFlux services, return the `Mono` directly; only call `.block()` from non-reactive contexts (e.g., `main`, `@Scheduled`).

- `WebClientAutoConfiguration` only registers the builder bean when `WebClient` is on the classpath (from `spring-webflux`) — it works even in Spring MVC apps.
- Use `ExchangeFilterFunction` for cross-cutting concerns: auth token injection, request/response logging, retry logic.
- `spring.codec.max-in-memory-size` controls the buffer limit for response bodies; increase it for large JSON payloads.
- For circuit-breaking and retry, combine with Resilience4j's `WebClientCustomizer` or call `.retryWhen(Retry.backoff(...))` on the `Mono`.
