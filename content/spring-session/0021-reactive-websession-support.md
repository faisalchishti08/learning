---
card: spring-session
gi: 21
slug: reactive-websession-support
title: "Reactive (WebSession) support"
---

## 1. What it is

For reactive, non-blocking applications built on Spring WebFlux, the equivalent of `HttpSession` is `WebSession`, and Spring Session provides a reactive counterpart to everything covered so far — `ReactiveSessionRepository` (card 0022) backing a `WebSessionManager`, wired via `@EnableRedisWebSession` or `@EnableRedisIndexedWebSession` — so a WebFlux application gets the same clustered-session capability as a traditional Spring MVC application, but built entirely on non-blocking, reactive types (`Mono`/`Flux`) rather than blocking calls.

## 2. Why & when

WebFlux applications are built around the principle that no operation should block a thread waiting on I/O — a thread should be freed to do other work while, say, a network call to Redis completes, rather than sitting idle. The blocking `SessionRepository` (card 0002) used throughout the rest of this card's non-reactive content would violate that principle if used directly inside a WebFlux application — every session lookup would block a reactive thread, defeating the entire point of the reactive stack. `ReactiveSessionRepository` and `WebSession` exist specifically to preserve non-blocking behavior end-to-end, including through session access.

Reach for reactive session support when:

- Building any application on Spring WebFlux (rather than traditional Spring MVC) that also needs clustered session storage — the reactive session APIs are the correct, idiomatic fit; using the blocking `HttpSession`-based APIs inside a WebFlux application either doesn't compile against the reactive contract or, worse, silently reintroduces blocking calls into a reactive pipeline.
- Migrating an existing blocking Spring MVC application with Spring Session already configured to WebFlux — this migration necessarily includes switching from `SessionRepository`/`HttpSession` to `ReactiveSessionRepository`/`WebSession`, not just a drop-in replacement of the surrounding web framework alone.
- Understanding why WebFlux controllers accept a `WebSession` (or a `Mono<WebSession>`) parameter instead of the familiar `HttpSession` — recognizing this at a glance avoids a common early confusion point for teams new to WebFlux coming from a Spring MVC background.

## 3. Core concept

Think of `HttpSession` and `SessionRepository` as a librarian who walks to the archive room, physically retrieves a requested book, and hands it back — the requester stands and waits (blocks) the entire time this happens. `WebSession` and `ReactiveSessionRepository` are like submitting a retrieval request through a pneumatic tube system instead: you hand over your request, immediately go do something else useful, and get notified (a `Mono` completing) the moment the book arrives — never standing idle waiting for the fetch itself, freeing you to help other patrons in the meantime.

```java
// Blocking (Spring MVC):
HttpSession session = request.getSession(); // blocks the calling thread until resolved

// Reactive (WebFlux):
Mono<WebSession> sessionMono = exchange.getSession(); // returns immediately; work happens async
sessionMono.map(session -> session.getAttribute("cart"));
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Blocking session access ties up a thread waiting on the store; reactive session access frees the thread immediately and completes asynchronously">
  <rect x="20" y="20" width="280" height="80" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Blocking (HttpSession)</text>
  <text x="160" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread blocks until Redis responds</text>
  <text x="160" y="86" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">thread unavailable for other work meanwhile</text>

  <rect x="360" y="20" width="280" height="80" rx="10" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="500" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Reactive (WebSession)</text>
  <text x="500" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mono returned immediately</text>
  <text x="500" y="86" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">thread freed to serve other requests</text>
</svg>

Both eventually deliver the same session data — the difference is entirely in what the calling thread is doing while waiting for it.

## 5. Runnable example

The scenario: a reactive cart controller using `WebSession`, growing to enable Redis-backed reactive session storage for clustering, and finally to compose multiple reactive session operations correctly within a single non-blocking pipeline, avoiding the common mistake of accidentally blocking inside a reactive chain.

### Level 1 — Basic

```java
// ReactiveCartController.java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.WebSession;
import reactor.core.publisher.Mono;

