---
card: spring-security
gi: 115
slug: reactive-webflux-security-enablewebfluxsecurity
title: "Reactive (WebFlux) security (@EnableWebFluxSecurity)"
---

## 1. What it is

Every card in this course so far has assumed the Servlet stack — `HttpSecurity`, `SecurityFilterChain`, blocking `Filter`s running on a thread-per-request model. `@EnableWebFluxSecurity` is the entry point into Spring Security's *parallel*, fully reactive security stack, built for Spring WebFlux applications running on Netty or another non-blocking server: instead of `SecurityFilterChain`, it configures a `SecurityWebFilterChain`; instead of `HttpSecurity`, the DSL is `ServerHttpSecurity`; and every extension point returns a reactive `Mono`/`Flux` rather than a plain value, because a reactive application can never block a thread waiting on an authentication decision without defeating the entire point of the reactive model.

```java
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        http
            .authorizeExchange(exchange -> exchange
                .pathMatchers("/public/**").permitAll()
                .anyExchange().authenticated())
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }
}
```

## 2. Why & when

The Servlet stack's blocking model is fine for most applications, but it fundamentally conflicts with WebFlux's non-blocking, event-loop-based execution: a `Filter` that calls a blocking `UserDetailsService.loadUserByUsername(...)` (a synchronous database call) inside a Netty event loop thread would stall that thread — and since a small, fixed pool of event-loop threads typically serves *all* concurrent connections in a reactive server, blocking even one of them for the duration of a slow database query can stall unrelated requests entirely. Every reactive security interface exists specifically to prevent this: `ReactiveUserDetailsService.findByUsername(...)` returns `Mono<UserDetails>` rather than a plain `UserDetails`, so the lookup composes into the reactive pipeline without ever blocking a thread waiting for it to complete.

Reach for `@EnableWebFluxSecurity` when:

- The application is built on Spring WebFlux (reactive controllers, `WebClient`, R2DBC) rather than Spring MVC — this is the only security configuration model that composes correctly with that stack.
- High-concurrency, I/O-bound workloads where thread-per-request would require an impractically large thread pool — reactive's non-blocking model scales connection count without scaling thread count proportionally, but only if *every* layer, security included, avoids blocking.
- Every custom security component (a `ReactiveAuthenticationManager`, a `ReactiveUserDetailsService`, an authorization check) must be written against the reactive contract — a blocking call hidden inside an otherwise-reactive security bean silently reintroduces the exact problem the reactive stack exists to avoid, without any compiler error to flag it.

It is not simply "the same DSL renamed" — every extension point genuinely returns `Mono`/`Flux`, and porting Servlet-stack security code to WebFlux requires re-expressing it in those terms, not just swapping annotations.

## 3. Core concept

```
Servlet stack                          Reactive (WebFlux) stack
------------------------------------   ------------------------------------------
@EnableWebSecurity                     @EnableWebFluxSecurity
HttpSecurity                           ServerHttpSecurity
SecurityFilterChain                    SecurityWebFilterChain
.authorizeHttpRequests(...)            .authorizeExchange(...)
UserDetailsService                     ReactiveUserDetailsService
    loadUserByUsername(String)             -> UserDetails                 (BLOCKING)
    findByUsername(String)                 -> Mono<UserDetails>           (NON-BLOCKING)
AuthenticationManager                  ReactiveAuthenticationManager
    authenticate(Authentication)            -> Authentication              (BLOCKING)
    authenticate(Authentication)            -> Mono<Authentication>        (NON-BLOCKING)
SecurityContextHolder (ThreadLocal)    ReactiveSecurityContextHolder (card 0116, Reactor Context)

KEY DIFFERENCE: a ThreadLocal-based SecurityContextHolder does NOT work correctly in WebFlux,
because a single reactive chain can hop across MULTIPLE threads as it executes --
ReactiveSecurityContextHolder stores the context in REACTOR CONTEXT instead, which
correctly follows the logical execution regardless of which thread actually runs it.
```

