---
card: spring-framework
gi: 374
slug: httphandler-adapters-reactor-netty-tomcat-jetty-undertow-ser
title: "HttpHandler & adapters (Reactor Netty, Tomcat, Jetty, Undertow, Servlet)"
---

## 1. What it is

`HttpHandler` is the lowest-level abstraction in Spring WebFlux — a single-method functional interface (`Mono<Void> handle(ServerHttpRequest, ServerHttpResponse)`) that represents "process this request, write this response," entirely independent of any specific server technology. Spring provides server-specific **adapter** implementations that bridge each supported server's native API (Reactor Netty's, Tomcat's Servlet 3.1+ non-blocking I/O API, Jetty's, Undertow's) to this one common `HttpHandler` contract — this is precisely what lets the exact same WebFlux application run unmodified on any of these servers.

```java
// You never implement HttpHandler directly in application code — it's the
// foundational abstraction DispatcherHandler itself is adapted TO, so that
// the same reactive application logic works across genuinely different servers.

HttpHandler httpHandler = WebHttpHandlerBuilder.applicationContext(context).build();
ReactorHttpHandlerAdapter adapter = new ReactorHttpHandlerAdapter(httpHandler);
HttpServer.create().handle(adapter).bindNow();
```

## 2. Why & when

Spring MVC is fundamentally tied to the Servlet API — `DispatcherServlet` extends `HttpServlet`, and every MVC application requires a genuine Servlet container. WebFlux was designed from the outset to run on servers that aren't Servlet containers at all (Reactor Netty being the flagship example, and Spring Boot's default choice for WebFlux applications) — this requires an abstraction layer *below* `DispatcherHandler` that can represent "handle this request" in a way that doesn't assume Servlet API types exist.

Understanding `HttpHandler` and its adapters matters when:

- You're choosing which server to run a WebFlux application on — understanding that Netty, Tomcat, Jetty, and Undertow are all genuinely interchangeable at this layer explains why the choice is mostly about operational familiarity and specific feature needs, not fundamental compatibility.
- You're debugging a genuinely low-level issue where behavior differs subtly between servers (connection handling edge cases, specific header behaviors) — knowing which adapter is in play helps narrow down whether an issue is WebFlux-level or server-adapter-level.
- You want to understand precisely how WebFlux achieves true non-blocking I/O even on a traditionally Servlet-API-based server like Tomcat — the answer lies in the Servlet 3.1+ non-blocking I/O API, which Spring's Servlet-specific `HttpHandler` adapter uses internally.

## 3. Core concept

```
HttpHandler (Mono<Void> handle(ServerHttpRequest, ServerHttpResponse)):

  ONE common contract, MULTIPLE server-specific adapters implement
  the "bridge" from each server's native API TO this contract:

  ReactorHttpHandlerAdapter    — bridges Reactor Netty's native reactive
                                   HTTP server API (genuinely non-Servlet)
  TomcatHttpHandlerAdapter     — bridges Tomcat, using Servlet 3.1+'s
                                   NON-BLOCKING I/O extensions (ReadListener/
                                   WriteListener) — NOT the classic blocking
                                   Servlet API
  JettyHttpHandlerAdapter      — bridges Jetty similarly
  UndertowHttpHandlerAdapter   — bridges Undertow similarly
  ServletHttpHandlerAdapter    — a MORE GENERIC Servlet 3.1+ adapter,
                                   usable on any compliant Servlet container

Layering (top to bottom):

  Your @RestController / RouterFunction
        |
  DispatcherHandler (implements WebHandler)
        |
  WebHttpHandlerBuilder wraps it with WebFilters, exception handling, etc.,
  producing a single HttpHandler
        |
  Server-specific ADAPTER bridges the server's native request/response
  representation to ServerHttpRequest/ServerHttpResponse
        |
  The ACTUAL server (Netty, Tomcat, Jetty, Undertow)
```

## 4. Diagram