@RestController
public class ReactiveCartController {

    @GetMapping("/cart/add")
    public Mono<String> addItem(WebSession session) {
        Integer count = session.getAttributeOrDefault("itemCount", 0);
        count = count + 1;
        session.getAttributes().put("itemCount", count);
        return Mono.just("Cart has " + count + " item(s). Session ID: " + session.getId());
    }
}
```

**How to run:** in a Spring Boot WebFlux application, call `GET /cart/add` repeatedly with the same session cookie. Expected output: the count increments across requests — functionally identical behavior to the blocking `HttpSession` example from card 0001, but the entire request pipeline, including session access, stays non-blocking throughout.

### Level 2 — Intermediate

Without any reactive-specific Spring Session configuration, `WebSession` defaults to an in-memory implementation (analogous to `MapSessionRepository`, card 0015) — clustering requires explicitly enabling reactive Redis session support.

```java
// ReactiveRedisSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.server.EnableRedisWebSession;

@Configuration
@EnableRedisWebSession
public class ReactiveRedisSessionConfig {
}
```

```properties
spring.data.redis.host=localhost
spring.data.redis.port=6379
```

**How to run:** add this configuration and a reactive Redis connection (via `spring-boot-starter-data-redis-reactive`), restart, repeat the `GET /cart/add` sequence, then restart the application entirely mid-sequence and continue with the same cookie. Expected behavior: exactly like the blocking Redis example (card 0001, Level 3), the cart count survives the application restart, since session data now lives in Redis rather than in-process — but every step of the way, session access remained non-blocking.

What changed: the reactive application gained the exact same clustering and durability benefits as its blocking counterpart, achieved through the reactive-specific configuration path rather than the blocking one, since the two aren't interchangeable.

### Level 3 — Advanced

A common mistake when adapting existing blocking-style thinking to reactive code is accidentally blocking inside a reactive chain (e.g. calling `.block()` on a `Mono` to "just get the value synchronously") — this defeats the entire purpose of the reactive stack and, in some reactive execution contexts, throws an exception outright. Correctly composing multiple session-dependent operations means chaining reactive operators throughout, never breaking out to blocking calls.

```java
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.WebSession;
import reactor.core.publisher.Mono;

@RestController
public class CheckoutController {

    private final InventoryService inventoryService; // a stand-in reactive service

