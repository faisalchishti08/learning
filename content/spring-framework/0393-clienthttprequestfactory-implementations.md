---
card: spring-framework
gi: 393
slug: clienthttprequestfactory-implementations
title: "ClientHttpRequestFactory implementations"
---

## 1. What it is

`ClientHttpRequestFactory` is the interface that decides *how* `RestTemplate` and `RestClient` actually open and send an HTTP connection — it abstracts away the underlying HTTP library. Spring ships several implementations backed by different HTTP engines (the plain JDK client, Apache HttpClient 5, Jetty's client, and others), each with different performance characteristics and configuration options, but all interchangeable behind the same factory interface.

```java
ClientHttpRequestFactory factory =
        ClientHttpRequestFactories.get(ClientHttpRequestFactorySettings.defaults()
                .withConnectTimeout(Duration.ofSeconds(2))
                .withReadTimeout(Duration.ofSeconds(5)));

RestTemplate restTemplate = new RestTemplate(factory);
```

## 2. Why & when

Since `RestTemplate`/`RestClient` delegate actual socket handling to a `ClientHttpRequestFactory`, swapping the factory changes the client's networking behavior without touching any calling code. This matters because the JDK's built-in `HttpURLConnection`-based factory (the silent default) has real limitations: no connection pooling by default, and awkward configuration for timeouts and proxies compared to a dedicated HTTP library.

Common implementations:

- **`SimpleClientHttpRequestFactory`** — wraps `java.net.HttpURLConnection`. Zero extra dependencies, adequate for simple or low-volume use, but no connection pooling.
- **`HttpComponentsClientHttpRequestFactory`** — wraps Apache HttpClient 5. Supports connection pooling, fine-grained timeout control, and proxy/auth configuration; the most common production choice for `RestTemplate`/`RestClient`.
- **`JettyClientHttpRequestFactory`** — wraps Jetty's `HttpClient`, useful when a project already depends on Jetty elsewhere.
- **`JdkClientHttpRequestFactory`** — wraps the newer `java.net.http.HttpClient` (Java 11+), which supports HTTP/2 without extra dependencies.

Choose based on what you need: pick Apache HttpClient 5 when you need pooling and detailed control (the common case), the JDK `HttpClient` when you want HTTP/2 with zero extra dependencies, and the simple factory only for the smallest use cases where a dependency isn't worth adding.

## 3. Core concept

```
RestTemplate / RestClient
        |
        | delegates connection creation to
        v
 ClientHttpRequestFactory  (interface)
        |
   -----+------------------------------
   |            |              |
Simple      HttpComponents   Jdk / Jetty
(JDK conn)  (Apache HC5)      (java.net.http / Jetty)
```

Every concrete factory implements the same `createRequest(URI, HttpMethod)` method; `RestTemplate`/`RestClient` never know or care which one is plugged in, which is what makes swapping them at configuration time possible with no code changes elsewhere.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestTemplate delegates to a pluggable ClientHttpRequestFactory implementation">
  <rect x="230" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">RestTemplate/RestClient</text>

  <rect x="230" y="90" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="117" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ClientHttpRequestFactory</text>

  <rect x="20" y="160" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SimpleClientHttp...</text>

  <rect x="250" y="160" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="325" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HttpComponents...</text>

  <rect x="470" y="160" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Jdk / Jetty...</text>

  <line x1="320" y1="64" x2="320" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="270" y1="134" x2="120" y2="158" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="134" x2="325" y2="158" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="370" y1="134" x2="530" y2="158" stroke="#8b949e" stroke-width="1.5"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Any of the three implementations plugs into the same `RestTemplate`/`RestClient` without changing calling code.

## 5. Runnable example

### Level 1 — Basic

The default: no factory specified, so `RestTemplate` uses `SimpleClientHttpRequestFactory` implicitly.

```java
import org.springframework.web.client.RestTemplate;

public class FactoryBasic {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate(); // implicit SimpleClientHttpRequestFactory

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: `java FactoryBasic.java` with `spring-web` and Jackson on the classpath.

Nothing about timeouts or pooling is configured here — this is what almost every "hello world" `RestTemplate` example uses, and it's also what silently causes hangs in production when the target server stalls.

### Level 2 — Intermediate

Explicitly configure timeouts using the JDK's own `HttpClient`-backed factory, showing that behavior changes purely from factory choice.

```java
import org.springframework.boot.web.client.ClientHttpRequestFactories;
import org.springframework.boot.web.client.ClientHttpRequestFactorySettings;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

public class FactoryIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        var settings = ClientHttpRequestFactorySettings.defaults()
                .withConnectTimeout(Duration.ofSeconds(2))
                .withReadTimeout(Duration.ofSeconds(3));

        var factory = ClientHttpRequestFactories.get(settings); // picks best available factory

        RestTemplate restTemplate = new RestTemplate(factory);
        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: run inside a Spring Boot project (`spring-boot-starter-web`) so `ClientHttpRequestFactories` is available, then execute `FactoryIntermediate.main`.

`ClientHttpRequestFactories.get(settings)` auto-detects the best factory available on the classpath (preferring Apache HttpClient 5 if present, otherwise falling back to the JDK client) and applies the timeouts uniformly — the calling code (`getForObject`) is completely unchanged from Level 1.

### Level 3 — Advanced

Production systems calling many downstream services need connection pooling, not just timeouts — explicitly configuring Apache HttpClient 5 with a pooling connection manager avoids opening a new TCP connection for every request.

```java
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.util.Timeout;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

public class FactoryAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        var connectionManager = new PoolingHttpClientConnectionManager();
        connectionManager.setMaxTotal(100);
        connectionManager.setDefaultMaxPerRoute(20);

        var httpClient = HttpClients.custom()
                .setConnectionManager(connectionManager)
                .build();

        var factory = new HttpComponentsClientHttpRequestFactory(httpClient);
        factory.setConnectTimeout(2000);

        RestTemplate restTemplate = new RestTemplate(factory);

        for (int i = 1; i <= 3; i++) {
            TodoItem todoItem = restTemplate.getForObject(
                    "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, i);
            System.out.println("Reused pooled connection for todoItem " + i + ": " + todoItem.title());
        }
    }
}
```

How to run: add `org.apache.httpcomponents.client5:httpclient5` to the classpath, then `java FactoryAdvanced.java`.

`PoolingHttpClientConnectionManager` keeps up to 100 total connections and up to 20 per route (per host) open and reusable, so the three sequential `getForObject` calls to the same host reuse an already-open connection instead of paying TCP/TLS handshake cost each time — the payoff scales with the number of calls an application makes over its lifetime.

## 6. Walkthrough

Trace `FactoryAdvanced.main` for the loop's second iteration (`i = 2`), where a connection already exists from the first:

1. **First call (i=1) already ran.** `PoolingHttpClientConnectionManager` opened a TCP connection to `jsonplaceholder.typicode.com`, completed the TLS handshake, sent `GET /todos/1`, read the response, and — because Apache HttpClient 5 keeps connections alive by default — returned the connection to the pool instead of closing it.
2. **Second call begins.** `restTemplate.getForObject(..., 2)` calls into `HttpComponentsClientHttpRequestFactory.createRequest(...)`, which asks the pooling connection manager for a connection to the same route (host+port+scheme).
3. **Pool hit.** The manager finds the idle connection from step 1 still open and valid, and leases it back out — no new TCP handshake, no new TLS negotiation.
4. **Request sent on the reused connection.**

   ```
   Request:  GET /todos/2 HTTP/1.1
             Host: jsonplaceholder.typicode.com
             Connection: keep-alive

   Response: HTTP/1.1 200 OK
             Connection: keep-alive

             {"userId":1,"id":2,"title":"quis ut nam...","completed":false}
   ```
5. **Response processed.** The body is converted to a `TodoItem` record exactly as with any other factory — factory choice only affects *how the bytes get there*, never how they're interpreted.
6. **Connection returned to pool again.** After the response completes, the connection goes back to the pool for the third iteration to reuse.

```
i=1: open TCP+TLS -> send -> recv -> keep connection in pool
i=2: reuse pooled connection -> send -> recv -> keep in pool
i=3: reuse pooled connection -> send -> recv -> keep in pool
```

Without pooling (`SimpleClientHttpRequestFactory`), each iteration would pay the TCP/TLS setup cost again — invisible in a 3-call demo, significant at production request volumes.

## 7. Gotchas & takeaways

> Gotcha: swapping in `HttpComponentsClientHttpRequestFactory` without configuring a `PoolingHttpClientConnectionManager` still creates a real HTTP client, but Apache HttpClient 5's *default* connection manager already pools modestly — the mistake to watch for is the opposite direction, sticking with the zero-configuration `SimpleClientHttpRequestFactory` in a high-throughput service and never noticing the missing pooling until latency investigations turn up constant TCP handshakes.

- `ClientHttpRequestFactory` is the seam that decides which underlying HTTP engine `RestTemplate`/`RestClient` actually uses — configure it once at startup, and every call through that client benefits.
- Prefer `HttpComponentsClientHttpRequestFactory` (Apache HttpClient 5) for production services that make many outbound calls, for its pooling and fine-grained control.
- Always set explicit connect and read/response timeouts on whichever factory you choose — none of the defaults are safe for production.
- `WebClient` has an equivalent seam (`ClientHttpConnector`, usually Reactor Netty) for the same reason: to decouple the fluent API from the underlying transport.
