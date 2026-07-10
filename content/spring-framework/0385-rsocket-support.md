---
card: spring-framework
gi: 385
slug: rsocket-support
title: "RSocket support"
---

## 1. What it is

RSocket is a binary, reactive application protocol (an alternative to HTTP) built from the ground up around Reactive Streams semantics, supporting four distinct interaction models — request-response, fire-and-forget, request-stream, and request-channel (bidirectional streaming) — with backpressure built into the protocol itself, not bolted on. Spring's RSocket support integrates it into the familiar `@MessageMapping`-annotated controller style, letting you write RSocket handlers with much the same ergonomics as WebFlux's `@RestController` methods.

```java
@Controller
public class ProductRSocketController {

    @MessageMapping("product.get")
    public Mono<Product> get(long id) {
        return productRepository.findById(id);
    }

    @MessageMapping("product.stream")
    public Flux<Product> stream() {
        return productRepository.findAll();
    }
}
```

## 2. Why & when

HTTP (even with WebFlux) is fundamentally a request/response protocol at its core, with SSE and WebSockets bolted on as separate mechanisms for streaming and bidirectional communication respectively. RSocket instead treats all four interaction patterns as first-class, native protocol features, with backpressure genuinely built into the wire protocol (not simulated on top of it) — this makes it a compelling choice specifically for:

