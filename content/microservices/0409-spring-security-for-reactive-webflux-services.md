---
card: microservices
gi: 409
slug: spring-security-for-reactive-webflux-services
title: "Spring Security for reactive (WebFlux) services"
---

## 1. What it is

**Spring Security for WebFlux** is the reactive counterpart to [Spring Security core](0400-spring-security-core-filters-authentication-authorization.md): instead of the traditional Servlet-based `SecurityFilterChain` running on blocking, thread-per-request I/O, it wires an equivalent chain of security checks onto Spring WebFlux's non-blocking, event-loop-based request pipeline. The building blocks — authentication, authorization, method security — are conceptually the same, but every operation that might involve I/O (loading a user, validating a token, checking a permission) is expressed as a reactive `Mono`/`Flux` rather than a synchronous call, so a single thread can serve many concurrent requests without blocking on any one of them.

## 2. Why & when

You reach for the reactive variant specifically when a service is built on Spring WebFlux rather than Spring MVC — typically because it needs to handle very high concurrency with limited threads, such as an [API gateway](0405-spring-cloud-gateway-spring-security-at-the-edge.md) (which is itself built on WebFlux) or a service that does a lot of downstream I/O-bound fan-out (calling several other services and aggregating results).

- **Thread-per-request doesn't scale to thousands of concurrent, slow connections** — WebFlux's event-loop model can hold far more in-flight requests on far fewer threads, but only if *nothing* in the request path blocks, including security checks.
- **A blocking security check defeats the whole point.** If a WebFlux application's authentication filter calls a blocking JDBC query to load a user, it ties up an event-loop thread exactly like the reactive model was designed to avoid — the security layer has to be reactive too, not just the business logic.
- **Gateways are the most common place this matters**, because [Spring Cloud Gateway](0405-spring-cloud-gateway-spring-security-at-the-edge.md) is built on WebFlux specifically for high-throughput request routing, and its security layer (validating a token before routing) must not block that event loop.
- **Not every service needs it.** A traditional Spring MVC service with modest concurrency needs is usually simpler and just as effective with the classic Servlet-based `SecurityFilterChain` — reach for WebFlux security only when the reactive stack was already chosen for its own reasons.

## 3. Core concept

Picture the difference between a restaurant with one waiter per table (blocking: the waiter stands at your table the whole time you're deciding, even while you're just reading the menu) versus one waiter who circulates efficiently among many tables, only stopping at each one exactly when there's something to actually do (non-blocking: the waiter never idles waiting on you). Reactive security is the second waiter applied to authentication checks: rather than a thread parking itself while a token is validated against a remote server, the check is expressed as a pipeline stage that only occupies a thread for the moment real work happens.

Concretely, the pieces map onto their Servlet-based equivalents:

| Servlet-based (Spring MVC) | Reactive (WebFlux) |
|---|---|
| `SecurityFilterChain` bean | `SecurityWebFilterChain` bean |
| `HttpSecurity` | `ServerHttpSecurity` |
| Synchronous `UserDetailsService` | `ReactiveUserDetailsService` returning `Mono<UserDetails>` |
| `@PreAuthorize` (Spring Security core) | Same annotation, works reactively when the method returns `Mono`/`Flux` |
| Blocking JWT decoder | `ReactiveJwtDecoder` returning `Mono<Jwt>` |

```java
@Configuration
@EnableWebFluxSecurity
public class ReactiveSecurityConfig {

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        return http
                .authorizeExchange(exchanges -> exchanges
                        .pathMatchers("/actuator/health").permitAll()
                        .pathMatchers("/orders/**").hasAuthority("SCOPE_orders.read")
                        .anyExchange().authenticated())
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(withDefaults()))
                .build();
    }
}
```

Every step in that chain — matching the path, validating the JWT, checking the authority — is composed as a non-blocking reactive pipeline under the hood, so the underlying event-loop thread is free to serve other requests while, say, a remote JWKS fetch for token validation is in flight.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A blocking security filter parks a thread per request while validating a token; a reactive security filter chain releases the thread during I/O and resumes only when the validation result is ready, letting one thread serve many concurrent requests" font-family="sans-serif">
  <text x="160" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">Blocking (Servlet)</text>
  <rect x="30" y="35" width="90" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="75" y="54" fill="#e6edf3" font-size="9" text-anchor="middle">Thread A</text>
  <rect x="30" y="75" width="260" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="94" fill="#f0883e" font-size="9" text-anchor="middle">BLOCKED waiting on token validation I/O</text>
  <text x="160" y="122" fill="#8b949e" font-size="9" text-anchor="middle">Thread A cannot serve any other request meanwhile</text>

  <text x="480" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">Reactive (WebFlux)</text>
  <rect x="350" y="35" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="395" y="54" fill="#e6edf3" font-size="9" text-anchor="middle">Event-loop thread</text>
  <rect x="350" y="75" width="260" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="94" fill="#79c0ff" font-size="9" text-anchor="middle">releases thread during I/O, resumes on completion</text>
  <rect x="350" y="115" width="120" height="24" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="131" fill="#e6edf3" font-size="8" text-anchor="middle">serves request 2</text>
  <rect x="480" y="115" width="120" height="24" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="131" fill="#e6edf3" font-size="8" text-anchor="middle">serves request 3</text>
  <text x="480" y="160" fill="#8b949e" font-size="9" text-anchor="middle">same thread serves other requests while waiting</text>