<svg viewBox="0 0 740 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="230" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">One HttpHandler contract, many server-specific adapters</text>

  <rect x="270" y="40" width="200" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="70" text-anchor="middle" fill="#6db33f" font-size="11">HttpHandler (one contract)</text>

  <line x1="330" y1="90" x2="140" y2="140" stroke="#8b949e" marker-end="url(#a50)"/>
  <line x1="350" y1="90" x2="280" y2="140" stroke="#8b949e" marker-end="url(#a50)"/>
  <line x1="390" y1="90" x2="460" y2="140" stroke="#8b949e" marker-end="url(#a50)"/>
  <line x1="410" y1="90" x2="600" y2="140" stroke="#8b949e" marker-end="url(#a50)"/>

  <rect x="60" y="140" width="160" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="165" text-anchor="middle" fill="#79c0ff" font-size="10">ReactorHttpHandlerAdapter</text>

  <rect x="220" y="140" width="120" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="280" y="165" text-anchor="middle" fill="#79c0ff" font-size="10">TomcatAdapter</text>

  <rect x="400" y="140" width="120" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="460" y="165" text-anchor="middle" fill="#79c0ff" font-size="10">JettyAdapter</text>

  <rect x="540" y="140" width="140" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="610" y="165" text-anchor="middle" fill="#79c0ff" font-size="10">UndertowAdapter</text>

  <defs>
    <marker id="a50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The same `HttpHandler`-based application logic runs unmodified across genuinely different underlying server technologies.*

## 5. Runnable example

### Level 1 — Basic

Swapping the underlying server for a WebFlux application via a single dependency change — no application code changes at all — demonstrating the adapter layer's payoff directly:

```xml
<!-- pom.xml — DEFAULT: Reactor Netty (Spring Boot's default WebFlux server) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
```

```java
// ProductController.java — IDENTICAL regardless of which server runs it
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

```xml
<!-- pom.xml — SWAPPED to Tomcat instead, via dependency exclusion + addition -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-reactor-netty</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-tomcat</artifactId>
</dependency>
```

**How to run:**
```bash
# With Netty (default):
./mvnw spring-boot:run
curl -v http://localhost:8080/products/1 2>&1 | grep -i server
# (Netty typically doesn't add a Server header by default, or shows minimal info)

# With Tomcat (after the dependency swap):
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}     <- IDENTICAL response, EXACT same controller code
```

`ProductController` required zero changes — Spring Boot's WebFlux autoconfiguration detects which server dependency is present on the classpath and wires in the corresponding `HttpHandler` adapter (`ReactorHttpHandlerAdapter` or `TomcatHttpHandlerAdapter`) automatically. This is the direct, concrete payoff of the `HttpHandler` abstraction: application-level reactive code is entirely portable across server implementations.

### Level 2 — Intermediate

Manually building and running an `HttpHandler`-based server outside of Spring Boot's autoconfiguration, to see the layering explicitly rather than relying on "it just works":

```java
// ManualServerBootstrap.java
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.server.reactive.HttpHandler;
import org.springframework.http.server.reactive.ReactorHttpHandlerAdapter;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;
import org.springframework.web.server.adapter.WebHttpHandlerBuilder;
import reactor.netty.http.server.HttpServer;

public class ManualServerBootstrap {

    record Product(long id, String name) {}

    public static void main(String[] args) {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext();
        context.registerBean(RouterFunction.class, () -> RouterFunctions.route()
            .GET("/products/{id}", request -> {
                long id = Long.parseLong(request.pathVariable("id"));
                return ServerResponse.ok().bodyValue(new Product(id, "Drill"));
            })
            .build());
        context.refresh();

        // Building the HttpHandler EXPLICITLY, then wrapping it with a specific
        // server adapter — this is what Spring Boot's autoconfiguration does
        // implicitly and automatically, made visible here.
        HttpHandler httpHandler = WebHttpHandlerBuilder.applicationContext(context).build();
        ReactorHttpHandlerAdapter adapter = new ReactorHttpHandlerAdapter(httpHandler);

        HttpServer.create()
            .port(8080)
            .handle(adapter)
            .bindNow();

        System.out.println("Server started on port 8080");
        new java.util.concurrent.CountDownLatch(1).await();   // keep the JVM alive
    }
}
```

**How to run:**
```bash
java ManualServerBootstrap.java
# Server started on port 8080

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
```

**What changed:** This program builds and runs a complete WebFlux application without Spring Boot's autoconfiguration at all — `WebHttpHandlerBuilder.applicationContext(context).build()` explicitly assembles `DispatcherHandler` (discovering the registered `RouterFunction` bean) together with WebFlux's filter chain into a single `HttpHandler`, and `ReactorHttpHandlerAdapter` explicitly bridges that `HttpHandler` to Reactor Netty's own `HttpServer` API. This is precisely the machinery Spring Boot wires together automatically — seeing it assembled by hand demystifies what "Spring Boot starts a WebFlux server" actually does under the hood.

### Level 3 — Advanced

Understanding the Servlet-based adapter's non-blocking mechanism specifically — since Tomcat is fundamentally a Servlet container, WebFlux's Tomcat adapter must achieve true non-blocking I/O using the Servlet 3.1+ asynchronous I/O extensions (`ReadListener`/`WriteListener`), not the classic blocking Servlet API — this explains a genuinely important architectural nuance for anyone choosing Tomcat as their WebFlux server:

```java
// This is CONCEPTUAL/illustrative — Spring's own TomcatHttpHandlerAdapter
// implements this internally; application code never touches these APIs directly.
// Shown here to make the underlying mechanism concrete rather than "magic."

