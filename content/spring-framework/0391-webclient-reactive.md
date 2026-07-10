---
card: spring-framework
gi: 391
slug: webclient-reactive
title: "WebClient (reactive)"
---

## 1. What it is

`WebClient` is Spring's non-blocking, reactive HTTP client, part of the Spring WebFlux module. It has the same fluent, chainable API shape as `RestClient` (method, URI, headers, body, then a terminal call), but instead of blocking the calling thread and returning a plain value, every terminal call returns a `Mono<T>` or `Flux<T>` that only does work once someone subscribes to it.

```java
WebClient client = WebClient.create("https://api.example.com");

Mono<Product> product = client.get()
        .uri("/products/{id}", 42)
        .retrieve()
        .bodyToMono(Product.class);
```

## 2. Why & when

`WebClient` exists because a blocking client like `RestTemplate` or `RestClient` ties up one thread per in-flight HTTP call — fine at low concurrency, wasteful when a service needs to fan out hundreds of concurrent downstream calls (the classic reactive-programming motivation covered in the reactive programming overview card). `WebClient` uses a small pool of event-loop threads and never blocks waiting for I/O, so it scales to far more concurrent outbound calls per thread.

Reach for `WebClient` when:

- You're already inside a Spring WebFlux (reactive) application and need to call other services without blocking the event loop.
- You need to make many concurrent outbound calls efficiently (e.g., an API gateway fanning out to several backend services and combining results).
- You want streaming support — consuming a `Flux` of server-sent events or a large JSON array incrementally instead of buffering the whole response.

If your application is a classic blocking Spring MVC app, prefer `RestClient` — introducing `WebClient` there just adds Reactor's learning curve without a concurrency benefit, since the calling thread blocks on `.block()` anyway.

## 3. Core concept

```
WebClient.create()
     |
     v
 .get()/.post()/...   <- choose HTTP method
     |
     v
 .uri("/path/{id}", id)
     |
     v
 .retrieve()            <- returns ResponseSpec (still lazy)
     |
     v
 .bodyToMono(Type.class) / .bodyToFlux(Type.class)   <- returns Mono/Flux (still lazy!)
     |
     v
 .subscribe() / .block()  <- ONLY here does the HTTP call actually fire
```

Nothing happens on the network until something subscribes to the returned `Mono`/`Flux` — building the request is just assembling a description of work to do later, which is the core reactive principle from the Project Reactor card.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebClient chain stays lazy until subscription triggers the actual HTTP call">
  <rect x="10" y="30" width="150" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="57" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.get().uri(...)</text>

  <rect x="200" y="30" width="150" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="275" y="57" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.retrieve()</text>

  <rect x="390" y="30" width="220" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="57" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.bodyToMono(Product.class)</text>

  <text x="320" y="100" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">^ all of the above is LAZY — nothing sent yet</text>

  <rect x="200" y="140" width="220" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="167" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.subscribe(...) triggers call</text>

  <line x1="160" y1="52" x2="195" y2="52" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="350" y1="52" x2="385" y2="52" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="500" y1="74" x2="330" y2="138" stroke="#3fb950" stroke-width="2" marker-end="url(#b)"/>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Building the request chain is free; only `subscribe()` (or `.block()`, which subscribes internally) sends bytes on the wire.

## 5. Runnable example

### Level 1 — Basic

A minimal reactive call, blocked at the very end only so `main` can print a result before the JVM exits.

```java
import org.springframework.web.reactive.function.client.WebClient;

public class WebClientBasic {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        WebClient client = WebClient.create("https://jsonplaceholder.typicode.com");

        TodoItem todoItem = client.get()
                .uri("/todos/{id}", 1)
                .retrieve()
                .bodyToMono(TodoItem.class)
                .block();  // only acceptable here: main() has no other way to wait

        System.out.println(todoItem);
    }
}
```

How to run: add `spring-webflux` and `reactor-netty` (or run inside a Spring Boot project with `spring-boot-starter-webflux`) to the classpath, then `java WebClientBasic.java`.

`bodyToMono(TodoItem.class)` returns a `Mono<TodoItem>` describing "fetch and deserialize this TodoItem" without doing it yet. `.block()` subscribes and waits synchronously — acceptable in a throwaway `main` method, but exactly what you'd avoid inside a real reactive pipeline.

### Level 2 — Intermediate

Real code stays non-blocking end-to-end: it composes the `Mono` with `.map()`/`.flatMap()` and subscribes asynchronously, and it handles error status codes explicitly.

```java
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.util.concurrent.CountDownLatch;

public class WebClientIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) throws InterruptedException {
        WebClient client = WebClient.create("https://jsonplaceholder.typicode.com");
        CountDownLatch done = new CountDownLatch(1);

        Mono<String> titleUpperCase = client.get()
                .uri("/todos/{id}", 1)
                .retrieve()
                .onStatus(status -> status.is4xxClientError(),
                        response -> Mono.error(new IllegalStateException("TodoItem not found")))
                .bodyToMono(TodoItem.class)
                .map(todoItem -> todoItem.title().toUpperCase());

        titleUpperCase.subscribe(
                value -> { System.out.println("Result: " + value); done.countDown(); },
                error -> { System.err.println("Failed: " + error.getMessage()); done.countDown(); }
        );

        done.await();  // demo-only: real apps let the reactive pipeline drive the response
    }
}
```