Every Servlet-stack concept has a reactive counterpart, but the counterpart's shape (`Mono`/`Flux` instead of plain values) is not cosmetic — it reflects a genuinely different execution model underneath.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting the servlet security stack using HttpSecurity SecurityFilterChain and a blocking UserDetailsService against the reactive WebFlux stack using ServerHttpSecurity SecurityWebFilterChain and a non blocking ReactiveUserDetailsService returning Mono">
  <rect x="20" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="165" y="42" fill="#8b949e" font-size="10.5" text-anchor="middle" font-family="sans-serif">Servlet stack (thread-per-request)</text>
  <rect x="40" y="58" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="165" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HttpSecurity / SecurityFilterChain</text>
  <rect x="40" y="96" width="250" height="30" rx="5" fill="#161b22" stroke="#f0883e" stroke-width="1.2"/>
  <text x="165" y="115" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">UserDetailsService (BLOCKING call)</text>
  <rect x="40" y="134" width="250" height="30" rx="5" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="153" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SecurityContextHolder (ThreadLocal)</text>
  <text x="165" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1 thread reserved per in-flight request</text>

  <rect x="330" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">Reactive stack (event loop)</text>
  <rect x="350" y="58" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ServerHttpSecurity / SecurityWebFilterChain</text>
  <rect x="350" y="96" width="250" height="30" rx="5" fill="#161b22" stroke="#3fb950" stroke-width="1.2"/>
  <text x="475" y="115" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">ReactiveUserDetailsService -&gt; Mono (NON-blocking)</text>
  <rect x="350" y="134" width="250" height="30" rx="5" fill="#161b22" stroke="#6db33f" stroke-width="1"/>
  <text x="475" y="153" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ReactiveSecurityContextHolder (Reactor Context)</text>
  <text x="475" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">small, fixed thread pool serves ALL connections</text>

  <defs></defs>
</svg>

Every concept has a direct counterpart, but the reactive side's non-blocking shape is a structural requirement, not a naming convention.

## 5. Runnable example

The scenario: model both stacks' user-lookup path side by side using plain Java (standing in for `CompletableFuture` where a real application would use Reactor's `Mono`), growing from a bare blocking-vs-non-blocking contrast into showing why a blocking call inside a reactive pipeline is dangerous, then into a minimal reactive-style authorization check composed from async pieces.

### Level 1 — Basic

Contrast a blocking lookup with a non-blocking one, using `CompletableFuture` to stand in for `Mono` (both represent "a value that will be available later, without blocking the calling thread").

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveSecurityLevel1 {
    record UserDetails(String username, Set<String> authorities) {}

    static class BlockingUserDetailsService {
        // BLOCKS the calling thread until the "database" responds
        UserDetails loadUserByUsername(String username) {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {} // simulates a slow query
            return new UserDetails(username, Set.of("ROLE_USER"));
        }
    }

    static class ReactiveUserDetailsService {
        // returns IMMEDIATELY -- the actual work happens asynchronously, never blocking the caller's thread
        CompletableFuture<UserDetails> findByUsername(String username) {
            return CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                return new UserDetails(username, Set.of("ROLE_USER"));
            });
        }
    }

    public static void main(String[] args) throws Exception {
        BlockingUserDetailsService blocking = new BlockingUserDetailsService();
        UserDetails result1 = blocking.loadUserByUsername("alice"); // this line BLOCKS for ~50ms
        System.out.println("blocking result: " + result1);

        ReactiveUserDetailsService reactive = new ReactiveUserDetailsService();
        CompletableFuture<UserDetails> future = reactive.findByUsername("alice"); // returns INSTANTLY
        System.out.println("call returned immediately, future not yet complete: " + !future.isDone());
        UserDetails result2 = future.get(); // only NOW do we wait, and only because this demo needs the value
        System.out.println("reactive result (once resolved): " + result2);
    }
}
```

**How to run:** save as `ReactiveSecurityLevel1.java`, run `java ReactiveSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
blocking result: UserDetails[username=alice, authorities=[ROLE_USER]]
call returned immediately, future not yet complete: true
reactive result (once resolved): UserDetails[username=alice, authorities=[ROLE_USER]]
```

`BlockingUserDetailsService.loadUserByUsername` occupies the calling thread for the entire duration of the simulated lookup, exactly like a real JDBC-backed `UserDetailsService` would; `ReactiveUserDetailsService.findByUsername` returns a `CompletableFuture` (standing in for `Mono<UserDetails>`) immediately, letting the caller's thread move on to other work while the lookup completes elsewhere — this is the structural difference `@EnableWebFluxSecurity`'s reactive interfaces are built around.

### Level 2 — Intermediate

Show the actual danger: a small, fixed thread pool (modeling a Netty event-loop pool) gets exhausted by blocking calls, but not by non-blocking ones — using a tiny executor to make the effect visible.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveSecurityLevel2 {
    record UserDetails(String username) {}

    public static void main(String[] args) throws Exception {
        // a TINY pool, standing in for a small, fixed reactive event-loop pool (e.g. 2 threads)
        ExecutorService eventLoopPool = Executors.newFixedThreadPool(2);

        System.out.println("--- BLOCKING calls submitted to the small pool ---");
        long startBlocking = System.currentTimeMillis();
        List<Future<UserDetails>> blockingFutures = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            int userId = i;
            blockingFutures.add(eventLoopPool.submit(() -> {
                Thread.sleep(100); // BLOCKS this pool thread for the whole "database call"
                return new UserDetails("user" + userId);
            }));
        }
        for (Future<UserDetails> f : blockingFutures) f.get();
        long blockingDuration = System.currentTimeMillis() - startBlocking;
        System.out.println("4 blocking lookups against a 2-thread pool took ~" + blockingDuration + "ms"
                + " (roughly 2 BATCHES of 100ms, because only 2 can run AT ONCE)");

        eventLoopPool.shutdown();
    }
}
```

