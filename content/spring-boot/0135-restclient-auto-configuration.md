---
card: spring-boot
gi: 135
slug: restclient-auto-configuration
title: RestClient auto-configuration
---

## 1. What it is

`RestClient` is a synchronous HTTP client introduced in Spring Framework 6.1 (Spring Boot 3.2). It has the same fluent API feel as `WebClient` but is blocking — it integrates with Spring MVC apps without requiring Project Reactor. Spring Boot auto-configures a `RestClient.Builder` bean (prototype scope) pre-wired with message converters, and supports `RestClientCustomizer` beans for shared configuration. `RestClient` replaces `RestTemplate` for new synchronous HTTP client code.

## 2. Why & when

`RestTemplate` is not deprecated but is in maintenance mode — no new features. `WebClient` is full reactive and awkward to use in blocking Spring MVC contexts (requires `.block()` everywhere). `RestClient` fills the gap:

- Synchronous, blocking — natural fit for Spring MVC apps.
- Fluent builder API matching `WebClient` conventions.
- Supports the same `ClientHttpRequestFactory` ecosystem as `RestTemplate`.
- Does not require the WebFlux dependency.

Use `RestClient` for new synchronous outbound HTTP in Spring Boot 3.2+ apps. Keep `RestTemplate` if you're on an older version or have extensive existing usage.

## 3. Core concept

`RestClientAutoConfiguration` registers a `RestClient.Builder` bean when `RestClient` is on the classpath (Spring Boot 3.2+). The builder is a prototype bean — each injection gets a fresh copy. `RestClientCustomizer` beans are called on every new builder, applying shared settings (base URL, default headers, request factory).

```
RestClientCustomizer beans (shared)
  ↓
RestClient.Builder (prototype)
  ↓ .baseUrl() .defaultHeader() .build()
RestClient (immutable, thread-safe)
```

Response bodies are deserialized via the same `HttpMessageConverter` stack as Spring MVC, auto-configured with Jackson, String, byte[], etc.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="105" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">RestClientCustomizer</text>
  <text x="97" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">beans</text>
  <rect x="255" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="105" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">RestClient.Builder</text>
  <text x="335" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(prototype)</text>
  <rect x="495" y="60" width="160" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="87" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">RestClient A</text>
  <rect x="495" y="120" width="160" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="147" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">RestClient B</text>
  <line x1="177" y1="110" x2="251" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cl)"/>
  <line x1="417" y1="98" x2="491" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cl2)"/>
  <line x1="417" y1="122" x2="491" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cl2)"/>
  <defs>
    <marker id="cl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cl2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`RestClientCustomizer` beans configure the shared builder; each service injects the prototype and calls `.build()` for its own immutable `RestClient`.

## 5. Runnable example

```java
// RestClientApp.java  —  Spring Boot 3.2+ project with spring-boot-starter-web
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestClientCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@SpringBootApplication
public class RestClientApp {
    public static void main(String[] args) {
        SpringApplication.run(RestClientApp.class, args);
    }
}

// Shared customizer — applies to all RestClient.Builder instances
@Configuration
class HttpConfig {

    @Bean
    public RestClientCustomizer loggingCustomizer() {
        return builder -> builder.requestInterceptor((request, body, execution) -> {
            System.out.println("→ " + request.getMethod() + " " + request.getURI());
            var response = execution.execute(request, body);
            System.out.println("← " + response.getStatusCode());
            return response;
        });
    }
}

record Post(int id, String title, String body) {}

@Service
class PostService {

    private final RestClient restClient;

    PostService(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("https://jsonplaceholder.typicode.com")
                .build();
    }

    public Post fetchPost(int id) {
        return restClient.get()
                .uri("/posts/{id}", id)
                .retrieve()
                .body(Post.class);   // blocking — returns the deserialized body
    }
}

@RestController
class PostController {

    private final PostService postService;

    PostController(PostService postService) { this.postService = postService; }

    @GetMapping("/posts/{id}")
    public Post getPost(@PathVariable int id) {
        return postService.fetchPost(id);
    }
}
```

**How to run:** start the app (needs internet), then `curl http://localhost:8080/posts/1`. Watch the console for the outgoing request log from the interceptor.

## 6. Walkthrough

- `RestClientCustomizer` adds a `requestInterceptor` — the functional callback equivalent of `RestTemplate`'s `ClientHttpRequestInterceptor`. It logs the method, URI, and response status for every request.
- `PostService` injects `RestClient.Builder` (prototype). `.baseUrl(...)` sets the base URL; `.build()` produces an immutable `RestClient`. The logging interceptor is already applied from the customizer.
- `.get().uri("/posts/{id}", id)` builds the request. URI template variables work identically to `RestTemplate.getForObject(url, type, vars)`.
- `.retrieve().body(Post.class)` executes the request synchronously (blocks until the response arrives) and deserialises the JSON body to `Post` using Jackson.
- `Post` is a Java record — Jackson deserialises it via constructor. Records work out of the box with the auto-configured `ObjectMapper`.
- Error responses (4xx, 5xx) throw `HttpClientErrorException` or `HttpServerErrorException` by default — catchable and inspectable.

## 7. Gotchas & takeaways

> `RestClient.Builder` is a **prototype** bean. If you inject it into a singleton service, Spring creates a fresh builder instance each time the service is created (once at startup). Don't call `.build()` inside request-handling code — build once and store the `RestClient` as a field.

> `RestClient` is synchronous. Each call blocks the calling thread. In Spring MVC that's fine; in a WebFlux app it would block the event loop — use `WebClient` there instead.

- `RestClientCustomizer` vs `RestTemplateCustomizer`: both exist in Spring Boot; they target different clients. Don't confuse them.
- `requestInterceptors` replace request body; use `requestInitializer` for headers only (no body access needed).
- Add connection/read timeouts via the underlying `ClientHttpRequestFactory` (e.g. `SimpleClientHttpRequestFactory.setConnectTimeout`).
- Spring Boot 3.2 also auto-configures the builder for `spring-boot-starter-web` apps — no WebFlux dependency needed.