How to run: `java WebClientIntermediate.java` (same classpath as Level 1).

`.onStatus(...)` converts a 4xx status into a `Mono.error`, which short-circuits the pipeline before `bodyToMono` runs. `.map()` transforms the emitted `TodoItem` without blocking. `.subscribe(onNext, onError)` starts the whole chain asynchronously — the `CountDownLatch` exists only so this demo `main` method doesn't exit before the async callback fires.

### Level 3 — Advanced

Production `WebClient` usage typically needs timeouts, retries for transient failures, and combining multiple concurrent calls — all without blocking a thread per call.

```java
import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.CountDownLatch;

public class WebClientAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) throws InterruptedException {
        HttpClient nettyClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 2000)
                .doOnConnected(conn -> conn.addHandlerLast(new ReadTimeoutHandler(2)));

        WebClient client = WebClient.builder()
                .baseUrl("https://jsonplaceholder.typicode.com")
                .clientConnector(new ReactorClientHttpConnector(nettyClient))
                .build();

        CountDownLatch done = new CountDownLatch(1);

        Mono<TodoItem> firstTodo = client.get().uri("/todos/1").retrieve().bodyToMono(TodoItem.class);
        Mono<TodoItem> secondTodo = client.get().uri("/todos/2").retrieve().bodyToMono(TodoItem.class);

        Mono.zip(firstTodo, secondTodo)
                .retryWhen(Retry.backoff(3, Duration.ofMillis(200))
                        .filter(ex -> !(ex instanceof IllegalStateException)))
                .subscribe(
                        tuple -> {
                            System.out.println("first=" + tuple.getT1());
                            System.out.println("second=" + tuple.getT2());
                            done.countDown();
                        },
                        error -> { System.err.println("Failed after retries: " + error); done.countDown(); }
                );

        done.await();
    }
}
```

How to run: add `reactor-netty` (already transitively pulled by `spring-boot-starter-webflux`) to the classpath, then `java WebClientAdvanced.java`.

`ReadTimeoutHandler`/`CONNECT_TIMEOUT_MILLIS` are configured on the underlying Reactor Netty `HttpClient` so slow servers fail fast instead of hanging a reactive thread. `Mono.zip` fires both `/todos/1` and `/todos/2` concurrently and completes only once both finish — neither call blocks the other. `retryWhen` with exponential backoff retries transient failures automatically, without any manual retry loop or blocked thread.

## 6. Walkthrough

Trace `WebClientAdvanced.main`:

1. **Connector setup.** A Reactor Netty `HttpClient` is configured with a 2-second connect timeout and a 2-second read timeout, then wrapped in a `ReactorClientHttpConnector` that `WebClient` uses instead of its own default connector.
2. **Two lazy `Mono`s built.** `firstTodo` and `secondTodo` each describe a `GET` request but neither has executed — building them is pure assembly, no network I/O yet.
3. **`Mono.zip` combines them.** This produces a new `Mono<Tuple2<TodoItem,TodoItem>>` that, once subscribed, will run both source `Mono`s concurrently (not sequentially) and complete when both have emitted.
4. **`retryWhen` wraps the zipped `Mono`.** This adds retry behavior around the whole combined operation, but still nothing has executed.
5. **`.subscribe(...)` triggers execution.** This is the moment both HTTP requests fire, conceptually:

   ```
   Client (event-loop thread)              Server
        |--- GET /todos/1 -------------------->|
        |--- GET /todos/2 -------------------->|  (both in flight concurrently)
        |<--- 200 OK {"id":1,...} --------------|
        |<--- 200 OK {"id":2,...} --------------|
   ```
6. **Deserialization.** Each response's JSON body is converted to a `TodoItem` by the shared Jackson message converters, same mechanism as `RestClient`/`RestTemplate`.
7. **Zip completes.** Once both `TodoItem`s have arrived, `Mono.zip` emits a `Tuple2`, which flows into the `subscribe` callback, printing both records. If either call had failed with a transient network error, `retryWhen` would have re-subscribed to the whole zipped `Mono` up to 3 times with increasing backoff before giving up.

The key structural difference from `RestClient`/`RestTemplate` is that steps 2–4 involve zero blocked threads: the calling thread returns immediately after `subscribe()` is called, and the Netty event loop delivers the result to the callback whenever the network I/O completes.

## 7. Gotchas & takeaways

> Gotcha: calling `.block()` inside a WebFlux request-handling thread (rather than in a throwaway `main` method) defeats the entire point of the reactive stack — it ties up one of the small number of event-loop threads, which can starve the server under load. Only call `.block()` at the outermost edge of a genuinely blocking application, never inside a reactive pipeline.

- `WebClient` chains are lazy: nothing is sent over the network until `.subscribe()` or `.block()` is called — building the request is free and side-effect-free.
- Use `Mono.zip`/`Flux.merge` to run independent calls concurrently instead of chaining them sequentially with `flatMap`, which would serialize them.
- Configure connect/read timeouts on the underlying `HttpClient` (Reactor Netty) — like `RestClient`/`RestTemplate`, the defaults have no timeout and a hung server can leave a subscription pending forever.
- `retryWhen(Retry.backoff(...))` gives you exponential-backoff retries in a couple of lines, something that requires manual loop code with blocking clients.