    public CheckoutController(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    @PostMapping("/cart/checkout")
    public Mono<String> checkout(WebSession session) {
        Integer itemCount = session.getAttributeOrDefault("itemCount", 0);

        if (itemCount == 0) {
            return Mono.just("Cart is empty, nothing to check out.");
        }

        // Correct: compose the downstream reactive call within the chain,
        // never blocking to "unwrap" a value early.
        return inventoryService.reserveItems(itemCount)
                .map(reservationId -> {
                    session.getAttributes().put("itemCount", 0); // clear cart, still non-blocking
                    return "Checkout complete. Reservation: " + reservationId;
                })
                .onErrorResume(error -> Mono.just("Checkout failed: " + error.getMessage()));
    }

    interface InventoryService {
        Mono<String> reserveItems(int count);
    }
}
```

**How to run:** call `POST /cart/checkout` after adding items via Level 1's endpoint, with a real or stubbed `InventoryService` implementation. Expected behavior: the response correctly reflects either a successful reservation (with the cart cleared afterward) or a handled failure — all without any thread ever blocking waiting on either the session store or the inventory service, and both operations composed cleanly within one reactive pipeline via `.map(...)` and `.onErrorResume(...)`.

What changed and why it's production-flavored: this demonstrates the actual discipline reactive session handling requires in a realistic multi-step operation (check cart, reserve inventory, update session, handle failure) — the temptation to reach for `.block()` "just this once" is common among teams new to reactive programming, and doing so anywhere in this chain would reintroduce the exact blocking behavior the whole reactive architecture exists to avoid.

## 6. Walkthrough

Tracing a reactive checkout request end-to-end, in execution order:

1. A `POST /cart/checkout` request arrives; WebFlux's reactive request-handling machinery resolves the `WebSession` parameter — this itself is an asynchronous operation (fetching from Redis, per Level 2's configuration) that completes without blocking the handling thread while the fetch is in flight.
2. `checkout(...)` reads `itemCount` from the now-resolved session and, if items exist, calls `inventoryService.reserveItems(itemCount)`, which returns a `Mono<String>` representing a reservation operation that hasn't completed yet.
3. `.map(...)` declares what should happen *once* that reservation eventually completes — clearing the cart in the session and building the success message — without the calling code ever waiting synchronously for that completion.
4. `.onErrorResume(...)` declares a fallback path for if the reservation fails, again purely declaratively, composed into the same reactive chain rather than handled via a blocking try/catch around a synchronous call.
5. The reactive framework's underlying event loop executes this entire declared pipeline asynchronously — the thread that initially received the request is free to serve other requests while `reserveItems` is in flight, and only resumes processing *this* particular request's pipeline once the inventory `Mono` actually emits a value or an error.
6. Once resolved, the final response (success or failure message) is written back to the client — from the client's perspective, this looked like an ordinary synchronous request/response; the non-blocking behavior was entirely an internal server-side execution efficiency, invisible externally.

```
POST /cart/checkout
   |
WebSession resolved (async, non-blocking Redis fetch)
   |
itemCount read from session
   |
inventoryService.reserveItems(count) -> Mono<String> (not yet resolved)
   |                                          |
   |                              (thread freed to serve other requests meanwhile)
   |                                          |
   |                              reservation completes (success or error)
   |
.map(...) or .onErrorResume(...) fires -> build response
   |
response sent to client
```

## 7. Gotchas & takeaways

> Calling `.block()` anywhere inside a WebFlux request-handling pipeline defeats the purpose of the reactive stack and, on Reactor's default `Schedulers.parallel()`-backed execution contexts (commonly used by WebFlux's Netty-based server), throws an `IllegalStateException` specifically to catch this mistake — treat any temptation to reach for `.block()` inside a controller or service method as a strong signal the code needs to be restructured as a proper reactive chain instead, not silenced by moving to a different scheduler.

- `WebSession` and `HttpSession`, along with `ReactiveSessionRepository` and `SessionRepository`, are entirely separate type hierarchies — a Spring MVC application's session-handling code cannot be reused as-is in a WebFlux application; the reactive equivalents are a parallel implementation, not a compatibility shim.
- The reactive-specific `@Enable*WebSession` annotations (`@EnableRedisWebSession`, and reactive-Mongo equivalents) are distinct from their blocking counterparts (`@EnableRedisHttpSession`) — using the wrong one for the application's actual web framework (MVC vs. WebFlux) either won't compile correctly against the framework's expectations or won't be picked up at all.
- Reactive Redis session support requires a *reactive* Redis client/connection factory (`spring-boot-starter-data-redis-reactive`), not the blocking one used for `@EnableRedisHttpSession` — mixing a blocking Redis client into a reactive session configuration reintroduces blocking calls despite otherwise using the reactive session APIs correctly.
- Debugging reactive session issues benefits from understanding Reactor's operators (`map`, `flatMap`, `onErrorResume`, and others) at least at a basic level — a bug in reactive session-dependent logic is very often a composition mistake (the wrong operator, or a step that should be async left as if it were synchronous) rather than a Spring Session-specific issue.
- Teams migrating from Spring MVC to WebFlux should budget real time for this transition specifically — session handling is one of several places (alongside database access, external HTTP calls, and general controller logic) where "just swap the annotation" doesn't work, and genuinely rethinking the code as a reactive pipeline is required.