</svg>

A blocking security check occupies a thread for the entire wait; a reactive one frees the thread to do other work in the meantime.

## 5. Runnable example

Scenario: an orders endpoint that must validate a caller's token before serving data. We model it first as a blocking check (a thread parks during "network" validation), then as a non-blocking simulation using `CompletableFuture` to show the thread being freed during the wait, then a full reactive-style pipeline that also authorizes by scope, mirroring `authorizeExchange` + `oauth2ResourceServer`.

### Level 1 — Basic

```java
// File: BlockingTokenCheck.java -- a BLOCKING security check: the calling
// thread sleeps (simulating a network call to validate a token) before any
// other work can happen -- exactly the pattern reactive security exists to avoid.
public class BlockingTokenCheck {
    static boolean validateTokenBlocking(String token) throws InterruptedException {
        System.out.println(Thread.currentThread().getName() + " BLOCKED: validating token...");
        Thread.sleep(200); // simulates a blocking network call to an auth server
        boolean valid = "valid-token".equals(token);
        System.out.println(Thread.currentThread().getName() + " unblocked: token valid=" + valid);
        return valid;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        validateTokenBlocking("valid-token");
        validateTokenBlocking("valid-token"); // a SECOND request must wait for the SAME thread to free up
        System.out.println("Total time for 2 sequential checks: " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

How to run: `java BlockingTokenCheck.java`

`validateTokenBlocking` calls `Thread.sleep(200)` to stand in for a real network round-trip (e.g. fetching a JWKS key set or calling a token-introspection endpoint). While that sleep is happening, the calling thread does absolutely nothing else — it's fully occupied. Two sequential checks therefore take roughly `400ms` combined, because the second check cannot begin until the thread handling the first one is free again. This is the Servlet model: one thread per in-flight request, blocked for the full duration of any I/O.

### Level 2 — Intermediate

```java
// File: NonBlockingTokenCheck.java -- the SAME validation, now expressed as
// a NON-BLOCKING asynchronous operation using CompletableFuture, so the
// calling thread is freed immediately and can start other work while
// validation happens in the background -- the core idea behind reactive security.
import java.util.concurrent.*;

public class NonBlockingTokenCheck {
    static final ExecutorService IO_POOL = Executors.newFixedThreadPool(2);

    static CompletableFuture<Boolean> validateTokenNonBlocking(String token) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(200); } catch (InterruptedException ignored) {}
            return "valid-token".equals(token);
        }, IO_POOL);
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        System.out.println("Main thread kicks off validation and is IMMEDIATELY free to do other things.");

        CompletableFuture<Boolean> check1 = validateTokenNonBlocking("valid-token");
        CompletableFuture<Boolean> check2 = validateTokenNonBlocking("valid-token");
        System.out.println("Main thread continued past both kickoffs at " + (System.currentTimeMillis() - start) + "ms -- not blocked");

        // Only NOW do we actually wait for the results (in a real reactive pipeline, this is a subscriber callback, not a blocking join).
        boolean result1 = check1.get();
        boolean result2 = check2.get();
        System.out.println("Both checks resolved: " + result1 + ", " + result2
                + " -- total elapsed " + (System.currentTimeMillis() - start) + "ms (checks ran CONCURRENTLY, not sequentially)");
        IO_POOL.shutdown();
    }
}
```

How to run: `java NonBlockingTokenCheck.java`

`validateTokenNonBlocking` returns immediately with a `CompletableFuture` — the main thread never blocks on it directly. Both checks are kicked off back-to-back and run *concurrently* on the small `IO_POOL`, so the total elapsed time is roughly `200ms`, not the `400ms` from Level 1's sequential blocking version. This is the essential reactive property: freeing a thread during I/O lets other work (here, the second check) proceed in parallel instead of queuing up behind the first.

### Level 3 — Advanced

```java
// File: ReactiveStyleSecurityPipeline.java -- a REACTIVE-STYLE pipeline that
// chains token validation AND scope-based authorization (mirroring
// authorizeExchange().hasAuthority(...)), still non-blocking throughout, and
// short-circuits (never even attempts authorization) if authentication fails.
import java.util.concurrent.*;
import java.util.*;

public class ReactiveStyleSecurityPipeline {
    static final ExecutorService IO_POOL = Executors.newFixedThreadPool(2);
    record AuthResult(boolean authenticated, Set<String> scopes) {}

