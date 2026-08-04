---
card: system-design
gi: 31
slug: server-sent-events-with-spring-webflux
title: Server-Sent Events with Spring WebFlux
---

## 1. What it is

**Spring WebFlux** is Spring's reactive, non-blocking web framework. It provides built-in support for **Server-Sent Events (SSE)** — the one-directional, server-push protocol covered earlier in this section — by letting a controller method return a reactive stream type, `Flux<T>`, which Spring automatically encodes as an SSE event stream, handling the `text/event-stream` formatting for you.

## 2. Why & when

Implementing SSE by hand means manually managing an open HTTP response and writing correctly formatted `data: ...\n\n` text to it over time, as shown in the earlier SSE tutorial's simulation. Spring WebFlux removes that manual work: you simply return a `Flux` (a reactive stream of values over time) from a controller method, and the framework handles connection lifecycle, formatting, and backpressure. You reach for this whenever you are building an SSE endpoint inside a Spring application and want to avoid manually managing the streaming response.

## 3. Core concept

**The core mapping:** a controller method annotated `@GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)` returns a `Flux<T>`. Each value the `Flux` emits becomes one SSE event, automatically serialized (commonly to JSON) and wrapped in the `data: ...\n\n` format the SSE protocol requires.

```java
@GetMapping(value = "/prices", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<PriceUpdate> streamPrices() {
    return Flux.interval(Duration.ofSeconds(1))
        .map(tick -> new PriceUpdate(fetchLatestPrice()));
}
```

**Why the reactive `Flux` type fits SSE naturally:** SSE is fundamentally "a stream of values arriving over time", which is exactly what `Flux<T>` represents in Spring's reactive programming model. The framework subscribes to the `Flux` on the client's behalf and writes each emitted item to the open HTTP connection as it arrives — you never touch the raw HTTP response or manage the connection's open/close lifecycle yourself.

**How this fits the layered flow:** the controller's `Flux`-returning method typically wraps a `Flux` produced by the service layer — perhaps derived from a message queue, a scheduled poll of a data source, or another reactive stream — keeping the same controller → service layering used elsewhere in a Spring application, just with a stream of values instead of a single response.

**Non-blocking end to end:** because WebFlux is non-blocking, holding many concurrent SSE connections open does not tie up one thread per connection the way a traditional blocking servlet container would — this matters at scale, when many clients are subscribed to live streams simultaneously.

## 4. Diagram

```
 Client                              Spring WebFlux Controller
   |--GET /prices, Accept: SSE------>|
   |<--200 OK text/event-stream-------|
   |                                   |  Flux<PriceUpdate>
   |<-- data: {"price":101.5}\n\n ----|<--- emits value 1
   |<-- data: {"price":102.0}\n\n ----|<--- emits value 2
   |<-- data: {"price":101.8}\n\n ----|<--- emits value 3
   (connection stays open; each emitted Flux value becomes one SSE event)
```
*Caption: each value the Flux emits is automatically framed as one SSE event and written to the still-open response.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling how a Flux's emitted values become formatted SSE events

```java
import java.util.*;
import java.util.function.*;

public class WebfluxSseDemo {

    record PriceUpdate(double price) {}

    // Stands in for Spring's Flux: a sequence of values produced over time,
    // each one handed to a consumer as it is emitted.
    static void simulatedFlux(List<PriceUpdate> values, Consumer<PriceUpdate> onNext) {
        for (PriceUpdate v : values) {
            onNext.accept(v);
        }
    }

    // Stands in for what Spring WebFlux does automatically for a
    // Flux<T> returned from an SSE-producing controller method.
    static String toSseEvent(PriceUpdate update) {
        return "data: {\"price\":" + update.price() + "}\n\n";
    }

    public static void main(String[] args) {
        System.out.println("GET /prices  Accept: text/event-stream");
        System.out.println("200 OK  Content-Type: text/event-stream");

        List<PriceUpdate> priceStream = List.of(
            new PriceUpdate(101.5),
            new PriceUpdate(102.0),
            new PriceUpdate(101.8)
        );

        simulatedFlux(priceStream, update -> {
            String event = toSseEvent(update);
            System.out.print(event); // simulates writing to the still-open response
        });
    }
}
```

**How to run:** save as `WebfluxSseDemo.java`, run `java WebfluxSseDemo.java` (JDK 17+). A real Spring WebFlux endpoint needs the `spring-boot-starter-webflux` dependency and returns an actual `reactor.core.publisher.Flux<T>`; this example models the same emit-and-format behavior with plain Java so it runs standalone.

## 6. Walkthrough

1. `simulatedFlux` stands in for Reactor's real `Flux<T>`: it represents a sequence of values that arrive one at a time, each handed off to a consumer callback as it is produced — this is the same shape as a controller's returned `Flux` being consumed internally by Spring WebFlux.
2. `toSseEvent` formats one value into the exact `data: ...\n\n` text the SSE protocol requires — the transformation Spring WebFlux performs automatically for you when a controller returns `Flux<T>` with the `TEXT_EVENT_STREAM_VALUE` media type.
3. `main` prints the initial request/response headers, then feeds three simulated price updates through `simulatedFlux`, printing each one as a formatted SSE event as it is "emitted".
4. Output:
```
GET /prices  Accept: text/event-stream
200 OK  Content-Type: text/event-stream
data: {"price":101.5}

data: {"price":102.0}

data: {"price":101.8}

```
5. This is exactly the output a real Spring WebFlux SSE endpoint produces on the wire — the difference is that in the real framework, you never write the `data: ...\n\n` formatting yourself; you just emit typed Java objects from a `Flux`, and Spring WebFlux performs this exact transformation automatically.

## 7. Gotchas & takeaways

> **Gotcha:** mixing blocking calls (like a traditional JDBC database call) inside a `Flux`-producing method in a WebFlux application. Because WebFlux relies on a small number of threads handling many concurrent connections non-blockingly, a single blocking call inside that pipeline can stall other requests sharing the same thread — use a reactive data access approach, or offload blocking calls to a separate thread pool.

- Return `Flux<T>` from a controller method with `produces = TEXT_EVENT_STREAM_VALUE`; Spring WebFlux handles the SSE formatting and connection lifecycle automatically.
- Each value the `Flux` emits becomes exactly one SSE event on the wire.
- WebFlux's non-blocking model is well suited to holding many concurrent SSE connections open without one dedicated thread per connection — but keep the entire pipeline non-blocking to get that benefit.
