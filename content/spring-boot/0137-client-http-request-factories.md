---
card: spring-boot
gi: 137
slug: client-http-request-factories
title: Client HTTP request factories
---

## 1. What it is

A **`ClientHttpRequestFactory`** is the low-level networking layer underneath `RestTemplate` and `RestClient`. It creates the actual HTTP connections. Spring ships several implementations, each backed by a different HTTP library: `SimpleClientHttpRequestFactory` (JDK's `HttpURLConnection`), `JdkClientHttpRequestFactory` (JDK 11+ `HttpClient`), `HttpComponentsClientHttpRequestFactory` (Apache HttpClient 5), and `OkHttp3ClientHttpRequestFactory` (OkHttp 3). Spring Boot auto-selects the best available factory on the classpath.

## 2. Why & when

The default `SimpleClientHttpRequestFactory` works for basic use cases but lacks:

- Connection pooling.
- Fine-grained timeout and TLS control.
- HTTP/2 support.
- Proxy authentication.

Switch to Apache HttpClient 5 or OkHttp when you need connection pooling (high-throughput services), mutual TLS, or HTTP/2 on the client side. Switch to `JdkClientHttpRequestFactory` (JDK 11+) for a zero-dependency option with built-in HTTP/2 and virtual-thread support.

## 3. Core concept

`ClientHttpRequestFactory` is a functional-like interface:

```java
ClientHttpRequest createRequest(URI uri, HttpMethod httpMethod) throws IOException;
```

`RestTemplate` and `RestClient` use it to open connections. You swap factories by passing a new one to the builder:

```java
RestClient.builder()
    .requestFactory(new HttpComponentsClientHttpRequestFactory(httpClient))
    .build();
```

Spring Boot 3.2+ includes `ClientHttpRequestFactories` utility class with factory methods for each implementation, applying timeouts automatically.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="85" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="115" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">RestTemplate / RestClient</text>
  <rect x="245" y="50" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="332" y="74" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">SimpleClientHttp…Factory</text>
  <rect x="245" y="100" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="332" y="124" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">HttpComponentsClientHttp…</text>
  <rect x="245" y="150" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="332" y="168" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">JdkClientHttpRequest…</text>
  <rect x="245" y="198" width="175" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="332" y="217" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">OkHttp3ClientHttp…</text>
  <rect x="505" y="90" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="582" y="120" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Network (TCP/TLS)</text>
  <line x1="162" y1="110" x2="241" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cf)"/>
  <line x1="162" y1="110" x2="241" y2="120" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#cf2)"/>
  <line x1="162" y1="110" x2="241" y2="170" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#cf2)"/>
  <line x1="422" y1="120" x2="501" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cf3)"/>
  <defs>
    <marker id="cf" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cf2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="cf3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`RestTemplate`/`RestClient` delegates connection creation to whichever `ClientHttpRequestFactory` you configure; all factories implement the same interface.

## 5. Runnable example

```java
// RequestFactoryApp.java  —  Spring Boot 3.2+ project with spring-boot-starter-web
// Add to pom.xml:
//   <dependency>
//     <groupId>org.apache.httpcomponents.client5</groupId>
//     <artifactId>httpclient5</artifactId>
//   </dependency>

import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@SpringBootApplication
public class RequestFactoryApp {
    public static void main(String[] args) {
        SpringApplication.run(RequestFactoryApp.class, args);
    }
}

@Configuration
class ApacheHttpConfig {

    @Bean
    public RestClient pooledRestClient() {
        // Connection pool: max 100 total, max 20 per route
        PoolingHttpClientConnectionManager cm = new PoolingHttpClientConnectionManager();
        cm.setMaxTotal(100);
        cm.setDefaultMaxPerRoute(20);

        var httpClient = HttpClients.custom()
                .setConnectionManager(cm)
                .build();

        return RestClient.builder()
                .requestFactory(new HttpComponentsClientHttpRequestFactory(httpClient))
                .baseUrl("https://jsonplaceholder.typicode.com")
                .build();
    }
}

@RestController
class UserController {

    private final RestClient restClient;

    UserController(RestClient restClient) { this.restClient = restClient; }

    @GetMapping("/user")
    public String user() {
        return restClient.get()
                .uri("/users/1")
                .retrieve()
                .body(String.class);
    }
}
```

**How to run:** add `httpclient5` dependency, start the app, then `curl http://localhost:8080/user`. The pooled Apache HttpClient handles the outbound connection.

## 6. Walkthrough

- `PoolingHttpClientConnectionManager` gives Apache HttpClient 5 a connection pool: up to 100 total connections and 20 connections per remote host. Without pooling, each request opens and closes a TCP connection, adding latency and load.
- `HttpClients.custom().setConnectionManager(cm).build()` creates an `CloseableHttpClient` using the pool. The client is thread-safe and meant to be shared.
- `new HttpComponentsClientHttpRequestFactory(httpClient)` wraps the Apache client as a Spring `ClientHttpRequestFactory`. `RestClient.builder().requestFactory(...)` installs it.
- `RestClient` is declared as a `@Bean` — a singleton. It is immutable and thread-safe; safe to share across controllers.
- `.retrieve().body(String.class)` returns the raw JSON string. In a real service you'd deserialise to a typed record.
- To use JDK's `HttpClient` instead: `new JdkClientHttpRequestFactory(HttpClient.newHttpClient())` — zero extra dependencies, supports HTTP/2 and virtual threads.

## 7. Gotchas & takeaways

> `SimpleClientHttpRequestFactory` has **no connection pool**. Under load, each request opens a new TCP connection. This is the default for `RestTemplate` — always replace it with a pooled factory for production services.

> Close the `CloseableHttpClient` (or connection manager) when the application shuts down — otherwise leaked file descriptors accumulate. Register a `DisposableBean` or use `@PreDestroy` to close it.

- Spring Boot 3.2 `ClientHttpRequestFactories.get(settings)` is a utility that picks the best available factory based on the classpath and applies timeout settings without manual factory construction.
- `OkHttp3ClientHttpRequestFactory` (OkHttp) is an alternative to Apache; it has its own connection pool and is popular in Android-inspired stacks.
- For `WebClient`, the underlying factory is different: `ReactorClientHttpConnector` (Reactor Netty) — not `ClientHttpRequestFactory`.
- `BufferingClientHttpRequestFactory` wraps another factory to allow repeated reading of the response body (e.g. in interceptors for logging) — at the cost of buffering the entire response in memory.