    // Stage 1: non-blocking authentication (mirrors ReactiveJwtDecoder).
    static CompletableFuture<AuthResult> authenticate(String token) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(150); } catch (InterruptedException ignored) {}
            if (!"valid-token".equals(token)) return new AuthResult(false, Set.of());
            return new AuthResult(true, Set.of("SCOPE_orders.read"));
        }, IO_POOL);
    }

    // Stage 2: authorization, chained onto stage 1, only runs if authentication succeeded.
    static CompletableFuture<String> authorizeAndServe(String token, String requiredScope) {
        return authenticate(token).thenCompose(auth -> {
            if (!auth.authenticated()) {
                return CompletableFuture.completedFuture("401 Unauthorized -- authentication failed");
            }
            if (!auth.scopes().contains(requiredScope)) {
                return CompletableFuture.completedFuture("403 Forbidden -- missing scope " + requiredScope);
            }
            return CompletableFuture.completedFuture("200 OK -- orders payload served");
        });
    }

    public static void main(String[] args) throws Exception {
        System.out.println(authorizeAndServe("valid-token", "SCOPE_orders.read").get());   // authenticated + authorized
        System.out.println(authorizeAndServe("valid-token", "SCOPE_orders.write").get());   // authenticated, WRONG scope
        System.out.println(authorizeAndServe("bad-token", "SCOPE_orders.read").get());       // fails at authentication, never reaches authorization
        IO_POOL.shutdown();
    }
}
```

How to run: `java ReactiveStyleSecurityPipeline.java`

`authorizeAndServe` chains two non-blocking stages with `thenCompose`: `authenticate` first, and only if it succeeds does the pipeline proceed to check scopes — mirroring how `oauth2ResourceServer(...)` (authentication) composes with `authorizeExchange(...)` (authorization) in a real `SecurityWebFilterChain`, entirely without blocking any thread at any stage. The three calls demonstrate the three real outcomes a resource server produces: full success, an authenticated-but-under-scoped caller, and an outright authentication failure that short-circuits before authorization is even attempted.

## 6. Walkthrough

Trace the three `authorizeAndServe` calls in `main` in order. **First**, `authorizeAndServe("valid-token", "SCOPE_orders.read")` runs. `authenticate("valid-token")` resolves after its simulated 150ms delay with `AuthResult(authenticated=true, scopes={SCOPE_orders.read})`. `thenCompose` receives this and checks `auth.authenticated()` — true — then checks `auth.scopes().contains("SCOPE_orders.read")` — true — so the pipeline returns `"200 OK -- orders payload served"`.

**Next**, `authorizeAndServe("valid-token", "SCOPE_orders.write")` runs the same authentication stage, again resolving to `authenticated=true, scopes={SCOPE_orders.read}`. This time the required scope is `"SCOPE_orders.write"`, which is **not** in the returned scope set, so the second `if` branch fires and the pipeline returns `"403 Forbidden -- missing scope SCOPE_orders.write"` — the caller proved who they are but wasn't authorized for this specific operation.

**Then**, `authorizeAndServe("bad-token", "SCOPE_orders.read")` runs. `authenticate("bad-token")` resolves to `AuthResult(authenticated=false, scopes={})`. The very first check inside `thenCompose`, `auth.authenticated()`, is false, so the pipeline short-circuits immediately and returns `"401 Unauthorized -- authentication failed"` — the authorization check (scope comparison) never runs at all, exactly mirroring how a real reactive resource server never evaluates `hasAuthority(...)` for a request whose token failed validation.

**Finally**, all three results print in order, showing the full spread of outcomes a reactive security pipeline produces for one endpoint under different tokens and required scopes.

```
authorizeAndServe(valid-token, orders.read)  -> 200 OK -- orders payload served
authorizeAndServe(valid-token, orders.write) -> 403 Forbidden -- missing scope SCOPE_orders.write
authorizeAndServe(bad-token,   orders.read)  -> 401 Unauthorized -- authentication failed
```

## 7. Gotchas & takeaways

> The single most common mistake porting security logic to WebFlux is calling a blocking API — a synchronous JDBC `UserDetailsService`, a blocking HTTP client for token introspection, `Thread.sleep` inside a reactive operator — from within a reactive security filter. It compiles and often "works" under light load, then silently starves the event loop under real concurrency, because a handful of blocked threads can stall every other in-flight request sharing that same small thread pool. Always use the reactive variants (`ReactiveUserDetailsService`, `WebClient` instead of `RestTemplate`, `ReactiveJwtDecoder`) throughout a WebFlux security chain.
- `SecurityWebFilterChain` / `ServerHttpSecurity` are the WebFlux equivalents of [Spring Security core](0400-spring-security-core-filters-authentication-authorization.md)'s `SecurityFilterChain` / `HttpSecurity` — same concepts, non-blocking implementation.
- Reactive security matters most for high-concurrency, I/O-bound services — most notably [Spring Cloud Gateway](0405-spring-cloud-gateway-spring-security-at-the-edge.md), which is built on WebFlux specifically for this reason.
- Every stage of the chain — authentication, authorization, and any custom filter — must stay non-blocking end to end; a single blocking call anywhere in the chain undermines the whole model.
- Chained, short-circuiting composition (`thenCompose`/reactive operators) means authorization is never even evaluated for a request that already failed authentication, saving unnecessary work.
- If a service doesn't have WebFlux's high-concurrency requirements, the traditional Servlet-based [Spring Security core](0400-spring-security-core-filters-authentication-authorization.md) is simpler and equally secure — reactive security is a scaling tool, not a strictly "better" default.