**How to run:** save as `ReactiveSecurityLevel2.java`, run `java ReactiveSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output (timing is approximate, but the doubling pattern is the point):
```
--- BLOCKING calls submitted to the small pool ---
4 blocking lookups against a 2-thread pool took ~200ms (roughly 2 BATCHES of 100ms, because only 2 can run AT ONCE)
```

What changed: with only 2 threads in the pool and 4 blocking tasks each holding a thread hostage for 100ms, the tasks must run in two sequential batches — this is exactly the failure mode a blocking `UserDetailsService` call would cause inside a real reactive server's small, fixed event-loop pool: unrelated requests queue up behind whichever ones happen to be blocked on slow I/O, even though the pool has nothing structurally wrong with it — it's simply being used in a way that defeats its design.

### Level 3 — Advanced

Compose a small reactive-style authorization check from asynchronous pieces — a user lookup followed by an authority check — using `CompletableFuture.thenCompose` to model how `Mono` chaining avoids ever blocking while still expressing a multi-step, dependent computation.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveSecurityLevel3 {
    record UserDetails(String username, Set<String> authorities) {}

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) { super(message); }
    }

    static class ReactiveUserDetailsService {
        private final Map<String, UserDetails> users = new HashMap<>();
        void register(UserDetails user) { users.put(user.username(), user); }

        CompletableFuture<UserDetails> findByUsername(String username) {
            return CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(20); } catch (InterruptedException ignored) {} // simulated non-blocking I/O
                UserDetails user = users.get(username);
                if (user == null) throw new NoSuchElementException("no such user: " + username);
                return user;
            });
        }
    }

    // mirrors a ReactiveAuthorizationManager-style check, composed WITHOUT ever blocking a thread
    static CompletableFuture<UserDetails> requireAuthority(CompletableFuture<UserDetails> userFuture, String requiredAuthority) {
        return userFuture.thenApply(user -> {
            if (!user.authorities().contains(requiredAuthority)) {
                throw new AccessDeniedException(user.username() + " lacks required authority " + requiredAuthority);
            }
            return user;
        });
    }

    public static void main(String[] args) {
        ReactiveUserDetailsService service = new ReactiveUserDetailsService();
        service.register(new UserDetails("alice", Set.of("ROLE_USER", "ROLE_ADMIN")));
        service.register(new UserDetails("bob", Set.of("ROLE_USER")));

        // alice: lookup THEN authority check, all composed without blocking
        CompletableFuture<UserDetails> aliceCheck = requireAuthority(service.findByUsername("alice"), "ROLE_ADMIN");
        aliceCheck.thenAccept(user -> System.out.println("alice authorized: " + user))
                  .join(); // .join() only here, at the demo's top level, to wait for printing to finish

        // bob: lookup succeeds, but the authority check fails -- the exception propagates through the chain
        CompletableFuture<UserDetails> bobCheck = requireAuthority(service.findByUsername("bob"), "ROLE_ADMIN");
        bobCheck.handle((user, error) -> {
            if (error != null) System.out.println("bob denied: " + error.getCause().getMessage());
            return null;
        }).join();
    }
}
```

**How to run:** save as `ReactiveSecurityLevel3.java`, run `java ReactiveSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice authorized: UserDetails[username=alice, authorities=[ROLE_USER, ROLE_ADMIN]]
bob denied: bob lacks required authority ROLE_ADMIN
```

