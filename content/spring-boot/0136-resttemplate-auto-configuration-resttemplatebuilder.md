---
card: spring-boot
gi: 136
slug: resttemplate-auto-configuration-resttemplatebuilder
title: RestTemplate auto-configuration (RestTemplateBuilder)
---

## 1. What it is

`RestTemplate` is Spring's classic synchronous HTTP client, used for making outbound REST calls. Spring Boot does **not** auto-configure a `RestTemplate` bean directly — instead it auto-configures a `RestTemplateBuilder` bean that lets you create a `RestTemplate` with consistent, app-wide settings. `RestTemplateCustomizer` beans apply shared configuration (timeouts, interceptors, message converters) to every builder instance.

## 2. Why & when

Spring Boot deliberately avoids a single shared `RestTemplate` bean because `RestTemplate` is not thread-safe after construction — each service typically needs its own instance with its own base URL, error handler, or interceptors. The builder pattern solves this cleanly: inject the builder, configure your service's specifics, call `.build()`.

Use `RestTemplateBuilder` (and `RestTemplate`) when:

- Your app is on Spring Boot < 3.2 and you need synchronous HTTP calls.
- You're maintaining existing code that already uses `RestTemplate`.
- You want the simplest blocking HTTP client with no extra dependency.

For new code on Spring Boot 3.2+, prefer `RestClient` — same synchronous model, cleaner API. For reactive apps, use `WebClient`.

## 3. Core concept

`RestTemplateAutoConfiguration` creates one `RestTemplateBuilder` prototype bean. The builder picks up all `RestTemplateCustomizer` beans registered in the application context and applies them before each `.build()` call.

```
application.properties (connection-timeout etc.)
  ↓
RestTemplateBuilder (prototype, customizers applied)
  ↓ .rootUri("https://api.example.com") .build()
RestTemplate (your service's instance)
```

Key builder methods:

| Method | Purpose |
|---|---|
| `.rootUri(url)` | Base URL prepended to all paths |
| `.defaultHeader(name, value)` | Default request header |
| `.setConnectTimeout(duration)` | TCP connection timeout |
| `.setReadTimeout(duration)` | Read timeout |
| `.interceptors(...)` | `ClientHttpRequestInterceptor` list |
| `.messageConverters(...)` | Replace or add `HttpMessageConverter` |

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="165" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="102" y="105" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">RestTemplateCustomizer</text>
  <text x="102" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">beans</text>
  <rect x="260" y="80" width="165" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="342" y="105" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">RestTemplateBuilder</text>
  <text x="342" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(prototype)</text>
  <rect x="500" y="60" width="155" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="87" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">RestTemplate A</text>
  <rect x="500" y="120" width="155" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="147" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">RestTemplate B</text>
  <line x1="187" y1="110" x2="256" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rt)"/>
  <line x1="427" y1="97" x2="496" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rt2)"/>
  <line x1="427" y1="123" x2="496" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rt2)"/>
  <defs>
    <marker id="rt" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rt2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Customizer beans configure the shared builder; each service injects the builder prototype and calls `.build()` for its own `RestTemplate`.

## 5. Runnable example

```java
// RestTemplateApp.java  —  Spring Boot project with spring-boot-starter-web
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.boot.web.client.RestTemplateCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@SpringBootApplication
public class RestTemplateApp {
    public static void main(String[] args) {
        SpringApplication.run(RestTemplateApp.class, args);
    }
}

@Configuration
class ClientConfig {

    // Shared customizer: applies to every RestTemplate built from the builder
    @Bean
    public RestTemplateCustomizer loggingCustomizer() {
        ClientHttpRequestInterceptor interceptor = (request, body, execution) -> {
            System.out.println("→ " + request.getMethod() + " " + request.getURI());
            return execution.execute(request, body);
        };
        return builder -> builder.additionalInterceptors(interceptor);
    }
}

record Post(int id, String title, String body) {}

@Service
class PostClient {

    private final RestTemplate restTemplate;

    PostClient(RestTemplateBuilder builder) {
        this.restTemplate = builder
                .rootUri("https://jsonplaceholder.typicode.com")
                .setConnectTimeout(Duration.ofSeconds(3))
                .setReadTimeout(Duration.ofSeconds(5))
                .build();
    }

    public Post fetchPost(int id) {
        return restTemplate.getForObject("/posts/{id}", Post.class, id);
    }
}

@RestController
class PostApi {

    private final PostClient client;

    PostApi(PostClient client) { this.client = client; }

    @GetMapping("/posts/{id}")
    public Post post(@PathVariable int id) {
        return client.fetchPost(id);
    }
}
```

**How to run:** start the app (needs internet), then `curl http://localhost:8080/posts/1`. The console shows the intercepted outgoing HTTP request log.

## 6. Walkthrough

- `RestTemplateCustomizer` returns a lambda that receives a `RestTemplateBuilder`. `additionalInterceptors(interceptor)` adds the logging interceptor to every builder that Spring Boot creates — no matter which service builds from it.
- `PostClient` injects `RestTemplateBuilder` (prototype — fresh copy). `.rootUri(...)` sets the base URL (prepended to relative paths). `.setConnectTimeout` and `.setReadTimeout` set the underlying `ClientHttpRequestFactory` timeouts via `SimpleClientHttpRequestFactory` by default.
- `.build()` produces the `RestTemplate` with the logging interceptor already wired in from the customizer.
- `restTemplate.getForObject("/posts/{id}", Post.class, id)` sends a `GET` request, deserialises the JSON response to `Post` using Jackson (auto-configured `MappingJackson2HttpMessageConverter`), and returns the object — blocking until complete.
- URI template expansion in `getForObject` replaces `{id}` with the actual value — safe, no manual string concatenation.

## 7. Gotchas & takeaways

> Do NOT inject `RestTemplateBuilder` and call `.build()` inside a request-handling method on every call — that creates a new `RestTemplate` (and possibly a new connection pool) on every HTTP request. Build once at service construction time and store it as a field.

> `RestTemplate` is not officially deprecated but marked as "in maintenance mode" in Spring 6. It receives bug fixes but no new features — prefer `RestClient` for new Spring Boot 3.2+ code.

- Spring Boot does not create a `RestTemplate` `@Bean` automatically — you must call `builder.build()` yourself.
- `RestTemplateCustomizer` is the shared hook; `RestTemplateBuilder` methods are per-instance. Use customizers for cross-cutting concerns (auth, logging); use builder methods for per-service config (base URL, timeouts).
- To use a different `ClientHttpRequestFactory` (OkHttp, Apache HttpClient), call `builder.requestFactory(supplier)` — the factory is then shared.
- Error handling: `HttpClientErrorException` (4xx) and `HttpServerErrorException` (5xx) are thrown by default; replace with `builder.errorHandler(...)` for custom handling.