// jakarta.servlet.ReadListener (Servlet 3.1+, NON-BLOCKING request body reading):
public interface ReadListener extends EventListener {
    void onDataAvailable() throws IOException;   // called when MORE data CAN be read without blocking
    void onAllDataRead() throws IOException;
    void onError(Throwable t);
}

// jakarta.servlet.WriteListener (Servlet 3.1+, NON-BLOCKING response writing):
public interface WriteListener extends EventListener {
    void onWritePossible() throws IOException;   // called when MORE data CAN be written without blocking
    void onError(Throwable t);
}

// TomcatHttpHandlerAdapter (and the analogous adapters for Jetty/Undertow)
// internally implement Reactive-Streams Publisher/Subscriber semantics
// ON TOP OF these listener-based, non-blocking Servlet 3.1+ primitives —
// bridging "give me a callback when I CAN read/write without blocking"
// into "here is a Publisher<DataBuffer> you can subscribe to reactively."
```

```java
// ProductController.java — genuinely IDENTICAL code, runs correctly non-blocking
// on Tomcat via this Servlet-3.1+-based bridging, exactly as it would on Netty.
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

**How to run:**
```bash
# (using the Tomcat-based WebFlux setup from Level 1)
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}     <- genuinely non-blocking, DESPITE running on
#                                 a fundamentally Servlet-API-based container
```

**What changed and why:**
- The `ReadListener`/`WriteListener` interfaces shown are the actual Servlet 3.1+ specification primitives that make non-blocking I/O possible on a Servlet container at all — they represent a fundamentally different interaction model from the classic, blocking `InputStream.read()`/`OutputStream.write()` methods most Java developers associate with the Servlet API, and their existence (since Servlet 3.1, part of Java EE 7 / Jakarta EE) is precisely what allows WebFlux to run genuinely non-blocking on Tomcat/Jetty/Undertow, not just "pretend" to be non-blocking while secretly still blocking threads.
- `TomcatHttpHandlerAdapter` (and its Jetty/Undertow counterparts) do the real, nontrivial engineering work of bridging this callback-based, listener-driven API to the Reactive Streams `Publisher`/`Subscriber` model WebFlux's `ServerHttpRequest`/`ServerHttpResponse` types expect — this bridging code is exactly what you'd need to write yourself if building a reactive framework on top of the Servlet API from scratch, and it's precisely what Spring having already built and battle-tested it saves you from needing to understand in day-to-day usage.
- The practical takeaway: choosing Tomcat over Netty for a WebFlux application (perhaps for organizational familiarity, existing Tomcat-specific tooling, or operational constraints) does **not** mean sacrificing WebFlux's core non-blocking guarantee — the adapter layer genuinely delivers equivalent non-blocking behavior, just achieved via a different underlying mechanism than Netty's native reactive I/O model.

## 6. Walkthrough

**Startup: `ManualServerBootstrap.main()` (Level 2 code), tracing the assembly explicitly.**