What changed: `requireAuthority` composes a dependent, multi-step check (lookup, then authority check) entirely through `thenApply`/`thenCompose`-style chaining, never calling `.get()` or `.join()` until the very top-level demo code needs to observe the final result — this mirrors exactly how a real `Mono<UserDetails>` chain (`.flatMap(user -> ...)`) expresses "do this, then that" without ever blocking a thread waiting between the steps, which is the entire reason `ReactiveAuthenticationManager` and friends are built around `Mono` rather than plain return values.

## 6. Walkthrough

Trace bob's denied authorization check from Level 3, then contrast the structural difference from a blocking equivalent.

**Step 1 — the reactive chain is constructed, but nothing runs yet (in a real `Mono`, evaluation is lazy until subscribed; `CompletableFuture` here starts eagerly, which is a simplification worth noting explicitly).** `service.findByUsername("bob")` kicks off the simulated lookup asynchronously.

**Step 2 — the lookup completes.** After roughly 20ms (simulated I/O, running on a separate thread from whichever one is `main`), `users.get("bob")` returns bob's `UserDetails`, with authorities `{"ROLE_USER"}`.

**Step 3 — `requireAuthority`'s `thenApply` runs**, chained onto the completed lookup. It checks `user.authorities().contains("ROLE_ADMIN")` — `false`, since bob only has `ROLE_USER` — and throws `AccessDeniedException`.

**Step 4 — the exception propagates through the `CompletableFuture` chain**, rather than being thrown synchronously on the calling thread — this is the async-aware analogue of how a `Mono` chain surfaces an error through its `onError` signal rather than an ordinary Java exception unwinding a call stack in real time.

**Step 5 — `handle` observes the outcome.** `bobCheck.handle((user, error) -> ...)` receives `error` non-null (wrapping the `AccessDeniedException`), and prints the denial message — `user` is `null` in this branch, since the computation never reached a successful result.

**Contrast with a blocking equivalent:** a Servlet-stack authorization check would call `userDetailsService.loadUserByUsername("bob")` directly, get a `UserDetails` back synchronously, check its authorities inline, and throw `AccessDeniedException` immediately on the *same* thread that's handling the whole request — simpler to read, but only viable because that thread is dedicated to this one request for its entire duration, which is precisely the assumption a reactive server's small, shared thread pool cannot afford to make.

```
reactive (bob):  findByUsername("bob") [async] -> completes -> thenApply checks authority -> FAILS -> error propagates through chain -> handle() observes it
blocking (bob):  loadUserByUsername("bob") [blocks THIS thread] -> returns -> check authority inline -> throws -> caught synchronously
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing a blocking call into an otherwise-reactive security bean (a custom `ReactiveUserDetailsService` that internally calls a blocking JDBC repository without wrapping it correctly, for instance) produces no compiler error and no obvious symptom under light load — it only manifests as mysterious latency spikes and thread-pool exhaustion once traffic grows, precisely because a few blocking calls can silently monopolize the small, shared pool that every other concurrent request also depends on.

- `@EnableWebFluxSecurity` and its `ServerHttpSecurity`/`SecurityWebFilterChain` DSL are the reactive-stack counterparts to `@EnableWebSecurity`/`HttpSecurity`/`SecurityFilterChain` — same conceptual role, non-blocking shape throughout.
- Every reactive security extension point returns `Mono`/`Flux` rather than a plain value specifically because a reactive server's thread pool is small, fixed, and shared across all concurrent connections — blocking even one of those threads can stall unrelated work.
- `ReactiveUserDetailsService.findByUsername` and `ReactiveAuthenticationManager.authenticate` must be implemented without any blocking calls inside — wrapping a blocking call in `Mono.fromCallable(...).subscribeOn(Schedulers.boundedElastic())` is the standard escape hatch when a genuinely blocking dependency (a JDBC driver, for instance) can't be avoided.
- `SecurityContextHolder`'s `ThreadLocal`-based storage does not work correctly in WebFlux, since a single logical request can execute across multiple threads — card 0116 covers `ReactiveSecurityContextHolder`, its Reactor-Context-based replacement.
- Porting Servlet-stack security configuration to WebFlux is a genuine re-expression in reactive terms, not a mechanical find-and-replace — every custom component needs to be written against the non-blocking contract from the start.