- **Service-to-service communication** in a microservices architecture where you control both ends and want a protocol genuinely optimized for reactive, streaming, backpressure-aware interaction, rather than adapting HTTP semantics to fit.
- **Request-channel** (bidirectional streaming) scenarios — a client streaming a continuous flow of data to the server while simultaneously receiving a continuous flow back — which has no clean, native HTTP equivalent (WebSockets get close but lack RSocket's built-in backpressure and multiple-interaction-model structure).
- Situations where connection-level multiplexing with genuine, protocol-native backpressure matters more than HTTP's ubiquity and tooling ecosystem — RSocket is a more specialized choice, not a default replacement for HTTP-based APIs consumed by browsers or general HTTP clients.

## 3. Core concept

```
Four RSocket interaction models, each with a direct Spring annotation mapping:

  Request-Response  (1 request -> 1 response)
    @MessageMapping("route")
    public Mono<Response> handle(Request request) { ... }

  Fire-and-Forget  (1 request -> NO response at all)
    @MessageMapping("route")
    public Mono<Void> handle(Request request) { ... }

  Request-Stream  (1 request -> MANY responses, streamed)
    @MessageMapping("route")
    public Flux<Response> handle(Request request) { ... }

  Request-Channel  (MANY requests -> MANY responses, BOTH streamed, BIDIRECTIONAL)
    @MessageMapping("route")
    public Flux<Response> handle(Flux<Request> requests) { ... }

Client side — RSocketRequester (the RSocket analog to WebClient):

  requester.route("product.get").data(id).retrieveMono(Product.class)
  requester.route("product.stream").retrieveFlux(Product.class)

Backpressure: BUILT INTO THE PROTOCOL ITSELF (via RSocket's own
REQUEST_N frame type) — not simulated on top like HTTP chunked
transfer encoding + Reactive-Streams-aware libraries have to do.
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Four RSocket interaction models</text>

  <rect x="20" y="50" width="160" height="60" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="75" text-anchor="middle" fill="#6db33f" font-size="10">Request-Response</text>
  <text x="100" y="93" text-anchor="middle" fill="#8b949e" font-size="8">1 in -&gt; 1 out</text>

  <rect x="200" y="50" width="160" height="60" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="280" y="75" text-anchor="middle" fill="#79c0ff" font-size="10">Fire-and-Forget</text>
  <text x="280" y="93" text-anchor="middle" fill="#8b949e" font-size="8">1 in -&gt; 0 out</text>

  <rect x="380" y="50" width="160" height="60" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="75" text-anchor="middle" fill="#6db33f" font-size="10">Request-Stream</text>
  <text x="460" y="93" text-anchor="middle" fill="#8b949e" font-size="8">1 in -&gt; N out</text>

  <rect x="560" y="50" width="160" height="60" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="640" y="75" text-anchor="middle" fill="#79c0ff" font-size="10">Request-Channel</text>
  <text x="640" y="93" text-anchor="middle" fill="#8b949e" font-size="8">N in -&gt; N out</text>

  <text x="370" y="150" text-anchor="middle" fill="#8b949e" font-size="10">Backpressure built into the wire protocol, for EVERY model</text>

  <defs>
    <marker id="a61" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Each interaction model maps to a distinct handler method signature, chosen purely by the parameter and return types used.*

## 5. Runnable example

### Level 1 — Basic

A request-response RSocket handler and its corresponding client call:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-rsocket</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  rsocket:
    server:
      port: 7000
```

```java
// ProductRSocketController.java
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Mono;

@Controller
public class ProductRSocketController {

    record Product(long id, String name) {}

    @MessageMapping("product.get")
    public Mono<Product> get(long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

```java
// ProductRSocketClient.java — a simple standalone client, illustrating RSocketRequester
import org.springframework.messaging.rsocket.RSocketRequester;

public class ProductRSocketClient {
    record Product(long id, String name) {}

    public static void main(String[] args) {
        RSocketRequester requester = RSocketRequester.builder()
            .tcp("localhost", 7000);

        Product product = requester.route("product.get")
            .data(1L)
            .retrieveMono(Product.class)
            .block();   // acceptable ONLY in a standalone client's main(), not in reactive server code

        System.out.println("Received: " + product);
        requester.rsocket().dispose();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
# (server listening on RSocket port 7000)

java ProductRSocketClient.java
# Received: Product[id=1, name=Drill]
```

`@MessageMapping("product.get")` maps a request to a specific "route" string (RSocket's equivalent of an HTTP path) — no `@GetMapping`/`@PostMapping` distinction, since RSocket's route-based dispatch doesn't map onto HTTP verbs at all. The `Mono<Product>` return type signals request-response semantics to Spring's RSocket infrastructure.

### Level 2 — Intermediate

A request-stream handler (one request, many streamed responses) — directly analogous to a `Flux`-returning WebFlux handler, but over RSocket's protocol instead of HTTP:

```java
// ProductRSocketController.java (extended)
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Flux;

import java.time.Duration;

@Controller
public class ProductRSocketController {

    record Product(long id, String name) {}

    @MessageMapping("product.stream")
    public Flux<Product> stream() {
        return Flux.just(new Product(1, "Drill"), new Product(2, "Hammer"), new Product(3, "Nail"))
            .delayElements(Duration.ofMillis(300));
    }
}
```

```java
// ProductRSocketClient.java (extended)
import org.springframework.messaging.rsocket.RSocketRequester;
import reactor.core.publisher.Flux;

public class ProductRSocketClient {
    record Product(long id, String name) {}

    public static void main(String[] args) throws InterruptedException {
        RSocketRequester requester = RSocketRequester.builder().tcp("localhost", 7000);

        Flux<Product> products = requester.route("product.stream")
            .retrieveFlux(Product.class);

        products.subscribe(p -> System.out.println("Received: " + p));

        Thread.sleep(1500);   // let the async stream complete before the demo's main() exits
        requester.rsocket().dispose();
    }
}
```

**How to run:**
```bash
java ProductRSocketClient.java
# Received: Product[id=1, name=Drill]
# (pause ~300ms)
# Received: Product[id=2, name=Hammer]
# (pause ~300ms)
# Received: Product[id=3, name=Nail]
```

**What changed:** `retrieveFlux(Product.class)` on the client side pairs naturally with the server's `Flux<Product>`-returning handler — the elements stream to the client progressively, with RSocket's own protocol-level backpressure (rather than an HTTP-specific mechanism like NDJSON chunking) governing the flow, entirely transparent to this simple example but genuinely load-bearing under real backpressure scenarios (a slow client naturally throttles the server's emission rate).

### Level 3 — Advanced

Request-channel (bidirectional streaming) — the interaction model with no clean HTTP equivalent — modeling a client continuously streaming sensor readings while receiving continuous processed/aggregated results back over the same logical exchange:

```java
// SensorController.java
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;
import reactor.core.publisher.Flux;

@Controller
public class SensorController {

    record Reading(String sensorId, double value) {}
    record RunningAverage(String sensorId, double average, int count) {}

    @MessageMapping("sensor.channel")
    public Flux<RunningAverage> processReadings(Flux<Reading> readings) {
        // Maintains a running average PER sensor, emitting an updated
        // RunningAverage for EACH incoming Reading — genuinely bidirectional:
        // the client sends readings continuously; the server responds
        // continuously, over the SAME logical exchange.
        java.util.Map<String, double[]> state = new java.util.concurrent.ConcurrentHashMap<>();   // [sum, count]

        return readings.map(reading -> {
            double[] agg = state.computeIfAbsent(reading.sensorId(), k -> new double[]{0, 0});
            synchronized (agg) {
                agg[0] += reading.value();
                agg[1] += 1;
                return new RunningAverage(reading.sensorId(), agg[0] / agg[1], (int) agg[1]);
            }
        });
    }
}
```

```java
// SensorClient.java
import org.springframework.messaging.rsocket.RSocketRequester;
import reactor.core.publisher.Flux;

import java.time.Duration;

public class SensorClient {
    record Reading(String sensorId, double value) {}
    record RunningAverage(String sensorId, double average, int count) {}

    public static void main(String[] args) throws InterruptedException {
        RSocketRequester requester = RSocketRequester.builder().tcp("localhost", 7000);

        Flux<Reading> outgoingReadings = Flux.just(
                new Reading("temp-1", 20.0), new Reading("temp-1", 22.0), new Reading("temp-1", 21.0))
            .delayElements(Duration.ofMillis(200));

        Flux<RunningAverage> incomingAverages = requester.route("sensor.channel")
            .data(outgoingReadings)
            .retrieveFlux(RunningAverage.class);

        incomingAverages.subscribe(avg ->
            System.out.println("Running average for " + avg.sensorId() + ": " + avg.average() + " (n=" + avg.count() + ")"));

        Thread.sleep(1500);
        requester.rsocket().dispose();
    }
}
```

**How to run:**
```bash
java SensorClient.java
# Running average for temp-1: 20.0 (n=1)
# Running average for temp-1: 21.0 (n=2)
# Running average for temp-1: 21.0 (n=3)
```

**What changed and why:**
- `processReadings(Flux<Reading> readings)` — note the parameter type is itself a `Flux`, not a single `Reading` — this is what signals request-channel semantics to Spring's RSocket infrastructure: the client streams a continuous sequence of `Reading`s, and the server's handler processes that inbound `Flux` while simultaneously producing its own outbound `Flux<RunningAverage>`, all over one logical, bidirectional exchange.
- This has no equivalent in ordinary HTTP-based WebFlux — even `@RequestBody Flux<T>` (from the reactive request/response body card) only supports ONE direction being a stream (the request), with the response being either a single value or a separately-streamed response, not a genuinely interleaved, bidirectional exchange over one connection. RSocket's request-channel model is architecturally distinct and specifically suited to scenarios like this continuous sensor-processing example.
- The running-average computation itself demonstrates a realistic use case: a client (perhaps an IoT device or a sensor gateway) streams raw readings continuously, and the server streams back continuously updated aggregates — both directions flowing concurrently and independently, exactly matching how a genuinely real-time, bidirectional data pipeline would need to behave.

## 6. Walkthrough

**Interaction: the client's request-channel call to `sensor.channel` (Level 3 code), tracing the bidirectional flow.**

1. `requester.route("sensor.channel").data(outgoingReadings).retrieveFlux(RunningAverage.class)` establishes an RSocket request-channel interaction — under the hood, this opens a single RSocket "stream" (a logical channel within the underlying TCP connection) that will carry both the client's outgoing `Reading` frames and the server's incoming `RunningAverage` frames simultaneously.
2. On the server side, `SensorController.processReadings` is invoked with a `Flux<Reading>` representing this specific channel's inbound stream. The handler constructs its processing pipeline (`readings.map(...)`) and returns the resulting `Flux<RunningAverage>` — this return value becomes the channel's outbound stream.
3. The client's `outgoingReadings` `Flux` begins emitting: `Reading("temp-1", 20.0)` first (with `delayElements(200ms)` pacing subsequent emissions). This is transmitted over the RSocket channel to the server.
4. The server's `readings.map(...)` pipeline receives this first `Reading`. Inside the lambda: `state.computeIfAbsent("temp-1", ...)` creates a fresh `[0, 0]` aggregate array (no prior state for this sensor), then updates it to `[20.0, 1]`, producing `RunningAverage("temp-1", 20.0, 1)`.
5. This `RunningAverage` is emitted from the server's outbound `Flux`, transmitted back over the same RSocket channel to the client, arriving at the client's `incomingAverages` subscription — the subscribe callback prints `"Running average for temp-1: 20.0 (n=1)"`.
6. ~200ms later, the client's `outgoingReadings` emits its second element, `Reading("temp-1", 22.0)`, sent over the channel.
7. The server processes it: `state.get("temp-1")` now returns the existing `[20.0, 1]` array, updates it to `[42.0, 2]`, producing `RunningAverage("temp-1", 21.0, 2)` (`42.0 / 2 = 21.0`) — sent back and received by the client, printing `"Running average for temp-1: 21.0 (n=2)"`.
8. This pattern repeats for the third reading, `21.0`, updating the aggregate to `[63.0, 3]`, producing `RunningAverage("temp-1", 21.0, 3)`.
9. Once the client's `outgoingReadings` `Flux` completes (all three readings sent), the inbound side of the channel signals completion to the server. The server's `readings.map(...)`-derived outbound `Flux` also completes shortly after (once its own final processing finishes), signaling completion back to the client, at which point the entire request-channel interaction concludes — both directions of the logical channel close together.

Throughout this entire exchange, both the client's outgoing readings and the server's outgoing averages flow concurrently and independently over the same underlying RSocket stream — neither side blocks waiting for the other, and RSocket's own protocol-level backpressure would naturally throttle either direction if either side's consumer fell behind, without any application code needing to implement that throttling manually.

## 7. Gotchas & takeaways

> **RSocket is a genuinely different wire protocol from HTTP, not an HTTP feature** — an ordinary web browser or standard HTTP client cannot speak RSocket directly; it requires an RSocket-aware client library (`RSocketRequester` on the Java/Spring side, or an equivalent client library in other languages). This makes it well-suited for service-to-service communication where you control both ends, but unsuitable as a direct replacement for browser-facing REST APIs.

> **Choosing the wrong handler method signature (parameter/return type combination) silently selects the wrong interaction model** — a `Mono<T>` parameter with a `Flux<T>` return is request-stream; a `Flux<T>` parameter with a `Flux<T>` return is request-channel; getting this "shape" wrong doesn't produce a compile error, but does produce behavior that doesn't match your actual intent, discovered only at runtime.

> **RSocket's route-based dispatch (`@MessageMapping("product.get")`) has no built-in path-variable or query-parameter concept analogous to HTTP's `@PathVariable`/`@RequestParam`** — route strings are typically treated as fixed identifiers, with actual data passed via the request's `data(...)` payload (as `id` was passed in the Level 1 example) rather than embedded in the route itself.

- RSocket is a reactive, binary application protocol with four native interaction models (request-response, fire-and-forget, request-stream, request-channel), each mapped to a distinct Spring `@MessageMapping` handler signature.
- Request-channel (bidirectional streaming, `Flux` parameter and `Flux` return) is RSocket's standout capability with no clean HTTP/WebFlux equivalent — genuinely concurrent, independent streams flowing in both directions over one logical exchange.
- Backpressure is built into RSocket's own wire protocol, not simulated on top of it, making it a strong choice for internal service-to-service reactive communication.
- RSocket requires RSocket-aware clients on both ends and is not a browser-facing protocol — reserve it for scenarios where you control both communicating parties and specifically need its native streaming/backpressure capabilities.