1. An `AnnotationConfigApplicationContext` is created and a `RouterFunction` bean is registered directly, then `context.refresh()` finalizes the Spring context, making the bean available for discovery.
2. `WebHttpHandlerBuilder.applicationContext(context).build()` inspects this context, discovers the registered `RouterFunction` bean (via the same `RouterFunctionMapping` mechanism `DispatcherHandler` uses internally), assembles a `DispatcherHandler` wired to recognize it, wraps this with any registered `WebFilter`s (none in this minimal example) and WebFlux's exception-handling infrastructure, and produces a single, self-contained `HttpHandler` instance representing the entire application's request-processing logic.
3. `new ReactorHttpHandlerAdapter(httpHandler)` wraps this generic `HttpHandler` in an adapter specifically capable of bridging Reactor Netty's own native server API (`reactor.netty.http.server.HttpServer`) to the `HttpHandler` contract — this adapter object is what actually knows how to translate Netty's request/response representations into WebFlux's `ServerHttpRequest`/`ServerHttpResponse` and back.
4. `HttpServer.create().port(8080).handle(adapter).bindNow()` starts an actual Reactor Netty server, configured to delegate every incoming connection's request handling to the `adapter` object from step 3 — at this point, the server is genuinely listening and ready to process requests.

**Request: `GET /products/1` against this manually-bootstrapped server.**

1. Reactor Netty's own event-loop receives the raw TCP connection and HTTP request, using its native, non-blocking I/O model (Netty predates and is independent of the Servlet API entirely).
2. `ReactorHttpHandlerAdapter` is invoked by Netty's own API with Netty-native request/response objects. The adapter constructs WebFlux's `ServerHttpRequest`/`ServerHttpResponse` wrappers around them and calls the wrapped `httpHandler.handle(request, response)`.
3. This invokes `DispatcherHandler` (embedded inside the built `HttpHandler`), which — exactly as detailed in the previous card — finds the matching `RouterFunctionMapping` result for `/products/1`, invokes the corresponding handler function, and produces the response.
4. The resulting `ServerResponse` (from the functional endpoint) is written back through the `ServerHttpResponse` wrapper, which `ReactorHttpHandlerAdapter` translates back into Netty-native response-writing calls.
5. Netty flushes the response bytes to the client over the original, still-open, non-blocking connection.
6. Client receives:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

Every step in this chain — from Netty's raw I/O event through `DispatcherHandler`'s handler resolution back down to Netty's response write — happens without any thread ever blocking waiting for I/O, which is the entire architectural point this layered abstraction (`HttpHandler` plus server-specific adapters) exists to deliver, regardless of which specific server technology is doing the actual byte-level I/O work underneath.

## 7. Gotchas & takeaways

> **`HttpHandler` and its adapters are almost never touched directly in application code** — Spring Boot's autoconfiguration assembles and wires everything automatically based on which server dependency is on the classpath. The manual bootstrap in Level 2 exists purely as an educational illustration of what that autoconfiguration does on your behalf, not as a pattern to replicate in real applications.

> **Choosing a non-default server for WebFlux (Tomcat/Jetty/Undertow instead of the default Netty) requires excluding the default Netty starter dependency explicitly** — simply adding a competing server dependency without excluding Netty can result in ambiguous autoconfiguration or, depending on classpath ordering, the "wrong" server actually starting, which can be confusing to diagnose.

> **Non-blocking behavior on Servlet-based servers (Tomcat, Jetty, Undertow) depends entirely on Servlet 3.1+'s asynchronous I/O extensions being genuinely used by the adapter** — this is handled correctly by Spring's own adapters, but it's worth knowing that "runs on Tomcat" does not inherently mean "blocking," since the adapter layer specifically avoids the classic, blocking Servlet I/O methods in favor of the newer, callback-driven ones.

- `HttpHandler` is the lowest-level, server-agnostic abstraction in WebFlux — a single method representing "handle this request, write this response," with no dependency on any specific server's API.
- Server-specific adapters (`ReactorHttpHandlerAdapter`, `TomcatHttpHandlerAdapter`, `JettyHttpHandlerAdapter`, `UndertowHttpHandlerAdapter`, and a more generic `ServletHttpHandlerAdapter`) bridge each server's native API to this common contract, enabling the exact same application code to run unmodified across genuinely different server technologies.
- Servlet-based servers achieve true non-blocking behavior for WebFlux via the Servlet 3.1+ `ReadListener`/`WriteListener` asynchronous I/O extensions, not the classic blocking Servlet API.
- `WebHttpHandlerBuilder` assembles `DispatcherHandler` plus registered `WebFilter`s and exception handling into a single, complete `HttpHandler` — the object each server-specific adapter ultimately wraps.
